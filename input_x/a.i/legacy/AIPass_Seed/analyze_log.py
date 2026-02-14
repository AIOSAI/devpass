import json
from pathlib import Path
from datetime import datetime

ANALYZE_LOG = Path(__file__).parent / "analyze_log.json"


def log_analyze_operation(file_path, analysis_data=None, error=None, caller=None):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "file_path": file_path,
        "success": error is None,
        "analysis": analysis_data if analysis_data is not None else None,
        "error": str(error) if error else None,
        "caller": caller,
    }
    try:
        if ANALYZE_LOG.exists():
            with open(ANALYZE_LOG, "r", encoding="utf-8") as f:
                log = json.load(f)
        else:
            log = []
        log.insert(0, entry)  # newest first
        # Limit to 50 entries to avoid bloat
        log = log[:50]
        with open(ANALYZE_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)
    except Exception as e:
        print(f"[analyze_log] Logging error: {e}")

def clear_analyze_log():
    try:
        if ANALYZE_LOG.exists():
            with open(ANALYZE_LOG, "w", encoding="utf-8") as f:
                json.dump([], f)
    except Exception as e:
        print(f"[analyze_log] Clear log error: {e}")
