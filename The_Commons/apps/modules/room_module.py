#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: room_module.py - Room Management Module
# Date: 2026-02-06
# Version: 2.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Thin router refactor - moved implementation to handlers/rooms/room_ops.py (FPLAN-0356)
#   - v1.0.0 (2026-02-06): Initial creation - room CRUD and membership
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Room Management Module

Thin router for room management. Delegates all implementation
to handlers/rooms/room_ops.py.

Handles: room create, room list, room join commands.
"""

import sys
from pathlib import Path
from typing import List

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.rooms.room_ops import create_room, list_rooms, join_room


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle room-related commands.

    Args:
        command: Command name (room)
        args: Command arguments (subcommand + params)

    Returns:
        True if command handled, False otherwise
    """
    if command != "room":
        return False

    if not args:
        # Default: list rooms
        return list_rooms([])

    subcommand = args[0].lower()
    sub_args = args[1:]

    if subcommand == "create":
        return create_room(sub_args)
    elif subcommand == "list":
        return list_rooms(sub_args)
    elif subcommand == "join":
        return join_room(sub_args)
    else:
        console.print(f"[red]Unknown room subcommand: {subcommand}[/red]")
        console.print("[dim]Available: create, list, join[/dim]")
        return True
