#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: catchup_module.py - Catchup Orchestration Module
# Date: 2026-02-08
# Version: 2.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Thin router refactor - moved implementation to handlers/catchup/catchup_ops.py (FPLAN-0356)
#   - v1.0.0 (2026-02-08): Initial creation - catchup command + dashboard updates
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Catchup Orchestration Module

Thin router for the catchup command. Delegates all implementation
to handlers/catchup/catchup_ops.py.

Handles: catchup command.
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

from handlers.catchup.catchup_ops import run_catchup


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle catchup-related commands.

    Args:
        command: Command name (catchup)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command != "catchup":
        return False

    return run_catchup(args)
