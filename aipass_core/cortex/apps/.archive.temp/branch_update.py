#!/usr/bin/env python3

# ===================AIPASS====================
# META DATA HEADER
# Name: branch_update.py - AIPass Branch Update System
# Date: 2025-10-29
# Version: 1.0.0
# Category: branch_operations
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-10-29): Initial standardized version - Added META header
# =============================================

"""
AIPass Branch Update System
Pushes template changes to existing branches while preserving all data

Usage:
    python3 branch_update.py /path/to/branch

Strategy:
    - Read existing branch JSON files
    - Read template JSON files
    - Deep merge: adopt new template structure + preserve existing data
    - Backup originals before modification
    - Update metadata.version to match template
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))

# Standard library imports
import argparse
import os
import json
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# AIPass infrastructure imports
from prax.apps.prax_logger import system_logger as logger

# Import from branch_lib
from branch_lib import (
    get_branch_name,
    detect_profile,
    get_git_repo,
    detect_unreplaced_placeholders,
    build_replacements_dict,
    apply_placeholder_replacements_to_dict,
)


# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

# Module root and JSON directory
MODULE_ROOT = Path(__file__).parent.parent
JSON_DIR = MODULE_ROOT / "branch_operations_json"

# Auto-create JSON directory
JSON_DIR.mkdir(exist_ok=True)

# 3-file JSON structure for branch_update module
CONFIG_FILE = JSON_DIR / "branch_update_config.json"
DATA_FILE = JSON_DIR / "branch_update_data.json"
LOG_FILE = JSON_DIR / "branch_update_log.json"

# Files that get renamed during branch creation (from branch_new.py)
# These placeholders are substituted with actual branch name
FILE_RENAMES = {
    "PROJECT.json": "{BRANCHNAME}.json",
    "LOCAL..json": "{BRANCHNAME}.local.json",
    "OBSERVATIONS.json": "{BRANCHNAME}.observations.json",
    "AI_MAIL.json": "{BRANCHNAME}.ai_mail.json",
    "BRANCH.ID.json": "{BRANCHNAME}.id.json",
}


# =============================================================================
# PATH GETTERS
# =============================================================================

def get_template_dir() -> Path:
    """
    Get path to template directory - single point of change for path migration

    Returns:
        Path to branch_template directory

    Note:
        Uses AIPASS_ROOT for dynamic path resolution.
        Template location: AIPASS_ROOT / "templates" / "branch_ template"
    """
    return AIPASS_ROOT / "templates" / "branch_ template"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log_operation(operation: str, success: bool, details: str = "", error: str = ""):
    """
    Log branch_update operations to module-specific log file

    Args:
        operation: Operation name (e.g., "branch_update_start")
        success: Whether operation succeeded
        details: Additional details about the operation
        error: Error message if operation failed
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "success": success,
        "details": details,
        "error": error
    }

    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []

    logs.append(log_entry)

    # Keep last 1000 entries
    if len(logs) > 1000:
        logs = logs[-1000:]

    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_update] Error saving log: {e}")


def load_config() -> Dict:
    """Load branch_update configuration"""
    default_config = {
        "enabled": True,
        "version": "1.0.0",
        "auto_backup": True,
        "require_confirmation": False,
        "max_log_entries": 1000
    }

    if not CONFIG_FILE.exists():
        save_config(default_config)
        return default_config

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[branch_update] Error loading config: {e}")
        return default_config


def save_config(config: Dict):
    """Save branch_update configuration"""
    try:
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_update] Error saving config: {e}")


def load_data() -> Dict:
    """Load branch_update runtime data"""
    default_data = {
        "created": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "operations_total": 0,
        "operations_successful": 0,
        "operations_failed": 0,
        "files_updated": 0
    }

    if not DATA_FILE.exists():
        return default_data

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[branch_update] Error loading data: {e}")
        return default_data


def save_data(data: Dict):
    """Save branch_update runtime data with auto timestamp"""
    data["last_updated"] = datetime.now().isoformat()
    try:
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_update] Error saving data: {e}")


# =============================================================================
# ID-BASED FILE TRACKING LOGIC
# =============================================================================

def load_template_registry() -> Optional[Dict]:
    """Load template_registry.json from template directory"""
    template_dir = get_template_dir()
    registry_path = template_dir / "template_registry.json"

    if not registry_path.exists():
        logger.warning(f"[branch_update] template_registry.json not found at {registry_path}")
        return None

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[branch_update] Error loading template_registry.json: {e}")
        return None


