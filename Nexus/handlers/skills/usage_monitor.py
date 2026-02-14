#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""Usage monitoring skill - track API usage per session"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "usage_log.json"
MAX_ENTRIES = 50

# Session-level tracking (mutable state)
SESSION_STATS = {
    "requests": 0,
    "session_start": datetime.now(timezone.utc).isoformat()
}

def _load_log():
    if DATA_PATH.exists():
        try:
            return json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return []
    return []

def _save_log(log):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(log[:MAX_ENTRIES], ensure_ascii=False, indent=2), encoding="utf-8")

def log_request():
    """Log an API request (called externally)"""
    SESSION_STATS["requests"] += 1

def save_session_usage():
    """Save session usage to log (called on session end)"""
    log = _load_log()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_start": SESSION_STATS["session_start"],
        "requests": SESSION_STATS["requests"]
    }
    log.insert(0, entry)
    _save_log(log)

def handle_request(user_input: str) -> Optional[str]:
    """Handle usage queries

    Patterns:
    - "usage" / "api usage" → show session and historical usage
    """
    lower = user_input.lower().strip()

    if lower in ("usage", "api usage", "usage stats", "token usage"):
        log = _load_log()
        recent = log[:5] if log else []

        lines = [f"Session: {SESSION_STATS['requests']} API requests"]
        if recent:
            lines.append(f"Recent sessions ({len(log)} total):")
            for entry in recent:
                lines.append(f"  - {entry['timestamp'][:10]}: {entry['requests']} requests")

        return "\n".join(lines)

    return None
