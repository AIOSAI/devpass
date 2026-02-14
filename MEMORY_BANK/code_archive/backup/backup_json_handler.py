#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: backup_json_handler.py
# Date: 2025-10-14
# Version: 1.0.0
# Category: backup_system
#
# CHANGELOG:
#   - v1.0.0 (2025-10-14): Initial extraction from backup.py
#     * Extracted JSON operations (lines 99-110, 365-550)
#     * 3-file JSON pattern + mode-specific JSONs
#     * Log rotation and statistics tracking
#     * Manages 9 JSON files total in backup_system_json/ folder
# =============================================

"""
Backup System JSON Handler

Manages all JSON file operations for the backup system.
Implements AIPass 3-file JSON pattern with mode-specific extensions.
All JSON files auto-create on first use.
"""

# =============================================
# IMPORTS
# =============================================

import sys
import json
import datetime
from pathlib import Path
from typing import Dict

# Infrastructure import pattern
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))
from prax.apps.prax_logger import system_logger as logger

# Import safe_print from backup_utils
from backup_utils import safe_print

# =============================================
# CONSTANTS
# =============================================

# Get branch root directory (module is in apps/, so parent.parent)
SCRIPT_DIR = Path(__file__).resolve().parent.parent

# JSON file paths (AIPass standard)
JSON_DIR = SCRIPT_DIR / "backup_system_json"
CONFIG_FILE = JSON_DIR / "backup_config.json"
DATA_FILE = JSON_DIR / "backup_data.json"
LOG_FILE = JSON_DIR / "backup_log.json"

# =============================================
# CORE JSON FUNCTIONS
# =============================================

def load_json_file(file_path: Path) -> dict:
    """Load JSON file, return empty dict if file doesn't exist.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary containing JSON data, or empty dict if file doesn't exist
    """
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        safe_print(f"⚠️ Warning: Could not load {file_path}: {e}")
        logger.warning(f"[Backup System] Failed to load JSON file {file_path}: {e}")
        return {}


