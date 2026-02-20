#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""Tests for the execution engine (handlers/execution/)."""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Ensure Nexus root is on path
NEXUS_DIR = Path(__file__).resolve().parent.parent
if str(NEXUS_DIR) not in sys.path:
    sys.path.insert(0, str(NEXUS_DIR))


def test_execution_context_creation():
    """ExecutionContext initializes with persistent globals."""
    from handlers.execution.context import ExecutionContext

    ctx = ExecutionContext()
    assert ctx.globals is not None
    # Standard builtins should be preloaded
    assert "Path" in ctx.globals
    assert "os" in ctx.globals
    assert "json" in ctx.globals


def test_execution_context_execute():
    """ExecutionContext.execute() runs code and returns output."""
    from handlers.execution.context import ExecutionContext

    ctx = ExecutionContext()
    result = ctx.execute("print('hello from test')")
    assert result["success"] is True
    assert "hello from test" in result["output"]


def test_execution_context_persistence():
    """Variables persist across multiple executions."""
    from handlers.execution.context import ExecutionContext

    ctx = ExecutionContext()
    ctx.execute("test_var = 42")
    result = ctx.execute("print(test_var)")
    assert result["success"] is True
    assert "42" in result["output"]


def test_execution_context_error_handling():
    """ExecutionContext handles errors gracefully."""
    from handlers.execution.context import ExecutionContext

    ctx = ExecutionContext()
    result = ctx.execute("raise ValueError('test error')")
    assert result["success"] is False
    assert "test error" in result.get("error", "")


def test_intent_detection_execution():
    """detect_intent recognizes code execution requests."""
    from handlers.execution.intent import detect_intent

    result = detect_intent("run this python code for me")
    assert result["intent"] == "execution"
    assert result["confidence"] > 0


def test_intent_detection_file_op():
    """detect_intent recognizes file operation requests."""
    from handlers.execution.intent import detect_intent

    result = detect_intent("show me the files in this directory")
    assert result["intent"] in ("file_op", "execution", "data")


def test_intent_detection_chat():
    """detect_intent classifies normal chat correctly."""
    from handlers.execution.intent import detect_intent

    result = detect_intent("how are you doing today?")
    assert result["intent"] == "chat"


def test_extract_code_blocks():
    """extract_code_blocks finds Python code in text."""
    from handlers.execution.runner import extract_code_blocks

    text = "Here's some code:\n```python\nprint('hello')\n```\nThat's it."
    blocks = extract_code_blocks(text)
    assert len(blocks) >= 1
    assert "print('hello')" in blocks[0]


def test_extract_code_blocks_empty():
    """extract_code_blocks returns empty list for plain text."""
    from handlers.execution.runner import extract_code_blocks

    blocks = extract_code_blocks("Just regular text, no code here.")
    assert blocks == []


def test_context_stats():
    """ExecutionContext.get_stats() returns execution statistics."""
    from handlers.execution.context import ExecutionContext

    ctx = ExecutionContext()
    ctx.execute("x = 1")
    stats = ctx.get_stats()
    assert stats["total_operations"] >= 1
    assert "successful" in stats
