#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: status.py - Dashboard Status Calculation Handler
# Date: 2025-11-24
# Version: 0.1.0
# Category: handlers/dashboard
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-24): Initial handler - status calculation and branch paths
#
# CODE STANDARDS:
#   - Pure business logic - no CLI imports
#   - Raises exceptions, caller handles logging
#   - Type hints on all functions
# =============================================

"""
Dashboard Status Handler

Handles status calculations and branch path resolution.
All business logic for dashboard status operations.
"""

import json
from pathlib import Path
from typing import Dict, List

AIPASS_ROOT = Path.home()
BRANCH_REGISTRY = AIPASS_ROOT / "BRANCH_REGISTRY.json"


def calculate_quick_status(sections: Dict) -> Dict:
    """
    Calculate quick status from all sections

    Args:
        sections: All dashboard sections

    Returns:
        Quick status dict with summary data
    """
    ai_mail = sections.get("ai_mail", {})
    # v2 schema: read "new" first, fall back to "unread" for backward compat
    new_mail = ai_mail.get("new", ai_mail.get("unread", 0))
    opened_mail = ai_mail.get("opened", 0)
    plans = sections.get("flow", {}).get("active_plans", 0)
    bulletins = len(sections.get("bulletin_board", {}).get("pending", []))

    # Only new (unviewed) mail requires action
    action_required = new_mail > 0 or bulletins > 0

    summary_parts = []
    if new_mail:
        summary_parts.append(f"{new_mail} new emails")
    if opened_mail:
        summary_parts.append(f"{opened_mail} opened")
    if plans:
        summary_parts.append(f"{plans} plans")
    if bulletins:
        summary_parts.append(f"{bulletins} bulletins")

    return {
        "new_mail": new_mail,
        "opened_mail": opened_mail,
        "active_plans": plans,
        "pending_bulletins": bulletins,
        "action_required": action_required,
        "summary": ", ".join(summary_parts) if summary_parts else "All clear"
    }


def get_branch_paths() -> List[Path]:
    """
    Get all branch paths from registry

    Returns:
        List of branch paths

    Raises:
        FileNotFoundError: If branch registry doesn't exist
        json.JSONDecodeError: If registry is corrupted
    """
    if not BRANCH_REGISTRY.exists():
        raise FileNotFoundError(f"Branch registry not found: {BRANCH_REGISTRY}")

    data = json.loads(BRANCH_REGISTRY.read_text())
    return [Path(b.get("path", "")) for b in data.get("branches", [])]
