#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: router.py - Command Routing Handler
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/handlers/routing
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-29): Extracted from drone.py lines 136-155
# CODE STANDARDS: Handler pattern - no prax, no CLI
# =============================================

"""
Command routing - routes commands to appropriate modules.
"""

from typing import List, Any


def route_command(command: str, args: List[str], modules: List[Any]) -> bool:
    """
    Route command to appropriate module.

    Args:
        command: Command name
        args: Additional arguments
        modules: List of discovered modules (must have handle_command method)

    Returns:
        True if command was handled, False otherwise
    """
    for module in modules:
        try:
            if module.handle_command(command, args):
                return True
        except Exception:
            # Continue to next module on failure
            # Caller should handle logging if needed
            continue

    return False
