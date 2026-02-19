#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: leaderboard_module.py - Leaderboard Module
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 6 Fun)
#
# CODE STANDARDS:
#   - Orchestration and rendering - delegates data ops to handlers/social/leaderboard_ops.py
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Leaderboard Module

Thin router for leaderboard commands.
Delegates all implementation to handlers/social/leaderboard_ops.py.

Handles: leaderboard, leaderboards commands.
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

from handlers.social.leaderboard_ops import show_leaderboard


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle leaderboard commands.

    Args:
        command: Command name (leaderboard, leaderboards)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in ["leaderboard", "leaderboards"]:
        return False

    return show_leaderboard(args)
