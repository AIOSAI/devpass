#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""
META:
  app: Nexus
  layer: handlers/cortex
  purpose: Cortex file awareness system - real-time workspace monitoring
  status: Active

Cortex gives Nexus awareness of its own workspace. It watches for file
changes (creates, modifications, deletions) and maintains persistent
summaries that get injected into the system prompt.

Rebuilt from v1's monolithic cortex_module.py (354 lines) into clean
separated handlers: watcher.py (event detection) and summarizer.py
(state persistence and summarization).

Usage from nexus.py::

    from handlers.cortex import (
        CortexFileWatcher,
        get_cortex_block,
        refresh_summary,
        reset_session_counters,
    )

    # Start watching
    watcher = CortexFileWatcher()
    watcher.start()

    # Get awareness block for system prompt
    block = get_cortex_block()

    # On session start
    reset_session_counters()
"""

from handlers.cortex.watcher import (
    CortexFileWatcher,
    WATCHDOG_AVAILABLE,
)
from handlers.cortex.summarizer import (
    load_cortex_data,
    save_cortex_data,
    refresh_summary,
    batch_refresh,
    get_cortex_block,
    reset_session_counters,
)

__all__ = [
    # Watcher
    "CortexFileWatcher",
    "WATCHDOG_AVAILABLE",

    # Summarizer
    "load_cortex_data",
    "save_cortex_data",
    "refresh_summary",
    "batch_refresh",
    "get_cortex_block",
    "reset_session_counters",
]
