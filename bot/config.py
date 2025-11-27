import os
from bot.log import logger
from database import get_patterns

from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")

message_patterns = get_patterns()


def update_patterns(regex: str, response: str):
    """update patterns in memory."""
    message_patterns.append({"regex": regex, "response": response})
    logger.info(f"Pattern added in memory: {regex}")


def load_chat_messages_from_db(
    mongo_uri="mongodb://localhost:27017",
    database="discord_bot",
    collection="messages",
):
    """
    Loads all chat messages from MongoDB.

    Args:
        mongo_uri (str): MongoDB connection URI
        database (str): Name of the MongoDB database
        collection (str): Name of the collection

    Returns:
        list: list of message strings
    """
    try:
        client = MongoClient(mongo_uri)
        db = client[database]
        col = db[collection]

        logger.debug(
            f"Connecting to MongoDB at {mongo_uri}, DB='{database}', Collection='{collection}'"
        )

        cursor = col.find({}, {"message": 1})
        messages = [doc["message"] for doc in cursor if "message" in doc]

        logger.info(f"Loaded {len(messages)} messages from MongoDB")

        return messages

    except Exception as e:
        logger.error(f"Failed to load messages from MongoDB: {e}")
        return []


def load_mongodb():
    messages = []

    if not MONGO_URI:
        logger.error("MONGO_URI is not set. Please contact the administrator.")
        return

    messages = load_chat_messages_from_db(MONGO_URI)
    if not messages:
        logger.warning("messages collection is empty after loading from MongoDB!")

    return messages


schizo_messages = load_mongodb()
