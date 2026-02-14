#!/usr/bin/env python3

# ===================AIPASS====================
# META DATA HEADER
# Name: branch_delete.py - AIPass Branch Delete Script
# Date: 2025-10-29
# Version: 1.0.0
# Category: branch_operations
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-10-29): Initial standardized version - Added META header
# =============================================

"""
AIPass Branch Delete Script
Permanently deletes branch with full cleanup and deletion record

Safety Features:
    - Two-step confirmation (exact name + "DELETE")
    - Creates deletion record before deletion
    - Registry removal
    - Complete directory deletion
    - Graceful handling of missing branches
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))

# Standard library imports
import argparse
import json
import shutil
from datetime import datetime
from typing import Optional, Dict

# AIPass infrastructure imports
from prax.apps.prax_logger import system_logger as logger

# Import from branch_lib
from branch_lib import (
    get_branch_name,
    find_branch_in_registry,
    remove_registry_entry,
    load_registry,
    detect_profile,
    get_git_repo
)


# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

# Module root and JSON directory
MODULE_ROOT = Path(__file__).parent.parent
JSON_DIR = MODULE_ROOT / "branch_operations_json"

# Auto-create JSON directory
JSON_DIR.mkdir(exist_ok=True)

# 3-file JSON structure for branch_delete module
CONFIG_FILE = JSON_DIR / "branch_delete_config.json"
DATA_FILE = JSON_DIR / "branch_delete_data.json"
LOG_FILE = JSON_DIR / "branch_delete_log.json"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def backup_branch_before_deletion(branch_path: Path, branch_name: str) -> Optional[Path]:
    """
    Backup branch to backup_system/deleted_branches before deletion

    Args:
        branch_path: Path to branch directory being deleted
        branch_name: Branch name (uppercase)

    Returns:
        Path to backup directory if successful, None if failed
    """
    # Get backup_system deleted_branches directory
    backup_system_dir = AIPASS_ROOT / "backup_system" / "deleted_branches"

    try:
        # Create deleted_branches directory if doesn't exist
        backup_system_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamped backup directory name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir_name = f"{branch_name}_deleted_{timestamp}"
        backup_path = backup_system_dir / backup_dir_name

        # Copy entire branch directory to backup location
        logger.info(f"Backing up branch {branch_name} to {backup_path}")
        shutil.copytree(branch_path, backup_path, symlinks=False)

        logger.info(f"Branch backup complete: {backup_path}")
        return backup_path

    except Exception as e:
        logger.error(f"Failed to backup branch before deletion: {e}")
        return None


def log_operation(operation: str, success: bool, details: str = "", error: str = ""):
    """
    Log branch_delete operations to module-specific log file

    Args:
        operation: Operation name (e.g., "branch_delete_start")
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
        logger.error(f"[branch_delete] Error saving log: {e}")


def load_config() -> Dict:
    """Load branch_delete configuration"""
    default_config = {
        "enabled": True,
        "version": "1.0.0",
        "auto_backup": True,
        "require_confirmation": True,
        "max_log_entries": 1000
    }

    if not CONFIG_FILE.exists():
        save_config(default_config)
        return default_config

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[branch_delete] Error loading config: {e}")
        return default_config


def save_config(config: Dict):
    """Save branch_delete configuration"""
    try:
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_delete] Error saving config: {e}")


def load_data() -> Dict:
    """Load branch_delete runtime data"""
    default_data = {
        "created": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "operations_total": 0,
        "operations_successful": 0,
        "operations_failed": 0,
        "branches_deleted": 0
    }

    if not DATA_FILE.exists():
        return default_data

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[branch_delete] Error loading data: {e}")
        return default_data


def save_data(data: Dict):
    """Save branch_delete runtime data with auto timestamp"""
    data["last_updated"] = datetime.now().isoformat()
    try:
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_delete] Error saving data: {e}")


# =============================================================================
# PATH GETTERS
# =============================================================================

def get_deletion_dir() -> Path:
    """
    Get path to deleted branches directory - single point of change for path migration

    Returns:
        Path to deleted_branches directory

    Note:
        Uses dynamic path for migration readiness.
        Current: Path.home() / "projects" / "aipass_1.0" / "deleted_branches"
        Future: AIPASS_ROOT / "deleted_branches" (when directory moves)
    """
    return Path.home() / "projects" / "aipass_1.0" / "deleted_branches"


# =============================================================================
# DELETION RECORD
# =============================================================================

