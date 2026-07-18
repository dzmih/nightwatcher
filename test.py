import os
import time
import json
def load_json(path):
    if not os.path.exists(path):
        return []

    for _ in range(5):
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            time.sleep(0.1)

    return []

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EVENTS_FILE = os.path.join(BASE_DIR, "events.json")

a = load_json(EVENTS_FILE)
print(type(a))