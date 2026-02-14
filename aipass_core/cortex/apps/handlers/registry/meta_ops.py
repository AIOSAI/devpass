#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: meta_ops.py - Metadata Operations Handler
# Date: 2025-11-04
# Version: 1.0.0
# Category: cortex/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-04): Metadata operations for branch updates
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Metadata Operations Handler

Functions for branch and template metadata:
- Load template registry
- Load branch metadata
- Generate metadata for existing branches
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple, List
import sys

# =============================================================================
# CONSTANTS
# =============================================================================

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

TEMPLATE_DIR = AIPASS_ROOT / "cortex" / "templates" / "branch_template"

# Files that get renamed during branch creation
FILE_RENAMES = {
    "PROJECT.json": "{BRANCHNAME}.json",
    "LOCAL.json": "{BRANCHNAME}.local.json",
    "OBSERVATIONS.json": "{BRANCHNAME}.observations.json",
    "AI_MAIL.json": "{BRANCHNAME}.ai_mail.json",
    "BRANCH.ID.json": "{BRANCHNAME}.id.json",
    "BRANCH.py": "{branchname}.py",
}


# =============================================================================
# REGISTRY VALIDATION
# =============================================================================

def validate_template_registry(template_registry: Dict, template_dir: Path) -> list:
    """
    Validate template registry against actual filesystem

    Checks if files/directories listed in registry actually exist at those paths.
    Skips files in FILE_RENAMES as they're expected to not exist (renamed during branch creation).

    Args:
        template_registry: Loaded template registry
        template_dir: Path to template directory

    Returns:
        List of mismatch dicts: {"id": str, "registry_path": str, "issue": str, "actual_path": str}
    """
    mismatches = []

    # Check files
    for file_id, file_info in template_registry.get("files", {}).items():
        registry_path = file_info.get("path", file_info["current_name"])
        file_path = template_dir / registry_path

        if not file_path.exists():
            # Skip files that are in FILE_RENAMES (expected to not exist as-is)
            filename = Path(registry_path).name
            if filename in FILE_RENAMES:
                continue

            # Try to find actual location
            actual_path = None

            # Check if dotted/undotted version exists
            if filename.startswith('.'):
                alt_path = template_dir / registry_path[1:]  # Remove dot
            else:
                alt_path = template_dir / ('.' + registry_path)  # Add dot

            if alt_path.exists():
                actual_path = str(alt_path.relative_to(template_dir))

            mismatches.append({
                "id": file_id,
                "type": "file",
                "registry_path": registry_path,
                "issue": "path_not_found",
                "actual_path": actual_path
            })

    # Check directories
    for dir_id, dir_info in template_registry.get("directories", {}).items():
        registry_path = dir_info.get("path", dir_info["current_name"])
        dir_path = template_dir / registry_path

        if not dir_path.exists():
            # Try to find actual location
            actual_path = None
            dirname = Path(registry_path).name

            # Check if dotted/undotted version exists
            if dirname.startswith('.'):
                alt_path = template_dir / registry_path[1:]  # Remove dot
            else:
                alt_path = template_dir / ('.' + registry_path)  # Add dot

            if alt_path.exists():
                actual_path = str(alt_path.relative_to(template_dir))

            mismatches.append({
                "id": dir_id,
                "type": "directory",
                "registry_path": registry_path,
                "issue": "path_not_found",
                "actual_path": actual_path
            })

    return mismatches


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_file_hash(file_path: Path) -> Tuple[str, Optional[str]]:
    """
    Calculate SHA-256 hash of file content

    Args:
        file_path: Path to file

    Returns:
        Tuple of (hash string, warning message or None)
        Hash is first 12 characters for readability, empty string if not a file
    """
    if not file_path.is_file():
        return ("", None)

    try:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        # Return first 12 chars of hash (enough for uniqueness)
        return (sha256.hexdigest()[:12], None)
    except Exception as e:
        return ("", f"Could not hash {file_path.name}: {e}")


# =============================================================================
# TEMPLATE REGISTRY OPERATIONS
# =============================================================================

def load_template_registry() -> Tuple[Optional[Dict], Optional[str]]:
    """
    Load .template_registry.json from template directory

    Returns:
        Tuple of (registry dict or None, error message or None)
    """
    registry_path = TEMPLATE_DIR / ".template_registry.json"

    if not registry_path.exists():
        return (None, f".template_registry.json not found at {registry_path}")

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            return (json.load(f), None)
    except Exception as e:
        return (None, f"Error loading .template_registry.json: {e}")


