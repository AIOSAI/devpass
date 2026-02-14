#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: error_detected.py - Error Detected Event Handler
# Date: 2026-02-02
# Version: 1.3.0
# Category: trigger/handlers/events
#
# CHANGELOG (Max 5 entries):
#   - v1.3.0 (2026-02-12): Medic Phase 2 - per-branch mute/unmute check
#   - v1.2.0 (2026-02-12): Medic toggle - check medic_enabled before dispatching
#   - v1.1.1 (2026-02-10): Add Seed standards reminder to error dispatch template
#   - v1.1.0 (2026-02-10): FPLAN-0310 Phase 2 - Rate limiting, structured context, reply_to fix
#   - v1.0.1 (2026-02-06): Validate target branch exists before delivery (fixes @telegram spam)
#   - v1.0.0 (2026-02-02): Created - FPLAN-0284 Phase 4 (moved from ai_mail)
#
# CODE STANDARDS:
#   - Follows AIPass Seed standards
#   - NO console.print() - handlers return data to modules
#   - NO logger calls in handler (causes recursion with trigger)
#   - Silent failure pattern - catch all exceptions
#   - Responds to error_detected events from Trigger's log_watcher
# =============================================

"""
Error Detected Event Consumer

Handles error_detected events fired by Trigger's log_watcher.
Delivers notifications to affected branches via AI_MAIL.

Event data from log_watcher.py:
    - branch: Target branch name (e.g., 'FLOW')
    - module: Module that logged the error
    - message: Error message text
    - log_path: Path to log file
    - error_hash: 8-char hash for deduplication
    - timestamp: When error occurred

Architecture:
    1. Trigger's log_watcher detects ERROR in branch logs
    2. log_watcher fires error_detected event
    3. This handler receives event, calls deliver_email_to_branch()
    4. Email delivered to affected branch inbox (auto_execute=True)
    5. Branch agent spawns and investigates
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

AIPASS_ROOT = Path.home() / "aipass_core"
AIPASS_HOME = Path.home()
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(AIPASS_HOME))

BRANCH_REGISTRY_FILE = AIPASS_HOME / "BRANCH_REGISTRY.json"
TRIGGER_CONFIG_FILE = AIPASS_ROOT / "trigger" / "trigger_json" / "trigger_config.json"

# Email send callback (set by module layer, avoids handler importing from modules)
_send_email: Optional[Callable[..., bool]] = None

# Rate limiting: max 3 dispatches per branch per 10 minutes
_dispatch_timestamps: Dict[str, List[float]] = {}
MAX_DISPATCHES_PER_WINDOW = 3
RATE_LIMIT_WINDOW_SECONDS = 600  # 10 minutes


def _is_medic_enabled() -> bool:
    """
    Check if medic (auto-healing dispatch) is enabled.

    Reads medic_enabled from trigger_config.json.
    Defaults to True if config is missing or unreadable.

    Returns:
        True if medic dispatch is enabled
    """
    try:
        if TRIGGER_CONFIG_FILE.exists():
            data = json.loads(TRIGGER_CONFIG_FILE.read_text(encoding='utf-8'))
            return bool(data.get('config', {}).get('medic_enabled', True))
    except Exception:
        return True  # Default to enabled on read failure
    return True


def _is_branch_muted(branch_name: str) -> bool:
    """
    Check if a specific branch is muted for medic dispatch.

    Reads muted_branches list from trigger_config.json.
    Muted branches have errors detected but NOT dispatched.

    Args:
        branch_name: Branch name (case-insensitive)

    Returns:
        True if branch is in the muted list
    """
    try:
        if TRIGGER_CONFIG_FILE.exists():
            data = json.loads(TRIGGER_CONFIG_FILE.read_text(encoding='utf-8'))
            muted = data.get('config', {}).get('muted_branches', [])
            return branch_name.lower() in [b.lower() for b in muted]
    except Exception:
        return False
    return False


def set_send_email_callback(callback: Callable[..., bool]) -> None:
    """
    Set the callback function for sending emails.

    Must be called by the module/registry layer before events fire.
    This avoids handler importing from modules (maintains independence).

    Args:
        callback: Function matching send_email_direct signature
    """
    global _send_email
    _send_email = callback


def _get_registered_emails() -> set:
    """
    Read registered branch emails from BRANCH_REGISTRY.json.

    Returns:
        Set of registered email addresses (e.g., {'@flow', '@drone'})
    """
    try:
        if BRANCH_REGISTRY_FILE.exists():
            data = json.loads(BRANCH_REGISTRY_FILE.read_text(encoding='utf-8'))
            return {b["email"] for b in data.get("branches", [])}
    except Exception:
        return set()
    return set()


def _is_rate_limited(branch_email: str) -> bool:
    """
    Check if a branch has exceeded the dispatch rate limit.

    Args:
        branch_email: Target branch email (e.g., '@flow')

    Returns:
        True if branch has hit the limit (3 dispatches in 10 minutes)
    """
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS

    if branch_email not in _dispatch_timestamps:
        _dispatch_timestamps[branch_email] = []

    # Prune old timestamps
    _dispatch_timestamps[branch_email] = [
        ts for ts in _dispatch_timestamps[branch_email] if ts > cutoff
    ]

    return len(_dispatch_timestamps[branch_email]) >= MAX_DISPATCHES_PER_WINDOW


def _record_dispatch(branch_email: str) -> None:
    """
    Record a dispatch timestamp for rate limiting.

    Args:
        branch_email: Target branch email (e.g., '@flow')
    """
    if branch_email not in _dispatch_timestamps:
        _dispatch_timestamps[branch_email] = []
    _dispatch_timestamps[branch_email].append(time.time())


def _read_log_context(log_path: str, error_message: str, context_lines: int = 2) -> str:
    """
    Read context lines around an error in the log file.

    Args:
        log_path: Path to the log file
        error_message: Error message to find in the log
        context_lines: Number of lines before and after to include

    Returns:
        Formatted context string, or empty string if unavailable
    """
    try:
        path = Path(log_path)
        if not path.exists():
            return ""
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
        # Find last occurrence of the error message
        target_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if error_message in lines[i]:
                target_idx = i
                break
        if target_idx < 0:
            return ""
        start = max(0, target_idx - context_lines)
        end = min(len(lines), target_idx + context_lines + 1)
        context = lines[start:end]
        return "\n".join(context)
    except Exception:
        return ""


def _build_notification_message(
    error_hash: str,
    module: str,
    message: str,
    timestamp: str,
    log_path: str,
    occurrences: int = 1,
    first_seen: str = "",
    last_seen: str = "",
    log_context: str = ""
) -> str:
    """
    Build error notification message with investigation instructions.

    Args:
        error_hash: Unique error identifier (8-char)
        module: Module that logged the error
        message: Error message text
        timestamp: When error occurred
        log_path: Path to source log file
        occurrences: Number of times this error was seen
        first_seen: Timestamp of first occurrence
        last_seen: Timestamp of most recent occurrence
        log_context: Lines surrounding the error from the log file

    Returns:
        Formatted message string with investigation instructions
    """
    ctx_block = ""
    if log_context:
        ctx_block = f"""
