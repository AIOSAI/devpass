#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: run_branch_log_watcher.py - Branch Log Watcher Runner
# Date: 2026-02-02
# Version: 1.0.0
# Category: trigger/tools
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-02): Created - FPLAN-0284 persistent watcher
#
# CODE STANDARDS:
#   - Runner script for persistent background operation
#   - Keeps watchdog observer alive
# =============================================

"""
Branch Log Watcher Runner

Runs the branch log watcher as a persistent background process.
Use with nohup: nohup python3 tools/run_branch_log_watcher.py &

Watches /home/aipass/aipass_core/*/logs/*.log for ERROR entries.
Fires error_detected events handled by AI_Mail's error_handler.
"""

import sys
import time
import signal
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from trigger.apps.modules.branch_log_events import start, stop
from trigger.apps.modules.core import trigger


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("[TRIGGER] Received shutdown signal, stopping watcher...")
    stop()
    sys.exit(0)


def main():
    """Run the branch log watcher persistently."""
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info("[TRIGGER] Starting branch log watcher daemon...")

    # Initialize trigger to register event handlers
    trigger.fire('daemon_startup')

    if not start():
        logger.error("[TRIGGER] Failed to start branch log watcher")
        sys.exit(1)

    logger.info("[TRIGGER] Branch log watcher running. Press Ctrl+C to stop.")

    # Keep alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("[TRIGGER] Interrupted, stopping...")
        stop()


if __name__ == "__main__":
    main()
