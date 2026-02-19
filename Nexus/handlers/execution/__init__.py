#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""
META:
  app: Nexus
  layer: handlers
  purpose: Natural Flow execution engine package
  status: Active

Nexus Natural Flow execution engine.

Provides the persistent Python execution environment, natural-language
intent detection, and code extraction / running pipeline.

Usage from nexus.py::

    from handlers.execution import (
        ExecutionContext,
        detect_intent,
        extract_code_blocks,
        run_code,
    )

    ctx = ExecutionContext()
    intent = detect_intent(user_input)
    blocks = extract_code_blocks(llm_response)
    result = run_code(blocks[0], ctx)
"""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from handlers.execution.context import ExecutionContext
from handlers.execution.intent import detect_intent
from handlers.execution.runner import extract_code_blocks, run_code, handle_execution_request

__all__ = [
    "ExecutionContext",
    "detect_intent",
    "extract_code_blocks",
    "run_code",
    "handle_execution_request",
]
