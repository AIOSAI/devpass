#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""Memory operations skill - search, recall, learn"""

import sys
from pathlib import Path
from typing import Optional

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

def handle_request(user_input: str) -> Optional[str]:
    """Handle memory-related commands

    Patterns:
    - "remember that ..." / "learn: ..." → add to knowledge base
    - "what do you know about ..." / "recall ..." → search knowledge base
    - "pulse" / "tick" → show current pulse tick
    - "memory status" → show all memory stats
    """
    lower = user_input.lower().strip()

    # Remember/Learn pattern
    if lower.startswith(("remember that ", "learn: ", "remember: ")):
        text = user_input.split(" ", 2)[-1] if "that" in lower else user_input.split(": ", 1)[-1]
        from handlers.memory import add_entry, load_knowledge
        add_entry(text, source="user")
        count = len(load_knowledge())
        return f"Learned. Knowledge base now has {count} entries."

    # Recall/Search pattern
    if lower.startswith(("what do you know about ", "recall ", "search memory ")):
        query = user_input.split(" ", 4)[-1] if "about" in lower else user_input.split(" ", 1)[-1]
        from handlers.memory import search_knowledge
        results = search_knowledge(query)
        if results:
            formatted = "\n".join(f"- {r['text']}" for r in results[:5])
            return f"Found {len(results)} matches:\n{formatted}"
        return f"No knowledge found matching '{query}'."

    # Pulse/tick status
    if lower in ("pulse", "tick", "what tick", "current tick"):
        from handlers.memory import get_pulse_data
        data = get_pulse_data()
        return f"Pulse tick: {data['current_tick']} | Sessions: {data['total_sessions']} | Last: {data['last_updated']}"

    # Memory status
    if lower in ("memory status", "memory stats", "mem status"):
        from handlers.memory import get_tick, load_knowledge, get_memory_count, load_summaries
        kb_count = len(load_knowledge())
        vec_count = get_memory_count()
        sum_count = len(load_summaries())
        tick = get_tick()
        return (f"Memory Status:\n"
                f"- Pulse tick: {tick}\n"
                f"- Knowledge entries: {kb_count}\n"
                f"- Vector memories: {vec_count}\n"
                f"- Session summaries: {sum_count}")

    return None  # Not handled
