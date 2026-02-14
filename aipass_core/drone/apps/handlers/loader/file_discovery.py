#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: file_discovery.py - Command File Discovery
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/loader
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): MIGRATION - Standalone handler from drone_loader.py
# =============================================

"""
Command File Discovery Handler

Discovers command JSON files in the Drone system from multiple sources.

Features:
- Recursive directory scanning for command files
- Registry-based module command discovery
- Path validation and filtering
- Auto-detection of command sources

Usage:
    from drone.apps.handlers.loader.file_discovery import discover_command_files

    files = discover_command_files()
    for file_path in files:
        print(file_path)
"""

# =============================================
# IMPORTS
# =============================================

import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

import json
from typing import List

from prax.apps.modules.logger import system_logger as logger

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "loader_file_discovery"
ECOSYSTEM_ROOT = Path.home()
DRONE_JSON_DIR = AIPASS_ROOT / "drone" / "drone_json"
COMMANDS_DIR = AIPASS_ROOT / "drone" / "commands"

# =============================================
# FUNCTIONS
# =============================================

def discover_command_files() -> List[Path]:
    """Discover all command JSON files from multiple sources

    Searches:
    1. commands/ directory and subdirectories
    2. Registry for module-specific command files

    Returns:
        List of Path objects for discovered JSON files

    Example:
        >>> files = discover_command_files()
        >>> print(len(files))
        5
        >>> print(files[0].name)
        core_commands.json
    """
    command_files = []

    try:
        # Search commands directory structure
        if COMMANDS_DIR.exists():
            # Recursively find all JSON files
            for json_file in COMMANDS_DIR.rglob("*.json"):
                command_files.append(json_file)
                logger.info(f"[{MODULE_NAME}] Found command file: {json_file.name}")

        # Check registry for module-specific command files
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
                        logger.info(f"[{MODULE_NAME}] Found module command file: {module_name}.json")

            except Exception as e:
                logger.warning(f"[{MODULE_NAME}] Could not check registry for command files: {e}")

        logger.info(f"[{MODULE_NAME}] Discovery complete: {len(command_files)} command files")
        return command_files

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error discovering command files: {e}")
        return []


def scan_commands_directory() -> List[Path]:
    """Scan commands directory for JSON files

    Returns:
        List of Path objects for JSON files in commands/

    Example:
        >>> files = scan_commands_directory()
        >>> all(f.suffix == '.json' for f in files)
        True
    """
    try:
        if not COMMANDS_DIR.exists():
            logger.warning(f"[{MODULE_NAME}] Commands directory not found: {COMMANDS_DIR}")
            return []

        json_files = list(COMMANDS_DIR.rglob("*.json"))
        logger.info(f"[{MODULE_NAME}] Found {len(json_files)} JSON files in commands/")
        return json_files

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error scanning commands directory: {e}")
        return []


def scan_registry_sources() -> List[Path]:
    """Scan registry for module-specific command files

    Returns:
        List of Path objects for module command files

    Example:
        >>> files = scan_registry_sources()
        >>> all('modules' in str(f) for f in files)
        True
    """
    module_files = []

    try:
        registry_file = DRONE_JSON_DIR / "drone_registry.json"
        if not registry_file.exists():
            logger.info(f"[{MODULE_NAME}] No registry file found")
            return []

        with open(registry_file, 'r', encoding='utf-8') as f:
            registry = json.load(f)

        # Find module command files
        for module_name in registry.get("modules", {}):
            module_file = COMMANDS_DIR / "modules" / f"{module_name}.json"
            if module_file.exists():
                module_files.append(module_file)
                logger.info(f"[{MODULE_NAME}] Found module file: {module_name}.json")

        return module_files

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error scanning registry sources: {e}")
        return []
