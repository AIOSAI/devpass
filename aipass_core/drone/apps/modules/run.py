#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: run.py - Run Module for Python Module Execution
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-29): Extracted from drone.py - handles 'drone run python3 <module> [args]'
#
# CODE STANDARDS:
#   - Seed pattern compliance - console.print() for all output
#   - Type hints on all functions
#   - Google-style docstrings
#   - Prax logger (system_logger as logger)
# =============================================

"""
Run Module - Execute Python modules with path resolution

Handles the 'drone run python3 <module.py> [args]' command.
Resolves module paths automatically from known locations.

Usage:
    drone run python3 flow.py close --all
    drone run python3 seed.py checklist
"""

# =============================================
# IMPORTS
# =============================================

import subprocess
import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "run"
ECOSYSTEM_ROOT = Path.home()  # /home/aipass

# =============================================
# PATH RESOLUTION
# =============================================

def resolve_module_path(module_name: str) -> Path | None:
    """
    Find a module by name, searching known locations.

    Args:
        module_name: e.g., "flow.py" or "seed.py"

    Returns:
        Full path to module or None if not found
    """
    # Strip .py if present for searching
    base_name = module_name.replace('.py', '')
    search_name = f"{base_name}.py"

    # Search locations: /home/aipass/*/apps/ and /home/aipass/aipass_core/*/apps/
    search_paths = [
        ECOSYSTEM_ROOT,
        ECOSYSTEM_ROOT / "aipass_core"
    ]

    for root in search_paths:
        if not root.exists():
            continue
        for branch_dir in root.iterdir():
            if branch_dir.is_dir() and not branch_dir.name.startswith('.'):
                apps_path = branch_dir / "apps" / search_name
                if apps_path.exists():
                    return apps_path

    return None


# =============================================
# INTROSPECTION
# =============================================

def print_introspection():
    """Display module info"""
    console.print()
    console.print("[bold cyan]Run Module - Python Module Execution[/bold cyan]")
    console.print()
    console.print("[dim]Executes Python modules with automatic path resolution.[/dim]")
    console.print()
    console.print("[yellow]Search Locations:[/yellow]")
    console.print("  ~/*/apps/")
    console.print("  ~/aipass_core/*/apps/")
    console.print()
    console.print("[dim]Run 'drone run --help' for usage information[/dim]")
    console.print()


# =============================================
# ORCHESTRATION
# =============================================

def handle_command(command: str, args: list) -> bool:
    """
    Handle 'run' command

    Args:
        command: Command name (should be 'run')
        args: Command arguments [python3, module.py, ...]

    Returns:
        True if handled, False otherwise
    """
    if command != "run":
        return False

    try:
        # No args - show usage
        if not args:
            console.print("[yellow]Usage: drone run python3 <module.py> [args][/yellow]")
            console.print()
            console.print("  Resolves module paths automatically.")
            console.print("  Example: [dim]drone run python3 flow.py close --all[/dim]")
            return True

        # Expect: python3 module.py [args]
        if args[0] != 'python3' or len(args) < 2:
            console.print("[red]Usage: drone run python3 <module.py> [args][/red]")
            return True

        module_name = args[1]
        module_args = args[2:] if len(args) > 2 else []

        # Resolve module path
        module_path = resolve_module_path(module_name)

        if not module_path:
            console.print(f"[red]Module not found: {module_name}[/red]")
            console.print()
            console.print("[dim]Searched in:[/dim]")
            console.print("  ~/*/apps/")
            console.print("  ~/aipass_core/*/apps/")
            return True

        # Build and execute command
        cmd = ['python3', str(module_path)] + module_args

        console.print(f"[dim]-> python3 {module_path.relative_to(ECOSYSTEM_ROOT)} {' '.join(module_args)}[/dim]")
        console.print()

        result = subprocess.run(cmd, cwd=ECOSYSTEM_ROOT)
        logger.info(f"Executed module: {module_path} with args: {module_args}, exit code: {result.returncode}")
        return True

    except Exception as e:
        logger.error(f"Error executing run command: {e}", exc_info=True)
        console.print(f"[red]Error: {e}[/red]")
        return True


# =============================================
# HELP SYSTEM
# =============================================

def print_help():
    """Display help using Rich formatted output"""
    console.print()
    console.print("[bold cyan]Run Module - Python Module Execution[/bold cyan]")
    console.print()
    console.print("[yellow]USAGE:[/yellow]")
    console.print("  drone run python3 <module.py> [args]")
    console.print()
    console.print("[yellow]EXAMPLES:[/yellow]")
    console.print("  drone run python3 flow.py close --all")
    console.print("  drone run python3 seed.py checklist")
    console.print("  drone run python3 backup_system.py --help")
    console.print()
    console.print("[yellow]SEARCH LOCATIONS:[/yellow]")
    console.print("  ~/*/apps/             (e.g., ~/seed/apps/seed.py)")
    console.print("  ~/aipass_core/*/apps/ (e.g., ~/aipass_core/flow/apps/flow.py)")
    console.print()


# =============================================
# MAIN ENTRY
# =============================================

def main():
    """Main entry point for testing"""
    args = sys.argv[1:]

    # Show introspection when run without arguments
    if len(args) == 0:
        print_introspection()
        return

    # Show help only for explicit help flags
    if args[0] in ['--help', '-h', 'help']:
        print_help()
        return

    # Handle as command
    command = args[0]
    remaining_args = args[1:]

    # If run directly, the command is the first arg after module name
    # Support: python3 run.py python3 flow.py list
    if command == 'python3':
        # Called as: python3 run.py python3 module.py args
        handled = handle_command('run', args)
    else:
        handled = handle_command(command, remaining_args)

    if not handled:
        console.print()
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print()
        console.print("[dim]Run 'python3 run.py --help' for available commands[/dim]")
        console.print()
        sys.exit(1)


if __name__ == "__main__":
    main()
