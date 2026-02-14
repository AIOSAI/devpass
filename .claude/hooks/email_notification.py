#!/usr/bin/env python3
"""
Email Notification Hook - Notifies users of new emails on prompt submit

Checks the current branch's inbox for unread emails (status: "new" or read: false)
and displays a notification if any exist.

Part of AI_MAIL Phase 4: Hook Notification for the Email Lifecycle v2

Version: 1.0.0
Created: 2025-11-30
"""
import json
from pathlib import Path

AIPASS_ROOT = Path.home()


def find_branch_root() -> Path | None:
    """
    Find the branch root directory by walking up from PWD.

    Branch root = directory containing *.id.json file or apps/ directory.
    Prefers the CLOSEST (deepest) branch root to PWD, not AIPASS_ROOT.

    Returns:
        Path to branch root, or None if not in a branch
    """
    cwd = Path.cwd()

    # Walk up directory tree (max 10 levels)
    search_path = cwd
    for _ in range(10):
        # Branch indicators
        has_id = list(search_path.glob("*.id.json"))
        has_apps = (search_path / "apps").is_dir()
        has_mail = (search_path / "ai_mail.local").is_dir()

        # Found a branch - but only return it if it's NOT AIPASS_ROOT
        # (AIPASS_ROOT has AIPASS.id.json but is not a "branch" for mail purposes)
        if (has_id or has_apps or has_mail) and search_path != AIPASS_ROOT:
            return search_path

        # Stop at AIPASS root
        if search_path == AIPASS_ROOT:
            break

        # Move up one level
        parent = search_path.parent
        if parent == search_path:  # Reached filesystem root
            break
        search_path = parent

    return None


def count_new_emails(branch_root: Path) -> int:
    """
    Count new (unread) emails in the branch's inbox.

    Supports both new status field (status: "new") and legacy read field (read: false).

    Args:
        branch_root: Path to branch directory

    Returns:
        Count of new/unread emails
    """
    inbox_path = branch_root / "ai_mail.local" / "inbox.json"

    if not inbox_path.exists():
        return 0

    try:
        with open(inbox_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        messages = data.get("messages", [])

        # Count messages with status: "new" OR read: false (backward compat)
        count = 0
        for msg in messages:
            # v2: Check status field first
            if msg.get("status") == "new":
                count += 1
            # v1: Fall back to read field
            elif msg.get("status") is None and not msg.get("read", False):
                count += 1

        return count

    except (json.JSONDecodeError, OSError):
        # Silent fail - don't break the prompt
        return 0


def main():
    """
    Main hook execution.

    Detects branch, checks for new emails, prints notification if any exist.
    Hook output is injected into Claude's context before each prompt.
    """
    branch_root = find_branch_root()

    if not branch_root:
        # Not in a branch - no notification needed
        return

    new_count = count_new_emails(branch_root)

    if new_count > 0:
        # Print notification (will be injected into prompt context)
        plural = "s" if new_count != 1 else ""
        print(f"\n📬 You have {new_count} new email{plural} - check your inbox")


if __name__ == "__main__":
    main()
