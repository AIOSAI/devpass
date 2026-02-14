#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: permissions.py - permissions Branch Orchestrator
# Date: 2025-11-09
# Version: 1.1.0
# Category: permissions/apps
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2025-11-22): CLI standard compliance - fixed imports, added --help support
#   - v1.0.0 (2025-11-09): Initial version - modular architecture
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
#   - CLI: Rich formatting only, custom --help implementation
# =============================================

"""
permissions Branch - Main Orchestrator

Modular architecture with auto-discovered modules.
Main handles routing, modules implement functionality.
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Standard library imports
import argparse
import importlib
from typing import Dict, Any, Optional, List

# AIPass infrastructure imports
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header, success, error

# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

# Module root
MODULE_ROOT = Path(__file__).parent.parent

# Modules directory
MODULES_DIR = MODULE_ROOT / "modules"

# =============================================================================
# MODULE DISCOVERY
# =============================================================================

def discover_modules() -> List[Any]:
    """
    Auto-discover modules from modules/ directory

    Returns:
        List of module objects with handle_command() function
    """
    modules = []

    if not MODULES_DIR.exists():
        logger.warning(f"Modules directory not found: {MODULES_DIR}")
        return modules

    # Add modules directory to path
    sys.path.insert(0, str(MODULES_DIR))

    logger.info(f"[{Path(__file__).stem}] Discovering modules...")

    for file_path in MODULES_DIR.glob("*.py"):
        # Skip __init__.py and private files
        if file_path.name.startswith("_"):
            continue

        module_name = file_path.stem

        try:
            # Import module
            module = importlib.import_module(module_name)

            # Check for required interface
            if hasattr(module, 'handle_command'):
                modules.append(module)
                logger.info(f"  [+] {module_name}")
            else:
                logger.warning(f"  [!] {module_name} - missing handle_command()")

        except Exception as e:
            logger.error(f"  [-] {module_name} - import error: {e}")

    logger.info(f"[{Path(__file__).stem}] Discovered {len(modules)} modules")
    return modules

# =============================================================================
# COMMAND ROUTING
# =============================================================================

def route_command(args: argparse.Namespace, modules: List[Any]) -> bool:
    """
    Route command to appropriate module

    Args:
        args: Parsed command line arguments
        modules: List of discovered modules

    Returns:
        True if command was handled
    """
    for module in modules:
        try:
            if module.handle_command(args):
                return True
        except Exception as e:
            logger.error(f"Module error: {e}")

    return False

# =============================================================================
# INTROSPECTION DISPLAY
# =============================================================================

def print_introspection():
    """Display discovered modules (not handlers - that's module-level)"""
    console.print()
    console.print("[bold cyan]Permissions Branch - Permissions Management[/bold cyan]")
    console.print()
    console.print("[dim]AIPass permissions management system[/dim]")
    console.print()

    # Discover modules
    modules = discover_modules()

    console.print(f"[yellow]Discovered Modules:[/yellow] {len(modules)}")
    console.print()

    for module in modules:
        module_name = module.__name__.split('.')[-1] if hasattr(module, '__name__') else str(module)
        console.print(f"  [cyan]•[/cyan] {module_name}")

    console.print()
    console.print("[dim]Run 'python3 permissions.py --help' for usage information[/dim]")
    console.print()


# =============================================================================
# HELP DISPLAY
# =============================================================================

def print_help():
    """Display Rich-formatted help"""
    console.print()
    header("Permissions Branch Operations")
    console.print()
    console.print("[dim]AIPass permissions management system[/dim]")
    console.print()
    console.print("─" * 70)
    console.print()

    console.print("[bold cyan]USAGE:[/bold cyan]")
    console.print()
    console.print("  python3 permissions.py <command> [options]")
    console.print()

    console.print("[bold cyan]OPTIONS:[/bold cyan]")
    console.print()
    console.print("  [green]--help, -h[/green]     Show this help message")
    console.print("  [green]--verbose, -v[/green]  Verbose output")
    console.print()

    console.print("[bold cyan]COMMANDS:[/bold cyan]")
    console.print()
    console.print("  Commands are auto-discovered from modules/ directory")
    console.print("  Run without arguments to see available modules")
    console.print()

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point"""
    # Show introspection when run without arguments
    if len(sys.argv) == 1:
        print_introspection()
        return 0

    # Handle --help flag before argparse (Drone compliance)
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        return 0

    parser = argparse.ArgumentParser(
        description='permissions Branch Operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False  # Disable argparse help to use custom Rich help
    )

    # Add your command line arguments here
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Discover modules
    modules = discover_modules()

    if not modules:
        console.print("❌ ERROR: No modules found")
        return 1

    # Route command
    if route_command(args, modules):
        return 0
    else:
        console.print(f"❌ ERROR: Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
