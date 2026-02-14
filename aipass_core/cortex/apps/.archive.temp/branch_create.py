#!/usr/bin/env python3

# ===================AIPASS====================
# META DATA HEADER
# Name: branch_new.py - AIPass Branch Setup Script
# Date: 2025-10-29
# Version: 1.0.0
# Category: branch_operations
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-10-29): Initial standardized version - Added META header
# =============================================

"""
AIPass Branch Setup Script
Copies template structure to new/existing branch with auto-healing

Tests: See tests/test_branch_new.py for comprehensive test coverage
"""

# =============================================
# IMPORTS
# =============================================

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))

# Standard library imports
import argparse
import json
from datetime import datetime, timezone
from typing import Dict

# AIPass infrastructure imports
from prax.apps.prax_logger import system_logger as logger

# Import all functions from branch_lib
from branch_lib import (
    get_branch_name,
    detect_profile,
    get_git_repo,
    generate_tree,
    replace_placeholders,
    find_existing_memory_files,
    detect_naming_mismatches,
    smart_rename_memory_files,
    rename_files,
    rename_json_directory,
    migrate_modules_to_apps,
    should_exclude,
    will_be_renamed,
    copy_template_contents,
    register_branch,
    detect_unreplaced_placeholders,
    build_replacements_dict,
)

# =============================================
# CONSTANTS & CONFIG
# =============================================

# Module root and JSON directory
MODULE_ROOT = Path(__file__).parent.parent
BRANCH_OPS_JSON_DIR = MODULE_ROOT / "branch_operations_json"

# Auto-create JSON directory
BRANCH_OPS_JSON_DIR.mkdir(exist_ok=True)

# 3-file JSON structure for branch_new module
CONFIG_FILE = BRANCH_OPS_JSON_DIR / "branch_new_config.json"
DATA_FILE = BRANCH_OPS_JSON_DIR / "branch_new_data.json"
LOG_FILE = BRANCH_OPS_JSON_DIR / "branch_new_log.json"

# Path getter function for migration readiness
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

TEMPLATE_DIR = get_template_dir()

# Files/directories to exclude
EXCLUDE_PATTERNS = [
    "setup_instructions",
    "new_branch_setup.py",
    "upgrade_branch.py",
    ".git",
    "__pycache__",
]

# Files to rename after copying
FILE_RENAMES = {
    "PROJECT.json": "{BRANCHNAME}.json",
    "LOCAL..json": "{BRANCHNAME}.local.json",
    "OBSERVATIONS.json": "{BRANCHNAME}.observations.json",
    "AI_MAIL.json": "{BRANCHNAME}.ai_mail.json",
    "BRANCH.ID.json": "{BRANCHNAME}.id.json",
}

# =============================================
# HELPER FUNCTIONS
# =============================================

