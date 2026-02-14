#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: command_builder.py - Command Tree Building
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/loader
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): MIGRATION - Standalone handler from drone_loader.py
# =============================================

"""
Command Tree Building Handler

Utilities for building and flattening command trees.

Features:
- Nested command flattening
- Command tree merging
- Composite key generation
- Hierarchical structure handling

Usage:
    from drone.apps.handlers.loader.command_builder import flatten_nested_commands

    nested = {"tools": {"seed": {"path": "seed.py"}}}
    flat = flatten_nested_commands(nested)
    # Result: {"tools_seed": {"path": "seed.py"}}
"""

# =============================================
# IMPORTS
# =============================================

import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from typing import Dict, Any

from prax.apps.modules.logger import system_logger as logger

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "loader_command_builder"

# =============================================
# FUNCTIONS
# =============================================

def flatten_nested_commands(commands: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
    """Flatten nested command structure into flat command dictionary

    Recursively processes nested dictionaries and builds composite keys.

    Args:
        commands: Nested command dictionary
        parent_key: Parent key for composite naming

    Returns:
        Flattened command dictionary

    Example:
        >>> nested = {
        ...     "tools": {
        ...         "seed": {"path": "seed.py"},
        ...         "drone": {"path": "drone.py"}
        ...     }
        ... }
        >>> flat = flatten_nested_commands(nested)
        >>> "tools_seed" in flat
        True
        >>> flat["tools_seed"]["path"]
        'seed.py'
    """
    flat_commands = {}

    try:
        for key, value in commands.items():
            current_key = f"{parent_key}_{key}" if parent_key else key

            if isinstance(value, dict):
                if "path" in value or "command" in value:
                    # This is a command definition
                    flat_commands[current_key] = value
                    logger.info(f"[{MODULE_NAME}] Added command: {current_key}")
                else:
                    # This is nested commands, recurse
                    nested = flatten_nested_commands(value, current_key)
                    flat_commands.update(nested)

        return flat_commands

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error flattening commands: {e}")
        return {}


def build_flat_command_dict(commands: Dict[str, Any]) -> Dict[str, Any]:
    """Build flat command dictionary from nested structure

    Wrapper around flatten_nested_commands with logging.

    Args:
        commands: Command dictionary (nested or flat)

    Returns:
        Flat command dictionary

    Example:
        >>> cmds = {"test": {"path": "test.py"}}
        >>> flat = build_flat_command_dict(cmds)
        >>> "test" in flat
        True
    """
    try:
        if not commands:
            logger.info(f"[{MODULE_NAME}] No commands to flatten")
            return {}

        flat = flatten_nested_commands(commands)
        logger.info(f"[{MODULE_NAME}] Flattened {len(commands)} inputs to {len(flat)} commands")
        return flat

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error building flat command dict: {e}")
        return {}


def merge_command_sources(sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple command sources into single tree

    Args:
        sources: Dictionary of source_name -> commands

    Returns:
        Merged command dictionary

    Example:
        >>> sources = {
        ...     "core": {"run_seed": {"path": "seed.py"}},
        ...     "tools": {"backup": {"path": "backup.py"}}
        ... }
        >>> merged = merge_command_sources(sources)
        >>> len(merged)
        2
        >>> "run_seed" in merged and "backup" in merged
        True
    """
    merged = {}

    try:
        for source_name, commands in sources.items():
            if not isinstance(commands, dict):
                logger.warning(f"[{MODULE_NAME}] Skipping invalid source: {source_name}")
                continue

            for cmd_name, cmd_data in commands.items():
                if cmd_name in merged:
                    logger.warning(f"[{MODULE_NAME}] Duplicate command '{cmd_name}' from {source_name} (overwriting)")

                merged[cmd_name] = cmd_data

            logger.info(f"[{MODULE_NAME}] Merged {len(commands)} commands from {source_name}")

        logger.info(f"[{MODULE_NAME}] Total commands merged: {len(merged)}")
        return merged

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error merging command sources: {e}")
        return {}
