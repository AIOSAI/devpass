#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: explore_module.py - Exploration Module
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 6 Fun)
#
# CODE STANDARDS:
#   - Orchestration and rendering - delegates data ops to handlers/rooms/explore_ops.py
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Exploration Module

Thin router for secret room exploration commands.
Delegates all implementation to handlers/rooms/explore_ops.py.

Handles: explore, secrets commands.
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

from handlers.rooms.explore_ops import explore_rooms, list_secrets


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle exploration commands.

    Args:
        command: Command name (explore, secrets)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in ["explore", "secrets"]:
        return False

    if command == "explore":
        return explore_rooms(args)
    elif command == "secrets":
        return list_secrets(args)

    return False
