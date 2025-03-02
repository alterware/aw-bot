import random
import re
from datetime import datetime, timedelta, timezone

import discord
import requests


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
    games = ["iw4", "s1", "iw6", "t7"]
    stats_message = "**Stats for all games:**\n"
    for game in games:
        data = await fetch_game_stats(game)
        if data:
            count_servers = data.get("countServers", "N/A")
            count_players = data.get("countPlayers", "N/A")
            stats_message += f"**{game.upper()}:** Total Servers: {count_servers}, Total Players: {count_players}\n"
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
    message = (
        f'Top {min(len(matching_servers), max_results)} servers matching "{query}":\n'
    )
    for server in matching_servers[:max_results]:
        message += (
            f"- **{server['hostnameDisplay']}** | {server['gameDisplay']} | "
            f"**Gametype**: {server['gametypeDisplay']} | **Map**: {server['mapDisplay']} | "
            f"**Players**: {server['realClients']}/{server['maxplayers']}\n"
        )
    return message


# Timeout a member
async def timeout_member(member: discord.Member):
    if not member:
        print("Debug: Member is None. Skipping timeout.")
        return

    try:
        # Debug: Print the member object and timeout duration
        print(f"Debug: Attempting to timeout member {member} (ID: {member.id}).")

        timeout_until = timedelta(minutes=1)
        print(f"Debug: Timeout duration set to {timeout_until}.")

        await member.timeout(timeout_until, reason="Requested by the bot")
        print(f"Debug: Successfully timed out {member}.")

    except discord.Forbidden:
        print(f"Debug: Bot lacks permissions to timeout member {member}.")
    except discord.HTTPException as e:
        print(f"Debug: HTTPException occurred: {e}")
    except Exception as e:
        print(f"Debug: Unexpected error occurred: {e}")


# Check if a username is valid
def is_valid_username(username: str) -> bool:
    pattern = r"^[\d\x00-\x7F\xC0-\xFF]{2,}"
    return bool(re.match(pattern, username))


# Check if a username is numeric
def is_numeric_name(username: str) -> bool:
    return username.isnumeric()


# Generate a random nickname
def generate_random_nickname() -> str:
    random_number = random.randint(1, 99)
    return f"Unknown Soldier {random_number:02d}"
