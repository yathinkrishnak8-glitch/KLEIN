import discord
from discord.ext import commands, tasks
import os
import random
import warnings

# Import our custom modules
from bot_keepalive import keep_alive
from bot_database import init_db, get_config
from bot_utils import send_dev_log

warnings.filterwarnings("ignore")
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

# We use commands.Bot to support our modular Cog system
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def setup_hook():
    init_db()
    # Load our separate files (Cogs)
    await bot.load_extension("bot_commands")
    await bot.load_extension("bot_events")
    await bot.tree.sync()
    status_task.start()
    print(f"Logged in as {bot.user} | Modular Engine Loaded Successfully")

@tasks.loop(minutes=15)
async def status_task():
    statuses = [
        discord.Activity(type=discord.ActivityType.watching, name="Modular Data Streams"),
        discord.Game(name="with Python Cogs"),
        discord.Activity(type=discord.ActivityType.listening, name="background processes"),
        discord.Game(name="with LLaMA 3.3"),
    ]
    await bot.change_presence(activity=random.choice(statuses))

@status_task.before_loop
async def before_status_task():
    await bot.wait_until_ready()

# --- GLOBAL ERROR & TOGGLE CHECKS ---
@bot.tree.interaction_check
async def check_toggles(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.application_command:
        cmd_name = interaction.command.name
        guild_id = interaction.guild_id or interaction.user.id
        if cmd_name in ["toggle", "purge", "lockdown", "unlock"]: return True
        toggles, _, _, _ = get_config(guild_id)
        if cmd_name in toggles and not toggles[cmd_name]:
            await interaction.response.send_message(f"🔴 Access Denied. `/{cmd_name}` is disabled.", ephemeral=True)
            return False
    return True

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    err_msg = f"❌ **System Error:** Command execution failed."
    try:
        if interaction.response.is_done(): await interaction.followup.send(err_msg, ephemeral=True)
        else: await interaction.response.send_message(err_msg, ephemeral=True)
    except: pass
    await send_dev_log(bot, interaction.guild_id, str(error))

# Start Flask server and connect to Discord
keep_alive()
bot.run(DISCORD_TOKEN)
