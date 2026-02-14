#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: list.py - D-PLAN listing handler
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
List Handler - D-PLAN Listing

Collects and returns D-PLAN data for display.
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

# NOTE: Handlers do NOT import Prax logger (per 3-tier standard)

from .status import extract_status

# =============================================================================
# CONFIGURATION
# =============================================================================

DEV_PLANNING_ROOT = Path.home() / "aipass_os" / "dev_central" / "dev_planning"


# =============================================================================
# HANDLER FUNCTIONS
# =============================================================================

def list_plans() -> Tuple[List[Dict[str, Any]], str]:
    """
    List all D-PLANs with their metadata

    Returns:
        Tuple of (plans_list, error_message)
        Each plan has: number, topic, date, status, file
    """
    plans = []

    if not DEV_PLANNING_ROOT.exists():
        return [], ""

    for plan_file in DEV_PLANNING_ROOT.glob("DPLAN-*.md"):
        match = re.match(r"DPLAN-(\d+)_(.+)_(\d{4}-\d{2}-\d{2})\.md", plan_file.name)
        if match:
            num = int(match.group(1))
            topic = match.group(2).replace('_', ' ')
            date = match.group(3)

            # Extract status from file content
            status = extract_status(plan_file)

            plans.append({
                "number": num,
                "topic": topic,
                "date": date,
                "status": status,
                "file": plan_file.name
            })

    # Sort by number
    plans.sort(key=lambda x: x["number"])

    return plans, ""
