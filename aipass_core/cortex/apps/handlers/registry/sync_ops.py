#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: sync_ops.py - Registry Synchronization Operations Handler
# Date: 2025-11-09
# Version: 1.0.0
# Category: cortex/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-09): Phase 1 - Handler infrastructure created
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Registry Synchronization Operations Handler

Functions for synchronizing branch registry with template:
- Synchronization need detection
- Registry structure synchronization
- File tracking snapshot preservation
"""

# Standard library imports
from pathlib import Path
from typing import Dict
from datetime import datetime
import sys

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from cortex.apps.handlers.branch.reconcile import calculate_file_hash


# =============================================================================
# SYNCHRONIZATION OPERATIONS
# =============================================================================

def needs_synchronization(
    branch_meta: Dict | None,
    template_registry: Dict
) -> tuple[bool, str]:
    """
    Check if branch registry needs synchronization with template.

    Args:
        branch_meta: Branch metadata dict
        template_registry: Template registry dict

    Returns:
        Tuple of (needs_sync: bool, reason: str)
    """
    if branch_meta is None:
        return (True, "No branch_meta.json found")

    if "file_tracking" not in branch_meta:
        return (True, "Missing file_tracking structure")

    if branch_meta.get("file_tracking"):
        # Check if using old format (name→id instead of id→file_info)
        first_value = next(iter(branch_meta["file_tracking"].values()))
        if isinstance(first_value, str):
            return (True, "Old registry format detected (name→id mapping)")
        else:
            # Check if registry IDs match template (structure sync)
            branch_ids = set(branch_meta["file_tracking"].keys())
            template_ids = set(template_registry.get("files", {}).keys()) | set(template_registry.get("directories", {}).keys())

            missing_ids = template_ids - branch_ids

            if missing_ids:
                return (True, f"Registry structure outdated ({len(missing_ids)} IDs missing from branch)")

    return (False, "")


def synchronize_registry(
    branch_meta: Dict | None,
    template_registry: Dict,
    branch_dir: Path,
    trace: bool = False
) -> Dict:
    """
    Synchronize branch registry structure with template.

    Replaces branch file_tracking with current template structure while
    preserving existing hashes where files haven't changed.

    Args:
        branch_meta: Branch metadata dict to update
        template_registry: Template registry dict
        branch_dir: Path to branch directory
        trace: Enable detailed logging

    Returns:
        Updated branch_meta with synchronized file_tracking
    """
    # Create new file_tracking from template structure
    new_file_tracking = {}

    for file_id, file_info in template_registry.get("files", {}).items():
        template_path = file_info.get("path", "")
        template_name = file_info.get("current_name", "")

        # Check if file exists in branch
        branch_file_path = branch_dir / template_path

        if branch_file_path.exists() and branch_file_path.is_file():
            # File exists - calculate current hash
            current_hash = calculate_file_hash(branch_file_path)

            new_file_tracking[file_id] = {
                "current_name": template_name,
                "path": template_path,
                "content_hash": current_hash
            }
        # If file doesn't exist, don't add to tracking (reconciliation will handle)

    # Do the same for directories
    for dir_id, dir_info in template_registry.get("directories", {}).items():
        template_path = dir_info.get("path", "")
        template_name = dir_info.get("current_name", "")

        branch_dir_path = branch_dir / template_path

        if branch_dir_path.exists() and branch_dir_path.is_dir():
            new_file_tracking[dir_id] = {
                "current_name": template_name,
                "path": template_path,
                "content_hash": ""  # Directories have empty hash
            }

    # Replace entire file_tracking structure
    if branch_meta is None:
        branch_meta = {
            "metadata": {
                "version": template_registry.get("metadata", {}).get("version", "1.0.0"),
                "last_updated": datetime.now().date().isoformat()
            },
            "file_tracking": new_file_tracking
        }
    else:
        branch_meta["file_tracking"] = new_file_tracking

    return branch_meta


def preserve_tracking_snapshot(branch_meta: Dict | None) -> Dict:
    """
    Create deep copy of file_tracking for rename detection.

    Args:
        branch_meta: Branch metadata dict

    Returns:
        Deep copy of file_tracking dict, or empty dict if none exists
    """
    if not branch_meta or "file_tracking" not in branch_meta:
        return {}

    return branch_meta["file_tracking"].copy()
