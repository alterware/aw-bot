import os
import csv
from database import get_patterns

message_patterns = get_patterns()


def update_patterns(regex: str, response: str):
    """update patterns in memory."""
    message_patterns.append({"regex": regex, "response": response})
    print(f"Pattern added in memory: {regex}")


def load_chat_messages(csv_path="chat/chat_messages.csv"):
    """
    Loads all messages from the given CSV file.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        list: List of message strings.
    """
    messages = []
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return messages

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            msg = row.get("Message")
            if msg:
                messages.append(msg)
    return messages


schizo_messages = load_chat_messages()
