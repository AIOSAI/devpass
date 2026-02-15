#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: vscode.py - VSCODE Branch Orchestrator
# Date: 2025-11-22
# Version: 1.1.0
# Category: dev/vscode
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2025-11-22): Fixed imports, added CLI services, updated standards
#   - v1.0.0 (2025-11-10): Initial version - modular architecture
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
# =============================================

"""
.vscode Branch - Main Orchestrator

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

# Prax logger
from prax.apps.modules.logger import system_logger as logger

# CLI services
from cli.apps.modules import console, header

# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

# Module root (apps directory)
MODULE_ROOT = Path(__file__).parent

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
    """Display discovered modules and handlers"""
    console.print()
    console.print("[bold cyan].vscode - VS Code Branch Operations[/bold cyan]")
    console.print()
    console.print("[dim]Performance monitoring and VS Code tooling[/dim]")
    console.print()

    # Discover modules
    modules = discover_modules()

    console.print(f"[yellow]Discovered Modules:[/yellow] {len(modules)}")
    console.print()

    for module in modules:
        module_name = module.__name__.split('.')[-1]
        console.print(f"  [cyan]•[/cyan] {module_name}")

    console.print()
    console.print("[dim]Run 'python3 vscode.py --help' for usage information[/dim]")
    console.print()


# =============================================================================
# HELP
# =============================================================================

def print_help():
    """Print help information"""
    console.print()
    header(".vscode Branch Operations")
    console.print()
    console.print("[dim]VS Code tooling and performance monitoring[/dim]")
    console.print()
    console.print("─" * 60)
    console.print()

    console.print("[bold cyan]USAGE:[/bold cyan]")
    console.print()
    console.print("  python3 vscode.py <command> [options]")
    console.print("  vscode.py <command> [options]")
    console.print()

    console.print("[bold cyan]OPTIONS:[/bold cyan]")
    console.print()
    console.print("  [cyan]--help, help[/cyan]  Show this help message")
    console.print("  [cyan]--verbose, -v[/cyan]  Verbose output")
    console.print()

    console.print("[bold cyan]COMMANDS:[/bold cyan]")
    console.print()
    console.print("  Auto-discovered from modules/ directory")
    console.print("  Run without arguments to see discovered modules")
    console.print()
    console.print("─" * 60)
    console.print()

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point - routes commands or shows help"""

    # Parse arguments
    args = sys.argv[1:]

    # Show introspection when run without arguments
    if len(args) == 0:
        print_introspection()
        return

    # Show help only for explicit help flags
    if args[0] in ['--help', '-h', 'help']:
        print_help()
        return

    # Command provided - try to route to modules
    parser = argparse.ArgumentParser(
        description='.vscode Branch Operations',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('command', help='Command to execute')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    parsed_args = parser.parse_args(args)

    # Discover modules
    modules = discover_modules()

    if not modules:
        console.print()
        console.print("[red]ERROR: No modules found[/red]")
        console.print()
        return 1

    # Route command
    if route_command(parsed_args, modules):
        return 0
    else:
        console.print()
        console.print(f"[red]Unknown command: {parsed_args.command}[/red]")
        console.print()
        console.print("Run [dim]python3 vscode.py --help[/dim] for available commands")
        console.print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
