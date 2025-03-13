import sqlite3
import os

DB_DIR = os.getenv("BOT_DATA_DIR", "/bot-data")
DB_PATH = os.path.join(DB_DIR, "database.db")

os.makedirs(DB_DIR, exist_ok=True)


def initialize_db():
    """Creates the database tables if they don't exist."""
    print(f"Opening database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(os.path.join(os.path.dirname(__file__), "schema.sql"), "r") as f:
        cursor.executescript(f.read())

    conn.commit()
    conn.close()

    print(f"Done loading database: {DB_PATH}")


def add_pattern(regex: str, response: str):
    """Adds a new pattern to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO message_patterns (regex, response) VALUES (?, ?)",
        (regex, response),
    )
    conn.commit()
    conn.close()


def get_patterns():
    """Fetches all regex-response pairs from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT regex, response FROM message_patterns")
    patterns = cursor.fetchall()
    conn.close()

    return [{"regex": row[0], "response": row[1]} for row in patterns]


def remove_pattern(pattern_id: int):
    """Removes a pattern by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM message_patterns WHERE id = ?", (pattern_id,))
    conn.commit()
    conn.close()
