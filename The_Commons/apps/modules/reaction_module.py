#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: reaction_module.py - Curation Orchestration Module
# Date: 2026-02-08
# Version: 2.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Thin router refactor - moved implementation to handlers/curation/curation_ops.py (FPLAN-0356)
#   - v1.0.0 (2026-02-08): Initial creation - reactions, pins, trending
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Curation Orchestration Module

Thin router for thread curation and engagement workflows.
Delegates all implementation to handlers/curation/curation_ops.py.

Handles: react, unreact, reactions, pin, unpin, pinned, trending commands.
"""

import sys
from pathlib import Path
from typing import List

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.curation.curation_ops import (
    add_react,
    remove_react,
    show_reactions,
    pin_post_cmd,
    unpin_post_cmd,
    show_pinned,
    show_trending,
)


# =============================================================================
# COMMAND ROUTING
# =============================================================================

HANDLED_COMMANDS = ["react", "unreact", "reactions", "pin", "unpin", "pinned", "trending"]


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle curation-related commands.

    Args:
        command: Command name
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in HANDLED_COMMANDS:
        return False

    if command == "react":
        return add_react(args)
    elif command == "unreact":
        return remove_react(args)
    elif command == "reactions":
        return show_reactions(args)
    elif command == "pin":
        return pin_post_cmd(args)
    elif command == "unpin":
        return unpin_post_cmd(args)
    elif command == "pinned":
        return show_pinned(args)
    elif command == "trending":
        return show_trending(args)

    return False
