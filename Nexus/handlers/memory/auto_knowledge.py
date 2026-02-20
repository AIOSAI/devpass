#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: auto_knowledge.py - Autonomous knowledge extraction from conversation
# Date: 2026-02-18
# Version: 1.0.0
# Category: Nexus/handlers/memory
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial build from v1 nexus.py auto-learn patterns
#
# CODE STANDARDS:
#   - Regex-based detection for sub-100ms processing
#   - Source tagging for knowledge provenance
#   - Conservative filtering: better to miss than to store noise
# =============================================

"""
Auto-Knowledge Extraction - Learn facts from conversation automatically.

Scans both user input and Nexus responses for learnable content:
- Learning patterns: When Nexus articulates new understanding
- Guidance patterns: When user corrects or provides direction
- Fact patterns: When user explicitly marks important info
- Memory search: Detects recall intent ("remember when...")

Integrates with knowledge_base.add_entry() for storage.
"""

import sys
import re
import logging
from pathlib import Path
from typing import Optional, Tuple, List

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

logger = logging.getLogger("nexus.auto_knowledge")

# ---------------------------------------------------------------------------
# Pattern definitions (from v1 nexus.py lines 164-220)
# ---------------------------------------------------------------------------

# Patterns that detect Nexus learning something (matched against responses)
LEARNING_PATTERNS = [
    re.compile(r"I (?:learned|discovered|found out|noticed) (?:that )?(.+?)(?:\.|$)", re.IGNORECASE),
    re.compile(r"(?:Now I understand|I now know|I see) (?:that )?(.+?)(?:\.|$)", re.IGNORECASE),
    re.compile(r"(?:This means|This tells me|This shows) (?:that )?(.+?)(?:\.|$)", re.IGNORECASE),
    re.compile(r"(?:I realize|I gather|It seems) (?:that )?(.+?)(?:\.|$)", re.IGNORECASE),
]

# Patterns that detect user corrections/guidance (matched against user input)
GUIDANCE_PATTERNS = [
    re.compile(r"^Actually,?\s*(.+?)(?:\.|!|$)", re.IGNORECASE),
    re.compile(r"^No,?\s*(.+?)(?:\.|!|$)", re.IGNORECASE),
    re.compile(r"^Guidance[:\-]\s*(.+?)(?:\.|!|$)", re.IGNORECASE),
    re.compile(r"^FYI[:\-]\s*(.+?)(?:\.|!|$)", re.IGNORECASE),
    re.compile(r"^For reference[:\-]\s*(.+?)(?:\.|!|$)", re.IGNORECASE),
]

# Patterns that detect explicit fact markers (matched against user input)
FACT_PATTERNS = [
    re.compile(r"^Important:\s*(.+)", re.IGNORECASE),
    re.compile(r"^Note:\s*(.+)", re.IGNORECASE),
    re.compile(r"^Key point:\s*(.+)", re.IGNORECASE),
    re.compile(r"^Remember this:\s*(.+)", re.IGNORECASE),
    re.compile(r"^For future reference:\s*(.+)", re.IGNORECASE),
]

# Explicit learn commands (matched against user input)
LEARN_COMMAND_PATTERNS = [
    re.compile(r"^(?:nexus,?\s*)?(?:please\s+)?(remember|note|learn|store)[:\s]+(.+)", re.IGNORECASE),
    re.compile(r"^(store fact|save info|add fact)[:\s]+(.+)", re.IGNORECASE),
    re.compile(r"^(remember|note|learn|store)\s+(?:this|that)[:\s]+(.+)", re.IGNORECASE),
    re.compile(r"^add knowledge:\s*(.+)", re.IGNORECASE),
]

# Memory search triggers (matched against user input)
MEMORY_SEARCH_TRIGGERS = [
    "remember when", "recall when", "do you remember",
    "we discussed", "we talked about", "we were chatting about",
    "last week we", "remember last", "what did we decide",
    "we covered", "remember our conversation", "remember that time",
    "didn't we talk about",
]

# Phrases that indicate content NOT worth storing
SKIP_PHRASES = [
    "i don't know", "i'm not sure", "maybe", "that's interesting",
    "good point", "thanks", "thank you", "ok", "okay", "sure",
    "got it", "i see", "right", "hmm", "huh", "yeah", "yep",
    "nah", "nope", "well", "so",
]

# Words that indicate meaningful content
MEANINGFUL_INDICATORS = {
    "is", "are", "was", "were", "has", "have", "can", "will",
    "should", "uses", "works", "means", "helps", "allows",
    "enables", "requires", "needs", "provides", "creates",
    "builds", "runs", "handles", "manages", "stores",
}


