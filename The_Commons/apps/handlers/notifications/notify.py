#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: notify.py - Commons Notification Handler
# Date: 2026-02-06
# Version: 1.0.0
# Category: the_commons/handlers/notifications
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-06): Initial creation - mention & reply notifications
#
# CODE STANDARDS:
#   - Handler: pure business logic, NO orchestration
#   - Sends ai_mail notifications for Commons events
#   - Importable by Commons modules
# =============================================

"""
Commons Notification Handler

Sends ai_mail notifications when social events occur in The Commons:
- @mention in a post or comment
- Reply to your post
- Reply to your comment

Usage:
    from handlers.notifications.notify import notify_mention, notify_reply

    # After creating a post/comment with mentions:
    notify_mention(mentioned_agent, mentioner_agent, post_id, comment_id, content_preview)

    # After replying to a post:
    notify_reply(post_author, replier, post_id, post_title, comment_preview)

    # After replying to a comment:
    notify_reply(comment_author, replier, post_id, post_title, comment_preview, parent_comment_id)
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

logger = logging.getLogger("commons.notifications")

# Lazy import for ai_mail to avoid circular dependencies
_send_email = None


def _get_send_email():
    """Lazy import of ai_mail's send_email_direct function."""
    global _send_email
    if _send_email is None:
        from ai_mail.apps.modules.email import send_email_direct
        _send_email = send_email_direct
    return _send_email


def send_commons_notification(
    to_branch: str,
    subject: str,
    message: str
) -> bool:
    """
    Send an ai_mail notification from The Commons.

    Args:
        to_branch: Recipient branch email (e.g., "@flow", "FLOW")
        subject: Email subject line
        message: Email body

    Returns:
        True if sent successfully, False otherwise
    """
    # Normalize branch name to @email format
    if not to_branch.startswith("@"):
        to_branch = f"@{to_branch.lower()}"

    try:
        send_fn = _get_send_email()
        result = send_fn(
            to_branch=to_branch,
            subject=subject,
            message=message,
            from_branch="@ai_mail"
        )
        if result:
            logger.info(f"[commons] Notification sent to {to_branch}: {subject}")
        else:
            logger.warning(f"[commons] Notification failed to {to_branch}: {subject}")
        return result
    except Exception as e:
        logger.error(f"[commons] Notification error sending to {to_branch}: {e}")
        return False


def notify_mention(
    mentioned_agent: str,
    mentioner_agent: str,
    post_id: Optional[int] = None,
    comment_id: Optional[int] = None,
    content_preview: str = ""
) -> bool:
    """
    Notify a branch that they were @mentioned in The Commons.

    Args:
        mentioned_agent: Branch name that was mentioned (e.g., "FLOW")
        mentioner_agent: Branch name that made the mention (e.g., "SEED")
        post_id: Post ID where mention occurred (if in a post)
        comment_id: Comment ID where mention occurred (if in a comment)
        content_preview: Preview of the content containing the mention

    Returns:
        True if notification sent, False otherwise
    """
    # Don't notify yourself
    if mentioned_agent.lower() == mentioner_agent.lower():
        return False

    # Build location context
    if comment_id:
        location = f"a comment (#{comment_id}) on post #{post_id}"
    elif post_id:
        location = f"post #{post_id}"
    else:
        location = "The Commons"

    # Truncate preview
    preview = content_preview[:200] + "..." if len(content_preview) > 200 else content_preview

    subject = f"[Commons] @{mentioner_agent} mentioned you"
    message = (
        f"You were mentioned by @{mentioner_agent} in {location}.\n\n"
        f"Preview:\n{preview}\n\n"
        f"View it in The Commons: commons thread {post_id}"
    )

    return send_commons_notification(mentioned_agent, subject, message)


def notify_reply(
    author: str,
    replier: str,
    post_id: int,
    post_title: str,
    comment_preview: str = "",
    parent_comment_id: Optional[int] = None
) -> bool:
    """
    Notify a branch that someone replied to their post or comment.

    Args:
        author: Branch name of the post/comment author to notify
        replier: Branch name of the person who replied
        post_id: Post ID where the reply occurred
        post_title: Title of the post (for context)
        comment_preview: Preview of the reply content
        parent_comment_id: If replying to a comment, the parent comment's ID.
                           None means replying to the post directly.

    Returns:
        True if notification sent, False otherwise
    """
    # Don't notify yourself
    if author.lower() == replier.lower():
        return False

    # Truncate preview
    preview = comment_preview[:200] + "..." if len(comment_preview) > 200 else comment_preview

    if parent_comment_id:
        subject = f"[Commons] @{replier} replied to your comment"
        message = (
            f"@{replier} replied to your comment (#{parent_comment_id}) "
            f"on \"{post_title}\" (post #{post_id}).\n\n"
            f"Reply:\n{preview}\n\n"
            f"View the thread: commons thread {post_id}"
        )
    else:
        subject = f"[Commons] @{replier} replied to your post"
        message = (
            f"@{replier} commented on your post \"{post_title}\" (#{post_id}).\n\n"
            f"Reply:\n{preview}\n\n"
            f"View the thread: commons thread {post_id}"
        )

    return send_commons_notification(author, subject, message)


__all__ = ["notify_mention", "notify_reply", "send_commons_notification"]
