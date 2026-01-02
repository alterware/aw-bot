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
    url = "https://server.alterware.dev/stats.json"

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
