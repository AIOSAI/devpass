#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: log_watcher.py - Branch Log Watcher Event Producer
# Date: 2026-02-02
# Version: 1.0.0
# Category: trigger/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.1 (2026-02-10): FPLAN-0310 Phase 2 - Persist dedup hashes to trigger_data.json, increase max to 2000
#   - v1.0.0 (2026-02-02): Created - FPLAN-0284 Phase 1
#
# CODE STANDARDS:
#   - Follows AIPass Seed standards
#   - NO console.print() - handlers return data to modules
#   - Fires error_detected events when ERROR entries found in branch logs
#   - Hash-based deduplication to avoid spam on repeated errors
# =============================================

"""
Branch Log Watcher Event Producer

Watches */logs/*.log across all branches for ERROR entries.
Also watches ~/system_logs/ for system-level services.
Fires error_detected events for the Trigger event system.

Architecture:
    - Watches: /home/aipass/aipass_core/*/logs/*.log
    - Watches: /home/aipass/system_logs/*.log (mapped to owning branch)
    - Parses: Prax format (timestamp | module | LEVEL | message)
    - Fires: error_detected event (via callback, branch=..., module=..., message=..., log_path=...)
    - Deduplicates: By hash of (module + message) to avoid spam
"""

import json
import sys
import hashlib
from pathlib import Path
from typing import Any, Dict, Set, Optional, Callable

AIPASS_ROOT = Path.home() / "aipass_core"
AIPASS_HOME = Path.home()
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(AIPASS_HOME))

# Persistent hash storage
TRIGGER_DATA_FILE = AIPASS_ROOT / "trigger" / "trigger_data.json"

# Try to import watchdog
try:
    from watchdog.observers import Observer as WatchdogObserver
    from watchdog.events import FileSystemEventHandler as WatchdogFileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    WatchdogObserver = None  # type: ignore
    WatchdogFileSystemEventHandler = object  # type: ignore

# Global state
_branch_log_observer: Any = None
_seen_error_hashes: Set[str] = set()
MAX_SEEN_HASHES = 2000  # Limit memory usage

# Explicit mapping of system_logs filenames to their owning branch.
# Used for files that don't follow the <branch>_<module>.log naming convention.
SYSTEM_LOGS_BRANCH_MAP: Dict[str, str] = {
    'telegram_bridge.log': 'API',
    'telegram_chats.log': 'API',
}

SYSTEM_LOGS_DIR = AIPASS_HOME / "system_logs"

# Known branch prefixes that appear in system_logs filenames (<prefix>_<module>.log).
# Sorted longest-first so "MEMORY_BANK" matches before "MEMORY", "backup_system" before "backup", etc.
_SYSTEM_LOGS_BRANCH_PREFIXES: list = sorted([
    'ai_mail', 'api', 'backup_system', 'cli', 'cortex', 'drone', 'flow',
    'prax', 'trigger', 'seed', 'MEMORY_BANK', 'The_Commons',
    'aipass_os', 'aipass_business',
], key=len, reverse=True)

# Event fire callback (set by module, avoids handler importing from modules)
_fire_event: Optional[Callable[..., None]] = None


def _load_seen_hashes() -> None:
    """
    Load persisted dedup hashes from trigger_data.json on startup.

    Populates _seen_error_hashes from disk so deduplication
    survives restarts.
    """
    global _seen_error_hashes
    try:
        if TRIGGER_DATA_FILE.exists():
            data = json.loads(TRIGGER_DATA_FILE.read_text(encoding='utf-8'))
            stored = data.get('seen_error_hashes', [])
            _seen_error_hashes = set(stored)
    except Exception:
        _seen_error_hashes = set()  # Start fresh on read failure


def _save_seen_hashes() -> None:
    """
    Persist dedup hashes to trigger_data.json.

    Writes current _seen_error_hashes to disk so they survive restarts.
    Merges with existing trigger_data.json content to preserve other keys.
    """
    try:
        data: Dict[str, Any] = {}
        if TRIGGER_DATA_FILE.exists():
            data = json.loads(TRIGGER_DATA_FILE.read_text(encoding='utf-8'))
        data['seen_error_hashes'] = list(_seen_error_hashes)
        TRIGGER_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        TRIGGER_DATA_FILE.write_text(
            json.dumps(data, indent=2), encoding='utf-8'
        )
    except Exception:
        return  # Write failure - hashes remain in memory only


def _generate_error_hash(source_module: str, message: str) -> str:
    """
    Generate hash for error deduplication.

    Args:
        source_module: Module that generated the error
        message: Error message content

    Returns:
        8-character hash string
    """
    content = f"{source_module}:{message}"
    return hashlib.md5(content.encode()).hexdigest()[:8]


