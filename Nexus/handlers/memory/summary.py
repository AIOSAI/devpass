#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""Session summary storage for Nexus v2 - rollover pattern"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "session_summaries.json"
MAX_SUMMARIES = 10

def load_summaries() -> list:
    """Load summaries from file."""
    if not DATA_PATH.exists() or DATA_PATH.stat().st_size == 0:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        DATA_PATH.write_text("[]", encoding="utf-8")
        return []
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        DATA_PATH.write_text("[]", encoding="utf-8")
        return []

def save_summary(summary_text: str, session_tick: int, key_topics: List[str] = None) -> None:
    """Save a session summary with tick and topics."""
    summaries = load_summaries()

    summary_entry = {
        "tick": session_tick,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": summary_text,
        "key_topics": key_topics if key_topics else []
    }

    summaries.insert(0, summary_entry)

    # Rolloff: keep only last MAX_SUMMARIES
    summaries = summaries[:MAX_SUMMARIES]

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")

def get_context_summary(n: int = 3) -> str:
    """Get combined text from last N summaries for system prompt injection."""
    summaries = load_summaries()
    recent_summaries = summaries[:n]

    if not recent_summaries:
        return ""

    context_parts = []
    for summary in recent_summaries:
        tick = summary.get("tick", "unknown")
        text = summary.get("summary", "")
        topics = summary.get("key_topics", [])

        summary_block = f"Session {tick}: {text}"
        if topics:
            summary_block += f" [Topics: {', '.join(topics)}]"

        context_parts.append(summary_block)

    return "\n".join(context_parts)
