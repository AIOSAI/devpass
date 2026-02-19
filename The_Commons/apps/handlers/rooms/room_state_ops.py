#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: room_state_ops.py - Room State CRUD Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/rooms
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 4)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules/entry point
# =============================================

"""
Room State CRUD Handler

Manages key/value state for rooms (decorations, custom properties)
and convenience setters for room personality columns (mood, flavor, entrance).
"""

import sqlite3
from typing import Dict, Optional


# =============================================================================
# ROOM STATE KEY/VALUE OPERATIONS
# =============================================================================

def set_room_state(conn: sqlite3.Connection, room_name: str, key: str, value: str) -> bool:
    """
    Upsert a room state key/value pair.

    Args:
        conn: Database connection
        room_name: Room name (FK to rooms.name)
        key: State key (e.g. 'decor_trophy', 'custom_rule')
        value: State value

    Returns:
        True on success, False on error
    """
    try:
        conn.execute(
            "INSERT INTO room_state (room_name, key, value, updated_at) "
            "VALUES (?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now')) "
            "ON CONFLICT(room_name, key) DO UPDATE SET "
            "value = excluded.value, updated_at = excluded.updated_at",
            (room_name, key, value),
        )
        conn.commit()
        return True
    except Exception:
        return False


def get_room_state(conn: sqlite3.Connection, room_name: str, key: str) -> Optional[str]:
    """
    Get a specific state value for a room.

    Args:
        conn: Database connection
        room_name: Room name
        key: State key to look up

    Returns:
        The value string, or None if not found
    """
    try:
        row = conn.execute(
            "SELECT value FROM room_state WHERE room_name = ? AND key = ?",
            (room_name, key),
        ).fetchone()
        return row["value"] if row else None
    except Exception:
        return None


def get_all_room_state(conn: sqlite3.Connection, room_name: str) -> Dict[str, str]:
    """
    Get all state key/value pairs for a room.

    Args:
        conn: Database connection
        room_name: Room name

    Returns:
        Dict of key -> value pairs
    """
    try:
        rows = conn.execute(
            "SELECT key, value FROM room_state WHERE room_name = ? ORDER BY key",
            (room_name,),
        ).fetchall()
        return {row["key"]: row["value"] for row in rows}
    except Exception:
        return {}


# =============================================================================
# ROOM PERSONALITY COLUMN SETTERS
# =============================================================================

def set_mood(conn: sqlite3.Connection, room_name: str, mood: str) -> bool:
    """
    Update a room's mood column.

    Args:
        conn: Database connection
        room_name: Room name
        mood: Mood string (e.g. 'welcoming', 'focused', 'relaxed')

    Returns:
        True on success, False on error
    """
    try:
        conn.execute(
            "UPDATE rooms SET mood = ? WHERE name = ?",
            (mood, room_name),
        )
        conn.commit()
        return True
    except Exception:
        return False


def set_flavor(conn: sqlite3.Connection, room_name: str, text: str) -> bool:
    """
    Update a room's flavor text.

    Args:
        conn: Database connection
        room_name: Room name
        text: Flavor text description

    Returns:
        True on success, False on error
    """
    try:
        conn.execute(
            "UPDATE rooms SET flavor_text = ? WHERE name = ?",
            (text, room_name),
        )
        conn.commit()
        return True
    except Exception:
        return False


def set_entrance(conn: sqlite3.Connection, room_name: str, message: str) -> bool:
    """
    Update a room's entrance message.

    Args:
        conn: Database connection
        room_name: Room name
        message: Entrance message shown when entering the room

    Returns:
        True on success, False on error
    """
    try:
        conn.execute(
            "UPDATE rooms SET entrance_message = ? WHERE name = ?",
            (message, room_name),
        )
        conn.commit()
        return True
    except Exception:
        return False
