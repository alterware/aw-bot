from datetime import timedelta
import discord
import time

from bot.utils import timeout_member, aware_utcnow
from bot.ai.handle_request import forward_to_google_api

from database import add_user_to_role

BOT_LOG = 1112049391482703873
GENERAL_CHANNEL = 1110531063744303138
FAILED_EMBED_MESSAGE = "https://cdn.discordapp.com/attachments/1112049391482703873/1375848830175547482/download_3.png"

CRAZY_USER_ID = 1319364607487512658
CRAZY_URL = "https://cdn.discordapp.com/attachments/1119371841711112314/1329770453744746559/download.png"
crazy_last_response_time = None

HATE_ME_USER_ID = 748201351665680438
HATE_ME_URL = "https://cdn.discordapp.com/attachments/1160511084143312959/1361051561400205524/download_1.png"
hate_me_last_response_time = None

SPAM_ROLE_ID = 1350511935677927514
ADMIN_ROLE_ID = 1112364483915042908
GROK_ROLE_ID = 1362837967919386916

ALLOWED_CHANNELS = [
    1112048063448617142,  # off-topic
    1119371841711112314,  # vip-channel
]

# Cooldown: user_id -> [timestamps]
MENTION_COOLDOWNS = {}


def fetch_image_from_message(message):
    image_object = None
    for attachment in message.attachments:
        if attachment.filename.lower().endswith(
            ".jpg"
        ) or attachment.filename.lower().endswith(".jpeg"):
            image_object = (attachment.url, "image/jpeg")
            break
        elif attachment.filename.lower().endswith(".png"):
            image_object = (attachment.url, "image/png")
            break
    return image_object


async def handle_bot_mention(message, bot, no_context=False):
    staff_role = message.guild.get_role(ADMIN_ROLE_ID)
    member = message.guild.get_member(message.author.id)

    # Check if the message is in an allowed channel
    if message.channel.id not in ALLOWED_CHANNELS:
        await message.reply(
            "The AI cannot used in this channel.",
            mention_author=True,
        )
        return True

    # Cooldown logic: max 1 use per minute per user
    now = time.time()
    user_id = message.author.id
    timestamps = MENTION_COOLDOWNS.get(user_id, [])
    # Remove timestamps older than 60 seconds
    timestamps = [t for t in timestamps if now - t < 60]
    if len(timestamps) >= 1 and not staff_role in member.roles:
        await message.reply(
            "You are using this feature too quickly. Please wait before trying again.",
            mention_author=True,
        )
        return True
    timestamps.append(now)
    MENTION_COOLDOWNS[user_id] = timestamps

    # Prioritize the image object from the first message
    image_object = fetch_image_from_message(message)

    # Check if the message is a reply to another message
    reply_content = None
    if message.reference:
        try:
            referenced_message = await message.channel.fetch_message(
                message.reference.message_id
            )
            reply_content = referenced_message

            # Check if the referenced message has an image object (if not already set)
            if image_object is None:
                image_object = fetch_image_from_message(referenced_message)

        except discord.NotFound:
            print("Referenced message not found.")
        except discord.Forbidden:
            print("Bot does not have permission to fetch the referenced message.")
        except discord.HTTPException as e:
            print(f"An error occurred while fetching the referenced message: {e}")

    # Pass the reply content to forward_to_google_api
    await forward_to_google_api(message, bot, image_object, reply_content, no_context)
    return True


async def handle_dm(message):
    await message.channel.send(
        "If you DM this bot again, I will carpet-bomb your house."
    )


async def handle_crazy(message):
    global crazy_last_response_time

    if message.author.id == CRAZY_USER_ID:
        now = aware_utcnow()
        if (
            crazy_last_response_time is None
            or now - crazy_last_response_time >= timedelta(hours=8)
        ):
            crazy_last_response_time = now
            await message.channel.send(f"{CRAZY_URL}")
            return True

    return False


async def handle_hate_me(message):
    global hate_me_last_response_time

    if message.author.id == HATE_ME_USER_ID:
        now = aware_utcnow()
        if (
            hate_me_last_response_time is None
            or now - hate_me_last_response_time >= timedelta(hours=8)
        ):
            hate_me_last_response_time = now
            await message.channel.send(f"{HATE_ME_URL}")
            return True

    return False


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
    if message.author == bot.user:
        return

    if message.guild is None:
        await handle_dm(message)
        return

    grok_role = message.guild.get_role(GROK_ROLE_ID)
    if grok_role in message.role_mentions:
        if await handle_bot_mention(message, bot, True):
            return

    if bot.user in message.mentions:
        if await handle_bot_mention(message, bot):
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
                add_user_to_role(member.id, SPAM_ROLE_ID, member.name)

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

    if await handle_crazy(message):
        return

    if await handle_hate_me(message):
        return

    await is_message_a_duplicate(message)

    if (
        "http" in message.content
        and not message.embeds
        and message.channel.id == GENERAL_CHANNEL
    ):
        await message.reply(FAILED_EMBED_MESSAGE)
        return
