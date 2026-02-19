#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: feed_module.py - Feed Orchestration Module
# Date: 2026-02-06
# Version: 2.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Thin router refactor - moved implementation to handlers/feed/feed_ops.py (FPLAN-0356)
#   - v1.0.0 (2026-02-06): Initial creation - feed display with sorting
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Feed Orchestration Module

Thin router for feed display. Delegates all implementation
to handlers/feed/feed_ops.py.

Handles: feed command with hot/new/top sorting.
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

from handlers.feed.feed_ops import display_feed


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle feed-related commands.

    Args:
        command: Command name (feed)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command != "feed":
        return False

    return display_feed(args)
