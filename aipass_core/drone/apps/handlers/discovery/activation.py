#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: activation.py - Command Activation Handler
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/discovery
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): BEAST MIGRATION - Extracted from drone_discovery.py (2,289 lines)
#   - v1.0.0 (2025-10-16): Original implementation in monolithic file
# =============================================

"""
Command Activation Handler

Interactive activation workflow for mapping registered commands to drone command names.
Prevents duplicate activations and manages active.json files.

Features:
- Interactive command selection
- Duplicate prevention (within session and across systems)
- Active state persistence
- Command lookup and validation

Usage:
    from drone.apps.handlers.discovery.activation import activate_commands_interactive

    result = activate_commands_interactive("flow")
    print(f"Activated {result['activated']} commands")
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
from typing import Dict, List, Optional, Any

# CLI for Rich formatting
from cli.apps.modules import console
from rich.panel import Panel

# Same-package imports allowed
from .command_parsing import load_system_registry, save_system_registry

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "activation"
DRONE_ROOT = AIPASS_ROOT / "drone"

# =============================================
# COMMAND LOOKUP
# =============================================

def lookup_activated_command(drone_command: str) -> dict | None:
    """
    Look up an activated drone command and return execution info

    Args:
        drone_command: The drone command to look up (e.g., "test create", "backup snap")

    Returns:
        {
            'module_path': str,
            'command_name': str,
            'system': str,
            'id': int
        } or None if not found

    Example:
        >>> info = lookup_activated_command("test create")
        >>> print(info['module_path'])
        '/home/aipass/flow/flow_plan.py'
    """
    try:
        commands_dir = DRONE_ROOT / "commands"

        if not commands_dir.exists():
            return None

        # Search all active.json files
        for system_dir in commands_dir.iterdir():
            if not system_dir.is_dir():
                continue

            active_file = system_dir / "active.json"
            if not active_file.exists():
                continue

            # Load active commands
            try:
                with open(active_file, 'r', encoding='utf-8') as f:
                    active_data = json.load(f)
            except Exception:
                continue

            # Check if our command is in this system
            if drone_command in active_data:
                cmd_data = active_data[drone_command]
                return {
                    'module_path': cmd_data.get('module_path', ''),
                    'command_name': cmd_data.get('command_name', ''),
                    'system': system_dir.name,
                    'id': cmd_data.get('id', 0)
                }

        return None

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error looking up command: {e}")
        return None

# =============================================
# INTERACTIVE ACTIVATION
# =============================================

def activate_commands_interactive(system_name: str) -> dict:
    """
    Interactive command activation

    Displays all registered commands for a system and prompts user to activate them
    by assigning drone command names. Prevents duplicates within session and across systems.

    Args:
        system_name: System to activate commands for

    Returns:
        {
            'success': bool,
            'activated': int,
            'active_commands': [{'id': int, 'command_name': str, 'drone_command': str}, ...],
            'error': str | None
        }

    Example:
        >>> result = activate_commands_interactive("flow")
        # Interactive prompts appear
        >>> print(result['activated'])
        3
    """
    result = {
        'success': False,
        'activated': 0,
        'active_commands': [],
        'error': None
    }

    try:
        # Load registry
        registry = load_system_registry(system_name)
        if not registry:
            result['error'] = f"No registry found for system '{system_name}'"
            return result

        # Load active.json to get actual activation state
        active_file = DRONE_ROOT / "commands" / system_name / "active.json"
        active_commands = {}
        if active_file.exists():
            try:
                with open(active_file, 'r', encoding='utf-8') as f:
                    active_data = json.load(f)
                    # Build lookup by ID
                    for drone_cmd, cmd_info in active_data.items():
                        active_commands[cmd_info['id']] = drone_cmd
            except Exception:
                pass

        # Build command list with IDs
        commands = []
        for cmd_name, cmd_data in registry.items():
            cmd_id = cmd_data['id']
            is_active = cmd_id in active_commands
            drone_cmd = active_commands.get(cmd_id, '')

            commands.append({
                'id': cmd_id,
                'name': cmd_name,
                'help': cmd_data.get('help', ''),
                'active': is_active,
                'drone_command': drone_cmd
            })

        # Sort by ID
        commands.sort(key=lambda x: x['id'])

        # Interactive loop
        activated = []

        while True:
            # Display current state
            console.print()
            console.print(Panel(f"Activate commands for: {system_name}", style="bold cyan", expand=False))
            console.print()
            console.print(f"{'ID':<6}  {'Command':<35}  {'Active':<8}  {'Drone Command'}")
            console.print(f"{'-'*4}  {'-'*33}  {'-'*6}  {'-'*30}")

            for cmd in commands:
                id_str = f"{cmd['id']:03d}"
                active_str = "[green]YES[/green]" if cmd['active'] else "[dim]No[/dim]"
                drone_cmd = cmd['drone_command'] if cmd['drone_command'] else "[dim]n/a[/dim]"
                console.print(f"{id_str:<6}  {cmd['name']:<35}  {active_str:<8}  {drone_cmd}")

            active_count = len([c for c in commands if c['active']])
            console.print(f"\n[cyan]{active_count} active[/cyan] / {len(commands)} total")

            # Prompt for ID
            console.print()
            console.print("[cyan]Enter command ID to activate[/cyan] [dim](or 'done' to finish):[/dim] ", end='')
            user_input = input().strip().lower()

            if user_input == 'done':
                break

            # Parse ID
            try:
                cmd_id = int(user_input)
            except ValueError:
                print(f"❌ Invalid input. Enter a number or 'done'")
                continue

            # Find command
            target_cmd = None
            for cmd in commands:
                if cmd['id'] == cmd_id:
                    target_cmd = cmd
                    break

            if not target_cmd:
                print(f"❌ Command ID {cmd_id:03d} not found")
                continue

            if target_cmd['active']:
                print(f"⚠️  Command {cmd_id:03d} ({target_cmd['name']}) is already active")
                continue

            # Get drone command name
            print(f"\n{'─'*70}")
            print(f"Activating ID {cmd_id:03d}: {target_cmd['name']}")
            print(f"{'─'*70}")
            print(f"Drone command name (e.g., 'test create', 'backup snap'): ", end='')
            drone_cmd = input().strip()

            if not drone_cmd:
                print("❌ Drone command name required")
                continue

            # Prevent duplicate drone command names within current session
            duplicate_in_session = any(
                cmd_entry['drone_command'] == drone_cmd and cmd_entry['active']
                for cmd_entry in commands
            )
            if duplicate_in_session:
                print(f"⚠️  Drone command '{drone_cmd}' is already in use during this activation session.")
                print("   Choose a unique drone command name.")
                logger.warning(
                    f"[{MODULE_NAME}] Duplicate drone command '{drone_cmd}' blocked in activation session for {system_name}"
                )
                continue

            # Prevent conflicts with commands activated in other systems
            existing_activation = lookup_activated_command(drone_cmd)
            if existing_activation:
                existing_system = existing_activation.get('system', 'unknown')
                existing_id = existing_activation.get('id')
                if isinstance(existing_id, int):
                    id_display = f"{existing_id:03d}"
                else:
                    id_display = str(existing_id) if existing_id is not None else "unknown"
                print(f"⚠️  Drone command '{drone_cmd}' is already active in system '{existing_system}' (ID {id_display}).")
                print("   Choose a unique drone command name.")
                logger.warning(
                    f"[{MODULE_NAME}] Drone command '{drone_cmd}' already active in {existing_system} (ID {id_display}); blocking duplicate for {system_name}"
                )
                continue

            # Optional description
            print(f"Description (optional, press Enter to skip): ", end='')
            description = input().strip()
            if not description:
                description = target_cmd['help']

            # Mark as activated
            target_cmd['active'] = True
            target_cmd['drone_command'] = drone_cmd
            target_cmd['description'] = description

            activated.append({
                'id': cmd_id,
                'command_name': target_cmd['name'],
                'drone_command': drone_cmd,
                'description': description
            })

            print(f"✅ Activated {cmd_id:03d} as 'drone {drone_cmd}'")

        # Save activated commands
        if activated:
            # Update registry
            for cmd in commands:
                if cmd['name'] in registry:
                    registry[cmd['name']]['active'] = cmd['active']
                    if cmd.get('drone_command'):
                        registry[cmd['name']]['drone_command'] = cmd['drone_command']
                    if cmd.get('description'):
                        registry[cmd['name']]['description'] = cmd['description']

            save_system_registry(system_name, registry)

            # Save active.json - MERGE with existing, don't overwrite
            active_file = DRONE_ROOT / "commands" / system_name / "active.json"

            # Load existing active data to preserve previous activations
            active_data = {}
            if active_file.exists():
                try:
                    with open(active_file, 'r', encoding='utf-8') as f:
                        active_data = json.load(f)
                except Exception:
                    active_data = {}

            # Now update/add new activations (and remove deactivated ones)
            for cmd in commands:
                if cmd['active']:
                    # Extract actual command name from registry (not the module:command key)
                    registry_data = registry[cmd['name']]
                    actual_command = registry_data.get('command_name', cmd['name'])

                    active_data[cmd['drone_command']] = {
                        'id': cmd['id'],
                        'command_name': actual_command,  # Use actual command, not registry key
                        'description': cmd.get('description', cmd['help']),
                        'module_path': registry_data.get('module_path', '')
                    }
                else:
                    # Remove deactivated commands
                    if cmd.get('drone_command') and cmd['drone_command'] in active_data:
                        del active_data[cmd['drone_command']]

            with open(active_file, 'w', encoding='utf-8') as f:
                json.dump(active_data, f, indent=2, ensure_ascii=False)

            result['success'] = True
            result['activated'] = len(activated)
            result['active_commands'] = activated
            logger.info(f"[{MODULE_NAME}] Activated {len(activated)} commands for {system_name}")
        else:
            result['success'] = True  # Not an error, just nothing activated
            result['activated'] = 0

    except Exception as e:
        result['error'] = f"Activation failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Activation error: {e}")

    return result
