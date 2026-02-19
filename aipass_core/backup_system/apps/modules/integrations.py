#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: integrations.py - External integrations and backup protection
# Date: 2025-11-29
# Version: 2.0.1
# Category: backup_system
#
# CHANGELOG (Max 5 entries):
#   - v2.0.1 (2025-11-29): UX FIX - Import error and missing help output
#     * Fixed ModuleNotFoundError by adding BACKUP_SYSTEM_APPS to sys.path
#     * Added __main__ block with comprehensive help output
#     * Shows available subcommands with status and usage examples
#     * Drone-compliant "Commands:" line at end
#   - v2.0.0 (2025-11-16): Created seed-compliant layout module
#     * Extracted from backup_integrations.py v1.1.0
#     * Implemented handle_command() for integration CLI routing
#     * Google Drive sync and backup protection functions
#     * Updated imports to seed pattern (handlers.utils)
#   - v1.1.0 (2025-10-30): Original backup_integrations features
#     * Enhanced Google Drive sync UI
#     * Storage quota display with color-coding
#   - v1.0.0 (2025-10-14): Initial extraction
#     * sync_to_drive() and set_backup_readonly() functions
#
# CODE STANDARDS:
#   - Follow seed 3-layer architecture
#   - Orchestrate workflows, delegate to handlers
#   - Import handlers, never implement business logic
# =============================================

"""
Backup System Integrations Module

Handles external integrations for the backup system following seed architecture standards.
Provides CLI command routing and integration orchestration.

This module manages optional features that integrate with external services
or provide additional protection mechanisms for backups:
- Google Drive cloud synchronization (optional)
- Backup directory protection (read-only permissions)

Architecture Pattern:
- handle_command(args) - CLI entry point for integration commands
- Integration functions with proper error handling and logging
- Graceful degradation for optional dependencies (Google Drive)
"""

# =============================================
# IMPORTS
# =============================================

# Infrastructure
import sys
import os
import stat
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Add backup_system/apps to path for handler imports
BACKUP_SYSTEM_APPS = Path(__file__).parent.parent
sys.path.insert(0, str(BACKUP_SYSTEM_APPS))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import header, success, error

# Handler imports - seed pattern
from handlers.utils.system_utils import safe_print

# Google Drive sync integration (optional - graceful degradation if not available)
try:
    from google_drive_sync import GoogleDriveSync  # type: ignore[import-not-found]
    DRIVE_SYNC_AVAILABLE = True
except ImportError:
    GoogleDriveSync = None  # type: ignore
    DRIVE_SYNC_AVAILABLE = False
    logger.info("[integrations] Google Drive sync module not available - sync features disabled")

# =============================================
# MODULE-LEVEL COMMAND HANDLER
# =============================================


def handle_command(args) -> bool | None:
    """Route integration commands to appropriate handler.

    This is the module-level entry point for CLI commands related to integrations.
    Routes integration-specific commands like sync-to-drive and set-readonly.

    Args:
        args: Command-line arguments from CLI parser

    Returns:
        bool: True if command succeeded, False otherwise, None if command not matched

    Example:
        result = handle_command(args)
        if result:
            console.print("Integration command completed successfully")

    Supported commands:
        - sync-to-drive: Sync backup to Google Drive
        - set-readonly: Protect backup with read-only permissions
    """
    if not hasattr(args, 'integration_command'):
        return None

    if args.integration_command == 'sync-to-drive':
        backup_path = Path(args.backup_path) if hasattr(args, 'backup_path') else None
        source_dir = Path(args.source_dir) if hasattr(args, 'source_dir') else None
        mode = getattr(args, 'mode', 'versioned')
        backup_note = getattr(args, 'backup_note', '')

        if not backup_path or not source_dir:
            logger.error("[integrations] Missing required arguments for sync-to-drive")
            return False

        return sync_to_drive(backup_path, source_dir, mode, backup_note)

    elif args.integration_command == 'set-readonly':
        backup_path = Path(args.backup_path) if hasattr(args, 'backup_path') else None
        if not backup_path:
            logger.error("[integrations] Missing backup_path argument for set-readonly")
            return False

        return set_backup_readonly(backup_path)

    return None

