import json
import os
from database import get_patterns

PATTERNS_FILE = "patterns.json"

BOT_DATA_DIR = os.getenv("BOT_DATA_DIR", "/bot-data")

message_patterns = get_patterns()


def update_patterns(regex: str, response: str):
    """update patterns in memory."""
    message_patterns.append({"regex": regex, "response": response})
    print(f"Pattern added in memory: {regex}")
