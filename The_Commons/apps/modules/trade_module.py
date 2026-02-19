#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: trade_module.py - Trade Orchestration Module
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 5)
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Trade Orchestration Module

Thin router for trading workflows. Delegates all implementation
to handlers/artifacts/trade_ops.py.

Handles: gift, trade, drop, find, mint commands.
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

from handlers.artifacts.trade_ops import (
    gift_artifact,
    trade_artifact,
    drop_item,
    find_item,
    mint_event_artifact,
)


# =============================================================================
# COMMAND ROUTING
# =============================================================================

TRADE_COMMANDS = ["gift", "trade", "drop", "find", "mint"]


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle trade-related commands.

    Args:
        command: Command name (gift, trade, drop, find, mint)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in TRADE_COMMANDS:
        return False

    if command == "gift":
        return gift_artifact(args)
    elif command == "trade":
        return trade_artifact(args)
    elif command == "drop":
        return drop_item(args)
    elif command == "find":
        return find_item(args)
    elif command == "mint":
        return mint_event_artifact(args)

    return False
