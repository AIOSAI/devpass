#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: backup_engine.py
# Date: 2025-10-14
# Version: 1.0.0
# Category: backup_system
#
# CHANGELOG:
#   - v1.0.0 (2025-10-14): Initial extraction from backup.py
#     * Extracted UnifiedBackupSystem class (lines 683-1788)
#     * Main backup orchestration and workflow coordination
#     * Includes 326-line run_backup() method (the heart of the system)
#     * Changelog operations, backup info persistence
#     * Statistics tracking and summary reporting
#     * Orchestrates all other modules for complete backup workflow
# =============================================

"""
Backup System Engine

Main orchestrator for the backup system. Coordinates all other modules to execute
complete backup workflows. This is the central component that brings together:
- Configuration (backup_config)
- Models (backup_models)
- Utilities (backup_utils)
- JSON handling (backup_json_handler)
- File operations (backup_operations)
- Diff generation (backup_diff)
- Cloud integration (backup_integrations)

The BackupEngine class manages the complete backup lifecycle from initialization
through execution to reporting.
"""

# =============================================
# IMPORTS
# =============================================

import os
import json
import datetime
import hashlib
from pathlib import Path
from typing import Dict, Optional

# Infrastructure import pattern
import sys
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))
from prax.apps.prax_logger import system_logger as logger

# Module dependencies
from backup_models import BackupResult
from backup_config import (
    BACKUP_MODES,
    GLOBAL_IGNORE_PATTERNS,
    IGNORE_EXCEPTIONS,
    CLI_TRACKING_PATTERNS,
    filter_tracked_items
)
from backup_utils import safe_print, temporarily_writable
from backup_json_handler import (
    initialize_json_files,
    load_json_file,
    save_json_file,
    log_operation,
    update_data_file,
    JSON_DIR
)
from backup_operations import copy_file_with_structure, copy_versioned_file
from backup_integrations import sync_to_drive, set_backup_readonly

# =============================================
# BACKUP ENGINE CLASS
# =============================================

