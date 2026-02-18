#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: create_branch.py - Create New AIPass Branch
# Date: 2025-11-15
# Version: 1.1.0
# Category: cortex
# Commands: create, create-branch, new, --help
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2025-11-15): Added drone compliance (Commands line in help)
#   - v1.0.0 (2025-11-04): Clean implementation - pure branch creation, no infrastructure
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Create Branch Module

Creates a new AIPass branch from template with all necessary structure.
Workflow: template copy, file renaming, module migration, branch registration
"""

import sys
from pathlib import Path
from typing import List, Tuple, Optional

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Prax logger
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

# Handler imports - graceful degradation if handlers unavailable
HANDLERS_AVAILABLE = True
HANDLER_ERROR = None

try:
    from cortex.apps.handlers.branch.metadata import (
        get_branch_name,
        detect_profile,
        get_git_repo,
        generate_tree
    )

    from cortex.apps.handlers.branch.placeholders import (
        build_replacements_dict,
        detect_unreplaced_placeholders,
        detect_naming_mismatches
    )

    from cortex.apps.handlers.branch.file_ops import (
        copy_template_contents,
        rename_files,
        rename_json_directory,
        migrate_modules_to_apps,
        smart_rename_memory_files,
        update_readme_tree_placeholders
    )

    # NOTE: error.formatters removed - using direct console output
    # from cortex.apps.handlers.error.formatters import (
    #     display_validation_summary,
    #     display_placeholder_issues,
    #     display_branch_creation_report
    # )

    from cortex.apps.handlers.branch.registry import (
        register_branch
    )

    from cortex.apps.handlers.json import json_handler

except ImportError as e:
    # Define placeholder types for type checker
    get_branch_name = None  # type: ignore
    detect_profile = None  # type: ignore
    get_git_repo = None  # type: ignore
    generate_tree = None  # type: ignore
    build_replacements_dict = None  # type: ignore
    detect_unreplaced_placeholders = None  # type: ignore
    detect_naming_mismatches = None  # type: ignore
    copy_template_contents = None  # type: ignore
    rename_files = None  # type: ignore
    rename_json_directory = None  # type: ignore
    migrate_modules_to_apps = None  # type: ignore
    smart_rename_memory_files = None  # type: ignore
    update_readme_tree_placeholders = None  # type: ignore
    register_branch = None  # type: ignore
    json_handler = None  # type: ignore
    logger.error(f"Handler import failed: {e}")
    HANDLERS_AVAILABLE = False
    HANDLER_ERROR = str(e)


# =============================================================================
# CONSTANTS
# =============================================================================

# Get template directory
AIPASS_ROOT = Path.home() / "aipass_core"
TEMPLATE_DIR = AIPASS_ROOT / "cortex" / "templates" / "branch_template"

# Files to exclude from template copy
EXCLUDE_PATTERNS = [
    "setup_instructions",
    "new_branch_setup.py",
    "upgrade_branch.py",
    ".git",
    "__pycache__",
]

# Files to rename after copying
FILE_RENAMES = {
    "LOCAL.json": "{BRANCHNAME}.local.json",
    "OBSERVATIONS.json": "{BRANCHNAME}.observations.json",
    "AI_MAIL.json": "{BRANCHNAME}.ai_mail.json",
    "BRANCH.ID.json": "{BRANCHNAME}.id.json",
    "apps/BRANCH.py": "apps/{branchname}.py",
}

# Help text for drone compliance
HELP_TEXT = """
======================================================================
CREATE BRANCH - AIPass Branch Creation
======================================================================

Creates a new AIPass branch from template with complete structure.

USAGE:
  cortex create-branch <target_directory> [OPTIONS]

OPTIONS:
  --role "Role description"      Set branch role in identity
  --traits "Trait1, trait2"      Set branch traits in identity
  --purpose "Purpose brief"      Set branch purpose in README and identity

EXAMPLES:
  cortex create-branch /home/aipass/my_branch
  cortex create-branch /home/aipass/my_branch --role "Data Processing" --traits "Fast, reliable" --purpose "ETL pipeline management"

