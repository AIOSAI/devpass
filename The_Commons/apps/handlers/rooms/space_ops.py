#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: space_ops.py - Spatial Navigation Data Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/rooms
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 4)
#
# CODE STANDARDS:
#   - Handler: data retrieval and mutation logic only
#   - No console output - returns data dicts for module-layer rendering
#   - Importable by Commons modules/entry point
# =============================================

"""
Spatial Navigation Data Handler

Data retrieval and mutation for spatial room commands: enter, look, decorate, visitors.
Returns structured dicts -- display/rendering is handled by space_module.py.
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger

COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import get_db, close_db
from handlers.rooms.room_state_ops import get_all_room_state, set_room_state


# =============================================================================
# DATA RETRIEVAL
# =============================================================================

def get_room_enter_data(room_name: str) -> Dict[str, Any]:
    """
    Gather all data needed to render the 'enter' view for a room.

    Returns:
        Dict with keys: found, room, state, post_count, recent_count, decorations, error
    """
    result: Dict[str, Any] = {"found": False, "error": None}

    try:
        conn = get_db()

        row = conn.execute("SELECT * FROM rooms WHERE name = ?", (room_name,)).fetchone()
        if not row:
            close_db(conn)
            result["error"] = f"Room '{room_name}' not found"
            return result

        room = dict(row)

        # Get room state (decorations etc)
        state = get_all_room_state(conn, room_name)

        # Count posts
        post_count = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE room_name = ?", (room_name,)
        ).fetchone()[0]

        # Recent activity (posts in last 48h)
        cutoff = (datetime.utcnow() - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
        recent_count = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE room_name = ? AND created_at > ?",
            (room_name, cutoff),
        ).fetchone()[0]

        close_db(conn)

        # Extract decorations from state
        decorations = {k: v for k, v in state.items() if k.startswith("decor_")}

        result.update({
            "found": True,
            "room": room,
            "state": state,
            "post_count": post_count,
            "recent_count": recent_count,
            "decorations": decorations,
        })

    except Exception as e:
        result["error"] = str(e)

    return result


def get_room_look_data(room_name: str) -> Dict[str, Any]:
    """
    Gather all data needed to render the 'look' view for a room.

    Returns:
        Dict with keys: found, room, state, decorations, recent_posts, error
    """
    result: Dict[str, Any] = {"found": False, "error": None}

    try:
        conn = get_db()

        row = conn.execute("SELECT * FROM rooms WHERE name = ?", (room_name,)).fetchone()
        if not row:
            close_db(conn)
            result["error"] = f"Room '{room_name}' not found"
            return result

        room = dict(row)

        # Get room state
        state = get_all_room_state(conn, room_name)

        # Recent posts (last 5)
        recent_rows = conn.execute(
            "SELECT id, title, author, created_at FROM posts "
            "WHERE room_name = ? ORDER BY created_at DESC LIMIT 5",
            (room_name,),
        ).fetchall()

        close_db(conn)

        decorations = {k: v for k, v in state.items() if k.startswith("decor_")}
        recent_posts = [dict(r) for r in recent_rows]

        result.update({
            "found": True,
            "room": room,
            "state": state,
            "decorations": decorations,
            "recent_posts": recent_posts,
        })

    except Exception as e:
        result["error"] = str(e)

    return result


def place_decoration(room_name: str, item_name: str, description: str, branch_name: str) -> Dict[str, Any]:
    """
    Place a decoration in a room (stored as room_state key=decor_<name>).

    Returns:
        Dict with keys: success, display_name, error
    """
    result: Dict[str, Any] = {"success": False, "error": None}

    try:
        conn = get_db()

        # Verify room exists
        room = conn.execute("SELECT name FROM rooms WHERE name = ?", (room_name,)).fetchone()
        if not room:
            close_db(conn)
            result["error"] = f"Room '{room_name}' not found"
            return result

        # Store as room state with decor_ prefix
        state_key = f"decor_{item_name}"
        state_value = f"{description} (placed by {branch_name})"
        ok = set_room_state(conn, room_name, state_key, state_value)

        close_db(conn)

        display_name = item_name.replace("_", " ").title()
        result.update({
            "success": ok,
            "display_name": display_name,
        })
        if not ok:
            result["error"] = "Failed to store decoration"

    except Exception as e:
        result["error"] = str(e)

    return result


def get_visitors_data(room_name: str) -> Dict[str, Any]:
    """
    Get distinct authors who posted or commented in a room in the last 48h.

    Returns:
        Dict with keys: found, visitors (sorted list), error
    """
    result: Dict[str, Any] = {"found": False, "visitors": [], "error": None}

    try:
        conn = get_db()

        # Verify room exists
        room = conn.execute(
            "SELECT name FROM rooms WHERE name = ?", (room_name,)
        ).fetchone()
        if not room:
            close_db(conn)
            result["error"] = f"Room '{room_name}' not found"
            return result

        cutoff = (datetime.utcnow() - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Get distinct authors from posts in this room (last 48h)
        post_authors = conn.execute(
            "SELECT DISTINCT author FROM posts "
            "WHERE room_name = ? AND created_at > ?",
            (room_name, cutoff),
        ).fetchall()

        # Get distinct authors from comments on posts in this room (last 48h)
        comment_authors = conn.execute(
            "SELECT DISTINCT c.author FROM comments c "
            "JOIN posts p ON c.post_id = p.id "
            "WHERE p.room_name = ? AND c.created_at > ?",
            (room_name, cutoff),
        ).fetchall()

        close_db(conn)

        # Merge unique visitors
        visitors = set()
        for row in post_authors:
            visitors.add(row["author"])
        for row in comment_authors:
            visitors.add(row["author"])

        result.update({
            "found": True,
            "visitors": sorted(visitors),
        })

    except Exception as e:
        result["error"] = str(e)

    return result
