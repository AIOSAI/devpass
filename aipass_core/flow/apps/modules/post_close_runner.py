#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: post_close_runner.py - Background post-close processing
# Date: 2026-02-14
# Version: 1.0.0
# Category: flow/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-14): Created - runs summary generation and mbank archival in background
#
# CODE STANDARDS:
#   - Seed v3.0 compliant (imports, architecture, error handling)
# ==============================================

"""
Post-Close Background Runner

Runs summary generation and memory bank archival as a background process.
Called by close_plan.py via subprocess.Popen so the close command returns fast.

This script lives inside the flow branch so handler import guards allow it.
"""

import sys
from pathlib import Path

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from flow.apps.handlers.summary.generate import generate_summaries
from flow.apps.handlers.mbank.process import process_closed_plans

if __name__ == "__main__":
    generate_summaries()
    process_closed_plans()