def log_operation(operation: str, success: bool, details: str = "", error: str = ""):
    """
    Log branch_new operations to module-specific log file

    Args:
        operation: Operation name (e.g., "branch_setup_start")
        success: Whether operation succeeded
        details: Additional details about the operation
        error: Error message if operation failed
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
        logger.error(f"[branch_new] Error saving log: {e}")


def load_config() -> Dict:
    """Load branch_new configuration"""
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
        logger.error(f"[branch_new] Error loading config: {e}")
        return default_config


def save_config(config: Dict):
    """Save branch_new configuration"""
    try:
        BRANCH_OPS_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_new] Error saving config: {e}")


def load_data() -> Dict:
    """Load branch_new runtime data"""
    default_data = {
        "created": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "operations_total": 0,
        "operations_successful": 0,
        "operations_failed": 0,
        "branches_created": 0
    }

    if not DATA_FILE.exists():
        return default_data

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[branch_new] Error loading data: {e}")
        return default_data


def save_data(data: Dict):
    """Save branch_new runtime data with auto timestamp"""
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    try:
        BRANCH_OPS_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_new] Error saving data: {e}")


def generate_branch_meta_json(target_dir: Path, branch_name: str) -> bool:
    """
    Generate .branch_meta.json tracking file IDs from template

    Loads template_registry.json and maps actual branch filenames to template IDs.
    This enables branch_update.py to detect renames vs new files vs pruned files.

    Args:
        target_dir: Branch directory path
        branch_name: Branch name (used for identifying renamed files)

    Returns:
        True if successful, False if template_registry.json not found
    """
    # Load template registry
    template_registry_path = TEMPLATE_DIR / "template_registry.json"
    if not template_registry_path.exists():
        logger.warning(f"[branch_new] template_registry.json not found at {template_registry_path}")
        return False

    try:
        with open(template_registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    except Exception as e:
        logger.error(f"[branch_new] Error loading template_registry.json: {e}")
        return False

    # Build reverse lookup: template_filename -> template_id
    template_name_to_id = {}

    # Map files
    for file_id, file_info in registry.get("files", {}).items():
        template_name_to_id[file_info["current_name"]] = file_id

    # Map directories
    for dir_id, dir_info in registry.get("directories", {}).items():
        template_name_to_id[dir_info["current_name"]] = dir_id

    # Build mapping: actual_filename -> template_id
    file_tracking = {}
    branch_upper = branch_name.upper().replace("-", "_")

    # Map renamed files (handle {{BRANCH}} placeholder substitution)
    for template_name, template_id in template_name_to_id.items():
        # Handle placeholder patterns
        if "{{BRANCH}}" in template_name:
            actual_name = template_name.replace("{{BRANCH}}", branch_upper)
        else:
            # Check if this file gets renamed by FILE_RENAMES
            if template_name in FILE_RENAMES:
                actual_name = FILE_RENAMES[template_name].replace("{BRANCHNAME}", branch_upper)
            else:
                actual_name = template_name

        # Check if file/directory exists in branch
        file_path = target_dir / actual_name
        if file_path.exists():
            file_tracking[actual_name] = template_id

    # Create .branch_meta.json
    meta_data = {
        "template_version": registry.get("metadata", {}).get("version", "1.0.0"),
        "branch_created": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "file_tracking": file_tracking
    }

    meta_path = target_dir / ".branch_meta.json"
    try:
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, indent=2, ensure_ascii=False)
        logger.info(f"[branch_new] Generated .branch_meta.json with {len(file_tracking)} tracked files")
        return True
    except Exception as e:
        logger.error(f"[branch_new] Error saving .branch_meta.json: {e}")
        return False


def print_setup_report(copied: list, skipped: list, renamed: list, json_rename: str | None,
                       migrated_modules: list, registration_result: str | None,
                       naming_mismatches: list) -> None:
    """
    Print detailed setup completion report

    Args:
        copied: List of copied files/directories
        skipped: List of skipped files (already existed)
        renamed: List of renamed files
        json_rename: JSON directory rename result
        migrated_modules: List of modules migrated to apps/
        registration_result: Branch registration result message
        naming_mismatches: List of files with naming convention mismatches
    """
    print(f"\n✅ Setup complete!")
    print(f"\nCopied: {len(copied)} files/directories")
    if copied and len(copied) <= 20:
        for item in copied:
            print(f"  + {item}")

    if renamed:
        print(f"\nRenamed: {len(renamed)} files")
        for item in renamed:
            print(f"  → {item}")

    if json_rename:
        print(f"\nDirectory renamed:")
        print(f"  → {json_rename}")

    if migrated_modules:
        print(f"\nMigrated to apps/: {len(migrated_modules)} Python module(s)")
        for module in migrated_modules:
            print(f"  → {module}")

    if registration_result:
        print(f"\nBranch Registration:")
        print(f"  ✅ {registration_result}")

    if skipped:
        print(f"\n⚠️  Skipped (already exist): {len(skipped)} files")
        if len(skipped) <= 10:
            for item in skipped:
                print(f"  - {item}")
        else:
            print(f"  (showing first 10)")
            for item in skipped[:10]:
                print(f"  - {item}")

    # Warn about naming mismatches
    if naming_mismatches:
        print(f"\n⚠️  WARNING: Naming Convention Mismatch Detected!")
        print(f"Found {len(naming_mismatches)} file(s) with non-standard naming:")
        for wrong_name, correct_name in naming_mismatches:
            print(f"  ❌ {wrong_name}")
            print(f"  ✅ {correct_name} (correct)")
        print(f"\nThese files likely have the same content but different names.")
        print(f"Please manually review and remove duplicates.")
        print(f"Standard: Branch names use UNDERSCORES (not hyphens) in uppercase.")


# =============================================
# MAIN FUNCTIONS
# =============================================

def main():
    parser = argparse.ArgumentParser(
        description='AIPass Branch Setup - Create new branch with template structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: setup

  setup <target_dir> - Create new branch structure from template

EXAMPLES:
  python3 branch_new.py /home/aipass/analytics
  python3 branch_new.py /home/aipass/aipass_core/backup_system
  /home/aipass/.venv/bin/python /home/aipass/aipass_core/branch_operations/apps/branch_new.py /home/aipass/aipass_core/<folder_name>
        """
    )
    parser.add_argument('target_directory', help='Path to branch directory (will be created if needed)')

    args = parser.parse_args()

    # Initialize JSON infrastructure
    config = load_config()
    data = load_data()

    # Get target directory
    target_dir = Path(args.target_directory).resolve()
    logger.info(f"Branch setup initiated for: {target_dir}")

    # Log operation start
    log_operation(
        operation="branch_setup_start",
        success=True,
        details=f"Initiating branch setup for: {target_dir}"
    )

    try:
        # Create target directory if doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        # Extract branch info
        branch_name = get_branch_name(target_dir)
        branchname_upper = branch_name.upper().replace("-", "_")

        # Detect profile and repo
        profile = detect_profile(target_dir)
        repo = get_git_repo(target_dir)

        # Build replacements dictionary
        replacements = build_replacements_dict(branch_name, target_dir, repo, profile)

        print(f"\n=== AIPass Branch Setup ===")
        print(f"Target: {target_dir}")
        print(f"Branch: {branch_name} ({branchname_upper})")
        print(f"Profile: {profile}")
        print(f"Repo: {repo}")
        print()

        # Smart rename existing memory files FIRST (before copying templates)
        print("Checking for existing memory files...")
        smart_renamed = smart_rename_memory_files(target_dir, branch_name)
        if smart_renamed:
            print(f"Renamed {len(smart_renamed)} existing memory file(s) to standard convention:")
            for item in smart_renamed:
                print(f"  → {item}")
            print()

        # Copy template contents
        print("Copying template contents...")
        copied, skipped = copy_template_contents(TEMPLATE_DIR, target_dir, replacements, branch_name, EXCLUDE_PATTERNS, FILE_RENAMES)
        logger.info(f"Template copy complete: {len(copied)} items copied, {len(skipped)} skipped")

        # Rename files
        print("\nRenaming files...")
        renamed = rename_files(target_dir, branch_name, FILE_RENAMES)
        logger.info(f"File renaming complete: {len(renamed)} files renamed")

        # Rename json directory
        json_rename = rename_json_directory(target_dir, branch_name)

        # Migrate Python modules to apps/ directory
        print("\nMigrating Python modules to apps/...")
        migrated_modules = migrate_modules_to_apps(target_dir)

        # Register branch in CLAUDE.md
        print("\nRegistering branch...")
        registration_result = register_branch(target_dir, branch_name, branchname_upper)

        # Generate tree output AFTER files are copied and update README.md
        print("\nGenerating directory tree...")
        tree_output = generate_tree(target_dir)
        readme_path = target_dir / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8')
            content = content.replace("{{TREE_PLACEHOLDER}}", tree_output)
            readme_path.write_text(content, encoding='utf-8')

        # Generate .branch_meta.json for tracking file IDs
        print("\nGenerating branch metadata...")
        meta_generated = generate_branch_meta_json(target_dir, branch_name)
        if meta_generated:
            print("  ✅ .branch_meta.json created (tracks template file IDs)")
        else:
            print("  ⚠️  .branch_meta.json skipped (template_registry.json not found)")

        # Detect naming mismatches (files with wrong naming convention)
        naming_mismatches = detect_naming_mismatches(target_dir, branch_name, FILE_RENAMES)

        # Validate that no template placeholders remain in critical branch files
        allowed_placeholders = {"AUTO_GENERATED_COMMANDS", "TREE_PLACEHOLDER"}
        placeholder_issues = detect_unreplaced_placeholders(
            target_dir,
            branch_name,
            allowed_placeholders=allowed_placeholders
        )
        if placeholder_issues:
            print("\n❌ ERROR: Unreplaced template placeholders detected after setup.")
            print("The following files still contain {{PLACEHOLDER}} tokens:")
            for file_path, placeholders in placeholder_issues:
                relative_path = file_path.relative_to(target_dir)
                placeholder_list = ", ".join(sorted(set(placeholders)))
                print(f"  - {relative_path}: {placeholder_list}")
            print("\nFix suggestion: ensure branch_update.py or placeholder replacement logic")
            print("applies to pre-existing files, then rerun this setup.")
            logger.error(
                f"Placeholder validation failed for branch {branch_name}: {placeholder_issues}"
            )
            raise RuntimeError("Unreplaced placeholders detected in branch files")

        # Print detailed completion report
        print_setup_report(copied, skipped, renamed, json_rename, migrated_modules,
                          registration_result, naming_mismatches)

        logger.info(f"Branch setup complete: {branch_name} at {target_dir}")

        # Log successful operation
        log_operation(
            operation="branch_setup_complete",
            success=True,
            details=f"Branch '{branch_name}' successfully created at {target_dir}. Files: {len(copied)} copied, {len(renamed)} renamed"
        )

        # Update statistics
        data["operations_total"] += 1
        data["operations_successful"] += 1
        data["branches_created"] += 1
        save_data(data)

        print(f"\n✅ Branch ready at: {target_dir}")
        print()

    except Exception as e:
        logger.error(f"Branch setup failed: {str(e)}")

        # Log failed operation
        log_operation(
            operation="branch_setup_failed",
            success=False,
            details=f"Branch setup failed at {target_dir}: {str(e)}"
        )

        # Update statistics
        data["operations_total"] += 1
        data["operations_failed"] += 1
        save_data(data)

        print(f"\n❌ Error: Branch setup failed - {str(e)}")
        print(f"   Target directory: {target_dir}")
        raise

# =============================================
# CLI/EXECUTION
# =============================================

if __name__ == "__main__":
    main()
