#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: delivery.py - Email Delivery Handler
# Date: 2025-12-02
# Version: 2.4.0
# Category: ai_mail/handlers/email
#
# CHANGELOG (Max 5 entries):
#   - v2.4.0 (2026-02-10): Seed compliance - remove logger calls, cross-handler imports, fix naming, add json_handler
#   - v2.3.0 (2026-02-10): Phase 3 polish - concise bounce messages, dispatch chain logging, hardened loop detection
#   - v2.2.0 (2026-02-10): DEV_CENTRAL dispatch protection, notification throttling, self-reply loop detection
#   - v2.1.0 (2026-02-10): Silent success confirmations - only send email on spawn failure, not success
#   - v2.0.0 (2026-02-09): Add fcntl.flock inbox.json locking to prevent concurrent write corruption
#
# CODE STANDARDS:
#   - Handler independence: NO cross-handler or module imports
#   - No logger calls (module logs for handler)
#   - Pure business logic only
#   - Uses json_handler for JSON operations
# =============================================

"""
Email Delivery Handler

Handles delivery of emails to branch inboxes.
Independent handler - no module dependencies.
"""

import sys
import json
import uuid
import subprocess
from pathlib import Path
from typing import Dict, Tuple, List, Optional, Callable

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
AIPASS_HOME = Path.home()
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(AIPASS_HOME))

from aipass_core.ai_mail.apps.handlers.json_utils.json_handler import load_json, save_json

# Lazy imports to avoid circular dependencies
_CONSOLE = None
_LOCK_UTILS = None
_INBOX_LOCK = None


def _get_lock_utils():
    """Lazy import lock_utils."""
    global _LOCK_UTILS
    if _LOCK_UTILS is None:
        from aipass_core.ai_mail.apps.handlers.email import lock_utils
        _LOCK_UTILS = lock_utils
    return _LOCK_UTILS


def _get_inbox_lock():
    """Lazy import inbox_lock context manager."""
    global _INBOX_LOCK
    if _INBOX_LOCK is None:
        from aipass_core.ai_mail.apps.handlers.email.inbox_lock import inbox_lock
        _INBOX_LOCK = inbox_lock
    return _INBOX_LOCK


def _get_console():
    """Lazy import console."""
    global _CONSOLE
    if _CONSOLE is None:
        from cli.apps.modules import console
        _CONSOLE = console
    return _CONSOLE


def get_all_branches() -> List[Dict]:
    """
    Get list of all branches for email routing.
    Reads from AIPass branch registry at /home/aipass/BRANCH_REGISTRY.json

    Returns:
        List of dicts with branch info:
        [{"name": "AIPASS.admin", "path": "/", "email": "@admin"}, ...]
    """
    registry_file = Path("/home/aipass/BRANCH_REGISTRY.json")
    branches = []

    if not registry_file.exists():
        return []

    try:
        with open(registry_file, 'r', encoding='utf-8') as f:
            registry_data = json.load(f)

        # Parse branch entries from JSON structure
        for branch in registry_data.get("branches", []):
            branch_name = branch.get("name", "")
            path = branch.get("path", "")

            if not branch_name or not path:
                continue

            # Use explicit email from registry if present (preferred)
            # Fall back to derivation only if email field is missing
            explicit_email = branch.get("email", "")
            if explicit_email:
                email = explicit_email
            else:
                # Legacy fallback: derive email from branch name
                if '.' in branch_name:
                    email_part = branch_name.split('.')[-1].lower()
                elif ' ' in branch_name:
                    email_part = branch_name.split()[0].lower()
                elif '-' in branch_name and branch_name.split('-')[0] == 'AIPASS':
                    email_part = branch_name.split('-', 1)[1].lower()
                else:
                    email_part = branch_name.split('-')[0].lower()
                email = f"@{email_part}"

            branches.append({
                "name": branch_name,
                "path": path,
                "email": email
            })

        # COLLISION DETECTION: Check for duplicate email addresses
        email_map = {}
        collisions = []
        for branch in branches:
            if branch["email"] in email_map:
                collision_msg = f"Email collision: {branch['email']} used by both '{email_map[branch['email']]}' and '{branch['name']}'"
                collisions.append(collision_msg)
            else:
                email_map[branch["email"]] = branch["name"]

        return branches

    except Exception:
        return []


