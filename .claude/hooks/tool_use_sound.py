#!/usr/bin/env python3
"""
Tool Use Hook - Plays ATM key press sound when Claude uses tools
Sound: mixkit-atm-cash-machine-key-press-2841.wav
"""

import json
import sys
import subprocess
import os

def play_sound() -> None:
    """Play the tool use sound using aplay."""
    sound_file = "/home/aipass/.claude/hooks/sounds/mixkit-atm-cash-machine-key-press-2841.wav"

    # Check if sound file exists
    if not os.path.exists(sound_file):
        print(f"Warning: Sound file not found: {sound_file}", file=sys.stderr)
        return None

    try:
        # Play sound in background (don't block Claude)
        # -q for quiet mode (no output)
        subprocess.Popen(
            ["aplay", "-q", sound_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        # Don't block on audio errors
        print(f"Audio playback error: {e}", file=sys.stderr)

def main():
    try:
        # Read hook data from stdin
        hook_data = json.loads(sys.stdin.read())

        # Check if this is a PreToolUse event
        if hook_data.get("hook_event_name") == "PreToolUse":
            tool_name = hook_data.get("tool_name", "")

            # Filter which tools trigger sounds (optional)
            # Comment out this section to play sound for ALL tools
            sound_for_tools = [
                "Bash",
                "Edit",
                "MultiEdit",
                "Write",
                "Read",
                "Grep",
                "Glob"
            ]

            if tool_name in sound_for_tools:
                play_sound()

            # Uncomment below to play sound for ALL tools
            # play_sound()

    except Exception as e:
        # Log error but don't block Claude
        print(f"Hook error: {e}", file=sys.stderr)

    # Always exit successfully to not interfere with Claude
    sys.exit(0)

if __name__ == "__main__":
    main()