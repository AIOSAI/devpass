#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: cursor_lock_handler.py - Cursor position locking handler
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
#   - Pure functions only, no classes, no Prax imports
# =============================================

"""
Cursor position locking handler for Speakeasy.

Provides functions for capturing and restoring cursor and window positions
using xdotool. Allows locking the cursor position before recording so text
can be inserted at the correct location.
"""

import subprocess
from typing import Optional, Dict, Any


# Module-level state for cursor lock
_lock_state: Optional[Dict[str, Any]] = None


def get_active_window() -> Dict[str, Any]:
    """
    Get information about the active window and cursor position.

    Returns:
        Dict with keys:
            - window_id: X11 window ID (int)
            - window_name: Window title (str)
            - cursor_x: Cursor X position (int)
            - cursor_y: Cursor Y position (int)

    Raises:
        RuntimeError: If xdotool commands fail
    """
    try:
        # Get active window ID
        result = subprocess.run(
            ['xdotool', 'getactivewindow'],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to get active window: {result.stderr}")

        window_id = int(result.stdout.strip())

        # Get window name
        result = subprocess.run(
            ['xdotool', 'getwindowname', str(window_id)],
            capture_output=True,
            text=True,
            timeout=2
        )

        window_name = result.stdout.strip() if result.returncode == 0 else "Unknown"

        # Get cursor position
        result = subprocess.run(
            ['xdotool', 'getmouselocation', '--shell'],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to get cursor position: {result.stderr}")

        # Parse output like: X=123\nY=456\nSCREEN=0\nWINDOW=789
        cursor_x = 0
        cursor_y = 0
        for line in result.stdout.strip().split('\n'):
            if line.startswith('X='):
                cursor_x = int(line.split('=')[1])
            elif line.startswith('Y='):
                cursor_y = int(line.split('=')[1])

        return {
            'window_id': window_id,
            'window_name': window_name,
            'cursor_x': cursor_x,
            'cursor_y': cursor_y
        }

    except FileNotFoundError:
        raise RuntimeError("xdotool not found. Install with: sudo apt-get install xdotool")
    except subprocess.TimeoutExpired:
        raise RuntimeError("xdotool operation timed out")
    except Exception as e:
        raise RuntimeError(f"Failed to get active window info: {str(e)}")


def lock_cursor() -> Dict[str, Any]:
    """
    Capture and lock the current cursor and window position.

    Returns:
        Lock state dict containing window and cursor info

    Raises:
        RuntimeError: If already locked or capture fails
    """
    global _lock_state

    if _lock_state is not None:
        raise RuntimeError("Cursor is already locked. Call unlock_cursor() first.")

    _lock_state = get_active_window()
    return _lock_state.copy()


def unlock_cursor() -> None:
    """
    Clear the cursor lock state without restoring position.
    """
    global _lock_state
    _lock_state = None


def restore_position(lock_state: Optional[Dict[str, Any]] = None) -> None:
    """
    Restore cursor to a locked position.

    Args:
        lock_state: Lock state dict from lock_cursor(). If None, uses current lock.

    Raises:
        RuntimeError: If no lock state available or restore fails
    """
    global _lock_state

    # Use provided lock_state or fall back to module state
    state = lock_state if lock_state is not None else _lock_state

    if state is None:
        raise RuntimeError("No lock state available. Call lock_cursor() first.")

    try:
        # Focus the window
        subprocess.run(
            ['xdotool', 'windowactivate', '--sync', str(state['window_id'])],
            capture_output=True,
            text=True,
            timeout=2
        )

        # Move cursor to locked position
        subprocess.run(
            ['xdotool', 'mousemove', str(state['cursor_x']), str(state['cursor_y'])],
            capture_output=True,
            text=True,
            timeout=2
        )

        # Click to ensure cursor is in the right place (optional, helps with text fields)
        subprocess.run(
            ['xdotool', 'click', '1'],
            capture_output=True,
            text=True,
            timeout=2
        )

    except FileNotFoundError:
        raise RuntimeError("xdotool not found. Install with: sudo apt-get install xdotool")
    except subprocess.TimeoutExpired:
        raise RuntimeError("xdotool operation timed out")
    except Exception as e:
        raise RuntimeError(f"Failed to restore cursor position: {str(e)}")


def is_locked() -> bool:
    """
    Check if cursor is currently locked.

    Returns:
        True if locked, False otherwise
    """
    return _lock_state is not None
