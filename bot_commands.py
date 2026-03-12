import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import json
import time
from duckduckgo_search import DDGS
from bot_database import get_config, update_config, conn
from bot_ai import groq_client
from bot_keepalive import bot_stats, start_time

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="info", description="View digital system status terminal")
    async def info(self, interaction: discord.Interaction):
        await interaction.response.defer()
        ping = round(self.bot.latency * 1000)
        uptime_hrs = round((time.time() - start_time) / 3600, 2)
        members = interaction.guild.member_count if interaction.guild else "N/A"
        _, current_personality, _, current_model = get_config(interaction.guild_id or interaction.user.id)
        active_persona = current_personality if current_personality else "Default AI (Klein)"
        
        embed = discord.Embed(title="💠 GROQ TERMINAL :: MODULAR CORE", color=0xFF5500)
        embed.add_field(name="📡 Status", value=f"🟢 Online\n**Ping:** `{ping}ms`\n**Uptime:** `{uptime_hrs}h`", inline=True)
        embed.add_field(name="👥 Network", value=f"**Members:** `{members}`\n**Messages:** `{bot_stats['messages_processed']}`", inline=True)
        embed.add_field(name="🧠 Core Engine", value=f"**Model:** `{current_model}`\n**Mode:** `Silent Intelligence`", inline=False)
        embed.add_field(name="🎭 Personality", value=f"> *{active_persona}*", inline=False)
        embed.set_footer(text="⚙️ Built by yathin | Modular Architecture")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="target", description="[PRANK] Acquire target details and deploy tactical countermeasures")
    async def target(self, interaction: discord.Interaction, target_user: discord.Member):
        await interaction.response.defer()
        
        # Generates a fake, blurred IP
        fake_ip = f"{random.randint(11, 215)}.{random.randint(10, 250)}.***.***"
        
        embed = discord.Embed(title="⚠️ TARGET ACQUIRED ⚠️", color=0xFF0000)
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.add_field(name="👤 Target Identity", value=f"**Username:** {target_user.name}\n**Network ID:** `{target_user.id}`", inline=False)
        embed.add_field(name="🌐 Trace Route", value=f"**Locating Node...**\n**IP Address:** `{fake_ip}`\n**Status:** Intercepted", inline=False)
        embed.add_field(name="🚀 Tactical Actions Deployed", value=
            "✅ Miscalled Jeffrey Epstein\n✅ B-2 Stealth Bombers Airborne\n✅ Calling SpaceX Orbital Strike Command\n✅ History sent to authorities", inline=False)
        embed.set_footer(text="OPERATION: DARKFALL | Secure Terminal")
        
        # Developer Touch: Hacker Loading Animation
        msg = await interaction.followup.send("`[SYSTEM]: Establishing secure connection...`")
        await asyncio.sleep(1.5)
        await msg.edit(content="`[SYSTEM]: Bypassing firewall...`")
        await asyncio.sleep(1.5)
        await msg.edit(content=None, embed=embed)

    @app_commands.command(name="changemodel", description="Switch the active Groq AI model")
    @app_commands.choices(model_name=[
        app_commands.Choice(name="LLaMA 3.3 70B (Max Intelligence)", value="llama-3.3-70b-versatile"),
        app_commands.Choice(name="LLaMA 3.1 8B (Max Speed)", value="llama-3.1-8b-instant")
    ])
    async def change_model(self, interaction: discord.Interaction, model_name: app_commands.Choice[str]):
        await interaction.response.defer()
        update_config(interaction.guild_id, model=model_name.value)
        await interaction.followup.send(f"🔄 **Engine Switched:** Now using `{model_name.name}`.")

    @app_commands.command(name="search", description="Scrape the web for live facts")
    async def search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        _, _, _, current_model = get_config(interaction.guild_id)
        def perform_scrape():
            try: return list(DDGS().text(query, max_results=3))
            except: return []

        text_data = await asyncio.to_thread(perform_scrape)
        if not text_data: return await interaction.followup.send("❌ No live data found.")

        web_context = "\n".join([f"- {r['title']}: {r['body']}" for r in text_data])
        prompt = f"Query: {query}\n\nLive Data:\n{web_context}\n\nSummarize naturally."
        response = await groq_client.chat.completions.create(model=current_model, messages=[{"role": "user", "content": prompt}], temperature=0.5)
        await interaction.followup.send(f"🌐 **Search Results:** `{query}`\n\n{response.choices[0].message.content}")

    @app_commands.command(name="tldr", description="Summarize the last 50 messages")
    async def tldr(self, interaction: discord.Interaction):
        await interaction.response.defer()
        _, _, _, current_model = get_config(interaction.guild_id)
        messages = [msg async for msg in interaction.channel.history(limit=50)]
        messages.reverse() 
        chat_log = "\n".join([f"{m.author.name}: {m.content}" for m in messages if not m.author.bot])
        if len(chat_log) < 50: return await interaction.followup.send("Not enough chat history.")
        prompt = f"Summarize this chat log briefly using bullet points:\n\n{chat_log[-3000:]}"
        response = await groq_client.chat.completions.create(model=current_model, messages=[{"role": "user", "content": prompt}], temperature=0.5)
        await interaction.followup.send(f"📜 **Channel TL;DR:**\n{response.choices[0].message.content}")

    @app_commands.command(name="toggle", description="[ADMIN] Turn any bot command ON or OFF")
    @app_commands.default_permissions(administrator=True)
    async def toggle_cmd(self, interaction: discord.Interaction, command_name: str):
        await interaction.response.defer()
        cmd = command_name.lower()
        toggles, _, _, _ = get_config(interaction.guild_id)
        if cmd not in toggles: return await interaction.followup.send(f"⚠️ `{cmd}` is not a valid feature.")
        toggles[cmd] = not toggles[cmd]
        update_config(interaction.guild_id, toggles=toggles)
        status = "🟢 **ENABLED**" if toggles[cmd] else "🔴 **DISABLED**"
        await interaction.followup.send(f"Master Switch: `{cmd}` updated to {status}.")

    @app_commands.command(name="setdevlog", description="[ADMIN] Set error log channel")
    @app_commands.default_permissions(administrator=True)
    async def setdevlog(self, interaction: discord.Interaction):
        await interaction.response.defer()
        update_config(interaction.guild_id, dev_channel=str(interaction.channel_id))
        await interaction.followup.send("🛠️ Dev-Log channel locked.")

    @app_commands.command(name="purge", description="[ADMIN] Bulk delete messages")
    @app_commands.default_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 Purged {len(deleted)} messages.", ephemeral=True)

    @app_commands.command(name="setchannel", description="Bot talks here automatically")
    async def set_channel(self, interaction: discord.Interaction):
        await interaction.response.defer()
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO active_channels (channel_id, guild_id) VALUES (?, ?)", (str(interaction.channel_id), str(interaction.guild_id)))
        conn.commit()
        await interaction.followup.send(f"👀 Monitoring #{interaction.channel.name}.")

    @app_commands.command(name="unsetchannel", description="Stop auto-talking")
    async def unset_channel(self, interaction: discord.Interaction):
        await interaction.response.defer()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM active_channels WHERE channel_id=?", (str(interaction.channel_id),))
        conn.commit()
        await interaction.followup.send("🛑 Stopped monitoring.")

    @app_commands.command(name="clearmemory", description="Wipe conversation history")
    async def clear_memory(self, interaction: discord.Interaction):
        await interaction.response.defer()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_memory WHERE channel_id=?", (str(interaction.channel_id),))
        conn.commit()
        await interaction.followup.send("🧠 Memory wiped.")

    @app_commands.command(name="personality", description="Set bot persona (Type 'default' to reset)")
    async def set_personality(self, interaction: discord.Interaction, bio: str):
        await interaction.response.defer()
        guild_id = interaction.guild_id or interaction.user.id
        if bio.strip().lower() == "default":
            update_config(guild_id, personality="")
            await interaction.followup.send("🧠 Restored default Klein persona.")
        else:
            update_config(guild_id, personality=bio)
            await interaction.followup.send(f"🎭 **Persona Updated:** Your bot will now act like: `{bio}`")

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))


