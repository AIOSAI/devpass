#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: profile_module.py - Social Profile Orchestration Module
# Date: 2026-02-08
# Version: 2.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Thin router refactor - moved implementation to handlers/profiles/profile_ops.py (FPLAN-0356)
#   - v1.0.0 (2026-02-08): Initial creation - profile view/edit + who listing
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Social Profile Orchestration Module

Thin router for profile viewing/editing and member listing.
Delegates all implementation to handlers/profiles/profile_ops.py.

Handles: profile, who commands.
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

from handlers.profiles.profile_ops import show_profile, list_members


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle profile and who commands.

    Args:
        command: Command name (profile, who)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in ["profile", "who"]:
        return False

    if command == "profile":
        return show_profile(args)
    elif command == "who":
        return list_members(args)

    return False
