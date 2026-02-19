#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: digest_module.py - Digest Orchestration Module
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 2)
#
# CODE STANDARDS:
#   - Module: Thin orchestration only
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Digest Orchestration Module

Thin router for community digest workflows. Delegates all
implementation to handlers/digest/digest_ops.py.

Handles: digest command.
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

from handlers.digest.digest_ops import show_digest


# =============================================================================
# COMMAND ROUTING
# =============================================================================

HANDLED_COMMANDS = ["digest"]


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle digest-related commands.

    Args:
        command: Command name (digest)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in HANDLED_COMMANDS:
        return False

    if command == "digest":
        return show_digest(args)

    return False
