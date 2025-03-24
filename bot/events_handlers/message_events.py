from datetime import timedelta
import re
import discord

from bot.utils import timeout_member, aware_utcnow
from bot.config import message_patterns

from database import add_user_to_role

BOT_LOG = 1112049391482703873

CRAZY_USER_ID = 1319364607487512658
CRAZY_URL = "https://cdn.discordapp.com/attachments/1119371841711112314/1329770453744746559/download.png"
crazy_last_response_time = None

ALLOWED_CHANNELS = [
    1110531063744303138,  # GENERAL_CHANNEL
    1145458108190163014,  # mw2 general
    1145456435518525611,  # mw2 mp
    1112016681880014928,  # mw2 sp
    1200082418481250374,  # mw2 dev
    1145459504436220014,  # iw5 support
    1145469136919613551,  # s1 general
    1145459788151537804,  # s1 support
    1145469106133401682,  # iw6 general
    1145458770122649691,  # iw6 support
    1180796251529293844,  # bo3 general
    1180796301953212537,  # bo3 support
    BOT_LOG,
]

SPAM_ROLE_ID = 1350511935677927514


async def handle_dm(message):
    await message.channel.send(
        "If you DM this bot again, I will carpet-bomb your house."
    )


async def is_message_a_duplicate(message):
    guild = message.guild
    for channel in guild.text_channels:
        if channel.id == message.channel.id:
            continue

        try:
            async for msg in channel.history(limit=5):
                # Too many false positives
                if msg.embeds:
                    continue
                # ^^
                if message.attachments:
                    continue
                # ^^
                if not message.content.strip():
                    continue

                if msg.author == message.author and msg.content == message.content:
                    current_time = aware_utcnow()
                    message_time = msg.created_at

                    time_difference = current_time - message_time
                    if time_difference >= timedelta(minutes=5):
                        print(
                            f"Message is probably not a duplicate. Time difference: {time_difference}"
                        )
                        continue

                    await message.channel.send(
                        f"Hey {message.author.name}, you've already sent this message in {channel.mention}!"
                    )
                    member = message.guild.get_member(message.author.id)
                    await timeout_member(member)
                    return
        except discord.Forbidden:
            print(f"Bot does not have permission to read messages in {channel.name}.")
        except discord.HTTPException as e:
            print(f"An error occurred: {e}")


async def was_message_replied_by_bot(message, bot):
    """
    Checks if a deleted message was replied to by a later message from the bot.

    Args:
        message (discord.Message): The deleted message.
        bot (discord.Client): The bot instance.

    Returns:
        discord.Message or None: The bot's reply message if it exists, otherwise None.
    """
    async for later_message in message.channel.history(after=message.created_at):
        if later_message.reference and later_message.reference.message_id == message.id:
            if later_message.author == bot.user:
                return later_message
    return None


async def detect_ghost_ping(message, bot):
    if not message.mentions:
        return

    channel = bot.get_channel(BOT_LOG)
    if not channel:
        return

    embed = discord.Embed(
        title="Ghost Ping",
        description="A ghost ping was detected.",
        color=0xDD2E44,
    )
    embed.add_field(name="Author", value=message.author.mention, inline=True)  # noqa
    embed.add_field(name="Channel", value=message.channel.mention, inline=True)  # noqa

    mentioned_users = ", ".join([user.name for user in message.mentions])
    embed.add_field(
        name="Mentions",
        value=f"The message deleted by {message.author} mentioned: {mentioned_users}",  # noqa
        inline=False,
    )  # noqa

    embed.set_footer(text=f"Message ID: {message.id} | Author ID: {message.author.id}")

    await channel.send(embed=embed)


async def detect_ghost_ping_in_edit(before, after, bot):
    before_mentions = set(before.mentions)
    after_mentions = set(after.mentions)

    if before_mentions == after_mentions:
        return

    added_mentions = after_mentions - before_mentions
    removed_mentions = before_mentions - after_mentions

    response = "The mentions in the message have been edited.\n"
    if added_mentions:
        response += f"Added mentions: {', '.join(user.name for user in added_mentions)}\n"  # noqa
    if removed_mentions:
        response += f"Removed mentions: {', '.join(user.name for user in removed_mentions)}"  # noqa

    channel = bot.get_channel(BOT_LOG)
    if not channel:
        return

    embed = discord.Embed(
        title="Ghost Ping",
        description="A ghost ping was detected.",
        color=0xDD2E44,
    )
    embed.add_field(name="Author", value=before.author.mention, inline=True)  # noqa
    embed.add_field(name="Channel", value=before.channel.mention, inline=True)  # noqa

    embed.add_field(
        name="Mentions",
        value=response,
        inline=False,
    )  # noqa

    embed.set_footer(text=f"Message ID: {before.id} | Author ID: {before.author.id}")

    await channel.send(embed=embed)


