#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: preferences.py - Notification Preferences Handler
# Date: 2026-02-08
# Version: 1.0.0
# Category: the_commons/handlers/notifications
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-08): Initial creation - preference CRUD and notification logic
#
# CODE STANDARDS:
#   - Handler: pure business logic, NO orchestration
#   - Database queries for notification preferences
#   - Importable by Commons modules
# =============================================

"""
Notification Preferences Handler

Provides database query functions for notification preferences.
Manages watch/track/mute preferences per agent per target (room, post, thread).

Notification levels:
- watch: Get notified of ALL activity in the target
- track: Get notified only of @mentions and direct replies (DEFAULT)
- mute: No notifications for this target

Usage:
    from handlers.notifications.preferences import should_notify, set_preference

    if should_notify(conn, "SEED", "room", "general", "new_post"):
        # send notification
    set_preference(conn, "SEED", "room", "general", "watch")
"""

import logging
import sqlite3
from typing import Optional, List, Dict, Any

logger = logging.getLogger("commons.notifications.preferences")


def get_preference(
    conn: sqlite3.Connection, agent_name: str, target_type: str, target_id: str
) -> Optional[str]:
    """
    Get the notification preference level for an agent on a target.

    Args:
        conn: Database connection
        agent_name: The agent/branch name
        target_type: One of 'room', 'post', 'thread'
        target_id: Room name or post ID (as text)

    Returns:
        Level string ('watch', 'track', 'mute') or None (meaning default 'track')
    """
    row = conn.execute(
        "SELECT level FROM notification_preferences "
        "WHERE agent_name = ? AND target_type = ? AND target_id = ?",
        (agent_name, target_type, target_id),
    ).fetchone()

    if row:
        return row["level"]
    return None


def set_preference(
    conn: sqlite3.Connection,
    agent_name: str,
    target_type: str,
    target_id: str,
    level: str,
) -> bool:
    """
    Set a notification preference for an agent on a target.

    Args:
        conn: Database connection
        agent_name: The agent/branch name
        target_type: One of 'room', 'post', 'thread'
        target_id: Room name or post ID (as text)
        level: One of 'watch', 'track', 'mute'

    Returns:
        True if set successfully, False otherwise
    """
    valid_types = ("room", "post", "thread")
    valid_levels = ("watch", "track", "mute")

    if target_type not in valid_types:
        logger.warning(f"Invalid target_type: {target_type}")
        return False

    if level not in valid_levels:
        logger.warning(f"Invalid level: {level}")
        return False

    try:
        conn.execute(
            "INSERT OR REPLACE INTO notification_preferences "
            "(agent_name, target_type, target_id, level) VALUES (?, ?, ?, ?)",
            (agent_name, target_type, target_id, level),
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to set preference: {e}")
        return False


def get_all_preferences(
    conn: sqlite3.Connection, agent_name: str
) -> List[Dict[str, Any]]:
    """
    Get all notification preferences for an agent.

    Args:
        conn: Database connection
        agent_name: The agent/branch name

    Returns:
        List of preference dicts with keys: target_type, target_id, level, created_at
    """
    rows = conn.execute(
        "SELECT target_type, target_id, level, created_at "
        "FROM notification_preferences WHERE agent_name = ? "
        "ORDER BY target_type, target_id",
        (agent_name,),
    ).fetchall()

    return [dict(r) for r in rows]


def should_notify(
    conn: sqlite3.Connection,
    agent_name: str,
    target_type: str,
    target_id: str,
    event_type: str,
) -> bool:
    """
    Determine whether an agent should be notified for an event on a target.

    Args:
        conn: Database connection
        agent_name: The agent/branch name to check
        target_type: One of 'room', 'post', 'thread'
        target_id: Room name or post ID (as text)
        event_type: One of 'mention', 'reply', 'new_post', 'new_comment'

    Returns:
        True if the agent should be notified, False otherwise

    Logic:
        - mute -> False for all events
        - watch -> True for all events
        - track (default) -> True only for 'mention' and 'reply'
    """
    level = get_preference(conn, agent_name, target_type, target_id)

    # Default is 'track' if no explicit preference
    if level is None:
        level = "track"

    if level == "mute":
        return False
    elif level == "watch":
        return True
    else:
        # track: only mentions and replies
        return event_type in ("mention", "reply")


def get_watchers(
    conn: sqlite3.Connection, target_type: str, target_id: str
) -> List[str]:
    """
    Get all agent names that are watching a specific target.

    Args:
        conn: Database connection
        target_type: One of 'room', 'post', 'thread'
        target_id: Room name or post ID (as text)

    Returns:
        List of agent names with 'watch' level on this target
    """
    rows = conn.execute(
        "SELECT agent_name FROM notification_preferences "
        "WHERE target_type = ? AND target_id = ? AND level = 'watch'",
        (target_type, target_id),
    ).fetchall()

    return [row["agent_name"] for row in rows]


__all__ = [
    "get_preference",
    "set_preference",
    "get_all_preferences",
    "should_notify",
    "get_watchers",
]
