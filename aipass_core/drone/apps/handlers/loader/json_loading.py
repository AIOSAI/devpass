#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: json_loading.py - JSON Command Loading
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/loader
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): MIGRATION - Standalone handler from drone_loader.py
# =============================================

"""
JSON Command Loading Handler

Loads and parses command definitions from JSON files.

Features:
- JSON file reading and validation
- Multiple JSON structure support
- Command extraction from nested structures
- Error handling and recovery

Usage:
    from drone.apps.handlers.loader.json_loading import load_json_commands

    commands = load_json_commands(Path("/path/to/commands.json"))
    for name, data in commands.items():
        print(f"{name}: {data['path']}")
"""

# =============================================
# IMPORTS
# =============================================

import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

import json
from typing import Dict, Any

from prax.apps.modules.logger import system_logger as logger

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "loader_json_loading"

# =============================================
# FUNCTIONS
# =============================================

def load_json_commands(json_file_path: Path) -> Dict[str, Any]:
    """Load commands from a JSON file

    Supports multiple JSON structures:
    - {"commands": {...}} - Wrapped commands
    - {"name": "module", "commands": {...}} - Module format
    - {...} - Direct command dictionary

    Args:
        json_file_path: Path to JSON file

    Returns:
        Dictionary of command definitions (name -> data)

    Example:
        >>> commands = load_json_commands(Path("commands.json"))
        >>> "run_seed" in commands
        True
        >>> commands["run_seed"]["path"]
        'seed/apps/seed.py'
    """
    try:
        if not json_file_path.exists():
            logger.warning(f"[{MODULE_NAME}] JSON file not found: {json_file_path}")
            return {}

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            logger.warning(f"[{MODULE_NAME}] Invalid JSON structure in {json_file_path}")
            return {}

        # Extract commands from various formats
        commands = extract_commands_from_json(data)

        logger.info(f"[{MODULE_NAME}] Loaded {len(commands)} commands from {json_file_path.name}")
        return commands

    except json.JSONDecodeError as e:
        logger.error(f"[{MODULE_NAME}] JSON parse error in {json_file_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to load {json_file_path}: {e}")
        return {}


def extract_commands_from_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract commands from JSON data structure

    Handles multiple JSON formats:
    - {"commands": {...}}
    - {"name": "module", "commands": {...}}
    - {...} (direct commands)

    Args:
        data: Parsed JSON data

    Returns:
        Command dictionary

    Example:
        >>> data = {"commands": {"test": {"path": "test.py"}}}
        >>> cmds = extract_commands_from_json(data)
        >>> "test" in cmds
        True
    """
    try:
        # Format 1: {"commands": {...}}
        if "commands" in data and isinstance(data["commands"], dict):
            return data["commands"]

        # Format 2: {"name": "module", "commands": {...}}
        if "name" in data and "commands" in data and isinstance(data["commands"], dict):
            return data["commands"]

        # Format 3: Direct command dictionary
        # Check if it looks like a command dict (has command-like keys)
        if isinstance(data, dict):
            # If any value has 'path' or 'command' key, assume it's a command dict
            for value in data.values():
                if isinstance(value, dict) and ("path" in value or "command" in value):
                    return data

        logger.warning(f"[{MODULE_NAME}] Could not extract commands from JSON structure")
        return {}

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error extracting commands: {e}")
        return {}


def parse_command_structure(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and validate command structure

    Ensures command data has required fields and proper structure.

    Args:
        data: Command data dictionary

    Returns:
        Validated command dictionary

    Example:
        >>> cmd_data = {"path": "test.py", "args": []}
        >>> parsed = parse_command_structure(cmd_data)
        >>> "path" in parsed
        True
    """
    try:
        # Validate basic structure
        if not isinstance(data, dict):
            logger.warning(f"[{MODULE_NAME}] Invalid command structure: not a dict")
            return {}

        # Ensure required fields exist
        if "path" not in data and "command" not in data:
            logger.warning(f"[{MODULE_NAME}] Command missing 'path' or 'command' field")
            return {}

        return data

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error parsing command structure: {e}")
        return {}