async def handle_message_edit(before, after, bot):
    channel = bot.get_channel(BOT_LOG)
    if not channel:
        return

    if not before.content:
        return

    if after.content and after.content == before.content:
        return

    embed = discord.Embed(
        title="Edited Message",
        description="A message was edited.",
        color=0xDD2E44,
    )
    embed.add_field(name="Author", value=before.author.mention, inline=True)  # noqa
    embed.add_field(name="Channel", value=before.channel.mention, inline=True)  # noqa
    embed.add_field(name="Content", value=before.content, inline=False)  # noqa
    embed.set_footer(text=f"Message ID: {before.id} | Author ID: {before.author.id}")

    await channel.send(embed=embed)
    await detect_ghost_ping_in_edit(before, after, bot)


async def handle_bulk_message_delete(messages, bot):
    channel = bot.get_channel(BOT_LOG)
    if not channel:
        return

    for message in messages:
        embed = discord.Embed(
            title="Deleted Message",
            description="A message was deleted.",
            color=0xDD2E44,
        )
        embed.add_field(
            name="Author", value=message.author.mention, inline=True
        )  # noqa
        embed.add_field(
            name="Channel", value=message.channel.mention, inline=True
        )  # noqa
        if message.content:
            embed.add_field(name="Content", value=message.content, inline=False)  # noqa
        embed.set_footer(
            text=f"Message ID: {message.id} | Author ID: {message.author.id}"  # noqa
        )

        await channel.send(embed=embed)


async def handle_message_delete(message, bot):
    channel = bot.get_channel(BOT_LOG)
    if not channel:
        return

    is_bot = message.author == bot.user
    if is_bot and message.channel.id != BOT_LOG:
        return

    if is_bot:
        await message.channel.send(
            "You attempted to delete a message from a channel where messages are logged and stored indefinitely. Please refrain from doing so."  # noqa
        )  # noqa
        # It is impossible to recover the message at this point
        return

    embed = discord.Embed(
        title="Deleted Message",
        description="A message was deleted.",
        color=0xDD2E44,
    )
    embed.add_field(name="Author", value=message.author.mention, inline=True)  # noqa
    embed.add_field(name="Channel", value=message.channel.mention, inline=True)  # noqa
    if message.content:
        embed.add_field(name="Content", value=message.content, inline=False)  # noqa

    if message.reference is not None:
        original_message = await message.channel.fetch_message(
            message.reference.message_id
        )

        embed.add_field(
            name="Replied",
            value=original_message.author.mention,
            inline=False,  # noqa
        )  # noqa

    embed.set_footer(
        text=f"Message ID: {message.id} | Author ID: {message.author.id}"  # noqa
    )  # noqa

    await channel.send(embed=embed)
    await detect_ghost_ping(message, bot)

    bot_reply = await was_message_replied_by_bot(message, bot)
    if bot_reply:
        await message.channel.send(
            f"{message.author.mention} I thought we had something special going on, why did you delete your message?"
        )


async def handle_message(message, bot):
    global crazy_last_response_time

    if message.author == bot.user:
        return

    if message.guild is None:
        await handle_dm(message)
        return

    # Too many mentions
    if len(message.mentions) >= 3:
        member = message.guild.get_member(message.author.id)
        await timeout_member(member, timedelta(minutes=5), "Spamming mentions")
        await message.delete()
        return

    if "@everyone" in message.content or "@here" in message.content:
        if not message.channel.permissions_for(message.author).mention_everyone:
            spam_role = message.guild.get_role(SPAM_ROLE_ID)
            member = message.guild.get_member(message.author.id)

            # Check if the member already has the spam role
            if spam_role not in member.roles:
                await member.add_roles(spam_role)

                # Add the user to the database
                add_user_to_role(member.id, SPAM_ROLE_ID)

            await message.reply(
                f"Dink Donk! Time to ping everyone! {spam_role.mention}",
                mention_author=True,
            )

            await timeout_member(member, timedelta(minutes=5), "Spamming mentions")
            return

    # Auto delete torrent if post in chat.
    for file in message.attachments:
        if file.filename.endswith((".torrent", ".TORRENT")):
            member = message.guild.get_member(message.author.id)
            await timeout_member(member, timedelta(minutes=120), "Torrents")
            await message.delete()
            return

    if message.author.id == CRAZY_USER_ID:
        now = aware_utcnow()
        if (
            crazy_last_response_time is None
            or now - crazy_last_response_time >= timedelta(hours=8)
        ):
            crazy_last_response_time = now
            await message.channel.send(f"{CRAZY_URL}")
            return

    await is_message_a_duplicate(message)

    # Check if the message is in an allowed channel
    if message.channel.id not in ALLOWED_CHANNELS:
        return

    # Check if any of the patterns match the message
    # print('Checking for patterns...')
    for pattern in message_patterns:
        if re.search(pattern["regex"], message.content, re.IGNORECASE):
            response = pattern["response"]
            reply_message = await message.reply(response, mention_author=True)
            await reply_message.add_reaction("\U0000274C")
            break