def create_deletion_record(branch_info: Dict, deletion_dir: Path) -> Optional[Path]:
    """
    Create permanent record of branch deletion

    Args:
        branch_info: Dict with branch information
        deletion_dir: Directory for deletion records

    Returns:
        Path to deletion record file or None if failed
    """
    # Ensure deletion directory exists
    try:
        deletion_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"ERROR: Failed to create deletion directory: {e}")
        return None

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    branch_name = branch_info.get("name", "UNKNOWN")

    # Create deletion record filename
    record_file = deletion_dir / f"{branch_name}_deleted_{timestamp}.txt"

    # Build deletion record content
    content = []
    content.append("=" * 70)
    content.append("BRANCH DELETION RECORD")
    content.append("=" * 70)
    content.append("")
    content.append(f"Branch Name: {branch_name}")
    content.append(f"Path: {branch_info.get('path', 'Unknown')}")
    content.append(f"Profile: {branch_info.get('profile', 'Unknown')}")
    content.append(f"Deleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"Deleted By: branch_delete.py")
    content.append("")
    content.append("Registry Info:")
    content.append(f"  - Description: {branch_info.get('description', 'N/A')}")
    content.append(f"  - Email: {branch_info.get('email', 'N/A')}")
    content.append(f"  - Created: {branch_info.get('created', 'N/A')}")
    content.append(f"  - Last Active: {branch_info.get('last_active', 'N/A')}")
    content.append(f"  - Status: {branch_info.get('status', 'N/A')}")

    # Add git info if available
    if "git_repo" in branch_info:
        content.append(f"  - Git Repo: {branch_info['git_repo']}")

    content.append("")
    content.append(f"Reason: {branch_info.get('deletion_reason', 'User requested')}")
    content.append("")
    content.append("=" * 70)
    content.append("")

    # Write deletion record
    try:
        with open(record_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        return record_file
    except Exception as e:
        print(f"ERROR: Failed to create deletion record: {e}")
        return None


# =============================================================================
# TWO-STEP CONFIRMATION
# =============================================================================

def get_two_step_confirmation(branch_name: str, branch_info: Dict) -> bool:
    """
    Get two-step confirmation from user

    Args:
        branch_name: Branch name to confirm
        branch_info: Dict with branch information

    Returns:
        True if user confirms both steps, False otherwise
    """
    print()
    print("=" * 70)
    print("WARNING: You are about to PERMANENTLY DELETE this branch")
    print("=" * 70)
    print()
    print(f"Branch Name: {branch_name}")
    print(f"Path: {branch_info.get('path', 'Unknown')}")
    print(f"Profile: {branch_info.get('profile', 'Unknown')}")
    print(f"Description: {branch_info.get('description', 'N/A')}")
    print(f"Created: {branch_info.get('created', 'N/A')}")
    print(f"Last Active: {branch_info.get('last_active', 'N/A')}")
    print()
    print("This action cannot be undone. All data will be lost.")
    print()

    # Step 1: Type exact branch name
    print(f"Step 1 - Type the exact branch name to proceed: ", end='', flush=True)
    user_input = input().strip()

    if user_input != branch_name:
        print()
        print(f"Confirmation failed. Expected '{branch_name}', got '{user_input}'")
        return False

    print()
    # Step 2: Type DELETE
    print(f"Step 2 - Type DELETE (all caps) to confirm: ", end='', flush=True)
    user_input = input().strip()

    if user_input != "DELETE":
        print()
        print(f"Confirmation failed. Expected 'DELETE', got '{user_input}'")
        return False

    return True


# =============================================================================
# MAIN DELETE FUNCTION
# =============================================================================

def delete_branch(branch_path: Path, force: bool = False) -> bool:
    """
    Delete branch with full cleanup

    Args:
        branch_path: Path to branch directory
        force: If True, skip confirmations (DANGEROUS)

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Branch delete initiated for: {branch_path} (force={force})")

    # Log operation start
    log_operation(
        operation="branch_delete_start",
        success=True,
        details=f"Initiating branch delete for: {branch_path} (force={force})"
    )

    # Validate path exists
    if not branch_path.exists():
        logger.info(f"Branch path does not exist (already deleted): {branch_path}")
        print(f"⚠️ Branch path does not exist: {branch_path}")
        print()
        print("Branch may have been already deleted.")
        print("Check deletion records in: /home/aipass/projects/aipass_1.0/deleted_branches/")
        return True  # Not an error - branch already gone

    if not branch_path.is_dir():
        logger.error(f"Target path is not a directory: {branch_path}")
        print(f"❌ ERROR: Path is not a directory: {branch_path}")
        return False

    # Get branch name
    branch_name = get_branch_name(branch_path)
    branchname_upper = branch_name.upper().replace("-", "_")

    print(f"Branch Delete Tool")
    print(f"Target: {branch_path}")
    print(f"Branch: {branchname_upper}")
    print()

    # Find in registry
    print("Looking up branch in registry...")
    branch_entry = find_branch_in_registry(branchname_upper)

    if not branch_entry:
        print(f"⚠️ WARNING: Branch '{branchname_upper}' not found in registry")
        print("Will delete directory but cannot create detailed deletion record")
        print()

        # Build minimal branch info
        branch_info = {
            "name": branchname_upper,
            "path": str(branch_path),
            "profile": detect_profile(branch_path),
            "description": "Not registered",
            "email": "N/A",
            "created": "Unknown",
            "last_active": "Unknown",
            "status": "unregistered"
        }
    else:
        print(f"Found in registry: {branch_entry['description']}")
        print()
        branch_info = branch_entry.copy()

    # Add git repo info
    git_repo = get_git_repo(branch_path)
    branch_info["git_repo"] = git_repo

    # Get confirmation (unless force flag)
    if not force:
        if not get_two_step_confirmation(branchname_upper, branch_info):
            print()
            print("Deletion cancelled by user.")
            return False
    else:
        print("Force flag enabled - skipping confirmation")

    print()
    print("=" * 70)
    print("Deleting branch...")
    print("=" * 70)
    print()

    # Step 1: Backup branch to backup_system/deleted_branches
    print("Backing up branch before deletion...")
    backup_path = backup_branch_before_deletion(branch_path, branchname_upper)

    if backup_path:
        print(f"  ✅ SUCCESS: Branch backed up to {backup_path}")
    else:
        print(f"  ⚠️ WARNING: Backup failed - Branch will be permanently lost if deleted")
        print(f"  Continue with deletion? (y/N): ", end='', flush=True)
        if not force:
            response = input().strip().lower()
            if response != 'y':
                print("\nDeletion cancelled - backup failed")
                return False
        else:
            print("  Force flag enabled - continuing despite backup failure")
    print()

    # Step 2: Create deletion record - using getter for migration readiness
    deletion_dir = get_deletion_dir()
    print("Creating deletion record...")
    record_path = create_deletion_record(branch_info, deletion_dir)

    if record_path:
        print(f"  ✅ SUCCESS: Deletion record created at {record_path.name}")
    else:
        print(f"  ⚠️ WARNING: Failed to create deletion record (continuing anyway)")
    print()

    # Step 3: Remove from registry
    if branch_entry:
        print("Removing from registry...")
        if remove_registry_entry(branchname_upper):
            print(f"  ✅ SUCCESS: Removed from BRANCH_REGISTRY.json")
        else:
            print(f"  ⚠️ WARNING: Failed to remove from registry (continuing anyway)")
    else:
        print("Skipping registry removal (not registered)")
    print()

    # Step 4: Delete directory
    print("Deleting directory...")
    try:
        shutil.rmtree(branch_path)
        print(f"  ✅ SUCCESS: Directory deleted")
    except Exception as e:
        print(f"  ❌ ERROR: Failed to delete directory: {e}")
        print()
        print("Deletion incomplete - directory could not be removed")
        log_operation(
            operation="branch_delete_failed",
            success=False,
            details=f"Failed to delete directory for branch '{branchname_upper}'",
            error=str(e)
        )
        return False
    print()

    # Verify deletion
    if branch_path.exists():
        logger.error(f"Branch deletion failed: Directory still exists after deletion attempt - {branch_path}")
        print("❌ ERROR: Directory still exists after deletion attempt")
        log_operation(
            operation="branch_delete_failed",
            success=False,
            details=f"Directory still exists after deletion attempt: {branch_path}",
            error="Directory verification failed"
        )
        return False

    # Report success
    logger.info(f"Branch deletion complete: {branchname_upper} permanently deleted from {branch_path}")
    log_operation(
        operation="branch_delete_complete",
        success=True,
        details=f"Branch '{branchname_upper}' permanently deleted from {branch_path}"
    )
    print("=" * 70)
    print("✅ Branch deleted successfully!")
    print("=" * 70)
    print()
    print(f"Branch '{branchname_upper}' has been permanently deleted.")

    if backup_path:
        print(f"Backup location: {backup_path}")
    if record_path:
        print(f"Deletion record: {record_path}")

    print()
    print("Summary:")
    print(f"  - Branch backup: {'Success' if backup_path else 'Failed'}")
    print(f"  - Deletion record: {'Created' if record_path else 'Failed'}")
    print(f"  - Registry removal: {'Success' if branch_entry else 'N/A (not registered)'}")
    print(f"  - Directory deletion: Success")

    return True


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='AIPass Branch Delete - Permanently delete branch with full cleanup',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: delete, --force

OPERATIONS:
  delete <branch_path>  - Permanently delete specified branch

DELETION PROCESS:
  1. User confirmation (two-step: name + DELETE)
  2. Create deletion record (audit trail)
  3. Remove from branch registry
  4. Delete directory and all contents

SAFETY FEATURES:
  --force               - Skip confirmation prompts (DANGEROUS)

Deletion records location:
  /home/aipass/projects/aipass_1.0/deleted_branches/

EXAMPLES:
  python3 branch_delete.py delete /home/aipass/old-feature
  python3 branch_delete.py delete /home/aipass/test-branch --force
        """
    )
    parser.add_argument('command', 
                       choices=['delete'],
                       help='Command to execute')
    parser.add_argument('branch_path', help='Path to branch directory to delete')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts (DANGEROUS)')

    args = parser.parse_args()
    target_path = Path(args.branch_path).resolve()

    # Initialize JSON infrastructure
    config = load_config()
    data = load_data()

    try:
        success = delete_branch(target_path, args.force)

        # Update statistics
        data["operations_total"] += 1
        if success:
            data["operations_successful"] += 1
            data["branches_deleted"] += 1
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