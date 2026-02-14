#!/usr/bin/env python3
"""
Notification Hook - Plays notification sound when Claude needs permission
Sound: mixkit-clear-announce-tones-2861.wav
"""

import json
import sys
import subprocess
import os

def play_sound() -> None:
    """Play the notification sound using aplay."""
    sound_file = "/home/aipass/.claude/hooks/sounds/mixkit-clear-announce-tones-2861.wav"

    # Check if sound file exists
    if not os.path.exists(sound_file):
        print(f"Warning: Sound file not found: {sound_file}", file=sys.stderr)
        return None

    try:
        # Play sound in background using aplay (don't block Claude)
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

        # Check if this is a Notification event
        if hook_data.get("hook_event_name") == "Notification":
            # Play the notification sound
            play_sound()

            # Optionally log the notification message
            message = hook_data.get("message", "")
            if message:
                print(f"Notification: {message}", file=sys.stderr)

    except Exception as e:
        # Log error but don't block Claude
        print(f"Hook error: {e}", file=sys.stderr)

    # Always exit successfully to not interfere with Claude
    sys.exit(0)

if __name__ == "__main__":
    main()