def load_branch_meta(branch_dir: Path) -> Optional[Dict]:
    """Load .branch_meta.json from branch directory"""
    meta_path = branch_dir / ".branch_meta.json"

    if not meta_path.exists():
        logger.info(f"[branch_update] .branch_meta.json not found - branch predates ID tracking system")
        return None

    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[branch_update] Error loading .branch_meta.json: {e}")
        return None


def detect_changes(template_registry: Dict, branch_meta: Optional[Dict], branch_dir: Path, branch_name: str) -> Dict:
    """
    Detect changes between template and branch using ID tracking

    Returns dict with:
        - renames: List[(old_name, new_name, file_id)]
        - additions: List[(template_name, file_id)]
        - pruned: List[(branch_name, file_id)]
    """
    changes = {
        "renames": [],
        "additions": [],
        "pruned": []
    }

    # If no branch_meta, can't detect renames - only additions
    if not branch_meta:
        logger.info("[branch_update] No branch_meta - treating all template files as potential additions")
        # All template files are potential additions (but skip if already exist)
        for file_id, file_info in template_registry.get("files", {}).items():
            template_name = file_info["current_name"]
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

    # Map template IDs to current names
    for file_id, file_info in template_registry.get("files", {}).items():
        template_ids[file_id] = file_info["current_name"]

    for dir_id, dir_info in template_registry.get("directories", {}).items():
        template_ids[dir_id] = dir_info["current_name"]

    # Reverse lookup: branch filename -> file_id
    branch_name_to_id = {name: fid for name, fid in branch_file_tracking.items()}

    # Detect renames: ID exists in both, but template name changed
    # But account for placeholder substitution (BRANCH.ID.json -> TEST_RENAME.id.json)
    branch_upper = branch_name.upper().replace("-", "_")

    for file_id, template_name in template_ids.items():
        # Find current branch name for this ID
        branch_name_for_id = None
        for branch_fname, branch_fid in branch_file_tracking.items():
            if branch_fid == file_id:
                branch_name_for_id = branch_fname
                break

        if branch_name_for_id and branch_name_for_id != template_name:
            # Check if this is a placeholder substitution (not a rename)
            # If template name matches FILE_RENAMES pattern, substitute and compare
            expected_branch_name = template_name
            if template_name in FILE_RENAMES:
                # Apply the same substitution branch_new.py did
                expected_branch_name = FILE_RENAMES[template_name].replace("{BRANCHNAME}", branch_upper)

            # If names match after substitution, skip (not a rename)
            if branch_name_for_id == expected_branch_name:
                continue

            # Template renamed this file
            changes["renames"].append((branch_name_for_id, template_name, file_id))

    # Detect additions: ID in template but not in branch
    for file_id, template_name in template_ids.items():
        if file_id not in branch_file_tracking.values():
            changes["additions"].append((template_name, file_id))

    # Detect pruned: ID in branch but not in template
    for branch_fname, file_id in branch_file_tracking.items():
        if file_id not in template_ids:
            changes["pruned"].append((branch_fname, file_id))

    return changes


