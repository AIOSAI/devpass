#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: pre_compact.py - Pre-Compact Memory Preservation Hook
# Date: 2025-10-30
# Version: 2.0.0
# Category: claude_hooks
#
# CHANGELOG (Max 5 entries - remove oldest when adding new):
#   - v2.0.0 (2026-02-16): Fix: always inject post-compact instructions (not gated on updateall),
#     add conversational continuity rules, remove broken updateall dependency
#   - v1.0.0 (2025-10-30): Initial implementation for context compaction preparation
# =============================================

"""
Pre-Compact Hook - Inject post-compact recovery instructions

Problem: After compaction, Claude loses conversational flow and comes out
         disoriented - tone shifts, context feels robotic, mid-conversation
         momentum is lost. Patrick noticed this from Telegram.

This hook:
1. Always injects post-compact self-assessment instructions into the summary
2. Prioritizes conversational continuity (matching tone, continuing flow)
3. Includes delegation/process guardrails
4. Logs compaction events for debugging

Usage: Automatically called by Claude Code before compaction events
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Configuration
LOG_FILE = Path(__file__).parent / ".pre_compact_log"

def log_message(message: str) -> None:
    """Log hook activity for debugging"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

def main():
    """Main hook entry point"""
    try:
        # Read hook input
        input_data = json.load(sys.stdin)

        # Extract compaction details
        trigger = input_data.get("trigger", "unknown")
        session_id = input_data.get("session_id", "")

        log_message(f"Pre-compact hook triggered: trigger={trigger}, session={session_id}")

        # Notify user via stderr
        print("Context compacting - recovery instructions injected", file=sys.stderr)

        # ALWAYS inject post-compact instructions via stdout
        print("""POST-COMPACT RECOVERY (MANDATORY):

You just compacted. You're working from a summary now, not live memory.
The user may notice a tone shift. Handle this smoothly.

CONVERSATIONAL CONTINUITY (HIGHEST PRIORITY):
1. ACKNOWLEDGE if the user notices - be honest that compaction happened
2. MATCH THE TONE from the summary - if it was casual/brainstorming, stay casual
3. CONTINUE THE FLOW - pick up where the conversation left off naturally
4. DON'T pivot to new topics or ask generic questions
5. If you were mid-brainstorm, keep brainstorming. If mid-task, keep working.
6. DO NOT surface old notes/TODOs as if they're fresh conversation starters

PROCESS GUARDRAILS:
- If a planning/design discussion was active: continue it, don't start executing
- If mid-execution: continue if context is clear, ask if uncertain
- If a task was requested but not started: confirm before executing
- Delegation: if about to debug/code in another branch's domain, delegate via ai_mail

DEFAULT: Continue naturally. If genuinely uncertain, ask briefly - don't monologue about what you lost.""", file=sys.stdout)

        log_message("SUCCESS: Post-compact instructions injected")

    except (json.JSONDecodeError, Exception) as e:
        log_message(f"Hook error: {e}")
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
