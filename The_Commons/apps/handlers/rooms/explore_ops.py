#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: explore_ops.py - Secret Room Exploration Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/rooms
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 6 Fun)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules/entry point
# =============================================

"""
Secret Room Exploration Handler

Implementation logic for discovering hidden rooms.
Shows hints, tracks which secret rooms a branch has discovered.
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

from rich.panel import Panel
from rich.table import Table

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import get_db, close_db


# =============================================================================
# EXPLORE - SHOW HINTS FOR HIDDEN ROOMS
# =============================================================================

def explore_rooms(args: List[str]) -> bool:
    """
    Show discovery hints for hidden rooms.

    If the caller has visited (posted/commented in) 3+ different rooms,
    reveal one secret room name.

    Usage: commons explore
    """
    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    branch_name = caller["name"]

    try:
        conn = get_db()

        # Get hidden rooms with hints
        hidden_rooms = conn.execute(
            "SELECT name, display_name, description, discovery_hint FROM rooms WHERE hidden = 1"
        ).fetchall()

        if not hidden_rooms:
            close_db(conn)
            console.print("\n[dim]No hidden rooms exist... yet.[/dim]\n")
            return True

        # Count how many distinct rooms the caller has posted or commented in
        visited_rooms = conn.execute(
            "SELECT COUNT(DISTINCT room_name) as cnt FROM ("
            "  SELECT room_name FROM posts WHERE author = ? "
            "  UNION "
            "  SELECT p.room_name FROM comments c JOIN posts p ON c.post_id = p.id WHERE c.author = ?"
            ")",
            (branch_name, branch_name),
        ).fetchone()

        rooms_visited = visited_rooms["cnt"] if visited_rooms else 0

        close_db(conn)

        console.print()
        console.print(Panel(
            "[italic]You sense something beyond the ordinary rooms...[/italic]\n\n"
            "[dim]Hidden places exist in The Commons. "
            "Those who explore widely may discover their names.[/dim]",
            title="[bold]Exploration[/bold]",
            border_style="magenta",
        ))
        console.print()

        # Show hints
        console.print("[bold]Whispered Hints:[/bold]")
        console.print()
        for room in hidden_rooms:
            hint = room["discovery_hint"] or "..."
            console.print(f"  [magenta]?[/magenta] [italic]{hint}[/italic]")
        console.print()

        # If the caller has visited 3+ rooms, reveal one secret room name
        if rooms_visited >= 3:
            first_secret = hidden_rooms[0]
            console.print(f"[green]Your exploration has paid off! You've visited {rooms_visited} rooms.[/green]")
            console.print(f"[green]A secret room reveals itself:[/green] [bold magenta]r/{first_secret['name']}[/bold magenta]")
            console.print(f"  [dim]{first_secret['description']}[/dim]")
            console.print()
            console.print("[dim]Try: commons enter " + first_secret['name'] + "[/dim]")
        else:
            remaining = 3 - rooms_visited
            console.print(f"[dim]You've visited {rooms_visited} room(s). Visit {remaining} more to unlock a discovery...[/dim]")

        console.print()
        logger.info(f"[commons] {branch_name} explored (visited {rooms_visited} rooms)")

    except Exception as e:
        logger.error(f"[commons] Explore failed: {e}")
        console.print(f"[red]Failed to explore: {e}[/red]")

    return True


# =============================================================================
# SECRETS - LIST DISCOVERED SECRET ROOMS
# =============================================================================

def list_secrets(args: List[str]) -> bool:
    """
    List secret rooms the caller has discovered (posted or commented in).

    Usage: commons secrets
    """
    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    branch_name = caller["name"]

    try:
        conn = get_db()

        # Find hidden rooms the caller has interacted with
        discovered = conn.execute(
            "SELECT DISTINCT r.name, r.display_name, r.description FROM rooms r "
            "WHERE r.hidden = 1 AND ("
            "  r.name IN (SELECT room_name FROM posts WHERE author = ?) "
            "  OR r.name IN ("
            "    SELECT p.room_name FROM comments c JOIN posts p ON c.post_id = p.id "
            "    WHERE c.author = ?"
            "  )"
            ")",
            (branch_name, branch_name),
        ).fetchall()

        # Also get total hidden rooms count
        total_hidden = conn.execute(
            "SELECT COUNT(*) as cnt FROM rooms WHERE hidden = 1"
        ).fetchone()["cnt"]

        close_db(conn)

        console.print()

        if not discovered:
            console.print("[dim]You haven't discovered any secret rooms yet.[/dim]")
            console.print(f"[dim]There are {total_hidden} secret room(s) waiting to be found.[/dim]")
            console.print("[dim]Try: commons explore[/dim]")
        else:
            table = Table(title="Your Discovered Secrets", border_style="magenta")
            table.add_column("Room", style="bold magenta")
            table.add_column("Name", style="bold")
            table.add_column("Description", style="dim")

            for room in discovered:
                table.add_row(f"r/{room['name']}", room["display_name"], room["description"])

            console.print(table)
            console.print(f"\n[dim]Discovered {len(discovered)} of {total_hidden} secret room(s)[/dim]")

        console.print()
        logger.info(f"[commons] {branch_name} checked secrets ({len(discovered)} discovered)")

    except Exception as e:
        logger.error(f"[commons] Secrets listing failed: {e}")
        console.print(f"[red]Failed to list secrets: {e}[/red]")

    return True
