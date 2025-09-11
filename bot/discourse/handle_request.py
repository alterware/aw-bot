import os

import requests
from bs4 import BeautifulSoup

from bot.log import logger

DISCOURSE_BASE_URL = os.getenv("DISCOURSE_BASE_URL")
API_KEY = os.getenv("DISCOURSE_API_KEY")
API_USERNAME = os.getenv("DISCOURSE_API_USERNAME")

headers = {"Api-Key": API_KEY, "Api-Username": API_USERNAME}


def get_topics_by_id(topic_id):
    """
    Fetches a topic by its ID and returns the topic data.

    Args:
        topic_id (int): The ID of the topic to fetch.

    Returns:
        dict or None: The topic data if successful, otherwise None.
    """
    try:
        response = requests.get(
            f"{DISCOURSE_BASE_URL}/t/{topic_id}.json",
            headers=headers,
            timeout=10,  # prevent hanging forever
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            logger.error(
                f"Access forbidden for topic {topic_id}: {response.status_code}"
            )
            return None
        else:
            logger.error(
                f"Error fetching topic {topic_id}: {response.status_code} - {response.text}"
            )
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for topic {topic_id}: {e}")
        return None


def get_topics_by_tag(tag_name):
    """
    Fetches all topics with a specific tag and retrieves the cooked string from each post.

    Args:
        tag_name (str): The name of the tag to filter topics.

    Returns:
        list: A list of cooked strings from all posts in the topics.
    """
    response = requests.get(
        f"{DISCOURSE_BASE_URL}/tag/{tag_name}.json", headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        topics = data.get("topic_list", {}).get("topics", [])
        cooked_strings = []

        for topic in topics:
            topic_id = topic["id"]
            topic_data = get_topics_by_id(topic_id)
            if topic_data:
                posts = topic_data.get("post_stream", {}).get("posts", [])
                for post in posts:
                    cooked_strings.append(post.get("cooked", ""))
        return cooked_strings
    elif response.status_code == 403:
        logger.error(f"Access forbidden for topic {topic_id}: {response.status_code}")
        return None
    else:
        logger.error(
            f"Error fetching topics with tag '{tag_name}': {response.status_code} - {response.text}"
        )
        return []


def fetch_cooked_posts(tag_name):
    """
    Fetches cooked strings from posts with a specific tag.

    Args:
        tag_name (str): The name of the tag to filter topics.

    Returns:
        list: A list of cooked strings from posts with the specified tag.
    """
    return get_topics_by_tag(tag_name)


def html_to_text(html_content):
    """
    Cleans the provided HTML content and converts it to plain text.

    Args:
        html_content (str): The HTML content to clean.

    Returns:
        str: The cleaned plain text.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n").strip()


def combine_posts_text(posts):
    """
    Combines the cooked content of all posts into a single plain text block.

    Args:
        posts (list): A list of posts, each containing a "cooked" HTML string.

    Returns:
        str: The combined plain text of all posts.
    """
    return "\n\n".join([html_to_text(post["cooked"]) for post in posts])
