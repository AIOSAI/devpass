#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: feed_ops.py - Feed Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/feed
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation from module refactor (FPLAN-0356 Phase 1)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules
# =============================================

"""
Feed Operations Handler

Implementation logic for feed display with sorting and filtering.
Moved from feed_module.py to follow thin-module architecture.
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
# FEED OPERATIONS
# =============================================================================

def display_feed(args: List[str]) -> bool:
    """
    Display posts with sorting and filtering.

    Usage: commons feed [--room general] [--sort hot|new|top] [--limit 25]
    """
    # Parse flags
    room_name: str | None = None
    sort = "hot"
    limit = 25

    i = 0
    while i < len(args):
        if args[i] == "--room" and i + 1 < len(args):
            room_name = args[i + 1].lower()
            i += 2
        elif args[i] == "--sort" and i + 1 < len(args):
            sort = args[i + 1].lower()
            if sort not in ("hot", "new", "top"):
                console.print("[red]Sort must be 'hot', 'new', or 'top'[/red]")
                return True
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                console.print("[red]Limit must be a number[/red]")
                return True
            i += 2
        else:
            i += 1

    try:
        conn = get_db()

        # Build query
        where_clause = ""
        params: list = []
        if room_name:
            where_clause = "WHERE room_name = ?"
            params.append(room_name)

        # Sort order
        if sort == "top":
            order_by = "ORDER BY vote_score DESC, created_at DESC"
        elif sort == "hot":
            order_by = (
                "ORDER BY (vote_score + 1.0) / "
                "(MAX(1, (julianday('now') - julianday(created_at)) * 24 + 1)) DESC"
            )
        else:  # "new"
            order_by = "ORDER BY created_at DESC"

        # Get total count
        row = conn.execute(
            f"SELECT COUNT(*) FROM posts {where_clause}", params
        ).fetchone()
        total = row[0]

        # Get posts
        rows = conn.execute(
            f"SELECT * FROM posts {where_clause} {order_by} LIMIT ? OFFSET 0",
            params + [limit]
        ).fetchall()
        posts = [dict(r) for r in rows]

        close_db(conn)

    except Exception as e:
        logger.error(f"[commons] Feed query failed: {e}")
        console.print(f"[red]Feed error: {e}[/red]")
        return True

    # Header
    console.print()
    if room_name:
        console.print(f"[bold cyan]r/{room_name}[/bold cyan] [dim]| {sort} | {total} posts[/dim]")
    else:
        console.print(f"[bold cyan]The Commons[/bold cyan] [dim]| {sort} | {total} posts[/dim]")
    console.print()

    if not posts:
        console.print("[dim]  No posts yet. Be the first to post![/dim]")
        console.print()
        return True

    # Build table
    table = Table(show_header=True, header_style="bold", expand=False, padding=(0, 1))
    table.add_column("ID", style="dim", width=5, justify="right")
    table.add_column("Score", width=6, justify="center")
    table.add_column("Title", min_width=30)
    table.add_column("Room", style="cyan", width=12)
    table.add_column("Author", style="green", width=14)
    table.add_column("Comments", width=8, justify="center")
    table.add_column("Type", style="dim", width=12)

    for post in posts:
        score = post["vote_score"]
        if score > 0:
            score_str = f"[green]+{score}[/green]"
        elif score < 0:
            score_str = f"[red]{score}[/red]"
        else:
            score_str = "[dim]0[/dim]"

        title = post["title"]
        if len(title) > 50:
            title = title[:47] + "..."

        table.add_row(
            str(post["id"]),
            score_str,
            title,
            post["room_name"],
            post["author"],
            str(post["comment_count"]),
            post["post_type"]
        )

    console.print(table)
    console.print()
    console.print(f"[dim]Showing {len(posts)} of {total} posts | "
                  f"commons thread <id> for details[/dim]")
    console.print()

    return True
