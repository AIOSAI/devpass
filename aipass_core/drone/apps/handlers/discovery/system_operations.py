#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: system_operations.py - System Operations Handler
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/discovery
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): BEAST MIGRATION - Extracted from drone_discovery.py (2,289 lines)
#   - v1.0.0 (2025-10-16): Original implementation in monolithic file
# =============================================

"""
System Operations Handler

Manages system-level operations: list systems, list commands, remove commands,
refresh systems, and edit commands. Handles active.json and registry.json coordination.

Features:
- List all registered systems with stats
- List all activated commands
- Remove activated commands
- Refresh system (re-scan for changes)
- Interactive command editing
- Orphan detection and healing

Usage:
    from drone.apps.handlers.discovery.system_operations import list_all_systems, refresh_system

    systems = list_all_systems()
    result = refresh_system("flow")
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

# CLI for Rich formatting
from cli.apps.modules import console
from rich.panel import Panel

# Same-package imports allowed
from .command_parsing import load_system_registry, save_system_registry, get_next_global_id, increment_global_id
from .module_scanning import scan_module

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "system_operations"
DRONE_ROOT = AIPASS_ROOT / "drone"
ECOSYSTEM_ROOT = Path.home()
BRANCH_REGISTRY_PATH = Path.home() / "BRANCH_REGISTRY.json"

# =============================================
# CALLER DETECTION (for Mission Control visibility)
# =============================================

def _detect_caller_branch() -> str:
    """
    Detect which branch is calling based on PWD.
    Returns branch name or 'UNKNOWN' if not detected.
    """
    try:
        cwd = Path.cwd()
        current = cwd.resolve()
        for _ in range(10):
            if list(current.glob("*.id.json")):
                if BRANCH_REGISTRY_PATH.exists():
                    with open(BRANCH_REGISTRY_PATH, 'r') as f:
                        registry = json.load(f)
                    for branch in registry.get("branches", []):
                        if Path(branch["path"]).resolve() == current:
                            return branch.get("name", "UNKNOWN")
                return current.name.upper()
            parent = current.parent
            if parent == current:
                break
            current = parent
    except Exception:
        pass
    return "UNKNOWN"

# =============================================
# LIST OPERATIONS
# =============================================

def list_all_systems() -> dict:
    """
    List all registered systems with statistics

    Returns:
        {
            'success': bool,
            'systems': [
                {
                    'name': str,
                    'registered': int,
                    'activated': int,
                    'module_path': str
                },
                ...
            ],
            'error': str | None
        }

    Example:
        >>> result = list_all_systems()
        >>> for system in result['systems']:
        ...     print(f"{system['name']}: {system['activated']} active")
        flow: 12 active
        prax: 8 active
    """
    result = {
        'success': False,
        'systems': [],
        'error': None
    }

    try:
        commands_dir = DRONE_ROOT / "commands"

        if not commands_dir.exists():
            result['error'] = "No systems registered yet"
            return result

        # Scan for system directories
        systems = []
        for system_dir in commands_dir.iterdir():
            if not system_dir.is_dir():
                continue

            registry_file = system_dir / "registry.json"
            if not registry_file.exists():
                continue

            # Load registry
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
            except Exception:
                continue

            # Count registered commands
            total_registered = len(registry)

            # Count activated commands from active.json (not registry.json)
            active_file = system_dir / "active.json"
            total_activated = 0
            if active_file.exists():
                try:
                    with open(active_file, 'r', encoding='utf-8') as f:
                        active_data = json.load(f)
                        total_activated = len(active_data)
                except Exception:
                    total_activated = 0

            # Get module path from any command
            module_path = ""
            if registry:
                first_cmd = next(iter(registry.values()))
                module_path = first_cmd.get('module_path', '')

            systems.append({
                'name': system_dir.name,
                'registered': total_registered,
                'activated': total_activated,
                'module_path': module_path
            })

        # Sort by name
        systems.sort(key=lambda x: x['name'])

        result['success'] = True
        result['systems'] = systems

    except Exception as e:
        result['error'] = f"Failed to list systems: {str(e)}"
        logger.error(f"[{MODULE_NAME}] List systems error: {e}")

    return result

def list_activated_commands(system_filter: Optional[str] = None) -> dict:
    """
    List all activated commands across all systems, or filter by specific system

    Args:
        system_filter: Optional system name to filter by (e.g., "prax", "flow")

    Returns:
        {
            'success': bool,
            'commands': [
                {
                    'drone_command': str,
                    'id': int,
                    'system': str,
                    'command_name': str,
                    'description': str,
                    'module_path': str
                },
                ...
            ],
            'error': str | None,
            'filtered_by': str | None
        }

    Example:
        >>> result = list_activated_commands()  # All systems
        >>> for cmd in result['commands']:
        ...     print(f"drone {cmd['drone_command']}")
        drone test create
        drone backup snap

        >>> result = list_activated_commands("prax")  # Only prax
        >>> for cmd in result['commands']:
        ...     print(f"drone {cmd['drone_command']}")
        drone prax file watcher
        drone prax module watcher
    """
    result = {
        'success': False,
        'commands': [],
        'error': None,
        'filtered_by': system_filter
    }

    try:
        commands_dir = DRONE_ROOT / "commands"

        if not commands_dir.exists():
            result['error'] = "No systems registered yet"
            return result

        # Scan for system directories
        all_commands = []
        for system_dir in commands_dir.iterdir():
            if not system_dir.is_dir():
                continue

            # Apply system filter if provided
            if system_filter and system_dir.name != system_filter:
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

            # Add system name to each command
            for drone_cmd, cmd_data in active_data.items():
                all_commands.append({
                    'drone_command': drone_cmd,
                    'id': cmd_data.get('id', 0),
                    'system': system_dir.name,
                    'command_name': cmd_data.get('command_name', ''),
                    'description': cmd_data.get('description', ''),
                    'module_path': cmd_data.get('module_path', '')
                })

        # Sort by drone command name
        all_commands.sort(key=lambda x: x['drone_command'])

        result['success'] = True
        result['commands'] = all_commands

    except Exception as e:
        result['error'] = f"Failed to list commands: {str(e)}"
        logger.error(f"[{MODULE_NAME}] List commands error: {e}")

    return result

# =============================================
# REMOVE OPERATIONS
# =============================================

def remove_activated_command(drone_command: str) -> dict:
    """
    Remove an activated command

    Args:
        drone_command: The drone command name to remove

    Returns:
        {
            'success': bool,
            'drone_command': str,
            'command_name': str,
            'system': str,
            'id': int,
            'error': str | None
        }

    Example:
        >>> result = remove_activated_command("test create")
        >>> print(result['success'])
        True
    """
    result = {
        'success': False,
        'drone_command': drone_command,
        'command_name': '',
        'system': '',
        'id': 0,
        'error': None
    }

    try:
        commands_dir = DRONE_ROOT / "commands"

        if not commands_dir.exists():
            result['error'] = "No systems registered"
            return result

        # Search all active.json files for the command
        found_system = None
        found_data = None

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
                found_system = system_dir.name
                found_data = active_data[drone_command]

                # Remove from active.json
                del active_data[drone_command]

                # Save updated active.json
                with open(active_file, 'w', encoding='utf-8') as f:
                    json.dump(active_data, f, indent=2, ensure_ascii=False)

                # Also update registry.json to mark as inactive
                registry = load_system_registry(found_system)
                if found_data['command_name'] in registry:
                    registry[found_data['command_name']]['active'] = False
                    registry[found_data['command_name']]['drone_command'] = ''
                    save_system_registry(found_system, registry)

                result['success'] = True
                result['command_name'] = found_data.get('command_name', '')
                result['system'] = found_system
                result['id'] = found_data.get('id', 0)

                logger.info(f"[{MODULE_NAME}] Removed command '{drone_command}' from {found_system}")
                break

        if not result['success']:
            result['error'] = f"Command '{drone_command}' not found in any active system"

    except Exception as e:
        result['error'] = f"Remove failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Remove error: {e}")

    return result

# =============================================
# REFRESH OPERATIONS
# =============================================

def refresh_system(system_name: str) -> dict:
    """
    Re-scan a system's module for new/changed commands

    Detects orphaned activations (commands no longer present) and removes them.

    Args:
        system_name: System to refresh

    Returns:
        {
            'success': bool,
            'system_name': str,
            'new_commands': int,
            'total_commands': int,
            'commands': [{'id': int, 'name': str, 'status': str}, ...],
            'error': str | None,
            'orphaned_commands': List[str]
        }

    Example:
        >>> result = refresh_system("flow")
        >>> print(f"New: {result['new_commands']}, Orphaned: {len(result['orphaned_commands'])}")
        New: 2, Orphaned: 1
    """
    result = {
        'success': False,
        'system_name': system_name,
        'new_commands': 0,
        'total_commands': 0,
        'commands': [],
        'error': None,
        'orphaned_commands': []
    }

    try:
        # Load existing registry
        existing_registry = load_system_registry(system_name)
        if not existing_registry:
            result['error'] = f"System '{system_name}' not registered"
            return result

        # Get directory path from registry (look at module_path and go up to directory)
        module_path = None
        if existing_registry:
            first_cmd = next(iter(existing_registry.values()))
            module_path_str = first_cmd.get('module_path', '')
            if module_path_str:
                # If it's a file, get the parent directory
                module_path_obj = Path(module_path_str)
                if module_path_obj.is_file():
                    module_path = str(module_path_obj.parent)
                else:
                    module_path = module_path_str

        if not module_path:
            result['error'] = "Module path not found in registry"
            return result

        # Re-scan the directory (convert to @ format for new standard)
        module_path_obj = Path(module_path)
        if module_path_obj.is_relative_to(ECOSYSTEM_ROOT):
            scan_path = f"@{module_path_obj.relative_to(ECOSYSTEM_ROOT)}"
        else:
            scan_path = f"@{module_path}"

        scan_result = scan_module(scan_path)

        if not scan_result['success']:
            result['error'] = scan_result.get('error', 'Scan failed')
            return result

        if not scan_result['commands']:
            result['error'] = 'No commands detected during refresh'
            return result

        # Build new registry from scan (same logic as register_module)
        new_registry = {}

        # Track existing activations to detect orphans later
        active_file = DRONE_ROOT / "commands" / system_name / "active.json"
        active_data = {}
        if active_file.exists():
            try:
                with open(active_file, 'r', encoding='utf-8') as f:
                    active_data = json.load(f)
            except Exception as e:
                logger.error(f"[{MODULE_NAME}] Failed to load active.json for {system_name}: {e}")
                active_data = {}

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
                        # Keep existing ID and data
                        new_registry[registry_key] = existing_registry[registry_key]
                        # Update module_path in case it changed
                        new_registry[registry_key]['module_path'] = module_path_for_cmd
                    else:
                        # Assign new ID
                        new_id = get_next_global_id()
                        increment_global_id()

                        new_registry[registry_key] = {
                            'id': new_id,
                            'command_name': cmd_name,
                            'module_name': module_stem,
                            'help': '',
                            'module_path': module_path_for_cmd,
                            'registered_date': datetime.now(timezone.utc).isoformat(),
                            'active': False
                        }

        # Detect orphaned activations (commands still marked active but no longer present)
        if active_data:
            valid_pairs = {
                (cmd_data.get('module_path'), cmd_data.get('command_name'))
                for cmd_data in new_registry.values()
            }

            orphaned_drone_commands = []
            updated_active_data = {}

            for drone_cmd, cmd_info in active_data.items():
                key = (cmd_info.get('module_path'), cmd_info.get('command_name'))
                if key in valid_pairs:
                    updated_active_data[drone_cmd] = cmd_info
                else:
                    orphaned_drone_commands.append(drone_cmd)

            if orphaned_drone_commands:
                logger.warning(
                    f"[{MODULE_NAME}] Removing orphaned activations for system {system_name}: {orphaned_drone_commands}"
                )
                result['orphaned_commands'] = orphaned_drone_commands
                active_data = updated_active_data
            else:
                active_data = updated_active_data

        # Persist healed active.json if changes were made
        if active_data is not None and active_file.exists():
            try:
                with open(active_file, 'w', encoding='utf-8') as f:
                    json.dump(active_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"[{MODULE_NAME}] Failed to write healed active.json for {system_name}: {e}")

        # Build command list for display
        new_command_list = []
        existing_keys = set(existing_registry.keys())
        new_keys = set(new_registry.keys())

        new_commands_found = new_keys - existing_keys

        for registry_key in sorted(new_registry.keys(), key=lambda k: new_registry[k]['id']):
            cmd_data = new_registry[registry_key]
            status = 'NEW' if registry_key in new_commands_found else 'EXISTS'

            new_command_list.append({
                'id': cmd_data['id'],
                'name': registry_key,
                'status': status
            })

        # Save updated registry
        save_system_registry(system_name, new_registry)

        result['success'] = True
        result['new_commands'] = len(new_commands_found)
        result['total_commands'] = len(new_registry)
        result['commands'] = new_command_list

        logger.info(f"[{MODULE_NAME}] Refreshed {system_name}: {len(new_commands_found)} new commands")

    except Exception as e:
        result['error'] = f"Refresh failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Refresh error: {e}")

    return result

# =============================================
# EDIT OPERATIONS
# =============================================

def edit_activated_command_interactive() -> dict:
    """
    Interactive command editing - list all activated commands, select by ID, edit fields

    Returns:
        {
            'success': bool,
            'edited': bool,
            'command_id': int,
            'drone_command': str,
            'changes': dict,
            'error': str | None
        }

    Example:
        >>> result = edit_activated_command_interactive()
        # Interactive prompts appear
        >>> print(result['changes'])
        {'drone_command': {'old': 'test create', 'new': 'test new'}}
    """
    result = {
        'success': False,
        'edited': False,
        'command_id': None,
        'drone_command': None,
        'changes': {},
        'error': None
    }

    try:
        # Step 1: List all activated commands
        list_result = list_activated_commands()
        if not list_result['success'] or not list_result['commands']:
            result['error'] = list_result.get('error', 'No activated commands found')
            return result

        # Import formatter here to avoid circular dependency
        from .formatters import format_list_output

        # Display the list
        format_list_output(list_result)
        print()

        # Step 2: Prompt for ID
        print("Enter ID to edit (or press Enter to cancel): ", end='')
        user_input = input().strip()

        if not user_input:
            result['success'] = True  # User cancelled, not an error
            result['error'] = 'Cancelled by user'
            return result

        # Parse ID
        try:
            cmd_id = int(user_input)
        except ValueError:
            result['error'] = f"Invalid ID: {user_input}"
            return result

        # Find the command with this ID
        target_command = None
        for cmd in list_result['commands']:
            if cmd['id'] == cmd_id:
                target_command = cmd
                break

        if not target_command:
            result['error'] = f"Command ID {cmd_id:03d} not found"
            return result

        # Step 3: Edit workflow
        console.print()
        console.print(Panel(f"Editing Command ID: {cmd_id:03d}", style="bold cyan", expand=False))
        console.print()

        system_name = target_command['system']
        old_drone_cmd = target_command['drone_command']
        old_description = target_command['description']

        changes = {}

        # Edit drone command name
        console.print(f"[cyan]Current drone command:[/cyan] {old_drone_cmd}")
        console.print("[dim]New drone command [press Enter to keep]:[/dim] ", end='')
        new_drone_cmd = input().strip()

        if new_drone_cmd and new_drone_cmd != old_drone_cmd:
            changes['drone_command'] = {'old': old_drone_cmd, 'new': new_drone_cmd}
            console.print(f"[green]→ Changed to:[/green] {new_drone_cmd}")
        else:
            new_drone_cmd = old_drone_cmd
            console.print("[dim]→ No change[/dim]")

        # Edit description
        console.print()
        console.print(f"[cyan]Current description:[/cyan] {old_description if old_description else '[dim](none)[/dim]'}")
        console.print("[dim]New description [press Enter to keep]:[/dim] ", end='')
        new_description = input().strip()

        if new_description and new_description != old_description:
            changes['description'] = {'old': old_description, 'new': new_description}
            console.print(f"[green]→ Changed to:[/green] {new_description}")
        else:
            new_description = old_description
            console.print("[dim]→ No change[/dim]")

        # Step 4: Save changes if any
        if changes:
            # Load active.json for this system
            active_file = DRONE_ROOT / "commands" / system_name / "active.json"

            if not active_file.exists():
                result['error'] = f"Active file not found for system '{system_name}'"
                return result

            with open(active_file, 'r', encoding='utf-8') as f:
                active_data = json.load(f)

            # Update the command
            if old_drone_cmd in active_data:
                # If drone command name changed, need to move the key
                if 'drone_command' in changes:
                    cmd_data = active_data.pop(old_drone_cmd)
                    cmd_data['description'] = new_description
                    active_data[new_drone_cmd] = cmd_data
                else:
                    # Just update description
                    active_data[old_drone_cmd]['description'] = new_description

                # Save back to active.json
                with open(active_file, 'w', encoding='utf-8') as f:
                    json.dump(active_data, f, indent=2, ensure_ascii=False)

                # Also update registry.json
                registry_file = DRONE_ROOT / "commands" / system_name / "registry.json"
                if registry_file.exists():
                    with open(registry_file, 'r', encoding='utf-8') as f:
                        registry = json.load(f)

                    # Find and update the command in registry
                    command_name = target_command['command_name']
                    if command_name in registry:
                        if 'drone_command' in changes:
                            registry[command_name]['drone_command'] = new_drone_cmd
                        if 'description' in changes:
                            registry[command_name]['description'] = new_description

                        with open(registry_file, 'w', encoding='utf-8') as f:
                            json.dump(registry, f, indent=2, ensure_ascii=False)

                result['success'] = True
                result['edited'] = True
                result['command_id'] = cmd_id
                result['drone_command'] = new_drone_cmd
                result['changes'] = changes

                console.print()
                console.print(f"[green]✅ Updated command {cmd_id:03d} ({system_name})[/green]")
                logger.info(f"[{MODULE_NAME}] Edited command {cmd_id:03d}: {changes}")
            else:
                result['error'] = f"Command '{old_drone_cmd}' not found in active.json"
                return result
        else:
            result['success'] = True
            result['edited'] = False
            result['command_id'] = cmd_id
            console.print()
            console.print(f"[yellow]ℹ️  No changes made to command {cmd_id:03d}[/yellow]")

    except Exception as e:
        result['error'] = f"Edit failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Edit command error: {e}")

    return result


# =============================================
# MODULE EXECUTION (@  and / pattern support)
# =============================================

def is_long_running_command(command_args: List[str]) -> bool:
    """
    Detect if command is a long-running/daemon process that needs no timeout

    Args:
        command_args: List of command arguments

    Returns:
        True if command should run without timeout, False otherwise

    Examples:
        ["branch-watcher", "start"] -> True (watcher daemon)
        ["run"] -> True (continuous logging mode)
        ["status"] -> False (quick command)
        ["help"] -> False (quick command)
    """
    # Convert all args to lowercase for case-insensitive matching
    args_lower = [arg.lower() for arg in command_args]
    args_str = ' '.join(args_lower)

    # Daemon/watcher keywords (run indefinitely)
    daemon_keywords = ['watcher', 'watch', 'monitor', 'daemon', 'serve', 'server']

    # Slow commands (need extended time but not infinite)
    slow_keywords = ['audit', 'diagnostics', 'sync', 'checklist']

    # Check for daemon keywords in command
    if any(keyword in args_str for keyword in daemon_keywords):
        return True

    # Check for slow commands
    if any(keyword in args_str for keyword in slow_keywords):
        return True

    # PRAX continuous mode
    if 'run' in args_lower and len(args_lower) == 1:
        return True

    return False


def _notify_env_failure(branch_name: str, command: str, stderr: str, python_cmd: str) -> None:
    """Send environment failure notification to @dev_central via ai_mail."""
    import subprocess as sp

    # Truncate stderr to last 10 lines to keep notification concise
    stderr_tail = '\n'.join(stderr.strip().splitlines()[-10:])
    subject = f"ENV ERROR: @{branch_name} import/environment failure"
    message = (
        f"Branch: @{branch_name}\n"
        f"Command: {command}\n"
        f"Python: {python_cmd}\n"
        f"Error:\n{stderr_tail}"
    )

    try:
        sp.run(
            ['drone', '@ai_mail', 'send', '@dev_central', subject, message],
            timeout=10,
            capture_output=True
        )
    except Exception:
        # Notification is best-effort - don't fail the caller
        logger.warning(f"[{MODULE_NAME}] Could not notify @dev_central of env failure in @{branch_name}")


def run_branch_module(module_path: Path, module_args: List[str], timeout: int | None = None) -> bool:
    """
    Run a branch module (seed, flow, prax, etc.) with arguments

    Handler for executing branch modules via @ arguments and / slash patterns.

    Args:
        module_path: Path to the module directory or .py file
        module_args: Arguments to pass to the module
        timeout: Timeout in seconds (None = auto-detect based on command)

    Returns:
        True if successful, False otherwise

    Usage:
        # Via @ pattern
        module_path = resolve_scan_path("@seed")
        run_branch_module(module_path, ["help"])

        # Via / pattern with timeout
        module_path = Path("/home/aipass/seed/apps/modules/imports_standard.py")
        run_branch_module(module_path, [], timeout=60)

        # Long-running daemon process (no timeout)
        run_branch_module(module_path, ["watcher", "start"], timeout=None)
    """
    import subprocess

    # If it's a directory, look for the main entry point
    if module_path.is_dir():
        # Try apps/<module_name>.py first (exact case)
        module_name = module_path.name
        entry_point = module_path / "apps" / f"{module_name}.py"

        if not entry_point.exists():
            # Try lowercase (Linux is case-sensitive, most entry points are lowercase)
            entry_point = module_path / "apps" / f"{module_name.lower()}.py"

        if not entry_point.exists():
            # Try apps/main.py as last resort
            entry_point = module_path / "apps" / "main.py"

        if not entry_point.exists():
            logger.error(f"[{MODULE_NAME}] No entry point found in {module_path}")
            return False
    else:
        entry_point = module_path

    # Auto-detect timeout if not specified
    if timeout is None:
        # Check for slow commands that need extended timeout
        args_lower = [arg.lower() for arg in module_args]
        args_str = ' '.join(args_lower)

        # Daemon/watcher keywords (run indefinitely) - no timeout
        daemon_keywords = ['watcher', 'watch', 'monitor', 'daemon', 'serve', 'server']
        if any(keyword in args_str for keyword in daemon_keywords):
            timeout = None
        # Continuous monitoring (PRAX run mode) - no timeout
        elif 'run' in args_lower and len(args_lower) == 1:
            timeout = None
        # Sync commands (data transfer, can take several minutes) - no timeout
        elif 'sync' in args_str:
            timeout = None
        # Slow commands (need extended time but not infinite) - 120 seconds
        elif 'audit' in args_str or 'diagnostics' in args_str or 'checklist' in args_str:
            timeout = 120
        # ai_mail send can take 25-30s due to startup overhead - extend timeout
        elif entry_point.name == 'ai_mail.py' and 'send' in args_lower:
            timeout = 60
        # Default timeout for normal commands - 30 seconds
        else:
            timeout = 30

    # Log execution with caller for Mission Control visibility
    caller_name = _detect_caller_branch()
    logger.info(
        f"[{MODULE_NAME}] Executing command [CALLER:{caller_name}]: "
        f"{entry_point.name} {' '.join(module_args)}"
    )

    # Detect branch venv - use it if available for correct dependencies
    branch_root = entry_point.parent
    while branch_root != Path.home() and branch_root != Path('/'):
        venv_python = branch_root / '.venv' / 'bin' / 'python3'
        if venv_python.exists():
            python_cmd = str(venv_python)
            break
        branch_root = branch_root.parent
    else:
        python_cmd = 'python3'

    # Run the module - stdout streams to terminal, stderr captured for inspection
    try:
        result = subprocess.run(
            [python_cmd, str(entry_point)] + module_args,
            timeout=timeout,
            stderr=subprocess.PIPE,
            text=True
        )

        # Check stderr for environment/import failures
        if result.stderr:
            stderr_lower = result.stderr.lower()
            env_patterns = [
                'modulenotfounderror', 'importerror', 'no module named',
                'no such file or directory', 'permission denied',
                'invalid interpreter', 'bad interpreter'
            ]
            is_env_error = any(p in stderr_lower for p in env_patterns)

            if is_env_error:
                branch_name = entry_point.parent.parent.name if entry_point.parent.name == 'apps' else entry_point.parent.name
                cmd_str = f"{entry_point.name} {' '.join(module_args)}"

                # Surface clear warning to terminal
                console.print(f"\n[bold yellow]⚠ Environment Error in @{branch_name}[/bold yellow]")
                console.print(f"[yellow]Command: {cmd_str}[/yellow]")
                for line in result.stderr.strip().splitlines()[-5:]:
                    console.print(f"  [red]{line}[/red]")
                console.print(f"[dim]Python used: {python_cmd}[/dim]")

                logger.error(
                    f"[{MODULE_NAME}] Environment error in @{branch_name}: "
                    f"{result.stderr.strip().splitlines()[-1]}"
                )

                # Notify @dev_central of environment failure
                _notify_env_failure(branch_name, cmd_str, result.stderr, python_cmd)

                return False
            elif result.returncode != 0:
                # Log the failure so TRIGGER can detect it
                last_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else f"exit code {result.returncode}"
                logger.error(
                    f"[{MODULE_NAME}] Command failed (rc={result.returncode}): "
                    f"{entry_point.name} {' '.join(module_args)} - {last_line}"
                )
                # Also print stderr to terminal so user sees it
                for line in result.stderr.strip().splitlines():
                    console.print(f"  [dim red]{line}[/dim red]", highlight=False)

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        timeout_msg = f"Command timed out after {timeout} seconds"
        logger.error(f"[{MODULE_NAME}] {timeout_msg}: {entry_point}")
        console.print(f"\n[red]{timeout_msg}[/red]")
        console.print(f"[dim]Try running directly: python3 {entry_point} {' '.join(module_args)}[/dim]")
        return False
    except BrokenPipeError:
        # Pipe closed before output finished (e.g. parent process exited).
        # Command likely completed; not a real failure.
        logger.info(f"[{MODULE_NAME}] Broken pipe (stdout closed early): {entry_point.name}")
        return True
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error running module: {e}")
        try:
            console.print(f"[red]Error: {str(e)}[/red]")
        except BrokenPipeError:
            pass
        return False


def resolve_slash_pattern(command: str) -> tuple[Path | None, str | None]:
    """
    Resolve / slash pattern for sub-modules

    Handles patterns like: seed/imports, flow/plan, drone/discovery

    Args:
        command: Command string with / (e.g., "seed/imports")

    Returns:
        Tuple of (module_path, error_message)
        If successful, returns (Path, None)
        If failed, returns (None, error_message)

    Examples:
        drone seed/imports → /home/aipass/seed/apps/modules/imports_standard.py
        drone flow/plan → /home/aipass/aipass_core/flow/apps/modules/plan.py
    """
    from .module_scanning import resolve_scan_path

    if '/' not in command:
        return None, "Not a slash pattern"

    parts = command.split('/', 1)
    branch_name = parts[0]
    sub_module = parts[1]

    # Resolve branch path using existing resolve_scan_path
    try:
        branch_path = resolve_scan_path(f"@{branch_name}")
    except FileNotFoundError:
        return None, f"Branch not found: {branch_name}"

    # Look for the sub-module in apps/modules/
    sub_module_path = branch_path / "apps" / "modules" / f"{sub_module}.py"

    if not sub_module_path.exists():
        # Try with _standard suffix (for seed standards)
        sub_module_path = branch_path / "apps" / "modules" / f"{sub_module}_standard.py"

    if sub_module_path.exists():
        return sub_module_path, None
    else:
        return None, f"Module not found: {command} (looked in {sub_module_path})"