def create_backup(branch_dir: Path) -> Optional[Path]:
    """
    Create full backup of branch directory before modifications

    Returns path to backup directory, or None on failure
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = branch_dir / ".backup" / f"pre_update_{timestamp}"

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files except .backup directory itself
        for item in branch_dir.iterdir():
            if item.name == ".backup":
                continue

            if item.is_file():
                shutil.copy2(item, backup_dir / item.name)
            elif item.is_dir():
                shutil.copytree(item, backup_dir / item.name, dirs_exist_ok=True)

        logger.info(f"[branch_update] Backup created at {backup_dir}")
        return backup_dir

    except Exception as e:
        logger.error(f"[branch_update] Backup creation failed: {e}")
        return None


def archive_pruned_file(branch_dir: Path, filename: str, file_id: str) -> bool:
    """
    Archive a pruned file to backup_system/pruned_files/

    Never deletes - always preserves
    Archives to centralized backup_system alongside deleted_branches/ and processed_plans/
    """
    source = branch_dir / filename
    if not source.exists():
        logger.warning(f"[branch_update] Pruned file not found: {filename}")
        return False

    # Archive to backup_system/pruned_files/{branch_name}/{timestamp}/
    branch_name = branch_dir.name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_base = AIPASS_ROOT / "backup_system" / "pruned_files"
    archive_dir = archive_base / branch_name / f"pruned_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    try:
        if source.is_file():
            shutil.copy2(source, archive_dir / filename)
        elif source.is_dir():
            shutil.copytree(source, archive_dir / filename, dirs_exist_ok=True)

        # Create metadata file
        metadata = {
            "branch_name": branch_name,
            "branch_path": str(branch_dir),
            "original_path": str(source),
            "file_id": file_id,
            "archived_at": datetime.now().isoformat(),
            "reason": "Pruned from template"
        }

        metadata_path = archive_dir / f"{filename}.metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Now safe to remove original
        if source.is_file():
            source.unlink()
        elif source.is_dir():
            shutil.rmtree(source)

        logger.info(f"[branch_update] Archived pruned file: {filename} -> {archive_dir}")
        return True

    except Exception as e:
        logger.error(f"[branch_update] Error archiving {filename}: {e}")
        return False


def execute_rename(branch_dir: Path, old_name: str, new_name: str, file_id: str) -> bool:
    """Execute a file/directory rename"""
    old_path = branch_dir / old_name
    new_path = branch_dir / new_name

    if not old_path.exists():
        logger.error(f"[branch_update] Rename source not found: {old_name}")
        return False

    if new_path.exists():
        logger.warning(f"[branch_update] Rename target already exists: {new_name} (skipping)")
        return False

    try:
        old_path.rename(new_path)
        logger.info(f"[branch_update] Renamed: {old_name} -> {new_name} (ID: {file_id})")
        return True
    except Exception as e:
        logger.error(f"[branch_update] Rename failed {old_name} -> {new_name}: {e}")
        return False


def copy_template_file(template_dir: Path, branch_dir: Path, filename: str, file_id: str, registry: Dict, branch_name: str) -> str:
    """
    Copy a new file from template to branch using path from registry

    Args:
        template_dir: Template directory path
        branch_dir: Branch directory path
        filename: Filename (may contain {{BRANCH}} placeholder)
        file_id: Template file ID
        registry: Template registry dict (to get path info)
        branch_name: Branch name for placeholder substitution

    Returns:
        "added" if file was added, "skipped" if already exists, "error" if failed
    """
    # Get the file's path from registry
    file_info = registry.get("files", {}).get(file_id)
    dir_info = registry.get("directories", {}).get(file_id)

    # Apply placeholder substitution to filename
    branch_upper = branch_name.upper().replace("-", "_")
    dest_filename = filename.replace("{{BRANCH}}", branch_upper)

    if file_info:
        # It's a file
        subpath = file_info.get("path", ".")
        # Apply placeholder substitution to path as well
        dest_subpath = subpath.replace("{{BRANCH}}", branch_upper) if subpath != "." else "."
        if subpath == ".":
            source = template_dir / filename
            dest = branch_dir / dest_filename
        else:
            source = template_dir / subpath / filename
            dest = branch_dir / dest_subpath / dest_filename
    elif dir_info:
        # It's a directory
        subpath = dir_info.get("path", ".")
        # Apply placeholder substitution to path as well
        dest_subpath = subpath.replace("{{BRANCH}}", branch_upper) if subpath != "." else "."
        if subpath == ".":
            source = template_dir / filename
            dest = branch_dir / dest_filename
        else:
            source = template_dir / subpath / filename
            dest = branch_dir / dest_subpath / dest_filename
    else:
        logger.error(f"[branch_update] File ID {file_id} not found in registry")
        return "error"

    if not source.exists():
        error_msg = f"Template file not found: {source.name}"
        logger.error(f"[branch_update] {error_msg}")
        return f"error:{error_msg}"  # Return error with reason

    if dest.exists():
        logger.info(f"[branch_update] File already exists: {dest.relative_to(branch_dir)} (skipping)")
        return "skipped"

    try:
        # Create parent directories if needed
        dest.parent.mkdir(parents=True, exist_ok=True)

        if source.is_file():
            shutil.copy2(source, dest)
        elif source.is_dir():
            shutil.copytree(source, dest, dirs_exist_ok=True)

        logger.info(f"[branch_update] Added: {dest.relative_to(branch_dir)} (ID: {file_id})")
        return "added"
    except Exception as e:
        error_msg = f"{e}"
        logger.error(f"[branch_update] Error copying {source} to {dest}: {e}")
        return f"error:{error_msg}"  # Return error with reason


# =============================================================================
# JSON MERGE LOGIC
# =============================================================================

def deep_merge(template: Any, existing: Any, path: str = "") -> Any:
    """
    Deep merge template structure with existing data

    Strategy:
    - Template defines structure (all fields, organization, defaults)
    - Existing data fills in values where present
    - New fields from template get defaults/empty values
    - Existing data preserved even if template structure changes

    Args:
        template: Template structure (provides fields and defaults)
        existing: Existing data (provides values to preserve)
        path: Current path in structure (for debugging)

    Returns:
        Merged result with template structure + existing values
    """
    # If existing is None/missing, use template
    if existing is None:
        return template

    # If types match, merge based on type
    if type(template) != type(existing):
        # Type mismatch - preserve existing data (it was valid before)
        return existing

    # Dict: merge keys
    if isinstance(template, dict):
        result = {}

        # Add all template keys (ensures new fields exist)
        for key in template.keys():
            if key in existing:
                # Recursively merge
                result[key] = deep_merge(template[key], existing[key], f"{path}.{key}")
            else:
                # New field - use template default
                result[key] = template[key]

        # Preserve existing keys not in template (user additions)
        for key in existing.keys():
            if key not in result:
                result[key] = existing[key]

        return result

    # List: preserve existing if not empty, otherwise use template
    elif isinstance(template, list):
        # If existing has data, preserve it
        if len(existing) > 0:
            return existing
        # If existing is empty and template has defaults, use template
        elif len(template) > 0:
            return template
        # Both empty
        else:
            return []

    # Scalar: preserve existing value
    else:
        return existing


def migrate_version(data: Dict[str, Any], template_version: str) -> Dict[str, Any]:
    """
    Migrate data to new version if needed

    Currently just updates version number.
    Future: Add version-specific migration logic here.

    Args:
        data: Merged data
        template_version: Target version from template

    Returns:
        Data with version updated
    """
    if "metadata" in data:
        old_version = data["metadata"].get("version", "unknown")
        data["metadata"]["version"] = template_version

        # Future version-specific migrations would go here:
        # if old_version == "1.0.0" and template_version == "1.1.0":
        #     # Perform 1.0.0 -> 1.1.0 migration
        #     pass

    return data


# =============================================================================
# FILE OPERATIONS
# =============================================================================

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file, return None if doesn't exist"""
    if not path.exists():
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ERROR loading {path.name}: {e}")
        return None


