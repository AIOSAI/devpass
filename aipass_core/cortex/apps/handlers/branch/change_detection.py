#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: change_detection.py - Branch Change Detection Handler
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
Branch Change Detection Handler

Functions for detecting changes between template and branch:
- Rename detection using file IDs
- Addition detection
- Update detection
- Pruned file detection
"""

# Standard library imports
from pathlib import Path
from typing import Dict
import sys

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

TEMPLATE_DIR = AIPASS_ROOT / "cortex" / "templates" / "branch_template"

from cortex.apps.handlers.registry.ignore import load_ignore_patterns, should_ignore
from cortex.apps.handlers.registry.meta_ops import FILE_RENAMES


# =============================================================================
# TEMPLATE VALIDATION
# =============================================================================

def detect_unregistered_items(template_dir: Path, template_registry: Dict) -> Dict:
    """
    Detect files/directories in template that aren't registered in .template_registry.json

    Args:
        template_dir: Path to template directory
        template_registry: Template registry dict

    Returns:
        Dict with:
            - unregistered_files: List of file paths
            - unregistered_dirs: List of directory paths
    """
    unregistered = {
        "unregistered_files": [],
        "unregistered_dirs": []
    }

    # Get all registered paths
    registered_files = set()
    registered_dirs = set()

    for file_info in template_registry.get("files", {}).values():
        registered_files.add(file_info.get("path", file_info.get("current_name")))

    for dir_info in template_registry.get("directories", {}).values():
        registered_dirs.add(dir_info.get("path", dir_info.get("current_name")))

    # Load ignore patterns
    ignore_data = load_ignore_patterns(template_dir)
    ignore_files = ignore_data.get("ignore_files", [])
    ignore_patterns = ignore_data.get("ignore_patterns", [])

    # Scan template directory
    for item in template_dir.rglob("*"):
        # Skip ignored items
        if should_ignore(item, template_dir, ignore_files, ignore_patterns):
            continue

        # Get relative path
        rel_path = str(item.relative_to(template_dir))

        # Check if registered
        if item.is_file():
            if rel_path not in registered_files:
                unregistered["unregistered_files"].append(rel_path)
        elif item.is_dir():
            if rel_path not in registered_dirs:
                unregistered["unregistered_dirs"].append(rel_path)

    return unregistered


# =============================================================================
# CHANGE DETECTION
# =============================================================================

def detect_changes(
    template_registry: Dict,
    branch_meta: Dict | None,
    branch_dir: Path,
    branch_name: str,
    old_branch_tracking: Dict | None = None,
    trace: bool = False
) -> Dict:
    """
    Detect changes between template and branch using ID tracking

    Args:
        template_registry: Template registry dict
        branch_meta: Branch metadata dict (may be None for old branches)
        branch_dir: Path to branch directory
        branch_name: Branch name
        old_branch_tracking: OLD branch tracking (before PHASE 0 sync) for rename detection
        trace: Enable trace output

    Returns:
        Dict with:
            - renames: List[(old_name, new_name, file_id)]
            - additions: List[(template_name, file_id)]
            - pruned: List[(branch_name, file_id)]
            - updates: List[(name, file_id, old_hash, new_hash)]
    """
    changes = {
        "renames": [],
        "additions": [],
        "pruned": [],
        "updates": []
    }

    # Load ignore patterns from template
    ignore_data = load_ignore_patterns(TEMPLATE_DIR)
    ignore_files = ignore_data.get("ignore_files", [])
    ignore_patterns = ignore_data.get("ignore_patterns", [])

    if trace:
        pass  # Trace/debug output removed - handlers should not display output

    # If no branch_meta, can't detect renames - only additions
    if not branch_meta:
        # All template files are potential additions (but skip if already exist)
        for file_id, file_info in template_registry.get("files", {}).items():
            template_name = file_info["current_name"]

            # Check if file should be ignored
            template_file_path = TEMPLATE_DIR / template_name
            if should_ignore(template_file_path, TEMPLATE_DIR, ignore_files, ignore_patterns):
                continue  # Skip ignored files

            # Handle placeholder substitution
            if "{{BRANCH}}" in template_name:
                branch_upper = branch_name.upper().replace("-", "_")
                actual_name = template_name.replace("{{BRANCH}}", branch_upper)
            else:
                actual_name = template_name

            file_path = branch_dir / actual_name
            if not file_path.exists():
                changes["additions"].append((actual_name, file_id))

        return changes

    # Build lookups
    branch_file_tracking = branch_meta.get("file_tracking", {})
    template_ids = {}

    # Map template IDs to current names (filter out ignored files)
    for file_id, file_info in template_registry.get("files", {}).items():
        template_name = file_info["current_name"]
        template_file_path = TEMPLATE_DIR / template_name

        # Skip ignored files
        if should_ignore(template_file_path, TEMPLATE_DIR, ignore_files, ignore_patterns):
            continue

        template_ids[file_id] = template_name

    for dir_id, dir_info in template_registry.get("directories", {}).items():
        dir_name = dir_info["current_name"]
        template_dir_path = TEMPLATE_DIR / dir_name

        # Skip ignored directories
        if should_ignore(template_dir_path, TEMPLATE_DIR, ignore_files, ignore_patterns):
            continue

        template_ids[dir_id] = dir_name

    # Detect renames: ID exists in both, but template name changed
    # Use old_branch_tracking if provided (before PHASE 0 sync) for accurate rename detection
    branch_upper = branch_name.upper().replace("-", "_")
    tracking_for_renames = old_branch_tracking if old_branch_tracking else branch_file_tracking

    for file_id, template_name in template_ids.items():
        # Check if this ID exists in branch tracking (use old tracking if available)
        if file_id in tracking_for_renames:
            # Get current name and hash from branch (use OLD tracking for rename detection)
            branch_file_info = tracking_for_renames[file_id]
            branch_name_for_id = branch_file_info["current_name"]
            branch_hash = branch_file_info.get("content_hash")

            # Get template hash
            template_info = template_registry.get("files", {}).get(file_id) or template_registry.get("directories", {}).get(file_id)
            template_hash = template_info.get("content_hash") if template_info else None

            if branch_name_for_id != template_name:
                # Check if this is a placeholder substitution (not a rename)
                expected_branch_name = template_name
                if template_name in FILE_RENAMES:
                    # Apply the same substitution branch_new.py did
                    expected_branch_name = FILE_RENAMES[template_name].replace("{BRANCHNAME}", branch_upper)

                # If names match after substitution, skip (not a rename)
                if branch_name_for_id == expected_branch_name:
                    continue

                # LEGITIMATE RENAME - same ID, name changed in template
                # ID is source of truth - preserve ALL branch content during rename
                # Hash comparison REMOVED - template files are empty, branch files have data
                # Hash will ALWAYS differ (this is expected and correct!)

                # Apply FILE_RENAMES substitution to new name
                new_branch_name = template_name
                if template_name in FILE_RENAMES:
                    new_branch_name = FILE_RENAMES[template_name].format(BRANCHNAME=branch_upper, branchname=branch_upper.lower())

                changes["renames"].append((branch_name_for_id, new_branch_name, file_id))

    # Detect additions: ID in template but not in branch AND file doesn't exist
    # (If file exists but isn't tracked, it will be picked up during metadata regeneration)
    for file_id, template_name in template_ids.items():
        if file_id not in branch_file_tracking:
            # Get full path from template registry to check if file actually exists
            template_info = template_registry.get("files", {}).get(file_id) or template_registry.get("directories", {}).get(file_id)
            if template_info:
                file_path_str = template_info.get("path", template_name)
                branch_upper = branch_name.upper().replace("-", "_")
                branch_lower = branch_name.lower().replace("-", "_")

                # Handle placeholder substitution (same logic as meta_ops.py)
                if "{{BRANCH}}" in file_path_str:
                    file_path_str = file_path_str.replace("{{BRANCH}}", branch_upper)
                else:
                    # Check if filename (not full path) is in FILE_RENAMES
                    path_obj = Path(file_path_str)
                    filename_only = path_obj.name
                    if filename_only in FILE_RENAMES:
                        # Apply FILE_RENAMES substitution to full path
                        renamed = FILE_RENAMES[filename_only].replace("{BRANCHNAME}", branch_upper).replace("{branchname}", branch_lower)
                        file_path_str = str(path_obj.parent / renamed)

                file_path = branch_dir / file_path_str

                # Check if file exists - if not, try lowercase variant for backward compatibility
                if not file_path.exists() and "_json" in file_path_str:
                    # Try lowercase variant (for branches created before case fix)
                    lowercase_variant = file_path_str.replace(f"{branch_upper}_json", f"{branch_lower}_json")
                    lowercase_path = branch_dir / lowercase_variant
                    if lowercase_path.exists():
                        # File exists with lowercase variant - don't count as addition
                        continue

                # Only add as "addition" if file doesn't exist
                if not file_path.exists():
                    changes["additions"].append((template_name, file_id))

    # Detect updates: Content hash changed (same ID, same location, different content)
    for file_id, template_name in template_ids.items():
        if file_id in branch_file_tracking:
            # Get hashes from both registries
            template_file_info = template_registry.get("files", {}).get(file_id, {})
            branch_file_info = branch_file_tracking.get(file_id, {})

            template_hash = template_file_info.get("content_hash", "")
            branch_hash = branch_file_info.get("content_hash", "")

            # Check if content changed
            if template_hash and branch_hash and template_hash != branch_hash:
                branch_fname = branch_file_info.get("current_name", template_name)
                changes["updates"].append((branch_fname, file_id, branch_hash, template_hash))

    # Detect pruned: ID in branch but not in template
    for file_id, file_info in branch_file_tracking.items():
        if file_id not in template_ids:
            branch_fname = file_info["current_name"]
            changes["pruned"].append((branch_fname, file_id))

    return changes
