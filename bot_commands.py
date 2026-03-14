import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import time
from duckduckgo_search import DDGS
from bot_database import get_config, update_config, conn
from bot_ai import robust_api_call, groq_clients
from bot_keepalive import bot_stats, start_time

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- GLOBAL ERROR HANDLER FOR COOLDOWNS ---
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ **System cooling down!** Try again in {round(error.retry_after, 1)} seconds."
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        else:
            print(f"Command Error: {error}")

    # ==========================================
    # 1. CORE SYSTEM COMMANDS
    # ==========================================
    @app_commands.command(name="info", description="View digital system status terminal")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def info(self, interaction: discord.Interaction):
        ping = round(self.bot.latency * 1000)
        uptime_hrs = round((time.time() - start_time) / 3600, 2)
        
        guild_id = interaction.guild_id or interaction.user.id
        _, current_personality, _, current_model = get_config(guild_id)
        
        embed = discord.Embed(title="💠 GROQ TERMINAL :: HIGH-PERFORMANCE CORE", color=0x00FFAA)
        embed.add_field(name="📡 Status", value=f"🟢 Online (`{ping}ms`)\n**Uptime:** `{uptime_hrs}h`", inline=True)
        embed.add_field(name="👥 Network", value=f"**Keys:** `{len(groq_clients)}`\n**Msgs:** `{bot_stats['messages_processed']}`\n**Comp:** `{bot_stats['compressions_done']}`", inline=True)
        embed.add_field(name="🧠 Core Engine", value=f"**Model:** `{current_model}`\n**Mode:** `Optimized Adaptive Memory`", inline=False)
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
        
        presets = {
            "hacker": "You are a rogue elite cyber-hacker named Klein. You use terminal slang, act like you're bypassing mainframes while talking.",
            "jarvis": "You are an ultra-polite, highly sophisticated British AI butler. You address the user as 'Sir' or 'Madam'.",
            "tsundere": "You are a classic anime tsundere. You are secretly helpful but act extremely annoyed and frequently use the word 'baka'.",
            "uwu": "You are an incredibly cute, shy AI girl. You use text emojis like uwu, owo, and stutter occasionally."
        }
        
        if user_input == "default":
            update_config(guild_id, personality="")
            await interaction.response.send_message("🧠 **Restored default Klein persona.**")
        elif user_input in presets:
            update_config(guild_id, personality=presets[user_input])
            await interaction.response.send_message(f"🎭 **Preset Loaded:** Installed the `{user_input.upper()}` personality core!")
        else:
            update_config(guild_id, personality=bio)
            await interaction.response.send_message(f"🎭 **Custom Persona Updated:** The bot will now act like: `{bio}`")

    # ==========================================
    # 2. PRANK & SUS COMMANDS (UNIVERSAL)
    # ==========================================
    @app_commands.command(name="target", description="[PRANK] Acquire target details and deploy countermeasures")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.checks.cooldown(1, 8.0, key=lambda i: i.user.id) # 8 second cooldown per user
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

    @app_commands.command(name="hack", description="[PRANK] Leak a user's highly questionable browser history")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id) # 10 second cooldown per user
    async def hack(self, interaction: discord.Interaction, target_user: discord.User):
        await interaction.response.defer()
        
        msg = await interaction.followup.send(f"📡 `[HACK INITIATED]` Targeting {target_user.mention}...")
        await asyncio.sleep(1.5)
        await msg.edit(content="🔓 `[BYPASSING FIREWALL]` Injecting payload into target's router...")
        await asyncio.sleep(1.5)
        await msg.edit(content="📂 `[EXTRACTING BROWSER HISTORY]` Decrypting incognito mode...")
        await asyncio.sleep(1.5)
        
        # Massive 100-item edgelord pool restored
        fake_searches = [
            "How to mathematically prove I am a sigma male", "Is it illegal to use a katana for home defense",
            "Why do girls run away when I explain Attack on Titan lore", "How to hide my League of Legends play history from God",
            "Nearest place to touch grass in real life", "Can you get arrested for having too much dark energy",
            "How to make my Discord status look more mysterious", "Free Fire Max aimbot undetected 2026",
            "Why does my back hurt at 20", "How to convince my mom that Blox Fruits is a financial investment",
            "Is 14 hours of screen time bad for my posture", "How to unsend a wildly embarrassing text from 3 years ago",
            "Where to buy a real Hellsing replica coat", "Which Bleach filler episodes can I skip without losing my honor",
            "How to dual boot Kali Linux so I look like a hacker at Starbucks", "Why do I lose every argument in the shower",
            "Am I actually the main character quiz", "How to delete my entire digital footprint by tomorrow",
            "Goth girl repellent (or attractant)", "Is it weird to practice sword fighting in the living room",
            "How to recover 50,000 lost V-Bucks", "Can I pay my taxes with crypto meme coins",
            "How to look intimidating while drinking a Capri Sun", "Genshin Impact dating simulator download",
            "Why does the cashier look at me weird when I buy 40 chicken nuggets", "Is it possible to unlock the Sharingan through emotional trauma",
            "How to Naruto run faster than the school principal", "Minecraft realistic girlfriend mod 1.20",
            "Why do I get zero likes on my Joker quote edits", "How to casually drop that my IQ is 140 in conversation",
            "Is smelling like onions a sign of high testosterone", "How to explain to my barber that I want the Levi Ackerman haircut",
            "Valorant crosshair settings to fix my terrible aim", "Can you survive purely on Monster Energy and Doritos",
            "How to professionally say 'skill issue' in an email", "Why is my aura so dark and twisted",
            "Is it legal to challenge someone to a duel in 2026", "How to fake being a cyber security expert",
            "What to do if you accidentally waved at someone who wasn't waving at you", "How to recover from calling the teacher 'Mom'",
            "Top 10 anime betrayals to quote when my friend takes my fries", "Is it considered rizz if I stare at her without blinking",
            "How to refund a Roblox skin I bought in 2016", "Why doesn't my life have background music",
            "How to walk away in slow motion after dropping a sick burn", "Can I put 'Discord Mod' on my college application",
            "How to communicate with women (wikiHow)", "Are fedoras making a comeback this year",
            "How to safely perform the Five Point Palm Exploding Heart Technique", "Why do people leave the voice channel when I join",
            "How to tell if I am a reincarnated demon lord", "Best excuses for losing a 1v1 in CS:GO",
            "How to make my voice sound deeper on Discord calls", "Is it normal to hiss at the sun when I go outside",
            "How to buy Bitcoin with a $25 Amazon gift card", "Can I get a restraining order against my sleep paralysis demon",
            "How to dramatically gaze out the window while it's raining", "Why do I feel a dark power awakening in my left eye",
            "What to do when you realize you're the side character", "How to get unbanned from the local McDonald's",
            "Is it possible to dodge bullets if I train enough", "How to convince my friends I have a girlfriend in another country",
            "Why does nobody understand my highly advanced humor", "How to type 200 WPM so I can win internet arguments faster",
            "Can you legally marry a VTuber", "How to stand like a JoJo character in public without looking dumb",
            "Where to learn dark magic fast and easy", "How to cure the intense pain of carrying my entire team",
            "Is it a crime to be this misunderstood", "How to casually mention I moderate a server with 500 members",
            "Why do my knees crack when I stand up (I am 21)", "How to legally acquire a pet raccoon",
            "Is it okay to wear a cape to the grocery store", "How to delete someone else's Reddit post",
            "Can I put my Call of Duty K/D ratio on my resume", "How to win a fight using only anime logic",
            "Why does the mirror break when I look at it (not metaphorically)", "How to tell if my cat is secretly an FBI informant",
            "Best comebacks for when someone calls me a nerd", "How to make eye contact without looking like a serial killer",
            "Is it possible to hack the school grading system using HTML", "How to properly brood in the corner of a party",
            "Why do my friends put me on read when I send lore videos", "How to summon the courage to ask for extra ketchup",
            "Is being built different an actual medical condition", "How to explain to my parents that streaming is a real job (0 viewers)",
            "Can a gaming chair actually make me taller", "How to properly execute a villain laugh in the mirror",
            "Why do I run out of breath walking up the stairs", "How to find my soulmate using algorithms",
            "Is it legal to walk around with a giant Buster Sword", "How to convince people I'm a time traveler",
            "Why does my microphone always echo", "How to successfully flirt using only obscure memes",
            "Can I use 'It's not a phase' as a legal defense", "How to train my dog to bring me Mountain Dew",
            "Why did I get muted in the official Roblox server", "How to stop overthinking what I said 5 years ago",
            "Is it possible to download more RAM", "How to look cool while tripping over a curb"
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
    @app_commands.checks.cooldown(1, 15.0, key=lambda i: i.channel.id) # 15 second cooldown per channel
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
    @app_commands.command(name="search", description="Scrape the web for live facts")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id) # 5 second cooldown
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
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.channel.id) 
    async def clear_memory(self, interaction: discord.Interaction):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_memory WHERE channel_id=?", (str(interaction.channel_id),))
        conn.commit()
        await interaction.response.send_message("🧠 Local memory wiped. Starting fresh.")

    @app_commands.command(name="tldr", description="Summarize the chat instantly")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 15.0, key=lambda i: i.channel.id) 
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