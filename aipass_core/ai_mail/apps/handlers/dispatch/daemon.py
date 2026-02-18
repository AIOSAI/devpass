#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: daemon.py - Dispatch Daemon Handler
# Date: 2026-02-17
# Version: 1.0.0
# Category: ai_mail/handlers/dispatch
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-17): Initial version - continuous polling daemon for autonomous dispatch
#
# CODE STANDARDS:
#   - Handler independence: NO cross-handler or module imports
#   - Pure business logic only
#   - Uses stdlib logging (standalone daemon process)
# =============================================

"""
Dispatch Daemon Handler

Polls registered branch inboxes for --dispatch emails and spawns agents.
The daemon IS the continuity - agents are ephemeral, wake-do-exit.

Architecture:
  - Polls every N seconds (configurable via safety_config.json)
  - Spawns via: cd /branch && claude -c -p 'prompt' (auto-continue most recent session)
  - Enforces: kill switch, max turns, max dispatches/day, lock files
  - Tracks daily dispatch counts per branch
"""

import json
import os
import sys
import time
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, Optional

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
AIPASS_HOME = Path.home()
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(AIPASS_HOME))

from aipass_core.ai_mail.apps.handlers.email.lock_utils import (
    acquire_lock, check_lock
)

# Paths
CONFIG_FILE = AIPASS_ROOT / "ai_mail" / "safety_config.json"
DAEMON_STATE_FILE = AIPASS_ROOT / "ai_mail" / "ai_mail.local" / "daemon_state.json"
DAEMON_LOG_FILE = AIPASS_ROOT / "ai_mail" / "ai_mail.local" / "dispatch_daemon.log"
BRANCH_REGISTRY = AIPASS_HOME / "BRANCH_REGISTRY.json"

# Graceful shutdown
SHUTDOWN = False

# Daemon logger (standalone - not Prax, handlers must not import Prax)
_DAEMON_LOGGER = logging.getLogger("dispatch_daemon")


def _setup_logging() -> None:
    """Configure daemon file and console logging."""
    DAEMON_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _DAEMON_LOGGER.setLevel(logging.INFO)
    if not _DAEMON_LOGGER.handlers:
        _DAEMON_LOGGER.addHandler(logging.FileHandler(str(DAEMON_LOG_FILE)))
        _DAEMON_LOGGER.addHandler(logging.StreamHandler())
    for handler in _DAEMON_LOGGER.handlers:
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))


def _handle_signal(signum, _frame):
    """Handle shutdown signals for graceful daemon stop."""
    global SHUTDOWN
    _DAEMON_LOGGER.info(f"Received signal {signum}, shutting down gracefully...")
    SHUTDOWN = True


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


