import json

try:
    with open("patterns.json", "r") as f:
        message_patterns = json.load(f)
except FileNotFoundError:
    message_patterns = []  # Fallback to an empty list if the file doesn't exist
