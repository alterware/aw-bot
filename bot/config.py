import csv
import os
import glob

from bot.log import logger
from database import get_patterns

message_patterns = get_patterns()


def update_patterns(regex: str, response: str):
    """update patterns in memory."""
    message_patterns.append({"regex": regex, "response": response})
    logger.info(f"Pattern added in memory: {regex}")


def load_chat_messages_from_disk(csv_path="chat/chat_messages_blue.csv"):
    """
    Loads all messages from the given CSV file.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        list: List of message strings.
    """
    messages = []
    if not os.path.exists(csv_path):
        logger.info(f"CSV file not found: {csv_path}")
        return messages

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            msg = row.get("Message")
            if msg:
                messages.append(msg)
    return messages


def load_chat_messages():
    """
    Loads and combines chat messages from all CSV files in the chat folder.

    Returns:
        list: Combined list of all message strings from all CSV files.
    """
    messages = []

    # Find all CSV files in the chat folder
    csv_files = glob.glob("chat/*.csv")

    if not csv_files:
        logger.error("No CSV files found in chat folder")
        return messages

    logger.info(
        f"Found {len(csv_files)} CSV files: {[os.path.basename(f) for f in csv_files]}"
    )

    # Load messages from each CSV file
    for csv_file in csv_files:
        file_messages = load_chat_messages_from_disk(csv_file)
        messages.extend(file_messages)
        logger.info(
            f"Loaded {len(file_messages)} messages from {os.path.basename(csv_file)}"
        )

    logger.info(f"Total messages loaded: {len(messages)}")

    return messages


schizo_messages = load_chat_messages()
