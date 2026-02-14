#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: prax_json_handler.py - Global JSON Handler Utility
# Date: 2025-11-03
# Version: 1.0.0
# Category: prax
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-03): Initial version - 3-file JSON utilities
# =============================================

"""
Prax JSON Handler - Global Utility

Provides standardized 3-file JSON structure (config/data/log) for all modules.
Write JSON handling ONCE here, all modules import and use.

GRACEFUL DEGRADATION:
If this module fails to import, modules should continue running without JSON.
Modules should catch ImportError and provide fallback behavior.
"""

# Standard library imports
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# =============================================================================
# CONSTANTS
# =============================================================================

# Standard JSON structure
DEFAULT_CONFIG_STRUCTURE = {
    "module_name": "",
    "version": "1.0.0",
    "timestamp": "",
    "config": {}
}

DEFAULT_DATA_STRUCTURE = {
    "module_name": "",
    "timestamp": "",
    "data": {}
}

DEFAULT_LOG_ENTRY = {
    "timestamp": "",
    "operation": "",
    "success": True,
    "details": None,
    "error": None
}

# =============================================================================
# CONFIG OPERATIONS
# =============================================================================

def load_config(module_name: str, json_dir: Path) -> Dict[str, Any]:
    """
    Load module config file with standard structure

    Args:
        module_name: Name of the module (e.g., "branch_create")
        json_dir: Directory where JSON files are stored

    Returns:
        Config dict with standard structure, or default if not found
    """
    config_file = json_dir / f"{module_name}_config.json"

    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Return default structure if file doesn't exist
            default = DEFAULT_CONFIG_STRUCTURE.copy()
            default["module_name"] = module_name
            default["timestamp"] = datetime.now().isoformat()
            return default
    except Exception as e:
        # Graceful degradation - return default on error
        print(f"⚠️  [prax_json_handler] Config load failed for {module_name}: {e}")
        default = DEFAULT_CONFIG_STRUCTURE.copy()
        default["module_name"] = module_name
        default["timestamp"] = datetime.now().isoformat()
        return default


def save_config(module_name: str, json_dir: Path, config_data: Dict[str, Any]) -> bool:
    """
    Save module config file with standard structure

    Args:
        module_name: Name of the module
        json_dir: Directory where JSON files are stored
        config_data: Config data dict (will be wrapped in standard structure)

    Returns:
        True if successful, False otherwise
    """
    config_file = json_dir / f"{module_name}_config.json"

    try:
        # Ensure directory exists
        json_dir.mkdir(parents=True, exist_ok=True)

        # Wrap data in standard structure
        output = {
            "module_name": module_name,
            "version": config_data.get("version", "1.0.0"),
            "timestamp": datetime.now().isoformat(),
            "config": config_data
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        # Graceful degradation - log error but don't crash
        print(f"⚠️  [prax_json_handler] Config save failed for {module_name}: {e}")
        return False

# =============================================================================
# DATA OPERATIONS
# =============================================================================

def load_data(module_name: str, json_dir: Path) -> Dict[str, Any]:
    """
    Load module data file with standard structure

    Args:
        module_name: Name of the module
        json_dir: Directory where JSON files are stored

    Returns:
        Data dict with standard structure, or default if not found
    """
    data_file = json_dir / f"{module_name}_data.json"

    try:
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Return default structure
            default = DEFAULT_DATA_STRUCTURE.copy()
            default["module_name"] = module_name
            default["timestamp"] = datetime.now().isoformat()
            return default
    except Exception as e:
        print(f"⚠️  [prax_json_handler] Data load failed for {module_name}: {e}")
        default = DEFAULT_DATA_STRUCTURE.copy()
        default["module_name"] = module_name
        default["timestamp"] = datetime.now().isoformat()
        return default


def save_data(module_name: str, json_dir: Path, data: Dict[str, Any]) -> bool:
    """
    Save module data file with standard structure

    Args:
        module_name: Name of the module
        json_dir: Directory where JSON files are stored
        data: Data dict (will be wrapped in standard structure)

    Returns:
        True if successful, False otherwise
    """
    data_file = json_dir / f"{module_name}_data.json"

    try:
        # Ensure directory exists
        json_dir.mkdir(parents=True, exist_ok=True)

        # Wrap data in standard structure
        output = {
            "module_name": module_name,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"⚠️  [prax_json_handler] Data save failed for {module_name}: {e}")
        return False

# =============================================================================
# LOG OPERATIONS
# =============================================================================

def log_operation(
    module_name: str,
    json_dir: Path,
    operation: str,
    success: bool = True,
    details: Any = None,
    error: Optional[str] = None
) -> bool:
    """
    Log module operation to log file

    Args:
        module_name: Name of the module
        json_dir: Directory where JSON files are stored
        operation: Operation description
        success: Whether operation succeeded
        details: Additional details (any JSON-serializable data)
        error: Error message if failed

    Returns:
        True if successful, False otherwise
    """
    log_file = json_dir / f"{module_name}_log.json"

    try:
        # Ensure directory exists
        json_dir.mkdir(parents=True, exist_ok=True)

        # Load existing log
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                log_entries = json.load(f)
        else:
            log_entries = []

        # Create new entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "success": success,
            "details": details,
            "error": error
        }

        # Add to log (newest first)
        log_entries.insert(0, entry)

        # Keep only last 100 entries
        log_entries = log_entries[:100]

        # Save log
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entries, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        # Graceful degradation - print but don't crash
        print(f"⚠️  [prax_json_handler] Log operation failed for {module_name}: {e}")
        return False

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def initialize_json_structure(module_name: str, json_dir: Path, initial_config: Optional[Dict] = None, initial_data: Optional[Dict] = None) -> bool:
    """
    Initialize complete 3-file JSON structure for a module

    Args:
        module_name: Name of the module
        json_dir: Directory where JSON files are stored
        initial_config: Initial config data (optional)
        initial_data: Initial data (optional)

    Returns:
        True if successful
    """
    try:
        # Create config
        if initial_config:
            save_config(module_name, json_dir, initial_config)
        else:
            save_config(module_name, json_dir, {})

        # Create data
        if initial_data:
            save_data(module_name, json_dir, initial_data)
        else:
            save_data(module_name, json_dir, {})

        # Create initial log entry
        log_operation(module_name, json_dir, "Module initialized", True, {"status": "ready"})

        return True
    except Exception as e:
        print(f"⚠️  [prax_json_handler] Initialization failed for {module_name}: {e}")
        return False

# =============================================================================
# GRACEFUL DEGRADATION HELPER
# =============================================================================

def is_available() -> bool:
    """
    Check if this module is available and working

    Returns:
        True if module can be used
    """
    # Simple test - can we create a temp dict and serialize it?
    try:
        test_data = {"test": "data"}
        json.dumps(test_data)
        return True
    except:
        return False
