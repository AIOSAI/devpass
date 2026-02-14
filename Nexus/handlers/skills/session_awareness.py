#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""Session awareness skill - recent work context"""

import sys
from pathlib import Path
from typing import Optional

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

def handle_request(user_input: str) -> Optional[str]:
    """Handle session context queries

    Patterns:
    - "what happened last session" / "last session" → summary from previous
    - "session info" / "session context" → current session details
    """
    lower = user_input.lower().strip()

    if lower in ("last session", "what happened last session", "previous session"):
        from handlers.memory import load_summaries, get_last_session_messages
        summaries = load_summaries()
        if summaries:
            s = summaries[0]
            topics = ", ".join(s.get("key_topics", []))
            return f"Last session (tick {s['tick']}, {s['timestamp'][:10]}):\n{s['summary']}\nTopics: {topics}"

        # Fall back to chat history
        msgs = get_last_session_messages()
        if msgs:
            preview = "\n".join(f"- {m['role']}: {m['content'][:80]}..." for m in msgs[:5])
            return f"Last session messages:\n{preview}"

        return "No previous session data available."

    if lower in ("session info", "session context", "context"):
        from handlers.memory import get_pulse_data, get_session_count
        data = get_pulse_data()
        session_count = get_session_count()
        return (f"Current Session:\n"
                f"- Pulse tick: {data['current_tick']}\n"
                f"- Session #{data['total_sessions']}\n"
                f"- Started at tick: {data.get('session_start_tick', 'N/A')}\n"
                f"- Historical sessions: {session_count}")

    return None
