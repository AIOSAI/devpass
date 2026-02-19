#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: dashboard.py - DPLAN Dashboard Push Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: devpulse/handlers/plan
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial version - dashboard + central push per FPLAN-0355
#
# CONNECTS:
#   - registry.py (reads registry for DPLAN counts)
#   - DASHBOARD.local.json (writes devpulse section)
#   - DEVPULSE.central.json at AI_CENTRAL (writes dplan_summary)
#
# CODE STANDARDS:
#   - Handler independence: NO cross-domain imports
#   - NO Prax logging (per 3-tier: modules log, handlers don't)
#   - Pure business logic only
# ==============================================

"""
Dashboard Handler - DPLAN Dashboard Integration

Pushes DPLAN summary data to DASHBOARD.local.json and DEVPULSE.central.json.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

# NOTE: Handlers do NOT import Prax logger (per 3-tier standard)

from .registry import load_registry

# =============================================================================
# CONFIGURATION
# =============================================================================

DEVPULSE_ROOT = Path.home() / "aipass_os" / "dev_central" / "devpulse"
DASHBOARD_FILE = DEVPULSE_ROOT / "DASHBOARD.local.json"
CENTRAL_FILE = Path.home() / "aipass_os" / "AI_CENTRAL" / "DEVPULSE.central.json"


# =============================================================================
# HANDLER FUNCTIONS
# =============================================================================

def compute_dplan_summary() -> Dict[str, Any]:
    """
    Compute DPLAN summary counts from registry.

    Returns:
        Dictionary with total_plans, by_status, by_tag breakdowns
    """
    registry = load_registry()
    plans = registry.get("plans", {})

    by_status: Dict[str, int] = {}
    by_tag: Dict[str, int] = {}

    for plan in plans.values():
        status = plan.get("status", "unknown")
        tag = plan.get("tag", "")

        by_status[status] = by_status.get(status, 0) + 1
        if tag:
            by_tag[tag] = by_tag.get(tag, 0) + 1

    return {
        "total_plans": len(plans),
        "by_status": by_status,
        "by_tag": by_tag,
        "last_updated": datetime.now().isoformat()
    }


def push_dplan_to_dashboard(summary: Dict[str, Any]) -> bool:
    """
    Update DASHBOARD.local.json devpulse section with DPLAN data.

    Args:
        summary: DPLAN summary from compute_dplan_summary()

    Returns:
        True if successful
    """
    if not DASHBOARD_FILE.exists():
        return False

    try:
        with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
            dashboard = json.load(f)

        dashboard.setdefault("sections", {})
        dashboard["sections"]["devpulse"] = {
            "managed_by": "devpulse",
            "summary": summary
        }
        dashboard["last_updated"] = datetime.now().strftime("%Y-%m-%d")

        with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)

        return True
    except Exception:
        return False


def push_dplan_to_central(summary: Dict[str, Any]) -> bool:
    """
    Add DPLAN counts to DEVPULSE.central.json alongside branch summaries.

    Args:
        summary: DPLAN summary from compute_dplan_summary()

    Returns:
        True if successful
    """
    if not CENTRAL_FILE.exists():
        return False

    try:
        with open(CENTRAL_FILE, 'r', encoding='utf-8') as f:
            central = json.load(f)

        central["dplan_summary"] = summary
        central["last_updated"] = datetime.now().isoformat()

        with open(CENTRAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(central, f, indent=2, ensure_ascii=False)

        return True
    except Exception:
        return False


def push_all() -> Dict[str, Any]:
    """
    Compute DPLAN summary and push to both dashboard and central.

    Returns:
        The computed summary dict
    """
    summary = compute_dplan_summary()
    push_dplan_to_dashboard(summary)
    push_dplan_to_central(summary)
    return summary
