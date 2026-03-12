import discord
from discord.ext import commands
import time
import json
import asyncio
from datetime import datetime, timedelta
from bot_database import get_config, conn
from bot_ai import needs_research, silent_search, groq_client, bot_settings, JAILBREAK_PROMPT
from bot_keepalive import bot_stats
from bot_utils import send_dev_log

user_cooldowns = {}
MAX_HISTORY = 40

class BotEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        
        now = time.time()
        if message.author.id in user_cooldowns and now - user_cooldowns[message.author.id] < 1.5: return
        user_cooldowns[message.author.id] = now
        
        bot_stats["messages_processed"] += 1
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM active_channels WHERE channel_id=?", (str(message.channel.id),))
        is_active = bool(cursor.fetchone())

        if self.bot.user.mentioned_in(message) or is_active or isinstance(message.channel, discord.DMChannel):
            guild_id = message.guild.id if message.guild else message.author.id
            toggles, custom_persona, _, current_model = get_config(guild_id)
            user_text = message.clean_content.replace(f"@{self.bot.user.name}", "").strip()
            
            async with message.channel.typing():
                # --- SILENT BACKGROUND INTELLIGENCE ---
                live_context = ""
                if toggles.get("auto_research", True) and await needs_research(user_text):
                    scraped_text = await silent_search(user_text)
                    if scraped_text:
                        live_context = f"\n\n[SYSTEM NOTICE: LIVE WEB DATA SCRAPED. Natively integrate this into your reply.]\n{scraped_text}"

                ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
                sys_content = custom_persona if custom_persona else "Your name is Klein. You are an elite AI."
                sys_prompt_text = sys_content + JAILBREAK_PROMPT + f" [Time: {ist_time.strftime('%I:%M %p')}]" + live_context
                sys_prompt = {"role": "system", "content": sys_prompt_text}
                
                # --- MEMORY HANDLING & SANITIZER ---
                channel_key = str(message.channel.id)
                cursor.execute("SELECT history FROM chat_memory WHERE channel_id=?", (channel_key,))
                row = cursor.fetchone()
                memory = json.loads(row[0]) if row else []
                
                # CRITICAL FIX: If the database contains old plain-text memory, wipe it so the bot doesn't crash.
                if memory and isinstance(memory[0], str):
                    memory = []

                memory.append({"role": "user", "content": f"[{message.author.display_name}]: {user_text}"})
                if len(memory) > MAX_HISTORY: memory = memory[-MAX_HISTORY:]

                # --- AI CALL WITH FALLBACK ---
                try:
                    response = await groq_client.chat.completions.create(model=current_model, messages=[sys_prompt] + memory, temperature=0.7)
                    reply = response.choices[0].message.content
                except Exception as e:
                    await send_dev_log(self.bot, guild_id, f"Primary Model Error: {str(e)}")
                    await asyncio.sleep(1)
                    try:
                        response = await groq_client.chat.completions.create(model=bot_settings["fallback_model"], messages=[sys_prompt] + memory, temperature=0.7)
                        reply = response.choices[0].message.content
                    except Exception as fallback_e:
                        await send_dev_log(self.bot, guild_id, f"Fallback Model Error: {str(fallback_e)}")
                        reply = f"Both AI cores failed due to API limitations or corrupted data. Use `/clearmemory` to force a reset."

                memory.append({"role": "assistant", "content": reply})
                cursor.execute("REPLACE INTO chat_memory (channel_id, history) VALUES (?, ?)", (channel_key, json.dumps(memory)))
                conn.commit()
                
                for i in range(0, len(reply), 1995): await message.reply(reply[i:i+1995])

async def setup(bot):
    await bot.add_cog(BotEvents(bot))


