#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: notification_module.py - Notification Preferences Orchestration Module
# Date: 2026-02-08
# Version: 2.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Thin router refactor - moved implementation to handlers/notifications/notification_ops.py (FPLAN-0356)
#   - v1.0.0 (2026-02-08): Initial creation - watch/mute/track/preferences commands
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Notification Preferences Orchestration Module

Thin router for notification preference commands. Delegates all implementation
to handlers/notifications/notification_ops.py.

Handles: watch, mute, track, preferences commands.
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

from handlers.notifications.notification_ops import (
    set_watch,
    set_mute,
    set_track,
    show_preferences,
)


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle notification preference commands.

    Args:
        command: Command name (watch, mute, track, preferences)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in ["watch", "mute", "track", "preferences"]:
        return False

    if command == "watch":
        return set_watch(args)
    elif command == "mute":
        return set_mute(args)
    elif command == "track":
        return set_track(args)
    elif command == "preferences":
        return show_preferences(args)

    return False
