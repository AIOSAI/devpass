#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: drone_registry.py - Command Registry Management
# Date: 2025-09-22
# Version: 1.0.0
# Category: drone
#
# CHANGELOG:
#   - v1.0.0 (2025-09-22): Initial implementation with flow registry patterns
# =============================================

"""
Drone Command Registry Management

Manages drone command registry with auto-healing capabilities.
Based on flow_registry patterns with command-specific adaptations.

Features:
- Registry-based command tracking
- Auto-healing on startup
- Module command mapping
- Conflict resolution
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.append(str(AIPASS_ROOT))

from prax.apps.prax_logger import system_logger as logger

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "drone_registry"
ECOSYSTEM_ROOT = Path.home()  # Scan from /home/aipass/ (not just aipass_core)
DRONE_JSON_DIR = AIPASS_ROOT / "drone" / "drone_json"

# Registry coordination file (stays as is)
REGISTRY_FILE = DRONE_JSON_DIR / "drone_registry.json"

# 3-File JSON Pattern for drone_registry module
CONFIG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_log.json"

# Modules to ignore in registry
IGNORED_MODULES = {
    "__main__", "script", "update_package_json", "validate_packages",
    "update_ext_version", "__pycache__", "test", "temp", "backup_old",
    "drone_discovery", "drone_registry", "drone_loader"  # Don't register ourselves
}

# =============================================
# JSON FILE MANAGEMENT (3-FILE PATTERN)
# =============================================

def create_config_file():
    """Create default config file if it doesn't exist"""
    if CONFIG_FILE.exists():
        return

    default_config = {
        "module_name": MODULE_NAME,
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
        DRONE_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        logger.info(f"[{MODULE_NAME}] Config file created")
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error creating config file: {e}")

def load_config():
    """Load configuration"""
    create_config_file()

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error loading config: {e}")
        return {"config": {"enabled": True}}

def update_data_file(stats):
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
        DRONE_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error updating data file: {e}")

def log_operation_local(operation: str, success: bool, details: str = "", error: str = ""):
    """Log registry operations to individual module log file"""
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
                # Handle both list and dict formats
                if isinstance(data, list):
                    logs = data
                elif isinstance(data, dict) and "entries" in data:
                    logs = data["entries"]
                else:
                    logs = []
        except:
            logs = []

    logs.append(log_entry)

    # Keep last 1000 entries
    if len(logs) > 1000:
        logs = logs[-1000:]

    try:
        DRONE_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error saving log: {e}")

# =============================================
# HELPER FUNCTIONS
# =============================================

def ensure_drone_json_dir():
    """Ensure drone_json directory exists"""
    DRONE_JSON_DIR.mkdir(exist_ok=True)

def log_operation(operation: str, details: Dict[str, Any], success: bool = True):
    """Log operation to drone log file - following flow pattern"""
    ensure_drone_json_dir()

    log_entry = {
        "id": get_next_log_id(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO" if success else "ERROR",
        "operation": operation,
        "message": details.get("message", ""),
        "success": success,
        "details": details
    }

    # Load existing log
    log_data = load_log_data()
    log_data["entries"].insert(0, log_entry)  # Newest first

    # Keep only last 100 entries
    log_data["entries"] = log_data["entries"][:100]
    log_data["summary"]["total_entries"] = len(log_data["entries"])
    log_data["summary"]["last_entry"] = log_entry["timestamp"]
    log_data["summary"]["next_id"] = log_entry["id"] + 1

    # Save log
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def get_next_log_id() -> int:
    """Get next sequential log ID"""
    log_data = load_log_data()
    return log_data["summary"]["next_id"]

def load_log_data() -> Dict:
    """Load log data with default structure"""
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle legacy list format (convert to new dict format)
            if isinstance(data, list):
                logger.info(f"[{MODULE_NAME}] Converting legacy log format to new structure")
                return {
                    "entries": data,
                    "summary": {
                        "total_entries": len(data),
                        "last_entry": data[0]["timestamp"] if data else None,
                        "next_id": len(data) + 1
                    }
                }

            # Already in correct dict format
            return data
        except Exception as e:
            logger.warning(f"Could not load log file: {e}")

    return {
        "entries": [],
        "summary": {
            "total_entries": 0,
            "last_entry": None,
            "next_id": 1
        }
    }

# =============================================
# MAIN FUNCTIONS
# =============================================

def load_registry() -> Dict:
    """Load command registry with auto-healing - following flow pattern"""
    # Load config and initialize JSON files
    config = load_config()
    registry_config = config.get("config", {})

    # Check if registry is enabled
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
            "registry_size_kb": 0  # Could add file size if needed
        }

        update_data_file(stats)
        log_operation_local("registry_load_completed", True, f"Registry loaded: {stats['total_commands']} commands, {stats['total_modules']} modules")

        logger.info(f"[{MODULE_NAME}] Registry loaded: {len(registry.get('commands', {}))} commands")
        return registry

    except Exception as e:
        log_operation_local("registry_load_failed", False, f"Failed to load registry: {e}", str(e))
        logger.error(f"[{MODULE_NAME}] Failed to load registry: {e}")
        logger.info(f"[{MODULE_NAME}] Creating new registry")
        return create_empty_registry()

def save_registry(registry: Dict):
    """Save command registry with validation"""
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
        log_operation("registry_saved", {
            "message": f"Registry saved with {len(registry.get('commands', {}))} commands",
            "command_count": len(registry.get('commands', {})),
            "module_count": len(registry.get('modules', {}))
        })

        return True

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to save registry: {e}")
        log_operation("registry_save_failed", {
            "message": f"Failed to save registry: {e}",
            "error": str(e)
        }, success=False)
        return False

def create_empty_registry() -> Dict:
    """Create empty registry with proper structure - following flow pattern"""
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

    log_operation("registry_created", {
        "message": "New registry created",
        "version": registry["version"]
    })

    return registry

def validate_registry_structure(registry: Dict) -> bool:
    """Validate registry has proper structure"""
    required_keys = ["commands", "modules", "last_updated", "version"]
    return all(key in registry for key in required_keys)

def get_default_value(key: str) -> Any:
    """Get default value for missing registry keys"""
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
    """Check if module should be ignored in registry"""
    return module_name in IGNORED_MODULES

# =============================================
# REACTIVE REGISTRY FUNCTIONS (AIPass Pattern)
# =============================================

def mark_dirty(reason: str = "command_change"):
    """Mark registry as dirty - needs rebuild"""
    try:
        registry = load_registry()
        registry["dirty"] = True
        registry["last_change"] = datetime.now(timezone.utc).isoformat()
        registry["change_reason"] = reason

        save_registry(registry)
        log_operation_local("registry_marked_dirty", True, f"Registry marked dirty: {reason}")
        logger.info(f"[{MODULE_NAME}] Registry marked dirty: {reason}")

    except Exception as e:
        log_operation_local("mark_dirty_failed", False, f"Failed to mark registry dirty: {e}", str(e))
        logger.error(f"[{MODULE_NAME}] Failed to mark registry dirty: {e}")

def mark_clean():
    """Mark registry as clean - cache is valid"""
    try:
        registry = load_registry()
        registry["dirty"] = False
        registry["last_clean"] = datetime.now(timezone.utc).isoformat()

        save_registry(registry)
        log_operation_local("registry_marked_clean", True, "Registry marked clean")
        logger.info(f"[{MODULE_NAME}] Registry marked clean")

    except Exception as e:
        log_operation_local("mark_clean_failed", False, f"Failed to mark registry clean: {e}", str(e))
        logger.error(f"[{MODULE_NAME}] Failed to mark registry clean: {e}")

def get_cached_commands() -> Optional[Dict]:
    """Get cached commands if registry is clean, None if dirty"""
    try:
        registry = load_registry()

        if registry.get("dirty", True):
            log_operation_local("cache_miss", True, "Registry is dirty, cache invalid")
            return None

        log_operation_local("cache_hit", True, f"Cache valid: {len(registry.get('commands', {}))} commands")
        return registry.get("commands", {})

    except Exception as e:
        log_operation_local("cache_check_failed", False, f"Failed to check cache: {e}", str(e))
        logger.error(f"[{MODULE_NAME}] Failed to check cache: {e}")
        return None

def register_command_location(location_path: str):
    """Add new command location to registry scan locations"""
    try:
        registry = load_registry()

        # Ensure scan_locations exists
        if "scan_locations" not in registry:
            registry["scan_locations"] = []

        # Add location if not already present
        if location_path not in registry["scan_locations"]:
            registry["scan_locations"].append(location_path)
            mark_dirty(f"new_location: {location_path}")
            log_operation_local("location_registered", True, f"New location registered: {location_path}")
            logger.info(f"[{MODULE_NAME}] New location registered: {location_path}")
        else:
            log_operation_local("location_exists", True, f"Location already registered: {location_path}")

    except Exception as e:
        log_operation_local("register_location_failed", False, f"Failed to register location: {e}", str(e))
        logger.error(f"[{MODULE_NAME}] Failed to register location: {e}")

def update_registry_on_change(command_file_path: str):
    """Update registry when command files change"""
    try:
        registry = load_registry()

        # Track the change in source_files
        if "source_files" not in registry:
            registry["source_files"] = {}

        file_name = Path(command_file_path).name
        registry["source_files"][file_name] = {
            "last_modified": datetime.now(timezone.utc).isoformat(),
            "full_path": command_file_path,
            "discovered": "manual"
        }

        mark_dirty(f"file_change: {file_name}")
        log_operation_local("file_change_tracked", True, f"Command file change tracked: {file_name}")

    except Exception as e:
        log_operation_local("track_change_failed", False, f"Failed to track change: {e}", str(e))
        logger.error(f"[{MODULE_NAME}] Failed to track change: {e}")

def register_module_commands(module_name: str, commands: Dict) -> bool:
    """Register commands for a module - following flow numbered pattern"""
    try:
        # Check if module should be ignored
        if should_ignore_module(module_name):
            logger.info(f"[{MODULE_NAME}] Ignoring module: {module_name}")
            return True

        registry = load_registry()

        # Register module
        registry["modules"][module_name] = {
            "registered": datetime.now(timezone.utc).isoformat(),
            "command_count": len(commands),
            "enabled": True,
            "commands": list(commands.keys())
        }

        # Register each command
        for cmd_name, cmd_data in commands.items():
            command_id = f"{module_name}_{cmd_name}"
            registry["commands"][command_id] = {
                "module": module_name,
                "command": cmd_name,
                "path": cmd_data.get("path", ""),
                "args": cmd_data.get("args", []),
                "description": cmd_data.get("description", ""),
                "registered": datetime.now(timezone.utc).isoformat(),
                "enabled": True
            }

        # Update statistics
        registry["statistics"]["total_commands"] = len(registry["commands"])
        registry["statistics"]["total_modules"] = len(registry["modules"])

        # Save registry
        if save_registry(registry):
            log_operation("module_registered", {
                "message": f"Module {module_name} registered with {len(commands)} commands",
                "module": module_name,
                "command_count": len(commands)
            })
            return True

        return False

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to register module {module_name}: {e}")
        log_operation("module_registration_failed", {
            "message": f"Failed to register module {module_name}: {e}",
            "module": module_name,
            "error": str(e)
        }, success=False)
        return False

def get_command(command_path: str) -> Optional[Dict]:
    """Get command by path (e.g., 'flow_create', 'backup_snapshot')"""
    registry = load_registry()
    return registry["commands"].get(command_path)

def get_module_commands(module_name: str) -> Dict:
    """Get all commands for a module"""
    registry = load_registry()
    module_commands = {}

    for cmd_id, cmd_data in registry["commands"].items():
        if cmd_data.get("module") == module_name:
            module_commands[cmd_data["command"]] = cmd_data

    return module_commands

def heal_registry() -> bool:
    """Auto-heal registry by checking for orphaned entries"""
    try:
        registry = load_registry()
        healed = False

        # Remove commands for non-existent modules
        valid_commands = {}
        for cmd_id, cmd_data in registry["commands"].items():
            module_name = cmd_data.get("module")
            if module_name in registry["modules"]:
                valid_commands[cmd_id] = cmd_data
            else:
                logger.warning(f"[{MODULE_NAME}] Removing orphaned command: {cmd_id}")
                healed = True

        if healed:
            registry["commands"] = valid_commands
            registry["statistics"]["auto_healing_count"] += 1
            save_registry(registry)

            log_operation("registry_healed", {
                "message": "Registry auto-healed, orphaned commands removed",
                "commands_removed": len(registry["commands"]) - len(valid_commands)
            })

        return healed

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Registry healing failed: {e}")
        return False

# =============================================
# CLI/EXECUTION
# =============================================

def main():
    """Main registry management function"""
    try:
        logger.info(f"[{MODULE_NAME}] Registry manager starting")

        # Load and heal registry
        registry = load_registry()
        healed = heal_registry()

        # Show status
        stats = registry.get("statistics", {})
        logger.info(f"[{MODULE_NAME}] Registry status:")
        logger.info(f"  - Commands: {stats.get('total_commands', 0)}")
        logger.info(f"  - Modules: {stats.get('total_modules', 0)}")
        logger.info(f"  - Auto-healed: {healed}")

        return registry

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Registry manager failed: {e}")
        raise

if __name__ == "__main__":
    registry = main()
    print(f"✅ Registry loaded: {len(registry['commands'])} commands from {len(registry['modules'])} modules")