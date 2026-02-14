from pathlib import Path
import json
from datetime import datetime, timezone

# File path for persistent knowledge base
KNOWLEDGE_PATH = Path(__file__).with_name("knowledge_base.json")

# Maximum stored entries
MAX_ENTRIES = 100


def _init_file() -> None:
    """Ensure the knowledge file exists."""
    if not KNOWLEDGE_PATH.exists():
        KNOWLEDGE_PATH.write_text("[]", encoding="utf-8")


def load_knowledge() -> list:
    """Load knowledge entries from disk."""
    _init_file()
    try:
        return json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        KNOWLEDGE_PATH.write_text("[]", encoding="utf-8")
        return []


def save_knowledge(entries: list) -> None:
    """Persist knowledge entries to disk."""
    KNOWLEDGE_PATH.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def add_entry(text: str) -> None:
    """Add a new knowledge entry with timestamp."""
    entries = load_knowledge()
    timestamp = datetime.now(timezone.utc).isoformat()
    entries.insert(0, {"timestamp": timestamp, "text": text})
    if len(entries) > MAX_ENTRIES:
        entries = entries[:MAX_ENTRIES]
    save_knowledge(entries)