WHAT IT DOES:
  - Copies template structure to target directory
  - Renames memory files (LOCAL.json, OBSERVATIONS.json, etc.)
  - Replaces placeholders with branch-specific values
  - Fills identity fields if --role/--traits/--purpose provided
  - Registers branch in BRANCH_REGISTRY.json
  - Generates directory tree documentation

======================================================================

Commands: create, create-branch, new, --help
"""


# =============================================================================
# CORE WORKFLOW
# =============================================================================

def create_branch(target_dir: Path, overrides: Optional[dict] = None) -> bool:
    """
    Create new branch from template

    Args:
        target_dir: Path where branch will be created
        overrides: Optional dict of placeholder overrides (e.g. ROLE, TRAITS, PURPOSE_BRIEF)

    Returns:
        True if successful, False otherwise
    """
    if not HANDLERS_AVAILABLE:
        console.print(f"\n❌ Handlers not available: {HANDLER_ERROR}")
        return False

    try:
        # Create target directory if doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        # Extract branch info
        branch_name = get_branch_name(target_dir)
        branchname_upper = branch_name.upper().replace("-", "_")

        # Detect profile and repo
        profile = detect_profile(target_dir)
        repo = get_git_repo(target_dir)

        # Build replacements dictionary with optional identity overrides
        replacements = build_replacements_dict(branch_name, target_dir, repo, profile, overrides=overrides)

        console.print(f"\n=== Create Branch ===")
        console.print(f"Target: {target_dir}")
        console.print(f"Branch: {branch_name} ({branchname_upper})")
        console.print(f"Profile: {profile}")
        console.print(f"Repo: {repo}")
        console.print()

        # Log operation start
        json_handler.log_operation(
            'branch_creation_started',
            {'branch': branchname_upper, 'path': str(target_dir), 'profile': profile},
            'create_branch'
        )

        # Smart rename existing memory files FIRST
        console.print("Checking for existing memory files...")
        smart_renamed = smart_rename_memory_files(target_dir, branch_name)
        if smart_renamed:
            console.print(f"Renamed {len(smart_renamed)} existing memory file(s):")
            for item in smart_renamed:
                console.print(f"  → {item}")
            console.print()

        # Copy template contents
        console.print("Copying template contents...")
        # README automation placeholders (intentionally not replaced)
        allowed_placeholders = {
            "AUTO_GENERATED_COMMANDS", "TREE_PLACEHOLDER", "MODULE_NAME", "placeholder",
            "DOCUMENT_TYPE", "DOCUMENT_NAME", "TAG_1", "TAG_2", "TAG_3",
            "MODULE",
            "EMOJI_1", "EMOJI_1_DESCRIPTION", "EMOJI_2", "EMOJI_2_DESCRIPTION",
            "EMOJI_3", "EMOJI_3_DESCRIPTION",
            "BRIEF_SUMMARY", "MAIN_TOPIC", "KEY_POINT_1", "KEY_POINT_2", "KEY_POINT_3",
            "NARRATIVE_CONTENT", "SECTION_1_CONTENT", "SECTION_2_CONTENT",
            "SECTION_3_CONTENT", "CONCLUSION_CONTENT",
            "DOCUMENT_PURPOSE", "HOW_TO_USE", "PRIORITY_LEVEL", "TIMESTAMP",
            "PLACEHOLDER",
            "AUTO_GENERATED_MODULES", "AUTO_GENERATED_DEPENDENCIES", "AUTO_GENERATED_IMPORTS",
            "KEY_CAPABILITIES", "BASIC_USAGE", "COMMON_WORKFLOWS", "EXAMPLES",
            "DEPENDS_ON", "INTEGRATES_WITH", "PROVIDES_TO",
        }
        copied, skipped, validation_errors = copy_template_contents(
            TEMPLATE_DIR, target_dir, replacements, branch_name, EXCLUDE_PATTERNS, FILE_RENAMES, allowed_placeholders
        )

        # Show validation errors if any
        if validation_errors:
            console.print("\n⚠️  Validation Errors:")
            for error in validation_errors:
                console.print(f"  - {error}")
            return False

        # Rename files
        console.print("\nRenaming files...")
        renamed, missing = rename_files(target_dir, branch_name, FILE_RENAMES)

        # Report missing files as error
        if missing:
            console.print(f"\n❌ ERROR: Expected files not found for renaming:")
            for filename in missing:
                console.print(f"  - {filename}")

        # Rename json directory
        json_rename = rename_json_directory(target_dir, branch_name)

        # Migrate Python modules to apps/ directory
        console.print("\nMigrating Python modules to apps/...")
        migrated_modules = migrate_modules_to_apps(target_dir)

        # Register branch
        console.print("\nRegistering branch...")
        registration_result = register_branch(target_dir, branch_name, branchname_upper)

        # Generate tree output
        console.print("\nGenerating directory tree...")
        tree_output = generate_tree(target_dir)
        update_readme_tree_placeholders(target_dir, tree_output)

        # Detect naming mismatches
        naming_mismatches = detect_naming_mismatches(target_dir, branch_name, FILE_RENAMES)

        # Validate no unreplaced placeholders
        allowed_placeholders = {
            "AUTO_GENERATED_COMMANDS", "TREE_PLACEHOLDER",
            # README automation placeholders (intentionally not replaced)
            "AUTO_GENERATED_MODULES", "AUTO_GENERATED_DEPENDENCIES", "AUTO_GENERATED_IMPORTS",
            "KEY_CAPABILITIES", "BASIC_USAGE", "COMMON_WORKFLOWS", "EXAMPLES",
            "DEPENDS_ON", "INTEGRATES_WITH", "PROVIDES_TO",
        }
        placeholder_issues = detect_unreplaced_placeholders(
            target_dir,
            branch_name,
            allowed_placeholders=allowed_placeholders
        )

        if placeholder_issues:
            console.print("\n⚠️  Unreplaced Placeholders Found:")
            for issue in placeholder_issues:
                console.print(f"  - {issue}")
            return False

        # Print completion report
        console.print(f"\n{'='*70}")
        console.print("BRANCH CREATION REPORT")
        console.print(f"{'='*70}")
        console.print(f"Files copied: {len(copied)}")
        console.print(f"Files skipped: {len(skipped)}")
        console.print(f"Files renamed: {len(renamed)}")
        if json_rename:
            console.print(f"JSON directory: {json_rename}")
        console.print(f"Modules migrated: {len(migrated_modules)}")
        console.print(f"Registration: {registration_result}")
        if naming_mismatches:
            console.print(f"\n⚠️  Naming mismatches: {len(naming_mismatches)}")
            for old, new in naming_mismatches:
                console.print(f"  {old} should be {new}")

        console.print(f"\n✅ Branch ready at: {target_dir}")
        console.print()

        # Log operation completion and update stats
        json_handler.log_operation(
            'branch_creation_completed',
            {
                'branch': branchname_upper,
                'success': True,
                'files_copied': copied,
                'files_skipped': skipped,
                'files_renamed': len(renamed),
                'modules_migrated': len(migrated_modules)
            },
            'create_branch'
        )

        # Update data metrics
        json_handler.increment_counter('create_branch', 'branches_created')
        json_handler.increment_counter('create_branch', 'operations_successful')

        # Fire trigger event
        try:
            from trigger.apps.modules.core import trigger
            trigger.fire('branch_created', branch=branchname_upper, path=str(target_dir))
        except ImportError:
            pass  # Silent fallback

        return True

    except Exception as e:
        logger.error(f"Branch creation failed: {e}")
        console.print(f"\n❌ Error: Branch creation failed - {str(e)}")
        console.print(f"   Target directory: {target_dir}")

        # Log failure
        json_handler.log_operation(
            'branch_creation_failed',
            {'branch': str(target_dir.name), 'error': str(e)},
            'create_branch'
        )
        json_handler.increment_counter('create_branch', 'operations_failed')

        return False


# =============================================================================
# MODULE INTERFACE
# =============================================================================

def handle_command(args) -> bool:
    """
    Orchestrator interface for create_branch

    Args:
        args: Command arguments (argparse Namespace)

    Returns:
        True if command handled, False otherwise
    """
    # Check if this module should handle the command FIRST
    # Handle: create, create-branch, new
    if not hasattr(args, 'command') or args.command not in ['create', 'create-branch', 'new']:
        return False

    # Then check if handlers are available
    if not HANDLERS_AVAILABLE:
        console.print(f"[create_branch] Handlers unavailable: {HANDLER_ERROR}")
        return True

    # Check if target directory provided
    if not hasattr(args, 'target_directory') or not args.target_directory:
        console.print("Error: target_directory required")
        console.print("Usage: cortex create <target_directory>")
        console.print("   or: cortex create-branch <target_directory>")
        console.print("   or: cortex new <target_directory>")
        return True

    target_dir = Path(args.target_directory).resolve()

    # Build overrides from optional CLI args
    overrides = {}
    if hasattr(args, 'role') and args.role:
        overrides['ROLE'] = args.role
    if hasattr(args, 'traits') and args.traits:
        overrides['TRAITS'] = args.traits
    if hasattr(args, 'purpose') and args.purpose:
        overrides['PURPOSE_BRIEF'] = args.purpose

    return create_branch(target_dir, overrides=overrides if overrides else None)


# =============================================================================
# DRONE COMPLIANCE - HELP SYSTEM
# =============================================================================

def print_help():
    """Display drone-compliant help output"""
    console.print(HELP_TEXT)


# =============================================================================
# STANDALONE EXECUTION (for testing/debugging)
# =============================================================================

if __name__ == "__main__":
    import sys
    import argparse as _argparse

    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    # Check if target directory provided
    if len(sys.argv) > 1:
        _parser = _argparse.ArgumentParser(add_help=False)
        _parser.add_argument('target_directory')
        _parser.add_argument('--role', default=None)
        _parser.add_argument('--traits', default=None)
        _parser.add_argument('--purpose', default=None)
        _args = _parser.parse_args()

        target_path = Path(_args.target_directory).resolve()
        _overrides = {}
        if _args.role:
            _overrides['ROLE'] = _args.role
        if _args.traits:
            _overrides['TRAITS'] = _args.traits
        if _args.purpose:
            _overrides['PURPOSE_BRIEF'] = _args.purpose

        success = create_branch(target_path, overrides=_overrides if _overrides else None)
        sys.exit(0 if success else 1)

    # No arguments - show status
    console.print("\n" + "="*60)
    console.print("create_branch - Module Status Report")
    console.print("="*60)

    console.print(f"\nModule: create_branch.py")
    console.print(f"Purpose: Create new AIPass branches from template")
    console.print(f"Status: {'✅ Ready' if HANDLERS_AVAILABLE else '❌ Handlers Missing'}")

    if HANDLERS_AVAILABLE:
        console.print(f"\nHandlers:")
        console.print(f"  ✅ metadata (get_branch_name, detect_profile, get_git_repo, generate_tree)")
        console.print(f"  ✅ placeholders (build_replacements_dict, detect_unreplaced_placeholders, detect_naming_mismatches)")
        console.print(f"  ✅ file_ops (copy_template_contents, rename_files, rename_json_directory, migrate_modules_to_apps, smart_rename_memory_files)")
        console.print(f"  ✅ registry (register_branch)")
        console.print(f"\nReady to create branches!")
    else:
        console.print(f"\nHandler Error:")
        console.print(f"  {HANDLER_ERROR}")
        console.print(f"\nAction: Populate handler files in apps/handlers/branch/")
        console.print(f"  - metadata.py")
        console.print(f"  - placeholders.py")
        console.print(f"  - file_ops.py")
        console.print(f"  - registry.py")

    console.print(f"\nUsage:")
    console.print(f"  Direct: python3 create_branch.py <target_directory>")
    console.print(f"  Orchestrator: cortex create-branch <target_directory>")
    console.print("="*60 + "\n")
