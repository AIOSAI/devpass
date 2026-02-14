#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: crud.py - Bulletin CRUD Handler
# Date: 2025-11-24
# Version: 0.1.0
# Category: aipass/handlers/bulletin
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-24): Initial handler - bulletin CRUD operations
#
# CODE STANDARDS:
#   - Handler tier 3 - pure functions, raises exceptions
#   - Same-package imports allowed (storage.py)
#   - Domain organized CRUD operations
# =============================================

"""
Bulletin CRUD Handler

Handles Create, Read, Update operations for bulletins.
Pure functions with proper error handling.
"""

from datetime import datetime
from typing import Dict, List, Optional

# Same-package imports allowed
from .storage import load_bulletins, save_bulletins


def create_bulletin(
    subject: str,
    message: str,
    priority: str = "normal",
    bulletin_type: str = "announcement",
    targets: Optional[List[str]] = None
) -> Dict:
    """
    Create a new bulletin

    Args:
        subject: Bulletin subject line
        message: Bulletin content/body
        priority: Priority level (low/normal/high/critical)
        bulletin_type: Type of bulletin (announcement/patch/action_required)
        targets: List of target branches (None = all branches)

    Returns:
        Dict with keys:
            - success (bool): True if created successfully
            - id (str): Generated bulletin ID (if successful)
            - error (str): Error message (if failed)

    Raises:
        json.JSONDecodeError: If bulletin data is corrupted
        OSError: If save operation fails
    """
    data = load_bulletins()
    bulletins = data.get("bulletins", [])

    # Generate unique ID
    existing_ids = [b.get("id", "") for b in bulletins]
    counter = 1
    while f"BULLETIN_{counter:04d}" in existing_ids:
        counter += 1

    bulletin_id = f"BULLETIN_{counter:04d}"

    # Create bulletin object
    new_bulletin = {
        "id": bulletin_id,
        "subject": subject,
        "message": message,
        "priority": priority,
        "type": bulletin_type,
        "targets": targets if targets else "all",
        "created": datetime.now().isoformat(),
        "status": "active",
        "acknowledgements": []
    }

    # Add to collection
    bulletins.append(new_bulletin)
    data["bulletins"] = bulletins

    # Save
    save_bulletins(data)
    return {"success": True, "id": bulletin_id}


def list_bulletins(status: str = "active") -> List[Dict]:
    """
    List bulletins filtered by status

    Args:
        status: Filter by status (active/completed/all)

    Returns:
        List of bulletin dictionaries matching the filter

    Raises:
        json.JSONDecodeError: If bulletin data is corrupted
    """
    data = load_bulletins()
    bulletins = data.get("bulletins", [])

    if status == "all":
        return bulletins

    return [b for b in bulletins if b.get("status") == status]


def acknowledge_bulletin(bulletin_id: str, branch: str) -> Dict:
    """
    Record branch acknowledgement of a bulletin

    Args:
        bulletin_id: The bulletin ID to acknowledge
        branch: Branch name acknowledging the bulletin

    Returns:
        Dict with keys:
            - success (bool): True if operation succeeded
            - acknowledged (bool): True if newly acknowledged (if success=True)
            - reason (str): Why not acknowledged (if acknowledged=False)
            - error (str): Error message (if success=False)
            - completed (bool): True if bulletin became completed (optional)

    Raises:
        json.JSONDecodeError: If bulletin data is corrupted
        OSError: If save operation fails
    """
    data = load_bulletins()
    bulletins = data.get("bulletins", [])

    # Find bulletin
    for bulletin in bulletins:
        if bulletin.get("id") == bulletin_id:
            acks = bulletin.get("acknowledgements", [])

            # Check if already acknowledged
            if branch in acks:
                return {
                    "success": True,
                    "acknowledged": False,
                    "reason": "Already acknowledged"
                }

            # Add acknowledgement
            acks.append(branch)
            bulletin["acknowledgements"] = acks

            # Check if all targets have acknowledged
            targets = bulletin.get("targets", "all")
            completed = False
            if targets != "all" and isinstance(targets, list):
                if set(acks) >= set(targets):
                    bulletin["status"] = "completed"
                    completed = True

            # Save changes
            save_bulletins(data)
            return {
                "success": True,
                "acknowledged": True,
                "completed": completed
            }

    return {"success": False, "error": "Bulletin not found"}
