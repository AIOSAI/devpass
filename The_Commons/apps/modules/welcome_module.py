#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: welcome_module.py - Welcome & Onboarding Orchestration Module
# Date: 2026-02-08
# Version: 2.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Thin router refactor - moved implementation to handlers/welcome/welcome_ops.py (FPLAN-0356)
#   - v1.0.0 (2026-02-08): Initial creation - welcome scan + manual welcome commands
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Welcome & Onboarding Orchestration Module

Thin router for the welcome command. Delegates all implementation
to handlers/welcome/welcome_ops.py.

Handles: welcome command.
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

from handlers.welcome.welcome_ops import run_welcome


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle welcome-related commands.

    Args:
        command: Command name (welcome)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command != "welcome":
        return False

    return run_welcome(args)
