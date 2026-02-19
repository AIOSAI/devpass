#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""
Intent detection for Nexus Natural Flow.

Analyses natural language input to determine whether the user is asking
for code execution, file operations, system checks, or plain
conversation.  The detection is deliberately fuzzy -- Nexus should feel
like talking to a colleague, not issuing commands.

Rebuilt from v1 natural_flow.py detect_operational_intent() into a
standalone module for Nexus v2.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Keyword / pattern tables
# ---------------------------------------------------------------------------

FILE_OPERATIONS: Dict[str, List[str]] = {
    "create": ["create", "make", "build", "generate", "write", "new"],
    "edit":   ["edit", "modify", "update", "change", "fix", "revise"],
    "read":   ["read", "show", "display", "view", "open", "see", "check"],
    "load":   ["load", "read file", "open file", "load file"],
    "delete": ["delete", "remove", "clear"],
    "list":   ["list", "show files", "what files", "ls", "dir"],
    "cache":  ["clear cache", "reset cache", "file cache"],
}

EXECUTION_PATTERNS: List[str] = [
    "run", "execute", "test", "try", "launch", "start",
    "script", "code", "python",
]

DATA_PATTERNS: List[str] = [
    "analyze", "process", "parse", "extract", "transform",
    "calculate", "count", "sum", "average",
]

SYSTEM_PATTERNS: List[str] = [
    "install", "setup", "configure", "check system", "status",
    "disk", "cpu", "memory usage", "uptime",
]

FILE_TYPE_INDICATORS: List[str] = [
    ".py", ".md", ".txt", ".json", ".csv", ".xml",
    ".yaml", ".yml", ".log", ".sh", ".toml",
]

CONTEXT_REFERENCES: List[str] = [
    "that file", "the script", "the code", "it",
    "this", "what we made", "the output", "last result",
]

# Words that strongly suggest the user is just chatting
CHAT_INDICATORS: List[str] = [
    "what do you think", "how are you", "tell me about",
    "explain", "why", "opinion", "feel", "believe",
    "hello", "hi", "hey", "thanks", "thank you",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_intent(user_input: str) -> Dict[str, Any]:
    """Determine the user's intent from natural language.

    Scans *user_input* against known keyword patterns and returns a
    structured dict describing what Nexus should do next.

    Args:
        user_input: Raw text from the user.

    Returns:
        Dict with keys:

        * ``intent`` -- one of ``"execution"``, ``"file_op"``,
          ``"data"``, ``"system"``, ``"chat"``.
        * ``is_operational`` -- ``True`` when Nexus should generate /
          run code rather than just reply conversationally.
        * ``operations`` -- list of matched operation categories.
        * ``confidence`` -- float 0.0 .. 1.0 indicating how certain the
          detection is.
        * ``details`` -- sub-dict with booleans for what matched.
    """
    lower = user_input.lower().strip()

    operations: List[str] = []
    score: float = 0.0

    # --- file operations ---
    matched_file_ops: List[str] = []
    for op_type, keywords in FILE_OPERATIONS.items():
        if any(kw in lower for kw in keywords):
            matched_file_ops.append(op_type)
            operations.append(f"file_{op_type}")
            score += 0.4

    # --- execution patterns ---
    has_exec = any(p in lower for p in EXECUTION_PATTERNS)
    if has_exec:
        operations.append("execution")
        score += 0.4

    # --- data patterns ---
    has_data = any(p in lower for p in DATA_PATTERNS)
    if has_data:
        operations.append("data_processing")
        score += 0.4

    # --- system patterns ---
    has_system = any(p in lower for p in SYSTEM_PATTERNS)
    if has_system:
        operations.append("system")
        score += 0.4

    # --- boosters ---
    has_file_type = any(ind in lower for ind in FILE_TYPE_INDICATORS)
    if has_file_type:
        score += 0.3

    has_context_ref = any(ref in lower for ref in CONTEXT_REFERENCES)
    if has_context_ref:
        score += 0.2

    # --- contains a code block already? ---
    has_code_block = "```" in user_input
    if has_code_block:
        operations.append("inline_code")
        score += 0.5

    # --- chat dampener ---
    has_chat = any(ci in lower for ci in CHAT_INDICATORS)
    if has_chat and not operations:
        score = max(score - 0.3, 0.0)

    # Clamp
    confidence = min(score, 1.0)
    is_operational = confidence >= 0.4 or len(operations) > 0

    # Pick primary intent
    if not is_operational:
        intent = "chat"
    elif "execution" in operations or "inline_code" in operations:
        intent = "execution"
    elif any(op.startswith("file_") for op in operations):
        intent = "file_op"
    elif "data_processing" in operations:
        intent = "data"
    elif "system" in operations:
        intent = "system"
    else:
        intent = "execution"

    return {
        "intent": intent,
        "is_operational": is_operational,
        "operations": operations,
        "confidence": confidence,
        "details": {
            "file_ops": matched_file_ops,
            "has_file_types": has_file_type,
            "has_context_refs": has_context_ref,
            "has_code_block": has_code_block,
            "has_chat_markers": has_chat,
        },
    }