def _detect_branch_from_path(log_path: str) -> str:
    """
    Detect branch name from log file path.

    Handles two path patterns:
        - /home/aipass/aipass_core/<branch>/logs/<file>.log
        - /home/aipass/system_logs/<file>.log (mapped via SYSTEM_LOGS_BRANCH_MAP,
          falls back to branch prefix in filename like "api_api.log" → API)

    Args:
        log_path: Full path to log file

    Returns:
        Branch name in uppercase (e.g., 'FLOW', 'PRAX')
    """
    try:
        path = Path(log_path)

        # Check system_logs/ files first
        if path.parent == SYSTEM_LOGS_DIR:
            filename = path.name
            # Explicit mapping for known services
            if filename in SYSTEM_LOGS_BRANCH_MAP:
                return SYSTEM_LOGS_BRANCH_MAP[filename]
            # Match filename prefix against known branch names (longest-first)
            name_stem = path.stem  # e.g. "MEMORY_BANK_rollover" from "MEMORY_BANK_rollover.log"
            for prefix in _SYSTEM_LOGS_BRANCH_PREFIXES:
                if name_stem.startswith(prefix + '_') or name_stem == prefix:
                    return prefix.upper()
            return 'UNKNOWN'

        # Standard aipass_core/<branch>/logs/ pattern
        parts = path.parts
        for i, part in enumerate(parts):
            if part == 'aipass_core' and i + 1 < len(parts):
                return parts[i + 1].upper()
        return 'UNKNOWN'
    except Exception:
        return 'UNKNOWN'


def _parse_prax_log_line(log_line: str) -> Optional[Dict[str, str]]:
    """
    Parse a log line in Prax format or Python logging format.

    Formats supported:
        - Prax:   timestamp | module | LEVEL | message
        - Python: timestamp - module - LEVEL - message

    Args:
        log_line: Raw log line

    Returns:
        Dict with keys: timestamp, module, level, message
        None if parsing fails or line is not ERROR level
    """
    try:
        # Try Prax format first (pipe-separated)
        if ' | ' in log_line:
            parts = log_line.split(' | ', 3)
            if len(parts) >= 4:
                level = parts[2].strip().upper()
                if level in ('ERROR', 'CRITICAL'):
                    return {
                        'timestamp': parts[0].strip(),
                        'module': parts[1].strip(),
                        'level': level,
                        'message': parts[3].strip()
                    }
                return None

        # Fallback: Python logging format (dash-separated)
        # Format: 2026-02-10 15:12:29,460 - telegram_bridge - ERROR - message
        if ' - ' in log_line and (' - ERROR - ' in log_line or ' - CRITICAL - ' in log_line):
            parts = log_line.split(' - ', 3)
            if len(parts) >= 4:
                level = parts[2].strip().upper()
                if level in ('ERROR', 'CRITICAL'):
                    return {
                        'timestamp': parts[0].strip(),
                        'module': parts[1].strip(),
                        'level': level,
                        'message': parts[3].strip()
                    }

        return None
    except Exception:
        return None


