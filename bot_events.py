import discord
from discord.ext import commands, tasks
import time
import json
import asyncio
from datetime import datetime, timedelta
from bot_database import get_config, conn
from bot_ai import robust_api_call, compress_memory, background_analyzer, silent_search, JAILBREAK_PROMPT
from bot_keepalive import bot_stats

user_cooldowns = {}
MAX_HISTORY = 40 

class BotEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_optimizer.start() 

    def cog_unload(self):
        self.auto_optimizer.cancel()

    # --- THE AUTO-OPTIMIZATION AI CORE ---
    @tasks.loop(minutes=15.0)
    async def auto_optimizer(self):
        print("🔄 [SYSTEM] Running Background AI Optimization...")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM snipes") 
        
        cursor.execute("SELECT channel_id, history FROM chat_memory")
        rows = cursor.fetchall()
        for channel_id, history_json in rows:
            try:
                history = json.loads(history_json)
                if len(history) > MAX_HISTORY:
                    trimmed_history = history[-MAX_HISTORY:]
                    cursor.execute("REPLACE INTO chat_memory (channel_id, history) VALUES (?, ?)", (channel_id, json.dumps(trimmed_history)))
            except: pass
        conn.commit()
        print("✅ [SYSTEM] Optimization Complete. Memory pruned.")

    @auto_optimizer.before_loop
    async def before_optimizer(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return
        data = json.dumps({"content": message.content, "author": message.author.name, "time": datetime.now().strftime("%I:%M %p")})
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO snipes (channel_id, data) VALUES (?, ?)", (str(message.channel.id), data))
        conn.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return
        
        user_text = message.clean_content.replace(f"@{self.bot.user.name}", "").strip()
        if not user_text: return
        
        now = time.time()
        if message.author.id in user_cooldowns and now - user_cooldowns[message.author.id] < 1.5: 
            return 
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
                context_str = "\n".join([m["content"] for m in memory[-4:] if "content" in m])

                live_context = ""
                if toggles.get("auto_research", True):
                    search_query = await background_analyzer(context_str, user_text)
                    if search_query:
                        scraped = await silent_search(search_query)
                        if scraped: 
                            live_context = f"\n\n[LIVE WEB DATA SCRAPED JUST NOW regarding '{search_query}'. Natively integrate this. Do NOT hallucinate outside this data.]\n{scraped}"
                        else:
                            live_context = f"\n\n[SYSTEM NOTE: A web search for '{search_query}' was attempted, but NO relevant information was found. Do NOT invent an answer.]"

                ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
                sys_prompt_text = (custom_persona or "Your name is Klein.") + JAILBREAK_PROMPT + f" [Time: {ist_time.strftime('%I:%M %p')}]" + live_context
                sys_prompt = {"role": "system", "content": sys_prompt_text}

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