#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: pre_compact.py - Pre-Compact Memory Preservation Hook
# Date: 2025-10-30
# Version: 1.0.0
# Category: claude_hooks
#
# CHANGELOG (Max 5 entries - remove oldest when adding new):
#   - v1.0.0 (2025-10-30): Initial implementation for context compaction preparation
# =============================================

"""
Pre-Compact Hook - Preserve context before token compaction

Problem: Sonnet 4.5 sometimes loses context after compaction events
Solution: Trigger memory file updates BEFORE compact happens so critical
          context is preserved in memory files that can be re-loaded

This hook:
1. Detects when compaction is about to occur
2. Triggers /updateall command to save current context
3. Ensures memory files are current before compaction
4. Helps Claude recover context by re-reading memory files post-compact

Usage: Automatically called by Claude Code before compaction events
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Configuration
AIPASS_ROOT = Path.home()
LOG_FILE = Path(__file__).parent / ".pre_compact_log"

def log_message(message: str) -> None:
    """Log hook activity for debugging"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

def trigger_memory_update() -> bool:
    """Trigger memory file updates before compaction"""
    try:
        # Run the updateall hook script directly
        updateall_script = Path(__file__).parent / "updateall_hook.py"

        if not updateall_script.exists():
            log_message("ERROR: updateall_hook.py not found")
            return False

        result = subprocess.run(
            [sys.executable, str(updateall_script)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            log_message("SUCCESS: Memory files updated before compaction")
            return True
        else:
            log_message(f"FAILED: updateall returned {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        log_message("TIMEOUT: Memory update took >30s")
        return False
    except Exception as e:
        log_message(f"ERROR: {e}")
        return False

def main():
    """Main hook entry point"""
    try:
        # Read hook input
        input_data = json.load(sys.stdin)

        # Extract compaction details
        trigger = input_data.get("trigger", "unknown")  # 'manual' or 'auto'
        session_id = input_data.get("session_id", "")
        transcript_path = input_data.get("transcript_path", "")
        custom_instructions = input_data.get("custom_instructions", "")

        log_message(f"Pre-compact hook triggered: trigger={trigger}, session={session_id}")

        # Trigger memory file updates
        success = trigger_memory_update()

        if success:
            # Send notification to user via stderr
            print("💾 Memory files updated before compaction", file=sys.stderr)

            # Send custom compact instructions via stdout (appended to compaction)
            print("""POST-COMPACT SELF-ASSESSMENT (MANDATORY):

Before taking ANY action, assess the conversation state:

1. DELEGATION FIRST - Am I about to debug or build something?
   → STOP. Check: Which branch owns this domain?
   → Read branch_system_prompt.md for expertise table
   → If another branch owns it: DELEGATE via ai_mail --auto-execute
   → DEV_CENTRAL orchestrates, agents execute. Don't burn context on their domain.

2. PLANNING vs EXECUTING - Was there an unresolved planning/design discussion?
   → If YES: Continue the discussion, DO NOT start executing

3. MID-PROCESS CHECK - Was I in the middle of executing a multi-step process?
   → If YES and confident about context: Continue
   → If uncertain: Ask before continuing

4. TASK REQUEST CHECK - Did the summary end with a task request that wasn't started?
   → Confirm with user before executing

5. ARCHITECTURE/DESIGN - Were we discussing system design or architecture?
   → Stay in discussion mode, don't start building

DEFAULT: If uncertain about state, ASK rather than assume and execute.
DEFAULT: If about to debug/code, DELEGATE to expert branch first.

Memory files preserved in branch *.local.json and *.observations.json.""", file=sys.stdout)
        else:
            print("⚠️ Memory update failed - check .pre_compact_log", file=sys.stderr)

    except (json.JSONDecodeError, Exception) as e:
        log_message(f"Hook error: {e}")
        pass  # Fail silently in hook context

    sys.exit(0)

if __name__ == "__main__":
    main()
