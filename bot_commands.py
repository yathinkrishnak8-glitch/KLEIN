import discord
from discord.ext import commands
from discord import app_commands
import asyncio, time, random, re
from bot_database import update_config, conn
from bot_ai import groq_clients, robust_api_call
from bot_keepalive import bot_stats, start_time

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 🧠 AI GENERATORS ---
    async def generate_prank_data(self, prank_type, target_name):
        """Uses the AI to generate edgy, randomized prank content."""
        if prank_type == "target":
            prompt = f"Generate 4 edgy and funny 'tactical actions' for a prank on {target_name}. Examples: 'Notifying local cartel', 'Sending search history to local church'. Make them unique and dark-humored. Also provide a fake IP and 18-digit Network ID."
        else:
            prompt = f"Generate 4 highly embarrassing and edgy search history items for {target_name}. Make them cringey and funny. Also provide a fake OS and GPU name."
        
        # We use a lower temperature for 'realism' and a fast model
        response, _ = await robust_api_call([{"role": "system", "content": "You are a rogue hacker AI. Output your response as a simple list."}, {"role": "user", "content": prompt}], "llama-3.1-8b-instant", temperature=0.9)
        
        # Clean the response into a list
        items = [line.strip("- ").strip("1234. ") for line in response.split("\n") if len(line.strip()) > 5]
        return items if len(items) >= 4 else None

    # --- 🛠️ SYSTEM COMMANDS ---
    @app_commands.command(name="info", description="Live System Telemetry")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def info(self, interaction: discord.Interaction):
        uptime = round((time.time() - start_time) / 3600, 2)
        embed = discord.Embed(title="💠 KLEIN PROTOCOL STATUS", color=0xff003c)
        embed.add_field(name="Latency", value=f"`{round(self.bot.latency*1000)}ms`")
        embed.add_field(name="API Nodes", value=f"`{len(groq_clients)}/10` Active")
        embed.set_footer(text="Abyssal Node | Fallen Angel Architecture")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setchannel", description="Authorize auto-chat in this channel")
    @app_commands.default_permissions(administrator=True)
    async def setchannel(self, interaction: discord.Interaction):
        conn.cursor().execute("REPLACE INTO active_channels (channel_id, guild_id) VALUES (?, ?)", (str(interaction.channel_id), str(interaction.guild_id)))
        conn.commit()
        await interaction.response.send_message(f"✅ **Klein is now listening.** Auto-chat authorized for <#{interaction.channel_id}>.")

    # --- 🎭 AI-DRIVEN HQ PRANKS ---
    @app_commands.command(name="target", description="[PRANK] Lock orbital strike and dox via AI")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def target(self, interaction: discord.Interaction, target: discord.User):
        await interaction.response.send_message(f"🛰️ `[SATELLITE LINK]` Triangulating cellular signal for {target.mention}...")
        
        # Generate dynamic data via AI
        ai_data = await self.generate_prank_data("target", target.name)
        
        # Fallback if AI is slow
        actions = ai_data[:4] if ai_data else ["Notifying local cartel...", "Activating web-camera...", "Leaking DMs...", "Rerouting IP..."]
        spoof_ip = f"{random.randint(11, 199)}.{random.randint(10, 255)}.***.***"
        spoof_id = f"{random.randint(700, 999)}{random.randint(100, 999)}{random.randint(100, 999)}{random.randint(100, 999)}{random.randint(100, 999)}"
        
        embed = discord.Embed(title="⚠️ TARGET ACQUIRED ⚠️", color=0xff0000)
        embed.add_field(name="👤 Target Identity", value=f"**Username:** {target.name}\n**Network ID:**\n`{spoof_id}`", inline=False)
        embed.add_field(name="🌐 Trace Route", value=f"**IP Address:** `{spoof_ip}`\n**Status:** Intercepted", inline=False)
        embed.add_field(name="🚀 Tactical Actions Deployed", value="\n".join([f"✅ {a}" for a in actions]), inline=False)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await asyncio.sleep(1.5)
        await interaction.edit_original_response(content=None, embed=embed)

    @app_commands.command(name="hack", description="[PRANK] AI-generated deep-web breach")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def hack(self, interaction: discord.Interaction, target: discord.User):
        await interaction.response.send_message(f"📡 `[UPLINK]` Bypassing Cloudflare layers for {target.mention}...")
        
        ai_data = await self.generate_prank_data("hack", target.name)
        history = ai_data[:4] if ai_data else ["Why do I have 0 rizz?", "How to get free Nitro", "Is 5'4 tall?", "Roblox aimbot download"]

        embed = discord.Embed(title="🛑 DATA BREACH SECURED", description=f"Extracted logs for **{target.name}**:", color=0xff003c)
        embed.add_field(name="🖥️ Device Fingerprint", value=f"**OS:** Windows 11 Pro\n**GPU:** RTX 4090\n**Camera:** `[ACTIVE]`", inline=False)
        embed.add_field(name="🔍 Private Search Logs (AI Scanned)", value="\n".join([f"🔎 *{s}*" for s in history]), inline=False)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"Klein Cyber-Sec | Node: {random.randint(10,99)}")
        
        await asyncio.sleep(2)
        await interaction.edit_original_response(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))