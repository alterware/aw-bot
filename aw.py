import datetime
import json
import os
import re
from typing import Literal

import discord
import requests
from discord import app_commands
from discord.ext import commands, tasks

GUILD_ID = 1110531063161299074
BOT_LOG = 1112049391482703873

# Define the channel IDs where auto responds are allowed
ALLOWED_CHANNELS = [
    1110531063744303138,
    1112048063448617142,
    1145458108190163014,
    1145456435518525611,
    1145469136919613551,
    1145459788151537804,
    1145469106133401682,
    1117540484085194833,
]
GENERAL_CHANNEL = 1110531063744303138

# Load existing patterns from file
try:
    with open("patterns.json", "r") as f:
        patterns = json.load(f)
except FileNotFoundError:
    patterns = []

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
tree = bot.tree


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


@bot.event
async def on_message_delete(message):
    channel = bot.get_channel(BOT_LOG)
    if channel:
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
            text=f"Message ID: {message.id} | Author ID: {message.author.id}"
        )

        await channel.send(embed=embed)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Too many mentions
    if len(message.mentions) >= 3:
        await message.delete()
        member = message.guild.get_member(message.author.id)
        if member:
            # Timeout the member for 60 seconds
            await member.timeout_for(
                discord.utils.utcnow() + datetime.timedelta(seconds=60)
            )
        return

    # Auto delete torrent if post in chat.
    for file in message.attachments:
        if file.filename.endswith((".torrent", ".TORRENT")):
            await message.delete()

    # Check if the message is in an allowed channel
    if message.channel.id not in ALLOWED_CHANNELS:
        return

    # Check if any of the patterns match the message
    # print('Checking for patterns...')
    for pattern in patterns:
        if re.search(pattern["regex"], message.content, re.IGNORECASE):
            # print('Checking message content:', message.content, re.IGNORECASE) # noqa
            # print('Matching pattern regex:', pattern['regex']) # noqa
            # print('Pattern match:', re.search(pattern['regex'], message.content, re.IGNORECASE)) # noqa
            response = pattern["response"]
            await message.channel.send(response)
            break


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


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    await tree.sync(
        guild=discord.Object(id=GUILD_ID)
    )  # Sync commands for a specific guild.
    update_status.start()


bot.run(os.getenv("BOT_TOKEN"))
