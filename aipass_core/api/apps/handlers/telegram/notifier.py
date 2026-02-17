#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: notifier.py - Telegram Push Notifications
# Date: 2026-02-17
# Version: 1.0.0
# Category: api/handlers/telegram
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-17): Initial implementation - reusable Telegram notification sender
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
#   - No cross-branch imports, no Prax logger
# =============================================

"""
Reusable Telegram notification sender.

One function, one file. Reads bot token and chat_id from
~/.aipass/scheduler_config.json and sends messages via the
Telegram Bot API. Silent failure on errors.

Usage:
    from apps.handlers.telegram.notifier import send_telegram_notification
    send_telegram_notification("System alert: disk usage at 90%")
"""

# Infrastructure
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Standard library
import json
from urllib.request import Request, urlopen
from urllib.error import URLError

# =============================================
# CONSTANTS
# =============================================

CONFIG_PATH = Path.home() / ".aipass" / "scheduler_config.json"

# =============================================
# PUBLIC API
# =============================================


def send_telegram_notification(message: str) -> bool:
    """
    Send a message to Telegram via the scheduler bot.

    Args:
        message: Text to send (plain text, supports emoji)

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        bot_token = config["telegram_bot_token"]
        chat_id = config["telegram_chat_id"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": message}).encode("utf-8")
    req = Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except (URLError, Exception):
        return False


# =============================================
# MAIN - Testing
# =============================================

if __name__ == "__main__":
    print("notifier.py - manual test")
    ok = send_telegram_notification("Test from api/handlers/telegram/notifier.py")
    print(f"Result: {'OK' if ok else 'FAILED'}")