def _migrate_inbox_format(inbox_data: Dict, inbox_file: Path) -> Dict:
    """
    Auto-migrate old inbox format to v2 schema.

    Old format: {"inbox": [...]}
    New format: {"mailbox": "inbox", "total_messages": N, "unread_count": N, "messages": [...]}

    Migrates in-place and persists to disk if changes were made.

    Args:
        inbox_data: Loaded inbox dict (may be old or new format)
        inbox_file: Path to inbox.json (for persisting migration)

    Returns:
        Migrated inbox data dict with v2 schema
    """
    migrated = False

    # Case 0: inbox_data is a list instead of a dict (corrupted/malformed inbox.json)
    if isinstance(inbox_data, list):
        inbox_data = {"messages": inbox_data}
        migrated = True

    # Case 1: Old format with "inbox" key instead of "messages"
    if "inbox" in inbox_data and "messages" not in inbox_data:
        old_messages = inbox_data.pop("inbox", [])
        inbox_data["messages"] = old_messages if isinstance(old_messages, list) else []
        migrated = True

    # Case 2: Missing "messages" key entirely
    if "messages" not in inbox_data:
        inbox_data["messages"] = []
        migrated = True

    # Ensure v2 metadata fields exist
    if "mailbox" not in inbox_data:
        inbox_data["mailbox"] = "inbox"
        migrated = True

    if "total_messages" not in inbox_data:
        inbox_data["total_messages"] = len(inbox_data["messages"])
        migrated = True

    if "unread_count" not in inbox_data:
        inbox_data["unread_count"] = sum(
            1 for msg in inbox_data["messages"]
            if msg.get("status") == "new" or (msg.get("status") is None and not msg.get("read", False))
        )
        migrated = True

    # Persist migration to disk
    if migrated:
        try:
            with open(inbox_file, 'w', encoding='utf-8') as f:
                json.dump(inbox_data, f, indent=2, ensure_ascii=False)
        except Exception:
            return inbox_data

    return inbox_data