def save_json(path: Path, data: Dict[str, Any]) -> bool:
    """Save JSON file with pretty formatting"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"  ERROR saving {path.name}: {e}")
        return False


def backup_file(source: Path, backup_dir: Path, timestamp: str) -> Optional[Path]:
    """Create timestamped backup of file"""
    if not source.exists():
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{source.name}.{timestamp}.backup"

    try:
        shutil.copy2(source, backup_path)
        return backup_path
    except Exception as e:
        print(f"  ERROR backing up {source.name}: {e}")
        return None


# =============================================================================
# UPDATE LOGIC
# =============================================================================

def update_branch_file(
    branch_file: Path,
    template_file: Path,
    backup_dir: Path,
    timestamp: str,
    file_label: str,
    replacements: Dict[str, str]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Update single branch JSON file from template

    Returns:
        (success, change_summary_dict)
    """
    print(f"\n{file_label}:")

    # Load existing and template
    existing = load_json(branch_file)
    template = load_json(template_file)

    if template is None:
        print(f"  SKIP: Template not found")
        return True, {"action": "skipped_template_missing"}

    # If existing doesn't exist, create from template
    if existing is None:
        print(f"  CREATE: New file from template")
        try:
            populated = apply_placeholder_replacements_to_dict(template, replacements)
        except ValueError as exc:
            print(f"  ERROR: {exc}")
            return False, {}

        if save_json(branch_file, populated):
            return True, {"action": "created", "fields_added": len(template.keys())}
        else:
            return False, {}

    # Backup existing file
    backup_path = backup_file(branch_file, backup_dir, timestamp)
    if backup_path:
        print(f"  BACKUP: {backup_path.name}")
    else:
        print(f"  WARNING: Backup failed")

    # Get versions
    old_version = existing.get("metadata", {}).get("version", "unknown")
    new_version = template.get("metadata", {}).get("version", "unknown")

    # Deep merge
    merged = deep_merge(template, existing)

    # Migrate version
    merged = migrate_version(merged, new_version)

    # Apply placeholder replacements
    try:
        merged = apply_placeholder_replacements_to_dict(merged, replacements)
    except ValueError as exc:
        print(f"  ERROR: {exc}")
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, branch_file)
            print(f"  RESTORED: From backup")
        return False, {}

    # Count changes
    new_fields = count_new_fields(template, existing)
    preserved_data = count_preserved_data(existing)

    # Save merged result
    if save_json(branch_file, merged):
        print(f"  UPDATE: Success")
        if old_version != new_version:
            print(f"  VERSION: {old_version} → {new_version}")
        if new_fields > 0:
            print(f"  ADDED: {new_fields} new field(s)")
        print(f"  PRESERVED: {preserved_data} existing value(s)")

        return True, {
            "action": "updated",
            "old_version": old_version,
            "new_version": new_version,
            "fields_added": new_fields,
            "data_preserved": preserved_data
        }
    else:
        print(f"  ERROR: Save failed")
        # Restore from backup
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, branch_file)
            print(f"  RESTORED: From backup")
        return False, {}


