#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: config.py - Telegram Configuration Handler
# Date: 2026-02-03
# Version: 1.1.0
# Category: api/handlers/telegram
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2026-02-03): Add allowed_user_ids loading for user allowlist
#   - v1.0.0 (2026-02-03): Initial config loader for Telegram bridge
#
# CODE STANDARDS:
#   - Pure functions with proper error raising
#   - No Prax imports (handler tier 3)
# =============================================

"""
Telegram Configuration Handler

Manages Telegram bot configuration:
- Load bot token from config file
- Load bot username
- Load allowed user IDs for access control
- Config file location: ~/.aipass/telegram_config.json
"""

# Infrastructure
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Standard library
import json
from typing import Optional, List

# =============================================
# CONSTANTS
# =============================================

CONFIG_PATH = Path.home() / ".aipass" / "telegram_config.json"

# =============================================
# CONFIGURATION LOADING
# =============================================

def load_telegram_config() -> Optional[dict]:
    """
    Load Telegram configuration from config file.

    Config file location: ~/.aipass/telegram_config.json
    Expected structure:
    {
        "telegram_bot_token": "...",
        "telegram_bot_username": "aipass_bridge_bot",
        "allowed_user_ids": []
    }

    Returns:
        Configuration dict or None if load fails
    """
    try:
        if not CONFIG_PATH.exists():
            return None

        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return config

    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def get_bot_token() -> Optional[str]:
    """
    Get Telegram bot token from config.

    Returns:
        Bot token string or None if not found
    """
    config = load_telegram_config()
    if not config:
        return None

    token = config.get("telegram_bot_token")
    if not token:
        return None

    return token


def get_bot_username() -> Optional[str]:
    """
    Get Telegram bot username from config.

    Returns:
        Bot username string or None if not found
    """
    config = load_telegram_config()
    if not config:
        return None

    username = config.get("telegram_bot_username")
    if not username:
        return None

    return username


def get_allowed_user_ids() -> List[int]:
    """
    Get list of allowed Telegram user IDs from config.

    Returns:
        List of allowed user IDs. Empty list means allow all (for testing).
    """
    config = load_telegram_config()
    if not config:
        return []

    allowed = config.get("allowed_user_ids", [])
    if not isinstance(allowed, list):
        return []

    return [int(uid) for uid in allowed if isinstance(uid, (int, str))]


def validate_config() -> bool:
    """
    Validate that Telegram configuration is complete.

    Returns:
        True if config is valid, False otherwise
    """
    config = load_telegram_config()
    if not config:
        return False

    if not config.get("telegram_bot_token"):
        return False

    return True
