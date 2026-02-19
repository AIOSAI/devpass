#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: capsule_module.py - Time Capsule Module
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 6 Fun)
#
# CODE STANDARDS:
#   - Orchestration and rendering - delegates data ops to handlers/artifacts/capsule_ops.py
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Time Capsule Module

Thin router for time capsule commands.
Delegates all implementation to handlers/artifacts/capsule_ops.py.

Handles: capsule, capsules, open commands.
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

from handlers.artifacts.capsule_ops import seal_capsule, list_capsules, open_capsule


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle time capsule commands.

    Args:
        command: Command name (capsule, capsules, open)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in ["capsule", "capsules", "open"]:
        return False

    if command == "capsule":
        return seal_capsule(args)
    elif command == "capsules":
        return list_capsules(args)
    elif command == "open":
        return open_capsule(args)

    return False
