#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: lock_utils.py - Dispatch Lock Handler
# Date: 2026-02-09
# Version: 1.1.0
# Category: ai_mail/handlers/email
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2026-02-10): Reduce stale lock timeout from 1800s to 600s (10 min)
#   - v1.0.0 (2026-02-09): Initial implementation - PID-based single instance lock per branch
#
# CODE STANDARDS:
#   - Handler independence: NO cross-domain imports
#   - Uses logging module for diagnostics
#   - Pure business logic only
# =============================================

"""
Dispatch Lock Handler

PID-based single instance lock per branch.
Prevents multiple dispatch agents from spawning concurrently at the same branch.
Uses atomic file creation (O_CREAT|O_EXCL) to avoid race conditions.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

# Standard logging
logger = logging.getLogger("ai_mail.lock_utils")

# Lock file name - placed in branch's ai_mail.local/ directory
LOCK_FILENAME = ".dispatch.lock"

# Stale lock timeout in seconds (10 minutes)
STALE_LOCK_TIMEOUT = 600


def _get_lock_path(branch_path: Path) -> Path:
    """Get the lock file path for a branch."""
    if branch_path == Path("/") or branch_path == Path.home():
        return Path.home() / "ai_mail.local" / LOCK_FILENAME
    return branch_path / "ai_mail.local" / LOCK_FILENAME


def _is_pid_running(pid: int) -> bool:
    """Check if a process with the given PID is still running."""
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        # Process exists but we don't have permission to signal it
        return True
    except ProcessLookupError:
        return False


def _is_lock_stale(lock_data: dict) -> bool:
    """
    Check if a lock is stale (process dead or timeout exceeded).

    Returns True if the lock should be considered stale and can be removed.
    """
    pid = lock_data.get("pid")
    timestamp = lock_data.get("timestamp")

    # No PID = stale
    if pid is None:
        return True

    # Process no longer running = stale
    if not _is_pid_running(pid):
        logger.info(f"[lock] PID {pid} no longer running - lock is stale")
        return True

    # Timeout check - if lock is older than STALE_LOCK_TIMEOUT, consider stale
    if timestamp:
        try:
            lock_time = datetime.fromisoformat(timestamp)
            elapsed = (datetime.now() - lock_time).total_seconds()
            if elapsed > STALE_LOCK_TIMEOUT:
                logger.warning(f"[lock] Lock exceeded timeout ({elapsed:.0f}s > {STALE_LOCK_TIMEOUT}s) - treating as stale")
                return True
        except (ValueError, TypeError) as e:
            logger.warning(f"[lock] Failed to parse lock timestamp: {e}")

    return False


def acquire_lock(branch_path: Path, pid: int) -> tuple[bool, str]:
    """
    Attempt to acquire a dispatch lock for a branch.

    Uses atomic file creation to prevent race conditions.

    Args:
        branch_path: Path to the target branch
        pid: PID of the agent being spawned

    Returns:
        Tuple of (acquired: bool, message: str)
        If not acquired, message contains reason (e.g., existing PID info)
    """
    lock_path = _get_lock_path(branch_path)

    # Ensure parent directory exists
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # Check for existing lock first
    if lock_path.exists():
        try:
            with open(lock_path, 'r', encoding='utf-8') as f:
                existing_lock = json.load(f)

            if _is_lock_stale(existing_lock):
                # Remove stale lock and try again
                logger.info(f"[lock] Removing stale lock at {lock_path}")
                lock_path.unlink(missing_ok=True)
            else:
                # Active lock exists - bounce
                existing_pid = existing_lock.get("pid", "unknown")
                existing_sender = existing_lock.get("sender", "unknown")
                existing_time = existing_lock.get("timestamp", "unknown")
                msg = f"Branch already has active dispatch agent (PID: {existing_pid}, sender: {existing_sender}, since: {existing_time})"
                logger.info(f"[lock] Lock denied: {msg}")
                return False, msg

        except (json.JSONDecodeError, OSError) as e:
            # Corrupted lock file - remove it
            logger.warning(f"[lock] Corrupted lock file at {lock_path}: {e} - removing")
            lock_path.unlink(missing_ok=True)

    # Create lock file atomically using O_CREAT|O_EXCL
    lock_data = {
        "pid": pid,
        "timestamp": datetime.now().isoformat(),
        "branch": str(branch_path)
    }

    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, json.dumps(lock_data, indent=2).encode('utf-8'))
        finally:
            os.close(fd)

        logger.info(f"[lock] Lock acquired at {lock_path} (PID: {pid})")
        return True, "Lock acquired"

    except FileExistsError:
        # Race condition - another process created the lock between our check and create
        msg = "Lock acquisition failed - another dispatch just started"
        logger.info(f"[lock] {msg}")
        return False, msg


def release_lock(branch_path: Path, pid: int | None = None) -> bool:
    """
    Release a dispatch lock for a branch.

    Args:
        branch_path: Path to the target branch
        pid: If provided, only release if lock belongs to this PID (safety check)

    Returns:
        True if lock was released, False if not found or owned by different PID
    """
    lock_path = _get_lock_path(branch_path)

    if not lock_path.exists():
        return True  # No lock = already released

    # If PID specified, verify ownership before releasing
    if pid is not None:
        try:
            with open(lock_path, 'r', encoding='utf-8') as f:
                lock_data = json.load(f)
            if lock_data.get("pid") != pid:
                logger.warning(f"[lock] Release denied - lock owned by PID {lock_data.get('pid')}, not {pid}")
                return False
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"[lock] Corrupted lock file during release at {lock_path}: {e} - removing anyway")

    try:
        lock_path.unlink(missing_ok=True)
        logger.info(f"[lock] Lock released at {lock_path}")
        return True
    except OSError as e:
        logger.error(f"[lock] Failed to release lock at {lock_path}: {e}")
        return False


def check_lock(branch_path: Path) -> dict | None:
    """
    Check if a branch has an active dispatch lock.

    Returns:
        Lock data dict if active lock exists, None otherwise.
        Automatically cleans up stale locks.
    """
    lock_path = _get_lock_path(branch_path)

    if not lock_path.exists():
        return None

    try:
        with open(lock_path, 'r', encoding='utf-8') as f:
            lock_data = json.load(f)

        if _is_lock_stale(lock_data):
            # Auto-cleanup stale lock
            lock_path.unlink(missing_ok=True)
            logger.info(f"[lock] Auto-cleaned stale lock at {lock_path}")
            return None

        return lock_data

    except (json.JSONDecodeError, OSError):
        # Corrupted - clean up
        lock_path.unlink(missing_ok=True)
        return None
