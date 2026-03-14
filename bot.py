import discord
from discord.ext import commands
import os
from bot_keepalive import keep_alive
from bot_database import init_db

class KleinBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="k!", intents=discord.Intents.all(), help_command=None)

    async def setup_hook(self):
        init_db() # Ensure database tables exist
        await self.load_extension("bot_commands")
        await self.load_extension("bot_events")
        await self.tree.sync()
        print("✅ [SYSTEM] Klein Omni-Core Synced and Ready.")

# Start the Web Dashboard
keep_alive()

# Boot the Bot
bot = KleinBot()
bot.run(os.environ.get("DISCORD_TOKEN"))