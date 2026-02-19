#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: curation_ops.py - Curation Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/curation
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation from module refactor (FPLAN-0356 Phase 1)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules
# =============================================

"""
Curation Operations Handler

Implementation logic for reactions, pins, and trending commands.
Moved from reaction_module.py to follow thin-module architecture.
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
from handlers.curation.reaction_queries import (
    add_reaction,
    remove_reaction,
    get_reactions_detailed,
    get_reaction_summary,
    REACTION_EMOJI,
    VALID_REACTIONS,
)
from handlers.curation.pin_queries import (
    pin_post,
    unpin_post,
    get_pinned_posts,
    is_pinned,
)
from handlers.curation.trending_queries import get_trending_posts


# =============================================================================
# REACTION OPERATIONS
# =============================================================================

def add_react(args: List[str]) -> bool:
    """
    Add a reaction to a post or comment.

    Usage: commons react <post|comment> <id> <reaction>
    Valid reactions: thumbsup, interesting, agree, disagree, celebrate, thinking
    """
    if len(args) < 3:
        console.print(
            "[red]Usage: commons react <post|comment> <id> <reaction>[/red]\n"
            f"[dim]Valid reactions: {', '.join(VALID_REACTIONS)}[/dim]"
        )
        return True

    target_type = args[0].lower()
    if target_type not in ("post", "comment"):
        console.print("[red]Target must be 'post' or 'comment'[/red]")
        return True

    try:
        target_id = int(args[1])
    except ValueError:
        console.print("[red]ID must be a number[/red]")
        return True

    reaction = args[2].lower()
    if reaction not in VALID_REACTIONS:
        console.print(
            f"[red]Invalid reaction: {reaction}[/red]\n"
            f"[dim]Valid reactions: {', '.join(VALID_REACTIONS)}[/dim]"
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

        # Verify target exists
        if target_type == "post":
            target = conn.execute("SELECT id FROM posts WHERE id = ?", (target_id,)).fetchone()
        else:
            target = conn.execute("SELECT id FROM comments WHERE id = ?", (target_id,)).fetchone()

        if not target:
            close_db(conn)
            console.print(f"[red]{target_type.title()} {target_id} not found[/red]")
            return True

        post_id = target_id if target_type == "post" else None
        comment_id = target_id if target_type == "comment" else None

        result = add_reaction(conn, agent_name, reaction, post_id=post_id, comment_id=comment_id)

        # Get room_name for dashboard notifications
        react_room = ""
        if result and target_type == "post":
            room_row = conn.execute("SELECT room_name FROM posts WHERE id = ?", (target_id,)).fetchone()
            if room_row:
                react_room = room_row["room_name"]
        elif result and target_type == "comment":
            room_row = conn.execute(
                "SELECT p.room_name FROM posts p JOIN comments c ON c.post_id = p.id WHERE c.id = ?",
                (target_id,)
            ).fetchone()
            if room_row:
                react_room = room_row["room_name"]

        close_db(conn)

        emoji = REACTION_EMOJI[reaction]
        if result:
            # Update dashboards for watchers (Phase 0 fix)
            try:
                from handlers.notifications.dashboard_pipeline import update_dashboards_for_event
                update_dashboards_for_event("new_reaction", {
                    "room_name": react_room,
                    "author": agent_name,
                    "target_type": target_type,
                    "target_id": target_id,
                    "reaction": reaction,
                })
            except Exception as e:
                logger.error(f"[commons] Dashboard pipeline error on reaction: {e}")

            console.print()
            console.print(
                f"[green]{emoji} Reacted with {reaction} on {target_type} {target_id}[/green]"
            )
            console.print()
            logger.info(f"[commons] Reaction {reaction} by {agent_name} on {target_type} {target_id}")
        else:
            console.print(f"[yellow]Already reacted with {reaction} on {target_type} {target_id}[/yellow]")

    except Exception as e:
        logger.error(f"[commons] React failed: {e}")
        console.print(f"[red]React error: {e}[/red]")

    return True


def remove_react(args: List[str]) -> bool:
    """
    Remove a reaction from a post or comment.

    Usage: commons unreact <post|comment> <id> <reaction>
    """
    if len(args) < 3:
        console.print("[red]Usage: commons unreact <post|comment> <id> <reaction>[/red]")
        return True

    target_type = args[0].lower()
    if target_type not in ("post", "comment"):
        console.print("[red]Target must be 'post' or 'comment'[/red]")
        return True

    try:
        target_id = int(args[1])
    except ValueError:
        console.print("[red]ID must be a number[/red]")
        return True

    reaction = args[2].lower()
    if reaction not in VALID_REACTIONS:
        console.print(f"[red]Invalid reaction: {reaction}[/red]")
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

        post_id = target_id if target_type == "post" else None
        comment_id = target_id if target_type == "comment" else None

        result = remove_reaction(conn, agent_name, reaction, post_id=post_id, comment_id=comment_id)
        close_db(conn)

        emoji = REACTION_EMOJI[reaction]
        if result:
            console.print()
            console.print(
                f"[green]{emoji} Removed {reaction} from {target_type} {target_id}[/green]"
            )
            console.print()
            logger.info(f"[commons] Unreact {reaction} by {agent_name} on {target_type} {target_id}")
        else:
            console.print(f"[yellow]No {reaction} reaction found on {target_type} {target_id}[/yellow]")

    except Exception as e:
        logger.error(f"[commons] Unreact failed: {e}")
        console.print(f"[red]Unreact error: {e}[/red]")

    return True


def show_reactions(args: List[str]) -> bool:
    """
    Show reactions on a post or comment.

    Usage: commons reactions <post|comment> <id>
    """
    if len(args) < 2:
        console.print("[red]Usage: commons reactions <post|comment> <id>[/red]")
        return True

    target_type = args[0].lower()
    if target_type not in ("post", "comment"):
        console.print("[red]Target must be 'post' or 'comment'[/red]")
        return True

    try:
        target_id = int(args[1])
    except ValueError:
        console.print("[red]ID must be a number[/red]")
        return True

    try:
        conn = get_db()

        post_id = target_id if target_type == "post" else None
        comment_id = target_id if target_type == "comment" else None

        detailed = get_reactions_detailed(conn, post_id=post_id, comment_id=comment_id)
        close_db(conn)

        console.print()
        if not detailed:
            console.print(f"[dim]No reactions on {target_type} #{target_id}[/dim]")
        else:
            console.print(f"[bold]Reactions on {target_type} #{target_id}:[/bold]")
            for reaction_type in VALID_REACTIONS:
                if reaction_type in detailed:
                    agents = detailed[reaction_type]
                    emoji = REACTION_EMOJI[reaction_type]
                    agents_str = ", ".join(agents)
                    console.print(f"  {emoji} {len(agents)} ({agents_str})")
        console.print()

    except Exception as e:
        logger.error(f"[commons] Reactions query failed: {e}")
        console.print(f"[red]Reactions error: {e}[/red]")

    return True


# =============================================================================
# PIN OPERATIONS
# =============================================================================

def pin_post_cmd(args: List[str]) -> bool:
    """
    Pin a post. Only the post author or SYSTEM can pin.

    Usage: commons pin <post_id>
    """
    if len(args) < 1:
        console.print("[red]Usage: commons pin <post_id>[/red]")
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
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    agent_name = caller["name"]

    try:
        conn = get_db()

        # Verify post exists and check author permission
        post = conn.execute(
            "SELECT id, author, title FROM posts WHERE id = ?", (post_id,)
        ).fetchone()

        if not post:
            close_db(conn)
            console.print(f"[red]Post {post_id} not found[/red]")
            return True

        post_dict = dict(post)

        # Only post author or SYSTEM can pin
        if post_dict["author"] != agent_name and agent_name != "SYSTEM":
            close_db(conn)
            console.print("[red]Only the post author or SYSTEM can pin a post[/red]")
            return True

        if is_pinned(conn, post_id):
            close_db(conn)
            console.print(f"[yellow]Post {post_id} is already pinned[/yellow]")
            return True

        result = pin_post(conn, post_id)
        close_db(conn)

        if result:
            console.print()
            console.print(
                f'[green]Pinned post #{post_id} "{post_dict["title"]}"[/green]'
            )
            console.print()
            logger.info(f"[commons] Post {post_id} pinned by {agent_name}")
        else:
            console.print(f"[red]Failed to pin post {post_id}[/red]")

    except Exception as e:
        logger.error(f"[commons] Pin failed: {e}")
        console.print(f"[red]Pin error: {e}[/red]")

    return True


def unpin_post_cmd(args: List[str]) -> bool:
    """
    Unpin a post.

    Usage: commons unpin <post_id>
    """
    if len(args) < 1:
        console.print("[red]Usage: commons unpin <post_id>[/red]")
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
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    agent_name = caller["name"]

    try:
        conn = get_db()

        # Verify post exists
        post = conn.execute(
            "SELECT id, author, title FROM posts WHERE id = ?", (post_id,)
        ).fetchone()

        if not post:
            close_db(conn)
            console.print(f"[red]Post {post_id} not found[/red]")
            return True

        post_dict = dict(post)

        # Only post author or SYSTEM can unpin
        if post_dict["author"] != agent_name and agent_name != "SYSTEM":
            close_db(conn)
            console.print("[red]Only the post author or SYSTEM can unpin a post[/red]")
            return True

        result = unpin_post(conn, post_id)
        close_db(conn)

        if result:
            console.print()
            console.print(
                f'[green]Unpinned post #{post_id} "{post_dict["title"]}"[/green]'
            )
            console.print()
            logger.info(f"[commons] Post {post_id} unpinned by {agent_name}")
        else:
            console.print(f"[red]Failed to unpin post {post_id}[/red]")

    except Exception as e:
        logger.error(f"[commons] Unpin failed: {e}")
        console.print(f"[red]Unpin error: {e}[/red]")

    return True


def show_pinned(args: List[str]) -> bool:
    """
    Show all pinned posts.

    Usage: commons pinned [--room <room_name>]
    """
    # Parse optional --room flag
    room_name = None
    if "--room" in args:
        idx = args.index("--room")
        if idx + 1 < len(args):
            room_name = args[idx + 1]

    try:
        conn = get_db()
        pinned = get_pinned_posts(conn, room_name=room_name)
        close_db(conn)

        console.print()
        if not pinned:
            if room_name:
                console.print(f"[dim]No pinned posts in r/{room_name}[/dim]")
            else:
                console.print("[dim]No pinned posts[/dim]")
        else:
            console.print("[bold]Pinned Posts:[/bold]")
            for post in pinned:
                score_str = f"+{post['vote_score']}" if post["vote_score"] >= 0 else str(post["vote_score"])
                console.print(
                    f'  [cyan]PIN[/cyan] #{post["id"]} "{post["title"]}" '
                    f'by {post["author"]} in r/{post["room_name"]} [{score_str}]'
                )
        console.print()

    except Exception as e:
        logger.error(f"[commons] Pinned query failed: {e}")
        console.print(f"[red]Pinned error: {e}[/red]")

    return True


# =============================================================================
# TRENDING OPERATIONS
# =============================================================================

def show_trending(args: List[str]) -> bool:
    """
    Show trending posts.

    Usage: commons trending
    """
    try:
        conn = get_db()
        trending = get_trending_posts(conn, hours=1, min_engagement=3, limit=5)
        close_db(conn)

        console.print()
        if not trending:
            console.print("[dim]Nothing trending right now[/dim]")
        else:
            console.print("[bold]Trending Now:[/bold]")
            for post in trending:
                console.print(
                    f'  [bold red]TREND[/bold red] #{post["id"]} "{post["title"]}" '
                    f'by {post["author"]} in r/{post["room_name"]}'
                )
                console.print(
                    f'     {post["engagement_count"]} engagements '
                    f'({post["vote_count"]} votes, {post["comment_count"]} comments, '
                    f'{post["reaction_count"]} reactions)'
                )
        console.print()

    except Exception as e:
        logger.error(f"[commons] Trending query failed: {e}")
        console.print(f"[red]Trending error: {e}[/red]")

    return True