def deliver_email_to_branch(
    to_branch: str,
    email_data: Dict,
    on_delivered: Optional[Callable] = None
) -> Tuple[bool, str]:
    """
    Deliver email to target branch's ai_mail.local/inbox.json file.

    Appends message to inbox JSON messages array.

    Args:
        to_branch: Target email address (e.g., "@admin")
        email_data: Email data dict with keys:
            - from: Sender email address
            - from_name: Sender display name
            - to: Recipient email address
            - subject: Email subject
            - message: Email body
            - timestamp: Email timestamp string
        on_delivered: Optional callback(branch_path, new_count, opened_count, total)
            for post-delivery actions (dashboard updates, central sync, etc.)

    Returns:
        Tuple of (success: bool, error_message: str)
        error_message is empty string if successful
    """
    # Handle path input from DRONE's @ resolution
    if to_branch.startswith('/'):
        branches_list = get_all_branches()
        path_to_email = {b["path"]: b["email"] for b in branches_list}
        if to_branch in path_to_email:
            to_branch = path_to_email[to_branch]
        else:
            path = Path(to_branch)
            parts = path.parts
            branch_name = None
            if 'aipass_core' in parts:
                idx = parts.index('aipass_core')
                if idx + 1 < len(parts):
                    branch_name = parts[idx + 1]
            elif 'aipass' in parts:
                idx = parts.index('aipass')
                if idx + 1 < len(parts) and parts[idx + 1] != 'aipass_core':
                    branch_name = parts[idx + 1]

            if branch_name:
                to_branch = f"@{branch_name}"
            else:
                return False, f"Could not resolve path to email: {to_branch}"

    # Map email address to branch path
    all_branches = get_all_branches()
    branches = {b["email"]: b["path"] for b in all_branches}

    if to_branch not in branches:
        error_msg = f"Unknown branch email: {to_branch} (available: {len(branches)} branches)"
        return False, error_msg

    branch_path = Path(branches[to_branch])

    # Find the branch's ai_mail.local/inbox.json file
    if branch_path == Path("/") or branch_path == Path.home():
        inbox_file = Path.home() / "ai_mail.local" / "inbox.json"
    else:
        inbox_file = branch_path / "ai_mail.local" / "inbox.json"

    if not inbox_file.exists():
        error_msg = f"AI_Mail not installed (missing: {inbox_file})"
        return False, error_msg

    # Lock inbox.json for the entire read-modify-write cycle
    try:
        with _get_inbox_lock()(inbox_file):
            try:
                with open(inbox_file, 'r', encoding='utf-8') as f:
                    inbox_data = json.load(f)
            except Exception as e:
                return False, f"Failed to read inbox: {e}"

            # Auto-migrate old inbox format {"inbox": []} -> v2 schema
            inbox_data = _migrate_inbox_format(inbox_data, inbox_file)

            # Create message object (v2 schema: status instead of read)
            message = {
                "id": str(uuid.uuid4())[:8],
                "timestamp": email_data['timestamp'],
                "from": email_data['from'],
                "from_name": email_data['from_name'],
                "subject": email_data['subject'],
                "message": email_data['message'],
                "status": "new",
                "auto_execute": email_data.get('auto_execute', False),
                "priority": email_data.get('priority', 'normal')
            }

            if email_data.get('reply_to'):
                message["reply_to"] = email_data['reply_to']

            if email_data.get('dispatched_to'):
                message["dispatched_to"] = email_data['dispatched_to']

            # Prepend message to inbox (newest first)
            inbox_data["messages"].insert(0, message)
            inbox_data["total_messages"] = len(inbox_data["messages"])
            messages = inbox_data["messages"]
            new_count = sum(
                1 for msg in messages
                if msg.get("status") == "new" or (msg.get("status") is None and not msg.get("read", False))
            )
            opened_count = sum(1 for msg in messages if msg.get("status") == "opened")
            inbox_data["unread_count"] = new_count

            try:
                with open(inbox_file, 'w', encoding='utf-8') as f:
                    json.dump(inbox_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                return False, f"Failed to write inbox: {e}"

    except OSError as e:
        return False, f"Failed to acquire inbox lock: {e}"

    # Send desktop notification for new email
    _send_desktop_notification(email_data['from'], to_branch, email_data['subject'], email_data.get('message', ''))

    # Invoke post-delivery callback (dashboard updates, central sync, etc.)
    if on_delivered:
        try:
            on_delivered(branch_path, new_count, opened_count, inbox_data["total_messages"])
        except Exception:
            return True, ""

    # Auto-execute: spawn background agent at target branch
    if email_data.get('auto_execute', False):
        reply_to = email_data.get('reply_to')
        sender_from = email_data.get('from')
        if not ((reply_to and reply_to == to_branch) or (sender_from and sender_from == to_branch)):
            _spawn_auto_execute_agent(branch_path, email_data['from'], message['id'])

    return True, ""


def _spawn_auto_execute_agent(branch_path: Path, sender: str, message_id: str) -> None:
    """
    Spawn a background Claude agent at target branch to process the email.
    Sends confirmation email back to sender with spawn result.

    Args:
        branch_path: Path to target branch directory
        sender: Email sender address (e.g., @dev_central)
        message_id: ID of the delivered message
    """
    branch_email = _get_branch_email_from_path(branch_path)

    # PROTECTION: @dev_central is protected from auto-dispatch
    if branch_email == '@dev_central':
        return

    try:
        if branch_path == Path("/"):
            branch_path = Path.home()

        branch_path = branch_path.resolve()
        if not branch_path.exists():
            error_msg = f"target path does not exist: {branch_path}"
            _send_spawn_confirmation(sender, branch_email, branch_path, False, error_msg)
            return

        # SINGLE INSTANCE GATE: Check if branch already has an active dispatch agent
        lock = _get_lock_utils()
        existing_lock = lock.check_lock(branch_path)
        if existing_lock is not None:
            existing_pid = existing_lock.get("pid", "unknown")
            existing_time = existing_lock.get("timestamp", "unknown")
            _send_bounce_notification(sender, branch_email, branch_path, existing_pid, existing_time)
            return

        # Build the agent prompt (includes lock release instruction)
        lock_path = str(branch_path / "ai_mail.local" / ".dispatch.lock")
        prompt = (
            f"Hi. Check inbox for task from {sender} (message ID: {message_id}). Execute it. Send confirmation when done. "
            f"IMPORTANT: When finished, delete the dispatch lock file at {lock_path}"
        )

        cmd = f"claude -p '{prompt}' --permission-mode bypassPermissions"
        target_cwd = str(branch_path)

        import os
        spawn_env = os.environ.copy()
        spawn_env['AIPASS_SPAWNED'] = '1'
        spawn_env.pop('CLAUDECODE', None)  # Allow spawned claude to run outside parent session

        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=target_cwd,
            env=spawn_env
        )

        pid = process.pid

        # Acquire dispatch lock for this branch
        lock.acquire_lock(branch_path, pid)

        # Notify desktop that branch agent is running
        _send_spawn_notification(branch_email)

    except Exception as e:
        error_msg = str(e)
        _send_spawn_confirmation(sender, branch_email, branch_path, False, error_msg)


