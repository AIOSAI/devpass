#!/usr/bin/env python3

# ===================AIPASS====================
# META DATA HEADER
# Name: scheduler_cron.py - ASSISTANT Scheduler Cron Trigger
# Date: 2026-02-15
# Version: 1.0.0
# Category: assistant/apps
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-15): Initial implementation - cron-triggered scheduler
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
#   - No Rich console (headless cron execution)
#   - Stdout logging (cron redirects to logs/scheduler_cron.log)
# =============================================

"""
Cron trigger script for the ASSISTANT scheduled task system.

Called every 30 minutes by cron:
  */30 * * * * cd /home/aipass/aipass_os/dev_central/assistant && \
    /usr/bin/python3 apps/scheduler_cron.py >> logs/scheduler_cron.log 2>&1

Flow:
  1. Acquire single-instance lock
  2. Send Telegram "triggered" notification
  3. Recover stale dispatches
  4. Process all due tasks (send emails, mark complete)
  5. Send Telegram "complete" or "error" notification with summary
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

import time
from datetime import datetime

import fcntl

from apps.handlers.schedule.telegram_notifier import (
    notify_triggered,
    notify_complete,
    notify_error,
)
from apps.handlers.schedule.task_registry import (
    get_due_tasks,
    mark_dispatching,
    mark_completed,
    mark_pending,
    recover_stale_dispatches,
)
from ai_mail.apps.modules.email import send_email_direct

# =============================================
# CONSTANTS
# =============================================

EVENT_NAME = "cron-run"
LOCK_FILE = ASSISTANT_ROOT / "assistant_json" / "schedule.lock"
STALE_DISPATCH_MAX_AGE = 5  # minutes

# =============================================
# LOGGING
# =============================================

def log(message: str) -> None:
    """Print timestamped log line to stdout (captured by cron redirect)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


# =============================================
# TASK PROCESSING
# =============================================

def process_due_tasks() -> dict:
    """
    Process all due scheduled tasks.

    Recovers stale dispatches, then iterates due tasks:
    mark dispatching -> send email -> mark completed or reset to pending.

    Returns:
        Dict with keys: due, success, failed, errors (list of error strings)
    """
    results = {
        "due": 0,
        "success": 0,
        "failed": 0,
        "recovered": 0,
        "errors": [],
    }

    # Recover any stale dispatches (stuck > 5 minutes)
    try:
        recovered = recover_stale_dispatches(max_age_minutes=STALE_DISPATCH_MAX_AGE)
        results["recovered"] = recovered
        if recovered:
            log(f"Recovered {recovered} stale dispatch(es)")
    except Exception as e:
        log(f"WARNING: Failed to recover stale dispatches: {e}")
        results["errors"].append(f"Stale recovery: {e}")

    # Get due tasks
    try:
        due_tasks = get_due_tasks()
    except Exception as e:
        log(f"ERROR: Failed to load due tasks: {e}")
        results["errors"].append(f"Load tasks: {e}")
        return results

    results["due"] = len(due_tasks)

    if not due_tasks:
        log("No tasks due at this time.")
        return results

    log(f"Found {len(due_tasks)} due task(s)")

    # Process each due task
    for task in due_tasks:
        task_id = task.get("id", "")
        recipient = task.get("recipient", "")
        task_desc = task.get("task", "")
        message = task.get("message", "")

        log(f"Processing: {task_id[:8]} -> {recipient}: {task_desc[:50]}")

        # Mark as dispatching (prevents re-dispatch)
        try:
            mark_dispatching(task_id)
        except Exception as e:
            log(f"WARNING: Failed to mark dispatching {task_id[:8]}: {e}")
            results["errors"].append(f"Mark dispatching {task_id[:8]}: {e}")
            results["failed"] += 1
            continue

        # Build email body
        email_body = f"{task_desc}"
        if message:
            email_body += f"\n\nDetails:\n{message}"

        # Send the email
        try:
            email_sent = send_email_direct(
                to_branch=recipient,
                subject=f"[SCHEDULED] {task_desc}",
                message=email_body,
                from_branch='@assistant',
                auto_execute=True,
                reply_to='@dev_central',
            )

            if email_sent:
                mark_completed(task_id)
                log(f"OK: Sent to {recipient}: {task_desc[:40]}")
                results["success"] += 1
            else:
                mark_pending(task_id)
                log(f"FAIL: Email returned False for {recipient}: {task_desc[:40]}")
                results["failed"] += 1
                results["errors"].append(f"Email failed: {task_id[:8]} -> {recipient}")

        except Exception as e:
            # Reset to pending for retry on next run
            try:
                mark_pending(task_id)
            except Exception:
                pass  # Best effort reset
            log(f"ERROR: Exception sending to {recipient}: {e}")
            results["failed"] += 1
            results["errors"].append(f"Email error {task_id[:8]}: {e}")

        # Small delay between dispatches (prevents thundering herd)
        time.sleep(1.0)

    return results


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
    log("Scheduler cron triggered")

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
    """Execute the cron job while holding the lock."""
    exit_code = 0

    # Step 1: Send "triggered" notification
    try:
        notify_triggered(EVENT_NAME)
        log("Telegram: triggered notification sent")
    except Exception as e:
        log(f"WARNING: Telegram triggered notification failed: {e}")
        # Continue anyway -- notification failure should not block task processing

    # Step 2: Process due tasks
    try:
        results = process_due_tasks()
    except Exception as e:
        log(f"CRITICAL: Unhandled error in process_due_tasks: {e}")
        try:
            notify_error(EVENT_NAME, f"Unhandled error: {e}")
        except Exception:
            pass
        return 1

    # Step 3: Build summary
    summary_parts = []
    if results["recovered"]:
        summary_parts.append(f"Recovered: {results['recovered']} stale")
    summary_parts.append(f"Due: {results['due']}")
    summary_parts.append(f"Sent: {results['success']}")
    if results["failed"]:
        summary_parts.append(f"Failed: {results['failed']}")
    summary = " | ".join(summary_parts)

    log(f"Results: {summary}")

    # Step 4: Send completion or error notification
    try:
        if results["failed"] > 0 or results["errors"]:
            error_detail = summary
            if results["errors"]:
                error_detail += f"\nErrors:\n" + "\n".join(
                    f"  - {e}" for e in results["errors"][:5]
                )
            notify_error(EVENT_NAME, error_detail)
            log("Telegram: error notification sent")
            exit_code = 1
        else:
            notify_complete(EVENT_NAME, summary)
            log("Telegram: complete notification sent")
    except Exception as e:
        log(f"WARNING: Telegram result notification failed: {e}")

    log("Scheduler cron finished")
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
            notify_error(EVENT_NAME, f"FATAL: {e}")
        except Exception:
            pass
        sys.exit(1)
