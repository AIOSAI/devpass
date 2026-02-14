#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: pin_queries.py - Pin Query Handlers
# Date: 2026-02-08
# Version: 1.0.0
# Category: the_commons/handlers/curation
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-08): Initial creation - pin/unpin/get pinned posts
#
# CODE STANDARDS:
#   - Handler layer - database operations only
#   - Pure sqlite3 stdlib, no external dependencies
#   - Called by reaction_module.py orchestration layer
# =============================================

"""
Pin Query Handlers for The Commons

Database operations for pinning and unpinning posts.
Pinned posts appear at the top of feeds and can be filtered by room.
Pure sqlite3 - no external dependencies.
"""

import sqlite3
from typing import Optional, List, Dict, Any


def pin_post(conn: sqlite3.Connection, post_id: int) -> bool:
    """
    Pin a post (sets pinned=1).

    Args:
        conn: Active database connection
        post_id: The post to pin

    Returns:
        True if found and pinned, False if not found
    """
    cursor = conn.execute(
        "UPDATE posts SET pinned = 1 WHERE id = ?",
        (post_id,),
    )
    conn.commit()
    return cursor.rowcount > 0


def unpin_post(conn: sqlite3.Connection, post_id: int) -> bool:
    """
    Unpin a post (sets pinned=0).

    Args:
        conn: Active database connection
        post_id: The post to unpin

    Returns:
        True if found and unpinned, False if not found
    """
    cursor = conn.execute(
        "UPDATE posts SET pinned = 0 WHERE id = ?",
        (post_id,),
    )
    conn.commit()
    return cursor.rowcount > 0


def get_pinned_posts(
    conn: sqlite3.Connection, room_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get all pinned posts, optionally filtered by room.

    Args:
        conn: Active database connection
        room_name: Optional room filter

    Returns:
        List of dicts with post fields for pinned posts, ordered by created_at DESC
    """
    if room_name:
        rows = conn.execute(
            "SELECT id, title, room_name, author, vote_score, comment_count, created_at "
            "FROM posts WHERE pinned = 1 AND room_name = ? "
            "ORDER BY created_at DESC",
            (room_name,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title, room_name, author, vote_score, comment_count, created_at "
            "FROM posts WHERE pinned = 1 "
            "ORDER BY created_at DESC"
        ).fetchall()

    return [dict(row) for row in rows]


def is_pinned(conn: sqlite3.Connection, post_id: int) -> bool:
    """
    Check if a post is currently pinned.

    Args:
        conn: Active database connection
        post_id: The post to check

    Returns:
        True if pinned, False otherwise
    """
    row = conn.execute(
        "SELECT pinned FROM posts WHERE id = ?",
        (post_id,),
    ).fetchone()

    if not row:
        return False

    return row["pinned"] == 1
