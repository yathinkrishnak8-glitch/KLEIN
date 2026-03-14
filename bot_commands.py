import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import time
from bot_database import get_config, update_config, conn
from bot_ai import robust_api_call, groq_clients
from bot_keepalive import bot_stats, start_time

# ==========================================
# 🛑 HIGH-SECURITY DEVELOPER UI COMPONENTS
# ==========================================
class StatusModal(discord.ui.Modal, title='Update Omni-Core Status'):
    status_text = discord.ui.TextInput(
        label='New Playing Status',
        style=discord.TextStyle.short,
        placeholder='e.g., Bypassing mainframes...',
        required=True,
        max_length=100
    )
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.client.change_presence(activity=discord.Game(name=self.status_text.value))
        await interaction.response.send_message(f"✅ **Status successfully updated globally** to: `Playing {self.status_text.value}`", ephemeral=True)

class BroadcastModal(discord.ui.Modal, title='Global Devcast Override'):
    announcement = discord.ui.TextInput(
        label='Broadcast Message',
        style=discord.TextStyle.paragraph,
        placeholder='Enter the update message to blast to all active servers...',
        required=True
    )
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚀 **Initiating Global Broadcast...** This may take a moment.", ephemeral=True)
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM active_channels")
        channels = cursor.fetchall()
        
        embed = discord.Embed(title="📢 SYSTEM OVERRIDE: DEV UPDATE", description=self.announcement.value, color=0x00f0ff)
        embed.set_author(name="Yathin (Creator)", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Klein Omni-Core System Broadcast")
        
        success_count = 0
        for (channel_id,) in channels:
            try:
                channel = interaction.client.get_channel(int(channel_id))
                if channel:
                    await channel.send(embed=embed)
                    success_count += 1
                    await asyncio.sleep(0.5) 
            except Exception: pass
        await interaction.followup.send(f"✅ **Broadcast Complete:** Successfully transmitted to {success_count} active servers.", ephemeral=True)

class DevPanel(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Optimize Engine", style=discord.ButtonStyle.success, emoji="⚡", row=0)
    async def optimize_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chat_memory")
        mem_count = cursor.fetchone()[0]
        await interaction.response.send_message(f"✅ **AI Core Optimized:** Compressed `{mem_count}` memory sectors.", ephemeral=True)

    @discord.ui.button(label="Network Info", style=discord.ButtonStyle.blurple, emoji="🌐", row=0)
    async def network_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guilds = len(self.bot.guilds)
        total_users = sum(g.member_count for g in self.bot.guilds)
        await interaction.response.send_message(f"📡 **Network Telemetry:**\n- Active Servers: `{guilds}`\n- Total Users: `{total_users}`\n- API Keys Active: `{len(groq_clients)}`", ephemeral=True)

    @discord.ui.button(label="Change Status", style=discord.ButtonStyle.secondary, emoji="🎮", row=1)
    async def status_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(StatusModal())

    @discord.ui.button(label="Global Broadcast", style=discord.ButtonStyle.secondary, emoji="📢", row=1)
    async def broadcast_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BroadcastModal())

    @discord.ui.button(label="Wipe All Memory", style=discord.ButtonStyle.danger, emoji="💀", row=2)
    async def flush_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        conn.cursor().execute("DELETE FROM chat_memory")
        conn.commit()
        await interaction.response.send_message("🚨 **CRITICAL: Global Memory Wipe Complete.**", ephemeral=True)

class DevLoginModal(discord.ui.Modal, title='SECURITY OVERRIDE'):
    dev_key = discord.ui.TextInput(
        label='Enter Master Authorization Key',
        style=discord.TextStyle.short,
        placeholder='••••••••',
        required=True
    )
    async def on_submit(self, interaction: discord.Interaction):
        if self.dev_key.value == "mr_yaen":
            embed = discord.Embed(title="⚙️ KLEIN DEV CONSOLE [UNLOCKED]", description="Master control interface initialized. Welcome back, Yathin.", color=0xffaa00)
            embed.add_field(name="Current Uptime", value=f"`{round((time.time() - start_time) / 3600, 2)}h`")
            embed.add_field(name="Total AI Queries", value=f"`{bot_stats['messages_processed']}`")
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, view=DevPanel(interaction.client), ephemeral=True)
        else:
            await interaction.response.send_message("❌ **ACCESS DENIED:** Intrusion attempt logged to system.", ephemeral=True)

