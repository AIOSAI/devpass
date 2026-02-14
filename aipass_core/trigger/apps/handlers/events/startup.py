#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: startup.py - Startup Event Handler
# Date: 2026-02-03
# Version: 0.2.0
# Category: trigger/handlers/events
#
# CHANGELOG (Max 5 entries):
#   - v0.2.0 (2026-02-03): Added error catch-up on startup
#   - v0.1.0 (2025-12-04): Created startup event handler
#
# CODE STANDARDS:
#   - Follows AIPass Seed standards
#   - Replaces Prax logger's hardcoded calls with event-based approach
#   - Handlers must not import Prax logger
#   - Handlers receive fire_event callback via kwargs (no module imports)
# =============================================

"""Startup Event Handler - Run startup checks

Replaces Prax logger's hardcoded calls with event-based approach.
Includes error catch-up: scans system logs for unprocessed errors on each startup.
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

AIPASS_ROOT = Path.home() / "aipass_core"
AIPASS_HOME = Path.home()
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(AIPASS_HOME))

SYSTEM_LOGS_DIR = AIPASS_HOME / "system_logs"
TRIGGER_DATA_FILE = AIPASS_ROOT / "trigger" / "trigger_json" / "trigger_data.json"
MAX_HASHES = 500
MAX_LOOKBACK_HOURS = 24


def _load_trigger_data() -> Dict[str, Any]:
    """Load trigger_data.json with error_catchup section."""
    try:
        if TRIGGER_DATA_FILE.exists():
            with open(TRIGGER_DATA_FILE, 'r') as f:
                data = json.load(f)
            if 'error_catchup' not in data:
                data['error_catchup'] = {
                    'last_scan_timestamp': None,
                    'processed_hashes': [],
                    'max_hashes': MAX_HASHES,
                    'max_lookback_hours': MAX_LOOKBACK_HOURS
                }
            return data
    except Exception:
        pass
    return {
        'error_catchup': {
            'last_scan_timestamp': None,
            'processed_hashes': [],
            'max_hashes': MAX_HASHES,
            'max_lookback_hours': MAX_LOOKBACK_HOURS
        }
    }


def _save_trigger_data(data: Dict[str, Any]) -> None:
    """Save trigger_data.json."""
    try:
        TRIGGER_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TRIGGER_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _generate_error_hash(module_name: str, message: str) -> str:
    """Generate 8-char hash for error deduplication."""
    content = f"{module_name}:{message}"
    return hashlib.md5(content.encode()).hexdigest()[:8]


def _detect_log_level(log_line: str) -> str:
    """Detect log level from log line content."""
    if ' - ERROR - ' in log_line or ' ERROR ' in log_line or '[ERROR]' in log_line:
        return 'error'
    if ' - CRITICAL - ' in log_line or ' CRITICAL ' in log_line or '[CRITICAL]' in log_line:
        return 'error'
    if ' - WARNING - ' in log_line or ' WARNING ' in log_line or '[WARNING]' in log_line:
        return 'warning'
    return 'info'


def _parse_log_message(log_line: str) -> str:
    """Extract clean message from log line."""
    if ' | ' in log_line:
        parts = log_line.split(' | ')
        if len(parts) >= 4:
            return ' | '.join(parts[3:]).strip()
        if len(parts) >= 2:
            return parts[-1].strip()
    return log_line.strip()


def _extract_module_name(log_line: str) -> str:
    """Extract module name from log line."""
    if ' | ' in log_line:
        parts = log_line.split(' | ')
        if len(parts) >= 2:
            return parts[1].strip()
    return 'unknown'


def _extract_timestamp(log_line: str) -> Optional[datetime]:
    """Extract timestamp from log line (format: YYYY-MM-DD HH:MM:SS)."""
    try:
        if ' | ' in log_line:
            parts = log_line.split(' | ')
            if parts:
                ts_str = parts[0].strip()
                return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
    except Exception:
        pass
    return None


def _detect_branch_from_log(log_file: str) -> str:
    """Detect branch from log filename (e.g., drone_ops.log -> DRONE)."""
    try:
        name = Path(log_file).stem
        if '_' in name:
            return name.split('_')[0].upper()
        return name.upper()
    except Exception:
        return 'UNKNOWN'


def _scan_system_logs_for_errors(since_timestamp: Optional[datetime], processed_hashes: Set[str]) -> List[Dict[str, Any]]:
    """
    Scan system logs for ERROR entries since timestamp.

    Returns list of error dicts with: branch, module, message, log_file, error_hash, timestamp
    """
    errors: List[Dict[str, Any]] = []

    if not SYSTEM_LOGS_DIR.exists():
        return errors

    cutoff = since_timestamp
    if cutoff is None:
        cutoff = datetime.now() - timedelta(hours=MAX_LOOKBACK_HOURS)

    for log_file in SYSTEM_LOGS_DIR.glob("*.log"):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    level = _detect_log_level(line)
                    if level != 'error':
                        continue

                    line_ts = _extract_timestamp(line)
                    if line_ts and line_ts < cutoff:
                        continue

                    module = _extract_module_name(line)
                    message = _parse_log_message(line)
                    error_hash = _generate_error_hash(module, message)

                    if error_hash in processed_hashes:
                        continue

                    branch = _detect_branch_from_log(str(log_file))

                    errors.append({
                        'branch': branch,
                        'module': module,
                        'message': message,
                        'log_file': str(log_file),
                        'error_hash': error_hash,
                        'timestamp': line_ts.isoformat() if line_ts else datetime.now().isoformat(),
                        'level': level
                    })

                    processed_hashes.add(error_hash)

        except Exception:
            continue

    return errors


def _run_error_catchup(fire_event: Optional[Callable[..., None]] = None) -> None:
    """
    Catch-up on errors missed while Trigger wasn't running.

    Args:
        fire_event: Callback to fire events (passed from module via kwargs)

    - Loads last_scan_timestamp from trigger_data.json
    - Scans system logs for ERROR entries since that time
    - Fires error_logged events for new errors via callback
    - Updates state with new timestamp and processed hashes
    """
    try:
        data = _load_trigger_data()
        catchup = data.get('error_catchup', {})

        last_scan = catchup.get('last_scan_timestamp')
        since_ts = None
        if last_scan:
            try:
                since_ts = datetime.fromisoformat(last_scan)
            except Exception:
                pass

        processed_hashes = set(catchup.get('processed_hashes', []))

        errors = _scan_system_logs_for_errors(since_ts, processed_hashes)

        if errors and fire_event is not None:
            for error in errors:
                fire_event('error_logged', **error)

        hash_list = list(processed_hashes)
        max_h = catchup.get('max_hashes', MAX_HASHES)
        if len(hash_list) > max_h:
            hash_list = hash_list[-max_h:]

        catchup['last_scan_timestamp'] = datetime.now().isoformat()
        catchup['processed_hashes'] = hash_list
        data['error_catchup'] = catchup

        _save_trigger_data(data)

    except Exception:
        pass


def handle_startup(**kwargs: Any) -> None:
    """
    Run startup checks - replaces Prax logger's hardcoded calls.

    Args:
        **kwargs: Event data, may include 'fire_event' callback
    """
    # Error catch-up (scan for missed errors)
    fire_event = kwargs.get('fire_event')
    _run_error_catchup(fire_event)

    # Schedule catch-up DISABLED for investigation
    # Was causing CPU spikes - needs debugging before re-enabling
    # import os
    # if os.environ.get('AIPASS_SPAWNED') != '1':
    #     try:
    #         import subprocess
    #         assistant_path = Path.home() / "aipass_os" / "dev_central" / "assistant"
    #         schedule_module = assistant_path / "apps" / "assistant.py"
    #         if schedule_module.exists():
    #             subprocess.run(
    #                 [sys.executable, str(schedule_module), "schedule", "run-due"],
    #                 cwd=str(assistant_path),
    #                 capture_output=True,
    #                 timeout=60
    #             )
    #     except Exception:
    #         pass

    # Memory Bank check (at /home/aipass/MEMORY_BANK - uppercase)
    try:
        from MEMORY_BANK.apps.handlers.monitor.memory_watcher import check_and_rollover  # type: ignore[import-not-found]
        check_and_rollover()
    except ImportError:
        pass  # Memory Bank not available
    except Exception:
        pass  # Silent failure - handlers cannot use logger or print
