#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: backup_integrations.py
# Date: 2025-10-30
# Version: 1.1.0
# Category: backup_system
#
# CHANGELOG:
#   - v1.1.0 (2025-10-30): Enhanced Google Drive sync UI
#     * Added visual header with project and credential information
#     * Implemented storage quota display with color-coded usage
#     * Changed folder name from "AIPass-Workshop" to "AIPass"
#     * Added authentication verification feedback
#   - v1.0.0 (2025-10-14): Initial extraction from backup.py
#     * Extracted sync_to_drive() method (lines 1298-1335)
#     * Extracted set_backup_readonly() method (lines 1337-1360)
#     * Google Drive sync integration (optional dependency)
#     * File protection through read-only permissions
#     * External integrations separated from core backup logic
# =============================================

"""
Backup System Integrations

Handles external integrations for the backup system:
- Google Drive cloud synchronization (optional)
- Backup directory protection (read-only permissions)
- Future integrations can be added here

This module manages optional features that integrate with external services
or provide additional protection mechanisms for backups.
"""

# =============================================
# IMPORTS
# =============================================

import sys
import os
import stat
from pathlib import Path
from typing import Optional

# Infrastructure import pattern
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))
from prax.apps.prax_logger import system_logger as logger

# Module dependencies
from backup_utils import safe_print

# Google Drive sync integration (optional - graceful degradation if not available)
try:
    from google_drive_sync import GoogleDriveSync
    DRIVE_SYNC_AVAILABLE = True
except ImportError:
    DRIVE_SYNC_AVAILABLE = False
    logger.info("[backup_integrations] Google Drive sync module not available - sync features disabled")

# =============================================
# GOOGLE DRIVE INTEGRATION
# =============================================

def sync_to_drive(backup_path: Path, source_dir: Path, mode: str, backup_note: str = "") -> bool:
    """Sync versioned backups to Google Drive.

    Integrates with the google_drive_sync module to upload backup files to cloud storage.
    Only works with versioned backups to maintain complete file history.

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
        logger.warning("[backup_integrations] Drive sync requested but google_drive_sync module not found")
        return False

    if mode != 'versioned':
        safe_print("[INFO] Drive sync only available for versioned backups")
        logger.info(f"[backup_integrations] Drive sync skipped - mode {mode} not supported (versioned only)")
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

        logger.info("[backup_integrations] Starting Google Drive sync")

        drive_sync = GoogleDriveSync()

        # Authenticate with visual feedback
        safe_print("\033[94m[AUTH]\033[0m Verifying Google Drive credentials...")
        if not drive_sync.authenticate():
            safe_print("\033[91m✗ ERROR: Authentication failed\033[0m")
            logger.error("[backup_integrations] Google Drive authentication failed - check Python environment and packages")
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

        logger.info(f"[backup_integrations] Syncing project '{project_name}' to Drive")

        # Sync all backup files from the current backup directory
        success = drive_sync.sync_backup_files(
            backup_dir=backup_path,
            project_name=project_name,
            note=backup_note
        )

        if success:
            logger.info(f"[backup_integrations] Drive sync completed successfully for {project_name}")
            return True
        else:
            logger.error("[backup_integrations] Drive sync completed with errors")
            return False

    except Exception as e:
        error_msg = f"Drive sync failed: {e}"
        safe_print(f"[ERROR] {error_msg}")
        logger.error(f"[backup_integrations] {error_msg}")
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
            print("Backup protected")
    """
    try:
        if not backup_path.exists():
            warning_msg = f"Backup path does not exist: {backup_path}"
            safe_print(f"[WARNING] {warning_msg}")
            logger.warning(f"[backup_integrations] {warning_msg}")
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
                logger.warning(f"[backup_integrations] Could not protect directory {root}: {e}")

            # Make all files read-only
            # Permissions: r--r--r-- (444 in octal)
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.chmod(file_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                    protected_files += 1
                except Exception as e:
                    logger.warning(f"[backup_integrations] Could not protect file {file_path}: {e}")

        success_msg = f"Backup directory set to read-only: {backup_path}"
        safe_print(f"[PROTECTION] {success_msg}")
        logger.info(f"[backup_integrations] {success_msg} ({protected_dirs} dirs, {protected_files} files)")
        return True

    except Exception as e:
        warning_msg = f"Could not set read-only protection: {e}"
        safe_print(f"[WARNING] {warning_msg}")
        logger.warning(f"[backup_integrations] {warning_msg}")
        return False

# =============================================
# MODULE INITIALIZATION
# =============================================

# Log module initialization
logger.info("[backup_integrations] Module loaded - external integration support ready")
if DRIVE_SYNC_AVAILABLE:
    logger.info("[backup_integrations] Google Drive sync available")
else:
    logger.info("[backup_integrations] Google Drive sync unavailable - install google_drive_sync.py to enable")
