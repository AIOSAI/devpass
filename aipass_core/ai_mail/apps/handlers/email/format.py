#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: format.py - Email Formatting Handler
# Date: 2025-11-15
# Version: 1.0.0
# Category: ai_mail/handlers/email
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-15): Created - email formatting and display utilities
#
# CODE STANDARDS:
#   - Handler independence: NO cross-domain imports
#   - Can import Prax modules (service providers)
#   - Pure business logic only
# =============================================

"""
Email Formatting Handler

Handles email display formatting, preview generation, and text utilities.
Independent handler - no module dependencies.
"""

import sys
from pathlib import Path
from typing import Dict

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from cli.apps.modules import console


def format_email_preview(message: str, max_length: int = 100) -> str:
    """
    Format email message as preview text.

    Args:
        message: Full email message text
        max_length: Maximum preview length (default: 100)

    Returns:
        Preview text with ellipsis if truncated
    """
    if len(message) <= max_length:
        return message

    return message[:max_length] + "..."


def format_email_header(email_data: Dict) -> str:
    """
    Format email header for display.

    Args:
        email_data: Email data dict with keys:
            - from_name: Sender display name
            - from: Sender email address
            - timestamp: Email timestamp
            - subject: Email subject

    Returns:
        Formatted header string
    """
    lines = [
        "=" * 70,
        f"From: {email_data.get('from_name', 'Unknown')} ({email_data.get('from', 'unknown')})",
        f"Date: {email_data.get('timestamp', 'Unknown')}",
        f"Subject: {email_data.get('subject', 'No Subject')}",
        "=" * 70
    ]
    return "\n".join(lines)


def format_email_list_item(index: int, email_data: Dict, show_unread: bool = True) -> str:
    """
    Format email as list item for inbox/sent display.

    Args:
        index: Item number in list
        email_data: Email data dict
        show_unread: Whether to show unread marker (default: True)

    Returns:
        Formatted list item string
    """
    lines = []

    # Unread marker + ID for copy-paste
    msg_id = email_data.get('id', '????????')
    if show_unread:
        # v2: check status first, fall back to read for backward compat
        status = email_data.get("status")
        is_new = status == "new" if status else not email_data.get("read", False)
        unread_marker = "📨" if is_new else "📬"
        lines.append(f"\n{index}. {unread_marker} \\[{msg_id}] From: {email_data.get('from_name', 'Unknown')} @ {email_data.get('timestamp', 'Unknown')}")
    else:
        lines.append(f"\n{index}. \\[{msg_id}] To: {email_data.get('to', 'Unknown')} @ {email_data.get('timestamp', 'Unknown')}")

    lines.append(f"   Subject: {email_data.get('subject', 'No Subject')}")

    # Preview
    message = email_data.get('message', '')
    preview = format_email_preview(message, 100)
    lines.append(f"   {preview}")

    return "\n".join(lines)


def format_inbox_summary(total_messages: int, unread_count: int) -> str:
    """
    Format inbox summary statistics.

    Args:
        total_messages: Total number of messages
        unread_count: Number of unread messages

    Returns:
        Formatted summary string
    """
    return f"📊 Total: {total_messages} messages ({unread_count} unread)"


def format_branch_email(branch_name: str) -> str:
    """
    Derive email address from branch name.

    Args:
        branch_name: Branch name (e.g., "AIPASS.admin", "DRONE", "AIPASS-HELP")

    Returns:
        Email address (e.g., "@admin", "@drone", "@help")
    """
    if '.' in branch_name:
        # Special case: AIPASS.admin -> admin
        email_part = branch_name.split('.')[-1].lower()
    elif ' ' in branch_name:
        # Handle spaces: take first word
        email_part = branch_name.split()[0].lower()
    elif '-' in branch_name and branch_name.split('-')[0] == 'AIPASS':
        # AIPASS-prefixed branches: use second part to avoid collision
        email_part = branch_name.split('-', 1)[1].lower()
    else:
        # Take first word before hyphen or whole name
        email_part = branch_name.split('-')[0].lower()

    return f"@{email_part}"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated (default: "...")

    Returns:
        Truncated text with suffix if needed
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


if __name__ == "__main__":
    console.print("\n" + "="*70)
    console.print("EMAIL FORMATTING HANDLER")
    console.print("="*70)
    console.print("\nPURPOSE:")
    console.print("  Email display formatting and text utilities")
    console.print()
    console.print("FUNCTIONS PROVIDED:")
    console.print("  - format_email_preview(message, max_length) -> str")
    console.print("  - format_email_header(email_data) -> str")
    console.print("  - format_email_list_item(index, email_data, show_unread) -> str")
    console.print("  - format_inbox_summary(total_messages, unread_count) -> str")
    console.print("  - format_branch_email(branch_name) -> str")
    console.print("  - truncate_text(text, max_length, suffix) -> str")
    console.print()
    console.print("HANDLER CHARACTERISTICS:")
    console.print("  ✓ Independent - no module dependencies")
    console.print("  ✓ Can import Prax (service provider)")
    console.print("  ✓ Pure business logic")
    console.print("  ✗ CANNOT import parent modules")
    console.print()
    console.print("USAGE FROM MODULES:")
    console.print("  from ai_mail.apps.handlers.email.format import format_email_preview")
    console.print("  from ai_mail.apps.handlers.email.format import format_email_header")
    console.print()
    console.print("="*70 + "\n")
