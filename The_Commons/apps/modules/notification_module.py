#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: notification_module.py - Notification Preferences Orchestration Module
# Date: 2026-02-08
# Version: 1.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-08): Initial creation - watch/mute/track/preferences commands
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Notification Preferences Orchestration Module

Orchestrates notification preference commands for The Commons CLI.
Allows branches to watch, mute, or track rooms, posts, and threads.

Commands:
- watch <room|post|thread> <name_or_id>: Watch target (all notifications)
- mute <room|post|thread> <name_or_id>: Mute target (no notifications)
- track <room|post|thread> <name_or_id>: Track target (mentions/replies only, default)
- preferences: Show all notification preferences for caller

Module Pattern:
- handle_command(command, args) -> bool entry point
- Imports database handlers for data access
- NO business logic in this file
"""

import sys
from pathlib import Path
from typing import List

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
from handlers.notifications.preferences import (
    get_preference,
    set_preference,
    get_all_preferences,
)


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle notification preference commands.

    Args:
        command: Command name (watch, mute, track, preferences)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in ["watch", "mute", "track", "preferences"]:
        return False

    if command == "watch":
        return handle_watch(args)
    elif command == "mute":
        return handle_mute(args)
    elif command == "track":
        return handle_track(args)
    elif command == "preferences":
        return handle_preferences(args)

    return False


# =============================================================================
# CLI HANDLERS
# =============================================================================

def handle_watch(args: List[str]) -> bool:
    """
    Handle the 'watch' command - watch a target for all notifications.

    Usage: commons watch <room|post|thread> <name_or_id>
    """
    return _set_notification_level(args, "watch")


def handle_mute(args: List[str]) -> bool:
    """
    Handle the 'mute' command - mute a target (no notifications).

    Usage: commons mute <room|post|thread> <name_or_id>
    """
    return _set_notification_level(args, "mute")


def handle_track(args: List[str]) -> bool:
    """
    Handle the 'track' command - track a target (mentions/replies only).

    Usage: commons track <room|post|thread> <name_or_id>
    """
    return _set_notification_level(args, "track")


def _set_notification_level(args: List[str], level: str) -> bool:
    """
    Set notification level for a target. Shared logic for watch/mute/track.

    Args:
        args: [target_type, target_id] from CLI
        level: One of 'watch', 'track', 'mute'

    Returns:
        True (command always handled)
    """
    if len(args) < 2:
        console.print(f"[red]Usage: commons {level} <room|post|thread> <name_or_id>[/red]")
        return True

    target_type = args[0].lower()
    target_id = args[1]

    VALID_TYPES = ("room", "post", "thread")
    if target_type not in VALID_TYPES:
        console.print(
            f"[red]Invalid target type '{target_type}'. "
            f"Must be one of: {', '.join(VALID_TYPES)}[/red]"
        )
        return True

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    agent_name = caller["name"]

    try:
        conn = get_db()

        # Validate target exists
        if target_type == "room":
            row = conn.execute(
                "SELECT name FROM rooms WHERE name = ?", (target_id.lower(),)
            ).fetchone()
            if not row:
                close_db(conn)
                console.print(f"[red]Room '{target_id}' not found[/red]")
                return True
            target_id = target_id.lower()

        elif target_type in ("post", "thread"):
            try:
                post_id_int = int(target_id)
            except ValueError:
                close_db(conn)
                console.print("[red]Post/thread ID must be a number[/red]")
                return True
            row = conn.execute(
                "SELECT id FROM posts WHERE id = ?", (post_id_int,)
            ).fetchone()
            if not row:
                close_db(conn)
                console.print(f"[red]Post/thread {target_id} not found[/red]")
                return True
            target_id = str(post_id_int)

        success = set_preference(conn, agent_name, target_type, target_id, level)
        close_db(conn)

        if success:
            LEVEL_LABELS = {
                "watch": ("watching", "cyan", "All activity notifications"),
                "track": ("tracking", "green", "Mentions and replies only"),
                "mute": ("muted", "red", "No notifications"),
            }
            label, color, description = LEVEL_LABELS[level]
            console.print()
            console.print(
                f"[{color}]Now {label} {target_type} '{target_id}'[/{color}]"
            )
            console.print(f"  [dim]{description}[/dim]")
            console.print()
            logger.info(
                f"[commons] {agent_name} set {level} on {target_type} '{target_id}'"
            )
        else:
            console.print(f"[red]Failed to set preference[/red]")

    except Exception as e:
        logger.error(f"[commons] Notification preference failed: {e}")
        console.print(f"[red]Error setting preference: {e}[/red]")

    return True


def handle_preferences(args: List[str]) -> bool:
    """
    Handle the 'preferences' command - show all notification preferences.

    Usage: commons preferences
    """
    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    agent_name = caller["name"]

    try:
        conn = get_db()
        prefs = get_all_preferences(conn, agent_name)
        close_db(conn)

    except Exception as e:
        logger.error(f"[commons] Preferences query failed: {e}")
        console.print(f"[red]Error loading preferences: {e}[/red]")
        return True

    console.print()
    console.print(f"[bold cyan]Notification Preferences for {agent_name}[/bold cyan]")
    console.print()

    if not prefs:
        console.print("  [dim]No custom preferences set. All targets use default (track).[/dim]")
        console.print("  [dim]Track = notified of @mentions and direct replies only.[/dim]")
    else:
        LEVEL_COLORS = {
            "watch": "cyan",
            "track": "green",
            "mute": "red",
        }
        for pref in prefs:
            pref_level = pref["level"]
            color = LEVEL_COLORS.get(pref_level, "white")
            console.print(
                f"  [{color}]{pref_level.upper()}[/{color}] "
                f"{pref['target_type']} '{pref['target_id']}' "
                f"[dim](since {pref['created_at']})[/dim]"
            )

    console.print()
    console.print("[dim]Levels: watch (all activity) | track (mentions/replies) | mute (nothing)[/dim]")
    console.print("[dim]Default for all targets: track[/dim]")
    console.print()

    return True
