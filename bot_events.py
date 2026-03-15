import discord
from discord.ext import commands, tasks
import time, json, asyncio
from datetime import datetime
from bot_database import get_config, conn
from bot_ai import robust_api_call, compress_memory, BASE_SYSTEM
from bot_keepalive import bot_stats

user_cooldowns = {}
MAX_HISTORY = 40 

class BotEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_optimizer.start() 

    def cog_unload(self):
        self.auto_optimizer.cancel()

    @tasks.loop(minutes=15.0)
    async def auto_optimizer(self):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM snipes") 
        cursor.execute("SELECT channel_id, history FROM chat_memory")
        for channel_id, history_json in cursor.fetchall():
            try:
                history = json.loads(history_json)
                if len(history) > MAX_HISTORY:
                    cursor.execute("REPLACE INTO chat_memory (channel_id, history) VALUES (?, ?)", (channel_id, json.dumps(history[-MAX_HISTORY:])))
            except: pass
        conn.commit()

    @auto_optimizer.before_loop
    async def before_optimizer(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return
        data = json.dumps({"content": message.content, "author": message.author.name})
        conn.cursor().execute("REPLACE INTO snipes (channel_id, data) VALUES (?, ?)", (str(message.channel.id), data))
        conn.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return
        
        user_text = message.clean_content.replace(f"@{self.bot.user.name}", "").strip()
        if not user_text: return
        
        now = time.time()
        if message.author.id in user_cooldowns and now - user_cooldowns[message.author.id] < 1.5: return 
        user_cooldowns[message.author.id] = now
        
        c = conn.cursor()
        c.execute("SELECT * FROM active_channels WHERE channel_id=?", (str(message.channel.id),))
        is_active = bool(c.fetchone())

        if self.bot.user.mentioned_in(message) or is_active or isinstance(message.channel, discord.DMChannel):
            bot_stats["messages_processed"] += 1
            guild_id = message.guild.id if message.guild else message.author.id
            toggles, custom_persona, _, current_model = get_config(guild_id)
            
            async with message.channel.typing():
                c.execute("SELECT history FROM chat_memory WHERE channel_id=?", (str(message.channel.id),))
                row = c.fetchone()
                raw_memory = json.loads(row[0]) if row else []
                memory = [msg for msg in raw_memory if isinstance(msg, dict) and "role" in msg and "content" in msg]

                memory = await compress_memory(memory)
                
                core_directive = custom_persona if custom_persona else "You are a highly intelligent AI named YoAI."
                sys_prompt = {"role": "system", "content": f"[CORE OVERRIDE]: {core_directive}\n\n{BASE_SYSTEM}"}

                memory.append({"role": "user", "content": f"[{message.author.display_name}]: {user_text}"})
                if len(memory) > MAX_HISTORY: memory = memory[-MAX_HISTORY:]

                reply, _ = await robust_api_call([sys_prompt] + memory, current_model)
                if "<think>" in reply and "</think>" in reply: 
                    reply = reply.split("</think>")[-1].strip()

                memory.append({"role": "assistant", "content": reply})
                c.execute("REPLACE INTO chat_memory (channel_id, history) VALUES (?, ?)", (str(message.channel.id), json.dumps(memory)))
                conn.commit()
                
                for i in range(0, len(reply), 1995): await message.reply(reply[i:i+1995])

async def setup(bot):
    await bot.add_cog(BotEvents(bot))