# =============================================
# GOOGLE DRIVE INTEGRATION
# =============================================


def sync_to_drive(backup_path: Path, source_dir: Path, mode: str, backup_note: str = "") -> bool:
    """Sync versioned backups to Google Drive.

    Integrates with the google_drive_sync module to upload backup files to cloud storage.
    Only works with versioned backups to maintain complete file history.

    Authentication and storage quota information are displayed during sync.
    Gracefully degrades if google_drive_sync module is not available.

    Args:
        backup_path: Path to backup directory to sync
        source_dir: Source directory being backed up (for project name)
        mode: Backup mode ('snapshot' or 'versioned')
        backup_note: Optional note describing the backup

    Returns:
        True if sync succeeded, False otherwise

    Example:
        success = sync_to_drive(
            backup_path=Path("/home/aipass/aipass_core/backup_system/backups/versioned_backup"),
            source_dir=Path("/home/aipass/aipass_core"),
            mode="versioned",
            backup_note="Before major refactor"
        )
    """
    if not DRIVE_SYNC_AVAILABLE:
        safe_print("\033[93m[WARNING] Google Drive sync module not available - check backup_system installation\033[0m")
        logger.warning("[integrations] Drive sync requested but google_drive_sync module not found")
        return False

    if mode != 'versioned':
        safe_print("[INFO] Drive sync only available for versioned backups")
        logger.info(f"[integrations] Drive sync skipped - mode {mode} not supported (versioned only)")
        return False

    try:
        # Display sync header with project and credential information
        safe_print("\n" + "="*70)
        safe_print("\033[96m           GOOGLE DRIVE SYNC\033[0m")
        safe_print("="*70)

        # Get project name - hardcoded for AIPass branch
        project_name = "AIPass"

        safe_print(f"\033[92m✓\033[0m Google Drive folder name: \033[1m{project_name}\033[0m")
        safe_print(f"\033[92m✓\033[0m Destination: Google Drive (versioned backups)")
        safe_print(f"\033[93m→\033[0m Credentials: /home/aipass/aipass_core/backup_system/apps/credentials.json")
        safe_print(f"\033[93m→\033[0m Token: ~/.aipass/drive_creds.json")
        safe_print("-"*70)

        logger.info("[integrations] Starting Google Drive sync")

        drive_sync = GoogleDriveSync()

        # Authenticate with visual feedback
        safe_print("\033[94m[AUTH]\033[0m Verifying Google Drive credentials...")
        if not drive_sync.authenticate():
            safe_print("\033[91m✗ ERROR: Authentication failed\033[0m")
            logger.error("[integrations] Google Drive authentication failed - check Python environment and packages")
            return False

        safe_print("\033[92m✓ Authentication successful\033[0m")

        # Get and display storage quota (only if API returns data)
        storage = drive_sync.get_storage_quota()
        if storage:
            used = storage['usage_gb']
            total = storage['limit_gb']
            free = storage['free_gb']
            percent = storage['percent_used']

            # Color code based on usage percentage
            if percent < 70:
                color = "\033[92m"  # Green
            elif percent < 90:
                color = "\033[93m"  # Yellow
            else:
                color = "\033[91m"  # Red

            safe_print(f"\033[94m[STORAGE]\033[0m {color}{used:.2f}GB used\033[0m / {total:.2f}GB total ({free:.2f}GB free, {percent:.1f}% used)")

        logger.info(f"[integrations] Syncing project '{project_name}' to Drive")

        # Sync all backup files from the current backup directory
        success = drive_sync.sync_backup_files(
            backup_dir=backup_path,
            project_name=project_name,
            note=backup_note
        )

        if success:
            logger.info(f"[integrations] Drive sync completed successfully for {project_name}")
            return True
        else:
            logger.error("[integrations] Drive sync completed with errors")
            return False

    except Exception as e:
        error_msg = f"Drive sync failed: {e}"
        safe_print(f"[ERROR] {error_msg}")
        logger.error(f"[integrations] {error_msg}")
        return False

# =============================================
# FILE PROTECTION
# =============================================


