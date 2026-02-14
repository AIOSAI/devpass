#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: operations.py - Dashboard Operations Handler
# Date: 2026-02-03
# Version: 0.2.0
# Category: handlers/dashboard
#
# CHANGELOG (Max 5 entries):
#   - v0.2.0 (2026-02-03): Fix empty file handling - treat empty JSON as new dashboard
#   - v0.1.0 (2025-11-24): Initial handler - dashboard load/save/update operations
#
# CODE STANDARDS:
#   - Pure business logic - no CLI imports
#   - Raises exceptions, caller handles logging
#   - Type hints on all functions
# =============================================

"""
Dashboard Operations Handler

Handles loading, saving, and updating dashboard files.
All business logic for dashboard file operations.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))


def get_dashboard_path(branch_path: Path) -> Path:
    """
    Get DASHBOARD.local.json path for a branch

    Args:
        branch_path: Path to branch root

    Returns:
        Path to dashboard file
    """
    return branch_path / "DASHBOARD.local.json"


def load_dashboard(branch_path: Path, template: Dict) -> Dict:
    """
    Load branch dashboard, creating if needed

    Args:
        branch_path: Path to branch root
        template: Dashboard template to use for new dashboards

    Returns:
        Dashboard data dict
    """
    dashboard_path = get_dashboard_path(branch_path)

    if dashboard_path.exists():
        content = dashboard_path.read_text().strip()
        # Handle empty or whitespace-only files (race condition protection)
        if not content:
            # File exists but is empty - treat as new dashboard
            new_dashboard = template.copy()
            new_dashboard["branch"] = branch_path.name.upper()
            return new_dashboard
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Corrupted file - recreate from template
            new_dashboard = template.copy()
            new_dashboard["branch"] = branch_path.name.upper()
            return new_dashboard
        # Ensure sections exist
        if "sections" not in data:
            data["sections"] = template["sections"].copy()
        return data

    # Return new dashboard from template
    new_dashboard = template.copy()
    new_dashboard["branch"] = branch_path.name.upper()
    return new_dashboard


def save_dashboard(branch_path: Path, data: Dict) -> bool:
    """
    Save branch dashboard

    Args:
        branch_path: Path to branch root
        data: Dashboard data to save

    Returns:
        True if saved successfully

    Raises:
        OSError: If file write fails
    """
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    dashboard_path = get_dashboard_path(branch_path)
    dashboard_path.write_text(json.dumps(data, indent=2))
    return True


def create_fresh_dashboard(branch_path: Path) -> Dict:
    """
    Create fresh dashboard with clean structure - NO preservation.

    This is the master function for creating/resetting dashboards.
    All services should call this, then populate their section.

    Args:
        branch_path: Path to branch root

    Returns:
        Fresh dashboard dict with warning and all sections
    """
    return {
        "_warning": "AUTO-GENERATED FILE - DO NOT MANUALLY EDIT. This file is 100% automated and will be overwritten. Services update their own sections.",
        "branch": branch_path.name.upper(),
        "last_updated": "",
        "quick_status": {"action_required": False},
        "sections": {
            "bulletin_board": {"managed_by": "aipass", "active_bulletins": [], "pending_ack": []},
            "ai_mail": {"managed_by": "ai_mail", "unread": 0, "total": 0},
            "memory_bank": {"managed_by": "memory_bank", "vectors_stored": 0, "notes": {}},
            "devpulse": {"managed_by": "devpulse", "summary": {}},
            "flow": {"managed_by": "flow", "active_plans": 0, "recently_closed": []}
        }
    }


def ensure_dashboard_structure(branch_path: Path) -> Dict:
    """
    Load dashboard, ensure all sections exist, return data.

    If dashboard doesn't exist, creates with default structure.
    If sections are missing, adds them with defaults.
    This allows services to always find their section ready.

    Args:
        branch_path: Path to the branch directory

    Returns:
        Dict with complete dashboard structure

    Raises:
        json.JSONDecodeError: If dashboard file is corrupted
    """
    dashboard_path = branch_path / "DASHBOARD.local.json"

    # Default structure - quick_status at top, flow at bottom (stacked output)
    default = {
        "branch": branch_path.name.upper(),
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "quick_status": {"action_required": False},
        "sections": {
            "bulletin_board": {"managed_by": "aipass", "active_bulletins": [], "pending_ack": []},
            "ai_mail": {"managed_by": "ai_mail", "unread": 0, "total": 0},
            "memory_bank": {"managed_by": "memory_bank", "vectors_stored": 0, "notes": {}},
            "devpulse": {"managed_by": "devpulse", "summary": {}},
            "flow": {"managed_by": "flow", "active_plans": 0, "recently_closed": []}
        }
    }

    if dashboard_path.exists():
        try:
            content = dashboard_path.read_text().strip()
            # Handle empty or whitespace-only files (race condition protection)
            if not content:
                return default
            data = json.loads(content)
            # Merge: keep existing data, add missing sections
            if "sections" not in data:
                data["sections"] = {}
            for section, content in default["sections"].items():
                if section not in data["sections"]:
                    data["sections"][section] = content
            return data
        except json.JSONDecodeError:
            # Re-raise to let caller handle
            raise
    else:
        return default


def update_section(
    branch_path: Path,
    section_name: str,
    section_data: Dict,
    template: Dict,
    calculate_status_func
) -> bool:
    """
    Update a specific section in branch dashboard

    Args:
        branch_path: Path to branch root
        section_name: Section to update (flow, ai_mail, etc)
        section_data: New data for section
        template: Dashboard template for fallback
        calculate_status_func: Function to calculate quick status

    Returns:
        True if updated successfully

    Raises:
        Exception: If load or save fails
    """
    dashboard = load_dashboard(branch_path, template)

    # Update only the specified section
    if "sections" not in dashboard:
        dashboard["sections"] = {}

    section_data["last_sync"] = datetime.now().strftime("%Y-%m-%d")
    dashboard["sections"][section_name] = section_data

    # Recalculate quick status
    dashboard["quick_status"] = calculate_status_func(dashboard["sections"])

    return save_dashboard(branch_path, dashboard)
