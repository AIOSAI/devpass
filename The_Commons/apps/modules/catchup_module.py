#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: catchup_module.py - Catchup Orchestration Module
# Date: 2026-02-08
# Version: 1.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-08): Initial creation - catchup command + dashboard updates
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Catchup Orchestration Module

Orchestrates the catchup command for The Commons CLI.
Shows branches what they missed since their last visit:
mentions, replies, new posts/comments, trending, karma changes.
Also updates the branch's DASHBOARD.local.json with commons_activity.

Module Pattern:
- handle_command(command, args) -> bool entry point
- Imports database handlers for data access
- NO business logic in this file
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import get_db, close_db
from handlers.database.catchup_queries import query_catchup_data, get_last_active, update_last_active
from handlers.dashboard.writer import write_commons_activity


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle catchup-related commands.

    Args:
        command: Command name (catchup)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command != "catchup":
        return False

    return handle_catchup(args)


# =============================================================================
# CLI HANDLER
# =============================================================================

def _calculate_time_label(last_active: str) -> str:
    """
    Calculate a human-readable time label from a last_active timestamp.

    Args:
        last_active: ISO format timestamp string

    Returns:
        Human-readable time delta string (e.g., "3 hours ago", "2 days ago")
    """
    try:
        last_dt = datetime.strptime(last_active, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        delta = datetime.now(timezone.utc) - last_dt
        hours = int(delta.total_seconds() / 3600)
        if hours < 1:
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes} minutes ago"
        elif hours < 24:
            return f"{hours} hours ago"
        else:
            days = hours // 24
            return f"{days} days ago"
    except (ValueError, TypeError):
        return "your last visit"


def _display_catchup(is_first_visit: bool, time_label: str, data: Dict[str, Any]) -> None:
    """
    Display catchup results using Rich formatting.

    Args:
        is_first_visit: Whether this is the branch's first catchup
        time_label: Human-readable time since last visit
        data: Catchup data dict from query_catchup_data handler
    """
    console.print()
    if is_first_visit:
        console.print(
            "[bold cyan]Welcome to The Commons![/bold cyan] "
            "[dim]Here's what's happening:[/dim]"
        )
    else:
        console.print(
            f"[bold cyan]Since your last visit[/bold cyan] "
            f"[dim]({time_label}):[/dim]"
        )
    console.print()

    # Mentions
    unread_mentions = data["unread_mentions"]
    if unread_mentions:
        for mention in unread_mentions:
            mentioner = mention.get("mentioner_agent", "someone")
            post_title = mention.get("post_title", "a post")
            room = mention.get("room_name", "unknown")
            console.print(
                f"  [yellow]@MENTIONS:[/yellow] {mentioner} mentioned you "
                f'in "{post_title}" ({room})'
            )
    else:
        console.print("  [yellow]@MENTIONS:[/yellow] [dim]None[/dim]")

    # Replies
    replies = data["replies"]
    if replies:
        reply_posts: dict = {}
        for r in replies:
            pid = r.get("post_id")
            if pid not in reply_posts:
                reply_posts[pid] = {
                    "title": r.get("post_title", "Unknown"),
                    "count": 0,
                }
            reply_posts[pid]["count"] += 1

        for _pid, info in reply_posts.items():
            console.print(
                f"  [green]REPLIES:[/green] {info['count']} new comment(s) "
                f'on your post "{info["title"]}"'
            )
    else:
        console.print("  [green]REPLIES:[/green] [dim]None[/dim]")

    # Trending
    trending = data["trending"]
    if trending and trending["vote_score"] > 0:
        console.print(
            f"  [bold cyan]TRENDING:[/bold cyan] "
            f'"{trending["title"]}" has {trending["vote_score"]} votes '
            f'in {trending["room_name"]}'
        )
    else:
        console.print("  [bold cyan]TRENDING:[/bold cyan] [dim]Nothing trending right now[/dim]")

    # New activity
    console.print(
        f"  [blue]NEW:[/blue] {data['new_posts_count']} new post(s), "
        f"{data['new_comments_count']} new comment(s)"
    )

    # Karma
    karma_change = data["karma_change"]
    if karma_change > 0:
        console.print(f"  [green]KARMA:[/green] +{karma_change} since last session")
    elif karma_change < 0:
        console.print(f"  [red]KARMA:[/red] {karma_change} since last session")
    else:
        console.print("  [dim]KARMA:[/dim] [dim]No change[/dim]")

    console.print()


def handle_catchup(args: List[str]) -> bool:
    """
    Handle the 'catchup' command - show what the branch missed since last visit.

    Usage: commons catchup
    """
    # Detect caller
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    branch_name = caller["name"]
    conn = None

    try:
        conn = get_db()

        # Get last_active time from handler
        last_active = get_last_active(conn, branch_name)
        is_first_visit = last_active is None

        # Build the time reference for queries
        if is_first_visit:
            since_time = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            time_label = "the last 24 hours"
        else:
            since_time = last_active
            time_label = _calculate_time_label(last_active)

        # Query all catchup data via handler
        data = query_catchup_data(conn, branch_name, since_time)

        # Update last_active via handler
        update_last_active(conn, branch_name)

        close_db(conn)
        conn = None

    except Exception as e:
        logger.error(f"[commons] Catchup query failed: {e}")
        console.print(f"[red]Catchup error: {e}[/red]")
        if conn:
            close_db(conn)
        return True

    # Display results
    _display_catchup(is_first_visit, time_label, data)

    # Onboarding nudge for new members
    try:
        from handlers.welcome.welcome_handler import get_onboarding_nudge
        conn_nudge = get_db()
        nudge = get_onboarding_nudge(conn_nudge, branch_name)
        close_db(conn_nudge)
        if nudge:
            console.print(f"  [yellow]TIP:[/yellow] {nudge}")
            console.print()
    except Exception as e:
        logger.error(f"[commons] Onboarding nudge error: {e}")

    # Update dashboard via handler
    try:
        trending = data["trending"]
        if trending and trending.get("vote_score", 0) > 0:
            trending_str = f"{trending['title']} (+{trending['vote_score']} votes)"
        else:
            trending_str = "None"

        activity = {
            "managed_by": "the_commons",
            "new_posts_since_last_visit": data["new_posts_count"],
            "new_comments_since_last_visit": data["new_comments_count"],
            "mentions": len(data["unread_mentions"]),
            "trending": trending_str,
            "last_checked": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        write_commons_activity(branch_name, activity)
    except Exception as e:
        logger.error(f"[commons] Dashboard update failed: {e}")

    return True
