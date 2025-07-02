import os
import json
from datetime import datetime

LOG_PATH = "logs/delivery_log.json"

def log_delivery(recipient_email, sender_username, status, error_message=None):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "recipient": recipient_email,
        "sender": sender_username,
        "status": status,
        "error": error_message
    }

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = []

    log_data.append(entry)

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    return entry
