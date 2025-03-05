import json
import os
from database import get_patterns, add_pattern

PATTERNS_FILE = "patterns.json"

BOT_DATA_DIR = os.getenv("BOT_DATA_DIR", "/bot-data")
MIGRATION_FLAG = os.path.join(BOT_DATA_DIR, "migration_done.flag")


def migrate_patterns():
    """Migrate patterns.json to the database if not already done."""
    if os.path.exists(MIGRATION_FLAG):
        print("Not performing migration: already done")
        return

    if not os.path.exists(PATTERNS_FILE):
        return

    try:
        with open(PATTERNS_FILE, "r") as f:
            patterns = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        patterns = []

    for pattern in patterns:
        add_pattern(pattern["regex"], pattern["response"])

    with open(MIGRATION_FLAG, "w") as f:
        f.write("done")

    print("Migration completed: patterns.json -> Database")


migrate_patterns()

message_patterns = get_patterns()


def update_patterns(regex: str, response: str):
    """update patterns in memory."""
    message_patterns.append({"regex": regex, "response": response})
    print(f"Pattern added in memory: {regex}")
