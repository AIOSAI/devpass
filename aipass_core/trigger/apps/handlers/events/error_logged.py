#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: error_logged.py - Error Logged Event Handler
# Date: 2026-01-31
# Version: 1.0.0
# Category: trigger/handlers/events
#
# CHANGELOG (Max 5 entries):
#   - v1.0.2 (2026-02-06): Validate target branch exists before delivery (fixes @telegram spam)
#   - v1.0.1 (2026-02-03): Fixed cross-branch import - uses module API instead of handler
#   - v1.0.0 (2026-01-31): Created - Phase 2 migration (FPLAN-0279)
#
# CODE STANDARDS:
#   - Follows AIPass Seed standards
#   - NO logger imports (causes infinite recursion in event handlers)
#   - NO print statements (handlers must be silent)
#   - Silent failure - catch all exceptions, pass
# =============================================

"""
Error Logged Event Handler

Handles error_logged events fired by Trigger log watcher.
Sends AI_Mail notification to affected branch for investigation.

Event data expected:
    - branch: Branch where error occurred (e.g., FLOW)
    - message: Error message text
    - error_hash: Unique hash for deduplication
    - timestamp: When the error occurred
    - log_file: Path to log file
    - module_name: Module that logged the error
    - level: Log level (always 'error' for this handler)
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

AIPASS_ROOT = Path.home() / "aipass_core"
AIPASS_HOME = Path.home()
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(AIPASS_HOME))


def _build_notification_message(
    error_hash: str,
    module_name: str,
    message: str,
    timestamp: str,
    log_file: str
) -> str:
    """
    Build error notification message with investigation instructions.

    Args:
        error_hash: Unique error identifier
        module_name: Module that logged the error
        message: Error message text
        timestamp: When error occurred
        log_file: Path to source log file

    Returns:
        Formatted message string
    """
    return f"""Error detected - investigate and respond.

Error ID: {error_hash}
Module: {module_name}
Timestamp: {timestamp}
Log file: {log_file}

Error message:
{message}

---
INVESTIGATION STEPS:
1. Check the log file for context around this error
2. Identify root cause

DECISION TREE:
- SIMPLE FIX (typo, missing import, config issue):
  -> Fix it yourself, then report what you did to @dev_central
- COMPLEX/UNCLEAR (needs research, affects multiple files):
  -> Report findings only to @dev_central, recommend action, don't fix
- CRITICAL (data loss risk, security, system stability):
  -> STOP immediately, escalate to @dev_central with full context

REPORT TO @dev_central:
  ai_mail send @dev_central "ERROR {error_hash[:8]} - [STATUS]" "Findings..."
"""


def handle_error_logged(
    branch: str | None = None,
    message: str | None = None,
    error_hash: str | None = None,
    timestamp: str | None = None,
    log_file: str | None = None,
    module_name: str | None = None,
    level: str | None = None,  # noqa: ARG001 - kept for event signature compatibility
    **kwargs: Any  # noqa: ARG001 - absorbs additional event data
) -> None:
    """
    Handle error_logged event - send AI_Mail notification to affected branch.

    Sends an email notification to the branch where an error was logged,
    prompting investigation. Uses the AI_Mail module API for delivery.

    Args:
        branch: Branch where error occurred - REQUIRED
        message: Error message text - REQUIRED
        error_hash: Unique error identifier - REQUIRED
        timestamp: When error occurred (defaults to now)
        log_file: Path to source log file
        module_name: Module that logged the error
        level: Log level (for reference, unused)
        **kwargs: Additional event data (ignored)

    Returns:
        None - handlers must not return values

    Note:
        Handler follows silent failure pattern - all exceptions caught.
        NO logger imports (causes infinite recursion with trigger events).
    """
    try:
        if not branch or not message or not error_hash:
            return

        try:
            from ai_mail.apps.modules.email import send_email_direct
            from ai_mail.apps.handlers.email.delivery import get_all_branches
        except ImportError:
            return

        target_branch = f"@{branch.lower()}"

        # Validate target branch exists in registry before attempting delivery
        registered_emails = {b["email"] for b in get_all_branches()}
        if target_branch not in registered_emails:
            # Unknown branch - route to @dev_central instead of spamming errors
            target_branch = '@dev_central'

        ts = timestamp if timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lf = log_file if log_file else "unknown"
        mn = module_name if module_name else "unknown"

        email_subject = f"[ERROR] {mn} - investigation needed"

        notification_message = _build_notification_message(
            error_hash=error_hash,
            module_name=mn,
            message=message,
            timestamp=ts,
            log_file=lf
        )

        send_email_direct(
            to_branch=target_branch,
            subject=email_subject,
            message=notification_message,
            auto_execute=True,
            reply_to='@dev_central',
            from_branch='@trigger'
        )

    except Exception:
        pass
