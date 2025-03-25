import sqlite3
import os

from bot.utils import aware_utcnow

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


def migrate_users_with_role(user_id: int, role_id: int, user_name: str):
    """Migrates existing users with the role to the new table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO user_roles (user_id, role_id, date_assigned, user_name) VALUES (?, ?, ?, ?)",
        (user_id, role_id, aware_utcnow().isoformat(), user_name),
    )

    conn.commit()
    conn.close()


def add_user_to_role(user_id: int, role_id: int, user_name: str):
    """Adds a new user when they receive the role."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR REPLACE INTO user_roles (user_id, role_id, date_assigned, user_name) VALUES (?, ?, ?, ?)",
        (user_id, role_id, aware_utcnow().isoformat(), user_name),
    )

    conn.commit()
    conn.close()


def user_has_role(user_id: int):
    """Checks if a user is in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user_roles WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    conn.close()

    return result is not None
