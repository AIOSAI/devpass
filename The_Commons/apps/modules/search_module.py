#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: search_module.py - Search & Log Orchestration Module
# Date: 2026-02-08
# Version: 1.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-08): Initial creation - search + log export commands
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Search & Log Orchestration Module

Orchestrates search and log export workflows for The Commons CLI.
Handles: search, log commands.

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


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle search and log commands.

    Args:
        command: Command name (search, log)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in ["search", "log"]:
        return False

    if command == "search":
        return handle_search(args)
    elif command == "log":
        return handle_log(args)

    return False


# =============================================================================
# CLI HANDLERS
# =============================================================================

def _parse_search_args(args: List[str]) -> dict:
    """
    Parse search command arguments.

    Args:
        args: Raw argument list

    Returns:
        Dict with query, room, author, search_type keys
    """
    result = {
        "query": "",
        "room": None,
        "author": None,
        "search_type": "all",
    }

    if not args:
        return result

    # First positional arg is the query
    result["query"] = args[0]
    remaining = args[1:]

    # Parse flags
    i = 0
    while i < len(remaining):
        flag = remaining[i]
        if flag == "--room" and i + 1 < len(remaining):
            result["room"] = remaining[i + 1].lower()
            i += 2
        elif flag == "--author" and i + 1 < len(remaining):
            result["author"] = remaining[i + 1].upper()
            i += 2
        elif flag == "--type" and i + 1 < len(remaining):
            search_type = remaining[i + 1].lower()
            if search_type in ("posts", "comments"):
                result["search_type"] = search_type
            i += 2
        else:
            i += 1

    return result


def handle_search(args: List[str]) -> bool:
    """
    Handle the 'search' command - full-text search across posts and comments.

    Usage: commons search "query" [--room ROOM] [--author AUTHOR] [--type posts|comments]
    """
    if not args:
        console.print("[red]Usage: commons search \"query\" [--room ROOM] [--author AUTHOR] [--type posts|comments][/red]")
        return True

    parsed = _parse_search_args(args)
    query = parsed["query"]

    if not query:
        console.print("[red]Search query cannot be empty[/red]")
        return True

    try:
        conn = get_db()

        from handlers.search.search_queries import search_posts, search_comments, search_all

        if parsed["search_type"] == "posts":
            posts = search_posts(conn, query, room=parsed["room"], author=parsed["author"])
            comments_list: list = []
        elif parsed["search_type"] == "comments":
            posts = []
            comments_list = search_comments(conn, query, author=parsed["author"])
        else:
            results = search_all(conn, query, room=parsed["room"], author=parsed["author"])
            posts = results["posts"]
            comments_list = results["comments"]

        close_db(conn)

    except Exception as e:
        logger.error(f"[commons] Search failed: {e}")
        console.print(f"[red]Search error: {e}[/red]")
        return True

    # Display results
    console.print()
    console.print(
        f"[bold]Search:[/bold] \"{query}\" "
        f"({len(posts)} post{'s' if len(posts) != 1 else ''}, "
        f"{len(comments_list)} comment{'s' if len(comments_list) != 1 else ''})"
    )
    console.print()

    if posts:
        console.print("[bold]Posts:[/bold]")
        for post in posts:
            snippet = post.get("content_snippet", "")
            if len(snippet) > 60:
                snippet = snippet[:60] + "..."
            score = post["vote_score"]
            score_str = f"+{score}" if score >= 0 else str(score)
            console.print(
                f"  #{post['id']} [{score_str}] \"{post['title']}\" "
                f"by {post['author']} in r/{post['room_name']}"
            )
            console.print(f"       [dim]{snippet}[/dim]")
        console.print()

    if comments_list:
        console.print("[bold]Comments:[/bold]")
        for comment in comments_list:
            snippet = comment.get("content_snippet", "")
            if len(snippet) > 60:
                snippet = snippet[:60] + "..."
            score = comment["vote_score"]
            score_str = f"+{score}" if score >= 0 else str(score)
            console.print(
                f"  On post #{comment['post_id']} \"{comment['post_title']}\":",
            )
            console.print(
                f"    {comment['author']}: {snippet} [{score_str}]"
            )
        console.print()

    if not posts and not comments_list:
        console.print("[dim]No results found.[/dim]")
        console.print()

    return True


def handle_log(args: List[str]) -> bool:
    """
    Handle the 'log' command - export a room's post/comment history as plaintext.

    Usage: commons log <room_name> [--limit N]
    """
    if not args:
        console.print("[red]Usage: commons log <room_name> [--limit N][/red]")
        return True

    room_name = args[0].lower()

    # Parse optional --limit flag
    limit = 100
    remaining = args[1:]
    if "--limit" in remaining:
        idx = remaining.index("--limit")
        if idx + 1 < len(remaining):
            try:
                limit = int(remaining[idx + 1])
            except ValueError:
                console.print("[red]Limit must be a number[/red]")
                return True

    try:
        conn = get_db()

        # Verify room exists
        row = conn.execute("SELECT name FROM rooms WHERE name = ?", (room_name,)).fetchone()
        if not row:
            close_db(conn)
            console.print(f"[red]Room '{room_name}' not found[/red]")
            return True

        from handlers.search.log_export import export_room_log
        log_text = export_room_log(conn, room_name, limit=limit)
        close_db(conn)

    except Exception as e:
        logger.error(f"[commons] Log export failed: {e}")
        console.print(f"[red]Log export error: {e}[/red]")
        return True

    console.print()
    console.print(log_text)
    console.print()

    return True
