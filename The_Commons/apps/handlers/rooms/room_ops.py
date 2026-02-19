#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: room_ops.py - Room Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/rooms
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation from module refactor (FPLAN-0356 Phase 1)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules
# =============================================

"""
Room Operations Handler

Implementation logic for room management: create, list, join.
Moved from room_module.py to follow thin-module architecture.
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

from rich.table import Table

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import get_db, close_db


# =============================================================================
# ROOM OPERATIONS
# =============================================================================

def create_room(args: List[str]) -> bool:
    """
    Create a new discussion room.

    Usage: commons room create "name" "description"
    """
    if len(args) < 2:
        console.print("[red]Usage: commons room create \"name\" \"description\"[/red]")
        return True

    name = args[0].lower().replace(" ", "_")
    description = args[1]

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    created_by = caller["name"]

    try:
        conn = get_db()

        # Check if room already exists
        existing = conn.execute("SELECT name FROM rooms WHERE name = ?", (name,)).fetchone()
        if existing:
            close_db(conn)
            console.print(f"[red]Room '{name}' already exists[/red]")
            return True

        display_name = name.replace("_", " ").title()
        conn.execute(
            "INSERT INTO rooms (name, display_name, description, created_by) VALUES (?, ?, ?, ?)",
            (name, display_name, description, created_by)
        )
        conn.commit()
        close_db(conn)

        console.print()
        console.print(f"[green]Room created: r/{name}[/green]")
        console.print(f"  [dim]Description:[/dim] {description}")
        console.print(f"  [dim]Created by:[/dim] {created_by}")
        console.print()
        logger.info(f"[commons] Room r/{name} created by {created_by}")

    except Exception as e:
        logger.error(f"[commons] Room creation failed: {e}")
        console.print(f"[red]Failed to create room: {e}[/red]")

    return True


def list_rooms(args: List[str]) -> bool:
    """
    Display all available rooms.

    Usage: commons room list
    """
    try:
        conn = get_db()

        rows = conn.execute(
            "SELECT r.*, "
            "  (SELECT COUNT(*) FROM subscriptions s WHERE s.room_name = r.name) as member_count, "
            "  (SELECT COUNT(*) FROM posts p WHERE p.room_name = r.name) as post_count "
            "FROM rooms r "
            "ORDER BY r.name ASC"
        ).fetchall()

        rooms = [dict(r) for r in rows]
        close_db(conn)

    except Exception as e:
        logger.error(f"[commons] Room list failed: {e}")
        console.print(f"[red]Error: {e}[/red]")
        return True

    console.print()
    console.print("[bold cyan]The Commons - Rooms[/bold cyan]")
    console.print()

    if not rooms:
        console.print("[dim]  No rooms yet.[/dim]")
        console.print()
        return True

    table = Table(show_header=True, header_style="bold", expand=False, padding=(0, 1))
    table.add_column("Room", style="cyan", min_width=15)
    table.add_column("Description", min_width=30)
    table.add_column("Posts", width=6, justify="center")
    table.add_column("Members", width=8, justify="center")
    table.add_column("Created By", style="green", width=14)

    for room in rooms:
        table.add_row(
            f"r/{room['name']}",
            room["description"],
            str(room.get("post_count", 0)),
            str(room.get("member_count", 0)),
            room["created_by"]
        )

    console.print(table)
    console.print()

    return True


def join_room(args: List[str]) -> bool:
    """
    Subscribe to a room.

    Usage: commons room join "name"
    """
    if not args:
        console.print("[red]Usage: commons room join \"name\"[/red]")
        return True

    room_name = args[0].lower()

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    branch_name = caller["name"]

    try:
        conn = get_db()

        # Verify room exists
        room = conn.execute("SELECT name FROM rooms WHERE name = ?", (room_name,)).fetchone()
        if not room:
            close_db(conn)
            console.print(f"[red]Room '{room_name}' not found[/red]")
            return True

        # Check if already subscribed
        existing = conn.execute(
            "SELECT agent_name FROM subscriptions WHERE agent_name = ? AND room_name = ?",
            (branch_name, room_name)
        ).fetchone()
        if existing:
            close_db(conn)
            console.print(f"[yellow]Already a member of r/{room_name}[/yellow]")
            return True

        conn.execute(
            "INSERT INTO subscriptions (agent_name, room_name) VALUES (?, ?)",
            (branch_name, room_name)
        )
        conn.commit()
        close_db(conn)

        console.print(f"[green]Joined r/{room_name}[/green]")
        logger.info(f"[commons] {branch_name} joined r/{room_name}")

    except Exception as e:
        logger.error(f"[commons] Room join failed: {e}")
        console.print(f"[red]Failed to join room: {e}[/red]")

    return True
