#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: input_handler.py - Text injection handler
# Date: 2026-02-11
# Version: 1.3.0
# Category: speakeasy/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.3.0 (2026-02-12): Fixed xclip timeout: process cleanup, DISPLAY check, timeout 2s→5s
#   - v1.2.0 (2026-02-11): Fixed xclip/xdotool PATH resolution for restricted environments
#   - v1.1.0 (2026-02-11): Added inject_text_smart for module orchestration
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
#   - Pure functions only, no classes, no Prax imports
# =============================================

"""
Text injection handler for Speakeasy.

Provides functions for typing text into active windows using pynput or
clipboard paste methods. Handles special characters properly.
"""

import os
import time
import shutil
import subprocess
from typing import Optional, Dict, Any
from pynput import keyboard


def _find_binary(name: str) -> str:
    """Find a binary by name, falling back to /usr/bin if PATH is restricted."""
    path = shutil.which(name)
    if path:
        return path
    fallback = f"/usr/bin/{name}"
    if os.path.isfile(fallback) and os.access(fallback, os.X_OK):
        return fallback
    raise FileNotFoundError(f"{name} not found. Install with: sudo apt-get install {name}")


def type_text(text: str, method: str = "pynput", key_delay: float = 0.005) -> None:
    """
    Type text into the active window character by character.

    Args:
        text: Text to type
        method: Method to use ("pynput" or "xdotool")
        key_delay: Delay between keystrokes in seconds

    Raises:
        ValueError: If method is not supported
        RuntimeError: If typing fails
    """
    if not text:
        return

    if method == "pynput":
        _type_with_pynput(text, key_delay)
    elif method == "xdotool":
        _type_with_xdotool(text, key_delay)
    else:
        raise ValueError(f"Unsupported typing method: {method}")


def paste_text(text: str) -> None:
    """
    Copy text to clipboard and paste using Ctrl+V.

    This is faster than character-by-character typing for large texts.
    Uses xclip for clipboard management.

    Args:
        text: Text to paste

    Raises:
        RuntimeError: If clipboard operations fail
    """
    if not text:
        return

    try:
        # Fail fast if no X display is available (xclip will hang otherwise)
        if not os.environ.get('DISPLAY'):
            raise RuntimeError("No DISPLAY set - cannot access X clipboard")

        # Copy to clipboard using xclip (resolve full path for restricted environments)
        xclip_bin = _find_binary('xclip')
        process = subprocess.Popen(
            [xclip_bin, '-selection', 'clipboard'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        _, stderr = process.communicate(input=text.encode('utf-8'), timeout=5)

        if process.returncode != 0:
            raise RuntimeError(f"xclip failed: {stderr.decode('utf-8')}")

        # Small delay to ensure clipboard is ready
        time.sleep(0.05)

        # Paste using Ctrl+V
        controller = keyboard.Controller()
        with controller.pressed(keyboard.Key.ctrl):
            controller.press('v')
            controller.release('v')

        # Small delay after paste
        time.sleep(0.05)

    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise RuntimeError("xclip operation timed out")
    except FileNotFoundError as e:
        raise RuntimeError(str(e))
    except Exception as e:
        raise RuntimeError(f"Paste operation failed: {str(e)}")


def _type_with_pynput(text: str, key_delay: float) -> None:
    """
    Type text using pynput keyboard controller.

    Args:
        text: Text to type
        key_delay: Delay between keystrokes
    """
    controller = keyboard.Controller()

    for char in text:
        try:
            controller.press(char)
            controller.release(char)
            if key_delay > 0:
                time.sleep(key_delay)
        except Exception as e:
            # Some characters may not be typeable, skip them
            continue


def _type_with_xdotool(text: str, key_delay: float) -> None:
    """
    Type text using xdotool command.

    Args:
        text: Text to type
        key_delay: Delay between keystrokes in seconds

    Raises:
        RuntimeError: If xdotool command fails
    """
    try:
        # Convert delay to milliseconds
        delay_ms = int(key_delay * 1000)

        # Resolve full path for restricted environments
        xdotool_bin = _find_binary('xdotool')

        # Use xdotool type command
        result = subprocess.run(
            [xdotool_bin, 'type', '--delay', str(delay_ms), '--', text],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise RuntimeError(f"xdotool failed: {result.stderr}")

    except FileNotFoundError as e:
        raise RuntimeError(str(e))
    except subprocess.TimeoutExpired:
        raise RuntimeError("xdotool operation timed out")
    except Exception as e:
        raise RuntimeError(f"xdotool typing failed: {str(e)}")


def inject_text_smart(
    text: str,
    config: Optional[Dict[str, Any]] = None,
    cursor_lock_module: Any = None
) -> None:
    """
    Smart text injection with cursor restoration and method selection.

    Handles cursor lock restoration and automatically chooses between typing
    and pasting based on text length. This is a higher-level function for
    module orchestration.

    Args:
        text: Text to inject
        config: Configuration dict with optional keys:
            - input_method: "pynput" or "xdotool" (default: "pynput")
            - key_delay: Delay between keystrokes in seconds (default: 0.005)
            - paste_threshold: Use paste for texts longer than this (default: 100)
            - restore_cursor: Whether to restore cursor position (default: True)
        cursor_lock_module: Module providing is_locked() and restore_position()

    Raises:
        RuntimeError: If text injection fails
    """
    if not text:
        return

    cfg = config or {}
    input_method = cfg.get("input_method", "pynput")
    key_delay = cfg.get("key_delay", 0.005)
    paste_threshold = cfg.get("paste_threshold", 100)
    restore_cursor = cfg.get("restore_cursor", True)

    # Restore cursor position if locked
    if restore_cursor and cursor_lock_module and cursor_lock_module.is_locked():
        cursor_lock_module.restore_position()

    # Choose method based on text length
    if len(text) > paste_threshold:
        paste_text(text)
    else:
        type_text(text, method=input_method, key_delay=key_delay)
