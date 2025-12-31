import random
import re
from datetime import datetime, timedelta, timezone
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

import discord
from bot.log import logger


def aware_utcnow():
    return datetime.now(timezone.utc)


def fetch_api_data():
    """
    Fetch data from the getserve.rs API

    Returns:
        dict: API response data or empty dict on failure
    """
    url = "https://api.getserve.rs/v1/servers/alterware"

    try:
        response = requests.get(url, timeout=10)

        response.raise_for_status()

        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"API returned non-200 status: {response.status_code}")
            return {}

    except Timeout:
        logger.error(f"Request to {url} timed out after 10 seconds")
        return {}

    except ConnectionError as e:
        # This catches DNS resolution errors, connection refused, etc.
        logger.error(f"Connection error for {url}: {e}")
        return {}

    except RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return {}

    except ValueError as e:
        logger.error(f"Failed to parse JSON response from {url}: {e}")
        return {}

    except Exception as e:
        logger.error(f"Unexpected error while fetching data from {url}: {e}")
        return {}


async def fetch_game_stats(game: str):
    """
    Fetch game-specific stats from the getserve.rs API

    Args:
        game (str): Game identifier

    Returns:
        dict: Game stats data or None on failure
    """
    url = f"https://api.getserve.rs/v1/servers/alterware/{game}"

    try:
        response = requests.get(url, timeout=10)

        response.raise_for_status()

        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(
                f"API returned non-200 status for game {game}: {response.status_code}"
            )
            return None

    except Timeout:
        logger.error(f"Request to {url} timed out after 10 seconds")
        return None

    except ConnectionError as e:
        # This catches DNS resolution errors, connection refused, etc.
        logger.error(f"Connection error for {url}: {e}")
        return None

    except RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return None

    except ValueError as e:
        logger.error(f"Failed to parse JSON response from {url}: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error while fetching game stats from {url}: {e}")
        return None


async def compile_stats():
    games = ["s1", "iw6", "t7"]
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
async def timeout_member(
    member: discord.Member,
    duration: timedelta = timedelta(minutes=1),
    reason: str = "Requested by the bot",
):
    if not member:
        logger.error("Member is None. Skipping timeout.")
        return

    try:
        # Debug: Print the member object and timeout duration
        logger.debug(f"Attempting to timeout member {member} (ID: {member.id}).")
        logger.debug(f"Timeout duration set to {duration}.")
        logger.debug(f"Reason: {reason}")

        await member.timeout(duration, reason=reason)
        logger.info(f"Successfully timed out {member}.")

    except discord.Forbidden:
        logger.error(f"Bot lacks permissions to timeout member {member}.")
    except discord.HTTPException as e:
        logger.error("HTTPException occurred: %s", e)
    except Exception as e:
        logger.error("Unexpected error occurred: %s", e)


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


def safe_truncate(text: str, max_len: int, placeholder: str = "...") -> str:
    """Truncate text to Discord's limits safely."""
    if not text:
        return "[no content]"
    if len(text) > max_len:
        return text[: max_len - len(placeholder)] + placeholder
    return text
