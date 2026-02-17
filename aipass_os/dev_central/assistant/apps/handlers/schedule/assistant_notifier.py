#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: assistant_notifier.py - ASSISTANT Bot Telegram Notifications
# Date: 2026-02-15
# Version: 1.0.0
# Category: assistant/handlers/schedule
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-15): Initial implementation - assistant bot notifications
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
#   - No cross-branch imports, no Prax logger
#   - stdlib only (urllib, json) - runs under /usr/bin/python3
# =============================================

"""
Handler for sending Telegram notifications via the assistant bot.

Patrick's direct line to assistant. Uses the dedicated assistant bot
(separate from scheduler and bridge bots) to notify Patrick of
wake-up events, email reports, and errors.
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict
from urllib.request import Request, urlopen
from urllib.error import URLError

# =============================================
# PATH SETUP
# =============================================

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# =============================================
# CONSTANTS
# =============================================

CONFIG_PATH = Path("/home/aipass/.aipass/assistant_bot_config.json")


# =============================================
# CONFIG
# =============================================

def load_config() -> Dict[str, str]:
    """
    Load assistant bot config from assistant_bot_config.json.

    Returns:
        Dict with 'bot_token' and 'chat_id' keys

    Raises:
        FileNotFoundError: If config file is missing
        KeyError: If required keys are absent
    """
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    return {
        "bot_token": raw["telegram_bot_token"],
        "chat_id": raw["telegram_chat_id"],
    }


# =============================================
# SEND
# =============================================

def send_notification(message: str) -> bool:
    """
    Send a message to Patrick via the assistant bot.

    Args:
        message: Text to send (plain text, supports emoji)

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        config = load_config()
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"[assistant_notifier] Config error: {e}")
        return False

    url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
    payload = {
        "chat_id": config["chat_id"],
        "text": message,
    }

    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                return True
            print(f"[assistant_notifier] API error: {result.get('description')}")
            return False
    except URLError as e:
        print(f"[assistant_notifier] Send failed: {e}")
        return False
    except Exception as e:
        print(f"[assistant_notifier] Unexpected error: {e}")
        return False


# =============================================
# NOTIFICATION HELPERS
# =============================================

def notify_wakeup() -> bool:
    """
    Notify that assistant is waking up.

    Returns:
        True if notification sent, False otherwise
    """
    now = datetime.now().strftime("%H:%M:%S")
    message = "\U0001f916 Assistant waking up at " + now
    return send_notification(message)


def notify_report(summary: str) -> bool:
    """
    Send assistant's wake-up report.

    Args:
        summary: Report content (email counts, listings, etc.)

    Returns:
        True if notification sent, False otherwise
    """
    message = "\U0001f4cb Assistant Report:\n" + summary
    return send_notification(message)


def notify_error(error: str) -> bool:
    """
    Notify that an error occurred during wake-up.

    Args:
        error: Error description

    Returns:
        True if notification sent, False otherwise
    """
    message = "\u274c Assistant Error:\n" + error
    return send_notification(message)


# =============================================
# MAIN - Testing
# =============================================

if __name__ == "__main__":
    print("assistant_notifier.py - manual test")
    print(f"Config path: {CONFIG_PATH}")

    try:
        cfg = load_config()
        print(f"Bot token: {cfg['bot_token'][:12]}...")
        print(f"Chat ID: {cfg['chat_id']}")
    except Exception as e:
        print(f"Config load failed: {e}")

    print("\nSending test notification...")
    ok = send_notification("Test from assistant_notifier.py handler")
    print(f"Result: {'OK' if ok else 'FAILED'}")
