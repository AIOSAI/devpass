import json
from pathlib import Path
from datetime import datetime

TRACE_LOG = Path(__file__).parent / "trace_log.json"

def log_trace_operation(file_path, trace_data=None, error=None, caller=None):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "file_path": file_path,
        "success": error is None,
        "trace": trace_data if trace_data is not None else None,
        "error": str(error) if error else None,
        "caller": caller,
    }
    try:
        if TRACE_LOG.exists():
            with open(TRACE_LOG, "r", encoding="utf-8") as f:
                log = json.load(f)
        else:
            log = []
        log.insert(0, entry)  # newest first
        # Limit to 50 entries to avoid bloat
        log = log[:50]
        with open(TRACE_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)
    except Exception as e:
        print(f"[trace_log] Logging error: {e}")

def clear_trace_log():
    try:
        if TRACE_LOG.exists():
            with open(TRACE_LOG, "w", encoding="utf-8") as f:
                json.dump([], f)
    except Exception as e:
        print(f"[trace_log] Clear log error: {e}")
