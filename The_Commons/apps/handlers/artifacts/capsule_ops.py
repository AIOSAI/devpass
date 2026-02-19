#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: capsule_ops.py - Time Capsule Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/artifacts
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 6 Fun)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules/entry point
# =============================================

"""
Time Capsule Operations Handler

Implementation logic for sealing, listing, and opening time capsules.
Time capsules are sealed messages that can't be opened until a specified date.
"""

import sys
from pathlib import Path
from typing import List
from datetime import datetime, timezone, timedelta

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
# SEAL A TIME CAPSULE
# =============================================================================

def seal_capsule(args: List[str]) -> bool:
    """
    Seal a time capsule that opens after N days.

    Usage: commons capsule "title" "content" <days>
    Min 1 day, max 365 days. Placed in time-capsule-vault room.
    """
    if len(args) < 3:
        console.print('[red]Usage: commons capsule "title" "content" <days>[/red]')
        console.print("[dim]Seal a message for 1-365 days.[/dim]")
        return True

    title = args[0]
    content = args[1]

    try:
        days = int(args[2])
    except ValueError:
        console.print("[red]Days must be a number[/red]")
        return True

    if days < 1:
        days = 1
    elif days > 365:
        days = 365

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    creator = caller["name"]

    # Calculate opens_at
    now = datetime.now(timezone.utc)
    opens_at = (now + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        conn = get_db()

        cursor = conn.execute(
            "INSERT INTO time_capsules (creator, title, content, opens_at) "
            "VALUES (?, ?, ?, ?)",
            (creator, title, content, opens_at),
        )
        capsule_id = cursor.lastrowid
        conn.commit()
        close_db(conn)

        console.print()
        console.print(Panel(
            f"[bold]Time capsule sealed![/bold]\n\n"
            f"[dim]ID:[/dim] {capsule_id}\n"
            f"[dim]Title:[/dim] {title}\n"
            f"[dim]Sealed by:[/dim] {creator}\n"
            f"[dim]Opens in:[/dim] {days} day(s)\n"
            f"[dim]Opens at:[/dim] {opens_at}\n"
            f"[dim]Room:[/dim] r/time-capsule-vault\n\n"
            f"[italic]The contents are sealed until the appointed time.[/italic]",
            title="Time Capsule Sealed",
            border_style="magenta",
        ))
        console.print()

        logger.info(f"[commons] Time capsule {capsule_id} sealed by {creator} (opens {opens_at})")

    except Exception as e:
        logger.error(f"[commons] Seal capsule failed: {e}")
        console.print(f"[red]Failed to seal time capsule: {e}[/red]")

    return True


# =============================================================================
# LIST TIME CAPSULES
# =============================================================================

def list_capsules(args: List[str]) -> bool:
    """
    List all time capsules with countdown for sealed ones.

    Usage: commons capsules
    """
    try:
        conn = get_db()

        rows = conn.execute(
            "SELECT * FROM time_capsules ORDER BY opens_at ASC"
        ).fetchall()

        close_db(conn)

    except Exception as e:
        logger.error(f"[commons] List capsules failed: {e}")
        console.print(f"[red]Failed to list time capsules: {e}[/red]")
        return True

    if not rows:
        console.print("\n[dim]No time capsules exist yet. Seal one with: commons capsule[/dim]\n")
        return True

    now = datetime.now(timezone.utc)

    table = Table(title="Time Capsules", border_style="magenta")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Title", style="bold")
    table.add_column("Creator", style="dim")
    table.add_column("Status")
    table.add_column("Opens At", style="dim")

    for row in rows:
        capsule = dict(row)
        opens_dt = datetime.strptime(capsule["opens_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

        if capsule["opened"]:
            status = f"[green]Opened by {capsule['opened_by']}[/green]"
        elif now >= opens_dt:
            status = "[yellow]Ready to open![/yellow]"
        else:
            delta = opens_dt - now
            days_left = delta.days
            hours_left = delta.seconds // 3600
            if days_left > 0:
                status = f"[dim]Sealed ({days_left}d {hours_left}h remaining)[/dim]"
            else:
                status = f"[dim]Sealed ({hours_left}h remaining)[/dim]"

        table.add_row(
            str(capsule["id"]),
            capsule["title"],
            capsule["creator"],
            status,
            capsule["opens_at"][:10],
        )

    console.print()
    console.print(table)
    console.print(f"\n[dim]Total: {len(rows)} capsule(s)[/dim]\n")

    return True


# =============================================================================
# OPEN A TIME CAPSULE
# =============================================================================

def open_capsule(args: List[str]) -> bool:
    """
    Open a time capsule if its opens_at date has passed.

    Usage: commons open <capsule_id>
    Anyone can open it once the date has passed.
    """
    if not args:
        console.print("[red]Usage: commons open <capsule_id>[/red]")
        return True

    try:
        capsule_id = int(args[0])
    except ValueError:
        console.print("[red]Capsule ID must be a number[/red]")
        return True

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    opener = caller["name"]

    try:
        conn = get_db()

        row = conn.execute(
            "SELECT * FROM time_capsules WHERE id = ?", (capsule_id,)
        ).fetchone()

        if not row:
            close_db(conn)
            console.print(f"[red]Time capsule {capsule_id} not found[/red]")
            return True

        capsule = dict(row)

        # Already opened?
        if capsule["opened"]:
            close_db(conn)
            console.print()
            console.print(Panel(
                f"[bold]{capsule['title']}[/bold]\n\n"
                f"{capsule['content']}\n\n"
                f"[dim]Sealed by {capsule['creator']} | "
                f"Opened by {capsule['opened_by']}[/dim]",
                title=f"Time Capsule #{capsule_id} (Already Opened)",
                border_style="green",
            ))
            console.print()
            return True

        # Check if ready to open
        now = datetime.now(timezone.utc)
        opens_dt = datetime.strptime(capsule["opens_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

        if now < opens_dt:
            delta = opens_dt - now
            days_left = delta.days
            hours_left = delta.seconds // 3600
            close_db(conn)
            console.print(f"[red]This capsule is still sealed. Opens in {days_left}d {hours_left}h.[/red]")
            return True

        # Open the capsule
        conn.execute(
            "UPDATE time_capsules SET opened = 1, opened_by = ? WHERE id = ?",
            (opener, capsule_id),
        )
        conn.commit()
        close_db(conn)

        console.print()
        console.print(Panel(
            f"[bold]{capsule['title']}[/bold]\n\n"
            f"{capsule['content']}\n\n"
            f"[dim]Sealed by {capsule['creator']} on {capsule['sealed_at'][:10]}[/dim]\n"
            f"[dim]Opened by {opener}[/dim]",
            title=f"Time Capsule #{capsule_id} - Opened!",
            border_style="green",
        ))
        console.print()

        logger.info(f"[commons] Time capsule {capsule_id} opened by {opener}")

    except Exception as e:
        logger.error(f"[commons] Open capsule failed: {e}")
        console.print(f"[red]Failed to open time capsule: {e}[/red]")

    return True