# ---------------------------------------------------------------------------
# Core detection functions
# ---------------------------------------------------------------------------

def detect_and_store(user_input: str, response_text: str) -> List[str]:
    """Scan conversation turn for learnable content and store it.

    Processes both user input (guidance, facts, commands) and Nexus
    response (learning patterns). Returns list of stored facts.

    Args:
        user_input:    The user's message text.
        response_text: Nexus's response text.

    Returns:
        List of fact strings that were stored. Empty if nothing learned.
    """
    stored = []

    # Check user input for explicit learn commands first
    command_fact = _detect_learn_command(user_input)
    if command_fact:
        _store_fact(command_fact, "[User] Explicit learn command")
        stored.append(command_fact)
        return stored  # Explicit command takes priority, skip auto-detection

    # Check user input for guidance patterns
    for pattern in GUIDANCE_PATTERNS:
        match = pattern.search(user_input)
        if match:
            fact = match.group(1).strip()
            if _is_worth_storing(fact):
                _store_fact(fact, "[Auto] User guidance")
                stored.append(fact)

    # Check user input for fact patterns
    for pattern in FACT_PATTERNS:
        match = pattern.search(user_input)
        if match:
            fact = match.group(1).strip()
            if _is_worth_storing(fact):
                _store_fact(fact, "[Auto] Important fact")
                stored.append(fact)

    # Check response for learning patterns
    for pattern in LEARNING_PATTERNS:
        match = pattern.search(response_text)
        if match:
            fact = match.group(1).strip()
            if _is_worth_storing(fact):
                _store_fact(fact, "[Auto] Nexus learned")
                stored.append(fact)

    if stored:
        logger.info("Auto-knowledge: stored %d fact(s) from conversation", len(stored))

    return stored


def detect_learn_command(user_input: str) -> Optional[str]:
    """Check if user input is an explicit learn/remember command.

    Args:
        user_input: The user's message.

    Returns:
        The fact to store, or None if not a learn command.
    """
    return _detect_learn_command(user_input)


def detect_memory_search(user_input: str) -> Tuple[bool, str]:
    """Detect if user is trying to recall a past memory.

    Args:
        user_input: The user's message.

    Returns:
        Tuple of (is_memory_search, search_query). Query is empty
        string if not a memory search.
    """
    input_lower = user_input.lower()
    for trigger in MEMORY_SEARCH_TRIGGERS:
        if trigger in input_lower:
            # Extract the search query after the trigger phrase
            idx = input_lower.index(trigger) + len(trigger)
            query = user_input[idx:].strip().strip("?.,!").strip()
            if query:
                return True, query
            # If no query after trigger, use everything before as fallback
            before = user_input[:input_lower.index(trigger)].strip()
            return True, before if before else trigger

    return False, ""


# ---------------------------------------------------------------------------
# Filtering - conservative: better to miss than to store noise
# ---------------------------------------------------------------------------

def _is_worth_storing(fact: str) -> bool:
    """Determine if a detected fact is worth persisting.

    Applies multiple filters to avoid storing trivial, ambiguous,
    or noisy content. Conservative by design.

    Args:
        fact: The extracted fact text.

    Returns:
        True if the fact passes all quality filters.
    """
    if not fact or len(fact) < 2:
        return False

    fact_lower = fact.lower().strip()

    # Skip trivial phrases
    for skip in SKIP_PHRASES:
        if fact_lower.startswith(skip):
            return False

    # Skip questions
    if fact.rstrip().endswith("?"):
        return False

    # Must have at least 3 words
    words = fact_lower.split()
    if len(words) < 3:
        return False

    # Must contain at least one meaningful indicator
    word_set = set(words)
    if not word_set.intersection(MEANINGFUL_INDICATORS):
        return False

    return True


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_learn_command(user_input: str) -> Optional[str]:
    """Check for explicit learn/remember commands in user input."""
    for pattern in LEARN_COMMAND_PATTERNS:
        match = pattern.search(user_input)
        if match:
            # Last group contains the fact content
            fact = match.group(match.lastindex or 1).strip()
            if fact and len(fact) > 2:
                return fact
    return None


def _store_fact(fact: str, source: str) -> None:
    """Store a fact in the knowledge base.

    Args:
        fact:   The fact text to store.
        source: Source tag for provenance tracking.
    """
    try:
        from handlers.memory.knowledge_base import add_entry
        add_entry(fact, source=source)
        logger.info("Stored knowledge [%s]: %s", source, fact[:80])
    except Exception as exc:
        logger.warning("Failed to store knowledge: %s", exc)