def _read_json(filepath: Path) -> Optional[Dict[str, Any]]:
    """Read and parse a JSON file, returning None on failure."""
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(filepath: Path, data: Dict[str, Any]) -> bool:
    """Write data to a JSON file, returning success."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


def load_config() -> Dict[str, Any]:
    """Load safety config from JSON file."""
    DEFAULTS = {
        "kill_switch_path": "/home/aipass/.aipass/autonomous_pause",
        "poll_interval_seconds": 300,
        "max_depth": 3,
        "max_turns_per_wake": 15,
        "max_dispatches_per_branch_per_day": 10,
        "session_rotation_cycles": 12,
        "cold_start_prompt": "Hi. Check inbox, process new emails, update memories when done.",
        "wake_prompt": "Wake. Check inbox, process new emails, continue work. Update memories when done.",
        "heartbeat_prompt": "Heartbeat wake. No new dispatch — check your NOTEPAD, review pending work, follow up on any silent teams. Update memories when done.",
        "heartbeat_branches": {},
        "autonomous_branches": []
    }

    config = _read_json(CONFIG_FILE)
    if config is None:
        return DEFAULTS

    for key, val in DEFAULTS.items():
        if key not in config:
            config[key] = val
    return config


def load_daemon_state() -> Dict[str, Any]:
    """Load daemon state (daily counts, session tracking)."""
    EMPTY_STATE = {"daily_counts": {}, "session_cycles": {}, "date": str(date.today())}

    state = _read_json(DAEMON_STATE_FILE)
    if state is None:
        return EMPTY_STATE

    # Reset counts on new day
    if state.get("date") != str(date.today()):
        state["daily_counts"] = {}
        state["date"] = str(date.today())
    return state


def save_daemon_state(state: Dict[str, Any]) -> None:
    """Persist daemon state to disk."""
    state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not _write_json(DAEMON_STATE_FILE, state):
        _DAEMON_LOGGER.info(f"Failed to save daemon state to {DAEMON_STATE_FILE}")


def is_kill_switch_active(config: Dict[str, Any]) -> bool:
    """Check if the system-wide kill switch is engaged."""
    kill_path = Path(config.get("kill_switch_path", "/home/aipass/.aipass/autonomous_pause"))
    return kill_path.exists()


def get_registered_branches() -> list:
    """Load all registered branches from BRANCH_REGISTRY.json."""
    data = _read_json(BRANCH_REGISTRY)
    if data is None:
        return []
    return data.get("branches", [])


def check_inbox_for_dispatch(branch_path: Path) -> Optional[Dict[str, Any]]:
    """
    Check a branch's inbox for unprocessed --dispatch emails.

    Returns the first new dispatch email found, or None.
    """
    inbox_file = branch_path / "ai_mail.local" / "inbox.json"
    inbox_data = _read_json(inbox_file)
    if inbox_data is None:
        return None

    for msg in inbox_data.get("messages", []):
        if msg.get("auto_execute") and msg.get("status") == "new":
            return msg
    return None


def count_new_emails(branch_path: Path) -> int:
    """Count new (unread) emails in a branch's inbox."""
    inbox_file = branch_path / "ai_mail.local" / "inbox.json"
    inbox_data = _read_json(inbox_file)
    if inbox_data is None:
        return 0
    return sum(1 for m in inbox_data.get("messages", []) if m.get("status") == "new")


def spawn_agent(
    branch_path: Path,
    branch_email: str,
    message: Dict[str, Any],
    config: Dict[str, Any],
    state: Dict[str, Any]
) -> bool:
    """
    Spawn a Claude agent at the target branch to process dispatch email.

    Uses 'claude -c -p' to auto-continue the most recent session in CWD.

    Args:
        branch_path: Path to target branch
        branch_email: Branch email (e.g., @flow)
        message: The dispatch email message dict
        config: Safety config
        state: Daemon state (for cycle tracking)

    Returns:
        True if agent was spawned successfully
    """
    sender = message.get("from", "unknown")
    msg_id = message.get("id", "unknown")
    subject = message.get("subject", "")
    max_turns = config.get("max_turns_per_wake", 15)

    lock_file_path = str(branch_path / "ai_mail.local" / ".dispatch.lock")

    prompt = (
        f"Hi. Check inbox for task from {sender} (message ID: {msg_id}). "
        f"Execute it. Send confirmation when done. "
        f"IMPORTANT: When finished, delete the dispatch lock file at {lock_file_path}"
    )

    SPAWN_CMD = [
        "claude", "-c", "-p", prompt,
        "--max-turns", str(max_turns),
        "--permission-mode", "bypassPermissions",
        "--output-format", "json"
    ]

    target_cwd = str(branch_path)
    spawn_env = os.environ.copy()
    spawn_env["AIPASS_SPAWNED"] = "1"
    spawn_env.pop("CLAUDECODE", None)

    try:
        process = subprocess.Popen(
            SPAWN_CMD,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=target_cwd,
            env=spawn_env
        )

        pid = process.pid

        acquired, lock_msg = acquire_lock(branch_path, pid)
        if not acquired:
            _DAEMON_LOGGER.info(f"Lock acquisition failed after spawn for {branch_email}: {lock_msg}")

        # Track session cycles for rotation
        cycles = state.get("session_cycles", {})
        branch_key = str(branch_path)
        cycles[branch_key] = cycles.get(branch_key, 0) + 1
        state["session_cycles"] = cycles

        # Increment daily count
        daily = state.get("daily_counts", {})
        daily[branch_email] = daily.get(branch_email, 0) + 1
        state["daily_counts"] = daily

        # Desktop notification — show who woke and why
        notif_title = f"Daemon → {branch_email}"
        notif_body = f"Task from {sender}: \"{subject[:80]}\"" if subject else f"Dispatch from {sender}"
        try:
            subprocess.run(
                ["notify-send", "-i", "dialog-information", notif_title, notif_body],
                capture_output=True, timeout=5
            )
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            _DAEMON_LOGGER.info(f"Desktop notification unavailable for {branch_email}")

        _DAEMON_LOGGER.info(f"SPAWN {branch_email} PID={pid} sender={sender} subject=\"{subject[:60]}\"")
        return True

    except Exception as e:
        _DAEMON_LOGGER.info(f"SPAWN FAILED {branch_email}: {e}")
        return False


