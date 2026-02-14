#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: drone_loader.py - Command Loading System
# Date: 2025-09-22
# Version: 1.0.0
# Category: drone
#
# CHANGELOG:
#   - v1.0.0 (2025-09-22): Initial implementation with dynamic command loading
# =============================================

"""
Drone Command Loading System

Loads commands dynamically from JSON files and builds command tree.
Replaces hardcoded COMMANDS dictionary with registry-based loading.

Features:
- Load commands from JSON files
- Parse nested command structures
- Validate command paths
- Build command tree dynamically
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
from typing import Dict, List, Optional, Any, Union

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "drone_loader"
ECOSYSTEM_ROOT = Path.home()  # Scan from /home/aipass/ (not just aipass_core)
DRONE_JSON_DIR = AIPASS_ROOT / "drone" / "drone_json"
COMMANDS_DIR = AIPASS_ROOT / "drone" / "commands"

# 3-File JSON Pattern
CONFIG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_log.json"

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
            "validation_enabled": True,
            "command_tree_caching": True,
            "max_source_files": 50,
            "path_validation_enabled": True,
            "auto_reload_enabled": False,
            "supported_formats": ["json"]
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
            "loader_active": True,
            "tree_building": False,
            "cache_valid": True
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
    """Log loader operations to individual module log file"""
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
                logs = json.load(f)
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

def log_operation(operation: str, details: Dict[str, Any], success: bool = True):
    """Log operation to drone system"""
    try:
        from drone_registry import log_operation as registry_log
        registry_log(operation, details, success)
    except ImportError:
        # Fallback logging
        level = "INFO" if success else "ERROR"
        logger.info(f"[{MODULE_NAME}] {level}: {operation} - {details}")

def validate_command_path(path: str, working_dir: Optional[str] = None) -> bool:
    """Validate that command path exists"""
    try:
        if working_dir:
            full_path = ECOSYSTEM_ROOT / working_dir / path
        else:
            full_path = ECOSYSTEM_ROOT / path

        # Handle direct commands like 'python3'
        if path in ['python3', 'python', 'node', 'npm']:
            return True

        # Check if file exists
        if full_path.exists():
            return True

        # Check if it's in PATH for system commands
        import shutil
        if shutil.which(path):
            return True

        return False

    except Exception as e:
        logger.warning(f"[{MODULE_NAME}] Error validating path {path}: {e}")
        return False

def resolve_command_path(path: str, working_dir: Optional[str] = None) -> str:
    """Resolve command path to absolute path"""
    try:
        # Handle direct commands
        if path in ['python3', 'python', 'node', 'npm']:
            return path

        # Handle relative paths
        if working_dir:
            return str(ECOSYSTEM_ROOT / working_dir / path)
        else:
            return str(ECOSYSTEM_ROOT / path)

    except Exception as e:
        logger.warning(f"[{MODULE_NAME}] Error resolving path {path}: {e}")
        return path

# =============================================
# MAIN FUNCTIONS
# =============================================

def load_json_commands(json_file_path: Path) -> Dict:
    """Load commands from a JSON file"""
    try:
        if not json_file_path.exists():
            logger.warning(f"[{MODULE_NAME}] JSON file not found: {json_file_path}")
            return {}

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            logger.warning(f"[{MODULE_NAME}] Invalid JSON structure in {json_file_path}")
            return {}

        logger.info(f"[{MODULE_NAME}] Loaded commands from {json_file_path.name}")
        return data

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to load {json_file_path}: {e}")
        return {}

def discover_command_files() -> List[Path]:
    """Discover all command JSON files"""
    command_files = []

    try:
        # Check existing commands directory structure
        if COMMANDS_DIR.exists():
            # Look for JSON files in commands/ and subdirectories
            for json_file in COMMANDS_DIR.rglob("*.json"):
                command_files.append(json_file)

        # Also check for module-specific command files in the registry
        registry_file = DRONE_JSON_DIR / "drone_registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)

                # Look for modules that might have their own command files
                for module_name in registry.get("modules", {}):
                    module_commands_file = COMMANDS_DIR / "modules" / f"{module_name}.json"
                    if module_commands_file.exists() and module_commands_file not in command_files:
                        command_files.append(module_commands_file)

            except Exception as e:
                logger.warning(f"[{MODULE_NAME}] Could not check registry for command files: {e}")

        logger.info(f"[{MODULE_NAME}] Discovered {len(command_files)} command files")
        return command_files

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error discovering command files: {e}")
        return []

def flatten_nested_commands(commands: Dict, parent_key: str = "") -> Dict:
    """Flatten nested command structure into flat command dictionary"""
    flat_commands = {}

    try:
        for key, value in commands.items():
            current_key = f"{parent_key}_{key}" if parent_key else key

            if isinstance(value, dict):
                if "path" in value or "command" in value:
                    # This is a command definition
                    flat_commands[current_key] = value
                else:
                    # This is nested commands, recurse
                    nested = flatten_nested_commands(value, current_key)
                    flat_commands.update(nested)

        return flat_commands

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error flattening commands: {e}")
        return {}

def build_command_tree() -> Dict:
    """Build complete command tree from all sources"""
    try:
        # Load config and initialize JSON files
        config = load_config()
        loader_config = config.get("config", {})

        # Ensure loader_config is a dict (fix for list indices error)
        if not isinstance(loader_config, dict):
            loader_config = {}

        # Check if loading is enabled
        if not loader_config.get("enabled", True):
            log_operation_local("loading_skipped", True, "Loading disabled in config")
            return {}

        log_operation_local("tree_building_started", True, "Building command tree")
        logger.info(f"[{MODULE_NAME}] Building command tree...")

        # Start with empty command tree
        command_tree = {}

        # Discover and load all command files
        command_files = discover_command_files()

        for json_file in command_files:
            file_commands = load_json_commands(json_file)

            # Extract commands from different JSON structures
            if "commands" in file_commands:
                # Format: {"commands": {...}}
                commands_data = file_commands["commands"]
            elif "name" in file_commands and "commands" in file_commands:
                # Format: {"name": "module", "commands": {...}}
                commands_data = file_commands["commands"]
            else:
                # Assume entire file is commands
                commands_data = file_commands

            # Use commands directly from JSON (no hidden flattening)
            # Validate and add commands
            for cmd_name, cmd_data in commands_data.items():
                if validate_command_data(cmd_data):
                    command_tree[cmd_name] = cmd_data
                    logger.info(f"[{MODULE_NAME}] Added command: {cmd_name}")
                else:
                    logger.warning(f"[{MODULE_NAME}] Invalid command data for: {cmd_name}")

        # Store commands in registry for caching
        from drone_registry import load_registry, save_registry
        registry = load_registry()
        registry["commands"] = command_tree
        registry["source_files"] = {}

        # Track source files for auto-discovery
        for json_file in command_files:
            file_name = Path(json_file).name
            # Store the FILE'S actual modification time, not current time!
            file_mtime = os.path.getmtime(json_file)
            file_modified = datetime.fromtimestamp(file_mtime, timezone.utc)
            registry["source_files"][file_name] = {
                "last_modified": file_modified.isoformat(),
                "full_path": str(json_file),
                "discovered": "auto"
            }

        # Update registry statistics
        registry["statistics"]["total_commands"] = len(command_tree)
        registry["statistics"]["total_locations"] = len(registry.get("scan_locations", []))
        save_registry(registry)

        # Update statistics and data file
        stats = {
            "total_commands_loaded": len(command_tree),
            "source_files_processed": len(command_files),
            "last_build": datetime.now(timezone.utc).isoformat(),
            "validation_enabled": loader_config.get("validation_enabled", True),
            "build_duration_ms": 0  # Could add timing if needed
        }

        update_data_file(stats)
        log_operation_local("tree_building_completed", True, f"Built command tree with {len(command_tree)} commands")

        # Also log to registry system (keep existing)
        log_operation("command_tree_built", {
            "message": f"Command tree built with {len(command_tree)} commands",
            "command_count": len(command_tree),
            "source_files": len(command_files)
        })

        logger.info(f"[{MODULE_NAME}] Command tree built: {len(command_tree)} commands")
        return command_tree

    except Exception as e:
        log_operation_local("tree_building_failed", False, f"Failed to build command tree: {e}", str(e))
        logger.error(f"[{MODULE_NAME}] Failed to build command tree: {e}")
        log_operation("command_tree_build_failed", {
            "message": f"Failed to build command tree: {e}",
            "error": str(e)
        }, success=False)
        return {}

def validate_command_data(cmd_data: Dict) -> bool:
    """Validate command data structure"""
    try:
        # Must have path or be a system command
        if "path" not in cmd_data:
            return False

        # Validate path exists (if not a system command)
        path = cmd_data["path"]
        working_dir = cmd_data.get("cwd")

        if not validate_command_path(path, working_dir):
            logger.warning(f"[{MODULE_NAME}] Command path not found: {path}")
            return False

        return True

    except Exception as e:
        logger.warning(f"[{MODULE_NAME}] Error validating command data: {e}")
        return False

def get_command_tree() -> Dict:
    """Get current command tree (cached or build new) - AIPass reactive pattern"""
    try:
        # Import registry functions
        from drone_registry import get_cached_commands, mark_clean

        # Check registry cache first
        cached_commands = get_cached_commands()
        if cached_commands is not None:
            log_operation_local("cache_hit", True, f"Using cached commands: {len(cached_commands)}")
            logger.info(f"[{MODULE_NAME}] Using cached commands: {len(cached_commands)}")
            return cached_commands

        # Cache miss - need to rebuild
        log_operation_local("cache_miss", True, "Registry dirty, rebuilding commands")
        logger.info(f"[{MODULE_NAME}] Registry dirty - rebuilding command tree")

        command_tree = build_command_tree()

        # Mark registry clean after successful rebuild
        mark_clean()
        log_operation_local("rebuild_complete", True, f"Command tree rebuilt: {len(command_tree)} commands")
        logger.info(f"[{MODULE_NAME}] Command tree rebuilt and registry marked clean")

        return command_tree

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get command tree: {e}")
        log_operation_local("get_tree_failed", False, f"Failed to get command tree: {e}", str(e))
        return {}

def resolve_command(command_path: str) -> Optional[Dict]:
    """Resolve a command by path (e.g., 'run_seed', 'backup_snapshot')"""
    try:
        command_tree = get_command_tree()
        return command_tree.get(command_path)

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to resolve command {command_path}: {e}")
        return None

def get_available_commands() -> List[str]:
    """Get list of all available commands"""
    try:
        command_tree = get_command_tree()
        return list(command_tree.keys())

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get available commands: {e}")
        return []

# =============================================
# CLI/EXECUTION
# =============================================

def main():
    """Main loader function for testing"""
    try:
        logger.info(f"[{MODULE_NAME}] Testing command loader...")

        # Build command tree
        command_tree = build_command_tree()

        # Show results
        logger.info(f"[{MODULE_NAME}] Command tree test complete:")
        logger.info(f"  - Total commands: {len(command_tree)}")

        # Show some commands
        for i, (cmd_name, cmd_data) in enumerate(list(command_tree.items())[:5]):
            logger.info(f"  - {cmd_name}: {cmd_data.get('path', 'No path')}")

        return command_tree

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Loader test failed: {e}")
        raise

if __name__ == "__main__":
    result = main()
    print(f"✅ Command loader test: {len(result)} commands loaded")
    for cmd_name in list(result.keys())[:10]:
        print(f"  - {cmd_name}")