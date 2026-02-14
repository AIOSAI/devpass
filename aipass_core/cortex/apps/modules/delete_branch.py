#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: delete_branch.py - Delete AIPass Branch
# Date: 2025-11-15
# Version: 1.1.0
# Category: cortex
# Commands: delete, delete-branch, --help
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2025-11-15): Added drone compliance (Commands line in help)
#   - v1.0.0 (2025-11-04): Clean implementation - pure branch deletion, no infrastructure
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Delete Branch Module

Deletes an AIPass branch with proper cleanup:
- Two-step confirmation (y/N prompt)
- Backup to deleted_branches directory
- Registry removal
- Directory deletion
"""

import sys
from pathlib import Path
import shutil
from datetime import datetime

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Prax logger
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console
from rich.prompt import Confirm

# Handler imports - graceful degradation if handlers unavailable
HANDLERS_AVAILABLE = True
HANDLER_ERROR = None

try:
    from cortex.apps.handlers.branch.metadata import (
        get_branch_name
    )

    from cortex.apps.handlers.branch.registry import (
        find_branch_in_registry,
        remove_registry_entry
    )


    from cortex.apps.handlers.json import json_handler

except ImportError as e:
    # Define placeholder types for type checker
    get_branch_name = None  # type: ignore
    find_branch_in_registry = None  # type: ignore
    remove_registry_entry = None  # type: ignore
    json_handler = None  # type: ignore
    logger.error(f"Handler import failed: {e}")
    HANDLERS_AVAILABLE = False
    HANDLER_ERROR = str(e)


# =============================================================================
# CONSTANTS
# =============================================================================

# Backup system directory for deleted branches
BACKUP_SYSTEM_ROOT = AIPASS_ROOT / "backup_system"
DELETED_BRANCHES_DIR = BACKUP_SYSTEM_ROOT / "deleted_branches"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def backup_branch(branch_path: Path, branch_name: str) -> Path:
    """
    Backup branch to deleted_branches directory

    Args:
        branch_path: Path to branch directory
        branch_name: Branch name (uppercase)

    Returns:
        Path to backup directory

    Raises:
        Exception if backup fails
    """
    # Create deleted_branches directory if needed
    # DIRECT OPERATION JUSTIFIED: System infrastructure directory creation
    # No handler exists for system-level directory creation (handlers are for branch operations)
    DELETED_BRANCHES_DIR.mkdir(parents=True, exist_ok=True)

    # Generate timestamped backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir_name = f"{branch_name}_deleted_{timestamp}"
    backup_path = DELETED_BRANCHES_DIR / backup_dir_name

    # Copy entire branch directory
    shutil.copytree(branch_path, backup_path, symlinks=False)

    # Fire trigger event
    try:
        from trigger.apps.modules.core import trigger
        trigger.fire('branch_backup_created', branch=branch_name, backup_path=str(backup_path))
    except ImportError:
        pass  # Silent fallback

    return backup_path


def delete_branch(target_dir: Path) -> bool:
    """
    Delete branch with proper cleanup

    Args:
        target_dir: Path to branch directory to delete

    Returns:
        True if successful, False otherwise
    """
    if not HANDLERS_AVAILABLE:
        console.print(f"[delete_branch] Handlers unavailable: {HANDLER_ERROR}")
        return False

    # Validate path
    target_dir = target_dir.resolve()

    if not target_dir.exists():
        console.print(f"ERROR: Branch directory does not exist: {target_dir}")
        return False

    if not target_dir.is_dir():
        console.print(f"ERROR: Path is not a directory: {target_dir}")
        return False

    # Get branch name
    branch_name = get_branch_name(target_dir)
    branchname_upper = branch_name.upper().replace("-", "_")

    console.print(f"\n{'='*70}")
    console.print(f"Delete Branch")
    console.print(f"{'='*70}")
    console.print(f"Target: {target_dir}")
    console.print(f"Branch: {branchname_upper}")
    console.print()

    # Log operation start
    json_handler.log_operation(
        'branch_deletion_started',
        {'branch': branchname_upper, 'path': str(target_dir)},
        'delete_branch'
    )

    # Lookup in registry
    branch_entry = find_branch_in_registry(branchname_upper)

    if branch_entry:
        console.print(f"Found in registry: {branch_entry.get('description', 'N/A')}")
        console.print(f"Profile: {branch_entry.get('profile', 'N/A')}")
        console.print(f"Created: {branch_entry.get('created', 'Unknown')}")
        console.print()
    else:
        console.print(f"WARNING: Branch not found in registry")
        console.print()

    # Get confirmation
    if not Confirm.ask(f"Delete '{branchname_upper}' permanently?", default=False):
        console.print("Deletion cancelled by user")
        return False

    console.print()
    console.print(f"{'='*70}")
    console.print("Deleting branch...")
    console.print(f"{'='*70}")
    console.print()

    # Step 1: Backup branch
    console.print("Backing up branch...")
    try:
        backup_path = backup_branch(target_dir, branchname_upper)
        console.print(f"  SUCCESS: Branch backed up to {backup_path}")
    except Exception as e:
        logger.error(f"Branch backup failed: {e}")
        console.print(f"  ERROR: Failed to backup branch: {e}")
        return False
    console.print()

    # Step 2: Remove from registry
    if branch_entry:
        console.print("Removing from registry...")
        try:
            remove_registry_entry(branchname_upper)
            console.print(f"  SUCCESS: Removed from BRANCH_REGISTRY.json")
        except Exception as e:
            logger.error(f"Registry entry removal failed: {e}")
            console.print(f"  WARNING: Failed to remove from registry: {e}")
    else:
        console.print("Skipping registry removal (not registered)")
    console.print()

    # Step 3: Delete directory
    console.print("Deleting directory...")
    try:
        shutil.rmtree(target_dir)
        console.print(f"  SUCCESS: Directory deleted")
    except Exception as e:
        logger.error(f"Directory deletion failed: {e}")
        console.print(f"  ERROR: Failed to delete directory: {e}")
        return False
    console.print()

    # Verify deletion
    if target_dir.exists():
        console.print("ERROR: Directory still exists after deletion attempt")
        return False

    # Report success
    console.print(f"{'='*70}")
    console.print("SUCCESS: Branch deleted successfully!")
    console.print(f"{'='*70}")
    console.print()
    console.print(f"Branch '{branchname_upper}' has been permanently deleted.")
    console.print(f"Backup location: {backup_path}")
    console.print()

    # Log operation completion and update stats
    json_handler.log_operation(
        'branch_deletion_completed',
        {
            'branch': branchname_upper,
            'success': True,
            'backup_path': str(backup_path)
        },
        'delete_branch'
    )

    # Update data metrics
    json_handler.increment_counter('delete_branch', 'branches_deleted')
    json_handler.increment_counter('delete_branch', 'operations_successful')

    # Fire trigger event
    try:
        from trigger.apps.modules.core import trigger
        trigger.fire('branch_deleted', branch=branchname_upper)
    except ImportError:
        pass  # Silent fallback

    return True


# =============================================================================
# MODULE INTERFACE
# =============================================================================

def handle_command(args) -> bool:
    """
    Orchestrator interface for delete_branch

    Args:
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    # Check if this module should handle the command FIRST
    if not hasattr(args, 'command') or args.command != 'delete-branch':
        return False

    # Then check if handlers are available
    if not HANDLERS_AVAILABLE:
        console.print(f"[delete_branch] Handlers unavailable: {HANDLER_ERROR}")
        return True

    if not hasattr(args, 'target_directory') or not args.target_directory:
        console.print("Error: target_directory required")
        console.print("Usage: cortex delete-branch <target_directory>")
        return True

    target_dir = Path(args.target_directory).resolve()
    return delete_branch(target_dir)


