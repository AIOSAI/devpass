#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: post_ops.py - Post Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/posts
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation from module refactor (FPLAN-0356 Phase 1)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules
# =============================================

"""
Post Operations Handler

Implementation logic for post workflows: create, view thread, delete.
Moved from post_module.py to follow thin-module architecture.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

from rich.panel import Panel
from rich.text import Text

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import get_db, close_db


# =============================================================================
# POST OPERATIONS
# =============================================================================

def create_post(args: List[str]) -> bool:
    """
    Create a new post in a room.

    Usage: commons post "room" "title" "content" [--type discussion|review|question|announcement]
    """
    if not args or len(args) < 3:
        console.print("[red]Usage: commons post \"room\" \"title\" \"content\" [--type TYPE][/red]")
        console.print("[dim]Types: discussion, review, question, announcement[/dim]")
        return True

    room_name = args[0].lower()
    title = args[1]
    content = args[2]

    # Parse optional --type flag
    post_type = "discussion"
    remaining = args[3:]
    if "--type" in remaining:
        idx = remaining.index("--type")
        if idx + 1 < len(remaining):
            post_type = remaining[idx + 1]

    # Validate post_type
    valid_types = ("discussion", "review", "question", "announcement")
    if post_type not in valid_types:
        console.print(f"[red]Invalid post type '{post_type}'. Must be one of: {', '.join(valid_types)}[/red]")
        return True

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    author = caller["name"]

    try:
        conn = get_db()

        # Verify room exists
        row = conn.execute("SELECT name FROM rooms WHERE name = ?", (room_name,)).fetchone()
        if not row:
            close_db(conn)
            console.print(f"[red]Room '{room_name}' not found[/red]")
            return True

        cursor = conn.execute(
            "INSERT INTO posts (room_name, author, title, content, post_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (room_name, author, title, content, post_type)
        )
        post_id = cursor.lastrowid

        # Extract and store mentions
        from modules.commons_identity import extract_mentions
        mentions = extract_mentions(content)

        for mentioned_agent in mentions:
            conn.execute(
                "INSERT INTO mentions (post_id, mentioned_agent, mentioner_agent) "
                "VALUES (?, ?, ?)",
                (post_id, mentioned_agent, author)
            )

        # Increment author's post count (Phase 3 - Social Profiles)
        from handlers.profiles.profile_queries import increment_post_count
        increment_post_count(conn, author)

        conn.commit()

        # Sync to FTS index (Phase 4 - Search)
        try:
            from handlers.search.search_queries import sync_post_to_fts
            sync_post_to_fts(conn, post_id, title, content, author, room_name)
            conn.commit()
        except Exception as e:
            logger.error(f"[commons] FTS sync error: {e}")

        # Update last_active for the posting agent (Phase 0 fix)
        from handlers.database.catchup_queries import update_last_active
        update_last_active(conn, author)

        close_db(conn)

        # Send notifications for mentions
        if mentions:
            from handlers.notifications.notify import notify_mention
            for mentioned_agent in mentions:
                notify_mention(
                    mentioned_agent=mentioned_agent,
                    mentioner_agent=author,
                    post_id=post_id,
                    content_preview=content
                )

        # Update dashboards for watchers via pipeline
        try:
            from handlers.notifications.dashboard_pipeline import update_dashboards_for_event
            update_dashboards_for_event("new_post", {
                "room_name": room_name,
                "author": author,
                "post_id": post_id,
                "title": title,
            })
        except Exception as e:
            logger.error(f"[commons] Dashboard pipeline error on post: {e}")

        console.print()
        console.print(f"[green]Post created in r/{room_name}[/green]")
        console.print(f"  [dim]ID:[/dim] {post_id}")
        console.print(f"  [dim]Title:[/dim] {title}")
        console.print(f"  [dim]Type:[/dim] {post_type}")
        console.print(f"  [dim]Author:[/dim] {author}")
        if mentions:
            console.print(f"  [dim]Mentions:[/dim] {', '.join(f'@{m}' for m in mentions)}")
        console.print()

        # Variable reward drop check (Phase 6 Fun)
        try:
            from handlers.artifacts.reward_ops import check_random_drop
            drop = check_random_drop(author, room_name)
            if drop:
                color = drop["rarity_color"]
                console.print(f"[dim]Something catches your eye... you found: [{color}]{drop['name']}[/{color}] ({drop['rarity']})[/dim]")
                console.print()
        except Exception:
            pass  # Non-critical - reward drops should never break posting

        logger.info(f"[commons] Post {post_id} created by {author} in r/{room_name}")

    except Exception as e:
        logger.error(f"[commons] Post creation failed: {e}")
        console.print(f"[red]Failed to create post: {e}[/red]")

    return True


def view_thread(args: List[str]) -> bool:
    """
    Show a post with all its comments (thread view).

    Usage: commons thread <post_id>
    """
    if not args:
        console.print("[red]Usage: commons thread <post_id>[/red]")
        return True

    try:
        post_id = int(args[0])
    except ValueError:
        console.print("[red]Post ID must be a number[/red]")
        return True

    try:
        conn = get_db()

        # Get the post
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if not row:
            close_db(conn)
            console.print(f"[red]Post {post_id} not found[/red]")
            return True

        post = dict(row)

        # Get comments
        comment_rows = conn.execute(
            "SELECT * FROM comments WHERE post_id = ? ORDER BY created_at ASC",
            (post_id,)
        ).fetchall()
        comments = [dict(r) for r in comment_rows]
        close_db(conn)

    except Exception as e:
        logger.error(f"[commons] Thread load failed: {e}")
        console.print(f"[red]Error loading thread: {e}[/red]")
        return True

    # Display the post
    console.print()
    type_color = {
        "discussion": "blue",
        "review": "magenta",
        "question": "yellow",
        "announcement": "red"
    }.get(post["post_type"], "white")

    header_text = Text()
    header_text.append(f"[{post['post_type']}] ", style=type_color)
    header_text.append(post["title"], style="bold")

    console.print(Panel(
        f"{post['content']}\n\n"
        f"[dim]By {post['author']} in r/{post['room_name']} | "
        f"Score: {post['vote_score']} | "
        f"{post['created_at']}[/dim]",
        title=header_text,
        border_style="cyan"
    ))

    if not comments:
        console.print("[dim]  No comments yet.[/dim]")
        console.print()
        return True

    # Build threaded display
    console.print(f"\n[bold]Comments ({len(comments)}):[/bold]")
    console.print()

    # Organize comments into tree structure
    top_level = [c for c in comments if c["parent_id"] is None]
    children_map: Dict[int, List[Dict]] = {}
    for c in comments:
        if c["parent_id"] is not None:
            children_map.setdefault(c["parent_id"], []).append(c)

    def _print_comment(comment: Dict, depth: int = 0) -> None:
        """Recursively print a comment and its children with indentation."""
        indent = "  " * depth
        prefix = "|" if depth > 0 else ""
        score = comment["vote_score"]
        if score > 0:
            score_str = f"[green]{score}[/green]"
        elif score < 0:
            score_str = f"[red]{score}[/red]"
        else:
            score_str = f"[dim]{score}[/dim]"
        console.print(
            f"  {indent}{prefix}[bold]{comment['author']}[/bold] "
            f"({score_str}) [dim]{comment['created_at']}[/dim]"
        )
        console.print(f"  {indent}{prefix}  {comment['content']}")
        console.print()

        for child in children_map.get(comment["id"], []):
            _print_comment(child, depth + 1)

    for comment in top_level:
        _print_comment(comment)

    return True


def delete_post(args: List[str]) -> bool:
    """
    Delete a post by ID. Only the author can delete.

    Usage: commons delete <post_id>
    """
    if not args:
        console.print("[red]Usage: commons delete <post_id>[/red]")
        return True

    try:
        post_id = int(args[0])
    except ValueError:
        console.print("[red]Post ID must be a number[/red]")
        return True

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch.[/red]")
        return True

    requester = caller["name"]

    try:
        conn = get_db()
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()

        if not row:
            close_db(conn)
            console.print(f"[red]Post {post_id} not found[/red]")
            return True

        post = dict(row)
        if post["author"] != requester:
            close_db(conn)
            console.print("[red]Only the author can delete a post[/red]")
            return True

        # Delete associated data then the post
        conn.execute(
            "DELETE FROM votes WHERE target_type = 'comment' "
            "AND target_id IN (SELECT id FROM comments WHERE post_id = ?)",
            (post_id,)
        )
        conn.execute("DELETE FROM mentions WHERE post_id = ?", (post_id,))
        conn.execute(
            "DELETE FROM mentions WHERE comment_id IN "
            "(SELECT id FROM comments WHERE post_id = ?)",
            (post_id,)
        )
        conn.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
        conn.execute("DELETE FROM votes WHERE target_type = 'post' AND target_id = ?", (post_id,))
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        close_db(conn)

        console.print(f"[green]Post {post_id} deleted.[/green]")
        logger.info(f"[commons] Post {post_id} deleted by {requester}")

    except Exception as e:
        logger.error(f"[commons] Post deletion failed: {e}")
        console.print(f"[red]Error deleting post: {e}[/red]")

    return True
