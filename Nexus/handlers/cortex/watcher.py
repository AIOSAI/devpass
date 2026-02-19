#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: watcher.py - Filesystem event detection
# Date: 2026-02-18
# Version: 1.0.0
# Category: Nexus/handlers/cortex
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial build from v1 cortex_module.py
#
# CODE STANDARDS:
#   - Error handling: graceful watchdog fallback
# =============================================

"""
CortexFileWatcher - Filesystem Event Detection

Monitors the Nexus directory for .py, .json, .md file changes using watchdog's
FileSystemEventHandler. Changes are tracked in memory with debouncing to avoid
excessive updates. The observer runs in a background thread.

If watchdog is not installed, the module degrades gracefully - logging a warning
and disabling file watching without crashing.
"""

import sys
import logging
import threading
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

logger = logging.getLogger(__name__)

# --- Graceful watchdog import ---
WATCHDOG_AVAILABLE = False
_BaseHandler = object

try:
    from watchdog.observers import Observer as _Observer
    from watchdog.events import FileSystemEventHandler as _FSHandler
    WATCHDOG_AVAILABLE = True
    _BaseHandler = _FSHandler
except ImportError:
    _Observer = None  # type: ignore[assignment, misc]
    logger.warning(
        "watchdog not installed - cortex file watching disabled. "
        "Install with: pip install watchdog"
    )

# --- Configuration ---
NEXUS_DIR = Path(__file__).resolve().parent.parent.parent
VALID_EXTENSIONS = {".py", ".json", ".md"}
IGNORE_DIRS = {
    ".venv", "__pycache__", ".git", ".archive", "data",
    "node_modules", ".mypy_cache", ".pytest_cache", "logs"
}
IGNORE_FILES = {
    "cortex.json",
    "chat_history.json",
    "pulse.json",
    "session_summaries.json",
    "summaries.json",
}
# Debounce: ignore repeated events on the same file within this window (seconds)
DEBOUNCE_SECONDS = 2.0
# Maximum tracked changes before oldest are evicted
MAX_TRACKED_CHANGES = 200