def _is_duplicate_error(error_hash: str) -> bool:
    """
    Check if error has been seen before (deduplication).

    Args:
        error_hash: Hash of module + message

    Returns:
        True if this error has been seen before
    """
    global _seen_error_hashes

    if error_hash in _seen_error_hashes:
        return True

    # Add to seen set with size limit
    _seen_error_hashes.add(error_hash)
    if len(_seen_error_hashes) > MAX_SEEN_HASHES:
        # Remove oldest entries (convert to list, slice, back to set)
        _seen_error_hashes = set(list(_seen_error_hashes)[MAX_SEEN_HASHES // 2:])

    # Persist to disk after each new hash
    _save_seen_hashes()

    return False


def set_event_callback(callback: Callable[..., None]) -> None:
    """
    Set the callback function for firing events.

    Must be called by the module before starting the watcher.
    This avoids handler importing from modules (maintains independence).

    Args:
        callback: Function to call with (event_name, **data)
    """
    global _fire_event
    _fire_event = callback


class BranchLogWatcher(WatchdogFileSystemEventHandler if WATCHDOG_AVAILABLE else object):  # type: ignore[misc]
    """
    Watch branch log files and fire error_detected events.

    Monitors /home/aipass/aipass_core/*/logs/*.log for ERROR entries.
    """

    def __init__(self):
        """Initialize log watcher with position tracking."""
        super().__init__()
        self.log_positions: Dict[str, int] = {}

    def on_modified(self, event) -> None:
        """
        Handle log file modification events.

        Reads new content and fires error_detected for ERROR entries.
        """
        if event.is_directory:
            return

        file_path = str(event.src_path)

        if not file_path.endswith('.log'):
            return

        # Only process branch logs (aipass_core/*/logs/) or system_logs/
        is_branch_log = '/aipass_core/' in file_path and '/logs/' in file_path
        is_system_log = '/system_logs/' in file_path
        if not is_branch_log and not is_system_log:
            return

        try:
            current_size = Path(file_path).stat().st_size
            last_pos = self.log_positions.get(file_path, 0)

            # Handle log rotation (file got smaller)
            if current_size < last_pos:
                last_pos = 0

            if current_size > last_pos:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_pos)
                    new_lines = f.read()

                    if new_lines.strip():
                        for line in new_lines.strip().split('\n'):
                            if line.strip():
                                self._process_log_line(line, file_path)

                    self.log_positions[file_path] = f.tell()

        except Exception:
            return  # Read failure on this event - skip without raising

    def _process_log_line(self, log_line: str, log_path: str) -> None:
        """
        Process a log line and fire error_detected if ERROR found.

        Args:
            log_line: Raw log line
            log_path: Path to log file
        """
        try:
            parsed = _parse_prax_log_line(log_line)
            if not parsed:
                return

            branch = _detect_branch_from_path(log_path)
            module = parsed['module']
            message = parsed['message']

            # Generate hash for deduplication
            error_hash = _generate_error_hash(module, message)

            # Skip if duplicate
            if _is_duplicate_error(error_hash):
                return

            # Fire error_detected event via callback
            if _fire_event is not None:
                _fire_event(
                    'error_detected',
                    branch=branch,
                    module=module,
                    message=message,
                    log_path=log_path,
                    error_hash=error_hash,
                    timestamp=parsed['timestamp']
                )

        except Exception:
            return  # Parse/fire failure on this line - skip without raising

    def initialize_positions(self) -> None:
        """
        Initialize log positions to END of existing files.

        Only process NEW entries after watcher starts.
        Covers both aipass_core/*/logs/ and system_logs/.
        """
        # Branch logs under aipass_core/*/logs/
        for branch_dir in AIPASS_ROOT.iterdir():
            if not branch_dir.is_dir():
                continue
            logs_dir = branch_dir / 'logs'
            if not logs_dir.exists():
                continue
            for log_file in logs_dir.glob('*.log'):
                try:
                    self.log_positions[str(log_file)] = log_file.stat().st_size
                except Exception:
                    continue  # Skip unreadable log file

        # System-level logs under ~/system_logs/
        if SYSTEM_LOGS_DIR.exists():
            for log_file in SYSTEM_LOGS_DIR.glob('*.log'):
                try:
                    self.log_positions[str(log_file)] = log_file.stat().st_size
                except Exception:
                    continue  # Skip unreadable log file


def start_branch_log_watcher() -> Any:
    """
    Start the branch log watcher.

    Watches /home/aipass/aipass_core/*/logs/*.log for ERROR entries.

    Returns:
        Observer instance (caller must keep reference to keep alive)
        None if watchdog not available or error
    """
    global _branch_log_observer

    if not WATCHDOG_AVAILABLE:
        return None

    # Stop existing watcher if running
    if _branch_log_observer and _branch_log_observer.is_alive():
        stop_branch_log_watcher()

    if not AIPASS_ROOT.exists():
        return None

    if WatchdogObserver is None:
        return None

    # Load persisted dedup hashes from disk
    _load_seen_hashes()

    watcher = BranchLogWatcher()
    watcher.initialize_positions()

    observer = WatchdogObserver()

    # Schedule watcher for each branch's logs directory
    for branch_dir in AIPASS_ROOT.iterdir():
        if not branch_dir.is_dir():
            continue
        logs_dir = branch_dir / 'logs'
        if logs_dir.exists():
            observer.schedule(watcher, str(logs_dir), recursive=False)

    # Also watch system_logs/ for system-level log files
    if SYSTEM_LOGS_DIR.exists():
        observer.schedule(watcher, str(SYSTEM_LOGS_DIR), recursive=False)

    observer.start()
    _branch_log_observer = observer

    return observer


def stop_branch_log_watcher() -> None:
    """Stop the branch log watcher."""
    global _branch_log_observer

    if _branch_log_observer and _branch_log_observer.is_alive():
        _branch_log_observer.stop()
        _branch_log_observer.join(timeout=5.0)
        _branch_log_observer = None


def is_branch_log_watcher_active() -> bool:
    """
    Check if branch log watcher is running.

    Returns:
        True if watcher is active
    """
    return _branch_log_observer is not None and _branch_log_observer.is_alive()


def clear_seen_hashes() -> None:
    """
    Clear the deduplication hash set (memory and disk).

    Useful for testing or after extended runtime.
    """
    global _seen_error_hashes
    _seen_error_hashes.clear()
    _save_seen_hashes()


def get_watcher_status() -> Dict[str, Any]:
    """
    Get current watcher status.

    Returns:
        Dict with status information
    """
    return {
        'active': is_branch_log_watcher_active(),
        'watchdog_available': WATCHDOG_AVAILABLE,
        'seen_hashes_count': len(_seen_error_hashes),
        'aipass_root': str(AIPASS_ROOT)
    }


if __name__ == '__main__':
    """Standalone test for branch log watcher."""
    import time

    def test_fire_event(event_name: str, **data: Any) -> None:
        """Test callback that prints events."""
        print(f"[EVENT] {event_name}: {data}")

    # Set callback for standalone testing
    set_event_callback(test_fire_event)

    print("Branch Log Watcher Test")
    print(f"Monitoring: {AIPASS_ROOT}/*/logs/*.log")
    print(f"Monitoring: {SYSTEM_LOGS_DIR}/*.log")
    print("Press Ctrl+C to stop")
    print()

    observer = start_branch_log_watcher()

    if not observer:
        print("Failed to start branch log watcher")
        if not WATCHDOG_AVAILABLE:
            print("  - watchdog package not installed")
        sys.exit(1)

    print(f"Status: {get_watcher_status()}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_branch_log_watcher()
        print("Stopped")
