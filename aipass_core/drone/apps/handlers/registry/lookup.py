#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: lookup.py - Registry Command Lookup
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/registry
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): PILOT MIGRATION - Standalone handler from drone_registry.py
#   - v1.0.0 (2025-11-07): Initial extraction with dependency injection
# =============================================

"""
Registry Command Lookup Handler

Provides lookup operations for commands and modules in the drone registry.
Supports command path lookup, module command queries, and basic search.

Features:
- Get command by path
- Get all commands for a module
- List all commands
- List all modules

Usage:
    from drone.apps.handlers.registry.lookup import get_command, get_module_commands

    cmd = get_command("flow_create")
    if cmd:
        console.print(f"Description: {cmd['description']}")

    flow_commands = get_module_commands("flow")
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
from rich.console import Console

AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

from typing import Dict, Optional

console = Console()

# Same-package imports allowed
from .ops import load_registry

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "registry_lookup"

# =============================================
# LOOKUP FUNCTIONS
# =============================================

def get_command(command_path: str) -> Optional[Dict]:
    """Get command by path (e.g., 'flow_create', 'backup_snapshot')

    Args:
        command_path: Command path/ID

    Returns:
        Command dict or None if not found

    Example:
        >>> cmd = get_command("flow_create")
        >>> if cmd:
        ...     print(cmd["description"])
    """
    try:
        registry = load_registry()
        return registry.get("commands", {}).get(command_path)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get command {command_path}: {e}")
        return None

def get_module_commands(module_name: str) -> Dict:
    """Get all commands for a module

    Args:
        module_name: Name of module

    Returns:
        Dict of commands for the module

    Example:
        >>> commands = get_module_commands("flow")
        >>> for cmd_name, cmd_data in commands.items():
        ...     print(f"{cmd_name}: {cmd_data['description']}")
    """
    try:
        registry = load_registry()
        module_commands = {}

        for cmd_id, cmd_data in registry.get("commands", {}).items():
            if cmd_data.get("module") == module_name:
                module_commands[cmd_data["command"]] = cmd_data

        return module_commands
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get module commands for {module_name}: {e}")
        return {}

def get_all_commands() -> Dict:
    """Get all commands from registry

    Returns:
        Dict of all commands

    Example:
        >>> commands = get_all_commands()
        >>> print(f"Total commands: {len(commands)}")
    """
    try:
        registry = load_registry()
        return registry.get("commands", {})
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get all commands: {e}")
        return {}

def get_all_modules() -> Dict:
    """Get all modules from registry

    Returns:
        Dict of all modules

    Example:
        >>> modules = get_all_modules()
        >>> for module_name, module_data in modules.items():
        ...     print(f"{module_name}: {module_data['command_count']} commands")
    """
    try:
        registry = load_registry()
        return registry.get("modules", {})
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get all modules: {e}")
        return {}
