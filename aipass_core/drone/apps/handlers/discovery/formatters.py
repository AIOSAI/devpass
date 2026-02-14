#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: formatters.py - Output Formatters Handler
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/discovery
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): BEAST MIGRATION - Extracted from drone_discovery.py (2,289 lines)
#   - v1.0.0 (2025-10-16): Original implementation in monolithic file
# =============================================

"""
Output Formatters Handler

Formats discovery results for console display. Handles scan output, registration output,
activation summaries, system lists, command lists, and operation results.

Features:
- Scan results formatting (files and directories)
- Registration output formatting
- Activation summary formatting
- System list formatting
- Command list formatting
- Remove/refresh/edit output formatting

Usage:
    from drone.apps.handlers.discovery.formatters import format_scan_output, format_list_output

    print(format_scan_output(scan_result))
    format_list_output(list_result)  # Prints directly to console
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from typing import Dict, List, Optional, Any
from cli.apps.modules import console
from rich.panel import Panel

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "formatters"

# =============================================
# SCAN FORMATTERS
# =============================================

def format_scan_output(result: dict, show_full_command: bool = False):
    """
    Format scan results for display

    Args:
        result: Scan result dictionary
        show_full_command: If True, show Full Command column (default: False)

    Example:
        >>> format_scan_output(scan_result)
        ======================================================================
        Scanning: /home/aipass/flow
        ======================================================================
        ...
    """
    console.print(Panel(f"Scanning: {result['module_path']}", style="bold cyan", expand=False))

    if result['error'] and not result.get('is_directory'):
        console.print(f"\n❌ Error: {result['error']}")
        return

    # Handle directory scanning
    if result.get('is_directory'):
        modules_scanned = result.get('modules_scanned', [])

        console.print(f"\n📁 Directory scan - found {len(modules_scanned)} Python modules")
        console.print()

        # Show modules with commands
        modules_with_cmds = [m for m in modules_scanned if m['commands']]
        modules_without_cmds = [m for m in modules_scanned if not m['commands']]

        if modules_with_cmds:
            console.print("✅ Modules with commands:")
            for mod in modules_with_cmds:
                console.print(f"   {mod['file']}: {len(mod['commands'])} commands")

        if modules_without_cmds:
            # Categorize by module type
            library_modules = [m for m in modules_without_cmds if m.get('module_type') == 'library']
            cli_modules = [m for m in modules_without_cmds if m.get('module_type') == 'cli']
            unknown_modules = [m for m in modules_without_cmds if m.get('module_type') not in ['library', 'cli']]

            console.print()

            # Show library modules (no CLI by design)
            if library_modules:
                console.print("📚 Library modules (no CLI by design):")
                for mod in library_modules:
                    console.print(f"   {mod['file']}")

            # Show CLI modules that need updating
            if cli_modules:
                if library_modules:
                    console.print()
                console.print("⚠️  CLI modules missing compliance (upgrade recommended):")
                for mod in cli_modules:
                    console.print(f"   {mod['file']}")

            # Show unknown modules
            if unknown_modules:
                if library_modules or cli_modules:
                    console.print()
                console.print("⚠️  Modules without commands:")
                for mod in unknown_modules:
                    console.print(f"   {mod['file']}")

        if not result['commands']:
            console.print()
            console.print("❌ No commands found in any module")
            return

        # Display aggregated commands
        console.print()
        console.print(f"📋 Aggregated commands ({len(result['commands'])} total):")
        console.print()

        # Build command list with module mapping (preserves order, handles duplicates)
        command_module_pairs = []
        for mod in modules_scanned:
            if mod['commands']:
                for cmd in mod['commands']:
                    command_module_pairs.append((cmd, mod['file'], mod['path']))

        # Conditionally show Full Command column
        if show_full_command:
            console.print(f"{'#':<8}{'Command':<24}{'Module':<30}{'Full Command'}")
            console.print(f"{'-' * 6}  {'-' * 22}  {'-' * 28}  {'-' * 50}")
        else:
            console.print(f"{'#':<8}{'Command':<24}{'Module'}")
            console.print(f"{'-' * 6}  {'-' * 22}  {'-' * 28}")

        # Get the base directory for cleaner paths
        base_dir = Path(result['module_path'])

        for i, (cmd, module, module_path) in enumerate(command_module_pairs, start=1):
            num = str(i)  # 1, 2, 3, ...
            if show_full_command:
                # Calculate relative path from base_dir (handles apps/ subdirectory)
                try:
                    rel_path = Path(module_path).relative_to(base_dir)
                    full_cmd = f"cd {base_dir} && python3 {rel_path} {cmd}"
                except ValueError:
                    # Fallback if relative path fails - use absolute path
                    full_cmd = f"python3 {module_path} {cmd}"
                console.print(f"{num:<8}{cmd:<24}{module:<30}{full_cmd}")
            else:
                console.print(f"{num:<8}{cmd:<24}{module}")

        console.print()
        console.print(f"{len(result['commands'])} commands found across {len(modules_with_cmds)} modules")
        console.print("\n[yellow]💡 Use 'drone register <module>' to register commands[/yellow]")

        return

    # Handle single file scanning
    if not result['success']:
        console.print("\n❌ Scan failed")
        return

    if not result['commands']:
        console.print("\n⚠️  No commands detected")
        return

    # Display commands
    console.print(f"\n✅ Commands detected via runtime --help:")
    console.print()

    if show_full_command:
        # Show with Full Command column (for copy-paste testing)
        console.print(f"{'#':<8}{'Command':<25}{'Full Command'}")
        console.print(f"{'-' * 6}  {'-' * 23}  {'-' * 50}")

        # Generate full command paths
        module_path = Path(result['module_path'])
        base_dir = module_path.parent
        relative_path = module_path.relative_to(base_dir) if module_path.is_absolute() else module_path.name

        for i, cmd in enumerate(result['commands'], start=1):
            num = str(i)
            full_cmd = f"cd {base_dir} && python3 {relative_path} {cmd}"
            console.print(f"{num:<8}{cmd:<25}{full_cmd}")
    else:
        # Compact view (default)
        console.print(f"{'#':<8}{'Command'}")
        console.print(f"{'-' * 6}  {'-' * 30}")

        for i, cmd in enumerate(result['commands'], start=1):
            num = str(i)
            console.print(f"{num:<8}{cmd}")

    console.print()
    console.print(f"{len(result['commands'])} commands found")
    console.print("\n[yellow]💡 Use 'drone register <module>' to register commands[/yellow]")

# =============================================
# REGISTRATION FORMATTERS
# =============================================

def format_registration_output(result: dict):
    """Format registration results for display"""
    console.print(Panel(f"Registering: {result.get('system_name', 'Unknown')}", style="bold cyan", expand=False))

    if result['error']:
        console.print(f"\n❌ Error: {result['error']}")
        return

    if not result['success']:
        console.print("\n❌ Registration failed")
        return

    # Show commands with IDs and module names
    console.print(f"\n✅ Commands registered:")
    console.print()
    console.print(f"{'ID':<8}{'Command':<22}{'Module':<30}{'Status':<12}{'Description'}")
    console.print(f"{'-' * 6}  {'-' * 20}  {'-' * 28}  {'-' * 10}  {'-' * 40}")

    new_count = 0
    for cmd in result['commands']:
        id_str = f"{cmd['id']:03d}"
        command_name = cmd.get('command_name', cmd['name'])
        module_name = cmd.get('module_name', '')
        status = "EXISTS" if cmd.get('already_registered') else "NEW"
        if not cmd.get('already_registered'):
            new_count += 1
        help_text = cmd['help'][:40] if cmd['help'] else '(no description)'
        console.print(f"{id_str:<8}{command_name:<22}{module_name:<30}{status:<12}{help_text}")

    console.print()
    console.print(f"{new_count} new commands registered")
    console.print(f"Registry: {result['registry_path']}")

# =============================================
# ACTIVATION FORMATTERS
# =============================================

def format_activation_summary(system_name: str, result: dict):
    """Format activation summary"""
    console.print(Panel(f"Activation Summary: {system_name}", style="bold cyan", expand=False))

    if result['error']:
        console.print(f"❌ Error: {result['error']}")
        return

    if result['activated'] == 0:
        console.print("No new commands activated")
        return

    console.print(f"{'ID':<6}{'Command':<20}{'Drone Command':<25}{'Description'}")
    console.print(f"{'-'*4}  {'-'*18}  {'-'*23}  {'-'*30}")

    for cmd in result['active_commands']:
        id_str = f"{cmd['id']:03d}"
        desc = cmd['description'][:30] if cmd['description'] else ''
        console.print(f"{id_str:<6}{cmd['command_name']:<20}{cmd['drone_command']:<25}{desc}")

    console.print(f"\n✅ {result['activated']} commands activated")
    console.print(f"\nYou can now use:")
    for cmd in result['active_commands']:
        console.print(f"  drone {cmd['drone_command']}")

# =============================================
# LIST FORMATTERS
# =============================================

def format_systems_output(result: dict):
    """Format systems list for display"""
    console.print(Panel("Registered Systems", style="bold cyan", expand=False))

    if result['error']:
        console.print(f"\n❌ Error: {result['error']}")
        return

    if not result['systems']:
        console.print("\n⚠️  No systems registered")
        console.print("\n[yellow]💡 Use 'drone reg <module>' to register a system[/yellow]")
        return

    # Display systems table
    console.print(f"\n{'System':<20}{'Registered':<15}{'Activated':<15}{'Module Path'}")
    console.print(f"{'-' * 18}  {'-' * 13}  {'-' * 13}  {'-' * 40}")

    total_reg = 0
    total_act = 0

    for system in result['systems']:
        name = system['name']
        reg = system['registered']
        act = system['activated']
        path = system['module_path']

        # Shorten path using ~ for home dir (keeps links clickable)
        path = path.replace("/home/aipass", "~")

        console.print(f"{name:<20}  {reg:<15}  {act:<15}  {path}")

        total_reg += reg
        total_act += act

    console.print()
    console.print(f"{len(result['systems'])} systems | {total_reg} total registered | {total_act} total activated")
    console.print("\n[yellow]💡 Use 'drone list' to see all activated commands[/yellow]")
    console.print("[yellow]💡 Use 'drone activate <system>' to activate commands[/yellow]")

def format_list_output(result: dict):
    """Format activated commands list for display"""
    # Show filtered title if filtering by system
    if result.get('filtered_by'):
        title = f"Activated Drone Commands - {result['filtered_by']}"
    else:
        title = "Activated Drone Commands"

    console.print(Panel(title, style="bold cyan", expand=False))

    if result['error']:
        console.print(f"\n❌ Error: {result['error']}")
        return

    if not result['commands']:
        if result.get('filtered_by'):
            console.print(f"\n⚠️  No commands activated for system: {result['filtered_by']}")
        else:
            console.print("\n⚠️  No commands activated")
        console.print("\n[yellow]💡 Use 'drone systems' to see registered systems[/yellow]")
        console.print("[yellow]💡 Use 'drone activate <system>' to activate commands[/yellow]")
        return

    # Display commands table
    console.print(f"\n{'Drone Command':<25}{'ID':<6}{'System':<15}{'Command':<20}{'Description'}")
    console.print(f"{'-' * 23}  {'-' * 4}  {'-' * 13}  {'-' * 18}  {'-' * 30}")

    for cmd in result['commands']:
        drone_cmd = cmd['drone_command']
        id_str = f"{cmd['id']:03d}"
        system = cmd['system']
        command = cmd['command_name']
        desc = cmd['description'][:30] if cmd['description'] else '(no description)'

        console.print(f"{drone_cmd:<25}{id_str:<6}{system:<15}{command:<20}{desc}")

    console.print()
    if result.get('filtered_by'):
        console.print(f"{len(result['commands'])} activated commands for {result['filtered_by']}")
    else:
        console.print(f"{len(result['commands'])} activated commands")

    console.print("\n[yellow]💡 Usage: drone <command>[/yellow]")
    console.print("[yellow]   Example: drone test create[/yellow]")

# =============================================
# OPERATION FORMATTERS
# =============================================

def format_remove_output(result: dict):
    """Format remove results for display"""
    console.print(Panel(f"Remove Command: {result['drone_command']}", style="bold cyan", expand=False))

    if result['error']:
        console.print(f"\n❌ Error: {result['error']}")
        console.print("\n[yellow]💡 Use 'drone list' to see activated commands[/yellow]")
        return

    if not result['success']:
        console.print("\n❌ Remove failed")
        return

    console.print(f"\n✅ Command removed successfully")
    console.print()
    console.print(f"{'Field':<20}{'Value'}")
    console.print(f"{'-' * 18}  {'-' * 40}")
    console.print(f"{'Drone Command':<20}{result['drone_command']}")
    console.print(f"{'Original Command':<20}{result['command_name']}")
    console.print(f"{'System':<20}{result['system']}")
    console.print(f"{'ID':<20}{result['id']:03d}")

    console.print(f"\n[yellow]💡 Command 'drone {result['drone_command']}' is no longer available[/yellow]")
    console.print(f"[yellow]💡 Use 'drone activate {result['system']}' to re-activate it[/yellow]")

def format_refresh_output(result: dict):
    """Format refresh results for display"""
    console.print(Panel(f"Refresh System: {result['system_name']}", style="bold cyan", expand=False))

    if result['error']:
        console.print(f"\n❌ Error: {result['error']}")
        return

    if not result['success']:
        console.print("\n❌ Refresh failed")
        return

    if result.get('orphaned_commands'):
        console.print("\n⚠️  Removed orphaned activations (no matching commands detected):")
        for drone_cmd in result['orphaned_commands']:
            console.print(f"   - drone {drone_cmd}")

    # Show all commands with status
    console.print(f"\n✅ System refreshed successfully")
    console.print()
    console.print(f"{'ID':<8}{'Command':<22}{'Module':<30}{'Status'}")
    console.print(f"{'-' * 6}  {'-' * 20}  {'-' * 28}  {'-' * 15}")

    for cmd in result['commands']:
        id_str = f"{cmd['id']:03d}"
        status = cmd['status']

        # Parse module:command format
        cmd_name = cmd['name']
        if ':' in cmd_name:
            module_name, command_name = cmd_name.split(':', 1)
        else:
            # Legacy format (no module prefix)
            module_name = ''
            command_name = cmd_name

        console.print(f"{id_str:<8}{command_name:<22}{module_name:<30}{status}")

    console.print()
    console.print(f"Total: {result['total_commands']} commands")
    console.print(f"New: {result['new_commands']} commands")

    if result['new_commands'] > 0:
        console.print(f"\n[yellow]💡 Use 'drone activate {result['system_name']}' to activate new commands[/yellow]")
    else:
        console.print("\n[yellow]💡 No new commands detected[/yellow]")

def format_edit_output(result: dict):
    """Format edit command output for display"""
    if result['error'] and result['error'] != 'Cancelled by user':
        console.print(f"❌ Error: {result['error']}")
    elif result['error'] == 'Cancelled by user':
        console.print("Cancelled")
    elif result['edited']:
        console.print(f"\n✅ Command {result['command_id']:03d} updated successfully")
        if result['changes']:
            console.print("\nChanges made:")
            for field, change in result['changes'].items():
                console.print(f"  {field}: '{change['old']}' → '{change['new']}'")
    else:
        console.print(f"\nℹ️  No changes made")