def count_new_fields(template: Dict, existing: Dict, path: str = "") -> int:
    """Count fields in template that don't exist in existing"""
    if not isinstance(template, dict) or not isinstance(existing, dict):
        return 0

    count = 0
    for key in template.keys():
        if key not in existing:
            count += 1
        elif isinstance(template[key], dict):
            count += count_new_fields(template[key], existing[key], f"{path}.{key}")

    return count


def count_preserved_data(data: Any, path: str = "") -> int:
    """Count non-empty values in data structure"""
    if isinstance(data, dict):
        count = 0
        for key, value in data.items():
            count += count_preserved_data(value, f"{path}.{key}")
        return count
    elif isinstance(data, list):
        if len(data) > 0:
            return 1  # Count non-empty lists as 1 preserved item
        return 0
    else:
        # Scalar value
        if data is not None and data != "":
            return 1
        return 0


# =============================================================================
# BRANCH METADATA GENERATION
# =============================================================================

def generate_branch_meta_for_existing_branch(target_path: Path, branch_name: str, template_registry: Dict) -> Dict | None:
    """
    Generate .branch_meta.json for an existing branch that predates ID tracking

    Similar to branch_new.py's generate_branch_meta_json() but adapted for existing branches.
    Scans the branch directory and maps existing files to template IDs.

    Args:
        target_path: Path to existing branch
        branch_name: Branch name for placeholder substitution
        template_registry: Loaded template registry

    Returns:
        Dict with metadata structure, or None if failed
    """
    # Build reverse lookup: template_filename -> template_id
    template_name_to_id = {}

    # Map files
    for file_id, file_info in template_registry.get("files", {}).items():
        template_name_to_id[file_info["current_name"]] = file_id

    # Map directories
    for dir_id, dir_info in template_registry.get("directories", {}).items():
        template_name_to_id[dir_info["current_name"]] = dir_id

    # Build mapping: actual_filename -> template_id
    file_tracking = {}
    branch_upper = branch_name.upper().replace("-", "_")

    # Map files (handle {{BRANCH}} placeholder substitution)
    for template_name, template_id in template_name_to_id.items():
        # Handle placeholder patterns
        if "{{BRANCH}}" in template_name:
            actual_name = template_name.replace("{{BRANCH}}", branch_upper)
        else:
            # Check if this file gets renamed by FILE_RENAMES pattern
            if template_name in FILE_RENAMES:
                actual_name = FILE_RENAMES[template_name].replace("{BRANCHNAME}", branch_upper)
            else:
                actual_name = template_name

        # Check if file/directory exists in branch
        file_path = target_path / actual_name
        if file_path.exists():
            file_tracking[actual_name] = template_id

    # Create metadata structure
    meta_data = {
        "template_version": template_registry.get("metadata", {}).get("version", "1.0.0"),
        "branch_created": "unknown",  # Can't determine for existing branches
        "last_updated": datetime.now().isoformat(),
        "file_tracking": file_tracking
    }

    logger.info(f"[branch_update] Generated metadata for existing branch with {len(file_tracking)} tracked files")
    return meta_data


