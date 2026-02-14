#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: discovery.py - Discovery Orchestrator Module
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2025-11-13): BEAST MIGRATION - Orchestrator created from drone_discovery.py (2,289 lines → 128 lines)
#   - v1.0.0 (2025-10-16): Original monolithic implementation
#
# CODE STANDARDS:
#   - Thin orchestrator pattern - delegates to handlers in drone/apps/handlers/discovery/
#   - Type hints on all functions
#   - Google-style docstrings
#   - Prax logger (system_logger as logger)
#   - CLI module for output (Rich console)
#   - Standard try/except error handling
# =============================================

"""
Discovery Orchestrator Module

Thin orchestration layer that coordinates discovery handlers. Delegates all business
logic to handlers in drone/apps/handlers/discovery/.

Commands:
- scan: Scan module for commands
- register: Register module commands
- activate: Activate commands interactively
- list: List activated commands
- systems: List registered systems
- remove: Remove activated command
- refresh: Refresh system
- edit: Edit activated command
- help: Show help for target

Usage:
    python3 discovery.py scan @flow
    python3 discovery.py register @flow
    python3 discovery.py activate flow
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

# CLI services for formatted output
from cli.apps.modules import console, header

# Import all handlers
from drone.apps.handlers.discovery import (
    # Scanning
    scan_module,
    resolve_system_name,
    # Registration
    register_module,
    # Activation
    activate_commands_interactive,
    # System operations
    list_all_systems,
    list_activated_commands,
    remove_activated_command,
    refresh_system,
    edit_activated_command_interactive,
    # Formatters
    format_scan_output,
    format_registration_output,
    format_activation_summary,
    format_systems_output,
    format_list_output,
    format_remove_output,
    format_refresh_output,
    format_edit_output,
    # Help display
    show_help_for_target,
    # Path resolution (for entry point)
    resolve_scan_path,
    run_branch_module,
    resolve_slash_pattern,
    is_long_running_command,
)

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "discovery"

# =============================================
# INTROSPECTION
# =============================================

def print_introspection():
    """Display module info and connected handlers"""
    console.print()
    console.print("[bold cyan]Discovery Module - Runtime Command Discovery[/bold cyan]")
    console.print()

    console.print("[yellow]Connected Handlers:[/yellow]")
    console.print()

    # Auto-discover handler files from handlers/discovery/ directory
    handlers_dir = Path(__file__).parent.parent / "handlers" / "discovery"

    if handlers_dir.exists():
        console.print("  [cyan]handlers/discovery/[/cyan]")
        handler_files = sorted([
            f.name for f in handlers_dir.glob("*.py")
            if not f.name.startswith("_")
        ])
        for handler_file in handler_files:
            console.print(f"    [dim]- {handler_file}[/dim]")
        console.print()

    console.print("[dim]Run 'python3 discovery.py --help' for usage information[/dim]")
    console.print()

# =============================================
# ORCHESTRATION
# =============================================

def handle_command(command: str, args: list) -> bool:
    """
    Handle discovery commands

    Args:
        command: Command name
        args: Command arguments

    Returns:
        True if handled, False otherwise
    """
    try:
        # SCAN command (now auto-registers and prompts for activation)
        if command == "scan":
            # Parse --all flag
            show_python_cmds = '--all' in args
            filtered_args = [a for a in args if a != '--all']

            if len(filtered_args) < 1:
                console.print("[yellow]Usage: drone scan [@module] [--all][/yellow]")
                console.print()
                console.print("  [dim]--all[/dim]  Show Python commands (for testing/debugging)")
                return True

            module_path = filtered_args[0]

            # Validate @ prefix before calling scan_module
            if not module_path.startswith('@'):
                console.print("[yellow]Usage: drone scan @module [--all][/yellow]")
                console.print()
                console.print(f"  [red]Got:[/red] '{module_path}' [dim](missing @ prefix)[/dim]")
                console.print()
                console.print("  [dim]Examples:[/dim]")
                console.print("    drone scan @devpulse")
                console.print("    drone scan @flow --all")
                return True

            # Step 1: Scan
            result = scan_module(module_path)
            format_scan_output(result, show_full_command=show_python_cmds)

            # Step 2: Auto-register if scan successful
            if result['success'] and result['commands']:
                console.print()
                reg_result = register_module(module_path)

                if reg_result['success']:
                    total = len(reg_result['commands'])
                    new_count = reg_result.get('new_commands', 0)

                    if new_count > 0:
                        console.print(f"[green]✅ Registered {new_count} new commands ({total} total)[/green]")
                    else:
                        console.print(f"[green]✅ Already registered ({total} total)[/green]")

                    # Step 3: Prompt to activate
                    console.print()
                    console.print("[cyan]Activate commands now?[/cyan] [dim][Y/n]:[/dim] ", end='')
                    try:
                        user_input = input().strip().lower()
                    except EOFError:
                        user_input = 'y'
                        console.print("y [dim](auto, non-interactive)[/dim]")

                    if user_input != 'n':
                        console.print()
                        system_name = resolve_system_name(module_path)
                        activate_result = activate_commands_interactive(system_name)
                        format_activation_summary(system_name, activate_result)
                else:
                    console.print(f"[red]❌ Registration failed: {reg_result.get('error', 'Unknown error')}[/red]")

            return True

        # REGISTER command (now optional/deprecated, but kept for backward compatibility)
        elif command == "register" or command == "reg":
            if len(args) < 1:
                console.print("[yellow]Usage: discovery register <module_path>[/yellow]")
                console.print("[dim]💡 Tip: 'drone scan' now auto-registers. Use that instead![/dim]")
                return True

            result = register_module(args[0])
            format_registration_output(result)
            return True

        # ACTIVATE command
        elif command == "activate":
            if len(args) < 1:
                console.print("[yellow]Usage: discovery activate <system_name>[/yellow]")
                return True

            # Resolve system name (handles @seed → seed)
            system_name = resolve_system_name(args[0])
            result = activate_commands_interactive(system_name)
            format_activation_summary(system_name, result)
            return True

        # LIST command
        elif command == "list":
            # Support optional system filter: drone list @prax OR drone list prax
            system_filter = None
            if args:
                # Accept both @system and system format
                system_filter = args[0].lstrip('@')

            result = list_activated_commands(system_filter)
            format_list_output(result)
            return True

        # SYSTEMS command
        elif command == "systems":
            result = list_all_systems()
            format_systems_output(result)
            return True

        # REMOVE command
        elif command == "remove":
            if len(args) < 1:
                console.print("[yellow]Usage: discovery remove <drone_command>[/yellow]")
                return True

            result = remove_activated_command(args[0])
            format_remove_output(result)
            return True

        # REFRESH command
        elif command == "refresh":
            if len(args) < 1:
                console.print("[yellow]Usage: discovery refresh <system_name>[/yellow]")
                return True

            # Resolve system name (handles @seed → seed)
            system_name = resolve_system_name(args[0])
            result = refresh_system(system_name)
            format_refresh_output(result)
            return True

        # EDIT command
        elif command == "edit":
            result = edit_activated_command_interactive()
            format_edit_output(result)
            return True

        # HELP command
        elif command == "help":
            if len(args) < 1:
                console.print("[yellow]Usage: discovery help <target>[/yellow]")
                return True

            success = show_help_for_target(args[0])
            if not success:
                console.print(f"[red]Target not found: {args[0]}[/red]")
            return True

        return False

    except Exception as e:
        logger.error(f"Error handling command '{command}': {str(e)}", exc_info=True)
        console.print(f"[red]Error executing command: {str(e)}[/red]")
        return True

# =============================================
# HELP SYSTEM
# =============================================

def print_help():
    """Display help using Rich formatted output"""
    console.print()
    console.print("[bold cyan]Discovery Module - Runtime Command Discovery[/bold cyan]")
    console.print()

    console.print("[yellow]COMMANDS:[/yellow]")
    console.print("  [cyan]scan[/cyan]         Scan module for commands")
    console.print("  [cyan]register[/cyan]     Register module commands")
    console.print("  [cyan]activate[/cyan]     Activate commands interactively")
    console.print("  [cyan]list[/cyan]         List activated commands (optionally filter with @system)")
    console.print("  [cyan]systems[/cyan]      List registered systems")
    console.print("  [cyan]remove[/cyan]       Remove activated command")
    console.print("  [cyan]refresh[/cyan]      Refresh system")
    console.print("  [cyan]edit[/cyan]         Edit activated command")
    console.print("  [cyan]help[/cyan]         Show help for target")
    console.print()

    console.print("[yellow]USAGE:[/yellow]")
    console.print("  drone scan @flow")
    console.print("  drone list              # All activated commands")
    console.print("  drone list @prax        # Only prax commands")
    console.print("  drone activate flow")
    console.print("  python3 discovery.py scan @flow")
    console.print("  python3 discovery.py register @flow")
    console.print("  python3 discovery.py activate flow")
    console.print()

# =============================================
# MAIN ENTRY
# =============================================

def main():
    """Main entry point for testing"""
    import sys

    # Handle help flags
    args = sys.argv[1:]

    # Show introspection when run without arguments
    if len(args) == 0:
        print_introspection()
        return True

    # Show help only for explicit help flags
    if args[0] in ['--help', '-h', 'help']:
        print_help()
        return True

    command = sys.argv[1]
    args = sys.argv[2:]

    handled = handle_command(command, args)

    if not handled:
        console.print()
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print()
        console.print("[yellow]Available Commands:[/yellow]")
        console.print("  [cyan]scan[/cyan]         Scan module for commands")
        console.print("  [cyan]register[/cyan]     Register module commands")
        console.print("  [cyan]activate[/cyan]     Activate commands interactively")
        console.print("  [cyan]list[/cyan]         List activated commands")
        console.print("  [cyan]systems[/cyan]      List registered systems")
        console.print("  [cyan]remove[/cyan]       Remove activated command")
        console.print("  [cyan]refresh[/cyan]      Refresh system")
        console.print("  [cyan]edit[/cyan]         Edit activated command")
        console.print("  [cyan]help[/cyan]         Show help for target")
        console.print()
        console.print("[dim]Commands: scan, register, activate, list, systems, remove, refresh, edit, help[/dim]")
        console.print()
        sys.exit(1)

if __name__ == "__main__":
    main()
