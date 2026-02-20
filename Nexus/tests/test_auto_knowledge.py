#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""Tests for auto-knowledge extraction and shorthand parsing."""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

NEXUS_DIR = Path(__file__).resolve().parent.parent
if str(NEXUS_DIR) not in sys.path:
    sys.path.insert(0, str(NEXUS_DIR))


# --- Auto-knowledge tests ---

def test_is_worth_storing_accepts_facts():
    """_is_worth_storing accepts meaningful facts."""
    from handlers.memory.auto_knowledge import _is_worth_storing

    assert _is_worth_storing("AIPass uses a branch-based architecture") is True
    assert _is_worth_storing("Nexus is the conversational AI module") is True
    assert _is_worth_storing("Python requires indentation for blocks") is True


def test_is_worth_storing_rejects_trivial():
    """_is_worth_storing rejects trivial content."""
    from handlers.memory.auto_knowledge import _is_worth_storing

    assert _is_worth_storing("") is False
    assert _is_worth_storing("ok") is False
    assert _is_worth_storing("thanks") is False
    assert _is_worth_storing("maybe something?") is False  # question
    assert _is_worth_storing("hi") is False  # too short
    assert _is_worth_storing("good point about that") is False  # skip phrase


def test_detect_learn_command():
    """detect_learn_command recognizes explicit learn requests."""
    from handlers.memory.auto_knowledge import detect_learn_command

    assert detect_learn_command("remember that Python is great") is not None
    assert detect_learn_command("learn: AIPass uses branches") is not None
    assert detect_learn_command("note: deployment is on Ubuntu") is not None
    assert detect_learn_command("how are you?") is None


def test_detect_memory_search():
    """detect_memory_search recognizes recall intent."""
    from handlers.memory.auto_knowledge import detect_memory_search

    is_search, query = detect_memory_search("do you remember when we set up cortex?")
    assert is_search is True
    assert len(query) > 0

    is_search, query = detect_memory_search("what's the weather like?")
    assert is_search is False


def test_guidance_pattern_detection():
    """Auto-detection catches user guidance patterns."""
    from handlers.memory.auto_knowledge import GUIDANCE_PATTERNS
    import re

    # "Actually" pattern
    match = GUIDANCE_PATTERNS[0].search("Actually, we should use Python 3.14")
    assert match is not None

    # "FYI" pattern
    match = GUIDANCE_PATTERNS[3].search("FYI: the server runs on port 8080")
    assert match is not None


def test_learning_pattern_detection():
    """Auto-detection catches Nexus learning patterns."""
    from handlers.memory.auto_knowledge import LEARNING_PATTERNS

    match = LEARNING_PATTERNS[0].search("I learned that AIPass uses memory files")
    assert match is not None

    match = LEARNING_PATTERNS[1].search("Now I understand that cortex watches files")
    assert match is not None


# --- Shorthand parser tests ---

def test_shorthand_parse_detects_hmm():
    """Parser detects 'hmm' as uncertainty."""
    from handlers.memory.shorthand_parser import parse

    signals = parse("hmm")
    assert len(signals) > 0
    assert any(s["state"] == "uncertainty" for s in signals)


def test_shorthand_parse_detects_ellipsis():
    """Parser detects '...' as trailing thought."""
    from handlers.memory.shorthand_parser import parse

    signals = parse("...")
    assert len(signals) > 0
    assert any(s["state"] == "trailing_thought" for s in signals)


def test_shorthand_parse_detects_frustration():
    """Parser detects 'fml' as frustration."""
    from handlers.memory.shorthand_parser import parse

    signals = parse("fml this is broken")
    assert any(s["state"] == "frustration" for s in signals)


def test_shorthand_parse_empty():
    """Parser returns empty list for plain input."""
    from handlers.memory.shorthand_parser import parse

    signals = parse("Can you help me write a function?")
    assert signals == []


def test_tone_context_format():
    """get_tone_context formats signals correctly."""
    from handlers.memory.shorthand_parser import parse, get_tone_context

    signals = parse("hmm")
    context = get_tone_context(signals)
    assert context is not None
    assert "[Tone Context]" in context
    assert "WhisperCatch" in context


def test_tone_context_none_for_empty():
    """get_tone_context returns None when no signals."""
    from handlers.memory.shorthand_parser import get_tone_context

    assert get_tone_context([]) is None


def test_is_emotional_input():
    """is_emotional_input quickly checks for emotional cues."""
    from handlers.memory.shorthand_parser import is_emotional_input

    assert is_emotional_input("hmm let me think") is True
    assert is_emotional_input("fml") is True
    assert is_emotional_input("Can you write a function?") is False


def test_get_active_modules():
    """get_active_modules extracts triggered module names."""
    from handlers.memory.shorthand_parser import parse, get_active_modules

    signals = parse("hmm...")
    modules = get_active_modules(signals)
    assert "WhisperCatch" in modules
