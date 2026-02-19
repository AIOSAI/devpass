#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: comment_module.py - Comment Orchestration Module
# Date: 2026-02-06
# Version: 2.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Thin router refactor - moved implementation to handlers/comments/comment_ops.py (FPLAN-0356)
#   - v1.1.0 (2026-02-09): Added dedup guard to prevent duplicate comments within 5min window
#   - v1.0.0 (2026-02-06): Initial creation - comment and vote orchestration
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Comment Orchestration Module

Thin router for comment and vote workflows. Delegates all implementation
to handlers/comments/comment_ops.py.

Handles: comment, vote commands.
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

from handlers.comments.comment_ops import add_comment, vote_on_content


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle comment and vote commands.

    Args:
        command: Command name (comment, vote)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in ["comment", "vote"]:
        return False

    if command == "comment":
        return add_comment(args)
    elif command == "vote":
        return vote_on_content(args)

    return False