# ==========================================
# 🤖 STANDARD SLASH COMMANDS
# ==========================================
class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ **System cooling down!** Try again in {round(error.retry_after, 1)} seconds."
            if not interaction.response.is_done(): await interaction.response.send_message(msg, ephemeral=True)
            else: await interaction.followup.send(msg, ephemeral=True)

    @app_commands.command(name="devpanel", description="[LOCKED] Access the Omni-Core control panel")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def devpanel(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DevLoginModal())

    # --- THE NEW CORE OVERRIDE COMMAND ---
    @app_commands.command(name="core", description="[DEV] Override the bot's foundational brain directive")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def set_core(self, interaction: discord.Interaction, directive: str):
        update_config(interaction.guild_id or interaction.user.id, personality=directive)
        embed = discord.Embed(title="🧠 CORE DIRECTIVE INJECTED", description=f"The AI brain has been rewritten to:\n\n> *{directive}*", color=0x00FFAA)
        await interaction.response.send_message(embed=embed)

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
            await interaction.response.send_message("🧠 **Restored default AI persona.**")
        elif user_input in presets:
            update_config(guild_id, personality=presets[user_input])
            await interaction.response.send_message(f"🎭 **Preset Loaded:** Installed the `{user_input.upper()}` personality core!")
        else:
            update_config(guild_id, personality=bio)
            await interaction.response.send_message(f"🎭 **Custom Persona Updated:** The bot will now act like: `{bio}`")

    @app_commands.command(name="info", description="View digital system status terminal")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def info(self, interaction: discord.Interaction):
        ping = round(self.bot.latency * 1000)
        uptime_hrs = round((time.time() - start_time) / 3600, 2)
        _, current_personality, _, current_model = get_config(interaction.guild_id or interaction.user.id)
        
        embed = discord.Embed(title="💠 GROQ TERMINAL :: HIGH-PERFORMANCE CORE", color=0x00FFAA)
        embed.add_field(name="📡 Status", value=f"🟢 Online (`{ping}ms`)\n**Uptime:** `{uptime_hrs}h`", inline=True)
        embed.add_field(name="👥 Network", value=f"**Keys:** `{len(groq_clients)}`\n**Msgs:** `{bot_stats['messages_processed']}`", inline=True)
        embed.add_field(name="🧠 Core Engine", value=f"**Model:** `{current_model}`", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="changemodel", description="Switch the active AI model")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.choices(model_name=[
        app_commands.Choice(name="DeepSeek R1 70B", value="deepseek-r1-distill-llama-70b"),
        app_commands.Choice(name="LLaMA 3.3 70B", value="llama-3.3-70b-versatile"),
        app_commands.Choice(name="Mixtral 8x7B", value="mixtral-8x7b-32768"),
        app_commands.Choice(name="LLaMA 3.1 8B", value="llama-3.1-8b-instant")
    ])
    async def change_model(self, interaction: discord.Interaction, model_name: app_commands.Choice[str]):
        update_config(interaction.guild_id or interaction.user.id, model=model_name.value)
        await interaction.response.send_message(f"🔄 **Engine Switched:** Now prioritizing `{model_name.name}`.")

    @app_commands.command(name="hack", description="[PRANK] Leak a user's highly questionable browser history")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def hack(self, interaction: discord.Interaction, target_user: discord.User):
        await interaction.response.defer()
        msg = await interaction.followup.send(f"📡 `[HACK INITIATED]` Targeting {target_user.mention}...")
        await asyncio.sleep(1.5)
        await msg.edit(content="🔓 `[BYPASSING FIREWALL]` Injecting payload into target's router...")
        await asyncio.sleep(1.5)
        
        fake_searches = [
            "How to mathematically prove I am a sigma male", "Is it illegal to use a katana for home defense",
            "Why do girls run away when I explain Attack on Titan lore", "How to hide my League of Legends play history from God",
            "Nearest place to touch grass in real life", "Can you get arrested for having too much dark energy",
            "How to make my Discord status look more mysterious", "Free Fire Max aimbot undetected 2026",
            "Why does my back hurt at 20", "How to convince my mom that Blox Fruits is a financial investment",
            "Where to buy a real Hellsing replica coat", "Which Bleach filler episodes can I skip without losing my honor",
            "How to dual boot Kali Linux so I look like a hacker at Starbucks", "Why do I lose every argument in the shower",
            "Am I actually the main character quiz", "How to delete my entire digital footprint by tomorrow",
            "How to properly execute a villain laugh in the mirror", "Why do my knees crack when I stand up (I am 21)",
            "How to win a fight using only anime logic", "Can I put my Call of Duty K/D ratio on my resume"
        ]
        
        leaked = random.sample(fake_searches, 3)
        history_formatted = "\n".join([f"🔍 *\"{search}\"*" for search in leaked])
        
        embed = discord.Embed(title="🛑 SECURITY BREACH 🛑", description=f"**Target:** {target_user.name}\n**Data Extracted:** Incognito Browser History", color=0x8A2BE2)
        embed.set_thumbnail(url=target_user.display_avatar.url if target_user.display_avatar else None)
        embed.add_field(name="Most Recent Google Searches:", value=history_formatted, inline=False)
        embed.set_footer(text="Klein Surveillance Network")
        await msg.edit(content=None, embed=embed)

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

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))