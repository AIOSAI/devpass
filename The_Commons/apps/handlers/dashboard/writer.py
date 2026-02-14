#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: writer.py - Dashboard File Handler
# Date: 2026-02-08
# Version: 1.0.0
# Category: the_commons/handlers/dashboard
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-08): Initial creation - dashboard read/write for commons_activity
#
# CODE STANDARDS:
#   - Handler: pure business logic, NO orchestration
#   - Reads/writes DASHBOARD.local.json for branches
#   - Importable by Commons modules
# =============================================

"""
Dashboard File Handler

Reads and writes DASHBOARD.local.json files for branches.
Handles the commons_activity section that shows catchup data
on each branch's dashboard.

Usage:
    from handlers.dashboard.writer import write_commons_activity

    write_commons_activity("SEED", activity_dict)
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("commons.dashboard")

# Constants
REGISTRY_PATH = Path("/home/aipass/BRANCH_REGISTRY.json")


def _find_branch_path(branch_name: str) -> Optional[Path]:
    """
    Look up a branch's directory path from BRANCH_REGISTRY.json.

    Args:
        branch_name: The branch name to look up (e.g., "SEED")

    Returns:
        Path to the branch directory, or None if not found
    """
    if not REGISTRY_PATH.exists():
        return None

    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    for branch in registry.get("branches", []):
        if branch["name"] == branch_name:
            return Path(branch["path"])

    return None


def write_commons_activity(branch_name: str, activity: Dict[str, Any]) -> bool:
    """
    Write the commons_activity section to a branch's DASHBOARD.local.json.

    Args:
        branch_name: The branch name whose dashboard to update
        activity: The commons_activity dict to write

    Returns:
        True if written successfully, False otherwise
    """
    found_path = _find_branch_path(branch_name)
    if not found_path:
        return False

    dashboard_file = found_path / "DASHBOARD.local.json"
    if not dashboard_file.exists():
        return False

    try:
        dashboard_data = json.loads(dashboard_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    if "sections" not in dashboard_data:
        dashboard_data["sections"] = {}

    dashboard_data["sections"]["commons_activity"] = activity

    try:
        dashboard_file.write_text(
            json.dumps(dashboard_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return True
    except OSError:
        return False