def spawn_heartbeat(
    branch_path: Path,
    branch_email: str,
    config: Dict[str, Any],
    state: Dict[str, Any]
) -> bool:
    """Spawn a heartbeat wake for a branch — no dispatch email needed.

    Heartbeat wakes let branches self-check on pending work and silent teams.

    Args:
        branch_path: Path to target branch
        branch_email: Branch email (e.g., @vera)
        config: Safety config
        state: Daemon state (for tracking)

    Returns:
        True if agent was spawned successfully
    """
    max_turns = config.get("max_turns_per_wake", 15)
    prompt = config.get(
        "heartbeat_prompt",
        "Heartbeat wake. Check your NOTEPAD, review pending work, follow up on silent teams. Update memories when done."
    )

    lock_file_path = str(branch_path / "ai_mail.local" / ".dispatch.lock")
    full_prompt = f"{prompt} IMPORTANT: When finished, delete the dispatch lock file at {lock_file_path}"

    spawn_cmd = [
        "claude", "-c", "-p", full_prompt,
        "--max-turns", str(max_turns),
        "--permission-mode", "bypassPermissions",
        "--output-format", "json"
    ]

    target_cwd = str(branch_path)
    spawn_env = os.environ.copy()
    spawn_env["AIPASS_SPAWNED"] = "1"
    spawn_env.pop("CLAUDECODE", None)

    try:
        process = subprocess.Popen(
            spawn_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=target_cwd,
            env=spawn_env
        )

        pid = process.pid

        acquired, lock_msg = acquire_lock(branch_path, pid)
        if not acquired:
            _DAEMON_LOGGER.info(f"Lock failed for heartbeat {branch_email}: {lock_msg}")

        # Track heartbeat time
        heartbeats = state.get("last_heartbeat", {})
        heartbeats[branch_email] = datetime.now().isoformat()
        state["last_heartbeat"] = heartbeats

        # Increment daily count (heartbeats count toward daily limit)
        daily = state.get("daily_counts", {})
        daily[branch_email] = daily.get(branch_email, 0) + 1
        state["daily_counts"] = daily

        # Desktop notification
        notif_title = f"Heartbeat → {branch_email}"
        notif_body = "Periodic self-check: reviewing pending work and silent teams"
        try:
            subprocess.run(
                ["notify-send", "-i", "dialog-information", notif_title, notif_body],
                capture_output=True, timeout=5
            )
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            pass

        _DAEMON_LOGGER.info(f"HEARTBEAT {branch_email} PID={pid}")
        return True

    except Exception as e:
        _DAEMON_LOGGER.info(f"HEARTBEAT FAILED {branch_email}: {e}")
        return False


def is_protected_branch(branch_email: str) -> bool:
    """Check if a branch is protected from auto-dispatch."""
    return branch_email == "@dev_central"


