#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: cache.py - Registry Reactive Caching
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/registry
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): PILOT MIGRATION - Standalone handler from drone_registry.py
#   - v1.0.0 (2025-11-07): Initial extraction with dependency injection
# =============================================

"""
Registry Reactive Caching Handler

Manages registry dirty/clean state for reactive cache invalidation.
Follows AIPass reactive pattern: mark dirty on change, check before use.

Features:
- Mark registry dirty (cache invalid)
- Mark registry clean (cache valid)
- Get cached commands (None if dirty)
- Register command locations
- Track file changes

Usage:
    from drone.apps.handlers.registry.cache import mark_dirty, get_cached_commands

    mark_dirty("new_command_added")
    commands = get_cached_commands()
    if commands is None:
        # Rebuild cache
        pass
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

from datetime import datetime, timezone
from typing import Dict, Optional

console = Console()

# Same-package imports allowed
from .ops import load_registry, save_registry, log_operation_local

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "registry_cache"

# =============================================
# REACTIVE CACHE FUNCTIONS
# =============================================

def mark_dirty(reason: str = "command_change"):
    """Mark registry as dirty - needs rebuild

    Args:
        reason: Reason for marking dirty

    Example:
        >>> mark_dirty("new_command_added")
        >>> mark_dirty("command_file_modified")
    """
    try:
        registry = load_registry()
        registry["dirty"] = True
        registry["last_change"] = datetime.now(timezone.utc).isoformat()
        registry["change_reason"] = reason

        save_registry(registry)
        log_operation_local("registry_marked_dirty", True, f"Registry marked dirty: {reason}")
        logger.info(f"[{MODULE_NAME}] Registry marked dirty: {reason}")

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to mark registry dirty: {e}")

def mark_clean():
    """Mark registry as clean - cache is valid

    Example:
        >>> mark_clean()
    """
    try:
        registry = load_registry()
        registry["dirty"] = False
        registry["last_clean"] = datetime.now(timezone.utc).isoformat()

        save_registry(registry)
        log_operation_local("registry_marked_clean", True, "Registry marked clean")
        logger.info(f"[{MODULE_NAME}] Registry marked clean")

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to mark registry clean: {e}")

def get_cached_commands() -> Optional[Dict]:
    """Get cached commands if registry is clean, None if dirty

    Returns:
        Commands dict if clean, None if dirty or error

    Example:
        >>> commands = get_cached_commands()
        >>> if commands is None:
        ...     print("Cache invalid, need to rebuild")
        ... else:
        ...     print(f"Got {len(commands)} cached commands")
    """
    try:
        registry = load_registry()

        if registry.get("dirty", True):
            log_operation_local("cache_miss", True, "Registry is dirty, cache invalid")
            return None

        log_operation_local("cache_hit", True, f"Cache valid: {len(registry.get('commands', {}))} commands")
        return registry.get("commands", {})

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to check cache: {e}")
        return None

def register_command_location(location_path: str):
    """Add new command location to registry scan locations

    Args:
        location_path: Path to command location

    Example:
        >>> register_command_location("/home/aipass/aipass_core/drone/commands")
    """
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
        logger.error(f"[{MODULE_NAME}] Failed to register location: {e}")

def update_registry_on_change(command_file_path: str):
    """Update registry when command files change

    Args:
        command_file_path: Path to changed command file

    Example:
        >>> update_registry_on_change("/path/to/drone_commands.json")
    """
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
        logger.error(f"[{MODULE_NAME}] Failed to track change: {e}")
