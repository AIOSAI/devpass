#!/usr/bin/env python3

# ===================AIPASS====================
# META DATA HEADER
# Name: branch_lib.py - AIPass Branch Operations Library
# Date: 2025-10-29
# Version: 1.0.0
# Category: branch_operations
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-10-29): Initial standardized version - Added META header, AIPASS_ROOT pattern, path getters
# =============================================

"""
AIPass Branch Operations Library
Shared functions for branch setup, upgrade, and maintenance scripts
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))

# Standard library imports
import os
import re
import shutil
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Iterable, Any
import json

# AIPass infrastructure imports
from prax.apps.prax_logger import system_logger as logger


# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

# AIPASS_ROOT already defined in infrastructure import pattern above
# This library module has no additional configuration


# =============================================================================
# METADATA EXTRACTION
# =============================================================================

def get_branch_name(target_path: Path) -> str:
    """
    Extract branch name from target path

    Args:
        target_path: Path to branch directory

    Returns:
        Branch name (last folder in path)
    """
    return Path(target_path).name


def detect_profile(target_path: Path) -> str:
    """
    Detect AIPass profile from path

    Args:
        target_path: Path to branch directory

    Returns:
        Profile name: Admin, Business, Input-X, or Workshop (default)
    """
    path_str = str(target_path)
    if path_str == "/":
        return "Admin"
    elif "/home/aipass-business/" in path_str:
        return "Business"
    elif "/home/input-x/" in path_str:
        return "Input-X"
    elif "/home/aipass/" in path_str:
        return "Workshop"
    else:
        return "Workshop"  # Default


def get_git_repo(target_path: Path) -> str:
    """
    Get git repo URL from target directory

    Args:
        target_path: Path to branch directory

    Returns:
        Git remote origin URL or "Not in git repository"
    """
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=target_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.error(f"get_git_repo failed for {target_path}: {e}")
    return "Not in git repository"


def generate_tree(target_dir: Path) -> str:
    """
    Generate directory tree output

    Args:
        target_dir: Path to directory to generate tree for

    Returns:
        Tree command output or error message
    """
    try:
        result = subprocess.run(
            ["tree", "-L", "2", "-a", str(target_dir)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout
    except Exception as e:
        logger.error(f"generate_tree failed for {target_dir}: {e}")
    return "[Tree command failed - install tree package]"


# =============================================================================
# PLACEHOLDER REPLACEMENT
# =============================================================================

def replace_placeholders(content: str, replacements: Dict[str, str]) -> str:
    """
    Replace placeholders in file content

    Placeholders must be in format: {{PLACEHOLDER_NAME}}

    Args:
        content: File content with placeholders
        replacements: Dict mapping placeholder names to replacement values

    Returns:
        Content with placeholders replaced
    """
    for placeholder, value in replacements.items():
        content = content.replace(f"{{{{{placeholder}}}}}", value)
    return content


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

    # Check for each expected file with correct naming
    for template_name, pattern in file_renames.items():
        correct_name = pattern.format(BRANCHNAME=branchname_upper)

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


def rename_files(target_dir: Path, branch_name: str, file_renames: Dict[str, str]) -> List[str]:
    """
    Rename template files to branch-specific names

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name
        file_renames: Dict mapping template names to rename patterns

    Returns:
        List of rename operations performed
    """
    branchname_upper = branch_name.upper().replace("-", "_")
    renamed = []

    for template_name, pattern in file_renames.items():
        source = target_dir / template_name
        if source.exists():
            new_name = pattern.format(BRANCHNAME=branchname_upper)
            dest = target_dir / new_name
            if not dest.exists():
                source.rename(dest)
                renamed.append(f"{template_name} → {new_name}")

    return renamed


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
            return f"{{{{BRANCH}}}}_json → {branch_name}_json"
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


# =============================================================================
# TEMPLATE OPERATIONS
# =============================================================================

def should_exclude(item_path: Path, template_dir: Path, exclude_patterns: List[str]) -> bool:
    """
    Check if item should be excluded from template copy

    Args:
        item_path: Path to item being checked
        template_dir: Path to template directory
        exclude_patterns: List of patterns to exclude

    Returns:
        True if item should be excluded, False otherwise
    """
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
    filename = rel_path.name

    # Check if it's a file that will be renamed
    if filename in file_renames:
        branchname_upper = branch_name.upper().replace("-", "_")
        new_name = file_renames[filename].format(BRANCHNAME=branchname_upper)
        return rel_path.parent / new_name

    # Check if it's the {{BRANCH}}_json directory
    if filename == "{{BRANCH}}_json":
        new_name = f"{branch_name}_json"
        return rel_path.parent / new_name

    return None


def validate_no_placeholders(
    content: str,
    file_path: str,
    allowed_placeholders: Optional[Iterable[str]] = None
) -> Tuple[bool, List[str]]:
    """
    Check if content still contains unreplaced placeholders.

    Args:
        content: File content to check
        file_path: Path to file (for error reporting)
        allowed_placeholders: Collection of placeholder tokens to ignore

    Returns:
        Tuple of (is_valid, list of unreplaced placeholders)
    """
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, content)

    if matches:
        allowed = set(allowed_placeholders or [])
        filtered = [placeholder for placeholder in matches if placeholder not in allowed]
        if filtered:
            return False, filtered
    return True, []


def detect_unreplaced_placeholders(
    target_dir: Path,
    branch_name: str,
    allowed_placeholders: Optional[Iterable[str]] = None
) -> List[Tuple[Path, List[str]]]:
    """
    Scan standard branch memory files for unreplaced template placeholders.

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name (used to build expected filenames)
        allowed_placeholders: Placeholders that may legitimately remain

    Returns:
        List of tuples (Path to file, list of placeholders found)
    """
    branchname_upper = branch_name.upper().replace("-", "_")
    expected_files = [
        target_dir / f"{branchname_upper}.json",
        target_dir / f"{branchname_upper}.local.json",
        target_dir / f"{branchname_upper}.observations.json",
        target_dir / f"{branchname_upper}.ai_mail.json",
        target_dir / f"{branchname_upper}.id.json",
    ]

    issues: List[Tuple[Path, List[str]]] = []
    for file_path in expected_files:
        if not file_path.exists() or not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError) as exc:
            logger.warning(f"Placeholder scan skipped for {file_path}: {exc}")
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
        "TIMESTAMP": now.strftime("%Y-%m-%d %H:%M:%S"),
        "REPO": repo,
        "PROFILE": profile,

        # New auto-fills
        "INSTANCE_NAME": branchname_upper,  # Same as BRANCHNAME
        "EMAIL": "aipass.system@gmail.com",  # Universal system email
        "AUTO_TIMESTAMP": now.strftime("%Y-%m-%d %H:%M:%S"),
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
    file_renames: Dict[str, str]
) -> Tuple[List[str], List[str]]:
    """
    Copy template contents to target directory

    Args:
        template_dir: Path to template directory
        target_dir: Path to target directory
        replacements: Dict of placeholder replacements
        branch_name: Branch name
        exclude_patterns: List of patterns to exclude
        file_renames: Dict mapping template names to rename patterns

    Returns:
        Tuple of (copied items list, skipped items list)
    """
    copied = []
    skipped = []

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

                # Store original for comparison
                original_content = content
                content = replace_placeholders(content, replacements)

                # Validate all placeholders were replaced
                is_valid, unreplaced = validate_no_placeholders(content, str(rel_path))

                if not is_valid:
                    print(f"\n{'='*70}")
                    print(f"❌ ERROR: UNREPLACED PLACEHOLDERS DETECTED")
                    print(f"{'='*70}")
                    print(f"File: {rel_path}")
                    print(f"Placeholders NOT replaced: {unreplaced}")
                    print(f"\n⚠️ Available replacement keys:")
                    for key in sorted(replacements.keys()):
                        print(f"  - {key}")
                    print(f"\n⚠️ First 300 characters of output:")
                    print(f"{content[:300]}")
                    print(f"{'='*70}\n")

                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                copied.append(str(rel_path))
            except (UnicodeDecodeError, UnicodeEncodeError):
                # Binary file or encoding issue - just copy
                shutil.copy2(item, target_path)
                copied.append(f"{rel_path} (binary)")

    return copied, skipped


# =============================================================================
# REGISTRY OPERATIONS (JSON-BASED)
# =============================================================================

def get_branch_registry_path() -> Path:
    """
    Get path to JSON branch registry - single point of change for path migration

    Returns:
        Path to BRANCH_REGISTRY.json at /home/aipass/BRANCH_REGISTRY.json
    """
    registry_path = Path.home() / "BRANCH_REGISTRY.json"
    logger.info(f"Branch registry path: {registry_path}")
    return registry_path


def load_registry() -> Dict:
    """
    Load branch registry from JSON file

    Returns:
        Dict containing registry data, or empty schema if file doesn't exist
    """
    registry_path = get_branch_registry_path()

    if not registry_path.exists():
        logger.info(f"Registry file not found at {registry_path}, returning empty schema")
        # Return empty schema
        return {
            "metadata": {
                "version": "1.0.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "total_branches": 0
            },
            "branches": []
        }

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded registry with {len(data.get('branches', []))} branches")
            return data
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load registry from {registry_path}: {e}")
        print(f"⚠️ Warning: Failed to load registry: {e}")
        # Return empty schema on error
        return {
            "metadata": {
                "version": "1.0.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "total_branches": 0
            },
            "branches": []
        }


def save_registry(data: Dict) -> bool:
    """
    Save registry data to JSON file

    Args:
        data: Registry data dict

    Returns:
        True on success, False on error
    """
    registry_path = get_branch_registry_path()

    # Auto-update last_updated timestamp
    data["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    try:
        # Ensure parent directory exists
        registry_path.parent.mkdir(parents=True, exist_ok=True)

        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved registry to {registry_path} with {len(data.get('branches', []))} branches")
        return True
    except (IOError, TypeError) as e:
        logger.error(f"Failed to save registry to {registry_path}: {e}")
        print(f"❌ Error: Failed to save registry: {e}")
        return False


def find_branch_in_registry(branch_name: str) -> Optional[Dict]:
    """
    Find branch entry in registry by name

    Args:
        branch_name: Branch name to search for

    Returns:
        Branch entry dict if found, None otherwise
    """
    registry = load_registry()

    for branch in registry.get("branches", []):
        if branch.get("name") == branch_name:
            return branch

    return None


def add_registry_entry(entry: Dict) -> bool:
    """
    Add new branch entry to registry

    Args:
        entry: Branch entry dict with required fields

    Returns:
        True on success, False on error
    """
    # Validate required fields
    required_fields = ["name", "path", "profile", "description", "email"]
    for field in required_fields:
        if field not in entry:
            print(f"❌ Error: Missing required field '{field}' in registry entry")
            return False

    # Load current registry
    registry = load_registry()

    # Check if already exists
    if find_branch_in_registry(entry["name"]):
        print(f"⚠️ Warning: Branch '{entry['name']}' already registered")
        return False

    # Add created/last_active dates if not present
    today = datetime.now().strftime("%Y-%m-%d")
    if "created" not in entry:
        entry["created"] = today
    if "last_active" not in entry:
        entry["last_active"] = today
    if "status" not in entry:
        entry["status"] = "active"

    # Add to branches list
    registry["branches"].append(entry)

    # Update total count
    registry["metadata"]["total_branches"] = len(registry["branches"])

    # Save
    return save_registry(registry)


def remove_registry_entry(branch_name: str) -> bool:
    """
    Remove branch entry from registry

    Args:
        branch_name: Branch name to remove

    Returns:
        True if found and removed, False if not found
    """
    registry = load_registry()

    # Find and remove branch
    original_count = len(registry["branches"])
    registry["branches"] = [
        b for b in registry["branches"]
        if b.get("name") != branch_name
    ]

    if len(registry["branches"]) == original_count:
        # Branch not found
        return False

    # Update total count
    registry["metadata"]["total_branches"] = len(registry["branches"])

    # Save
    save_registry(registry)
    return True


def register_branch(target_dir: Path, branch_name: str, branchname_upper: str) -> Optional[str]:
    """
    Register new branch in JSON registry

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name (lowercase with hyphens)
        branchname_upper: Branch name (uppercase with underscores)

    Returns:
        Status message or None if registration failed
    """
    # Determine profile based on path
    path_str = str(target_dir)
    if path_str.startswith("/home/aipass-business/"):
        profile = "AIPass Business"
    elif path_str.startswith("/home/input-x/"):
        profile = "Input-X"
    elif path_str.startswith("/home/aipass/"):
        profile = "AIPass Workshop"
    else:
        profile = "Admin"

    # Derive email from branch name
    email = f"@{branch_name.lower().replace('-', '_')}"

    # Build registry entry
    entry = {
        "name": branchname_upper,
        "path": str(target_dir),
        "profile": profile,
        "description": "New branch - purpose TBD",
        "email": email,
        "status": "active"
    }

    # Add to registry
    if add_registry_entry(entry):
        return f"Registered in BRANCH_REGISTRY.json as {branchname_upper}"
    else:
        # Check if already registered
        if find_branch_in_registry(branchname_upper):
            return "Already registered"
        return None