Log context (surrounding lines):
{log_context}
"""

    return f"""Error detected - investigate and respond.

Error ID: {error_hash}
Module: {module}
Timestamp: {timestamp}
Log file: {log_path}
Occurrences: {occurrences}
First seen: {first_seen or timestamp}
Last seen: {last_seen or timestamp}

Error message:
{message}
{ctx_block}
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

SEED STANDARDS REMINDER:
- Any code changes made during this investigation MUST follow Seed standards
- After fixing, run: drone @seed checklist <modified_file>
- Fixes scoring below 80% on Seed audit should NOT be shipped - clean up first

REPORT TO @dev_central:
  ai_mail send @dev_central "ERROR {error_hash} - [STATUS]" "Findings..."

  Include: Error ID, severity (low/medium/high/critical), what you found, action taken or recommended.
"""


def handle_error_detected(
    branch: str | None = None,
    module: str | None = None,
    message: str | None = None,
    log_path: str | None = None,
    error_hash: str | None = None,
    timestamp: str | None = None,
    **kwargs: Any
) -> None:
    """
    Handle error_detected event - deliver notification to affected branch.

    Called by Trigger when log_watcher detects an ERROR in branch logs.
    Sends email to affected branch with auto_execute=True so an
    investigation agent spawns automatically.

    Args:
        branch: Target branch name (e.g., 'FLOW') - REQUIRED
        module: Module that logged the error - REQUIRED
        message: Error message text - REQUIRED
        log_path: Path to source log file
        error_hash: 8-char unique error identifier - REQUIRED
        timestamp: When error occurred (defaults to now)
        **kwargs: Additional event data (ignored)

    Returns:
        None - handlers must not return values

    Note:
        Handler follows silent failure pattern - all exceptions caught.
        NO logger imports (causes infinite recursion with trigger events).
        NO console.print() (handlers must be silent).
    """
    try:
        # Validate required fields
        if not branch or not module or not message or not error_hash:
            return

        # Medic toggle - if disabled, log but do NOT dispatch
        if not _is_medic_enabled():
            try:
                medic_log = AIPASS_ROOT / "trigger" / "logs" / "medic_suppressed.log"
                medic_log.parent.mkdir(parents=True, exist_ok=True)
                with open(medic_log, 'a') as f:
                    f.write(
                        f"{datetime.now().isoformat()} | "
                        f"Medic OFF - suppressed dispatch for {branch}: "
                        f"{module} - {message[:100]}\n"
                    )
            except Exception:
                return  # Can't log suppression, but still skip dispatch
            return

        # Per-branch mute check - muted branches have errors logged but NOT dispatched
        if _is_branch_muted(branch):
            try:
                suppressed_log = AIPASS_ROOT / "trigger" / "logs" / "medic_suppressed.log"
                suppressed_log.parent.mkdir(parents=True, exist_ok=True)
                with open(suppressed_log, 'a') as f:
                    f.write(
                        f"{datetime.now().isoformat()} | "
                        f"Branch muted - suppressed dispatch for {branch}: "
                        f"{module} - {message[:100]}\n"
                    )
            except Exception:
                return  # Can't log suppression, but still skip dispatch
            return

        # Callback must be set by module layer before events fire
        if _send_email is None:
            return

        # Convert branch name to email format (FLOW -> @flow)
        recipient = f"@{branch.lower()}"

        # HARD RULE: DEV_CENTRAL is NEVER auto-triggered
        if recipient == '@dev_central':
            return

        # Validate target branch exists in registry before attempting delivery
        registered_emails = _get_registered_emails()
        if recipient not in registered_emails:
            # Unknown branch - log and skip (do NOT route to dev_central)
            try:
                suppressed_log = AIPASS_ROOT / "trigger" / "logs" / "medic_suppressed.log"
                suppressed_log.parent.mkdir(parents=True, exist_ok=True)
                with open(suppressed_log, 'a') as f:
                    f.write(
                        f"{datetime.now().isoformat()} | "
                        f"Unknown branch skipped: {recipient} - "
                        f"{module}: {message[:100]}\n"
                    )
            except Exception:
                return  # Can't log skip, still don't dispatch
            return

        # Check rate limit before dispatching
        recent_count = len([
            ts for ts in _dispatch_timestamps.get(recipient, [])
            if ts > time.time() - RATE_LIMIT_WINDOW_SECONDS
        ])
        if _is_rate_limited(recipient):
            # Log rate limit hit (safe - writing to file, not using logger)
            try:
                rate_limit_log = AIPASS_ROOT / "trigger" / "logs" / "rate_limited.log"
                rate_limit_log.parent.mkdir(parents=True, exist_ok=True)
                with open(rate_limit_log, 'a') as f:
                    f.write(
                        f"{datetime.now().isoformat()} | "
                        f"Rate limited: {recipient} has {recent_count} "
                        f"recent dispatches, skipping\n"
                    )
            except Exception:
                return  # Can't log rate limit, but still skip dispatch
            return

        # Default timestamp to now if not provided
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Default log_path if not provided
        effective_log_path = log_path if log_path else "unknown"

        # Read log context (2 lines before and after)
        error_log_context = _read_log_context(effective_log_path, message)

        # Build subject line
        email_subject = f"[ERROR] {module} - detected in logs"

        # Build notification message with structured context
        notification_message = _build_notification_message(
            error_hash=error_hash,
            module=module,
            message=message,
            timestamp=timestamp,
            log_path=effective_log_path,
            occurrences=1,
            first_seen=timestamp,
            last_seen=timestamp,
            log_context=error_log_context
        )

        # Send via callback (set by module layer, trigger isn't a branch so PWD detection fails)
        _send_email(
            to_branch=recipient,
            subject=email_subject,
            message=notification_message,
            auto_execute=True,
            reply_to='@trigger',
            from_branch='@trigger'
        )

        # Record dispatch for rate limiting
        _record_dispatch(recipient)

    except Exception:
        return  # Silent failure - handler must not raise
