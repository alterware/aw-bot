import os
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field

from bot.log import logger

from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")


@dataclass
class DeletedMessage:
    message_id: int
    channel_id: int
    author_id: int
    author_name: str
    content: str
    timestamp: datetime
    deleted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return asdict(self)


def get_mongodb_uri():
    if not MONGO_URI:
        logger.error("MONGO_URI is not set. Please contact the administrator.")
        return "mongodb://localhost:27017"

    return MONGO_URI


def write_deleted_message_to_collection(
    deleted_message: DeletedMessage,
    database="discord_bot",
    collection="deleted_messages",
):
    mongo_uri = get_mongodb_uri()

    try:
        with MongoClient(mongo_uri) as client:
            db = client[database]
            col = db[collection]

            logger.debug(
                f"Connecting to MongoDB at {mongo_uri}, DB='{database}', Collection='{collection}'"
            )

            result = col.insert_one(deleted_message.to_dict())
            logger.debug(f"Deleted message logged with _id: {result.inserted_id}")
    except Exception as e:
        logger.error(f"Failed to write a deleted message to MongoDB: {e}")
        return []


def read_message_from_collection(
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
    mongo_uri = get_mongodb_uri()

    try:
        with MongoClient(mongo_uri) as client:
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


def load_chat_messages_from_db():
    messages = []

    messages = read_message_from_collection()
    if not messages:
        logger.warning("messages collection is empty after loading from MongoDB!")

    return messages
