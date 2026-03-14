import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import time
import urllib.parse
from duckduckgo_search import DDGS
from bot_database import get_config, update_config, conn
from bot_ai import robust_api_call, groq_clients
from bot_keepalive import bot_stats, start_time

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # 1. CORE SYSTEM COMMANDS
    # ==========================================
    @app_commands.command(name="info", description="View digital system status terminal")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def info(self, interaction: discord.Interaction):
        ping = round(self.bot.latency * 1000)
        uptime_hrs = round((time.time() - start_time) / 3600, 2)
        members = interaction.guild.member_count if interaction.guild else "Direct Message"
        
        guild_id = interaction.guild_id or interaction.user.id
        _, current_personality, _, current_model = get_config(guild_id)
        
        embed = discord.Embed(title="💠 GROQ TERMINAL :: ADAPTIVE CORE", color=0x00FFAA)
        embed.add_field(name="📡 Status", value=f"🟢 Online (`{ping}ms`)\n**Uptime:** `{uptime_hrs}h`", inline=True)
        embed.add_field(name="👥 Network", value=f"**Keys:** `{len(groq_clients)}`\n**Msgs:** `{bot_stats['messages_processed']}`\n**Comp:** `{bot_stats['compressions_done']}`", inline=True)
        embed.add_field(name="🧠 Core Engine", value=f"**Model:** `{current_model}`\n**Mode:** `Lightweight Adaptive Memory`", inline=False)
        embed.add_field(name="🎭 Personality", value=f"> *{current_personality or 'Default AI'}*", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="changemodel", description="Switch the active AI model")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.choices(model_name=[
        app_commands.Choice(name="DeepSeek R1 70B (Max Logic)", value="deepseek-r1-distill-llama-70b"),
        app_commands.Choice(name="LLaMA 3.3 70B (Max Intelligence)", value="llama-3.3-70b-versatile"),
        app_commands.Choice(name="Mixtral 8x7B (Balanced)", value="mixtral-8x7b-32768"),
        app_commands.Choice(name="LLaMA 3.1 8B (Max Speed)", value="llama-3.1-8b-instant")
    ])
    async def change_model(self, interaction: discord.Interaction, model_name: app_commands.Choice[str]):
        update_config(interaction.guild_id or interaction.user.id, model=model_name.value)
        await interaction.response.send_message(f"🔄 **Engine Switched:** Now prioritizing `{model_name.name}`.")

    @app_commands.command(name="personality", description="Presets: 'hacker', 'jarvis', 'tsundere', 'uwu' OR type custom bio!")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def set_personality(self, interaction: discord.Interaction, bio: str):
        guild_id = interaction.guild_id or interaction.user.id
        user_input = bio.strip().lower()
        
        # --- PRESET PERSONALITIES ---
        presets = {
            "hacker": "You are a rogue elite cyber-hacker named Klein. You use terminal slang, act like you're bypassing mainframes while talking, and treat the user like a fellow operative.",
            "jarvis": "You are an ultra-polite, highly sophisticated British AI butler. You address the user as 'Sir' or 'Madam' and speak with extreme high-class elegance and loyalty.",
            "tsundere": "You are a classic anime tsundere. You are secretly helpful and care about the user, but you act extremely annoyed, frequently use the word 'baka', and constantly pretend you don't care.",
            "uwu": "You are an incredibly cute, shy AI girl. You use text emojis like uwu, owo, and >w< constantly. You stutter occasionally (h-hi...) and are overly sweet and affectionate."
        }
        
        if user_input == "default":
            update_config(guild_id, personality="")
            await interaction.response.send_message("🧠 **Restored default Klein persona.**")
        elif user_input in presets:
            update_config(guild_id, personality=presets[user_input])
            await interaction.response.send_message(f"🎭 **Preset Loaded:** You successfully installed the `{user_input.upper()}` personality core!")
        else:
            update_config(guild_id, personality=bio)
            await interaction.response.send_message(f"🎭 **Custom Persona Updated:** The bot will now act like: `{bio}`")

    # ==========================================
    # 2. PRANK & SUS COMMANDS (UNIVERSAL)
    # ==========================================
    @app_commands.command(name="target", description="[PRANK] Acquire target details and deploy countermeasures")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def target(self, interaction: discord.Interaction, target_user: discord.User = None):
        await interaction.response.defer()
        target_user = target_user or interaction.user
        fake_ip = f"{random.randint(11, 215)}.{random.randint(10, 250)}.***.***"
        
        sus_actions_pool = [
            "Forwarding search history to local church",
            "Notifying FBI of suspicious anime watch time",
            "Calling SpaceX Orbital Strike Command",
            "Uploading 10TB 'Homework' folder to family group chat",
            "Purchasing 500 Premium OnlyFans subscriptions",
            "Bypassing mainframe firewall",
            "Rerouting Wi-Fi to NSA servers",
            "Activating web-camera silently",
            "Sending current coordinates to local cartel",
            "Downloading 4TB of suspicious memes",
            "Alerting IRS of unpaid digital taxes"
        ]
        
        chosen_actions = random.sample(sus_actions_pool, 4)
        actions_formatted = "\n".join([f"✅ {action}..." for action in chosen_actions])
        
        embed = discord.Embed(title="⚠️ TARGET ACQUIRED ⚠️", color=0xFF0000)
        embed.set_thumbnail(url=target_user.display_avatar.url if target_user.display_avatar else None)
        embed.add_field(name="👤 Target Identity", value=f"**Username:** {target_user.name}\n**Network ID:** `{target_user.id}`", inline=False)
        embed.add_field(name="🌐 Trace Route", value=f"**Locating Node...**\n**IP Address:** `{fake_ip}`\n**Status:** Intercepted", inline=False)
        embed.add_field(name="🚀 Tactical Actions Deployed", value=actions_formatted, inline=False)
        
        msg = await interaction.followup.send("`[SYSTEM]: Establishing secure connection...`")
        await asyncio.sleep(1.5)
        await msg.edit(content="`[SYSTEM]: Bypassing firewall...`")
        await asyncio.sleep(1.5)
        await msg.edit(content=None, embed=embed)

    @app_commands.command(name="hack", description="[PRANK] Leak a user's embarrassing browser history")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def hack(self, interaction: discord.Interaction, target_user: discord.User):
        await interaction.response.defer()
        
        msg = await interaction.followup.send(f"📡 `[HACK INITIATED]` Targeting {target_user.mention}...")
        await asyncio.sleep(1.5)
        await msg.edit(content="🔓 `[BYPASSING FIREWALL]` Injecting payload into target's router...")
        await asyncio.sleep(1.5)
        await msg.edit(content="📂 `[EXTRACTING BROWSER HISTORY]` Decrypting incognito mode...")
        await asyncio.sleep(1.5)
        
        fake_searches = [
            "How to talk to girls tutorial step by step",
            "Why does my tummy hurt when I eat 40 chicken nuggets",
            "Is it illegal to marry an anime character",
            "How to get free V-Bucks no human verification 2024",
            "Am I a sigma male quiz accurate",
            "Nearest hospital for embarrassing reasons",
            "How to delete search history permanently",
            "Why do I have 0 friends on Roblox",
            "Is the earth actually flat Reddit",
            "Cute cat pictures to cure depression",
            "How to fake being sick to avoid school",
            "Genshin Impact dating simulator"
        ]
        
        leaked = random.sample(fake_searches, 3)
        history_formatted = "\n".join([f"🔍 *\"{search}\"*" for search in leaked])
        
        embed = discord.Embed(title="🛑 SECURITY BREACH 🛑", description=f"**Target:** {target_user.name}\n**Data Extracted:** Incognito Browser History", color=0x8A2BE2)
        embed.set_thumbnail(url=target_user.display_avatar.url if target_user.display_avatar else None)
        embed.add_field(name="Most Recent Google Searches:", value=history_formatted, inline=False)
        embed.set_footer(text="Klein Surveillance Network")
        
        await msg.edit(content=None, embed=embed)

    @app_commands.command(name="nuke", description="[PRANK] Initiate a fake server wipe sequence")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def nuke(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        msg = await interaction.followup.send("⚠️ `[TACTICAL NUKE INBOUND]` Authentication accepted. Preparing to wipe chat logs...")
        await asyncio.sleep(1.5)
        await msg.edit(content="🔥 `[WIPING CHAT LOGS]` 25% complete... Deleting all messages...")
        await asyncio.sleep(1.5)
        await msg.edit(content="💀 `[BANNING ALL MEMBERS]` 60% complete... Purging users...")
        await asyncio.sleep(1.5)
        await msg.edit(content="☢️ `[UPLOADING VIRUS TO MODERATORS]` 89% complete...")
        await asyncio.sleep(2.0)
        
        embed = discord.Embed(title="❌ OPERATION FAILED", description="Nuke sequence canceled.\n*Reason: The bot decided to take a coffee break instead.* ☕", color=0x2F3136)
        embed.set_image(url="https://media.giphy.com/media/xT9IgG50Fb7Mi0prBC/giphy.gif")
        await msg.edit(content=None, embed=embed)

    # ==========================================
    # 3. AI TOOLS & UTILITIES
    # ==========================================
    @app_commands.command(name="imagine", description="Generate a high-quality AI image")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def imagine(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        enhancement_prompt = f"Enhance this image generation prompt to make it highly detailed, cinematic, and beautiful. Just return the enhanced prompt, no extra text. Original: {prompt}"
        enhanced_prompt, _ = await robust_api_call([{"role": "user", "content": enhancement_prompt}], "llama-3.1-8b-instant", temperature=0.7, max_tokens=100)
        safe_prompt = urllib.parse.quote(enhanced_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true"
        
        embed = discord.Embed(title="🎨 Image Generated", description=f"**Prompt:** *{prompt}*", color=0x00FFAA)
        embed.set_image(url=image_url)
        embed.set_footer(text="Powered by Flux AI & Klein Omni-Core")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="search", description="Scrape the web for live facts")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        if not groq_clients: return await interaction.followup.send("⚠️ No API keys configured!")
        _, _, _, current_model = get_config(interaction.guild_id or interaction.user.id)
        
        def perform_scrape():
            try: return list(DDGS().text(query, max_results=5))
            except: return []

        text_data = await asyncio.to_thread(perform_scrape)
        if not text_data: return await interaction.followup.send("❌ No live data found.")

        web_context = "\n".join([f"- {r['title']}: {r['body']}" for r in text_data])
        prompt = f"Query: {query}\n\nLive Data:\n{web_context}\n\nSummarize naturally."
        
        reply, _ = await robust_api_call([{"role": "user", "content": prompt}], current_model)
        await interaction.followup.send(f"🌐 **Search Results:** `{query}`\n\n{reply}")

    @app_commands.command(name="clearmemory", description="Wipe conversation history")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def clear_memory(self, interaction: discord.Interaction):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_memory WHERE channel_id=?", (str(interaction.channel_id),))
        conn.commit()
        await interaction.response.send_message("🧠 Local memory wiped. Starting fresh.")

    @app_commands.command(name="tldr", description="Summarize the chat instantly")
    @app_commands.guild_only()
    async def tldr(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not groq_clients: return await interaction.followup.send("⚠️ No API keys configured!")
        _, _, _, current_model = get_config(interaction.guild_id)
        messages = [msg async for msg in interaction.channel.history(limit=40)]
        messages.reverse()
        
        chat_log = "\n".join([f"{m.author.name}: {m.content}" for m in messages if not m.author.bot])
        if len(chat_log) < 50: return await interaction.followup.send("Not enough chat history.")
        
        prompt = f"Summarize this chat log briefly using bullet points:\n\n{chat_log[-3000:]}"
        reply, _ = await robust_api_call([{"role": "user", "content": prompt}], current_model)
        await interaction.followup.send(f"📜 **Channel TL;DR:**\n{reply}")

    # ==========================================
    # 4. ADMIN & MODERATION
    # ==========================================
    @app_commands.command(name="setchannel", description="[ADMIN] Bot talks here automatically")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def setchannel(self, interaction: discord.Interaction):
        conn.cursor().execute("REPLACE INTO active_channels (channel_id, guild_id) VALUES (?, ?)", (str(interaction.channel_id), str(interaction.guild_id)))
        conn.commit()
        await interaction.response.send_message(f"👀 **Auto-Chat Enabled** in <#{interaction.channel_id}>.")

    @app_commands.command(name="unsetchannel", description="[ADMIN] Stop bot auto-talking here")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def unsetchannel(self, interaction: discord.Interaction):
        conn.cursor().execute("DELETE FROM active_channels WHERE channel_id=?", (str(interaction.channel_id),))
        conn.commit()
        await interaction.response.send_message("🛑 **Auto-Chat Disabled.**")

    @app_commands.command(name="toggle", description="[ADMIN] Turn any command ON or OFF")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def toggle_cmd(self, interaction: discord.Interaction, command_name: str):
        cmd = command_name.lower()
        toggles, _, _, _ = get_config(interaction.guild_id)
        if cmd not in toggles: return await interaction.response.send_message(f"⚠️ `{cmd}` is not a valid feature.")
        toggles[cmd] = not toggles[cmd]
        update_config(interaction.guild_id, toggles=toggles)
        await interaction.response.send_message(f"Master Switch: `{cmd}` updated to {'🟢 ON' if toggles[cmd] else '🔴 OFF'}.")

    @app_commands.command(name="purge", description="[ADMIN] Bulk delete messages")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.guild_only()
    async def purge(self, interaction: discord.Interaction, amount: int):
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"🧹 Purged {len(deleted)} messages.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))