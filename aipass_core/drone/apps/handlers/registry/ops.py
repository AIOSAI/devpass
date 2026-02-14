#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: ops.py - Registry CRUD Operations
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/registry
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2025-11-13): PILOT MIGRATION - Standalone handler from drone_registry.py
#   - v1.0.0 (2025-11-07): Initial extraction with dependency injection
# CODE STANDARDS: Handler pattern - pure implementation, no CLI
# =============================================

"""
Registry CRUD Operations Handler

Core operations for loading, saving, creating, and validating the drone command registry.
This handler is independent and transportable - no cross-handler imports.

Features:
- Load registry with auto-healing
- Save registry with validation
- Create new empty registry
- Validate registry structure
- Get default values for missing keys
- Module ignore filtering

Usage:
    from drone.apps.handlers.registry.ops import load_registry, save_registry

    registry = load_registry()
    registry["commands"]["new_cmd"] = {...}
    save_registry(registry)
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "registry_ops"
DRONE_JSON_DIR = AIPASS_ROOT / "drone" / "drone_json"
REGISTRY_FILE = DRONE_JSON_DIR / "drone_registry.json"
CONFIG_FILE = DRONE_JSON_DIR / "drone_registry_config.json"
DATA_FILE = DRONE_JSON_DIR / "drone_registry_data.json"
LOG_FILE = DRONE_JSON_DIR / "drone_registry_log.json"

# Modules to ignore in registry
IGNORED_MODULES = {
    "__main__", "script", "update_package_json", "validate_packages",
    "update_ext_version", "__pycache__", "test", "temp", "backup_old",
    "drone_discovery", "drone_registry", "drone_loader"
}

# =============================================
# HELPER FUNCTIONS
# =============================================

def ensure_drone_json_dir():
    """Ensure drone_json directory exists"""
    DRONE_JSON_DIR.mkdir(parents=True, exist_ok=True)

def log_operation_local(operation: str, success: bool, details: str = "", error: str = ""):
    """Log registry operations to module log file"""
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
                data = json.load(f)
                if isinstance(data, list):
                    logs = data
                elif isinstance(data, dict) and "entries" in data:
                    logs = data["entries"]
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            logs = []

    logs.append(log_entry)

    # Keep last 1000 entries
    if len(logs) > 1000:
        logs = logs[-1000:]

    try:
        ensure_drone_json_dir()
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error saving log: {e}")

def load_config() -> Dict:
    """Load registry configuration"""
    if not CONFIG_FILE.exists():
        # Create default config
        default_config = {
            "module_name": "drone_registry",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "enabled": True,
                "version": "1.0.0",
                "auto_healing_enabled": True,
                "registry_monitoring": True,
                "cleanup_orphans": True,
                "max_registry_entries": 1000,
                "ignore_modules": list(IGNORED_MODULES)
            }
        }
        try:
            ensure_drone_json_dir()
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Error creating config: {e}")
        return default_config

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error loading config: {e}")
        return {"config": {"enabled": True}}

def update_data_file(stats: Dict):
    """Update data file with current statistics"""
    data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "runtime_state": {
            "registry_active": True,
            "auto_healing": True,
            "monitoring_enabled": True
        },
        "statistics": stats
    }

    try:
        ensure_drone_json_dir()
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error updating data file: {e}")

# =============================================
# CORE REGISTRY OPERATIONS
# =============================================

def load_registry() -> Dict:
    """Load command registry with auto-healing

    Returns:
        Registry dict with commands, modules, and metadata

    Example:
        >>> registry = load_registry()
        >>> print(f"Commands: {len(registry.get('commands', {}))}")
    """
    config = load_config()
    registry_config = config.get("config", {})

    if not registry_config.get("enabled", True):
        log_operation_local("registry_load_skipped", True, "Registry disabled in config")
        return {}

    ensure_drone_json_dir()
    log_operation_local("registry_load_started", True, "Loading registry")

    if not REGISTRY_FILE.exists():
        log_operation_local("registry_created", True, "Creating new registry")
        logger.info(f"[{MODULE_NAME}] Creating new registry")
        return create_empty_registry()

    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            registry = json.load(f)

        # Auto-heal registry structure if needed
        if not isinstance(registry, dict):
            logger.warning(f"[{MODULE_NAME}] Invalid registry structure, recreating")
            return create_empty_registry()

        # Ensure required keys exist
        required_keys = ["commands", "modules", "last_updated", "version"]
        for key in required_keys:
            if key not in registry:
                registry[key] = get_default_value(key)

        # Update statistics and data file
        stats = {
            "total_commands": len(registry.get('commands', {})),
            "total_modules": len(registry.get('modules', {})),
            "last_load": datetime.now(timezone.utc).isoformat(),
            "auto_healing_enabled": registry_config.get("auto_healing_enabled", True),
            "registry_size_kb": 0
        }

        update_data_file(stats)
        log_operation_local("registry_load_completed", True, f"Registry loaded: {stats['total_commands']} commands, {stats['total_modules']} modules")

        logger.info(f"[{MODULE_NAME}] Registry loaded: {len(registry.get('commands', {}))} commands")
        return registry

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to load registry: {e}")
        logger.info(f"[{MODULE_NAME}] Creating new registry")
        return create_empty_registry()

def save_registry(registry: Dict) -> bool:
    """Save command registry with validation

    Args:
        registry: Registry dict to save

    Returns:
        True if saved successfully

    Example:
        >>> registry["commands"]["new_cmd"] = {...}
        >>> save_registry(registry)
        True
    """
    ensure_drone_json_dir()

    try:
        # Update timestamp
        registry["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Validate structure
        if not validate_registry_structure(registry):
            logger.error(f"[{MODULE_NAME}] Invalid registry structure, cannot save")
            return False

        # Save registry
        with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)

        logger.info(f"[{MODULE_NAME}] Registry saved: {len(registry.get('commands', {}))} commands")

        # Log operation
        log_operation_local("registry_saved", True, f"Registry saved with {len(registry.get('commands', {}))} commands")

        return True

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to save registry: {e}")
        return False

def create_empty_registry() -> Dict:
    """Create empty registry with proper structure

    Returns:
        New empty registry dict

    Example:
        >>> registry = create_empty_registry()
        >>> print(registry["version"])
        '1.0.0'
    """
    registry = {
        "version": "1.0.0",
        "created": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "commands": {},
        "modules": {},
        "statistics": {
            "total_commands": 0,
            "total_modules": 0,
            "last_discovery": None,
            "auto_healing_count": 0
        }
    }

    save_registry(registry)
    log_operation_local("registry_created", True, "New registry created")

    return registry

# =============================================
# VALIDATION
# =============================================

def validate_registry_structure(registry: Dict) -> bool:
    """Validate registry has proper structure

    Args:
        registry: Registry dict to validate

    Returns:
        True if valid structure

    Example:
        >>> registry = {"commands": {}, "modules": {}, "last_updated": "...", "version": "1.0.0"}
        >>> validate_registry_structure(registry)
        True
    """
    required_keys = ["commands", "modules", "last_updated", "version"]
    return all(key in registry for key in required_keys)

def get_default_value(key: str) -> Any:
    """Get default value for missing registry keys

    Args:
        key: Registry key name

    Returns:
        Default value for the key

    Example:
        >>> get_default_value("commands")
        {}
    """
    defaults = {
        "commands": {},
        "modules": {},
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "statistics": {
            "total_commands": 0,
            "total_modules": 0,
            "last_discovery": None,
            "auto_healing_count": 0
        }
    }
    return defaults.get(key, None)

def should_ignore_module(module_name: str) -> bool:
    """Check if module should be ignored in registry

    Args:
        module_name: Name of module to check

    Returns:
        True if module should be ignored

    Example:
        >>> should_ignore_module("__pycache__")
        True
        >>> should_ignore_module("backup_system")
        False
    """
    return module_name in IGNORED_MODULES