# =============================================================================
# DRONE COMPLIANCE - HELP SYSTEM
# =============================================================================

def print_help():
    """Display drone-compliant help output"""
    console.print()
    console.print("="*70)
    console.print("DELETE BRANCH - AIPass Branch Deletion")
    console.print("="*70)
    console.print()
    console.print("Deletes an AIPass branch with proper cleanup and backup.")
    console.print()
    console.print("USAGE:")
    console.print("  python3 delete_branch.py <target_directory>")
    console.print("  cortex delete <target_directory>")
    console.print("  cortex delete-branch <target_directory>")
    console.print()
    console.print("EXAMPLE:")
    console.print("  python3 delete_branch.py /home/aipass/aipass_core/old_branch")
    console.print()
    console.print("WHAT IT DOES:")
    console.print("  - Prompts for confirmation (y/N)")
    console.print("  - Creates backup in deleted_branches directory")
    console.print("  - Removes entry from BRANCH_REGISTRY.json")
    console.print("  - Deletes the branch directory")
    console.print()
    console.print("REQUIREMENTS:")
    console.print("  - Target directory must exist")
    console.print("  - User confirmation required")
    console.print()
    console.print("="*70)
    console.print()
    console.print("Commands: delete, delete-branch, --help")
    console.print()


# =============================================================================
# STANDALONE EXECUTION (for testing/debugging)
# =============================================================================

if __name__ == "__main__":
    import sys

    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    # Check if target directory provided
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1]).resolve()
        success = delete_branch(target_path)
        sys.exit(0 if success else 1)

    # No arguments - show status
    console.print("\n" + "="*60)
    console.print("delete_branch - Module Status Report")
    console.print("="*60)

    console.print(f"\nModule: delete_branch.py")
    console.print(f"Purpose: Delete AIPass branches with backup")
    console.print(f"Status: {'Ready' if HANDLERS_AVAILABLE else 'Handlers Missing'}")

    if HANDLERS_AVAILABLE:
        console.print(f"\nHandlers:")
        console.print(f"  metadata (get_branch_name)")
        console.print(f"  registry (find_branch_in_registry, remove_registry_entry)")
        console.print(f"  cli.prompts (confirm_yes_no)")
        console.print(f"\nReady to delete branches!")
    else:
        console.print(f"\nHandler Error:")
        console.print(f"  {HANDLER_ERROR}")

    console.print(f"\nUsage:")
    console.print(f"  Direct: python3 delete_branch.py <target_directory>")
    console.print(f"  Orchestrator: cortex delete-branch <target_directory>")
    console.print("="*60 + "\n")
