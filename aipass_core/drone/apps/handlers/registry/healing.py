#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: healing.py - Registry Auto-Healing
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/registry
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): PILOT MIGRATION - Standalone handler from drone_registry.py
#   - v1.0.0 (2025-11-07): Initial extraction with dependency injection
# =============================================

"""
Registry Auto-Healing Handler

Automatically heals the drone registry by removing orphaned entries,
fixing invalid data, and maintaining registry health.

Features:
- Remove orphaned commands (commands without modules)
- Track healing count
- Log healing operations
- Report healing results

Usage:
    from drone.apps.handlers.registry.healing import heal_registry

    healed = heal_registry()
    if healed:
        console.print("Registry was healed")
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

console = Console()

# Same-package imports allowed
from .ops import load_registry, save_registry, log_operation_local

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "registry_healing"

# =============================================
# HEALING FUNCTIONS
# =============================================

def heal_registry() -> bool:
    """Auto-heal registry by checking for orphaned entries

    Returns:
        True if registry was healed (changes made), False otherwise

    Example:
        >>> healed = heal_registry()
        >>> if healed:
        ...     print("Registry was healed")
    """
    try:
        registry = load_registry()
        healed = False
        commands_removed = 0

        # Remove commands for non-existent modules
        valid_commands = {}
        for cmd_id, cmd_data in registry.get("commands", {}).items():
            module_name = cmd_data.get("module")
            if module_name in registry.get("modules", {}):
                valid_commands[cmd_id] = cmd_data
            else:
                logger.warning(f"[{MODULE_NAME}] Removing orphaned command: {cmd_id}")
                commands_removed += 1
                healed = True

        if healed:
            registry["commands"] = valid_commands
            if "statistics" not in registry:
                registry["statistics"] = {}
            if "auto_healing_count" not in registry["statistics"]:
                registry["statistics"]["auto_healing_count"] = 0
            registry["statistics"]["auto_healing_count"] += 1

            save_registry(registry)

            log_operation_local("registry_healed", True, f"Registry auto-healed, {commands_removed} orphaned commands removed")
            logger.info(f"[{MODULE_NAME}] Registry auto-healed, {commands_removed} orphaned commands removed")

        return healed

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Registry healing failed: {e}")
        return False
