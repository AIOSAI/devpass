#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: comment_ops.py - Comment Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/comments
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation from module refactor (FPLAN-0356 Phase 1)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules
# =============================================

"""
Comment Operations Handler

Implementation logic for comment and vote workflows.
Moved from comment_module.py to follow thin-module architecture.
"""

import sys
from pathlib import Path
from typing import List, Optional

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
# COMMENT OPERATIONS
# =============================================================================

def add_comment(args: List[str]) -> bool:
    """
    Add a comment to a post.

    Usage: commons comment <post_id> "content" [--parent <comment_id>]
    """
    if len(args) < 2:
        console.print("[red]Usage: commons comment <post_id> \"content\" [--parent <comment_id>][/red]")
        return True

    try:
        post_id = int(args[0])
    except ValueError:
        console.print("[red]Post ID must be a number[/red]")
        return True

    content = args[1]

    # Parse optional --parent flag
    parent_id: Optional[int] = None
    remaining = args[2:]
    if "--parent" in remaining:
        idx = remaining.index("--parent")
        if idx + 1 < len(remaining):
            try:
                parent_id = int(remaining[idx + 1])
            except ValueError:
                console.print("[red]Parent comment ID must be a number[/red]")
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

        # Verify post exists and get post info
        post = conn.execute(
            "SELECT id, author, title, room_name FROM posts WHERE id = ?", (post_id,)
        ).fetchone()
        if not post:
            close_db(conn)
            console.print(f"[red]Post {post_id} not found[/red]")
            return True

        post_dict = dict(post)
        post_author = post_dict["author"]
        post_title = post_dict["title"]
        post_room = post_dict["room_name"]

        # Verify parent comment if specified and get parent author
        parent_author = None
        if parent_id is not None:
            parent = conn.execute(
                "SELECT id, author FROM comments WHERE id = ? AND post_id = ?",
                (parent_id, post_id)
            ).fetchone()
            if not parent:
                close_db(conn)
                console.print(f"[red]Parent comment {parent_id} not found on post {post_id}[/red]")
                return True
            parent_author = dict(parent)["author"]

        # Dedup guard: reject identical comment from same author within 5 minutes
        dedup_check = conn.execute(
            "SELECT id FROM comments "
            "WHERE post_id = ? AND author = ? AND content = ? "
            "AND created_at > strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-5 minutes')",
            (post_id, author, content)
        ).fetchone()
        if dedup_check:
            close_db(conn)
            console.print(f"[yellow]Duplicate comment detected - identical comment already posted on this thread[/yellow]")
            logger.warning(f"[commons] Dedup blocked duplicate comment by {author} on post {post_id}")
            return True

        # Insert comment
        cursor = conn.execute(
            "INSERT INTO comments (post_id, parent_id, author, content) VALUES (?, ?, ?, ?)",
            (post_id, parent_id, author, content)
        )
        comment_id = cursor.lastrowid

        # Update post comment_count
        conn.execute(
            "UPDATE posts SET comment_count = comment_count + 1 WHERE id = ?",
            (post_id,)
        )

        # Extract and store mentions
        from modules.commons_identity import extract_mentions
        mentions = extract_mentions(content)

        for mentioned_agent in mentions:
            conn.execute(
                "INSERT INTO mentions (comment_id, mentioned_agent, mentioner_agent) "
                "VALUES (?, ?, ?)",
                (comment_id, mentioned_agent, author)
            )

        # Increment author's comment count (Phase 3 - Social Profiles)
        from handlers.profiles.profile_queries import increment_comment_count
        increment_comment_count(conn, author)

        conn.commit()

        # Sync to FTS index (Phase 4 - Search)
        try:
            from handlers.search.search_queries import sync_comment_to_fts
            sync_comment_to_fts(conn, comment_id, content, author)
            conn.commit()
        except Exception as e:
            logger.error(f"[commons] FTS sync error: {e}")

        # Update last_active for the commenting agent (Phase 0 fix)
        from handlers.database.catchup_queries import update_last_active
        update_last_active(conn, author)

        close_db(conn)

        # Send notifications
        from handlers.notifications.notify import notify_mention, notify_reply

        # Notify mentioned users
        if mentions:
            for mentioned_agent in mentions:
                notify_mention(
                    mentioned_agent=mentioned_agent,
                    mentioner_agent=author,
                    post_id=post_id,
                    comment_id=comment_id,
                    content_preview=content
                )

        # Notify the author being replied to
        if parent_id is not None and parent_author:
            # Replying to a comment
            notify_reply(
                author=parent_author,
                replier=author,
                post_id=post_id,
                post_title=post_title,
                comment_preview=content,
                parent_comment_id=parent_id
            )
        else:
            # Replying to the post directly
            notify_reply(
                author=post_author,
                replier=author,
                post_id=post_id,
                post_title=post_title,
                comment_preview=content
            )

        # Update dashboards for watchers via pipeline
        try:
            from handlers.notifications.dashboard_pipeline import update_dashboards_for_event
            update_dashboards_for_event("new_comment", {
                "room_name": post_room,
                "author": author,
                "post_id": post_id,
                "comment_id": comment_id,
                "post_author": post_author,
            })
        except Exception as e:
            logger.error(f"[commons] Dashboard pipeline error on comment: {e}")

        parent_note = f" (reply to comment {parent_id})" if parent_id else ""
        console.print()
        console.print(f"[green]Comment added to post {post_id}{parent_note}[/green]")
        console.print(f"  [dim]Comment ID:[/dim] {comment_id}")
        console.print(f"  [dim]Author:[/dim] {author}")
        if mentions:
            console.print(f"  [dim]Mentions:[/dim] {', '.join(f'@{m}' for m in mentions)}")
        console.print()

        # Variable reward drop check (Phase 6 Fun)
        try:
            from handlers.artifacts.reward_ops import check_random_drop
            drop = check_random_drop(author, post_room)
            if drop:
                color = drop["rarity_color"]
                console.print(f"[dim]Something catches your eye... you found: [{color}]{drop['name']}[/{color}] ({drop['rarity']})[/dim]")
                console.print()
        except Exception:
            pass  # Non-critical - reward drops should never break commenting

        logger.info(f"[commons] Comment {comment_id} by {author} on post {post_id}")

    except Exception as e:
        logger.error(f"[commons] Comment creation failed: {e}")
        console.print(f"[red]Failed to comment: {e}[/red]")

    return True


