#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Memory handlers for Nexus v2"""

from .chat_history import load_history, save_session, get_last_session_messages, get_session_count
from .summary import load_summaries, save_summary, get_context_summary
from .pulse_manager import (
    get_tick, increment_tick, get_pulse_data,
    start_session, end_session
)
from .knowledge_base import (
    load_knowledge, add_entry, search_knowledge, get_recent
)
from .vector_memory import (
    store_memory, search_memories, get_memory_count
)
from .auto_knowledge import (
    detect_and_store, detect_learn_command, detect_memory_search
)
from .shorthand_parser import (
    parse as parse_shorthand, get_tone_context, is_emotional_input
)

__all__ = [
    # Chat history
    'load_history',
    'save_session',
    'get_last_session_messages',
    'get_session_count',

    # Summaries
    'load_summaries',
    'save_summary',
    'get_context_summary',

    # Pulse manager
    'get_tick',
    'increment_tick',
    'get_pulse_data',
    'start_session',
    'end_session',

    # Knowledge base
    'load_knowledge',
    'add_entry',
    'search_knowledge',
    'get_recent',

    # Vector memory
    'store_memory',
    'search_memories',
    'get_memory_count',

    # Auto-knowledge extraction
    'detect_and_store',
    'detect_learn_command',
    'detect_memory_search',

    # Shorthand parsing
    'parse_shorthand',
    'get_tone_context',
    'is_emotional_input',
]