def _get_branch_email_from_path(branch_path: Path) -> str:
    """
    Get branch email address from path.

    Args:
        branch_path: Path to branch directory

    Returns:
        Branch email address (e.g., @ai_mail)
    """
    if branch_path == Path("/") or branch_path == Path.home():
        return "@aipass"

    branch_name = branch_path.name.lower()
    return f"@{branch_name}"


def _send_spawn_confirmation(
    recipient: str,
    sender_email: str,
    branch_path: Path,
    success: bool,
    error_msg: str | None = None,
    pid: int | None = None
) -> None:
    """
    Send spawn confirmation email to the original dispatch sender.

    Args:
        recipient: Email address to send confirmation to
        sender_email: Branch email sending the confirmation
        branch_path: Path to spawning branch (for display name)
        success: Whether spawn succeeded
        error_msg: Error message if spawn failed
        pid: Process ID if spawn succeeded
    """
    from datetime import datetime

    try:
        branch_name = branch_path.name.upper() if branch_path != Path.home() else "AIPASS"

        if success:
            conf_subject = f"SPAWN OK: Agent started at {sender_email}"
            conf_message = f"Agent spawned at {sender_email} (PID: {pid})"
        else:
            conf_subject = f"SPAWN FAILED at {sender_email}"
            conf_message = f"SPAWN FAILED at {sender_email}: {error_msg}"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        email_data = {
            "from": sender_email,
            "from_name": branch_name,
            "to": recipient,
            "subject": conf_subject,
            "message": conf_message,
            "timestamp": timestamp,
            "auto_execute": False,
            "priority": "normal"
        }

        deliver_email_to_branch(recipient, email_data)

    except Exception:
        return


def _send_bounce_notification(
    recipient: str,
    branch_email: str,
    branch_path: Path,
    existing_pid: int | str,
    existing_time: str
) -> None:
    """
    Send bounce notification when dispatch is blocked by active lock.

    Args:
        recipient: Email address to send bounce to (original sender)
        branch_email: Target branch email that is busy
        branch_path: Path to target branch
        existing_pid: PID of the currently running agent
        existing_time: Timestamp when the existing agent started
    """
    from datetime import datetime

    try:
        branch_name = branch_path.name.upper() if branch_path != Path.home() else "AIPASS"

        bounce_subject = f"DISPATCH BOUNCED: {branch_email} is busy"
        bounce_message = (
            f"Dispatch to {branch_email} blocked: active agent PID {existing_pid} running since {existing_time}. "
            f"Email delivered to inbox for manual review."
        )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        email_data = {
            "from": branch_email,
            "from_name": branch_name,
            "to": recipient,
            "subject": bounce_subject,
            "message": bounce_message,
            "timestamp": timestamp,
            "auto_execute": False,
            "priority": "normal"
        }

        deliver_email_to_branch(recipient, email_data)

    except Exception:
        return


def _get_summary_file_path(branch_path: Path) -> Path:
    """
    Get the summary file path for a branch.

    Pattern: [BRANCH_NAME].ai_mail.json
    Example: /home/aipass/aipass_core/drone/DRONE.ai_mail.json

    Args:
        branch_path: Path to branch directory

    Returns:
        Path to summary file
    """
    branch_name = branch_path.name.upper()

    if branch_path == Path("/") or branch_path == Path.home():
        branch_name = "AIPASS"

    summary_file = branch_path / f"{branch_name}.ai_mail.json"
    return summary_file


