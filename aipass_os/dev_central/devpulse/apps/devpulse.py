#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: devpulse.py - DEVPULSE Branch Entry Point
# Date: 2025-11-16
# Version: 1.0.0
# Category: Branch Entry
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-16): Seed-compliant architecture with introspection
#
# CODE STANDARDS:
#   - Follows seed.py pattern: sys.argv, introspection, no argparse
#   - Auto-discovers modules with handle_command() interface
# =============================================

"""
DEVPULSE Branch - Development Tracking Entry Point

Manages dev.local.md tracking across AIPass branches.
Auto-discovers modules and routes commands.
"""

import sys
from pathlib import Path
from typing import List, Any
import importlib

# =============================================================================
# INFRASTRUCTURE SETUP
# =============================================================================

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header

# =============================================================================
# INTROSPECTION DISPLAY
# =============================================================================

def print_introspection():
    """Display discovered modules and handlers when run without arguments"""
    console.print()
    console.print("[bold cyan]DEVPULSE - Development Tracking[/bold cyan]")
    console.print()
    console.print("[dim]Manages dev.local.md tracking across AIPass branches[/dim]")
    console.print()

    # Discover modules
    modules = discover_modules()

    console.print(f"[yellow]Discovered Modules:[/yellow] {len(modules)}")
    console.print()

    for module in modules:
        module_name = module.__name__.split('.')[-1]
        console.print(f"  [cyan]•[/cyan] {module_name}")

    console.print()
    console.print("[dim]Run 'python3 devpulse.py --help' for usage information[/dim]")
    console.print()


def print_help():
    """Display detailed help"""
    console.print()
    header("DEVPULSE - Development Tracking")
    console.print()

    console.print("[bold cyan]USAGE:[/bold cyan]")
    console.print()
    console.print("  python3 devpulse.py <command> [args]")
    console.print()
    console.print("─" * 70)
    console.print()

    console.print("[bold cyan]AVAILABLE COMMANDS:[/bold cyan]")
    console.print()

    # Discover modules and show their commands
    modules = discover_modules()

    for module in modules:
        module_name = module.__name__.split('.')[-1]
        console.print(f"  [green]{module_name}[/green]")

        # Try to get commands from module
        if hasattr(module, '__doc__') and module.__doc__:
            doc_lines = module.__doc__.strip().split('\n')
            if len(doc_lines) > 0:
                console.print(f"    [dim]{doc_lines[0].strip()}[/dim]")

        console.print()

    console.print("─" * 70)
    console.print()

    console.print("[bold cyan]EXAMPLES:[/bold cyan]")
    console.print()
    console.print("  # Show module help")
    console.print("  [dim]python3 devpulse.py dev --help[/dim]")
    console.print()
    console.print("  # List available sections")
    console.print("  [dim]python3 devpulse.py dev sections[/dim]")
    console.print()
    console.print("  # Add entry to branch")
    console.print("  [dim]python3 devpulse.py dev add @flow \"Issues\" \"Bug found\"[/dim]")
    console.print()
    console.print("  # Check compliance")
    console.print("  [dim]python3 devpulse.py dev status @flow[/dim]")
    console.print()

    console.print("─" * 70)
    console.print()
    console.print("[dim]Commands: dev, track, help, --help[/dim]")
    console.print()


# =============================================================================
# MODULE DISCOVERY
# =============================================================================

MODULES_DIR = Path(__file__).parent / "modules"

def discover_modules() -> List[Any]:
    """Auto-discover modules from modules/ directory"""
    modules = []

    if not MODULES_DIR.exists():
        return modules

    for file_path in MODULES_DIR.glob("*.py"):
        if file_path.name.startswith("_"):
            continue

        module_name = f"aipass_os.dev_central.devpulse.apps.modules.{file_path.stem}"

        try:
            module = importlib.import_module(module_name)

            if hasattr(module, 'handle_command'):
                modules.append(module)
                logger.info(f"Discovered module: {module_name}")
        except Exception as e:
            logger.error(f"Failed to load module {module_name}: {e}")

    return modules


def route_command(command: str, args: List[str], modules: List[Any]) -> bool:
    """Route command to appropriate module"""
    for module in modules:
        try:
            if module.handle_command(command, args):
                return True
        except Exception as e:
            logger.error(f"Module {module.__name__} error: {e}")

    return False


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point - routes commands or shows help"""

    # Parse arguments (sys.argv style, not argparse)
    args = sys.argv[1:]

    # Show introspection when run without arguments
    if len(args) == 0:
        print_introspection()
        return

    # Show help for explicit help flags
    if args[0] in ['--help', '-h', 'help']:
        print_help()
        return

    # Command provided - try to route to modules
    modules = discover_modules()
    command = args[0]
    remaining_args = args[1:] if len(args) > 1 else []

    if route_command(command, remaining_args, modules):
        return  # Module handled it successfully
    else:
        console.print()
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print()
        console.print("Run [dim]python3 devpulse.py --help[/dim] for available commands")
        console.print()
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"DEVPULSE entry point error: {e}", exc_info=True)
        console.print(f"\n❌ Error: {e}")
        sys.exit(1)
