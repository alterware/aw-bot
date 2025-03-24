from dotenv import load_dotenv
import os

import discord
from discord.ext import commands

from database import initialize_db

GUILD_ID = 1110531063161299074
BOT_LOG = 1112049391482703873
GENERAL_CHANNEL = 1110531063744303138
OFFTOPIC_CHANNEL = 1112048063448617142

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Load environment variables from .env file (if it exists)
load_dotenv(override=True)

initialize_db()


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("Slash commands synchronized!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Load extensions asynchronously
    await bot.load_extension("bot.tasks")
    await bot.load_extension("bot.events")
    await bot.load_extension("bot.commands")


bot.run(os.getenv("BOT_TOKEN"))
