import json
import os
import random
import re
from datetime import datetime, timedelta, timezone
from typing import Literal

import discord
import requests
from discord import app_commands
from discord.ext import commands, tasks

GUILD_ID = 1110531063161299074
BOT_LOG = 1112049391482703873
GENERAL_CHANNEL = 1110531063744303138
OFFTOPIC_CHANNEL = 1112048063448617142

CRAZY_USER_ID = 1319364607487512658
CRAZY_URL = "https://cdn.discordapp.com/attachments/1119371841711112314/1329770453744746559/download.png"
crazy_last_response_time = None

TARGET_DATE = datetime(2036, 8, 12, tzinfo=timezone.utc)

# Define the channel IDs where auto responds are allowed
ALLOWED_CHANNELS = [
    GENERAL_CHANNEL,
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

# Load existing patterns from file
try:
    with open("patterns.json", "r") as f:
        patterns = json.load(f)
except FileNotFoundError:
    patterns = []

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
tree = bot.tree


def aware_utcnow():
    return datetime.now(timezone.utc)


def fetch_api_data():
    response = requests.get("https://api.getserve.rs/v1/servers/alterware")
    if response.status_code == 200:
        return response.json()
    return {}


async def fetch_game_stats(game: str):
    url = f"https://api.getserve.rs/v1/servers/alterware/{game}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None


async def compile_stats():
    games = ["iw4", "s1", "iw6"]
    stats_message = "**Stats for all games:**\n"
    for game in games:
        data = await fetch_game_stats(game)
        if data:
            count_servers = data.get("countServers", "N/A")
            count_players = data.get("countPlayers", "N/A")
            stats_message += f"**{game.upper()}:** Total Servers: {count_servers}, Total Players: {count_players}\n"  # noqa
        else:
            stats_message += f"**{game.upper()}:** Failed to fetch stats.\n"
    return stats_message


async def perform_search(query: str):
    data = fetch_api_data()
    servers = data.get("servers", [])
    matching_servers = [
        server
        for server in servers
        if query.lower() in server.get("hostnameDisplay", "").lower()
        or query.lower() in server.get("ip", "").lower()
    ]

    if not matching_servers:
        return "No servers found matching your query."

    max_results = 5
    message = f'Top {min(len(matching_servers), max_results)} servers matching "{query}":\n'  # noqa
    for server in matching_servers[:max_results]:
        message += (
            f"- **{server['hostnameDisplay']}** | {server['gameDisplay']} | "
            f"**Gametype**: {server['gametypeDisplay']} | **Map**: {server['mapDisplay']} | "  # noqa
            f"**Players**: {server['realClients']}/{server['maxplayers']}\n"
        )
    return message


@tree.command(
    name="search",
    description="Search for servers by hostname or IP.",
    guild=discord.Object(id=GUILD_ID),
)
async def slash_search(interaction: discord.Interaction, query: str):
    results = await perform_search(query)
    await interaction.response.send_message(results)


@app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id, i.user.id))
@tree.command(
    name="stats",
    description="Get stats for a specific game or all games",
    guild=discord.Object(id=GUILD_ID),
)
async def stats(
    interaction: discord.Interaction, game: Literal["iw4", "s1", "iw6", "all"]
):
    if game == "all":
        stats_message = await compile_stats()
    else:
        data = await fetch_game_stats(game)
        if data:
            stats_message = f"**Stats for {game.upper()}:**\n"
            count_servers = data.get("countServers", "N/A")
            count_players = data.get("countPlayers", "N/A")
            stats_message += f"Total Servers: {count_servers}\n"  # noqa
            stats_message += f"Total Players: {count_players}\n"  # noqa
        else:
            stats_message = (
                "Failed to fetch game stats. Please try again later."  # noqa
            )

    await interaction.response.send_message(stats_message, ephemeral=True)
    # await interaction.delete_original_response()


async def on_tree_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.CommandOnCooldown):
        return await interaction.response.send_message(
            f"Command is currently on cooldown! Try again in **{error.retry_after:.2f}** seconds!"  # noqa
        )
    elif isinstance(error, app_commands.MissingPermissions):
        return await interaction.response.send_message(
            "You are missing permissions to use that"
        )
    else:
        raise error


bot.tree.on_error = on_tree_error


async def detect_ghost_ping(message):
    if not message.mentions:
        return

    channel = bot.get_channel(BOT_LOG)
    if channel:
        embed = discord.Embed(
            title="Ghost Ping",
            description="A ghost ping was detected.",
            color=0xDD2E44,
        )
        embed.add_field(
            name="Author", value=message.author.mention, inline=True
        )  # noqa
        embed.add_field(
            name="Channel", value=message.channel.mention, inline=True
        )  # noqa

        mentioned_users = ", ".join([user.name for user in message.mentions])
        embed.add_field(
            name="Mentions",
            value=f"The message deleted by {message.author} mentioned: {mentioned_users}",  # noqa
            inline=False,
        )  # noqa

        embed.set_footer(
            text=f"Message ID: {message.id} | Author ID: {message.author.id}"
        )

        await channel.send(embed=embed)


async def detect_ghost_ping_in_edit(before, after):
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
    if channel:
        embed = discord.Embed(
            title="Ghost Ping",
            description="A ghost ping was detected.",
            color=0xDD2E44,
        )
        embed.add_field(name="Author", value=before.author.mention, inline=True)  # noqa
        embed.add_field(
            name="Channel", value=before.channel.mention, inline=True
        )  # noqa

        embed.add_field(
            name="Mentions",
            value=response,
            inline=False,
        )  # noqa

        embed.set_footer(
            text=f"Message ID: {before.id} | Author ID: {before.author.id}"
        )

        await channel.send(embed=embed)


