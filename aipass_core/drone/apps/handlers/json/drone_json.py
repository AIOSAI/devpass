#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: drone_json.py
# Date: 2025-11-07
# Version: 1.0.0
# Category: drone/handlers/json
#
# CHANGELOG:
#   - v1.0.0 (2025-11-07): Consolidated from drone_registry, drone_loader, drone_discovery - unified JSON operations
# =============================================

"""
Drone JSON Operations Handler

Consolidated JSON operations for drone system.
Provides unified 3-file JSON pattern management for all drone modules.

Features:
- Config file creation and loading
- Data file updates
- Operation logging (both local and system-wide)
- JSON directory management
- Log ID generation

Usage:
    from drone.apps.handlers.json.drone_json import load_config, log_operation

    config = load_config("my_module")
    log_operation("my_module", "operation_name", True, "Details here")
"""

# =============================================
# IMPORTS
# =============================================

import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

# =============================================
# CONFIGURATION
# =============================================

MODULE_NAME = "drone_json"
DRONE_JSON_DIR = AIPASS_ROOT / "drone" / "drone_json"

# =============================================
# DIRECTORY MANAGEMENT
# =============================================

def ensure_drone_json_dir() -> bool:
    """Ensure drone JSON directory exists

    Returns:
        True if directory exists or was created successfully
    """
    try:
        DRONE_JSON_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error creating JSON directory: {e}")
        return False

# =============================================
# CONFIG FILE OPERATIONS
# =============================================

def create_config_file(module_name: str, default_config: Dict[str, Any] | None = None) -> bool:
    """Create default config file if it doesn't exist

    Args:
        module_name: Name of the module
        default_config: Optional default configuration dict

    Returns:
        True if file was created or already exists

    Example:
        >>> create_config_file("drone_registry", {"enabled": True})
        True
    """
    config_file = DRONE_JSON_DIR / f"{module_name}_config.json"

    if config_file.exists():
        return True

    if default_config is None:
        default_config = {"enabled": True}

    config_structure = {
        "module_name": module_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": default_config
    }

    try:
        ensure_drone_json_dir()
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_structure, f, indent=2, ensure_ascii=False)
        logger.info(f"[{MODULE_NAME}] Config file created for {module_name}")
        return True
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error creating config file for {module_name}: {e}")
        return False


def load_config(module_name: str) -> Dict[str, Any]:
    """Load configuration for a module

    Args:
        module_name: Name of the module

    Returns:
        Configuration dict, or default if error

    Example:
        >>> config = load_config("drone_registry")
        >>> enabled = config.get("config", {}).get("enabled", True)
    """
    config_file = DRONE_JSON_DIR / f"{module_name}_config.json"

    # Create if doesn't exist
    if not config_file.exists():
        create_config_file(module_name)

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error loading config for {module_name}: {e}")
        return {"config": {"enabled": True}}

# =============================================
# DATA FILE OPERATIONS
# =============================================

def update_data_file(module_name: str, data: Dict[str, Any]) -> bool:
    """Update data file with current information

    Args:
        module_name: Name of the module
        data: Data dict to write

    Returns:
        True if successful

    Example:
        >>> update_data_file("drone_registry", {"stats": {"total": 10}})
        True
    """
    data_file = DRONE_JSON_DIR / f"{module_name}_data.json"

    data_structure = {
        "module_name": module_name,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "data": data
    }

    try:
        ensure_drone_json_dir()
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data_structure, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error updating data file for {module_name}: {e}")
        return False

# =============================================
# LOG FILE OPERATIONS
# =============================================

def get_next_log_id(module_name: str) -> int:
    """Get next available log ID for a module

    Args:
        module_name: Name of the module

    Returns:
        Next log ID number

    Example:
        >>> next_id = get_next_log_id("drone_registry")
        >>> print(next_id)
        1
    """
    log_file = DRONE_JSON_DIR / f"{module_name}_log.json"

    if not log_file.exists():
        return 1

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both list and dict formats
            if isinstance(data, list):
                return len(data) + 1
            elif isinstance(data, dict) and "entries" in data:
                return len(data["entries"]) + 1
            else:
                return 1
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error getting next log ID for {module_name}: {e}")
        return 1


def load_log_data(module_name: str) -> list:
    """Load log entries for a module

    Args:
        module_name: Name of the module

    Returns:
        List of log entries

    Example:
        >>> logs = load_log_data("drone_registry")
        >>> print(f"Total logs: {len(logs)}")
    """
    log_file = DRONE_JSON_DIR / f"{module_name}_log.json"

    if not log_file.exists():
        return []

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both list and dict formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "entries" in data:
                return data["entries"]
            else:
                return []
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error loading log data for {module_name}: {e}")
        return []


def log_operation_local(module_name: str, operation: str, success: bool, details: str = "", error: str = "") -> bool:
    """Log operation to individual module log file

    Args:
        module_name: Name of the module
        operation: Operation name
        success: Whether operation succeeded
        details: Optional operation details
        error: Optional error message

    Returns:
        True if logged successfully

    Example:
        >>> log_operation_local("drone_registry", "load_registry", True, "Loaded 10 modules")
        True
    """
    log_file = DRONE_JSON_DIR / f"{module_name}_log.json"

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "success": success,
        "details": details,
        "error": error
    }

    logs = load_log_data(module_name)
    logs.insert(0, log_entry)  # Newest first
    logs = logs[:100]  # Keep last 100 entries

    try:
        ensure_drone_json_dir()
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error logging operation for {module_name}: {e}")
        return False


def log_operation(module_name: str, operation: str, success: bool, details: Any = None, error: str | None = None) -> bool:
    """Log operation to system-wide drone log

    Args:
        module_name: Name of the module
        operation: Operation name
        success: Whether operation succeeded
        details: Optional operation details (any type)
        error: Optional error message

    Returns:
        True if logged successfully

    Example:
        >>> log_operation("drone_discovery", "scan_module", True, {"modules_found": 5})
        True
    """
    # Convert details to string if needed
    details_str = str(details) if details is not None else ""

    return log_operation_local(module_name, operation, success, details_str, error or "")
