#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: input_module.py - Input orchestration module
# Date: 2026-02-11
# Version: 1.1.0
# Category: speakeasy/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2026-02-11): Refactored to thin orchestration - moved implementation to handlers
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
# =============================================

"""
Input module for Speakeasy - orchestrates hotkey and text input.

Provides high-level functions for managing keyboard listeners, text injection,
and cursor position locking.
"""

import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

# Import handlers
sys.path.insert(0, str(Path(__file__).parent.parent))
from handlers import hotkey_handler
from handlers import input_handler
from handlers import cursor_lock_handler

from typing import Optional, Dict, Any, Callable


# Module state - thin wrapper for handler state
_LISTENER_REF = []
_CONFIG = None


def handle_command(command: str, args: Dict[str, Any]) -> bool:
    """
    Handle commands for auto-discovery.

    Args:
        command: Command name ("listen", "type", "lock", "unlock", "stop")
        args: Command arguments

    Returns:
        True if command executed successfully
    """
    global _CONFIG

    if command == "listen":
        try:
            _CONFIG = hotkey_handler.start_listening_with_config(
                listener_ref=_LISTENER_REF,
                config=args.get("config"),
                on_recording_start=args.get("on_recording_start"),
                on_recording_stop=args.get("on_recording_stop")
            )
            logger.info(f"Hotkey listener started: {_CONFIG.get('activation_key', 'ctrl+space')}")
        except Exception as e:
            logger.error(f"Failed to start listener: {e}")
            raise
        return True

    elif command == "type":
        try:
            input_handler.inject_text_smart(
                text=args.get("text", ""),
                config=args.get("config") or _CONFIG,
                cursor_lock_module=cursor_lock_handler
            )
            logger.info(f"Text injected: {len(args.get('text', ''))} characters")
        except Exception as e:
            logger.error(f"Failed to inject text: {e}")
            raise
        return True

    elif command == "lock":
        try:
            lock_state = cursor_lock_handler.lock_cursor()
            logger.info(f"Cursor locked at ({lock_state['cursor_x']}, {lock_state['cursor_y']})")
        except Exception as e:
            logger.error(f"Failed to lock cursor: {e}")
            raise
        return True

    elif command == "unlock":
        cursor_lock_handler.unlock_cursor()
        logger.info("Cursor unlocked")
        return True

    elif command == "stop":
        hotkey_handler.stop_listening_with_state(_LISTENER_REF)
        logger.info("Hotkey listener stopped")
        return True

    else:
        return False
