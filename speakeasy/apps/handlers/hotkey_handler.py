#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: hotkey_handler.py - Hotkey detection handler
# Date: 2026-02-11
# Version: 1.1.0
# Category: speakeasy/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2026-02-11): Added state management functions for module orchestration
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
#   - Pure functions only, no classes, no Prax imports
# =============================================

"""
Hotkey detection handler for Speakeasy.

Provides functions for parsing hotkey strings and managing keyboard listeners
using pynput. Supports both press-to-toggle and hold-to-record modes.
"""

from typing import Tuple, Callable, Optional, Set, Any, Dict, List
from pynput import keyboard


def parse_hotkey(hotkey_string: str) -> Tuple[Set[str], str]:
    """
    Parse a hotkey string like "ctrl+space" into modifiers and key.

    Args:
        hotkey_string: String representation like "ctrl+space", "ctrl+shift+a"

    Returns:
        Tuple of (set of modifiers, key string)
        Example: ("ctrl+space",) -> ({"ctrl"}, "space")

    Raises:
        ValueError: If hotkey string is empty or invalid format
    """
    if not hotkey_string or not hotkey_string.strip():
        raise ValueError("Hotkey string cannot be empty")

    parts = [p.strip().lower() for p in hotkey_string.split('+')]

    if len(parts) < 1:
        raise ValueError(f"Invalid hotkey format: {hotkey_string}")

    # Last part is the key, everything else is modifiers
    key = parts[-1]
    modifiers = set(parts[:-1]) if len(parts) > 1 else set()

    # Validate modifiers
    valid_modifiers = {'ctrl', 'shift', 'alt', 'cmd', 'super'}
    invalid_mods = modifiers - valid_modifiers
    if invalid_mods:
        raise ValueError(f"Invalid modifiers: {invalid_mods}")

    return modifiers, key


def start_listener(
    activation_key: str = "ctrl+space",
    on_activate: Optional[Callable[[], None]] = None,
    on_deactivate: Optional[Callable[[], None]] = None,
    backend: str = "auto"
) -> Any:
    """
    Start a keyboard listener for hotkey detection.

    Args:
        activation_key: Hotkey string like "ctrl+space"
        on_activate: Callback when hotkey is pressed
        on_deactivate: Callback when hotkey is released
        backend: Backend to use ("auto", "pynput"). Currently only pynput supported.

    Returns:
        Listener object that can be passed to stop_listener()

    Raises:
        ValueError: If backend is not supported or hotkey is invalid
    """
    if backend not in ("auto", "pynput"):
        raise ValueError(f"Unsupported backend: {backend}. Use 'auto' or 'pynput'")

    # Parse the hotkey
    modifiers, key = parse_hotkey(activation_key)

    # Track currently pressed keys
    current_keys = set()
    hotkey_was_active = False

    # Map modifier names to pynput Key objects
    modifier_map = {
        'ctrl': {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl},
        'shift': {keyboard.Key.shift_l, keyboard.Key.shift_r, keyboard.Key.shift},
        'alt': {keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt},
        'cmd': {keyboard.Key.cmd_l, keyboard.Key.cmd_r, keyboard.Key.cmd},
        'super': {keyboard.Key.cmd_l, keyboard.Key.cmd_r, keyboard.Key.cmd}
    }

    def normalize_key(k) -> str:
        """Normalize a key to string format."""
        if hasattr(k, 'char') and k.char:
            return k.char.lower()
        elif hasattr(k, 'name'):
            return k.name.lower()
        else:
            return str(k).lower()

    def is_hotkey_active() -> bool:
        """Check if the hotkey combination is currently pressed."""
        # Check if all modifiers are pressed
        for mod in modifiers:
            mod_keys = modifier_map.get(mod, set())
            if not any(mk in current_keys for mk in mod_keys):
                return False

        # Check if the key is pressed
        key_pressed = False
        for pressed_key in current_keys:
            norm_key = normalize_key(pressed_key)
            if norm_key == key:
                key_pressed = True
                break

        return key_pressed

    def on_press(k):
        """Handle key press events."""
        nonlocal hotkey_was_active
        current_keys.add(k)

        is_active = is_hotkey_active()

        # Trigger on_activate when transitioning from inactive to active
        if is_active and not hotkey_was_active:
            hotkey_was_active = True
            if on_activate:
                on_activate()

    def on_release(k):
        """Handle key release events."""
        nonlocal hotkey_was_active
        current_keys.discard(k)

        is_active = is_hotkey_active()

        # Trigger on_deactivate when transitioning from active to inactive
        if not is_active and hotkey_was_active:
            hotkey_was_active = False
            if on_deactivate:
                on_deactivate()

    # Create and start the listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    return listener


def stop_listener(listener: Any) -> None:
    """
    Stop a running keyboard listener.

    Args:
        listener: Listener object returned from start_listener()
    """
    if listener and hasattr(listener, 'stop'):
        listener.stop()


# State management functions for module orchestration
def start_listening_with_config(
    listener_ref: list,
    config: Optional[dict] = None,
    on_recording_start: Optional[Callable[[], None]] = None,
    on_recording_stop: Optional[Callable[[], None]] = None
) -> Dict[str, Any]:
    """
    Start listener with config management and state tracking.

    This is a higher-level function that handles config extraction and state.
    Used by modules for orchestration.

    Args:
        listener_ref: List containing current listener (modified in place)
        config: Configuration dict with optional keys:
            - activation_key: Hotkey string (default: "ctrl+space")
            - backend: Backend to use (default: "auto")
        on_recording_start: Callback when hotkey is pressed
        on_recording_stop: Callback when hotkey is released

    Returns:
        Configuration dict used

    Raises:
        RuntimeError: If listener already running or start fails
    """
    if listener_ref and listener_ref[0] is not None:
        raise RuntimeError("Listener already running. Stop existing listener first.")

    cfg = config or {}
    activation_key = cfg.get("activation_key", "ctrl+space")
    backend = cfg.get("backend", "auto")

    listener = start_listener(
        activation_key=activation_key,
        on_activate=on_recording_start,
        on_deactivate=on_recording_stop,
        backend=backend
    )

    listener_ref.clear()
    listener_ref.append(listener)

    return cfg


def stop_listening_with_state(listener_ref: list) -> None:
    """
    Stop listener and clear state.

    This is a higher-level function that handles state management.
    Used by modules for orchestration.

    Args:
        listener_ref: List containing current listener (modified in place)
    """
    if not listener_ref or listener_ref[0] is None:
        return

    listener = listener_ref[0]
    stop_listener(listener)
    listener_ref.clear()