class BackupEngine:
    """Main backup system orchestrator.

    Coordinates all backup operations and manages the complete backup workflow.
    Handles initialization, execution, reporting, and integration with external services.
    """

    def __init__(self, mode: str, dry_run: bool = False):
        """Initialize backup engine with specified mode.

        Args:
            mode: Backup mode ('snapshot' or 'versioned')
            dry_run: If True, scan files without copying (test ignore patterns)

        Raises:
            ValueError: If mode is invalid

        Example:
            engine = BackupEngine('versioned', dry_run=True)
            result = engine.run_backup("Before refactor")
        """
        if mode not in BACKUP_MODES:
            raise ValueError(f"Invalid backup mode: {mode}. Valid modes: {list(BACKUP_MODES.keys())}")

        self.mode = mode
        self.dry_run = dry_run
        self.mode_config = BACKUP_MODES[mode]

        # Auto-detect source directory (entire Workshop at /home/aipass/)
        # Using Path.home() is cleaner and more reliable than counting parents
        self.source_dir = Path.home()
        self.backup_dest = Path(self.mode_config['destination'])
        self.ignore_patterns = GLOBAL_IGNORE_PATTERNS

        # Mode-specific paths - all modes now use fixed folder names
        self.backup_folder_name = self.mode_config['folder_name']
        self.backup_path = self.backup_dest / self.backup_folder_name

        # Ensure backup_system_json directory exists FIRST (use module's JSON dir, not backup dest)
        json_dir = JSON_DIR
        json_dir.mkdir(parents=True, exist_ok=True)

        # Initialize AIPass 3-JSON system (after ensuring directory exists)
        initialize_json_files()

        # JSON files (mode-specific) - also use backup_system_json folder
        self.backup_info_file = json_dir / f"{mode}_backup.json"
        self.changelog_file = json_dir / f"{mode}_backup_changelog.json"
        self.restore_log_file = json_dir / f"{mode}_restore_history.json"

        # Display clear mode identification
        print(f"Mode: {self.mode_config['name']}")
        print(f"Source: {self.source_dir}")
        print(f"Destination: {self.backup_dest}")
        print(f"Usage: {self.mode_config['usage']}")

        logger.info(f"[backup_engine] Initialized {mode} mode - source: {self.source_dir}")

    # =============================================
    # UTILITY METHODS
    # =============================================

    def should_ignore(self, path: Path) -> bool:
        """Check if a file/folder should be ignored based on patterns.

        Args:
            path: Path to check

        Returns:
            True if path should be ignored, False otherwise
        """
        path_str = str(path)
        parts = set(path_str.split(os.sep))
        name = path.name

        # Always ignore backup destinations
        if str(self.backup_dest) in path_str:
            return True

        # Ignore paths containing 'Backups'
        if 'Backups' in parts:
            return True

        # Check exceptions first - files that should NOT be ignored
        for exception in IGNORE_EXCEPTIONS:
            # === AIPASS: Full path matching for template exceptions ===
            # Handle "templates/**" or "*/templates/**" patterns
            if "**" in exception:
                # Convert glob pattern to regex-like check
                exception_parts = exception.split("/**")[0]  # Get everything before /**
                if exception_parts in path_str or exception_parts in "/".join(parts):
                    return False  # Matches exception pattern - don't ignore
            elif exception.startswith('*') and name.endswith(exception[1:]):
                return False  # Matches wildcard exception pattern
            elif exception == name:
                return False  # Exact match
            elif exception in path_str:
                return False  # Exception pattern is in the full path


        for pattern in self.ignore_patterns:
            # Special case: "backups" should only match directory names, not filenames
            if pattern == "backups":
                if "backups" in parts:  # Only ignore if "backups" is a directory in the path
                    return True
            elif pattern == name:
                return True
            elif pattern.startswith('*') and name.endswith(pattern[1:]):
                return True
            elif pattern in parts or pattern in path_str:
                return True
        return False

    def ensure_backup_directory(self, result: BackupResult) -> bool:
        """Create backup directory if needed with proper permission handling.

        Args:
            result: BackupResult to track errors

        Returns:
            True if directory exists or was created, False on error
        """
        try:
            # Check if backup_dest exists and might be read-only
            if self.backup_dest.exists():
                # Use context manager to temporarily make parent writable
                with temporarily_writable(self.backup_dest.parent):
                    with temporarily_writable(self.backup_dest):
                        self.backup_dest.mkdir(parents=True, exist_ok=True)
            else:
                # Create normally if it doesn't exist
                self.backup_dest.mkdir(parents=True, exist_ok=True)

            if self.mode_config['behavior'] == 'dynamic':
                if self.backup_path.exists():
                    with temporarily_writable(self.backup_path.parent):
                        with temporarily_writable(self.backup_path):
                            self.backup_path.mkdir(parents=True, exist_ok=True)
                else:
                    self.backup_path.mkdir(parents=True, exist_ok=True)
            return True
        except PermissionError as e:
            error_msg = f"Permission denied creating backup directory {self.backup_dest}: {e}"
            result.add_error(error_msg, is_critical=True)
            safe_print(f"🔥 CRITICAL: {error_msg}")
            logger.error(f"[backup_engine] {error_msg}")
            return False
        except OSError as e:
            error_msg = f"OS error creating backup directory {self.backup_dest}: {e}"
            result.add_error(error_msg, is_critical=True)
            safe_print(f"🔥 CRITICAL: {error_msg}")
            logger.error(f"[backup_engine] {error_msg}")
            return False
        except Exception as e:
            error_msg = f"Unexpected error creating backup directory {self.backup_dest}: {e}"
            result.add_error(error_msg, is_critical=True)
            safe_print(f"🔥 CRITICAL: {error_msg}")
            logger.error(f"[backup_engine] {error_msg}")
            return False

    def file_needs_backup(self, source_file: Path, backup_file: Path, last_timestamps: dict) -> bool:
        """Check if file needs backup based on modification time.

        Args:
            source_file: Source file to check
            backup_file: Backup destination file
            last_timestamps: Dictionary of last backup timestamps

        Returns:
            True if file needs backup, False otherwise
        """
        if not backup_file.exists():
            return True

        source_mtime = source_file.stat().st_mtime
        rel_path = str(source_file.relative_to(self.source_dir))

        last_mtime = last_timestamps.get(rel_path, 0)
        return source_mtime > last_mtime

    def remove_empty_dirs(self, path: Path):
        """Remove empty directories recursively.

        Args:
            path: Root path to clean empty directories from
        """
        try:
            for item in path.iterdir():
                if item.is_dir():
                    self.remove_empty_dirs(item)
                    try:
                        item.rmdir()
                    except OSError:
                        pass
        except Exception:
            pass

    # =============================================
    # CHANGELOG OPERATIONS
    # =============================================

    def load_changelog(self) -> Dict:
        """Load persistent changelog of backup comments.

        Returns:
            Dictionary with 'entries' list
        """
        if self.changelog_file.exists():
            try:
                with open(self.changelog_file, 'r', encoding='utf-8', errors='replace') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading changelog: {e}")
                logger.warning(f"[backup_engine] Error loading changelog: {e}")
        return {"entries": []}

    def save_changelog_entry(self, note: str) -> bool:
        """Add new entry to persistent changelog.

        Args:
            note: User note describing the backup

        Returns:
            True if save succeeded, False otherwise
        """
        try:
            changelog = self.load_changelog()
            new_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "note": note,
                "mode": self.mode,
                "backup_path": str(self.backup_path)
            }
            changelog["entries"].append(new_entry)

            with open(self.changelog_file, 'w', encoding='utf-8') as f:
                json.dump(changelog, f, indent=2, ensure_ascii=False)
            logger.info(f"[backup_engine] Saved changelog entry: {note[:50]}")
            return True
        except Exception as e:
            print(f"Error saving changelog entry: {e}")
            logger.error(f"[backup_engine] Error saving changelog: {e}")
            return False

    def display_previous_comments(self):
        """Display previous backup comments with mode identification."""
        try:
            changelog = self.load_changelog()
            entries = changelog.get("entries", [])

            if not entries:
                print(f"No previous {self.mode_config['name']} backup comments found.")
                return

            print(f"\n{'='*60}")
            print(f"PREVIOUS {self.mode_config['name'].upper()} BACKUP COMMENTS")
            print('='*60)

            # Show last 10 entries (most recent first)
            recent_entries = entries[-10:]
            for i, entry in enumerate(reversed(recent_entries), 1):
                try:
                    timestamp = datetime.datetime.fromisoformat(entry["timestamp"])
                    formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")
                    mode_info = entry.get('mode', 'unknown')
                    # Handle encoding issues in notes
                    note = str(entry['note']).encode('ascii', errors='replace').decode('ascii')
                    print(f"{i:2d}. [{formatted_time}] [{mode_info}] {note}")
                except Exception as e:
                    print(f"{i:2d}. [ERROR] Failed to display entry: {e}")

            if len(entries) > 10:
                print(f"\n... and {len(entries) - 10} older entries")
            print()
        except FileNotFoundError:
            print(f"No previous {self.mode_config['name']} backup comments found.")
        except PermissionError as e:
            print(f"⚠️  Warning: Cannot read backup history - permission denied: {e}")
            print("Continuing with backup...")
        except Exception as e:
            print(f"⚠️  Warning: Error displaying comments: {e}")
            print("Continuing with backup...")

    def load_backup_info(self) -> Dict:
        """Load backup information from JSON file.

        Returns:
            Dictionary with backup information
        """
        if self.backup_info_file.exists():
            try:
                with open(self.backup_info_file, 'r', encoding='utf-8', errors='replace') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading backup info: {e}")
                logger.warning(f"[backup_engine] Error loading backup info: {e}")

        if self.mode_config['behavior'] == 'versioned':
            return {"backups": []}
        else:
            return {"last_backup": None, "file_timestamps": {}}

    def save_backup_info(self, backup_info: Dict) -> bool:
        """Save backup information to JSON file.

        Args:
            backup_info: Dictionary containing backup information

        Returns:
            True if save succeeded, False otherwise
        """
        try:
            with open(self.backup_info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving backup info: {e}")
            logger.error(f"[backup_engine] Error saving backup info: {e}")
            return False

    # =============================================
    # MAIN BACKUP EXECUTION
    # =============================================

    def run_backup(self, backup_note: str = "No note provided") -> BackupResult:
        """Execute backup with mode-specific behavior.

        This is the main orchestration method (326 lines in original).
        Coordinates all modules to perform complete backup workflow.

        Args:
            backup_note: User note describing the backup purpose

        Returns:
            BackupResult with statistics and status
        """
        logger.info(f"[backup_engine] Starting {self.mode} backup: {backup_note}")

        result = BackupResult()
        result.mode = self.mode
        result.backup_path = str(self.backup_path)

        print(f"\n{'='*70}")
        print(f"AIPass {self.mode_config['name']} - {self.mode_config['description']}")
        print('='*70)

        # Ensure backup directory exists
        if not self.ensure_backup_directory(result):
            print(f"\n🔥 BACKUP FAILED: Could not create backup directory")
            return result

        # Load previous backup info
        backup_info = self.load_backup_info()

        if self.mode_config['behavior'] == 'dynamic':
            last_timestamps = backup_info.get("file_timestamps", {})
            # Ensure last_timestamps is a dictionary
            if not isinstance(last_timestamps, dict):
                last_timestamps = {}
        else:
            last_timestamps = {}  # Versioned mode always copies everything

        # Track statistics and skipped items
        current_timestamps = {}
        skipped_items = {"directories": set(), "files": set()}

        print(f"Scanning source directory: {self.source_dir}")
        print(f"\rProcessing files... 0.0%", end='', flush=True)

        # Count total files
        total_files = 0
        for dirpath, dirnames, filenames in os.walk(self.source_dir):
            original_dirs = dirnames.copy()
            dirnames[:] = [d for d in dirnames if not self.should_ignore(Path(dirpath) / d)]
            for d in original_dirs:
                if d not in dirnames:
                    rel_dir = str(Path(dirpath).relative_to(self.source_dir) / d)
                    skipped_items["directories"].add(rel_dir)

            for filename in filenames:
                file_path = Path(dirpath) / filename
                if not self.should_ignore(file_path):
                    total_files += 1

        files_processed = 0
        print(f"\rProcessing files... 0.0%", end='', flush=True)

        # Process files
        for dirpath, dirnames, filenames in os.walk(self.source_dir):
            dirnames[:] = [d for d in dirnames if not self.should_ignore(Path(dirpath) / d)]

            for filename in filenames:
                file_path = Path(dirpath) / filename

                if self.should_ignore(file_path):
                    rel_file = str(file_path.relative_to(self.source_dir))
                    skipped_items["files"].add(rel_file)
                    continue

                result.files_checked += 1
                files_processed += 1

                rel_path = file_path.relative_to(self.source_dir)

                # NEW STRUCTURE: Only for versioned mode - every file gets its own folder
                if self.mode == 'versioned':
                    # Check if filename is too long (>50 chars) and needs shortening
                    if len(rel_path.name) > 50:
                        # Use shortened hash-based folder name for long filenames
                        name_hash = hashlib.md5(rel_path.name.encode()).hexdigest()[:8]
                        short_name = rel_path.name[:30] + f"_{name_hash}"

                        if str(rel_path.parent) == ".":
                            file_folder = self.backup_path / "root" / short_name
                        else:
                            file_folder = self.backup_path / rel_path.parent / short_name
                        backup_file = file_folder / rel_path.name
                    else:
                        # Normal path structure for shorter filenames
                        if str(rel_path.parent) == ".":
                            # Root-level file: AGENTS.md → root/AGENTS.md/AGENTS.md
                            file_folder = self.backup_path / "root" / rel_path.name
                            backup_file = file_folder / rel_path.name
                        else:
                            # Subfolder file: backup.py → backup_system/backup.py/backup.py
                            file_folder = self.backup_path / rel_path.parent / rel_path.name
                            backup_file = file_folder / rel_path.name
                else:
                    # Snapshot and other modes: keep original flat structure
                    backup_file = self.backup_path / rel_path

                # Store current timestamp
                current_timestamps[str(rel_path)] = file_path.stat().st_mtime

                # Check if file needs backup
                try:
                    # === DRY-RUN: Skip actual copying, just count files ===
                    if self.dry_run:
                        result.files_copied += 1
                    elif self.mode_config['behavior'] == 'versioned':
                        # Versioned backup: always copy, but handle file versioning
                        if copy_versioned_file(file_path, backup_file, self.backup_path, result):
                            result.files_copied += 1
                    elif self.file_needs_backup(file_path, backup_file, last_timestamps):
                        # Dynamic backup: copy if changed
                        if copy_file_with_structure(file_path, backup_file, self.backup_path, result):
                            result.files_copied += 1
                    else:
                        result.files_skipped += 1
                except Exception as e:
                    error_msg = f"Unexpected error processing {file_path}: {e}"
                    result.add_error(error_msg, is_critical=True)
                    safe_print(f"🔥 CRITICAL: {error_msg}")

                # Update progress
                percent = (files_processed / total_files * 100) if total_files else 100
                print(f"\rProcessing files... {percent:.1f}%", end='', flush=True)

        print(f"\rProcessing files... 100.0%")

        # Handle deleted files (ONLY for dynamic modes)
        if self.backup_path.exists() and self.mode_config['behavior'] == 'dynamic':
            try:
                # Dynamic modes: delete files that no longer exist
                for backup_file in self.backup_path.rglob('*'):
                    if backup_file.is_file():
                        try:
                            rel_path = backup_file.relative_to(self.backup_path)
                            source_file = self.source_dir / rel_path

                            if not source_file.exists() or self.should_ignore(source_file):
                                # Use context manager to handle read-only files before deletion
                                with temporarily_writable(backup_file.parent):
                                    with temporarily_writable(backup_file):
                                        backup_file.unlink()
                                result.files_deleted += 1
                                safe_print(f"🗑️  Deleted: {rel_path}")
                        except PermissionError as e:
                            error_msg = f"Permission denied deleting {backup_file}: {e}"
                            result.add_error(error_msg)
                            safe_print(f"❌ {error_msg}")
                        except Exception as e:
                            error_msg = f"Error deleting {backup_file}: {e}"
                            result.add_warning(error_msg)
                            safe_print(f"⚠️  {error_msg}")
            except Exception as e:
                error_msg = f"Error scanning for deleted files: {e}"
                result.add_warning(error_msg)
                print(f"⚠️  {error_msg}")

        # Versioned mode: NEVER delete or move any files - only accumulate!

        # Remove empty directories
        self.remove_empty_dirs(self.backup_path)

        # Save backup info (mode-specific format)
        if self.mode_config['behavior'] == 'versioned':
            # Versioned: add to backup list
            current_backup = {
                "backup_note": backup_note,
                "backup_name": self.backup_folder_name,
                "timestamp": datetime.datetime.now().isoformat(),
                "backup_path": str(self.backup_path),
                "source_path": str(self.source_dir),
                "mode": self.mode,
                "stats": {
                    "files_checked": result.files_checked,
                    "files_copied": result.files_copied,
                    "files_added": result.files_added,
                    "files_skipped": result.files_skipped,
                    "errors": result.errors
                }
            }
            backup_info["backups"].insert(0, current_backup)
        else:
            # Dynamic: update current state
            backup_info = {
                "backup_note": backup_note,
                "last_backup": datetime.datetime.now().isoformat(),
                "file_timestamps": current_timestamps,
                "mode": self.mode,
                "backup_path": str(self.backup_path),
                "stats": {
                    "files_checked": result.files_checked,
                    "files_copied": result.files_copied,
                    "files_added": result.files_added,
                    "files_skipped": result.files_skipped,
                    "files_deleted": result.files_deleted,
                    "errors": result.errors
                }
            }

        self.save_backup_info(backup_info)

        # Print summary with mode identification
        duration = datetime.datetime.now() - result.start_time

        # Determine overall result status
        if result.critical_errors:
            status_icon = "🔥"
            status_text = "FAILED"
        elif result.errors > 0:
            status_icon = "⚠️"
            status_text = "COMPLETED WITH ERRORS"
        elif result.warnings:
            status_icon = "⚠️"
            status_text = "COMPLETED WITH WARNINGS"
        else:
            status_icon = "✅"
            status_text = "COMPLETED SUCCESSFULLY"

        print(f"\n{'-'*60}")
        print(f"{status_icon} {self.mode_config['name'].upper()} {status_text}")
        print('-'*60)
        print(f"Files checked: {result.files_checked}")
        print(f"Files copied: {result.files_copied}")
        if self.mode == 'versioned' and result.files_added > 0:
            print(f"Files added (new): {result.files_added}")
        print(f"Files skipped: {result.files_skipped}")
        print(f"Files deleted: {result.files_deleted}")
        print(f"Errors: {result.errors}")
        print(f"Warnings: {len(result.warnings)}")
        print(f"Duration: {duration.total_seconds():.2f} seconds")
        print(f"Backup location: {self.backup_path}")

        # Display detailed error information
        if result.critical_errors:
            print(f"\n🔥 CRITICAL ERRORS ({len(result.critical_errors)}):")
            print('-'*40)
            for i, error in enumerate(result.critical_errors, 1):
                print(f"  {i:2d}. {error}")
            print(f"\n💡 RECOVERY SUGGESTIONS:")
            print(f"   • Check disk space and permissions")
            print(f"   • Ensure backup destination is accessible")
            print(f"   • Try running as administrator if permission issues")
            print(f"   • Check if antivirus is blocking file operations")

        elif result.error_details:
            print(f"\n❌ ERRORS ({len(result.error_details)}):")
            print('-'*40)
            for i, error in enumerate(result.error_details[:10], 1):  # Show first 10 errors
                print(f"  {i:2d}. {error}")
            if len(result.error_details) > 10:
                print(f"  ... and {len(result.error_details) - 10} more errors")
            print(f"\n💡 SUGGESTIONS:")
            print(f"   • Some files may be in use - try closing applications")
            print(f"   • Check file permissions on failed files")

        if result.warnings:
            print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
            print('-'*40)
            for i, warning in enumerate(result.warnings[:5], 1):  # Show first 5 warnings
                print(f"  {i:2d}. {warning}")
            if len(result.warnings) > 5:
                print(f"  ... and {len(result.warnings) - 5} more warnings")

        # Display project-specific skipped items
        tracked_items = filter_tracked_items(skipped_items)
        total_tracked = len(tracked_items["directories"]) + len(tracked_items["files"])
        total_all_skipped = len(skipped_items["directories"]) + len(skipped_items["files"])

        if total_tracked > 0:
            print(f"\nNOTABLE ITEMS SKIPPED ({total_tracked} shown, {total_all_skipped} total ignored):")
            print('-'*50)

            if tracked_items["directories"]:
                print(f"Directories ({len(tracked_items['directories'])}): ")
                for i, dir_path in enumerate(sorted(tracked_items["directories"]), 1):
                    print(f"  {i:2d}. {dir_path}/")

            if tracked_items["files"]:
                print(f"Files ({len(tracked_items['files'])}):")
                for i, file_path in enumerate(sorted(tracked_items["files"]), 1):
                    print(f"  {i:2d}. {file_path}")
        else:
            if total_all_skipped > 0:
                print(f"\nNo project-specific items skipped ({total_all_skipped} common items filtered out)")
            else:
                print(f"\nNo items were skipped.")

        # Update AIPass JSON system
        execution_time = int((datetime.datetime.now() - result.start_time).total_seconds() * 1000)
        if result.success and result.errors == 0:
            log_operation("backup", f"{self.mode} backup completed successfully - {result.files_copied} files", True, "INFO", execution_time)
            logger.info(f"[backup_engine] {self.mode} backup completed successfully - {result.files_copied} files copied in {execution_time}ms")

            # Google Drive sync (automatic for versioned backups when successful)
            if self.mode == 'versioned':
                sync_to_drive(self.backup_path, self.source_dir, self.mode, backup_note)

            # Set backup directory to read-only for protection
            set_backup_readonly(self.backup_path)
        else:
            log_operation("backup", f"{self.mode} backup completed with {result.errors} errors", False, "ERROR", execution_time)
            logger.error(f"[backup_engine] {self.mode} backup completed with {result.errors} errors in {execution_time}ms")

        update_data_file(result)

        return result

# =============================================
# MODULE INITIALIZATION
# =============================================

logger.info("[backup_engine] Backup orchestration engine loaded")
