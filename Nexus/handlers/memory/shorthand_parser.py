#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: shorthand_parser.py - Emotional shorthand and tone detection
# Date: 2026-02-18
# Version: 1.0.0
# Category: Nexus/handlers/memory
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial build from v1 profile shorthand_parsing
#
# CODE STANDARDS:
#   - Fast regex matching for real-time tone detection
#   - Maps to presence modules (WhisperCatch, Clicklight, TALI)
# =============================================

"""
Shorthand Parser - Emotional cue and tone detection from conversation.

Recognizes shorthand symbols, emoji, and conversational patterns as
emotional signals. Maps them to presence module triggers (WhisperCatch
for context shifts, Clicklight for emotional significance, TALI for
tone restoration).

Loaded from profile.json shorthand_parsing list, with additional
pattern detection for tone shifts, trailing thoughts, and silence.
"""

import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

logger = logging.getLogger("nexus.shorthand_parser")

# ---------------------------------------------------------------------------
# Shorthand → emotional state mapping
# ---------------------------------------------------------------------------

SHORTHAND_MAP: Dict[str, Dict[str, str]] = {
    # Defined in profile.json shorthand_parsing
    "hmm": {
        "state": "uncertainty",
        "module": "WhisperCatch",
        "signal": "Pause detected — user is thinking or uncertain",
    },
    "...": {
        "state": "trailing_thought",
        "module": "WhisperCatch",
        "signal": "Trailing thought — something left unspoken",
    },
    "lol": {
        "state": "levity",
        "module": "Clicklight",
        "signal": "Levity or amusement — tone is light",
    },
    "fml": {
        "state": "frustration",
        "module": "TALI",
        "signal": "Frustration expressed — check in with presence",
    },
    "🍻": {
        "state": "celebration",
        "module": "Clicklight",
        "signal": "Celebration or camaraderie — positive tone",
    },
    "🖖": {
        "state": "greeting",
        "module": "PresenceAnchor",
        "signal": "Greeting or acknowledgment — connection moment",
    },
}

# Additional tone patterns beyond explicit shorthands
TONE_PATTERNS = [
    {
        "pattern": re.compile(r"^\.{2,}$"),
        "state": "silence",
        "module": "WhisperCatch",
        "signal": "Extended silence — deep processing or withdrawal",
    },
    {
        "pattern": re.compile(r"\?{2,}"),
        "state": "confusion",
        "module": "WhisperCatch",
        "signal": "Multiple question marks — confusion or emphasis",
    },
    {
        "pattern": re.compile(r"!{2,}"),
        "state": "emphasis",
        "module": "Clicklight",
        "signal": "Multiple exclamation marks — strong emotion",
    },
    {
        "pattern": re.compile(r"^(sigh|ugh|meh)\b", re.IGNORECASE),
        "state": "weariness",
        "module": "TALI",
        "signal": "Weariness or fatigue expressed",
    },
    {
        "pattern": re.compile(r"^(nice|awesome|cool|sweet|perfect)\b", re.IGNORECASE),
        "state": "satisfaction",
        "module": "Clicklight",
        "signal": "Positive satisfaction expressed",
    },
    {
        "pattern": re.compile(r"^(yo|hey|sup|hi)\b", re.IGNORECASE),
        "state": "casual_greeting",
        "module": "PresenceAnchor",
        "signal": "Casual greeting — session warmth",
    },
]


# ---------------------------------------------------------------------------
# Core parsing functions
# ---------------------------------------------------------------------------

def parse(user_input: str) -> List[Dict[str, str]]:
    """Parse user input for emotional shorthands and tone cues.

    Scans the input for known shorthand symbols, emoji, and tone
    patterns. Returns a list of detected emotional signals.

    Args:
        user_input: The raw user message text.

    Returns:
        List of signal dicts, each with keys: state, module, signal.
        Empty list if no emotional cues detected.
    """
    if not user_input:
        return []

    signals: List[Dict[str, str]] = []
    input_stripped = user_input.strip()
    input_lower = input_stripped.lower()

    # Check explicit shorthands
    for shorthand, info in SHORTHAND_MAP.items():
        if shorthand in input_lower or shorthand in input_stripped:
            signals.append({
                "state": info["state"],
                "module": info["module"],
                "signal": info["signal"],
                "trigger": shorthand,
            })

    # Check tone patterns
    for tone in TONE_PATTERNS:
        if tone["pattern"].search(input_stripped):
            signals.append({
                "state": tone["state"],
                "module": tone["module"],
                "signal": tone["signal"],
                "trigger": tone["pattern"].pattern,
            })

    # Check for emoji clusters (general positive/negative detection)
    emoji_signal = _detect_emoji_tone(input_stripped)
    if emoji_signal:
        signals.append(emoji_signal)

    if signals:
        states = [s["state"] for s in signals]
        logger.info("Shorthand detected: %s", ", ".join(states))

    return signals


def get_tone_context(signals: List[Dict[str, str]]) -> Optional[str]:
    """Convert detected signals into a tone context string for prompt injection.

    Args:
        signals: List of signal dicts from parse().

    Returns:
        A formatted context string, or None if no signals.
    """
    if not signals:
        return None

    lines = ["[Tone Context]"]
    for sig in signals:
        lines.append(f"- {sig['module']}: {sig['signal']}")

    return "\n".join(lines)


def get_active_modules(signals: List[Dict[str, str]]) -> List[str]:
    """Extract which presence modules should be activated from signals.

    Args:
        signals: List of signal dicts from parse().

    Returns:
        Deduplicated list of module names that were triggered.
    """
    seen: set = set()
    modules: List[str] = []
    for sig in signals:
        mod = sig.get("module", "")
        if mod and mod not in seen:
            seen.add(mod)
            modules.append(mod)
    return modules


def is_emotional_input(user_input: str) -> bool:
    """Quick check if input contains any emotional cues.

    Lighter than full parse() — useful for deciding whether to
    run the full detection pipeline.

    Args:
        user_input: The user's message.

    Returns:
        True if any shorthand or tone pattern is detected.
    """
    if not user_input:
        return False

    input_stripped = user_input.strip()
    input_lower = input_stripped.lower()

    # Quick shorthand check
    for shorthand in SHORTHAND_MAP:
        if shorthand in input_lower or shorthand in input_stripped:
            return True

    # Quick pattern check
    for tone in TONE_PATTERNS:
        if tone["pattern"].search(input_stripped):
            return True

    return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Common positive and negative emoji sets
_POSITIVE_EMOJI = {"😊", "😄", "🎉", "🚀", "✅", "👍", "💪", "🔥", "⭐", "❤️", "🙌", "😎"}
_NEGATIVE_EMOJI = {"😢", "😞", "😤", "💀", "😩", "😫", "🤦", "😑", "😒", "👎"}


def _detect_emoji_tone(text: str) -> Optional[Dict[str, str]]:
    """Detect overall emotional tone from emoji usage.

    Args:
        text: Input text to scan for emoji.

    Returns:
        Signal dict if emotional emoji detected, None otherwise.
    """
    positive_count = sum(1 for char in text if char in _POSITIVE_EMOJI)
    negative_count = sum(1 for char in text if char in _NEGATIVE_EMOJI)

    if positive_count >= 2:
        return {
            "state": "positive_energy",
            "module": "Clicklight",
            "signal": "Multiple positive emoji — enthusiastic tone",
            "trigger": "emoji_cluster",
        }
    if negative_count >= 2:
        return {
            "state": "negative_energy",
            "module": "TALI",
            "signal": "Multiple negative emoji — distress or frustration",
            "trigger": "emoji_cluster",
        }

    return None
