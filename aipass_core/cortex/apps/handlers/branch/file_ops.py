#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: file_ops.py - File Operations Handler
# Date: 2025-11-04
# Version: 1.0.0
# Category: cortex/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-04): Extracted from branch_lib, file operation functions
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
File Operations Handler

Functions for file and directory operations:
- File renaming
- Directory renaming
- Template content copying
- Module migration
- Memory file management
"""

# Standard library imports
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Iterable, Any

# AIPASS_ROOT for registry_ignore import
import sys
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Internal handler imports
from cortex.apps.handlers.branch.placeholders import replace_placeholders, validate_no_placeholders
from cortex.apps.handlers.registry.ignore import load_ignore_patterns, should_ignore


# =============================================================================
# FILE DISCOVERY AND MATCHING
# =============================================================================

def find_existing_memory_files(target_dir: Path, branch_name: str) -> Dict[str, Path]:
    """
    Find existing memory files with any naming convention (hyphens, underscores, etc.)

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name to match against

    Returns:
        Dict mapping file types (main, local, observations, ai_mail, id) to Path objects
    """
    found_files = {}
    branchname_upper = branch_name.upper().replace("-", "_")

    # Memory file suffixes to check (JSON format)
    memory_suffixes = [".json", ".local.json", ".observations.json", ".ai_mail.json", ".id.json"]

    for item in target_dir.iterdir():
        if not item.is_file():
            continue

        # Check each memory file type
        for suffix in memory_suffixes:
            if item.name.endswith(suffix):
                # Extract the prefix (everything before the suffix)
                prefix = item.name[:-len(suffix)]

                # Normalize to check if it matches branch name
                prefix_normalized = prefix.replace("-", "_").upper()

                if prefix_normalized == branchname_upper:
                    # Found a matching file - determine its type
                    file_type: str
                    if suffix == ".json":
                        file_type = "main"
                    elif suffix == ".local.json":
                        file_type = "local"
                    elif suffix == ".observations.json":
                        file_type = "observations"
                    elif suffix == ".ai_mail.json":
                        file_type = "ai_mail"
                    elif suffix == ".id.json":
                        file_type = "id"
                    else:
                        # Unknown suffix, skip this file
                        continue

                    found_files[file_type] = item
                    break

    return found_files


def detect_naming_mismatches(target_dir: Path, branch_name: str, file_renames: Dict[str, str]) -> List[Tuple[str, str]]:
    """
    Detect files with non-standard naming (hyphens instead of underscores)

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name
        file_renames: Dict mapping template names to rename patterns

    Returns:
        List of tuples (wrong_name, correct_name)
    """
    mismatches = []
    branchname_upper = branch_name.upper().replace("-", "_")
    branchname_lower = branch_name.lower().replace("-", "_")

    # Check for each expected file with correct naming
    for _, pattern in file_renames.items():
        correct_name = pattern.format(BRANCHNAME=branchname_upper, branchname=branchname_lower)

        # Look for files that match the pattern but use different separator
        for item in target_dir.iterdir():
            if item.is_file() and item.name != correct_name:
                # Check if it's a similar name with hyphens or mixed separators
                item_name_normalized = item.name.replace("-", "_")
                correct_name_normalized = correct_name.replace("-", "_")

                if item_name_normalized == correct_name_normalized and item.name != correct_name:
                    mismatches.append((item.name, correct_name))

    return mismatches


# =============================================================================
# FILE OPERATIONS
# =============================================================================

def smart_rename_memory_files(target_dir: Path, branch_name: str) -> List[str]:
    """
    Rename existing memory files to standard convention, preserving content

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name

    Returns:
        List of rename operations performed (formatted strings)
    """
    branchname_upper = branch_name.upper().replace("-", "_")
    renamed = []

    # Find existing memory files
    existing_files = find_existing_memory_files(target_dir, branch_name)

    # Expected filenames (standard convention)
    expected_names = {
        "main": f"{branchname_upper}.json",
        "local": f"{branchname_upper}.local.json",
        "observations": f"{branchname_upper}.observations.json",
        "ai_mail": f"{branchname_upper}.ai_mail.json",
        "id": f"{branchname_upper}.id.json",
    }

    # Rename each file to standard convention
    for file_type, existing_file in existing_files.items():
        expected_name = expected_names[file_type]

        # Skip if already correctly named
        if existing_file.name == expected_name:
            continue

        # Rename to standard convention
        dest = target_dir / expected_name

        # Safety check - don't overwrite if target already exists
        if dest.exists():
            # This shouldn't happen, but log it
            renamed.append(f"⚠️  {existing_file.name} → {expected_name} (SKIPPED - target exists)")
            continue

        # Rename the file
        existing_file.rename(dest)
        renamed.append(f"{existing_file.name} → {expected_name}")

    return renamed


def rename_files(target_dir: Path, branch_name: str, file_renames: Dict[str, str]) -> Tuple[List[str], List[str]]:
    """
    Rename template files to branch-specific names

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name
        file_renames: Dict mapping template names to rename patterns

    Returns:
        Tuple of (renamed files list, missing files list)
    """
    branchname_upper = branch_name.upper().replace("-", "_")
    branchname_lower = branch_name.lower().replace("-", "_")
    renamed = []
    missing = []

    for template_name, pattern in file_renames.items():
        source = target_dir / template_name
        if source.exists():
            new_name = pattern.format(BRANCHNAME=branchname_upper, branchname=branchname_lower)
            dest = target_dir / new_name
            if not dest.exists():
                source.rename(dest)
                renamed.append(f"{template_name} → {new_name}")
        else:
            # Expected file not found
            missing.append(template_name)

    return renamed, missing


def rename_json_directory(target_dir: Path, branch_name: str) -> Optional[str]:
    """
    Rename {{BRANCH}}_json to branch-specific name

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name

    Returns:
        Rename operation string or None if not performed
    """
    source = target_dir / "{{BRANCH}}_json"
    if source.exists():
        dest = target_dir / f"{branch_name}_json"
        if not dest.exists():
            source.rename(dest)
            # Use source.name to avoid placeholder pattern in output
            return f"{source.name} → {branch_name}_json"
    return None


def migrate_modules_to_apps(target_dir: Path) -> List[str]:
    """
    Move Python modules from root to apps/ directory

    Args:
        target_dir: Path to branch directory

    Returns:
        List of migrated module names
    """
    migrated = []

    # Ensure apps/ directory exists
    apps_dir = target_dir / "apps"
    apps_dir.mkdir(exist_ok=True)

    # Create __init__.py to make apps/ a Python package
    apps_init = apps_dir / "__init__.py"
    if not apps_init.exists():
        apps_init.write_text("# Apps package\n")

    # Files to exclude from migration (scripts, not modules)
    exclude_files = [
        "new_branch_setup.py",
        "upgrade_branch.py",
        "setup.py",  # Common setup file
    ]

    # Find all .py files at root level only
    for item in target_dir.iterdir():
        # Only process .py files at root
        if not item.is_file() or item.suffix != ".py":
            continue

        # Skip excluded files
        if item.name in exclude_files:
            continue

        # Check if file already exists in apps/
        dest = apps_dir / item.name
        if dest.exists():
            continue  # Don't overwrite existing files in apps/

        # Move file to apps/
        item.rename(dest)
        migrated.append(item.name)

    return migrated


def update_readme_tree_placeholders(target_dir: Path, tree_output: str) -> None:
    """
    Update TREE_PLACEHOLDER in README files

    Args:
        target_dir: Path to branch directory
        tree_output: Generated tree output to replace placeholder with
    """
    # Update README.md
    readme_md = target_dir / "README.md"
    if readme_md.exists():
        content = readme_md.read_text(encoding='utf-8')
        content = content.replace("{{TREE_PLACEHOLDER}}", tree_output)
        readme_md.write_text(content, encoding='utf-8')

    # Update README.json
    readme_json = target_dir / "README.json"
    if readme_json.exists():
        content = readme_json.read_text(encoding='utf-8')
        content = content.replace("{{TREE_PLACEHOLDER}}", tree_output)
        readme_json.write_text(content, encoding='utf-8')


# =============================================================================
# TEMPLATE OPERATIONS
# =============================================================================

def should_exclude(item_path: Path, template_dir: Path, exclude_patterns: List[str]) -> bool:
    """
    Check if item should be excluded from template copy

    Uses both registry_ignore patterns AND legacy exclude_patterns for backwards compatibility.

    Args:
        item_path: Path to item being checked
        template_dir: Path to template directory
        exclude_patterns: List of patterns to exclude (legacy)

    Returns:
        True if item should be excluded, False otherwise
    """
    # Load registry ignore patterns
    ignore_patterns = load_ignore_patterns(template_dir)
    ignore_files = ignore_patterns.get("ignore_files", [])
    ignore_globs = ignore_patterns.get("ignore_patterns", [])

    # Check registry_ignore first (takes priority)
    if should_ignore(item_path, template_dir, ignore_files, ignore_globs):
        return True

    # Fallback to legacy exclude patterns for backwards compatibility
    rel_path = item_path.relative_to(template_dir)
    path_str = str(rel_path)

    # Special handling for .git directory (don't exclude .gitignore or .gitattributes)
    if path_str.startswith(".git") and path_str != ".gitignore" and path_str != ".gitattributes":
        return True

    # Check other exclude patterns
    for pattern in exclude_patterns:
        if pattern == ".git":
            continue  # Already handled above
        if pattern in path_str:
            return True

    # Exclude PLAN*.md files
    if item_path.name.startswith("PLAN") and item_path.name.endswith(".md"):
        return True

    # Exclude .gitkeep files (template needs them for git, branches don't)
    if item_path.name == ".gitkeep":
        return True

    return False


def will_be_renamed(rel_path: Path, branch_name: str, file_renames: Dict[str, str]) -> Optional[Path]:
    """
    Check if this file will be renamed, return final name if yes

    Args:
        rel_path: Relative path to file
        branch_name: Branch name
        file_renames: Dict mapping template names to rename patterns

    Returns:
        Final path after rename, or None if no rename
    """
    # Check if full relative path is in file_renames (for files in subdirs like apps/BRANCH.py)
    rel_path_str = str(rel_path).replace("\\", "/")  # Normalize path separators
    if rel_path_str in file_renames:
        branchname_upper = branch_name.upper().replace("-", "_")
        branchname_lower = branch_name.lower().replace("-", "_")
        new_name = file_renames[rel_path_str].format(BRANCHNAME=branchname_upper, branchname=branchname_lower)
        return Path(new_name)

    # Check if just the filename is in file_renames
    filename = rel_path.name
    if filename in file_renames:
        branchname_upper = branch_name.upper().replace("-", "_")
        branchname_lower = branch_name.lower().replace("-", "_")
        new_name = file_renames[filename].format(BRANCHNAME=branchname_upper, branchname=branchname_lower)
        return rel_path.parent / new_name

    # Check if it's the {{BRANCH}}_json directory
    if filename == "{{BRANCH}}_json":
        new_name = f"{branch_name}_json"
        return rel_path.parent / new_name

    return None


def detect_unreplaced_placeholders(
    target_dir: Path,
    branch_name: str,
    allowed_placeholders: Optional[Iterable[str]] = None
) -> List[Tuple[Path, List[Dict[str, Any]]]]:
    """
    Scan standard branch memory files for unreplaced template placeholders.

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name (used to build expected filenames)
        allowed_placeholders: Placeholders that may legitimately remain

    Returns:
        List of tuples (Path to file, list of placeholder detail dicts)
        Each placeholder detail dict contains line numbers and context
    """
    branchname_upper = branch_name.upper().replace("-", "_")
    expected_files = [
        target_dir / f"{branchname_upper}.json",
        target_dir / f"{branchname_upper}.local.json",
        target_dir / f"{branchname_upper}.observations.json",
        target_dir / f"{branchname_upper}.ai_mail.json",
        target_dir / f"{branchname_upper}.id.json",
    ]

    issues: List[Tuple[Path, List[Dict[str, Any]]]] = []
    for file_path in expected_files:
        if not file_path.exists() or not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            # Skip files that cannot be read (permission/encoding issues)
            continue

        is_valid, placeholders = validate_no_placeholders(
            content,
            str(file_path),
            allowed_placeholders=allowed_placeholders
        )
        if not is_valid and placeholders:
            issues.append((file_path, placeholders))

    return issues


def apply_placeholder_replacements_to_dict(
    data: Dict[str, Any],
    replacements: Dict[str, str]
) -> Dict[str, Any]:
    """
    Apply placeholder replacements to a JSON-compatible dictionary.

    Args:
        data: Dictionary loaded from template or merged result
        replacements: Placeholder replacement mapping

    Returns:
        Dictionary with placeholders replaced

    Raises:
        ValueError: If replacement results in invalid JSON structure
    """
    serialized = json.dumps(data, indent=2, ensure_ascii=False)
    serialized = replace_placeholders(serialized, replacements)
    try:
        return json.loads(serialized)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON after placeholder replacement: {exc}") from exc


def build_replacements_dict(branch_name: str, target_dir: Path, repo: str, profile: str) -> dict:
    """
    Build replacements dictionary for template placeholders.

    Args:
        branch_name: Branch name (lowercase with hyphens)
        target_dir: Target directory path
        repo: Git repository name
        profile: AIPass profile (Workshop, Business, etc.)

    Returns:
        Dictionary of template placeholders and their replacement values
    """
    branchname_upper = branch_name.upper().replace("-", "_")
    foldername_lower = branch_name.lower()
    now = datetime.now()

    return {
        # Already implemented
        "BRANCHNAME": branchname_upper,
        "branchname": foldername_lower,  # Lowercase for .gitignore patterns
        "FOLDERNAME": foldername_lower,
        "BRANCH": foldername_lower,  # For {{BRANCH}}_json
        "CWD": str(target_dir),
        "DATE": now.strftime("%Y-%m-%d"),
        "TIMESTAMP": now.strftime("%Y-%m-%d"),
        "REPO": repo,
        "PROFILE": profile,

        # New auto-fills
        "INSTANCE_NAME": branchname_upper,  # Same as BRANCHNAME
        "EMAIL": "aipass.system@gmail.com",  # Universal system email
        "AUTO_TIMESTAMP": now.strftime("%Y-%m-%d"),
        "AUTO_GENERATED_TREE": "{{TREE_PLACEHOLDER}}",  # Will be replaced after files copied

        # Blank fields for AI to fill during first session
        "ROLE": "",
        "TRAITS": "",
        "PURPOSE_DESCRIPTION": "",
        "PURPOSE_BRIEF": "",
        "WHAT_I_DO": "",
        "WHAT_I_DONT_DO": "",
        "HOW_I_WORK": "",
        "RESPONSIBILITIES_LIST": "",
        "USAGE_INSTRUCTIONS": "",
        "BRANCH_DESCRIPTION": "",

        # Keep as placeholder (AI fills during updates)
        # AUTO_GENERATED_COMMANDS stays as {{AUTO_GENERATED_COMMANDS}}
    }


def copy_template_contents(
    template_dir: Path,
    target_dir: Path,
    replacements: Dict[str, str],
    branch_name: str,
    exclude_patterns: List[str],
    file_renames: Dict[str, str],
    allowed_placeholders: set | None = None
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """
    Copy template contents to target directory

    Args:
        template_dir: Path to template directory
        target_dir: Path to target directory
        replacements: Dict of placeholder replacements
        branch_name: Branch name
        exclude_patterns: List of patterns to exclude
        file_renames: Dict mapping template names to rename patterns
        allowed_placeholders: Set of placeholders that don't need to be replaced yet

    Returns:
        Tuple of (copied items list, skipped items list, validation errors list)
        Each validation error dict contains:
            - 'file': str (file path)
            - 'placeholder_details': list (detailed placeholder info)
            - 'available_keys': list (available replacement keys)
    """
    copied = []
    skipped = []
    validation_errors = []

    # Walk template directory recursively including hidden files
    def walk_all(directory):
        """Walk directory including hidden files"""
        for item in directory.iterdir():
            yield item
            if item.is_dir():
                # Recursively walk subdirectories (including hidden ones like .claude)
                # But skip .git directory (handled in should_exclude)
                if item.name != ".git":
                    yield from walk_all(item)

    # Collect all items
    items = list(walk_all(template_dir))

    # Walk all items
    for item in items:
        # Skip if in exclude list
        if should_exclude(item, template_dir, exclude_patterns):
            continue

        # Get relative path
        rel_path = item.relative_to(template_dir)
        target_path = target_dir / rel_path

        # Check if file/directory will be renamed
        renamed_path = will_be_renamed(rel_path, branch_name, file_renames)

        # Skip if already exists (check both template name and renamed version)
        if target_path.exists():
            skipped.append(str(rel_path))
            continue
        if renamed_path and (target_dir / renamed_path).exists():
            skipped.append(f"{rel_path} (renamed version exists)")
            continue

        # Check if parent directory will be renamed (for files inside renamed dirs)
        if item.is_file():
            parent_renamed = will_be_renamed(rel_path.parent, branch_name, file_renames)
            if parent_renamed and (target_dir / parent_renamed).exists():
                # Parent directory was renamed and exists, skip file (should already be in renamed dir)
                skipped.append(f"{rel_path} (parent renamed)")
                continue

        # Copy directory
        if item.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            copied.append(f"{rel_path}/ (directory)")

        # Copy file
        elif item.is_file():
            # Create parent directory if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Try to read as text and replace placeholders
            try:
                with open(item, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Replace placeholders
                content = replace_placeholders(content, replacements)

                # Validate all placeholders were replaced
                is_valid, unreplaced = validate_no_placeholders(content, str(rel_path), allowed_placeholders)

                if not is_valid:
                    # Collect error for summary reporting (don't print immediately)
                    validation_errors.append({
                        'file': str(rel_path),
                        'placeholder_details': unreplaced,
                        'available_keys': list(replacements.keys())
                    })

                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                copied.append(str(rel_path))
            except (UnicodeDecodeError, UnicodeEncodeError):
                # Binary file or encoding issue - just copy
                shutil.copy2(item, target_path)
                copied.append(f"{rel_path} (binary)")

    return copied, skipped, validation_errors


# =============================================================================
# UPDATE OPERATIONS
# =============================================================================

def create_backup(branch_dir: Path) -> Tuple[Optional[Path], str]:
    """
    Create full backup of branch directory before modifications

    Uses single 'latest' backup that gets overwritten each time.
    Loads ignore patterns from .backup_ignore.json if available.

    Args:
        branch_dir: Path to branch directory

    Returns:
        Tuple of (backup directory path or None, status message)
    """
    backup_dir = branch_dir / ".backup" / "latest"

    # Load backup ignore patterns from template - REQUIRED, no defaults
    AIPASS_ROOT = Path.home() / "aipass_core"
    TEMPLATE_DIR = AIPASS_ROOT / "cortex" / "templates" / "branch_template"
    template_ignore_file = TEMPLATE_DIR / ".backup_ignore.json"

    # Always ignore backup dirs to prevent recursion
    ignore_dirs = {".backup", "backups"}
    ignore_patterns_list = []

    # Load patterns from template - required
    if not template_ignore_file.exists():
        error_msg = (
            f"ERROR: Backup ignore configuration missing!\n"
            f"  Required file: {template_ignore_file}\n"
            f"  Please create .backup_ignore.json in the template with ignore_directories and ignore_patterns.\n"
            f"  Without this config, backup could copy massive directories (like .venv, node_modules, etc.)"
        )
        return (None, error_msg)

    try:
        with open(template_ignore_file, 'r', encoding='utf-8') as f:
            backup_ignore = json.load(f)
            ignore_dirs.update(backup_ignore.get("ignore_directories", []))
            ignore_patterns_list = backup_ignore.get("ignore_patterns", [])
    except Exception as e:
        error_msg = (
            f"ERROR: Failed to load backup ignore config!\n"
            f"  File: {template_ignore_file}\n"
            f"  Error: {e}\n"
            f"  Fix the JSON syntax and try again."
        )
        return (None, error_msg)

    def ignore_patterns(directory, contents):
        """Ignore backup dirs, large dependency dirs, and pattern matches"""
        from fnmatch import fnmatch
        ignored = []
        for name in contents:
            # Check if directory name matches ignore list
            if name in ignore_dirs:
                ignored.append(name)
                continue
            # Check if filename matches any ignore patterns
            if any(fnmatch(name, pattern) for pattern in ignore_patterns_list):
                ignored.append(name)
        return ignored

    try:
        # Remove old backup if exists
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        backup_dir.mkdir(parents=True, exist_ok=True)

        # Count items for progress
        items = list(branch_dir.iterdir())
        total_items = len([i for i in items if i.name not in [".backup", "backups"]])
        processed = 0
        skipped = 0

        # Copy all files except .backup and backups directories
        for item in items:
            # Skip .backup directory and backups directory
            if item.name in [".backup", "backups"]:
                continue

            # Check if this item will be ignored (directory or file pattern match)
            if item.name in ignore_dirs:
                skipped += 1
                continue

            # Check if file matches any ignore patterns
            from fnmatch import fnmatch
            if any(fnmatch(item.name, pattern) for pattern in ignore_patterns_list):
                skipped += 1
                continue

            if item.is_file():
                processed += 1
                shutil.copy2(item, backup_dir / item.name)
            elif item.is_dir():
                processed += 1
                # Use ignore function to skip .backup and backups at all levels
                shutil.copytree(item, backup_dir / item.name, ignore=ignore_patterns, dirs_exist_ok=True)

        return (backup_dir, f"Backup created at {backup_dir}")

    except Exception as e:
        return (None, f"Backup creation failed: {e}")


def archive_pruned_file(branch_dir: Path, filename: str, file_id: str, aipass_root: Path) -> Tuple[bool, str]:
    """
    Archive a pruned file to backup_system/pruned_files/

    Never deletes - always preserves
    Archives to centralized backup_system alongside deleted_branches/ and processed_plans/

    Args:
        branch_dir: Path to branch directory
        filename: Filename to archive
        file_id: Template file ID
        aipass_root: AIPass root path for backup_system

    Returns:
        Tuple of (success status, status message)
    """
    source = branch_dir / filename
    if not source.exists():
        # Silent skip - file already deleted or never existed
        return (False, f"File not found: {filename}")

    # Archive to backup_system/pruned_files/{branch_name}/{timestamp}/
    branch_name = branch_dir.name
    timestamp = datetime.now().strftime("%Y%m%d")
    archive_base = aipass_root / "backup_system" / "pruned_files"
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

        return (True, f"Archived: {filename} → {archive_dir}")

    except Exception as e:
        return (False, f"Failed to archive {filename}: {e}")


def execute_rename(branch_dir: Path, old_name: str, new_name: str, file_id: str) -> Tuple[bool, str]:
    """
    Execute a file/directory rename

    Args:
        branch_dir: Path to branch directory
        old_name: Old filename/directory name
        new_name: New filename/directory name
        file_id: Template file ID

    Returns:
        Tuple of (success status, status message)
    """
    old_path = branch_dir / old_name
    new_path = branch_dir / new_name

    if not old_path.exists():
        return (False, f"Rename source not found: {old_name}")

    if new_path.exists():
        return (False, f"Rename target already exists: {new_name} (skipping)")

    try:
        old_path.rename(new_path)
        return (True, f"Renamed: {old_name} → {new_name} (ID: {file_id})")
    except Exception as e:
        return (False, f"Rename failed {old_name} → {new_name}: {e}")


def copy_template_file(
    template_dir: Path,
    branch_dir: Path,
    filename: str,
    file_id: str,
    registry: Dict[str, Any],
    branch_name: str,
    file_renames: Optional[Dict[str, str]] = None,
    force_overwrite: bool = False
) -> Tuple[str, str]:
    """
    Copy a new file from template to branch using path from registry

    Args:
        template_dir: Template directory path
        branch_dir: Branch directory path
        filename: Filename (may contain {{BRANCH}} placeholder)
        file_id: Template file ID
        registry: Template registry dict (to get path info)
        branch_name: Branch name for placeholder substitution
        file_renames: Optional dict mapping template names to rename patterns
        force_overwrite: If True, overwrite existing files (default: False)

    Returns:
        Tuple of (status, message) where status is:
        "added" if file was added
        "updated" if file was overwritten
        "skipped" if already exists
        "protected" if Python file (never overwrite)
        "error" if failed
    """
    # Get the file's path from registry
    file_info = registry.get("files", {}).get(file_id)
    dir_info = registry.get("directories", {}).get(file_id)

    # Apply placeholder substitution to filename
    branch_upper = branch_name.upper().replace("-", "_")
    branch_lower = branch_name.lower().replace("-", "_")
    dest_filename = filename.replace("{{BRANCH}}", branch_upper)

    # Apply FILE_RENAMES substitution if filename matches
    if file_renames and filename in file_renames:
        rename_pattern = file_renames[filename]
        dest_filename = rename_pattern.format(BRANCHNAME=branch_upper, branchname=branch_lower)

    if file_info:
        # It's a file - path in registry is full relative path
        registry_path = file_info.get("path", filename)
        # Apply placeholder substitution to path
        source_path = registry_path.replace("{{BRANCH}}", branch_upper)

        # For destination, use dest_filename (which may be renamed) instead of original filename
        registry_path_parent = Path(registry_path).parent
        if str(registry_path_parent) == ".":
            dest_path = dest_filename
        else:
            dest_path = str(registry_path_parent / dest_filename)
        dest_path = dest_path.replace("{{BRANCH}}", branch_upper)

        source = template_dir / source_path
        dest = branch_dir / dest_path
    elif dir_info:
        # It's a directory - subpath is full path from registry
        subpath = dir_info.get("path", filename)

        # For directories: source keeps original name (with {{BRANCH}} placeholder literal)
        # Only destination gets placeholder replacement
        source_subpath = subpath  # Keep template name as-is

        # Apply placeholder substitution to DESTINATION only
        # Use lowercase for _json directories, uppercase for others
        branch_lower = branch_name.lower().replace("-", "_")
        if "_json" in subpath:
            dest_subpath = subpath.replace("{{BRANCH}}", branch_lower)
        else:
            dest_subpath = subpath.replace("{{BRANCH}}", branch_upper)

        source = template_dir / source_subpath
        dest = branch_dir / dest_subpath
    else:
        return ("error", f"File ID {file_id} not found in registry")

    if not source.exists():
        error_msg = f"Template file not found: {source.name}"
        return ("error", error_msg)

    # Check if destination exists
    if dest.exists():
        # PROTECTION RULE: Python files in apps/ are NEVER overwritten
        is_python_file = dest.suffix == '.py' and 'apps' in dest.parts

        if is_python_file:
            return ("protected", f"Python file protected: {dest.relative_to(branch_dir)} (never overwrite)")

        # Non-Python files: respect force_overwrite flag
        if not force_overwrite:
            return ("skipped", f"File already exists: {dest.relative_to(branch_dir)} (skipping)")

        # force_overwrite=True: Replace the file
        # (Will continue to copy logic below)

    # Determine if this is an add or update
    is_update = dest.exists()

    try:
        # Create parent directories if needed
        dest.parent.mkdir(parents=True, exist_ok=True)

        if source.is_file():
            # Try to read as text and replace placeholders
            try:
                from cortex.apps.handlers.branch.placeholders import (
                    build_replacements_dict,
                    replace_placeholders
                )

                with open(source, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Build replacements dict
                # Use minimal defaults if metadata not available
                repo = "aipass_core"  # Default repo
                profile = "AIPass Core Infrastructure"  # Default profile

                replacements = build_replacements_dict(branch_name, branch_dir, repo, profile)

                # Replace placeholders
                content = replace_placeholders(content, replacements)

                # Write with placeholders replaced
                with open(dest, 'w', encoding='utf-8') as f:
                    f.write(content)

            except (UnicodeDecodeError, ImportError):
                # Binary file or placeholder handler unavailable - just copy
                shutil.copy2(source, dest)

        elif source.is_dir():
            # Import registry_ignore to filter GLOBAL_IGNORES when copying directories
            from cortex.apps.handlers.registry.ignore import should_ignore, load_ignore_patterns

            # Create ignore function for copytree
            def ignore_global_files(directory, contents):
                """Filter out GLOBAL_IGNORES files during directory copy"""
                ignored = []
                for name in contents:
                    item_path = Path(directory) / name
                    # Use registry_ignore logic (GLOBAL_IGNORES + patterns)
                    if should_ignore(item_path, template_dir, [], []):
                        ignored.append(name)
                return ignored

            shutil.copytree(source, dest, ignore=ignore_global_files, dirs_exist_ok=True)

        # Return appropriate status based on operation type
        if is_update:
            return ("updated", f"Updated: {dest.relative_to(branch_dir)} (ID: {file_id})")
        else:
            return ("added", f"Added: {dest.relative_to(branch_dir)} (ID: {file_id})")
    except Exception as e:
        return ("error", f"Failed to copy {source} to {dest}: {e}")


