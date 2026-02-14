#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: session_store.py - Telegram Session Persistence Store
# Date: 2026-02-10
# Version: 2.0.0
# Category: api/handlers/telegram
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-12): tmux session tracking - store branch_name per chat, add get_session_by_branch
#   - v1.0.0 (2026-02-10): Initial - JSON file store with fcntl locking for session persistence
#
# CODE STANDARDS:
#   - Pure functions with proper error raising
#   - No Prax imports (handler tier 3)
# =============================================

"""
Telegram Session Persistence Store v2

Stores tmux session info per Telegram chat_id in a JSON file.
Tracks which branch each chat is targeting and session metadata.

File location: ~/.aipass/telegram_sessions.json
Format: {chat_id_str: {branch_name, session_id, created_at, last_used, message_count}}

Thread-safe via fcntl.flock file locking.
"""

# Infrastructure
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Standard library
import fcntl
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger("telegram_session_store")

SESSION_FILE = Path.home() / ".aipass" / "telegram_sessions.json"


def _read_store() -> Dict[str, Any]:
    """
    Read the session store from disk with file locking.

    Returns:
        Dict mapping chat_id strings to session data, or empty dict on error.
    """
    if not SESSION_FILE.exists():
        return {}

    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read session store: %s", e)
        return {}


def _write_store(data: Dict[str, Any]) -> bool:
    """
    Write the session store to disk with file locking.

    Args:
        data: The full session store dict to write.

    Returns:
        True if written successfully, False on error.
    """
    try:
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return True
    except OSError as e:
        logger.error("Failed to write session store: %s", e)
        return False


def get_session(chat_id: int) -> Optional[Dict[str, Any]]:
    """
    Get stored session data for a chat_id.

    Args:
        chat_id: Telegram chat ID.

    Returns:
        Dict with {branch_name, session_id, created_at, last_used, message_count} or None.
    """
    store = _read_store()
    return store.get(str(chat_id))


def save_session(chat_id: int, branch_name: str, session_id: Optional[str] = None) -> None:
    """
    Create or update a session entry for a chat_id.

    If the chat_id already has an entry with the same branch_name,
    updates last_used and increments message_count.
    Otherwise creates a new entry.

    Args:
        chat_id: Telegram chat ID.
        branch_name: Target branch name (e.g. 'dev_central').
        session_id: Optional Claude session ID (set by Stop hook).
    """
    store = _read_store()
    key = str(chat_id)
    now = datetime.now().isoformat()

    existing = store.get(key)
    if existing and existing.get("branch_name") == branch_name:
        existing["last_used"] = now
        existing["message_count"] = existing.get("message_count", 0) + 1
        if session_id:
            existing["session_id"] = session_id
    else:
        store[key] = {
            "branch_name": branch_name,
            "session_id": session_id or f"tmux-{branch_name}",
            "created_at": now,
            "last_used": now,
            "message_count": 1,
        }

    _write_store(store)


def clear_session(chat_id: int) -> None:
    """
    Remove the session entry for a chat_id.

    Args:
        chat_id: Telegram chat ID.
    """
    store = _read_store()
    key = str(chat_id)
    if key in store:
        del store[key]
        _write_store(store)


def get_session_info(chat_id: int) -> str:
    """
    Get a formatted string with session details for /status command.

    Args:
        chat_id: Telegram chat ID.

    Returns:
        Human-readable session info string.
    """
    session = get_session(chat_id)
    if not session:
        return "No active session. Send a message to start one."

    branch_name = session.get("branch_name", "unknown")
    session_id = session.get("session_id", "unknown")
    created_at = session.get("created_at", "unknown")
    last_used = session.get("last_used", "unknown")
    message_count = session.get("message_count", 0)

    return (
        f"Branch: @{branch_name}\n"
        f"Session: {session_id[:8]}...\n"
        f"Created: {created_at}\n"
        f"Last used: {last_used}\n"
        f"Messages: {message_count}"
    )


def get_session_by_branch(branch_name: str) -> Optional[Dict[str, Any]]:
    """
    Find a session entry by branch name (searches all chats).

    Args:
        branch_name: Branch name to search for.

    Returns:
        Session data dict or None if not found.
    """
    store = _read_store()
    for entry in store.values():
        if isinstance(entry, dict) and entry.get("branch_name") == branch_name:
            return entry
    return None