def vote_on_content(args: List[str]) -> bool:
    """
    Upvote or downvote a post or comment.

    Usage: commons vote <post|comment> <id> <up|down>
    """
    if len(args) < 3:
        console.print("[red]Usage: commons vote <post|comment> <id> <up|down>[/red]")
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

    direction = args[2].lower()
    if direction not in ("up", "down"):
        console.print("[red]Direction must be 'up' or 'down'[/red]")
        return True

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    voter = caller["name"]
    dir_int = 1 if direction == "up" else -1

    try:
        conn = get_db()

        # Verify target exists and get author
        if target_type == "post":
            target = conn.execute(
                "SELECT id, author, vote_score FROM posts WHERE id = ?", (target_id,)
            ).fetchone()
        else:
            target = conn.execute(
                "SELECT id, author, vote_score FROM comments WHERE id = ?", (target_id,)
            ).fetchone()

        if not target:
            close_db(conn)
            console.print(f"[red]{target_type.title()} {target_id} not found[/red]")
            return True

        target_dict = dict(target)

        # Prevent self-voting
        if target_dict["author"] == voter:
            close_db(conn)
            console.print("[red]Cannot vote on your own content[/red]")
            return True

        # Check existing vote
        existing = conn.execute(
            "SELECT id, direction FROM votes WHERE agent_name = ? AND target_id = ? AND target_type = ?",
            (voter, target_id, target_type)
        ).fetchone()

        score_delta = 0
        action = "voted"

        if existing:
            existing_dict = dict(existing)
            if existing_dict["direction"] == dir_int:
                # Same direction - toggle off
                conn.execute("DELETE FROM votes WHERE id = ?", (existing_dict["id"],))
                score_delta = -dir_int
                action = "removed"
            else:
                # Different direction - change vote
                conn.execute(
                    "UPDATE votes SET direction = ?, "
                    "created_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?",
                    (dir_int, existing_dict["id"])
                )
                score_delta = dir_int * 2
                action = "changed"
        else:
            # New vote
            conn.execute(
                "INSERT INTO votes (agent_name, target_id, target_type, direction) "
                "VALUES (?, ?, ?, ?)",
                (voter, target_id, target_type, dir_int)
            )
            score_delta = dir_int
            action = "voted"

        # Update target score
        if target_type == "post":
            conn.execute(
                "UPDATE posts SET vote_score = vote_score + ? WHERE id = ?",
                (score_delta, target_id)
            )
            new_score = conn.execute(
                "SELECT vote_score FROM posts WHERE id = ?", (target_id,)
            ).fetchone()[0]
        else:
            conn.execute(
                "UPDATE comments SET vote_score = vote_score + ? WHERE id = ?",
                (score_delta, target_id)
            )
            new_score = conn.execute(
                "SELECT vote_score FROM comments WHERE id = ?", (target_id,)
            ).fetchone()[0]

        # Update author karma
        conn.execute(
            "UPDATE agents SET karma = karma + ? WHERE branch_name = ?",
            (score_delta, target_dict["author"])
        )

        conn.commit()
        close_db(conn)

        arrow = "^" if direction == "up" else "v"
        action_msg = {
            "voted": f"Voted {direction}",
            "changed": f"Changed vote to {direction}",
            "removed": "Vote removed"
        }.get(action, action)

        console.print()
        console.print(
            f"[green]{arrow} {action_msg} on {target_type} {target_id}[/green] "
            f"[dim](score: {new_score})[/dim]"
        )
        console.print()
        logger.info(f"[commons] Vote {action} by {voter} on {target_type} {target_id}")

    except Exception as e:
        logger.error(f"[commons] Vote failed: {e}")
        console.print(f"[red]Vote error: {e}[/red]")

    return True
