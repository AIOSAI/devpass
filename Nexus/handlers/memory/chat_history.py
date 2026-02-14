#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chat history persistence for Nexus v2"""

import json
from pathlib import Path
from datetime import datetime, timezone

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "chat_history.json"
MAX_SESSIONS = 5  # Keep last 5 sessions

def load_history() -> list:
    """Load all sessions from chat history"""
    if not DATA_PATH.exists() or DATA_PATH.stat().st_size == 0:
        DATA_PATH.write_text("[]", encoding="utf-8")
        return []
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        # Handle legacy dict format with "sessions" key
        if isinstance(data, dict):
            return data.get("sessions", [])
        # Handle new list format
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        DATA_PATH.write_text("[]", encoding="utf-8")
        return []

def save_session(messages: list) -> None:
    """Save current session to history"""
    if not messages:
        return

    history = load_history()

    # Create session object
    session = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "messages": messages
    }

    # Add to front of history
    history.insert(0, session)

    # Rolloff: keep only last N sessions
    history = history[:MAX_SESSIONS]

    # Save
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

def get_last_session_messages() -> list:
    """Get messages from last session for context"""
    history = load_history()
    if history and len(history) > 0:
        return history[0].get("messages", [])
    return []

def get_session_count() -> int:
    """Return number of stored sessions"""
    return len(load_history())
