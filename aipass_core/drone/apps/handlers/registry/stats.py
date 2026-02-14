#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: stats.py - Registry Statistics
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/registry
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): PILOT MIGRATION - Extracted from drone_registry.py
# =============================================

"""
Registry Statistics Handler

Provides statistics and metrics about the drone command registry.
Tracks command counts, module counts, and registry health metrics.

Features:
- Get registry statistics
- Get module statistics
- Get command count
- Get module count

Usage:
    from drone.apps.handlers.registry.stats import get_registry_statistics

    stats = get_registry_statistics()
    print(f"Total commands: {stats['total_commands']}")
    print(f"Total modules: {stats['total_modules']}")
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

from typing import Dict

# Same-package imports allowed
from .ops import load_registry

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "registry_stats"

# =============================================
# STATISTICS FUNCTIONS
# =============================================

def get_registry_statistics() -> Dict:
    """Get overall registry statistics

    Returns:
        Dict with registry statistics

    Example:
        >>> stats = get_registry_statistics()
        >>> print(f"Commands: {stats['total_commands']}")
        >>> print(f"Modules: {stats['total_modules']}")
    """
    try:
        registry = load_registry()
        return registry.get("statistics", {
            "total_commands": len(registry.get("commands", {})),
            "total_modules": len(registry.get("modules", {})),
            "last_discovery": None,
            "auto_healing_count": 0
        })
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get registry statistics: {e}")
        return {
            "total_commands": 0,
            "total_modules": 0,
            "last_discovery": None,
            "auto_healing_count": 0
        }

def get_command_count() -> int:
    """Get total number of registered commands

    Returns:
        Number of commands

    Example:
        >>> count = get_command_count()
        >>> print(f"Total commands: {count}")
    """
    try:
        registry = load_registry()
        return len(registry.get("commands", {}))
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get command count: {e}")
        return 0

def get_module_count() -> int:
    """Get total number of registered modules

    Returns:
        Number of modules

    Example:
        >>> count = get_module_count()
        >>> print(f"Total modules: {count}")
    """
    try:
        registry = load_registry()
        return len(registry.get("modules", {}))
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get module count: {e}")
        return 0

def get_module_stats(module_name: str) -> Dict:
    """Get statistics for a specific module

    Args:
        module_name: Name of module

    Returns:
        Dict with module statistics

    Example:
        >>> stats = get_module_stats("flow")
        >>> print(f"Command count: {stats['command_count']}")
    """
    try:
        registry = load_registry()
        module_data = registry.get("modules", {}).get(module_name, {})
        return {
            "command_count": module_data.get("command_count", 0),
            "enabled": module_data.get("enabled", False),
            "registered": module_data.get("registered", None),
            "commands": module_data.get("commands", [])
        }
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get module stats for {module_name}: {e}")
        return {
            "command_count": 0,
            "enabled": False,
            "registered": None,
            "commands": []
        }
