#!/usr/bin/env python3

# ===================AIPASS====================
# META DATA HEADER
# Name: json_ops.py - JSON Operations Handler
# Date: 2025-11-04
# Version: 1.0.0
# Category: cortex/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-04): JSON operations for branch updates
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
JSON Operations Handler

Functions for JSON file operations and merging:
- Load/save JSON files
- Deep merge template + existing data
- Version migration
- Field counting for change reporting
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List
from fnmatch import fnmatch
import sys

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))


# =============================================================================
# FILE OPERATIONS
# =============================================================================

def prepare_json_backup_dir(branch_dir: Path) -> Path:
    """
    Prepare JSON backup directory (single 'json_latest' that overwrites)

    Args:
        branch_dir: Path to branch directory

    Returns:
        Path to JSON backup directory
    """
    json_backup_dir = branch_dir / ".backup" / "json_latest"

    # Clean old JSON backup if exists
    if json_backup_dir.exists():
        shutil.rmtree(json_backup_dir)

    json_backup_dir.mkdir(parents=True, exist_ok=True)
    return json_backup_dir


def load_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Load JSON file with error handling

    Args:
        path: Path to JSON file

    Returns:
        Tuple of (dict or None, error message or None)
    """
    if not path.exists():
        return (None, None)

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return (json.load(f), None)
    except Exception as e:
        return (None, f"Error loading {path.name}: {e}")


def save_json(path: Path, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Save JSON file with pretty formatting

    Args:
        path: Path to save JSON file
        data: Data to save

    Returns:
        Tuple of (success status, error message or None)
    """
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return (True, None)
    except Exception as e:
        return (False, f"Error saving {path.name}: {e}")


def backup_json_file(source: Path, backup_dir: Path, timestamp: str) -> Tuple[Optional[Path], str]:
    """
    Create timestamped backup of JSON file

    Args:
        source: Source file to backup
        backup_dir: Directory to store backup
        timestamp: Timestamp string for backup filename

    Returns:
        Tuple of (backup path or None, status message)
    """
    if not source.exists():
        return (None, f"Source file not found: {source.name}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{source.name}.{timestamp}.backup"

    try:
        shutil.copy2(source, backup_path)
        return (backup_path, f"Backup created: {backup_path.name}")
    except Exception as e:
        return (None, f"Error backing up {source.name}: {e}")


# =============================================================================
# DEEP MERGE
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

    # If types mismatch, preserve existing data (it was valid before)
    if type(template) != type(existing):
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


# =============================================================================
# VERSION MIGRATION
# =============================================================================

def migrate_version(data: Dict[str, Any], template_version: str) -> Dict[str, Any]:
    """
    Migrate data to new version

    Currently just updates version number.
    Future: Add version-specific migration logic here.

    Args:
        data: Merged data
        template_version: Target version from template

    Returns:
        Data with version updated
    """
    if "metadata" in data:
        data["metadata"]["version"] = template_version

        # Future version-specific migrations would go here:
        # if old_version == "1.0.0" and template_version == "1.1.0":
        #     # Perform 1.0.0 -> 1.1.0 migration
        #     pass

    return data


# =============================================================================
# FIELD COUNTING (for change reporting)
# =============================================================================

def count_new_fields(template: Dict, existing: Dict, path: str = "") -> int:
    """
    Count fields in template that don't exist in existing

    Args:
        template: Template structure
        existing: Existing data
        path: Current path (for debugging)

    Returns:
        Number of new fields
    """
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
    """
    Count non-empty values in data structure

    Args:
        data: Data structure to count
        path: Current path (for debugging)

    Returns:
        Number of non-empty values
    """
    if isinstance(data, dict):
        count = 0
        for key, value in data.items():
            count += count_preserved_data(value, f"{path}.{key}")
        return count
    elif isinstance(data, list):
        if len(data) > 0:
            return 1  # Count non-empty lists as 1 preserved item
        return 0
    elif isinstance(data, str):
        return 1 if data else 0
    elif data is not None:
        return 1
    else:
        return 0


# =============================================================================
# MIGRATION SYSTEM - Nested Value Operations
# =============================================================================

def _get_nested_value(data: Dict[str, Any], key_path: str) -> Optional[Any]:
    """
    Get value from nested dictionary using dot notation

    Args:
        data: Dictionary to search
        key_path: Dot-notation path (e.g., "metadata.version")

    Returns:
        Value if found, None otherwise

    Examples:
        _get_nested_value({"a": {"b": "value"}}, "a.b") → "value"
        _get_nested_value({"x": 1}, "x") → 1
        _get_nested_value({"x": 1}, "y") → None
    """
    if not key_path:
        return data

    keys = key_path.split('.')
    current = data

    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]

    return current


