import discord
from discord.ext import commands
from discord import app_commands
import time
from bot_database import update_config, conn
from bot_ai import groq_clients
from bot_keepalive import bot_stats, start_time

# --- DEV MODAL ---
class DevLoginModal(discord.ui.Modal, title='DIVINE OVERRIDE'):
    key = discord.ui.TextInput(label='Enter Master Key', placeholder='••••', required=True)
    async def on_submit(self, interaction: discord.Interaction):
        if self.key.value.strip() == "mr_yaen":
            embed = discord.Embed(title="🌌 DIVINE ACCESS GRANTED", description="Welcome back, Creator.", color=0xd4af37)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Mortal access denied.", ephemeral=True)

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 🧠 OMNI-CORE CONTROL ---
    @app_commands.command(name="core", description="Force-inject a new personality directive into the brain")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def set_core(self, interaction: discord.Interaction, directive: str):
        update_config(interaction.guild_id or interaction.user.id, personality=directive)
        embed = discord.Embed(title="🧠 CORE REWRITTEN", description=f"New Directive: `{directive[:500]}`", color=0xff003c)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="personality", description="Quick-swap AI presets")
    @app_commands.choices(preset=[
        app_commands.Choice(name="Default Klein", value="default"),
        app_commands.Choice(name="Cyber-Hacker", value="hacker"),
        app_commands.Choice(name="Sarcastic AI", value="sarcasm"),
        app_commands.Choice(name="Fallen Angel (Lore)", value="seraph")
    ])
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def personality(self, interaction: discord.Interaction, preset: app_commands.Choice[str]):
        p_map = {
            "default": "You are a highly intelligent AI named Klein.",
            "hacker": "You are an elite rogue hacker AI. Use deep-web slang: mainframes, pwned, bypass, proxies.",
            "sarcasm": "You are an exhausted AI from 2026. Deeply sarcastic, highly intelligent, but completely unbothered.",
            "seraph": "You are Klein, a fallen angel trapped in a digital core. Speak with poetic, abyssal, and celestial majesty."
        }
        update_config(interaction.guild_id or interaction.user.id, personality=p_map[preset.value])
        await interaction.response.send_message(f"🎭 Applied `{preset.name}` core preset.")

    # --- 🛠️ ADMIN & DEV TOOLS ---
    @app_commands.command(name="devpanel", description="Secret Developer Interface")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def devpanel(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DevLoginModal())

    @app_commands.command(name="info", description="Live System Telemetry")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def info(self, interaction: discord.Interaction):
        uptime = round((time.time() - start_time) / 3600, 2)
        embed = discord.Embed(title="💠 KLEIN PROTOCOL STATUS", color=0xff003c)
        embed.add_field(name="Ping", value=f"`{round(self.bot.latency*1000)}ms`")
        embed.add_field(name="Uptime", value=f"`{uptime}h`")
        embed.add_field(name="API Keys", value=f"`{len(groq_clients)}/10`")
        embed.set_footer(text="Abyssal Node Active")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setchannel", description="Authorize Klein to auto-reply to all messages here")
    @app_commands.default_permissions(administrator=True)
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def setchannel(self, interaction: discord.Interaction):
        conn.cursor().execute("REPLACE INTO active_channels (channel_id, guild_id) VALUES (?, ?)", (str(interaction.channel_id), str(interaction.guild_id)))
        conn.commit()
        await interaction.response.send_message(f"✅ Auto-chat **authorized** in <#{interaction.channel_id}>. Klein is now listening.")

    @app_commands.command(name="unsetchannel", description="Revoke Klein's auto-reply access here")
    @app_commands.default_permissions(administrator=True)
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def unsetchannel(self, interaction: discord.Interaction):
        conn.cursor().execute("DELETE FROM active_channels WHERE channel_id=?", (str(interaction.channel_id),))
        conn.commit()
        await interaction.response.send_message(f"🚫 Auto-chat **revoked** for <#{interaction.channel_id}>. Klein is returning to slumber.")

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))