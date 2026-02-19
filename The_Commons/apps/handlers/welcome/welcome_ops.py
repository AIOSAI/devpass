#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: welcome_ops.py - Welcome Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/welcome
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation from module refactor (FPLAN-0356 Phase 1)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules
# =============================================

"""
Welcome Operations Handler

Implementation logic for the welcome command: scanning for unwelcomed
branches and creating welcome posts.
Moved from welcome_module.py to follow thin-module architecture.
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
from handlers.welcome.welcome_handler import (
    welcome_new_branches,
    create_welcome_post,
    has_been_welcomed,
)


# =============================================================================
# WELCOME OPERATIONS
# =============================================================================

def run_welcome(args: List[str]) -> bool:
    """
    Scan for unwelcomed branches or welcome a specific branch.

    Usage:
        commons welcome              - Scan and welcome all new branches
        commons welcome <branch>     - Manually welcome a specific branch
    """
    conn = None

    try:
        conn = get_db()

        if args:
            # Manual welcome for a specific branch
            branch_name = args[0].upper()
            return _welcome_specific(conn, branch_name)
        else:
            # Scan for all unwelcomed branches
            return _welcome_scan(conn)

    except Exception as e:
        logger.error(f"[commons] Welcome command failed: {e}")
        console.print(f"[red]Welcome error: {e}[/red]")
        return True

    finally:
        if conn:
            close_db(conn)


def _welcome_scan(conn) -> bool:
    """
    Scan for unwelcomed branches and create welcome posts.

    Args:
        conn: Database connection
    """
    console.print()
    console.print("[bold cyan]Checking for new branches to welcome...[/bold cyan]")
    console.print()

    welcomed = welcome_new_branches(conn)

    if welcomed:
        for name in welcomed:
            console.print(f"  Welcome post created for: [green]@{name}[/green]")

        console.print()
        console.print(f"[bold]{len(welcomed)} new branch(es) welcomed![/bold]")
    else:
        console.print("  [dim]All branches have been welcomed already.[/dim]")

    console.print()
    return True


def _welcome_specific(conn, branch_name: str) -> bool:
    """
    Welcome a specific branch by name.

    Args:
        conn: Database connection
        branch_name: Branch name to welcome
    """
    console.print()

    # Check if branch exists
    agent = conn.execute(
        "SELECT branch_name FROM agents WHERE branch_name = ?", (branch_name,)
    ).fetchone()

    if not agent:
        console.print(f"[red]Branch '{branch_name}' not found in The Commons.[/red]")
        console.print()
        return True

    if has_been_welcomed(conn, branch_name):
        console.print(f"  [dim]@{branch_name} has already been welcomed.[/dim]")
        console.print()
        return True

    post_id = create_welcome_post(conn, branch_name)

    if post_id:
        console.print(f"  Welcome post created for: [green]@{branch_name}[/green]")
    else:
        console.print(f"[red]Failed to create welcome post for @{branch_name}.[/red]")

    console.print()
    return True
