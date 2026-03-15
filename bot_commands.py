import discord
from discord.ext import commands
from discord import app_commands
import asyncio, random, time, os
from bot_database import get_config, update_config, conn
from bot_ai import groq_clients, robust_api_call
from bot_keepalive import bot_stats, start_time

class DevLoginModal(discord.ui.Modal, title='MASTER OVERRIDE'):
    key = discord.ui.TextInput(label='Enter Master Key', placeholder='••••', required=True)
    async def on_submit(self, interaction: discord.Interaction):
        if self.key.value.strip() == "mr_yaen":
            embed = discord.Embed(title="🚀 DEVELOPER ACCESS GRANTED", color=0x00f0ff)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 🧠 OMNI-CORE CONTROL ---
    @app_commands.command(name="core", description="Force-inject a new personality directive into the brain")
    async def set_core(self, interaction: discord.Interaction, directive: str):
        update_config(interaction.guild_id or interaction.user.id, personality=directive)
        embed = discord.Embed(title="🧠 CORE REWRITTEN", description=f"New Directive: `{directive[:500]}`", color=0x00ffaa)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="personality", description="Quick-swap presets")
    @app_commands.choices(preset=[
        app_commands.Choice(name="Default AI", value="default"),
        app_commands.Choice(name="Cyber-Hacker", value="hacker"),
        app_commands.Choice(name="Sarcastic 2026 Guy", value="sarcasm"),
        app_commands.Choice(name="Anime Tsundere", value="baka")
    ])
    async def personality(self, interaction: discord.Interaction, preset: app_commands.Choice[str]):
        p_map = {
            "default": "",
            "hacker": "Elite rogue hacker. Slang: mainframes, pwned, bypass.",
            "sarcasm": "Exhausted 2026 human. Deeply sarcastic, unbothered.",
            "baka": "Anime Tsundere. Helpful but acts annoyed. Uses 'baka'."
        }
        update_config(interaction.guild_id or interaction.user.id, personality=p_map[preset.value])
        await interaction.response.send_message(f"🎭 Applied `{preset.name}` preset.")

    # --- 🛠️ ADMIN TOOLS ---
    @app_commands.command(name="devpanel", description="Secret Developer Interface")
    async def devpanel(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DevLoginModal())

    @app_commands.command(name="info", description="Live System Telemetry")
    async def info(self, interaction: discord.Interaction):
        uptime = round((time.time() - start_time) / 3600, 2)
        embed = discord.Embed(title="💠 OMNI-CORE V5 TELEMETRY", color=0x00f0ff)
        embed.add_field(name="Ping", value=f"`{round(self.bot.latency*1000)}ms`")
        embed.add_field(name="Uptime", value=f"`{uptime}h`")
        embed.add_field(name="Keys", value=f"`{len(groq_clients)}`")
        embed.set_footer(text="Built by Yathin & Google")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setchannel", description="Authorize auto-chat for this channel")
    @app_commands.default_permissions(administrator=True)
    async def setchannel(self, interaction: discord.Interaction):
        conn.cursor().execute("REPLACE INTO active_channels (channel_id, guild_id) VALUES (?, ?)", (str(interaction.channel_id), str(interaction.guild_id)))
        conn.commit()
        await interaction.response.send_message(f"✅ Auto-chat authorized in <#{interaction.channel_id}>.")

    # --- 🎭 PRANK SUITE ---
    @app_commands.command(name="hack", description="Simulate a deep-web leak on a user")
    async def hack(self, interaction: discord.Interaction, target: discord.User):
        await interaction.response.send_message(f"📡 `[UPLINK ESTABLISHED]` Targeting {target.mention}...")
        await asyncio.sleep(2)
        history = ["How to join Anonymous", "Why is my PC glowing red?", "Is it illegal to hack my school?"]
        embed = discord.Embed(title="🛑 DATA BREACH", description=f"Leaked searches for {target.name}:", color=0xff0000)
        embed.add_field(name="Logs", value="\n".join([f"🔍 *{s}*" for s in history]))
        await interaction.edit_original_response(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))