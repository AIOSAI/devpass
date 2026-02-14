#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: counter.py - D-PLAN counter management
# Date: 2025-12-02
# Version: 1.0.0
# Category: devpulse/handlers/plan
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-12-02): Extracted from dev_flow.py module
#
# CODE STANDARDS:
#   - Handler independence: NO cross-domain imports
#   - NO Prax logging (per 3-tier: modules log, handlers don't)
#   - Pure business logic only
# ==============================================

"""
Counter Handler - D-PLAN Numbering

Manages sequential D-PLAN numbers by scanning existing files.
Counter file is a cache, not source of truth.
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
import json
import re
from pathlib import Path
from typing import Tuple

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

# NOTE: Handlers do NOT import Prax logger (per 3-tier standard)
# Modules do the logging, handlers return errors

# =============================================================================
# CONFIGURATION
# =============================================================================

DEV_PLANNING_ROOT = Path.home() / "aipass_os" / "dev_central" / "dev_planning"
COUNTER_FILE = DEV_PLANNING_ROOT / "counter.json"


# =============================================================================
# HANDLER FUNCTIONS
# =============================================================================

def get_next_plan_number() -> Tuple[int, str]:
    """
    Get next D-PLAN number

    Strategy: Scan files for highest number, increment by 1.
    Counter file is cache, not source of truth.

    Returns:
        Tuple of (next_number, error_message)
        Error message is empty on success
    """
    # Scan existing plans to find highest number
    highest = 0

    if DEV_PLANNING_ROOT.exists():
        for plan_file in DEV_PLANNING_ROOT.glob("DPLAN-*.md"):
            match = re.match(r"DPLAN-(\d+)", plan_file.name)
            if match:
                num = int(match.group(1))
                if num > highest:
                    highest = num

    next_num = highest + 1

    # Update counter cache (best effort, return error for logging by module)
    cache_error = ""
    try:
        COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(COUNTER_FILE, 'w', encoding='utf-8') as f:
            json.dump({"next_number": next_num + 1}, f, indent=2)
    except Exception as e:
        cache_error = f"Cache update failed: {e}"

    # Return number even if cache failed (cache is not critical)
    return next_num, cache_error