class CortexFileWatcher(_BaseHandler):  # type: ignore[misc]
    """Watches the Nexus directory for file system events.

    Tracks file creates, modifications, and deletions for files matching
    VALID_EXTENSIONS, while ignoring transient directories and data files.
    Changes are stored in an ordered dict with debouncing to prevent
    duplicate events from rapid saves.

    Attributes:
        changes: OrderedDict mapping filepath -> change record
        _lock: Thread lock for safe concurrent access
        _debounce: Dict tracking last event time per filepath
    """

    def __init__(self, watch_dir: "Path | None" = None):
        """Initialize the watcher.

        Args:
            watch_dir: Directory to watch. Defaults to Nexus root.
        """
        super().__init__()
        self.watch_dir = Path(watch_dir) if watch_dir else NEXUS_DIR
        self.changes: OrderedDict = OrderedDict()
        self._lock = threading.Lock()
        self._debounce: dict = {}
        self._observer = None
        logger.info("CortexFileWatcher initialized for: %s", self.watch_dir)

    # --- Public API ---

    def start(self) -> bool:
        """Start the background filesystem observer.

        Creates a watchdog Observer thread that monitors the watch_dir
        recursively. No-op if watchdog is unavailable or already running.
        """
        if not WATCHDOG_AVAILABLE or _Observer is None:
            logger.warning("Cannot start watcher - watchdog not installed")
            return False

        if self._observer and self._observer.is_alive():
            logger.info("Watcher already running")
            return True

        try:
            self._observer = _Observer()
            self._observer.daemon = True  # Don't block shutdown
            self._observer.schedule(self, str(self.watch_dir), recursive=True)
            self._observer.start()
            logger.info("Cortex watcher started: %s", self.watch_dir)
            return True
        except Exception as e:
            logger.error("Failed to start cortex watcher: %s", e)
            self._observer = None
            return False

    def stop(self):
        """Stop the background filesystem observer.

        Cleanly shuts down the observer thread. Safe to call even if
        not running.
        """
        if self._observer and self._observer.is_alive():
            try:
                self._observer.stop()
                self._observer.join(timeout=5)
                logger.info("Cortex watcher stopped")
            except Exception as e:
                logger.error("Error stopping cortex watcher: %s", e)
            finally:
                self._observer = None
        else:
            logger.info("Watcher not running, nothing to stop")

    def is_running(self) -> bool:
        """Check if the watcher is currently active."""
        return bool(self._observer and self._observer.is_alive())

    def get_recent_changes(self, n: int = 10) -> list:
        """Return the N most recent file changes.

        Args:
            n: Number of recent changes to return. Default 10.

        Returns:
            List of dicts, each with keys: filepath, change_type,
            timestamp, changes_count. Most recent first.
        """
        with self._lock:
            items = list(self.changes.items())
        # Sort by timestamp descending, take n
        items.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)
        result = []
        for filepath, record in items[:n]:
            result.append({
                "filepath": filepath,
                "change_type": record.get("change_type", "unknown"),
                "timestamp": record.get("timestamp", ""),
                "changes_count": record.get("changes_count", 0),
            })
        return result

    def get_all_changes(self) -> dict:
        """Return a copy of all tracked changes."""
        with self._lock:
            return dict(self.changes)

    def reset_session(self):
        """Reset all session change counters to zero.

        Called at session start so Nexus knows which changes happened
        during the current conversation vs. previous ones.
        """
        with self._lock:
            for record in self.changes.values():
                record["changes_count"] = 0
            self._debounce.clear()
        logger.info("Cortex session counters reset")

    def clear(self):
        """Clear all tracked changes."""
        with self._lock:
            self.changes.clear()
            self._debounce.clear()
        logger.info("Cortex change tracking cleared")

    # --- Watchdog event handlers ---

    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self._handle_event(event.src_path, "created")

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self._handle_event(event.src_path, "modified")

    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            self._handle_event(event.src_path, "deleted")

    # --- Internal methods ---

    def _handle_event(self, src_path: str, change_type: str):
        """Process a filesystem event with validation and debouncing.

        Args:
            src_path: Absolute path of the affected file.
            change_type: One of 'created', 'modified', 'deleted'.
        """
        path = Path(src_path)

        # Validate file
        if not self._is_valid_file(path):
            return

        # Debounce: skip if same file changed within DEBOUNCE_SECONDS
        now = time.time()
        filepath_str = str(path)
        last_time = self._debounce.get(filepath_str, 0)
        if (now - last_time) < DEBOUNCE_SECONDS:
            return

        # Make path relative to watch dir for clean keys
        try:
            rel_path = str(path.relative_to(self.watch_dir))
        except ValueError:
            rel_path = str(path)

        timestamp = datetime.now().isoformat()

        with self._lock:
            self._debounce[filepath_str] = now

            if rel_path in self.changes:
                record = self.changes[rel_path]
                record["change_type"] = change_type
                record["timestamp"] = timestamp
                record["changes_count"] = record.get("changes_count", 0) + 1
                # Move to end (most recent)
                self.changes.move_to_end(rel_path)
            else:
                self.changes[rel_path] = {
                    "change_type": change_type,
                    "timestamp": timestamp,
                    "changes_count": 1,
                }

            # Evict oldest if over limit
            while len(self.changes) > MAX_TRACKED_CHANGES:
                self.changes.popitem(last=False)

        logger.info("Cortex: %s -> %s", change_type, rel_path)

    def _is_valid_file(self, path: Path) -> bool:
        """Check if a file should be tracked.

        Args:
            path: Path to check.

        Returns:
            True if the file has a valid extension, is not in an
            ignored directory, and is not an ignored file.
        """
        # Check extension
        if path.suffix.lower() not in VALID_EXTENSIONS:
            return False

        # Check ignored filenames
        if path.name in IGNORE_FILES:
            return False

        # Check ignored directories (any parent)
        for part in path.parts:
            if part in IGNORE_DIRS:
                return False

        return True
