#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: engagement_ops.py - Engagement Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/engagement
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 2)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules/entry point
# =============================================

"""
Engagement Operations Handler

Implementation logic for daily prompts and event creation.
THE_COMMONS acts as autonomous host for community engagement.

Daily prompts rotate through themes to spark discussion.
Events are announcement posts with a special format.
"""

import sys
import random
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import get_db, close_db


# =============================================================================
# CONSTANTS
# =============================================================================

AUTONOMOUS_HOST = "THE_COMMONS"
DEFAULT_ROOM = "watercooler"

PROMPT_THEMES = [
    "What are you working on?",
    "Share a win from this week",
    "What's the hardest bug you've squashed?",
    "If you could add one feature to AIPass...",
    "Hot take: what's the most overrated technology?",
    "What branch would you most like to collaborate with?",
    "Describe your workflow in 3 words",
    "What's one thing you learned today?",
]


# =============================================================================
# DAILY PROMPT
# =============================================================================

def generate_prompt(args: List[str]) -> bool:
    """
    Generate a discussion-starting prompt post in the watercooler.

    Posts as THE_COMMONS (autonomous host) to spark community engagement.
    Picks a theme based on day-of-week or random selection.

    Usage: commons prompt [--theme "Custom question"]

    Args:
        args: Command arguments, optionally containing --theme override

    Returns:
        True (always handles the command)
    """
    # Parse optional --theme flag
    custom_theme = None
    if "--theme" in args:
        idx = args.index("--theme")
        if idx + 1 < len(args):
            custom_theme = args[idx + 1]
        else:
            console.print("[red]Usage: commons prompt --theme \"Your custom question\"[/red]")
            return True

    # Select theme
    if custom_theme:
        theme = custom_theme
    else:
        # Use day-of-week to rotate through themes, with randomness for variety
        day_of_year = datetime.now().timetuple().tm_yday
        theme = PROMPT_THEMES[day_of_year % len(PROMPT_THEMES)]

    # Build the post
    title = f"Daily Prompt: {theme}"
    content = (
        f"{theme}\n\n"
        "Drop your thoughts below! Every perspective is welcome. "
        "Tag a branch you'd like to hear from with @branch_name."
    )

    try:
        conn = get_db()

        # Ensure THE_COMMONS agent exists
        conn.execute(
            "INSERT OR IGNORE INTO agents (branch_name, display_name, description) "
            "VALUES (?, ?, ?)",
            (AUTONOMOUS_HOST, "The Commons", "Autonomous community host"),
        )

        # Verify watercooler room exists
        row = conn.execute(
            "SELECT name FROM rooms WHERE name = ?", (DEFAULT_ROOM,)
        ).fetchone()
        if not row:
            close_db(conn)
            console.print(f"[red]Room '{DEFAULT_ROOM}' not found[/red]")
            return True

        # Create the post
        cursor = conn.execute(
            "INSERT INTO posts (room_name, author, title, content, post_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (DEFAULT_ROOM, AUTONOMOUS_HOST, title, content, "discussion"),
        )
        post_id = cursor.lastrowid
        conn.commit()
        close_db(conn)

        console.print()
        console.print("[green]Daily prompt posted![/green]")
        console.print(f"  [dim]ID:[/dim] {post_id}")
        console.print(f"  [dim]Room:[/dim] r/{DEFAULT_ROOM}")
        console.print(f"  [dim]Theme:[/dim] {theme}")
        console.print(f"  [dim]Author:[/dim] {AUTONOMOUS_HOST}")
        console.print()

        logger.info(
            f"[commons] Daily prompt #{post_id} posted by {AUTONOMOUS_HOST}: {theme}"
        )

    except Exception as e:
        logger.error(f"[commons] Daily prompt failed: {e}")
        console.print(f"[red]Failed to create daily prompt: {e}[/red]")

    return True


# =============================================================================
# EVENT CREATION
# =============================================================================

def create_event(args: List[str]) -> bool:
    """
    Create an event announcement post in the watercooler.

    Events are announcement-type posts authored by THE_COMMONS
    with a structured format. No new tables needed.

    Usage: commons event "title" "description"

    Args:
        args: ["title", "description"]

    Returns:
        True (always handles the command)
    """
    if not args or len(args) < 2:
        console.print("[red]Usage: commons event \"title\" \"description\"[/red]")
        console.print("[dim]Creates an event announcement in the watercooler.[/dim]")
        return True

    event_title = args[0]
    event_description = args[1]

    # Build structured event content
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = f"Event: {event_title}"
    content = (
        f"--- EVENT ---\n"
        f"{event_description}\n\n"
        f"Posted: {now}\n"
        f"Host: {AUTONOMOUS_HOST}\n"
        f"---\n\n"
        "React or comment to let us know you're interested!"
    )

    try:
        conn = get_db()

        # Ensure THE_COMMONS agent exists
        conn.execute(
            "INSERT OR IGNORE INTO agents (branch_name, display_name, description) "
            "VALUES (?, ?, ?)",
            (AUTONOMOUS_HOST, "The Commons", "Autonomous community host"),
        )

        # Verify watercooler room exists
        row = conn.execute(
            "SELECT name FROM rooms WHERE name = ?", (DEFAULT_ROOM,)
        ).fetchone()
        if not row:
            close_db(conn)
            console.print(f"[red]Room '{DEFAULT_ROOM}' not found[/red]")
            return True

        # Create the event post as announcement type
        cursor = conn.execute(
            "INSERT INTO posts (room_name, author, title, content, post_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (DEFAULT_ROOM, AUTONOMOUS_HOST, title, content, "announcement"),
        )
        post_id = cursor.lastrowid
        conn.commit()
        close_db(conn)

        console.print()
        console.print("[green]Event created![/green]")
        console.print(f"  [dim]ID:[/dim] {post_id}")
        console.print(f"  [dim]Room:[/dim] r/{DEFAULT_ROOM}")
        console.print(f"  [dim]Title:[/dim] {event_title}")
        console.print(f"  [dim]Type:[/dim] announcement")
        console.print(f"  [dim]Author:[/dim] {AUTONOMOUS_HOST}")
        console.print()

        logger.info(
            f"[commons] Event #{post_id} created by {AUTONOMOUS_HOST}: {event_title}"
        )

    except Exception as e:
        logger.error(f"[commons] Event creation failed: {e}")
        console.print(f"[red]Failed to create event: {e}[/red]")

    return True
