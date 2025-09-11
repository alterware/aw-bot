from datetime import timedelta

from bot.utils import aware_utcnow
from bot.log import logger

import discord


async def handle_reaction_add(reaction, user, bot):
    if user == bot.user:
        return

    if reaction.emoji != "\U0000274c":
        return

    if reaction.message.author != bot.user:
        return

    current_time = aware_utcnow()
    time_difference = current_time - reaction.message.created_at
    if time_difference >= timedelta(minutes=5):
        return

    if reaction.message.reference is None:
        return

    try:
        original_message = await reaction.message.channel.fetch_message(
            reaction.message.reference.message_id
        )
    except discord.NotFound:
        logger.error(
            "Error while trying to fetch message: referenced message was deleted or unavailable"
        )
        return
    except discord.Forbidden:
        logger.error(
            "Error while trying to fetch message: Bot doesn't have permissions to read that message/channel"
        )
        return

    if original_message.author == user:
        await reaction.message.delete()
    else:
        await reaction.remove(user)
