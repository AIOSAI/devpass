#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: ui_module.py - UI Orchestration Module
# Date: 2026-02-11
# Version: 1.3.0
# Category: speakeasy/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.3.0 (2026-02-11): Updated to new GUI-based ui_handler API
#   - v1.2.0 (2026-02-11): Inlined all functions into handle_command for Seed compliance
#   - v1.1.0 (2026-02-11): Moved implementation to ui_handler
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
#   - Modules use Prax logger, handlers raise exceptions
# =============================================

"""UI Module - Orchestrates UI components for Speakeasy.

Manages system tray icon, status window, notifications, and audio feedback.
Routes commands from main application to UI handlers.
"""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

# Import handlers (internal to speakeasy branch)
sys.path.insert(0, str(Path(__file__).parent.parent))
from handlers import ui_handler


# ============================================================================
# MODULE STATE
# ============================================================================

TRAY_ICON = None
STATUS_WINDOW = None
APP_INSTANCE = None


# ============================================================================
# COMMAND HANDLER (Auto-discovery interface)
# ============================================================================

def handle_command(command, args) -> bool:
    """Handle UI commands (auto-discovery entry point).

    Args:
        command: Command name
        args: Command arguments (dict or None)

    Returns:
        bool: True if command succeeded, False otherwise

    Available commands:
        - status: Update status window display
        - tray-status: Update tray icon status
        - tray: Control tray icon visibility
        - cleanup: Clean shutdown of UI components
    """
    global TRAY_ICON, STATUS_WINDOW, APP_INSTANCE

    logger.info(f"UI command received: {command} with args: {args}")

    try:
        if command == "status":
            status = args.get("status") if args else "ready"
            text = args.get("text", "") if args else ""
            logger.info(f"Setting UI status: {status}")
            if STATUS_WINDOW:
                ui_handler.update_status_window(STATUS_WINDOW, status, text)
            return True

        elif command == "tray-status":
            status = args.get("status") if args else "ready"
            if TRAY_ICON:
                ui_handler.update_tray_status(TRAY_ICON, status)
            return True

        elif command == "tray":
            if not args or "action" not in args:
                logger.info("Tray command missing action")
                return False
            action = args["action"]
            if action == "show" and TRAY_ICON:
                ui_handler.show_tray_icon(TRAY_ICON)
                return True
            elif action == "hide" and TRAY_ICON:
                ui_handler.hide_tray_icon(TRAY_ICON)
                return True
            logger.info(f"Tray action failed: {action}")
            return False

        elif command == "cleanup":
            logger.info("Cleaning up UI components")
            if TRAY_ICON:
                ui_handler.hide_tray_icon(TRAY_ICON)
            TRAY_ICON = None
            STATUS_WINDOW = None
            APP_INSTANCE = None
            try:
                from trigger import trigger
                trigger.fire('speakeasy_ui_cleanup', {"status": "complete"})
            except ImportError:
                logger.info("Trigger module not available for cleanup event")
            logger.info("UI cleanup complete")
            return True

        else:
            return False

    except Exception as e:
        logger.error(f"UI command failed: {command}", exc_info=True)
        return False