def _set_nested_value(data: Dict[str, Any], key_path: str, value: Any) -> bool:
    """
    Set value in nested dictionary using dot notation

    Args:
        data: Dictionary to modify (modified in place)
        key_path: Dot-notation path
        value: Value to set

    Returns:
        True if successful, False if path invalid

    Examples:
        _set_nested_value({}, "a.b", "value") → {"a": {"b": "value"}}
        _set_nested_value({"x": 1}, "x", 2) → {"x": 2}
    """
    if not key_path:
        return False

    keys = key_path.split('.')
    current = data

    # Navigate to parent, creating dicts as needed
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        elif not isinstance(current[key], dict):
            return False  # Path blocked by non-dict value
        current = current[key]

    # Set final key
    current[keys[-1]] = value
    return True


def _delete_nested_key(data: Dict[str, Any], key_path: str) -> bool:
    """
    Delete key from nested dictionary using dot notation

    Args:
        data: Dictionary to modify (modified in place)
        key_path: Dot-notation path

    Returns:
        True if deleted, False if key doesn't exist

    Examples:
        _delete_nested_key({"a": {"b": "x"}}, "a.b") → True, {"a": {}}
        _delete_nested_key({"x": 1}, "y") → False
    """
    if not key_path:
        return False

    keys = key_path.split('.')
    current = data

    # Navigate to parent
    for key in keys[:-1]:
        if not isinstance(current, dict) or key not in current:
            return False
        current = current[key]

    # Delete final key
    if isinstance(current, dict) and keys[-1] in current:
        del current[keys[-1]]
        return True

    return False


# =============================================================================
# MIGRATION SYSTEM - Operation Functions
# =============================================================================

def _apply_key_rename(
    data: Dict[str, Any],
    from_key: str,
    to_key: str,
    operation_id: str
) -> Tuple[str, str]:
    """
    Rename a key, preserving its value

    Args:
        data: Data dictionary (modified in place)
        from_key: Old key path (dot notation)
        to_key: New key path (dot notation)
        operation_id: ID for logging

    Returns:
        Tuple of (status, message): status is 'success', 'skip', or 'error'
    """
    # Check if target already exists (already migrated)
    if _get_nested_value(data, to_key) is not None:
        return ("skip", f"{to_key} already exists (already migrated)")

    # Check if source exists
    value = _get_nested_value(data, from_key)
    if value is None:
        return ("skip", f"{from_key} not found (already removed or never existed)")

    # Perform rename
    if _set_nested_value(data, to_key, value) and _delete_nested_key(data, from_key):
        return ("success", f"Renamed {from_key} → {to_key}")
    else:
        return ("error", f"Failed to rename {from_key} → {to_key}")


def _apply_move_to_nested(
    data: Dict[str, Any],
    source_keys: List[str],
    target_parent: str,
    operation_id: str
) -> Tuple[str, str]:
    """
    Move multiple keys under a new parent key

    Args:
        data: Data dictionary (modified in place)
        source_keys: List of keys to move (top-level only for now)
        target_parent: New parent key name
        operation_id: ID for logging

    Returns:
        Tuple of (status, message): status is 'success', 'skip', or 'error'
    """
    # Check if target parent already exists and has the keys (already migrated)
    parent = _get_nested_value(data, target_parent)
    if parent and isinstance(parent, dict):
        if all(key in parent for key in source_keys):
            return ("skip", f"{target_parent} already contains all source keys (already migrated)")

    # Collect values to move
    values_to_move = {}
    for key in source_keys:
        value = data.get(key)
        if value is not None:
            values_to_move[key] = value

    if not values_to_move:
        return ("skip", "No source keys found to move")

    # Create or get target parent
    if target_parent not in data:
        data[target_parent] = {}
    elif not isinstance(data[target_parent], dict):
        return ("error", f"{target_parent} exists as non-dict type")

    # Move keys
    for key, value in values_to_move.items():
        data[target_parent][key] = value
        del data[key]

    return ("success", f"Moved {len(values_to_move)} key(s) to {target_parent}")


def _apply_add_missing_keys(
    data: Dict[str, Any],
    parent: str,
    keys: Dict[str, Any],
    operation_id: str
) -> Tuple[str, str]:
    """
    Add new keys with default values if they don't exist

    Args:
        data: Data dictionary (modified in place)
        parent: Parent key path (empty string for root)
        keys: Dict of key→value pairs to add
        operation_id: ID for logging

    Returns:
        Tuple of (status, message): status is 'success', 'skip', or 'error'
    """
    # Get target location
    if parent:
        target = _get_nested_value(data, parent)
        if target is None:
            # Create parent if missing
            if not _set_nested_value(data, parent, {}):
                return ("error", f"Could not create parent {parent}")
            target = _get_nested_value(data, parent)

        if not isinstance(target, dict):
            return ("error", f"{parent} exists as non-dict type")
    else:
        target = data

    # Add missing keys
    added_count = 0
    for key, value in keys.items():
        if key not in target:
            target[key] = value
            added_count += 1

    if added_count == 0:
        return ("skip", "All keys already exist")

    return ("success", f"Added {added_count} missing key(s)")


