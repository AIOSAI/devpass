#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: refresh.py - Dashboard Refresh Handler
# Date: 2025-11-27
# Version: 0.1.0
# Category: aipass/handlers/dashboard
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-27): Initial handler - refresh dashboards from centrals
#
# CODE STANDARDS:
#   - Handler tier 3 - pure functions, raises exceptions
#   - Reads from central files, writes to branch dashboards
#   - No CLI imports, caller handles logging
# =============================================

"""
Dashboard Refresh Handler

Reads all .central.json files and writes to branch dashboards.
AIPASS owns all dashboards - services only maintain their central files.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Same-package imports allowed
from .operations import create_fresh_dashboard, save_dashboard

# Cross-handler imports for central reader
from ..central.reader import read_all_centrals

# Infrastructure
AIPASS_ROOT = Path.home()
BRANCH_REGISTRY = AIPASS_ROOT / "BRANCH_REGISTRY.json"


def _load_branch_paths() -> List[Path]:
    """
    Load all branch paths from registry.

    Returns:
        List of Path objects for each branch

    Raises:
        FileNotFoundError: If registry doesn't exist
    """
    if not BRANCH_REGISTRY.exists():
        raise FileNotFoundError(f"Branch registry not found: {BRANCH_REGISTRY}")

    data = json.loads(BRANCH_REGISTRY.read_text())
    branches = data.get("branches", [])

    paths = []
    for branch in branches:
        path_str = branch.get("path")
        if path_str:
            path = Path(path_str)
            if path.exists():
                paths.append(path)

    return paths


def _extract_flow_section(centrals: Dict, branch_name: str) -> Dict:
    """Extract flow section from PLANS.central.json"""
    plans_data = centrals.get("plans")
    if not plans_data:
        return {"managed_by": "flow", "active_plans": 0, "recently_closed": []}

    active_plans = plans_data.get("active_plans", [])

    # Count plans for this branch
    branch_plans = [p for p in active_plans if p.get("branch") == branch_name]

    # Get recently_closed from top-level (already limited to 5 by push_central)
    recently_closed_raw = plans_data.get("recently_closed", [])
    # Simplify for dashboard display (just id and subject)
    recently_closed = [
        {"plan_id": p.get("plan_id", ""), "subject": p.get("subject", "")}
        for p in recently_closed_raw[:5]
    ]

    return {
        "managed_by": "flow",
        "active_plans": len(branch_plans),
        "recently_closed": recently_closed
    }


def _extract_ai_mail_section(centrals: Dict, branch_name: str) -> Dict:
    """Extract ai_mail section from AI_MAIL.central.json"""
    mail_data = centrals.get("ai_mail")
    if not mail_data:
        return {"managed_by": "ai_mail", "unread": 0, "total": 0}

    branch_stats = mail_data.get("branch_stats", {})
    stats = branch_stats.get(branch_name, {"unread": 0, "total": 0})

    return {
        "managed_by": "ai_mail",
        "unread": stats.get("unread", 0),
        "total": stats.get("total", 0)
    }


def _extract_memory_bank_section(centrals: Dict, branch_path: Path) -> Dict:
    """
    Extract memory_bank section - LOCAL vectors for this branch.

    Each branch shows its own .chroma/ vector count, not the global count.
    Global stats are in MEMORY_BANK.central.json for reference only.
    """
    local_vectors = 0

    # Check for local .chroma directory
    chroma_dir = branch_path / ".chroma"
    if chroma_dir.exists():
        # Try to count vectors from local ChromaDB
        try:
            sqlite_file = chroma_dir / "chroma.sqlite3"
            if sqlite_file.exists():
                import sqlite3
                conn = sqlite3.connect(str(sqlite_file))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM embeddings")
                local_vectors = cursor.fetchone()[0]
                conn.close()
        except Exception:
            # If counting fails, just report 0
            pass

    return {
        "managed_by": "memory_bank",
        "vectors_stored": local_vectors,
        "notes": {}
    }


def _extract_devpulse_section(centrals: Dict, branch_name: str) -> Dict:
    """Extract devpulse section from DEVPULSE.central.json"""
    dp_data = centrals.get("devpulse")
    if not dp_data:
        return {"managed_by": "devpulse", "summary": {}}

    summaries = dp_data.get("branch_summaries", {})
    branch_summary = summaries.get(branch_name, {})

    return {
        "managed_by": "devpulse",
        "summary": branch_summary
    }


def _extract_bulletin_section(centrals: Dict) -> Dict:
    """Extract bulletin_board section from BULLETIN_BOARD_central.json"""
    bb_data = centrals.get("bulletin_board")
    if not bb_data:
        return {"managed_by": "aipass", "active_bulletins": [], "pending_ack": []}

    bulletins = bb_data.get("bulletins", [])
    active = [b for b in bulletins if b.get("active", False)]

    return {
        "managed_by": "aipass",
        "active_bulletins": active,
        "pending_ack": []
    }


def _calculate_quick_status(sections: Dict) -> Dict:
    """Calculate quick_status from sections (v2 schema)"""
    ai_mail = sections.get("ai_mail", {})
    flow = sections.get("flow", {})
    bulletin = sections.get("bulletin_board", {})

    # v2 schema: read "new" first, fall back to "unread" for backward compat
    new_mail = ai_mail.get("new", ai_mail.get("unread", 0))
    opened_mail = ai_mail.get("opened", 0)
    plans = flow.get("active_plans", 0)
    pending = len(bulletin.get("pending_ack", []))

    # Only new (unviewed) mail requires action
    action_required = new_mail > 0 or pending > 0

    parts = []
    if new_mail > 0:
        parts.append(f"{new_mail} new emails")
    if opened_mail > 0:
        parts.append(f"{opened_mail} opened")
    if plans > 0:
        parts.append(f"{plans} plans")
    if pending > 0:
        parts.append(f"{pending} bulletins")

    return {
        "new_mail": new_mail,
        "opened_mail": opened_mail,
        "active_plans": plans,
        "pending_bulletins": pending,
        "action_required": action_required,
        "summary": ", ".join(parts) if parts else "All clear"
    }


def refresh_all_dashboards() -> Dict:
    """
    Refresh all branch dashboards from central files.

    This is the main entry point. Reads all .central.json files,
    then writes to all branch DASHBOARD.local.json files.

    Returns:
        Dict with status, branches_updated, branches_failed, errors
    """
    errors = []
    branches_updated = 0
    branches_failed = 0

    # Read all central files
    centrals = read_all_centrals()

    # Get all branch paths
    try:
        branch_paths = _load_branch_paths()
    except Exception as e:
        return {
            "status": "error",
            "branches_updated": 0,
            "branches_failed": 0,
            "errors": [str(e)]
        }

    # Update each branch
    for branch_path in branch_paths:
        branch_name = branch_path.name.upper()

        try:
            # Create fresh dashboard
            dashboard = create_fresh_dashboard(branch_path)

            # Populate sections from centrals (order: bulletin, mail, memory, devpulse, flow at bottom)
            dashboard["sections"]["bulletin_board"] = _extract_bulletin_section(centrals)
            dashboard["sections"]["ai_mail"] = _extract_ai_mail_section(centrals, branch_name)
            dashboard["sections"]["memory_bank"] = _extract_memory_bank_section(centrals, branch_path)
            dashboard["sections"]["devpulse"] = _extract_devpulse_section(centrals, branch_name)
            dashboard["sections"]["flow"] = _extract_flow_section(centrals, branch_name)

            # Calculate quick status
            dashboard["quick_status"] = _calculate_quick_status(dashboard["sections"])

            # Save
            save_dashboard(branch_path, dashboard)
            branches_updated += 1

        except Exception as e:
            errors.append(f"{branch_name}: {str(e)}")
            branches_failed += 1

    # Determine status
    if branches_failed == 0:
        status = "success"
    elif branches_updated > 0:
        status = "partial"
    else:
        status = "error"

    return {
        "status": status,
        "branches_updated": branches_updated,
        "branches_failed": branches_failed,
        "errors": errors
    }


def refresh_single_dashboard(branch_path: Path) -> Dict:
    """
    Refresh a single branch's dashboard.

    Args:
        branch_path: Path to branch root

    Returns:
        Dict with status and any errors
    """
    centrals = read_all_centrals()
    branch_name = branch_path.name.upper()

    try:
        dashboard = create_fresh_dashboard(branch_path)

        dashboard["sections"]["bulletin_board"] = _extract_bulletin_section(centrals)
        dashboard["sections"]["ai_mail"] = _extract_ai_mail_section(centrals, branch_name)
        dashboard["sections"]["memory_bank"] = _extract_memory_bank_section(centrals, branch_path)
        dashboard["sections"]["devpulse"] = _extract_devpulse_section(centrals, branch_name)
        dashboard["sections"]["flow"] = _extract_flow_section(centrals, branch_name)

        dashboard["quick_status"] = _calculate_quick_status(dashboard["sections"])

        save_dashboard(branch_path, dashboard)

        return {"status": "success", "branch": branch_name}

    except Exception as e:
        return {"status": "error", "branch": branch_name, "error": str(e)}
