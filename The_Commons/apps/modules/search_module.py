#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: search_module.py - Search & Log Orchestration Module
# Date: 2026-02-08
# Version: 2.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Thin router refactor - moved implementation to handlers/search/search_ops.py (FPLAN-0356)
#   - v1.0.0 (2026-02-08): Initial creation - search + log export commands
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Search & Log Orchestration Module

Thin router for search and log export workflows.
Delegates all implementation to handlers/search/search_ops.py.

Handles: search, log commands.
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

from handlers.search.search_ops import run_search, export_log


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle search and log commands.

    Args:
        command: Command name (search, log)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in ["search", "log"]:
        return False

    if command == "search":
        return run_search(args)
    elif command == "log":
        return export_log(args)

    return False
