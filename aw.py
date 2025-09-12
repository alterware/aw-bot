import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from bot.ai.handle_request import DiscourseSummarizer
from bot.log import logger
from database import initialize_db

GUILD_ID = 1110531063161299074
BOT_LOG = 1112049391482703873
GENERAL_CHANNEL = 1110531063744303138
OFFTOPIC_CHANNEL = 1112048063448617142

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Load environment variables from .env file (if it exists)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

build_date = os.getenv("BUILD_DATE")
git_tag = os.getenv("GIT_TAG")

initialize_db()

bot.ai_helper = DiscourseSummarizer()


@bot.event
async def on_ready():
    # Print build info if available
    if build_date and git_tag:
        logger.info(f"AlterWare Bot - Built on {build_date} {git_tag}")

    logger.info(f"{bot.user.name} has connected to Discord!")

    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        logger.info("Slash commands synchronized!")
    except Exception as e:
        logger.error("Failed to sync commands: %s", e)

    # Load extensions asynchronously
    await bot.load_extension("bot.tasks")
    await bot.load_extension("bot.events")
    await bot.load_extension("bot.commands")


bot.run(os.getenv("BOT_TOKEN"), log_handler=None)