def poll_cycle(config: Dict[str, Any], state: Dict[str, Any]) -> int:
    """
    Run one poll cycle across all registered branches.

    Returns:
        Number of agents spawned this cycle
    """
    branches = get_registered_branches()
    autonomous_list = config.get("autonomous_branches", [])
    max_daily = config.get("max_dispatches_per_branch_per_day", 10)
    spawned = 0

    for branch in branches:
        if SHUTDOWN:
            break

        branch_email = branch.get("email", "")
        branch_path_str = branch.get("path", "")
        if not branch_email or not branch_path_str:
            continue

        branch_path = Path(branch_path_str)

        if is_protected_branch(branch_email):
            continue

        if autonomous_list and branch_email not in autonomous_list:
            continue

        daily_count = state.get("daily_counts", {}).get(branch_email, 0)
        if daily_count >= max_daily:
            continue

        dispatch_msg = check_inbox_for_dispatch(branch_path)
        if dispatch_msg is None:
            continue

        existing = check_lock(branch_path)
        if existing is not None:
            _DAEMON_LOGGER.info(f"SKIP {branch_email}: active lock (PID {existing.get('pid', '?')})")
            continue

        if spawn_agent(branch_path, branch_email, dispatch_msg, config, state):
            spawned += 1

    # Heartbeat checks — wake configured branches on a timer even without mail
    heartbeat_cfg = config.get("heartbeat_branches", {})
    if heartbeat_cfg:
        branch_lookup = {b.get("email", ""): b for b in branches}
        for hb_email, interval_seconds in heartbeat_cfg.items():
            if SHUTDOWN:
                break
            if is_protected_branch(hb_email):
                continue

            branch_info = branch_lookup.get(hb_email)
            if not branch_info:
                continue

            hb_path = Path(branch_info.get("path", ""))
            daily_count = state.get("daily_counts", {}).get(hb_email, 0)
            if daily_count >= max_daily:
                continue

            # Check if enough time has passed since last heartbeat
            last_hb = state.get("last_heartbeat", {}).get(hb_email)
            if last_hb:
                try:
                    elapsed = (datetime.now() - datetime.fromisoformat(last_hb)).total_seconds()
                    if elapsed < interval_seconds:
                        continue
                except (ValueError, TypeError):
                    pass

            # Skip if branch has active lock (already working)
            existing = check_lock(hb_path)
            if existing is not None:
                continue

            # Skip if branch has pending dispatch (dispatch takes priority)
            if check_inbox_for_dispatch(hb_path) is not None:
                continue

            if spawn_heartbeat(hb_path, hb_email, config, state):
                spawned += 1

    return spawned


def run_daemon() -> None:
    """
    Main daemon loop. Polls inboxes at configured interval, spawns agents.

    Exits gracefully on SIGTERM/SIGINT or kill switch.
    """
    _setup_logging()

    _DAEMON_LOGGER.info("=" * 60)
    _DAEMON_LOGGER.info("DISPATCH DAEMON STARTING")
    _DAEMON_LOGGER.info("=" * 60)

    config = load_config()
    poll_interval = config.get("poll_interval_seconds", 300)

    _DAEMON_LOGGER.info(f"Poll interval: {poll_interval}s")
    _DAEMON_LOGGER.info(f"Kill switch: {config.get('kill_switch_path')}")
    _DAEMON_LOGGER.info(f"Max turns/wake: {config.get('max_turns_per_wake')}")
    _DAEMON_LOGGER.info(f"Max dispatches/branch/day: {config.get('max_dispatches_per_branch_per_day')}")

    autonomous = config.get("autonomous_branches", [])
    if autonomous:
        _DAEMON_LOGGER.info(f"Autonomous branches: {', '.join(autonomous)}")
    else:
        _DAEMON_LOGGER.info("Autonomous branches: ALL (no filter)")

    heartbeats = config.get("heartbeat_branches", {})
    if heartbeats:
        for hb_email, hb_interval in heartbeats.items():
            _DAEMON_LOGGER.info(f"Heartbeat: {hb_email} every {hb_interval}s ({hb_interval // 60}m)")
    else:
        _DAEMON_LOGGER.info("Heartbeat: none configured")

    cycle_count = 0

    while not SHUTDOWN:
        if is_kill_switch_active(config):
            _DAEMON_LOGGER.info("Kill switch ACTIVE - pausing all dispatches")
            time.sleep(poll_interval)
            continue

        config = load_config()
        poll_interval = config.get("poll_interval_seconds", 300)

        state = load_daemon_state()
        cycle_count += 1

        _DAEMON_LOGGER.info(f"--- Poll cycle {cycle_count} ---")

        spawned = poll_cycle(config, state)

        if spawned > 0:
            _DAEMON_LOGGER.info(f"Cycle {cycle_count}: spawned {spawned} agent(s)")

        save_daemon_state(state)

        elapsed = 0
        while elapsed < poll_interval and not SHUTDOWN:
            time.sleep(min(5, poll_interval - elapsed))
            elapsed += 5

    _DAEMON_LOGGER.info("DISPATCH DAEMON STOPPED")


if __name__ == "__main__":
    run_daemon()