# =============================================================================
# BRANCH METADATA OPERATIONS
# =============================================================================

def load_branch_meta(branch_dir: Path) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Load .branch_meta.json from branch directory

    Args:
        branch_dir: Path to branch directory

    Returns:
        Tuple of (metadata dict or None, error message or None)
        None metadata is normal for old branches that predate ID tracking
    """
    meta_path = branch_dir / ".branch_meta.json"

    if not meta_path.exists():
        # This is normal for old branches that predate ID tracking
        return (None, None)

    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            return (json.load(f), None)
    except Exception as e:
        return (None, f"Error loading .branch_meta.json: {e}")


def heal_branch_meta(
    branch_dir: Path,
    branch_meta: Optional[Dict],
    template_registry: Dict,
    template_version: str
) -> Tuple[Optional[Dict], List[str]]:
    """
    Auto-heal branch metadata if format is outdated or missing

    Handles:
    - Missing .branch_meta.json (returns None - caller should regenerate)
    - Old format: name→id mapping (auto-converts to new id→file_info format)
    - Corrupted/invalid data (regenerates from scratch)

    Args:
        branch_dir: Path to branch directory
        branch_meta: Loaded metadata (or None if missing)
        template_registry: Template registry for regeneration
        template_version: Current template version

    Returns:
        Tuple of (healed metadata dict or None, list of change messages)
    """
    changes = []

    # If no metadata exists, signal caller to regenerate
    if branch_meta is None:
        changes.append("No branch_meta - treating all template files as potential additions")
        return (None, changes)

    # Check if file_tracking exists and needs healing
    if "file_tracking" not in branch_meta:
        changes.append("Missing file_tracking - regenerating metadata")
        return (None, changes)

    file_tracking = branch_meta.get("file_tracking", {})
    if not file_tracking:
        # Empty tracking is fine
        return (branch_meta, changes)

    # Detect old format: first value is string (name→id) vs dict (id→file_info)
    first_value = next(iter(file_tracking.values()))

    if isinstance(first_value, str):
        # OLD FORMAT DETECTED - Auto-heal to new format AND remap IDs
        changes.append("Old branch_meta format detected - auto-healing")

        # Build hash→template_id lookup for ID remapping
        hash_to_template_id = {}
        for file_id, file_info in template_registry.get("files", {}).items():
            if file_info.get("content_hash"):
                hash_to_template_id[file_info["content_hash"]] = file_id

        # Old format: {"filename.py": "f001"}
        # New format: {"f001": {"current_name": "filename.py", "content_hash": "abc123"}}

        # Invert the mapping: name→id becomes id→file_info
        healed_tracking = {}
        id_remapping = {}  # Track old_id → new_id for reporting

        for filename, old_file_id in file_tracking.items():
            # Calculate content hash if file exists
            file_path = branch_dir / filename
            content_hash = None
            if file_path.exists() and file_path.is_file():
                content_hash, warning = calculate_file_hash(file_path)
                if warning:
                    changes.append(f"Hash warning: {warning}")

            # Try to remap ID using content hash
            new_file_id = old_file_id  # Default to old ID

            # Skip remapping for empty files (hash: e3b0c44298fc = empty file)
            # Multiple empty files share same hash, causing false matches
            if content_hash and content_hash != "e3b0c44298fc" and content_hash in hash_to_template_id:
                new_file_id = hash_to_template_id[content_hash]
                if new_file_id != old_file_id:
                    id_remapping[old_file_id] = new_file_id

            healed_tracking[new_file_id] = {
                "current_name": filename,
                "content_hash": content_hash
            }

        # Update metadata with healed format
        branch_meta["file_tracking"] = healed_tracking

        # Save healed version
        success, error = save_branch_meta(branch_dir, branch_meta)
        if not success and error:
            changes.append(f"Save error: {error}")

        changes.append("Auto-healed old format successfully")
        return (branch_meta, changes)

    # Format is already correct - but check if IDs need remapping (silent check)

    # Build hash→template_id lookup
    hash_to_template_id = {}
    for file_id, file_info in template_registry.get("files", {}).items():
        if file_info.get("content_hash"):
            hash_to_template_id[file_info["content_hash"]] = file_id

    # Check each tracked file for ID reassignment
    remapped_tracking = {}
    id_remapping = {}

    for current_id, file_info in file_tracking.items():
        content_hash = file_info.get("content_hash")

        # Try to remap ID using content hash
        new_id = current_id  # Default to current ID

        # Skip remapping for empty files (hash: e3b0c44298fc = empty file)
        # Multiple empty files share same hash, causing false matches
        if content_hash and content_hash != "e3b0c44298fc" and content_hash in hash_to_template_id:
            new_id = hash_to_template_id[content_hash]
            if new_id != current_id:
                id_remapping[current_id] = new_id

        remapped_tracking[new_id] = file_info

    # If IDs were remapped, save updated metadata (silent)
    if id_remapping:
        branch_meta["file_tracking"] = remapped_tracking
        branch_meta["last_updated"] = datetime.now().date().isoformat()
        success, error = save_branch_meta(branch_dir, branch_meta)
        if not success and error:
            changes.append(f"Save error during ID remap: {error}")
        else:
            changes.append(f"Remapped {len(id_remapping)} file IDs")
    # else: All IDs current - no action needed (silent)

    # Format is already correct
    return (branch_meta, changes)


def save_branch_meta(branch_dir: Path, metadata: Dict) -> Tuple[bool, Optional[str]]:
    """
    Save .branch_meta.json to branch directory

    Args:
        branch_dir: Path to branch directory
        metadata: Metadata dict to save

    Returns:
        Tuple of (success status, error message or None)
    """
    meta_path = branch_dir / ".branch_meta.json"

    try:
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        return (True, None)
    except Exception as e:
        return (False, f"Error saving .branch_meta.json: {e}")


def generate_branch_meta_for_existing_branch(
    target_path: Path,
    branch_name: str,
    template_registry: Dict
) -> Optional[Dict]:
    """
    Generate .branch_meta.json for existing branch that predates ID tracking

    Scans the branch directory and maps existing files to template IDs with content hashes.

    Args:
        target_path: Path to existing branch
        branch_name: Branch name for placeholder substitution
        template_registry: Loaded template registry

    Returns:
        Dict with metadata structure, or None if failed
    """
    # Build reverse lookup: template_filename -> (template_id, file_info)
    template_name_to_info = {}

    # Map files
    for file_id, file_info in template_registry.get("files", {}).items():
        template_name_to_info[file_info["current_name"]] = (file_id, file_info)

    # Map directories
    for dir_id, dir_info in template_registry.get("directories", {}).items():
        template_name_to_info[dir_info["current_name"]] = (dir_id, dir_info)

    # Build file tracking with new structure: file_id -> {current_name, path, content_hash}
    file_tracking = {}
    branch_upper = branch_name.upper().replace("-", "_")

    # Map files (handle {{BRANCH}} placeholder substitution)
    for template_name, (template_id, template_info) in template_name_to_info.items():
        # Get full path from template registry (includes subdirectories)
        full_path = template_info.get("path", template_name)

        # Handle placeholder patterns
        if "{{BRANCH}}" in full_path:
            actual_path = full_path.replace("{{BRANCH}}", branch_upper)
        else:
            # Check if this file gets renamed by FILE_RENAMES pattern
            if template_name in FILE_RENAMES:
                actual_path = FILE_RENAMES[template_name].replace("{BRANCHNAME}", branch_upper)
            else:
                actual_path = full_path

        # Check if file/directory exists in branch (use full path with subdirectories)
        file_path = target_path / actual_path
        if file_path.exists():
            # Calculate content hash for files (not directories)
            content_hash = ""
            if file_path.is_file():
                content_hash, _ = calculate_file_hash(file_path)  # Ignore warning in this context

            # Use new structure matching .template_registry.json
            # current_name: just the filename
            # path: full relative path including subdirectories
            actual_name = Path(actual_path).name
            file_tracking[template_id] = {
                "current_name": actual_name,
                "path": actual_path,  # Relative path from branch root (includes subdirs)
                "content_hash": content_hash,
                "has_branch_placeholder": "{{BRANCH}}" in template_name or "{{BRANCHNAME}}" in template_name
            }

    # Create metadata structure
    meta_data = {
        "template_version": template_registry.get("metadata", {}).get("version", "1.0.0"),
        "branch_created": "unknown",  # Can't determine for existing branches
        "last_updated": datetime.now().date().isoformat(),
        "file_tracking": file_tracking
    }

    return meta_data