# =============================================================================
# MAIN UPDATE PROCESS
# =============================================================================

def update_branch(target_path: Path, dry_run: bool = False) -> bool:
    """
    Update branch from template using ID-based file tracking

    Strategy:
        1. Load template_registry.json and .branch_meta.json
        2. Detect changes (renames, additions, pruned files)
        3. Create backup before any modifications
        4. Show preview of changes
        5. Ask for confirmation (unless dry_run)
        6. Execute changes (renames, additions, archival)
        7. Update .branch_meta.json

    Args:
        target_path: Path to branch directory
        dry_run: If True, show preview without executing

    Returns:
        True if successful
    """
    logger.info(f"Branch update initiated for: {target_path} (dry_run={dry_run})")

    # Log operation start
    log_operation(
        operation="branch_update_start",
        success=True,
        details=f"Initiating branch update for: {target_path} (dry_run={dry_run})"
    )

    # Validate target path
    if not target_path.exists():
        logger.error(f"Target path does not exist: {target_path}")
        print(f"❌ ERROR: Target path does not exist: {target_path}")
        return False

    if not target_path.is_dir():
        logger.error(f"Target path is not a directory: {target_path}")
        print(f"❌ ERROR: Target path is not a directory: {target_path}")
        return False

    # Get branch info
    branch_name = get_branch_name(target_path)
    print(f"\n=== Branch Update System (ID-Based Tracking) ===")
    print(f"Branch: {branch_name}")
    print(f"Path: {target_path}")
    if dry_run:
        print("Mode: DRY RUN (preview only)")
    print()

    # Load template registry
    template_registry = load_template_registry()
    if not template_registry:
        print(f"❌ ERROR: Could not load template_registry.json")
        return False

    template_version = template_registry.get("metadata", {}).get("version", "unknown")
    print(f"Template version: {template_version}")

    # Load branch metadata (may not exist for old branches)
    branch_meta = load_branch_meta(target_path)
    if branch_meta:
        branch_version = branch_meta.get("template_version", "unknown")
        print(f"Branch version: {branch_version}")
    else:
        print("Branch version: N/A (predates ID tracking)")
    print()

    # Detect changes
    print("Detecting changes...")
    changes = detect_changes(template_registry, branch_meta, target_path, branch_name)

    renames = changes["renames"]
    additions = changes["additions"]
    pruned = changes["pruned"]

    # Show preview
    print("\n" + "="*60)
    print("CHANGE PREVIEW")
    print("="*60)

    if renames:
        print(f"\n📝 RENAMES ({len(renames)}):")
        for old_name, new_name, file_id in renames:
            print(f"  {old_name} → {new_name} (ID: {file_id})")
    else:
        print("\n📝 RENAMES: None")

    if additions:
        print(f"\n➕ ADDITIONS ({len(additions)}):")
        for filename, file_id in additions:
            print(f"  + {filename} (ID: {file_id})")
    else:
        print("\n➕ ADDITIONS: None")

    if pruned:
        print(f"\n🗄️  PRUNED FILES (will be archived) ({len(pruned)}):")
        for filename, file_id in pruned:
            print(f"  → backup_system/pruned_files/: {filename} (ID: {file_id})")
    else:
        print("\n🗄️  PRUNED FILES: None")

    total_changes = len(renames) + len(additions) + len(pruned)

    if total_changes == 0:
        print("\n✅ No changes detected - branch is up to date!")
        return True

    print(f"\nTotal changes: {total_changes}")

    # Dry run mode - stop here
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes executed")
        return True

    # Ask for confirmation
    print("\n" + "="*60)
    response = input("Execute these changes? (yes/no): ").strip().lower()
    if response not in ["yes", "y"]:
        print("❌ Update cancelled by user")
        return False

    # Create backup
    print("\nCreating backup...")
    backup_dir = create_backup(target_path)
    if not backup_dir:
        print("❌ ERROR: Backup creation failed - aborting update")
        return False
    print(f"✅ Backup created: {backup_dir}")

    # Execute changes
    print("\n" + "="*60)
    print("EXECUTING CHANGES")
    print("="*60)

    success_count = 0
    skip_count = 0
    error_count = 0
    template_dir = get_template_dir()

    # Execute renames first
    if renames:
        print(f"\nExecuting {len(renames)} rename(s)...")
        for old_name, new_name, file_id in renames:
            if execute_rename(target_path, old_name, new_name, file_id):
                success_count += 1
                print(f"  ✅ {old_name} → {new_name}")
            else:
                error_count += 1
                print(f"  ❌ Failed: {old_name} → {new_name}")

    # Execute additions
    if additions:
        print(f"\nAdding {len(additions)} new file(s)...")
        for filename, file_id in additions:
            result = copy_template_file(template_dir, target_path, filename, file_id, template_registry, branch_name)
            if result == "added":
                success_count += 1
                print(f"  ✅ Added: {filename}")
            elif result == "skipped":
                skip_count += 1
                print(f"  ℹ️  Skipped: {filename} (already exists)")
            else:  # error (format: "error:reason")
                error_count += 1
                error_reason = result.split(":", 1)[1] if ":" in result else "unknown error"
                print(f"  ❌ Failed: {filename} - {error_reason}")

    # Archive pruned files
    if pruned:
        print(f"\nArchiving {len(pruned)} pruned file(s)...")
        for filename, file_id in pruned:
            if archive_pruned_file(target_path, filename, file_id):
                success_count += 1
                print(f"  ✅ Archived: {filename}")
            else:
                error_count += 1
                print(f"  ❌ Failed: {filename}")

    # Update/Create .branch_meta.json
    print("\nUpdating branch metadata...")
    meta_path = target_path / ".branch_meta.json"

    if branch_meta:
        # Existing metadata - regenerate file tracking and update timestamp
        updated_meta = generate_branch_meta_for_existing_branch(target_path, branch_name, template_registry)
        if updated_meta:
            # Preserve branch_created if it exists
            if "branch_created" in branch_meta and branch_meta["branch_created"] != "unknown":
                updated_meta["branch_created"] = branch_meta["branch_created"]
            branch_meta = updated_meta
        else:
            # Fallback: just update timestamp
            branch_meta["last_updated"] = datetime.now().isoformat()
    else:
        # No metadata exists - create it for old branch
        print("  ℹ️  Branch predates ID tracking - generating metadata...")
        branch_meta = generate_branch_meta_for_existing_branch(target_path, branch_name, template_registry)
        if not branch_meta:
            print("  ⚠️  Metadata generation failed")
            logger.warning(f"Could not generate .branch_meta.json for {branch_name}")

    # Save metadata
    if branch_meta:
        meta_existed = meta_path.exists()  # Check before writing
        try:
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(branch_meta, f, indent=2, ensure_ascii=False)
            action = "updated" if meta_existed else "created"
            print(f"  ✅ Metadata {action} ({len(branch_meta.get('file_tracking', {}))} files tracked)")
        except Exception as e:
            logger.error(f"Error saving .branch_meta.json: {e}")
            print(f"  ⚠️  Metadata save failed: {e}")

    # Summary
    print("\n" + "="*60)
    print("UPDATE SUMMARY")
    print("="*60)
    print(f"✅ Added/Updated: {success_count}")
    if skip_count > 0:
        print(f"ℹ️  Skipped: {skip_count} (already exist)")
    if error_count > 0:
        print(f"❌ Errors: {error_count}")
    print(f"📦 Backup: {backup_dir}")

    success = error_count == 0
    if success:
        logger.info(f"Branch update complete: {branch_name}")
        log_operation(
            operation="branch_update_complete",
            success=True,
            details=f"Branch '{branch_name}' updated successfully. {success_count} added, {skip_count} skipped, 0 errors"
        )
        print("\n✅ Update complete!")
    else:
        logger.error(f"Branch update completed with errors: {branch_name}")
        log_operation(
            operation="branch_update_failed",
            success=False,
            details=f"Branch '{branch_name}' update had {error_count} error(s)",
            error=f"{error_count} operations failed"
        )
        print("\n⚠️  Update completed with errors - check backup if needed")

    return success