# =============================================================================
# MIGRATION SYSTEM - Orchestration
# =============================================================================

def load_migrations(template_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load .migrations.json from template directory

    Args:
        template_dir: Path to template directory

    Returns:
        Migrations dict if found, None otherwise
    """
    migrations_file = template_dir / ".migrations.json"
    if not migrations_file.exists():
        return None

    migrations, _ = load_json(migrations_file)
    return migrations


def apply_migrations(
    data: Dict[str, Any],
    migrations: Dict[str, Any],
    filename: str
) -> List[Tuple[str, str]]:
    """
    Apply migrations to data based on filename pattern matching

    Args:
        data: Data to migrate (modified in place)
        migrations: Migrations dict from .migrations.json
        filename: Name of file being migrated

    Returns:
        List of tuples (status, message) for each migration operation
    """
    results = []

    # Get migrations list
    migration_list = migrations.get("migrations", [])

    for migration in migration_list:
        migration_id = migration.get("id", "unknown")
        applies_to_files = migration.get("applies_to_files", [])

        # Check if migration applies to this file
        applies = False
        for pattern in applies_to_files:
            if fnmatch(filename, pattern):
                applies = True
                break

        if not applies:
            continue

        # Apply each operation in this migration
        operations = migration.get("operations", [])
        for op in operations:
            op_type = op.get("type")

            if op_type == "key_rename":
                result = _apply_key_rename(
                    data,
                    op.get("from", ""),
                    op.get("to", ""),
                    migration_id
                )
                results.append(result)

            elif op_type == "move_to_nested":
                result = _apply_move_to_nested(
                    data,
                    op.get("source_keys", []),
                    op.get("target_parent", ""),
                    migration_id
                )
                results.append(result)

            elif op_type == "add_missing_keys":
                result = _apply_add_missing_keys(
                    data,
                    op.get("parent", ""),
                    op.get("keys", {}),
                    migration_id
                )
                results.append(result)

    return results


# =============================================================================
# BRANCH FILE UPDATE (complex operation)
# =============================================================================

def update_branch_file(
    branch_file: Path,
    template_file: Path,
    backup_dir: Path,
    timestamp: str,
    file_label: str,
    replacements: Dict[str, str],
    apply_placeholders_func,
    migrations: Optional[Dict[str, Any]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Update single branch JSON file from template with optional migrations

    Args:
        branch_file: Path to branch JSON file
        template_file: Path to template JSON file
        backup_dir: Directory for backups
        timestamp: Timestamp string
        file_label: Label for progress output
        replacements: Placeholder replacements
        apply_placeholders_func: Function to apply placeholders
        migrations: Optional migrations dict from .migrations.json

    Returns:
        (success, change_summary_dict)
    """
    # Load existing and template
    existing, _ = load_json(branch_file)
    template, _ = load_json(template_file)

    if template is None:
        return True, {"action": "skipped_template_missing"}

    # If existing doesn't exist, create from template
    if existing is None:
        try:
            populated = apply_placeholders_func(template, replacements)
        except ValueError as exc:
            return False, {}

        success, error = save_json(branch_file, populated)
        if success:
            return True, {"action": "created", "fields_added": len(template.keys())}
        else:
            return False, {}

    # Backup existing file
    backup_path, backup_msg = backup_json_file(branch_file, backup_dir, timestamp)

    # Get versions
    old_version = existing.get("metadata", {}).get("version", "unknown")
    new_version = template.get("metadata", {}).get("version", "unknown")

    # Apply migrations to existing data BEFORE deep merge
    migration_results = []
    if migrations:
        migration_results = apply_migrations(existing, migrations, branch_file.name)

        # Count migration results (handler should not display output)
        if migration_results:
            succeeded = sum(1 for status, _ in migration_results if status == "success")
            skipped = sum(1 for status, _ in migration_results if status == "skip")
            failed = sum(1 for status, _ in migration_results if status == "error")

    # Deep merge
    merged = deep_merge(template, existing)

    # Migrate version
    merged = migrate_version(merged, new_version)

    # Apply placeholder replacements
    try:
        merged = apply_placeholders_func(merged, replacements)
    except ValueError as exc:
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, branch_file)
        return False, {}

    # Count changes
    new_fields = count_new_fields(template, existing)
    preserved_data = count_preserved_data(existing)

    # Save merged result
    success, error = save_json(branch_file, merged)
    if success:
        result = {
            "action": "updated",
            "old_version": old_version,
            "new_version": new_version,
            "fields_added": new_fields,
            "data_preserved": preserved_data
        }

        # Add migration stats if migrations were applied
        if migration_results:
            result["migrations_applied"] = sum(1 for status, _ in migration_results if status == "success")
            result["migrations_skipped"] = sum(1 for status, _ in migration_results if status == "skip")
            result["migrations_failed"] = sum(1 for status, _ in migration_results if status == "error")

        return True, result
    else:
        # Restore from backup
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, branch_file)
        return False, {}
