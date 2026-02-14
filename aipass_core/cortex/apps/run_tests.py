#!/usr/bin/env python3

# ===================AIPASS====================
# META DATA HEADER
# Name: run_tests.py - Cortex Test Runner
# Date: 2025-11-08
# Version: 1.0.0
# Category: cortex
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-08): Initial version
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Pytest wrapper for cortex
Validates working directory before running tests
"""

import sys
import subprocess
from pathlib import Path

# Expected directory
EXPECTED_DIR = Path(__file__).parent.resolve()
CURRENT_DIR = Path.cwd().resolve()

if CURRENT_DIR != EXPECTED_DIR:
    error_msg = f"""
{'='*70}
❌ ERROR: Running tests from wrong directory
{'='*70}

Current directory:  {CURRENT_DIR}
Expected directory: {EXPECTED_DIR}

Tests must be run from the branch_operations directory.

To fix:
  1. cd {EXPECTED_DIR}
  2. python3 run_tests.py

Or run pytest directly:
  /home/aipass/.venv/bin/pytest --cov=apps --cov-report=term --no-cov-on-fail

{'='*70}
"""
    print(error_msg)
    sys.exit(1)

# Run pytest with coverage
cmd = [
    "/home/aipass/.venv/bin/pytest",
    "--cov=apps",
    "--cov-report=term",
    "--no-cov-on-fail"
]

# Pass any additional arguments to pytest
if len(sys.argv) > 1:
    cmd.extend(sys.argv[1:])

sys.exit(subprocess.run(cmd).returncode)
