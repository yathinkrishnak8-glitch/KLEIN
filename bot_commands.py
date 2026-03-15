import discord
from discord.ext import commands
from discord import app_commands
import asyncio, time
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

    # --- 🎭 HQ REALISTIC PRANK SUITE ---
    @app_commands.command(name="hack", description="[PRANK] Simulate a highly realistic deep-web breach on a user")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def hack(self, interaction: discord.Interaction, target: discord.User):
        await interaction.response.send_message(f"📡 `[UPLINK ESTABLISHED]` Bypassing Cloudflare protocols for {target.mention}...")
        await asyncio.sleep(2)
        await interaction.edit_original_response(content=f"🔓 `[FIREWALL BREACHED]` Extracting local browser cache from {target.name}'s IPv6 address...")
        await asyncio.sleep(2)
        await interaction.edit_original_response(content=f"📂 `[DECRYPTING PACKETS]` Found 4 hidden folders. Uploading to public mainframe...")
        await asyncio.sleep(2.5)
        history = [
            "How to get free V-Bucks no scam 2026", 
            "Why do I have 0 rizz?", 
            "Is it illegal to use aimbot in Roblox?",
            "How to talk to girls (WikiHow)"
        ]
        embed = discord.Embed(title="🛑 DATA BREACH SECURED", description=f"Extracted search logs for **{target.name}**:", color=0xff003c)
        embed.add_field(name="Private Browser History", value="\n".join([f"🔍 *{s}*" for s in history]))
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Klein Cyber-Sec Unit")
        await interaction.edit_original_response(content=None, embed=embed)

    @app_commands.command(name="target", description="[PRANK] Lock an orbital strike onto a user")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def target(self, interaction: discord.Interaction, target: discord.User):
        await interaction.response.send_message(f"🛰️ `[SATELLITE LINK]` Triangulating cellular signal for {target.mention}...")
        await asyncio.sleep(2)
        await interaction.edit_original_response(content=f"🎯 `[LOCK ACQUIRED]` Coordinates locked. Routing targeting data through proxy mesh...")
        await asyncio.sleep(2)
        embed = discord.Embed(title="⚠️ TACTICAL STRIKE IMMINENT", description=f"Orbital payload aligned on **{target.name}**.", color=0xff0000)
        embed.add_field(name="Status", value="Payload dropped. Impact in 3... 2... 1...")
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.edit_original_response(content=None, embed=embed)
        await asyncio.sleep(3)
        
        embed.color = 0x555555
        embed.title = "❌ STRIKE ABORTED"
        embed.description = f"Orbital strike on **{target.name}** failed."
        embed.clear_fields()
        embed.add_field(name="Error Log", value="Target was actively playing Roblox. Strike aborted out of pity.")
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="nuke", description="[PRANK] Simulate a highly destructive server wipe")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def nuke(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"☢️ `[SYSTEM WARNING]` Abyssal Nuke sequence initiated by {interaction.user.mention}.")
        await asyncio.sleep(2)
        await interaction.edit_original_response(content="🔥 `[OVERRIDE]` Bypassing Discord API rate limits... Preparing to delete all channels.")
        await asyncio.sleep(2.5)
        await interaction.edit_original_response(content="💀 `[CRITICAL]` Injecting payload. Say goodbye to the server in 3 seconds.")
        await asyncio.sleep(3)
        
        embed = discord.Embed(title="🛡️ NUKE FAILED", description="Klein's mom said he has to go to bed. Server spared.", color=0x00ff00)
        await interaction.edit_original_response(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))