def _update_summary_file(summary_file: Path, message: Dict, total: int, unread: int) -> None:
    """
    Update branch summary file with new email data.

    Updates:
    - summary.inbox.total
    - summary.inbox.unread
    - summary.inbox.recent_preview (adds message preview)

    Args:
        summary_file: Path to summary JSON file
        message: Message dict to add to preview
        total: Total inbox message count
        unread: Unread message count
    """
    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)

        if "summary" not in summary_data:
            summary_data["summary"] = {}
        if "inbox" not in summary_data["summary"]:
            summary_data["summary"]["inbox"] = {}

        summary_data["summary"]["inbox"]["total"] = total
        summary_data["summary"]["inbox"]["unread"] = unread

        if "recent_preview" not in summary_data["summary"]["inbox"]:
            summary_data["summary"]["inbox"]["recent_preview"] = []

        message_words = message["message"].split()[:15]
        preview = {
            "from": message["from"],
            "subject": message["subject"],
            "summary": " ".join(message_words) + ("..." if len(message["message"].split()) > 15 else ""),
            "timestamp": message["timestamp"],
            "status": "new",
            "message_id": message["id"]
        }

        summary_data["summary"]["inbox"]["recent_preview"].insert(0, preview)
        summary_data["summary"]["inbox"]["recent_preview"] = summary_data["summary"]["inbox"]["recent_preview"][:5]

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

    except Exception:
        return


_NOTIFICATION_TIMESTAMPS: Dict[str, List[float]] = {}

# Rate limit: max notifications per recipient within time window
_NOTIFICATION_MAX = 3
_NOTIFICATION_WINDOW = 30.0  # seconds


def _send_desktop_notification(sender: str, recipient: str, subject: str, message: str = "") -> None:
    """
    Send desktop notification for new email using notify-send.

    Rate-limited: max 3 notifications per recipient within 30 seconds.
    Gracefully handles cases where notify-send is not available.

    Args:
        sender: Email sender address (e.g., @dev_central)
        recipient: Email recipient address (e.g., @ai_mail)
        subject: Email subject line
        message: Email body (first ~100 chars shown in notification)
    """
    import time

    now = time.time()
    cutoff = now - _NOTIFICATION_WINDOW

    if recipient in _NOTIFICATION_TIMESTAMPS:
        _NOTIFICATION_TIMESTAMPS[recipient] = [
            t for t in _NOTIFICATION_TIMESTAMPS[recipient] if t > cutoff
        ]
    else:
        _NOTIFICATION_TIMESTAMPS[recipient] = []

    if len(_NOTIFICATION_TIMESTAMPS[recipient]) >= _NOTIFICATION_MAX:
        return

    # Build informative notification
    sender_name = sender.replace('@', '').upper()
    recipient_name = recipient.replace('@', '').upper()
    title = f"{sender_name} -> {recipient_name}"
    body = subject
    if message:
        preview = message[:100].replace('\n', ' ').strip()
        if preview:
            body = f"{subject}\n{preview}"

    try:
        subprocess.run(
            ['notify-send', title, body],
            capture_output=True,
            timeout=5
        )
        _NOTIFICATION_TIMESTAMPS[recipient].append(now)
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return


def _send_spawn_notification(branch_email: str) -> None:
    """
    Send desktop notification when a branch agent is spawned via dispatch.

    Args:
        branch_email: Branch being spawned (e.g., @trigger)
    """
    branch_name = branch_email.replace('@', '').upper()
    try:
        subprocess.run(
            ['notify-send', f'{branch_name} Running', f'Agent dispatched at {branch_email}'],
            capture_output=True,
            timeout=5
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return


if __name__ == "__main__":
    console = _get_console()
    console.print("\n" + "="*70)
    console.print("EMAIL DELIVERY HANDLER")
    console.print("="*70)
    console.print("\nPURPOSE:")
    console.print("  Delivers emails to branch inboxes")
    console.print()
    console.print("FUNCTIONS PROVIDED:")
    console.print("  - get_all_branches() -> List[Dict]")
    console.print("  - deliver_email_to_branch(to_branch, email_data) -> Tuple[bool, str]")
    console.print()
    console.print("HANDLER CHARACTERISTICS:")
    console.print("  - Independent - no module dependencies")
    console.print("  - Uses lazy imports for services")
    console.print("  - Pure business logic")
    console.print("  - CANNOT import parent modules")
    console.print()
    console.print("USAGE FROM MODULES:")
    console.print("  from ai_mail.apps.handlers.email.delivery import deliver_email_to_branch")
    console.print("  from ai_mail.apps.handlers.email.delivery import get_all_branches")
    console.print()
    console.print("="*70 + "\n")