@bot.event
async def on_message_delete(message):
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

    await detect_ghost_ping(message)
    await channel.send(embed=embed)


@bot.event
async def on_bulk_message_delete(messages):
    channel = bot.get_channel(BOT_LOG)
    if channel:
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
                embed.add_field(
                    name="Content", value=message.content, inline=False
                )  # noqa
            embed.set_footer(
                text=f"Message ID: {message.id} | Author ID: {message.author.id}"  # noqa
            )

            await channel.send(embed=embed)


@bot.event
async def on_message_edit(before, after):
    channel = bot.get_channel(BOT_LOG)
    if channel:
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
        embed.add_field(
            name="Channel", value=before.channel.mention, inline=True
        )  # noqa
        embed.add_field(name="Content", value=before.content, inline=False)  # noqa
        embed.set_footer(
            text=f"Message ID: {before.id} | Author ID: {before.author.id}"
        )

        await detect_ghost_ping_in_edit(before, after)
        await channel.send(embed=embed)


async def timeout_member(member):
    if not member:
        print("Debug: Member is None. Skipping timeout.")
        return

    try:
        # Debug: Print the member object and timeout duration
        print(f"Debug: Attempting to timeout member {member} (ID: {member.id}).")

        timeout_until = timedelta(minutes=1)
        print(f"Debug: Timeout duration set to {timeout_until}.")

        await member.timeout(timedelta(minutes=1), reason="Requested by the bot")
        print(f"Debug: Successfully timed out {member}.")

    except discord.Forbidden:
        print(f"Debug: Bot lacks permissions to timeout member {member}.")
    except discord.HTTPException as e:
        print(f"Debug: HTTPException occurred: {e}")
    except Exception as e:
        print(f"Debug: Unexpected error occurred: {e}")


@bot.event
async def on_message(message):
    global crazy_last_response_time

    if message.author == bot.user:
        return

    # Too many mentions
    if len(message.mentions) >= 3:
        member = message.guild.get_member(message.author.id)
        await timeout_member(member)
        await message.delete()
        return

    # Auto delete torrent if post in chat.
    for file in message.attachments:
        if file.filename.endswith((".torrent", ".TORRENT")):
            member = message.guild.get_member(message.author.id)
            await timeout_member(member)
            await message.delete()

    if message.author.id == CRAZY_USER_ID:
        now = aware_utcnow()
        if (
            crazy_last_response_time is None
            or now - crazy_last_response_time >= timedelta(hours=8)
        ):
            crazy_last_response_time = now
            await message.channel.send(f"{CRAZY_URL}")

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

    # Check if the message is in an allowed channel
    if message.channel.id not in ALLOWED_CHANNELS:
        return

    # Check if any of the patterns match the message
    # print('Checking for patterns...')
    for pattern in patterns:
        if re.search(pattern["regex"], message.content, re.IGNORECASE):
            response = pattern["response"]
            reply_message = await message.reply(response, mention_author=True)
            await reply_message.add_reaction("\U0000274C")
            break


@bot.event
async def on_reaction_add(reaction, user):
    if reaction.emoji != "\U0000274C":
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


def generate_random_nickname():
    random_number = random.randint(1, 99)
    return f"Unknown Soldier {random_number:02d}"


def is_valid_username(username):
    pattern = r"^[\d\x00-\x7F\xC0-\xFF]{2,}"
    return bool(re.match(pattern, username))


def is_numeric_name(username):
    return username.isnumeric()


@bot.event
async def on_member_join(member):
    name_to_check = member.name

    if member.display_name:
        name_to_check = member.display_name

    if (
        len(name_to_check) < 3
        or not is_valid_username(name_to_check)
        or is_numeric_name(name_to_check)
    ):
        new_nick = generate_random_nickname()
        await member.edit(nick=new_nick)


@bot.event
async def on_member_update(before, after):
    name_to_check = after.name

    if after.nick:
        name_to_check = after.nick

    if (
        len(name_to_check) < 3
        or not is_valid_username(name_to_check)
        or is_numeric_name(name_to_check)
    ):
        new_nick = generate_random_nickname()
        await after.edit(nick=new_nick)


# Update Player Counts from API
@tasks.loop(minutes=10)
async def update_status():
    data = fetch_api_data()
    countPlayers = data.get("countPlayers", 0)
    countServers = data.get("countServers", 0)
    activity = discord.Game(
        name=f"with {countPlayers} players on {countServers} servers"
    )
    await bot.change_presence(activity=activity)


@tasks.loop(minutes=10080)
async def heat_death():
    try:
        now = aware_utcnow()

        remaining_seconds = int((TARGET_DATE - now).total_seconds())

        print(f"Seconds until August 12, 2036, UTC: {remaining_seconds}")

        channel = bot.get_channel(OFFTOPIC_CHANNEL)
        if channel:
            await channel.send(
                f"Can you believe it? Only {remaining_seconds} seconds until August 12th, 2036, the heat death of the universe."
            )
        else:
            print("Debug: Channel not found. Check the OFFTOPIC_CHANNEL variable.")
    except Exception as e:
        print(f"An error occurred in heat_death task: {e}")


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    await tree.sync(
        guild=discord.Object(id=GUILD_ID)
    )  # Sync commands for a specific guild.
    update_status.start()
    heat_death.start()


bot.run(os.getenv("BOT_TOKEN"))
