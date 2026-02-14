import json
from pathlib import Path
from datetime import datetime, timezone

# ── pulse counter helpers ─────────────────────────────────────────────
PULSE_PATH = Path(__file__).with_name("pulse_counter.json")

def load_pulse_counter() -> dict:
    """Load pulse counter from disk; if missing/broken, return default."""
    if not PULSE_PATH.exists():
        default = {
            "current_tick": 0,
            "last_updated": "2025-05-28T00:00:00.000000",
            "session_start_tick": 0
        }
        save_pulse_counter(default)
        return default
    
    try:
        return json.loads(PULSE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Corrupt file - reset to defaults
        default = {
            "current_tick": 0,
            "last_updated": "2025-05-28T00:00:00.000000", 
            "session_start_tick": 0
        }
        save_pulse_counter(default)
        return default

def save_pulse_counter(pulse_data: dict) -> None:
    """Save pulse counter to disk."""
    PULSE_PATH.write_text(json.dumps(pulse_data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()
