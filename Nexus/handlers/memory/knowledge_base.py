#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""Knowledge base for Nexus v2 - upgraded to 200 entries"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge_base.json"
MAX_ENTRIES = 200

def _init_file() -> None:
    """Ensure the knowledge file exists."""
    if not DATA_PATH.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        DATA_PATH.write_text("[]", encoding="utf-8")

def load_knowledge() -> list:
    """Load knowledge entries from disk."""
    _init_file()
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        DATA_PATH.write_text("[]", encoding="utf-8")
        return []

def save_knowledge(entries: list) -> None:
    """Persist knowledge entries to disk."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )

def add_entry(text: str, source: str = "auto") -> None:
    """Add a new knowledge entry with timestamp and source."""
    entries = load_knowledge()
    timestamp = datetime.now(timezone.utc).isoformat()
    entries.insert(0, {
        "timestamp": timestamp,
        "text": text,
        "source": source
    })
    if len(entries) > MAX_ENTRIES:
        entries = entries[:MAX_ENTRIES]
    save_knowledge(entries)

def search_knowledge(query: str) -> list:
    """Search knowledge entries (case-insensitive substring matching)."""
    entries = load_knowledge()
    query_lower = query.lower()
    return [
        entry for entry in entries
        if query_lower in entry.get("text", "").lower()
    ]

def get_recent(n: int = 10) -> list:
    """Get N most recent knowledge entries."""
    entries = load_knowledge()
    return entries[:n]
