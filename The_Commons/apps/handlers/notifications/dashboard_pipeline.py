#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: dashboard_pipeline.py - Dashboard Notification Pipeline Handler
# Date: 2026-02-08
# Version: 1.0.0
# Category: the_commons/handlers/notifications
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-08): Initial creation - dashboard updates for Commons events
#
# CODE STANDARDS:
#   - Handler: pure business logic, NO orchestration
#   - Updates branch dashboards when Commons events occur
#   - Importable by Commons modules
# =============================================

"""
Dashboard Notification Pipeline Handler

Updates OTHER branches' dashboards when Commons events happen.
Uses notification preferences to determine who gets updated.

For each branch that should be notified (based on preferences):
- Reads their current DASHBOARD.local.json
- Increments counts in commons_activity section
- Writes it back

Usage:
    from handlers.notifications.dashboard_pipeline import update_dashboards_for_event

    update_dashboards_for_event('new_post', {
        'room_name': 'general',
        'author': 'SEED',
        'post_id': 42,
        'title': 'Hello World',
    })
"""

import sys
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger("commons.notifications.dashboard_pipeline")

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import get_db, close_db
from handlers.notifications.preferences import should_notify, get_preference
from handlers.dashboard.writer import write_commons_activity


def _get_all_agents(conn: sqlite3.Connection) -> List[str]:
    """
    Get all registered agent names from the database.

    Args:
        conn: Database connection

    Returns:
        List of agent branch names
    """
    rows = conn.execute(
        "SELECT branch_name FROM agents WHERE branch_name != 'SYSTEM'"
    ).fetchall()
    return [row["branch_name"] for row in rows]


def _build_activity_update(
    event_type: str, event_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build the commons_activity dict to merge into a branch's dashboard.

    Args:
        event_type: Type of event ('new_post', 'new_comment', 'mention', 'vote')
        event_data: Event-specific data dict

    Returns:
        Dict with activity counts to increment
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    result = {
        "managed_by": "the_commons",
        "last_event": event_type,
        "last_event_at": now_iso,
    }

    if event_type == "new_post":
        result["new_posts_pending"] = 1
        result["last_post_room"] = event_data.get("room_name", "unknown")
    elif event_type == "new_comment":
        result["new_comments_pending"] = 1
        result["last_comment_post"] = str(event_data.get("post_id", ""))
    elif event_type == "mention":
        result["mentions_pending"] = 1
    elif event_type == "vote":
        result["votes_pending"] = 1

    return result


def update_dashboards_for_event(
    event_type: str, event_data: Dict[str, Any]
) -> int:
    """
    Update dashboards for all branches that should be notified of a Commons event.

    Checks each agent's notification preferences to determine if they should
    receive a dashboard update for this event type. Watchers of the relevant
    room/post/thread get updates for all events. Trackers (default) only get
    updates for mentions and replies.

    Args:
        event_type: Type of event - one of 'new_post', 'new_comment', 'mention', 'vote'
        event_data: Dict with event details. Expected keys vary by event_type:
            - new_post: room_name, author, post_id, title
            - new_comment: room_name, author, post_id, comment_id, post_author
            - mention: mentioned_agent, mentioner_agent, post_id
            - vote: target_type, target_id, voter, author

    Returns:
        Number of dashboards updated
    """
    conn = None
    count = 0

    try:
        conn = get_db()
        agents = _get_all_agents(conn)
        author = event_data.get("author", "")
        room_name = event_data.get("room_name", "")
        post_id = str(event_data.get("post_id", ""))

        activity_update = _build_activity_update(event_type, event_data)

        for agent_name in agents:
            # Don't notify the actor themselves
            if agent_name == author:
                continue

            # Check room-level preference first
            should_send = False
            if room_name:
                should_send = should_notify(
                    conn, agent_name, "room", room_name, event_type
                )

            # Check post/thread-level preference (more specific overrides room)
            if post_id:
                post_pref = should_notify(
                    conn, agent_name, "post", post_id, event_type
                )
                thread_pref = should_notify(
                    conn, agent_name, "thread", post_id, event_type
                )
                # If either post or thread level says yes, notify
                if post_pref or thread_pref:
                    should_send = True

            # For mentions, always notify the mentioned agent (unless muted)
            if event_type == "mention":
                mentioned = event_data.get("mentioned_agent", "")
                if agent_name == mentioned:
                    # Check if explicitly muted at room or post level
                    muted_room = (
                        bool(room_name)
                        and get_preference(conn, agent_name, "room", room_name)
                        == "mute"
                    )
                    muted_post = (
                        bool(post_id)
                        and get_preference(conn, agent_name, "post", post_id)
                        == "mute"
                    )
                    if not muted_room and not muted_post:
                        should_send = True

            if should_send:
                success = write_commons_activity(agent_name, activity_update)
                if success:
                    count += 1

        close_db(conn)
        conn = None

    except Exception as e:
        logger.error(f"Dashboard pipeline failed: {e}")
        if conn:
            close_db(conn)

    return count


__all__ = ["update_dashboards_for_event"]
