import json
from datetime import datetime
from pathlib import Path
import atexit

OUTLINE_LOG_PATH = Path(__file__).parent / "outline_log.json"

def log_outline_operation(file_path, outline_data=None, error=None, caller="user"):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "file_path": str(file_path),
        "success": error is None,
        "outline": outline_data if error is None else None,
        "error": str(error) if error else None,
        "caller": caller
    }
    if OUTLINE_LOG_PATH.exists():
        try:
            with open(OUTLINE_LOG_PATH, "r", encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            log = []
    else:
        log = []
    log.insert(0, entry)
    log = log[:100]  # Keep last 100 entries, newest first
    with open(OUTLINE_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

def clear_outline_log():
    with open(OUTLINE_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)

atexit.register(clear_outline_log)