def set_backup_readonly(backup_path: Path) -> bool:
    """Set backup directory to read-only for protection against accidental modification.

    Applies read-only permissions recursively to all directories and files in the backup.
    This prevents accidental deletion or modification of backup files while still allowing
    the backup system to update them using the temporarily_writable() context manager.

    Directory permissions: r-xr-xr-x (read + execute for traversal)
    File permissions: r--r--r-- (read-only)

    Args:
        backup_path: Path to backup directory to protect

    Returns:
        True if protection applied successfully, False otherwise

    Example:
        success = set_backup_readonly(Path("/home/aipass/aipass_core/backup_system/backups/versioned_backup"))
        if success:
            console.print("Backup protected")
    """
    try:
        if not backup_path.exists():
            warning_msg = f"Backup path does not exist: {backup_path}"
            safe_print(f"[WARNING] {warning_msg}")
            logger.warning(f"[integrations] {warning_msg}")
            return False

        # Set directory and all files to read-only
        protected_dirs = 0
        protected_files = 0

        for root, dirs, files in os.walk(str(backup_path)):
            # Make directory read-only (must keep execute for traversal)
            # Permissions: r-xr-xr-x (555 in octal)
            try:
                os.chmod(root, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
                              stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                protected_dirs += 1
            except Exception as e:
                logger.warning(f"[integrations] Could not protect directory {root}: {e}")

            # Make all files read-only
            # Permissions: r--r--r-- (444 in octal)
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.chmod(file_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                    protected_files += 1
                except Exception as e:
                    logger.warning(f"[integrations] Could not protect file {file_path}: {e}")

        success_msg = f"Backup directory set to read-only: {backup_path}"
        safe_print(f"[PROTECTION] {success_msg}")
        logger.info(f"[integrations] {success_msg} ({protected_dirs} dirs, {protected_files} files)")
        return True

    except Exception as e:
        warning_msg = f"Could not set read-only protection: {e}"
        safe_print(f"[WARNING] {warning_msg}")
        logger.warning(f"[integrations] {warning_msg}")
        return False

# =============================================
# MODULE INITIALIZATION
# =============================================

# Log module initialization
logger.info("[integrations] Module loaded - external integration support ready")
if DRIVE_SYNC_AVAILABLE:
    logger.info("[integrations] Google Drive sync available")
else:
    logger.info("[integrations] Google Drive sync unavailable - install google_drive_sync.py to enable")

# =============================================
# MAIN ENTRY POINT
# =============================================

def show_help():
    """Display help information for the integrations module."""
    header("BACKUP SYSTEM - INTEGRATIONS MODULE")
    safe_print("")
    safe_print("\033[1mPURPOSE:\033[0m")
    safe_print("  External integrations for the backup system")
    safe_print("")
    safe_print("\033[1mAVAILABLE SUBCOMMANDS:\033[0m")
    safe_print("")
    safe_print("  \033[92msync-to-drive\033[0m")
    safe_print("    Sync versioned backups to Google Drive cloud storage")
    safe_print("    Requires: backup_path, source_dir, mode, backup_note")
    safe_print("    Status: " + ("\033[92mAvailable\033[0m" if DRIVE_SYNC_AVAILABLE else "\033[93mUnavailable (google_drive_sync module not found)\033[0m"))
    safe_print("")
    safe_print("  \033[92mset-readonly\033[0m")
    safe_print("    Protect backup directory with read-only permissions")
    safe_print("    Requires: backup_path")
    safe_print("    Status: \033[92mAvailable\033[0m")
    safe_print("")
    safe_print("\033[1mUSAGE:\033[0m")
    safe_print("  This module is called via the backup system CLI:")
    safe_print("  \033[90m$ backup integration sync-to-drive --backup-path <path> ...\033[0m")
    safe_print("  \033[90m$ backup integration set-readonly --backup-path <path>\033[0m")
    safe_print("")
    safe_print("\033[1mOR\033[0m import functions directly in Python:")
    safe_print("  \033[90mfrom backup_system.apps.modules.integrations import sync_to_drive, set_backup_readonly\033[0m")
    safe_print("")
    safe_print("-"*70)
    safe_print("\033[1mCommands:\033[0m sync-to-drive, set-readonly")
    safe_print("="*70)
    safe_print("")

if __name__ == "__main__":
    """Display help when module is run directly."""
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
    else:
        show_help()