def save_json_file(file_path: Path, data: dict):
    """Save data to JSON file with proper formatting.

    Args:
        file_path: Path to JSON file
        data: Dictionary to save
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        safe_print(f"❌ Error saving {file_path}: {e}")
        logger.error(f"[Backup System] Failed to save JSON file {file_path}: {e}")


def initialize_json_files() -> bool:
    """Initialize the 3-JSON system files if they don't exist.

    Creates backup_system_json/ directory and initializes:
    - backup_config.json (static configuration)
    - backup_data.json (runtime state and statistics)
    - backup_log.json (operation history)

    Returns:
        True if all files exist or were created successfully, False otherwise
    """
    try:
        # Ensure JSON directory exists first
        JSON_DIR.mkdir(parents=True, exist_ok=True)

        # Track what gets created
        created_files = []

        # Initialize config file
        if not CONFIG_FILE.exists():
            default_config = {
                "module_name": "backup_system",
                "version": "1.0.0",
                "timestamp": datetime.datetime.now().isoformat(),
                "config": {
                    "auto_create_backups": True,
                    "max_log_entries": 1000,
                    "default_mode": "snapshot",
                    "compression_enabled": False,
                    "notifications_enabled": True
                }
            }
            save_json_file(CONFIG_FILE, default_config)
            created_files.append(CONFIG_FILE.name)
            logger.info(f"[Backup System] Initialized config file: {CONFIG_FILE}")

        # Initialize data file
        if not DATA_FILE.exists():
            default_data = {
                "last_updated": datetime.datetime.now().isoformat(),
                "runtime_state": {
                    "current_status": "idle",
                    "last_backup": None,
                    "active_mode": None,
                    "total_files_backed_up": 0,
                    "backup_in_progress": False
                },
                "statistics": {
                    "total_backups": 0,
                    "successful_backups": 0,
                    "failed_backups": 0,
                    "snapshot_backups": 0,
                    "versioned_backups": 0,
                    "total_files_processed": 0
                },
                "recent_backups": []
            }
            save_json_file(DATA_FILE, default_data)
            created_files.append(DATA_FILE.name)
            logger.info(f"[Backup System] Initialized data file: {DATA_FILE}")

        # Initialize log file
        if not LOG_FILE.exists():
            default_log = {
                "entries": [],
                "summary": {
                    "total_entries": 0,
                    "last_entry": None,
                    "error_count": 0,
                    "warning_count": 0,
                    "info_count": 0
                }
            }
            save_json_file(LOG_FILE, default_log)
            created_files.append(LOG_FILE.name)
            logger.info(f"[Backup System] Initialized log file: {LOG_FILE}")

        # Verify all JSON files exist
        all_exist = CONFIG_FILE.exists() and DATA_FILE.exists() and LOG_FILE.exists()

        if created_files:
            safe_print(f"✅ Created JSON files in {JSON_DIR}: {', '.join(created_files)}")

        if all_exist:
            safe_print(f"✅ All JSON files confirmed in: {JSON_DIR}")
            logger.info("[Backup System] AIPass 3-JSON system initialization completed successfully")
        else:
            missing = []
            if not CONFIG_FILE.exists(): missing.append("config")
            if not DATA_FILE.exists(): missing.append("data")
            if not LOG_FILE.exists(): missing.append("log")
            safe_print(f"❌ Missing JSON files: {', '.join(missing)}")
            return False

        return True
    except Exception as e:
        safe_print(f"❌ Error initializing JSON files: {e}")
        logger.error(f"[Backup System] Failed to initialize JSON files: {e}")
        return False


def log_operation(operation: str, message: str, success: bool, level: str = "INFO", execution_time_ms: int = 0):
    """Add entry to backup log following AIPass standards.

    Args:
        operation: Operation name (e.g., "backup", "restore")
        message: Human-readable message describing the operation
        success: Whether the operation succeeded
        level: Log level ("INFO", "WARNING", "ERROR")
        execution_time_ms: Execution time in milliseconds (optional)
    """
    try:
        log_data = load_json_file(LOG_FILE)
        if "entries" not in log_data:
            log_data["entries"] = []
        if "summary" not in log_data:
            log_data["summary"] = {"total_entries": 0, "last_entry": None, "error_count": 0, "warning_count": 0, "info_count": 0}

        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": level,
            "operation": operation,
            "message": message,
            "success": success,
            "execution_time_ms": execution_time_ms
        }

        log_data["entries"].append(entry)
        log_data["summary"]["total_entries"] = len(log_data["entries"])
        log_data["summary"]["last_entry"] = entry["timestamp"]

        # Update counters
        if level == "ERROR":
            log_data["summary"]["error_count"] += 1
        elif level == "WARNING":
            log_data["summary"]["warning_count"] += 1
        else:
            log_data["summary"]["info_count"] += 1

        # Log rotation: keep last 1000 entries
        if len(log_data["entries"]) > 1000:
            log_data["entries"] = log_data["entries"][-1000:]
            log_data["summary"]["total_entries"] = len(log_data["entries"])

        save_json_file(LOG_FILE, log_data)
    except Exception as e:
        safe_print(f"❌ Error logging operation: {e}")
        logger.error(f"[Backup System] Failed to log operation: {e}")


def update_data_file(backup_result):
    """Update data file with backup statistics.

    Args:
        backup_result: BackupResult instance with operation statistics
    """
    try:
        data = load_json_file(DATA_FILE)

        # Update runtime state
        data["last_updated"] = datetime.datetime.now().isoformat()
        data["runtime_state"]["current_status"] = "completed" if backup_result.success else "failed"
        data["runtime_state"]["last_backup"] = datetime.datetime.now().isoformat()
        data["runtime_state"]["active_mode"] = backup_result.mode
        data["runtime_state"]["total_files_backed_up"] = backup_result.files_copied
        data["runtime_state"]["backup_in_progress"] = False

        # Update statistics
        data["statistics"]["total_backups"] += 1
        if backup_result.success:
            data["statistics"]["successful_backups"] += 1
        else:
            data["statistics"]["failed_backups"] += 1

        # Mode-specific counters
        if backup_result.mode == "snapshot":
            data["statistics"]["snapshot_backups"] += 1
        elif backup_result.mode == "versioned":
            data["statistics"]["versioned_backups"] += 1

        data["statistics"]["total_files_processed"] += backup_result.files_checked

        # Add to recent backups (keep last 10)
        if "recent_backups" not in data:
            data["recent_backups"] = []
        data["recent_backups"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "mode": backup_result.mode,
            "success": backup_result.success,
            "files_copied": backup_result.files_copied,
            "errors": backup_result.errors
        })
        data["recent_backups"] = data["recent_backups"][-10:]  # Keep last 10

        save_json_file(DATA_FILE, data)
    except Exception as e:
        safe_print(f"❌ Error updating data file: {e}")
        logger.error(f"[Backup System] Failed to update data file: {e}")


def get_json_dir() -> Path:
    """Get the JSON directory path.

    Returns:
        Path object for backup_system_json/ directory
    """
    return JSON_DIR


def get_config_file_path() -> Path:
    """Get the config file path.

    Returns:
        Path object for backup_config.json
    """
    return CONFIG_FILE


def get_data_file_path() -> Path:
    """Get the data file path.

    Returns:
        Path object for backup_data.json
    """
    return DATA_FILE


def get_log_file_path() -> Path:
    """Get the log file path.

    Returns:
        Path object for backup_log.json
    """
    return LOG_FILE

# =============================================
# MODULE INITIALIZATION
# =============================================

# Auto-initialize on import (AIPass pattern)
logger.info("[backup_json_handler] Module loaded - JSON operations ready")
