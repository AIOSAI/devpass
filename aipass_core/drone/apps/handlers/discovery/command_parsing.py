#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: command_parsing.py - Command Registration Handler
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/discovery
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): BEAST MIGRATION - Extracted from drone_discovery.py (2,289 lines)
#   - v1.0.0 (2025-10-16): Original implementation in monolithic file
# =============================================

"""
Command Registration Handler

Handles registration of discovered commands with global ID assignment.
Creates system-specific registries and manages command metadata.

Features:
- Global ID allocation and increment
- Module registration with auto-detection
- Command metadata tracking
- System directory creation
- Registry file management

Usage:
    from drone.apps.handlers.discovery.command_parsing import register_module

    result = register_module("@flow")
    print(f"Registered {result['commands_registered']} commands")
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Same-package imports allowed
from .module_scanning import scan_module

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "command_parsing"
DRONE_ROOT = AIPASS_ROOT / "drone"
ECOSYSTEM_ROOT = Path.home()
DRONE_JSON_DIR = DRONE_ROOT / "drone_json"

# =============================================
# GLOBAL ID MANAGEMENT
# =============================================

def get_next_global_id() -> int:
    """
    Get next available global ID from registry

    Returns:
        Next available ID (integer)

    Example:
        >>> next_id = get_next_global_id()
        >>> print(next_id)
        42
    """
    from drone.apps.handlers.registry import load_registry

    registry = load_registry()
    current_id = registry.get("global_id_counter", 0)
    return current_id + 1

def increment_global_id():
    """
    Increment global ID counter in registry

    Side Effects:
        Updates drone_registry.json with incremented counter

    Example:
        >>> increment_global_id()
        # ID counter increased by 1
    """
    from drone.apps.handlers.registry import load_registry

    registry = load_registry()
    registry["global_id_counter"] = registry.get("global_id_counter", 0) + 1

    # Save updated registry
    registry_file = DRONE_JSON_DIR / "drone_registry.json"
    try:
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error updating global ID counter: {e}")

# =============================================
# REGISTRY FILE MANAGEMENT
# =============================================

def load_system_registry(system_name: str) -> dict:
    """
    Load registry for a specific system

    Args:
        system_name: System name to load

    Returns:
        Registry dict (empty if not found)

    Example:
        >>> registry = load_system_registry("flow")
        >>> print(len(registry))
        12
    """
    registry_file = DRONE_ROOT / "commands" / system_name / "registry.json"
    if not registry_file.exists():
        return {}

    try:
        with open(registry_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error loading registry for {system_name}: {e}")
        return {}

def save_system_registry(system_name: str, registry: dict):
    """
    Save registry for a specific system

    Args:
        system_name: System name
        registry: Registry dict to save

    Side Effects:
        Writes registry.json file

    Example:
        >>> save_system_registry("flow", registry_data)
    """
    registry_file = DRONE_ROOT / "commands" / system_name / "registry.json"
    try:
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error saving registry for {system_name}: {e}")

# =============================================
# MODULE REGISTRATION
# =============================================

def register_module(module_path: str | Path, system_name: str | None = None) -> dict:
    """
    Register a module and assign global IDs to its commands

    Args:
        module_path: Path to Python module or @ symbol path
        system_name: Optional system name (defaults to module name)

    Returns:
        {
            'success': bool,
            'system_name': str,
            'commands_registered': int,
            'registry_path': str,
            'commands': [{'id': int, 'name': str, 'help': str}, ...],
            'error': str | None
        }

    Example:
        >>> result = register_module("@flow")
        >>> print(result['commands_registered'])
        12
    """
    result = {
        'success': False,
        'system_name': '',
        'commands_registered': 0,
        'registry_path': '',
        'commands': [],
        'error': None
    }

    try:
        # First, scan the module (this resolves @ symbols)
        scan_result = scan_module(module_path)

        if not scan_result['success']:
            result['error'] = scan_result.get('error', 'Scan failed')
            return result

        if not scan_result['commands']:
            # Check if module is non-compliant CLI module
            module_type = scan_result.get('module_type')
            resolved_path = Path(scan_result['module_path'])

            if module_type == 'cli':
                # Non-compliant CLI module - suggest upgrade
                result['error'] = 'No commands detected to register\n\n'
                result['error'] += '💡 This module appears to be non-compliant (missing --help with Commands: line)\n\n'
                result['error'] += '   Upgrade to compliance:\n'

                # Show path relative to ecosystem root if possible
                try:
                    rel_path = resolved_path.relative_to(ECOSYSTEM_ROOT)
                    result['error'] += f'   drone comply @{rel_path}'
                except ValueError:
                    result['error'] += f'   drone comply {resolved_path}'
            else:
                result['error'] = 'No commands detected to register'

            return result

        # Use resolved path from scan_result
        resolved_path = Path(scan_result['module_path'])

        # Determine system name
        if not system_name:
            if resolved_path.is_file():
                system_name = resolved_path.stem
            else:
                system_name = resolved_path.name

        result['system_name'] = system_name

        # Create registry directory for this system
        commands_dir = DRONE_ROOT / "commands"
        system_dir = commands_dir / system_name
        system_dir.mkdir(parents=True, exist_ok=True)

        registry_file = system_dir / "registry.json"
        result['registry_path'] = str(registry_file)

        # Load existing registry if present
        existing_registry = load_system_registry(system_name)

        # Build registry directly from modules_scanned to preserve all module:command combinations
        registry = {}

        if scan_result.get('is_directory') and scan_result.get('modules_scanned'):
            # Directory scan - process each module's commands
            for module_info in scan_result['modules_scanned']:
                module_path_for_cmd = module_info['path']
                module_stem = Path(module_path_for_cmd).stem

                for cmd_name in module_info['commands']:
                    # Create registry key: module:command
                    registry_key = f"{module_stem}:{cmd_name}"

                    # Check if already registered
                    if registry_key in existing_registry:
                        # Keep existing ID
                        existing_id = existing_registry[registry_key]['id']
                        already_reg = True
                    else:
                        # Assign new ID
                        existing_id = get_next_global_id()
                        increment_global_id()
                        already_reg = False

                    registry[registry_key] = {
                        'id': existing_id,
                        'command_name': cmd_name,
                        'module_name': module_stem,
                        'help': '',
                        'module_path': module_path_for_cmd,
                        'registered_date': datetime.now(timezone.utc).isoformat(),
                        'active': False
                    }
        else:
            # Single file scan - no module prefix needed
            for cmd_name in scan_result['commands']:
                module_stem = Path(resolved_path).stem
                registry_key = f"{module_stem}:{cmd_name}"

                # Check if already registered
                if registry_key in existing_registry:
                    existing_id = existing_registry[registry_key]['id']
                    already_reg = True
                else:
                    existing_id = get_next_global_id()
                    increment_global_id()
                    already_reg = False

                registry[registry_key] = {
                    'id': existing_id,
                    'command_name': cmd_name,
                    'module_name': module_stem,
                    'help': '',
                    'module_path': str(resolved_path),
                    'registered_date': datetime.now(timezone.utc).isoformat(),
                    'active': False
                }

        # Rebuild registered_commands from final registry
        final_registered_commands = []
        for registry_key, cmd_data in registry.items():
            # Check if it was already registered (check by registry_key)
            already_reg = registry_key in existing_registry
            final_registered_commands.append({
                'id': cmd_data['id'],
                'name': registry_key,  # Show as "module:command"
                'command_name': cmd_data['command_name'],  # Actual command
                'module_name': cmd_data['module_name'],  # Module name
                'help': cmd_data['help'],
                'already_registered': already_reg
            })

        # Save registry
        save_system_registry(system_name, registry)

        result['success'] = True
        result['commands'] = final_registered_commands
        result['commands_registered'] = len([c for c in final_registered_commands if not c.get('already_registered', False)])

        logger.info(f"[{MODULE_NAME}] Registered {result['commands_registered']} new commands for {system_name}")

    except Exception as e:
        result['error'] = f"Registration failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Registration error: {e}")

    return result
