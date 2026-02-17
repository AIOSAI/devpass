#!/usr/bin/env python3

# ===================AIPASS====================
# META DATA HEADER
# Name: assistant_wakeup.py - ASSISTANT Wake-Up Cron Trigger
# Date: 2026-02-15
# Version: 1.0.0
# Category: assistant/apps
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-15): Initial implementation - cron-triggered wake-up checker
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
#   - No Rich console (headless cron execution)
#   - Stdout logging (cron redirects to logs/assistant_wakeup.log)
#   - stdlib only + aipass_core imports
# =============================================

"""
Cron trigger script for the ASSISTANT wake-up system.

Called every 30 minutes (offset from scheduler) by cron:
  15,45 * * * * cd /home/aipass/aipass_os/dev_central/assistant && \
    /usr/bin/python3 apps/assistant_wakeup.py >> logs/assistant_wakeup.log 2>&1

Flow:
  1. Acquire single-instance lock
  2. Send Telegram "waking up" notification via assistant bot
  3. Check assistant's email inbox (new/opened counts)
  4. Build summary report with sender/subject listings
  5. Send report notification via assistant bot
"""

# =============================================
# PATH SETUP
# =============================================

import sys
from pathlib import Path

ASSISTANT_ROOT = Path(__file__).parent.parent  # /home/aipass/aipass_os/dev_central/assistant
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(ASSISTANT_ROOT))
sys.path.insert(0, str(AIPASS_ROOT))

# =============================================
# IMPORTS
# =============================================

import json
import fcntl
import time
from datetime import datetime

from apps.handlers.schedule.assistant_notifier import (
    notify_wakeup,
    notify_report,
    notify_error,
)

# =============================================
# CONSTANTS
# =============================================

LOCK_FILE = ASSISTANT_ROOT / "assistant_json" / "wakeup.lock"
CHAT_LOCK_FILE = ASSISTANT_ROOT / "assistant_json" / "chat.lock"
INBOX_PATH = ASSISTANT_ROOT / "ai_mail.local" / "inbox.json"

# =============================================
# LOGGING
# =============================================

def log(message: str) -> None:
    """Print timestamped log line to stdout (captured by cron redirect)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


# =============================================
# CHAT LOCK CHECK
# =============================================

def is_chat_active() -> bool:
    """
    Check if assistant is in an active Telegram chat session.

    The chat listener (assistant_chat.py) creates a lock file while running.
    If the lock exists and is fresh (<60 minutes), skip the wake-up cycle
    to avoid interfering with the live conversation.

    Returns:
        True if chat session is active, False otherwise
    """
    if not CHAT_LOCK_FILE.exists():
        return False
    try:
        age = time.time() - CHAT_LOCK_FILE.stat().st_mtime
        if age > 3600:  # 60 minutes - treat as stale
            return False
        return True
    except OSError:
        return False


# =============================================
# EMAIL CHECK
# =============================================

def check_inbox() -> dict:
    """
    Check assistant's email inbox for new and opened emails.

    Reads inbox.json directly (stdlib only, no module imports that
    require Rich/console).

    Returns:
        Dict with keys: new_count, opened_count, emails (list of brief dicts)
    """
    result = {
        "new_count": 0,
        "opened_count": 0,
        "emails": [],
    }

    if not INBOX_PATH.exists():
        log("Inbox file not found, skipping email check")
        return result

    try:
        with open(INBOX_PATH, "r", encoding="utf-8") as f:
            inbox_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log(f"WARNING: Failed to read inbox: {e}")
        return result

    messages = inbox_data.get("messages", [])

    for msg in messages:
        status = msg.get("status", "")
        if status == "new":
            result["new_count"] += 1
            result["emails"].append({
                "from": msg.get("from", "unknown"),
                "subject": msg.get("subject", "(no subject)"),
                "status": "new",
            })
        elif status == "opened":
            result["opened_count"] += 1
            result["emails"].append({
                "from": msg.get("from", "unknown"),
                "subject": msg.get("subject", "(no subject)"),
                "status": "opened",
            })

    return result


# =============================================
# REPORT BUILDER
# =============================================

def build_report(inbox: dict) -> str:
    """
    Build a summary report from inbox check results.

    Args:
        inbox: Dict from check_inbox()

    Returns:
        Formatted report string
    """
    new_count = inbox["new_count"]
    opened_count = inbox["opened_count"]
    total_unread = new_count + opened_count
    emails = inbox["emails"]

    lines = []

    if total_unread == 0:
        lines.append("No new emails")
    else:
        lines.append(f"New: {new_count} | Opened: {opened_count}")

        # List up to 10 most recent unread emails (brief, 1 line each)
        shown = emails[:10]
        for email in shown:
            marker = "[NEW]" if email["status"] == "new" else "[OPENED]"
            subject = email["subject"][:50]
            lines.append(f"  {marker} {email['from']}: {subject}")

        if len(emails) > 10:
            lines.append(f"  ... and {len(emails) - 10} more")

    return "\n".join(lines)


# =============================================
# MAIN
# =============================================

def main() -> int:
    """
    Main cron entry point.

    Returns:
        0 on success, 1 on error
    """
    log("=" * 60)
    log("Assistant wake-up triggered")

    # Check if chat session is active (skip wake-up to avoid interference)
    if is_chat_active():
        log("Chat session active, skipping wake-up cycle")
        return 0

    # Acquire single-instance lock (non-blocking, stdlib fcntl)
    lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("Another instance already running, skipping.")
        lock_fd.close()
        return 0

    try:
        return _run_locked()
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


def _run_locked() -> int:
    """Execute the wake-up job while holding the lock."""
    exit_code = 0

    # Step 1: Send "waking up" notification
    try:
        notify_wakeup()
        log("Telegram: wakeup notification sent")
    except Exception as e:
        log(f"WARNING: Telegram wakeup notification failed: {e}")
        # Continue anyway -- notification failure should not block inbox check

    # Step 2: Check inbox
    try:
        inbox = check_inbox()
        log(f"Inbox: {inbox['new_count']} new, {inbox['opened_count']} opened")
    except Exception as e:
        log(f"CRITICAL: Unhandled error in check_inbox: {e}")
        try:
            notify_error(f"Inbox check failed: {e}")
        except Exception:
            pass
        return 1

    # Step 3: Build report
    report = build_report(inbox)
    log(f"Report: {report.splitlines()[0]}")

    # Step 4: Send report notification
    try:
        notify_report(report)
        log("Telegram: report notification sent")
    except Exception as e:
        log(f"WARNING: Telegram report notification failed: {e}")
        exit_code = 1

    log("Assistant wake-up finished")
    log("=" * 60)
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # Last-resort catch -- never crash silently
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] FATAL: Unhandled exception: {e}", flush=True)
        try:
            notify_error(f"FATAL: {e}")
        except Exception:
            pass
        sys.exit(1)
