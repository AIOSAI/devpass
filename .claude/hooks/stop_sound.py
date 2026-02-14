#!/usr/bin/env python3
"""
Stop Hook - Plays achievement bell sound when Claude finishes responding
Sound: mixkit-achievement-bell-600.wav
"""

import json
import sys
import subprocess
import os

def play_sound() -> None:
    """Play the achievement bell sound using aplay."""
    sound_file = "/home/aipass/.claude/hooks/sounds/mixkit-achievement-bell-600.wav"

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

        # Check if this is a Stop event (should always be for this hook)
        if hook_data.get("hook_event_name") == "Stop":
            # Check if stop_hook_active to prevent infinite loops
            if not hook_data.get("stop_hook_active", False):
                play_sound()

    except Exception as e:
        # Log error but don't block Claude
        print(f"Hook error: {e}", file=sys.stderr)

    # Always exit successfully to not interfere with Claude
    sys.exit(0)

if __name__ == "__main__":
    main()