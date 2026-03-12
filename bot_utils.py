import discord
from datetime import datetime
from bot_database import get_config

async def send_dev_log(bot, guild_id, error_message, severity="ERROR"):
    _, _, dev_chan_id, _ = get_config(guild_id)
    if dev_chan_id:
        channel = bot.get_channel(int(dev_chan_id))
        if channel:
            embed = discord.Embed(title=f"⚠️ System {severity}", color=0xFF0000)
            # Slicing the error message to ensure it doesn't exceed Discord's embed limits
            error_text = str(error_message)[:3900]
            embed.description = f"```python\n{error_text}\n```"
            embed.timestamp = datetime.utcnow()
            await channel.send(embed=embed)
