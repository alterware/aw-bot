import os

from bot.log import logger
from bot.mongodb.load_db import load_chat_messages_from_db

from database import get_patterns

MONGO_URI = os.getenv("MONGO_URI")


def update_patterns(regex: str, response: str):
    """update patterns in memory."""
    message_patterns.append({"regex": regex, "response": response})
    logger.info(f"Pattern added in memory: {regex}")


# load global variables

message_patterns = get_patterns()

schizo_messages = load_chat_messages_from_db()
