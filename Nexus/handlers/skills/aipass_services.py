#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""AIPass services skill - drone commands, ai_mail"""

import sys
import subprocess
from pathlib import Path
from typing import Optional

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

def handle_request(user_input: str) -> Optional[str]:
    """Handle AIPass service commands

    Patterns:
    - "drone ..." → run drone command
    - "send mail to @branch ..." → send ai_mail
    - "check inbox" / "inbox" → check ai_mail inbox
    - "system status" → system-wide status
    """
    lower = user_input.lower().strip()

    # Drone command passthrough
    if lower.startswith("drone "):
        cmd = user_input.strip()
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30,
                cwd="/home/aipass"
            )
            output = result.stdout.strip() or result.stderr.strip() or "(no output)"
            return f"```\n{output}\n```"
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds."
        except Exception as e:
            return f"Error: {e}"

    # Send mail
    if lower.startswith(("send mail to ", "mail ")):
        # Parse: send mail to @branch "subject" "message"
        # Simple extraction
        parts = user_input.split('"')
        if len(parts) >= 4:
            target = parts[0].split()[-1]  # @branch
            subject = parts[1]
            message = parts[3] if len(parts) > 3 else ""
            cmd = f'drone @ai_mail send {target} "{subject}" "{message}"'
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=15,
                    cwd="/home/aipass"
                )
                return result.stdout.strip() or "Mail sent."
            except Exception as e:
                return f"Mail error: {e}"
        return "Usage: send mail to @branch \"subject\" \"message\""

    # Check inbox
    if lower in ("inbox", "check inbox", "check mail", "mail"):
        try:
            result = subprocess.run(
                "drone @ai_mail inbox", shell=True, capture_output=True, text=True,
                timeout=15, cwd="/home/aipass"
            )
            return result.stdout.strip() or "Inbox empty."
        except Exception as e:
            return f"Inbox error: {e}"

    # System status
    if lower in ("system status", "aipass status", "status"):
        try:
            result = subprocess.run(
                "drone systems", shell=True, capture_output=True, text=True,
                timeout=15, cwd="/home/aipass"
            )
            return result.stdout.strip() or "(no output)"
        except Exception as e:
            return f"Status error: {e}"

    return None
