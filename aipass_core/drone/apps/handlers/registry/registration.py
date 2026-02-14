#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# FILE: registration.py
# DESCRIPTION: Registry command registration handler. Manages registration of
#              modules and their commands into the drone registry with metadata
#              tracking and statistics updates.
#
# DEPENDENCIES:
#   - drone.apps.handlers.registry.ops (load_registry, save_registry, should_ignore_module, log_operation_local)
#   - prax.apps.modules.logger (system logging)
#   - drone registry JSON file (DRONE.registry.json)
#
# CODE STANDARDS:
#   - Handler independence (minimal cross-handler imports)
#   - No orchestration (handlers don't call modules)
#   - No CLI output (handlers are pure implementation)
#   - Type hints on all functions
#   - Same-package imports allowed for registry handlers
#   - Dependency injection pattern (uses ops.py for registry access)
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): PILOT MIGRATION - Standalone handler from drone_registry.py
#   - v1.0.0 (2025-11-07): Initial extraction with dependency injection
# ==============================================

"""
Registry Command Registration Handler

Manages registration of modules and their commands into the drone registry.
Handles command metadata, module tracking, and statistics updates.

Features:
- Register module commands
- Update module statistics
- Auto-detect caller module (future)
- Ignore filtering

Usage:
    from drone.apps.handlers.registry.registration import register_module_commands

    commands = {
        "scan": {"path": "...", "args": [], "description": "Scan for commands"},
        "load": {"path": "...", "args": [], "description": "Load command"}
    }
    # With explicit module name:
    register_module_commands(commands, "drone")
    # Or with auto-detection:
    register_module_commands(commands)
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import inspect

# Same-package imports allowed
from .ops import load_registry, save_registry, log_operation_local, should_ignore_module

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "registry_registration"

# =============================================
# AUTO-DETECTION FUNCTIONS
# =============================================

def _get_caller_module_name() -> str:
    """
    Auto-detect calling module name from call stack

    Returns:
        Module name (e.g., "registry_service" from registry_service.py)
    """
    try:
        stack = inspect.stack()
        # Skip frames: [0]=this function, [1]=register_module_commands, [2]=actual caller
        if len(stack) > 2:
            caller_frame = stack[2]
            caller_path = Path(caller_frame.filename)
            module_name = caller_path.stem

            # Validate module name
            if module_name and not module_name.startswith('_'):
                return module_name

        # Fallback
        logger.warning("Could not auto-detect module name, using 'unknown'")
        return "unknown"
    except Exception as e:
        logger.error(f"Error detecting caller: {e}")
        return "unknown"

# =============================================
# REGISTRATION FUNCTIONS
# =============================================

def register_module_commands(commands: Dict[str, Any], module_name: Optional[str] = None) -> bool:
    """Register commands for a module

    Auto-detects calling module if module_name not provided.

    Args:
        commands: Dict of commands to register
        module_name: Optional module name (auto-detected if not provided)

    Returns:
        True if registered successfully

    Example:
        >>> commands = {
        ...     "scan": {"path": "/path/to/scan", "args": [], "description": "Scan"},
        ...     "load": {"path": "/path/to/load", "args": ["file"], "description": "Load"}
        ... }
        >>> register_module_commands(commands, "drone")
        True
        >>> # Or with auto-detection:
        >>> register_module_commands(commands)
        True
    """
    # Auto-detect module name if not provided
    if module_name is None:
        module_name = _get_caller_module_name()

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
            log_operation_local("module_registered", True, f"Module {module_name} registered with {len(commands)} commands")
            logger.info(f"[{MODULE_NAME}] Module {module_name} registered with {len(commands)} commands")
            return True

        return False

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to register module {module_name}: {e}")
        return False
