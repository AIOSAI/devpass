#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""Pulse counter for Nexus v2 - continues from tick 933"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "pulse.json"

def load_pulse_data() -> dict:
    """Load pulse data from disk; if missing/broken, initialize at tick 933."""
    if not DATA_PATH.exists():
        default = {
            "current_tick": 933,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "session_start_tick": None,
            "total_sessions": 0
        }
        save_pulse_data(default)
        return default

    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Corrupt file - reset to defaults
        default = {
            "current_tick": 933,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "session_start_tick": None,
            "total_sessions": 0
        }
        save_pulse_data(default)
        return default

def save_pulse_data(pulse_data: dict) -> None:
    """Save pulse data to disk."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(pulse_data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_tick() -> int:
    """Get current pulse tick."""
    return load_pulse_data()["current_tick"]

def increment_tick() -> int:
    """Increment pulse tick and update timestamp."""
    pulse_data = load_pulse_data()
    pulse_data["current_tick"] += 1
    pulse_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_pulse_data(pulse_data)
    return pulse_data["current_tick"]

def get_pulse_data() -> dict:
    """Get full pulse data dictionary."""
    return load_pulse_data()

def start_session() -> dict:
    """Start a new session - set session_start_tick and increment total_sessions."""
    pulse_data = load_pulse_data()
    pulse_data["session_start_tick"] = pulse_data["current_tick"]
    pulse_data["total_sessions"] += 1
    pulse_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_pulse_data(pulse_data)
    return pulse_data

def end_session() -> dict:
    """End current session - just saves current state."""
    pulse_data = load_pulse_data()
    pulse_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_pulse_data(pulse_data)
    return pulse_data
