#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: propagation.py - Bulletin Propagation Handler
# Date: 2025-11-24
# Version: 0.1.0
# Category: aipass/handlers/bulletin
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-24): Initial handler - bulletin propagation to branches
#
# CODE STANDARDS:
#   - Handler tier 3 - pure functions, raises exceptions
#   - Same-package imports allowed (storage.py)
#   - Domain organized propagation operations
# =============================================

"""
Bulletin Propagation Handler

Handles propagation of bulletins to branch dashboards.
Pure functions with proper error handling.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Same-package imports allowed
from .storage import load_bulletins

# Cross-handler imports for shared utilities
from ..dashboard.operations import create_fresh_dashboard, save_dashboard

# Infrastructure
AIPASS_ROOT = Path.home()

# Paths
BRANCH_REGISTRY = AIPASS_ROOT / "BRANCH_REGISTRY.json"


def _load_branch_registry() -> List[Dict]:
    """
    Load branch registry

    Returns:
        List of branch dicts with name, path, status

    Raises:
        FileNotFoundError: If registry doesn't exist
        json.JSONDecodeError: If registry is malformed
    """
    if not BRANCH_REGISTRY.exists():
        raise FileNotFoundError(f"Branch registry not found: {BRANCH_REGISTRY}")

    data = json.loads(BRANCH_REGISTRY.read_text())
    return data.get("branches", [])


def _load_dashboard(branch_path: Path) -> Dict:
    """
    Load existing dashboard or create new if missing.

    Preserves other services' sections (ai_mail, flow, etc).
    Only bulletin_board section will be updated by propagation.

    Args:
        branch_path: Path to branch root

    Returns:
        Dashboard data dict (existing or new)
    """
    dashboard_path = branch_path / "DASHBOARD.local.json"

    if dashboard_path.exists():
        try:
            content = dashboard_path.read_text().strip()
            if not content:
                return create_fresh_dashboard(branch_path)
            data = json.loads(content)
            # Ensure sections dict exists
            if "sections" not in data:
                data["sections"] = {}
            # Ensure bulletin_board section exists (we'll update it)
            if "bulletin_board" not in data["sections"]:
                data["sections"]["bulletin_board"] = {
                    "managed_by": "aipass",
                    "active_bulletins": [],
                    "pending_ack": []
                }
            return data
        except json.JSONDecodeError:
            # Invalid JSON - create fresh
            pass

    # No dashboard or invalid - create fresh
    return create_fresh_dashboard(branch_path)




def _filter_active_bulletins(bulletins: List[Dict]) -> List[Dict]:
    """
    Filter bulletins to only active ones

    Args:
        bulletins: List of all bulletins

    Returns:
        List of active bulletins only
    """
    return [b for b in bulletins if b.get("active", False)]


def propagate_to_branches() -> Dict:
    """
    Propagate active bulletins to branch dashboards

    This function will:
    1. Load active bulletins from central storage
    2. Load branch registry to find all branches
    3. For each branch, update its DASHBOARD.local.json
    4. Add/update bulletin_board section with active bulletins

    Returns:
        Dict with keys:
            - status (str): Operation status (success/partial/error)
            - branches_updated (int): Number of branches successfully updated
            - branches_failed (int): Number of branches that failed to update
            - errors (List[str]): List of error messages (if any)

    Raises:
        Exception: If critical operations fail (registry load, bulletin load)
    """
    errors = []
    branches_updated = 0
    branches_failed = 0

    # Load branch registry
    try:
        branches = _load_branch_registry()
    except Exception as e:
        raise Exception(f"Failed to load branch registry: {e}")

    # Load bulletins
    try:
        bulletin_data = load_bulletins()
        all_bulletins = bulletin_data.get("bulletins", [])
        active_bulletins = _filter_active_bulletins(all_bulletins)
    except Exception as e:
        raise Exception(f"Failed to load bulletins: {e}")

    # Update each branch dashboard
    for branch in branches:
        branch_name = branch.get("name", "UNKNOWN")
        branch_path_str = branch.get("path")

        if not branch_path_str:
            errors.append(f"{branch_name}: No path in registry")
            branches_failed += 1
            continue

        branch_path = Path(branch_path_str)

        if not branch_path.exists():
            errors.append(f"{branch_name}: Path does not exist: {branch_path}")
            branches_failed += 1
            continue

        try:
            # Load dashboard
            dashboard = _load_dashboard(branch_path)

            # Update bulletin_board section ONLY
            if "sections" not in dashboard:
                dashboard["sections"] = {}

            dashboard["sections"]["bulletin_board"] = {
                "managed_by": "aipass",
                "active_bulletins": active_bulletins,
                "pending_ack": []
            }

            # Save dashboard using dashboard handler
            save_dashboard(branch_path, dashboard)
            branches_updated += 1

        except Exception as e:
            errors.append(f"{branch_name}: {str(e)}")
            branches_failed += 1

    # Determine overall status
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


def check_and_propagate() -> Dict:
    """
    Check for active bulletins and propagate if any exist.

    This is the entry point called by Prax logger on startup.
    Wraps propagate_to_branches() with silent failure handling.

    Returns:
        Dict with propagation results or skip status
    """
    try:
        # Load bulletins to check if any are active
        bulletin_data = load_bulletins()
        bulletins = bulletin_data.get("bulletins", [])
        active = [b for b in bulletins if b.get("active", False)]

        if not active:
            return {"status": "skipped", "reason": "No active bulletins"}

        # Propagate active bulletins
        return propagate_to_branches()
    except Exception:
        # Silent failure - don't break the calling process
        return {"status": "error", "reason": "Propagation check failed"}