# =============================================================================
# BATCH OPERATIONS
# =============================================================================

def update_all_branches(dry_run: bool = False) -> Tuple[int, int]:
    """
    Update all branches from BRANCH_REGISTRY.json

    Args:
        dry_run: If True, preview only

    Returns:
        Tuple of (success_count, total_count)
    """
    # Load branch registry
    registry_path = Path.home() / "BRANCH_REGISTRY.json"
    if not registry_path.exists():
        print(f"❌ ERROR: BRANCH_REGISTRY.json not found at {registry_path}")
        return (0, 0)

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    except Exception as e:
        print(f"❌ ERROR: Could not load BRANCH_REGISTRY.json: {e}")
        return (0, 0)

    branches = registry.get("branches", [])
    total_branches = len(branches)

    print(f"\n{'='*60}")
    print(f"BATCH UPDATE - {total_branches} branches")
    print(f"{'='*60}")
    if dry_run:
        print("Mode: DRY RUN (preview only)\n")

    success_count = 0
    failed_branches = []

    for i, branch_info in enumerate(branches, 1):
        branch_path = Path(branch_info["path"])
        branch_name = branch_info["name"]

        print(f"\n[{i}/{total_branches}] {branch_name}")
        print(f"Path: {branch_path}")
        print("-" * 60)

        if not branch_path.exists():
            print(f"⚠️  Branch directory not found - skipping")
            failed_branches.append((branch_name, "Directory not found"))
            continue

        try:
            success = update_branch(branch_path, dry_run=dry_run)
            if success:
                success_count += 1
            else:
                failed_branches.append((branch_name, "Update failed"))
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed_branches.append((branch_name, str(e)))
            logger.error(f"Batch update error for {branch_name}: {e}")

    # Summary
    print(f"\n{'='*60}")
    print("BATCH UPDATE SUMMARY")
    print(f"{'='*60}")
    print(f"Total branches: {total_branches}")
    print(f"✅ Successful: {success_count}")
    if failed_branches:
        print(f"❌ Failed: {len(failed_branches)}")
        print("\nFailed branches:")
        for branch_name, reason in failed_branches:
            print(f"  - {branch_name}: {reason}")

    return (success_count, total_branches)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='AIPass Branch Update - ID-based template updates with rename support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
