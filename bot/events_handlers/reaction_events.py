from datetime import timedelta
from bot.utils import aware_utcnow


async def handle_reaction_add(reaction, user, bot):
    # Ignore reactions from the bot itself
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

    original_message = await reaction.message.channel.fetch_message(
        reaction.message.reference.message_id
    )

    if original_message.author == user:
        await reaction.message.delete()
    else:
        # If the user is not the original author, remove their reaction
        await reaction.remove(user)