FEATURES:
  - ID-based file tracking (detects renames vs new files)
  - Safe rename operations (preserves content)
  - Automatic archival of pruned files (never deletes)
  - Full backup before any modifications
  - Preview mode (--dry-run)
  - Batch update all branches (--all)

EXAMPLES:
  # Single branch
  python3 branch_update.py /home/aipass/analytics
  python3 branch_update.py /home/aipass/backup_system --dry-run

  # Batch update all branches
  python3 branch_update.py --all --dry-run   # Preview all
  python3 branch_update.py --all             # Update all

WORKFLOW:
  1. Load template_registry.json and .branch_meta.json
  2. Detect changes (renames, additions, pruned files)
  3. Show preview
  4. Create backup (unless dry-run)
  5. Execute changes with confirmation
  6. Archive pruned files to backup_system/pruned_files/
        """
    )
    parser.add_argument('branch_path', nargs='?', help='Path to branch directory to update (omit with --all)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without executing (no backup, no modifications)')
    parser.add_argument('--all', action='store_true',
                        help='Update all branches from BRANCH_REGISTRY.json')

    args = parser.parse_args()

    # Validate arguments
    if args.all and args.branch_path:
        print("❌ ERROR: Cannot specify both branch_path and --all")
        sys.exit(1)

    if not args.all and not args.branch_path:
        print("❌ ERROR: Must specify either branch_path or --all")
        parser.print_help()
        sys.exit(1)

    # Initialize JSON infrastructure
    config = load_config()
    data = load_data()

    try:
        if args.all:
            # Batch update all branches
            success_count, total_count = update_all_branches(dry_run=args.dry_run)

            # Update statistics (but not for dry-run)
            if not args.dry_run:
                data["operations_total"] += total_count
                data["operations_successful"] += success_count
                data["operations_failed"] += (total_count - success_count)
                data["files_updated"] += success_count
                save_data(data)

            sys.exit(0 if success_count == total_count else 1)
        else:
            # Single branch update
            target_path = Path(args.branch_path).resolve()
            success = update_branch(target_path, dry_run=args.dry_run)

            # Update statistics (but not for dry-run)
            if not args.dry_run:
                data["operations_total"] += 1
                if success:
                    data["operations_successful"] += 1
                    data["files_updated"] += 1
                else:
                    data["operations_failed"] += 1
                save_data(data)

            sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
