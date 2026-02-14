#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: aipass.py - AIPASS Branch Orchestrator
# Date: 2025-11-09
# Version: 1.0.0
# Category: Orchestrator
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-09): Initial version - modular architecture
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
aipass Branch - Main Orchestrator

Modular architecture with auto-discovered modules.
Main handles routing, modules implement functionality.
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / 'aipass_core'
sys.path.insert(0, str(AIPASS_ROOT))

# Standard library imports
import argparse
import importlib
from typing import Dict, Any, Optional, List

# AIPass infrastructure imports
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header

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
    console.print("[bold cyan]AIPASS - Main Branch Orchestrator[/bold cyan]")
    console.print()
    console.print("[dim]Main orchestrator for AIPass ecosystem[/dim]")
    console.print()

    # Discover modules
    modules = discover_modules()

    console.print(f"[yellow]Discovered Modules:[/yellow] {len(modules)}")
    console.print()

    for module in modules:
        module_name = module.__name__.split('.')[-1] if hasattr(module, '__name__') else str(module)
        console.print(f"  [cyan]•[/cyan] {module_name}")

    console.print()
    console.print("[dim]Run 'python3 aipass.py --help' for usage information[/dim]")
    console.print()


# =============================================================================
# MAIN
# =============================================================================

def print_help():
    """Print help message with drone-compliant format"""
    console.print()
    header("AIPASS Branch Operations")
    console.print()
    console.print("Main orchestrator for AIPass ecosystem")
    console.print()
    console.print("─" * 50)
    console.print()
    console.print("[bold cyan]USAGE:[/bold cyan]")
    console.print("  aipass <command> [options]")
    console.print()
    console.print("[bold cyan]COMMANDS:[/bold cyan]")
    console.print("  coordinate   Coordinate branch operations")
    console.print("  deploy       Deploy new features")
    console.print("  status       Show branch status")
    console.print("  --help       Show this help message")
    console.print()
    console.print("[bold cyan]OPTIONS:[/bold cyan]")
    console.print("  --verbose, -v    Verbose output")
    console.print("  --help           Show this help message")
    console.print()
    console.print("─" * 50)
    console.print()
    console.print("[dim]Commands: coordinate, deploy, status, --help[/dim]")
    console.print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='aipass Branch Operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )

    # Add your command line arguments here
    parser.add_argument('command', nargs='?', default=None, help='Command to execute')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--help', '-h', action='store_true', help='Show help message')

    args = parser.parse_args()

    # Handle help flag
    if args.help or args.command == '--help' or args.command == 'help':
        print_help()
        return 0

    # Show introspection when run without arguments
    if not args.command:
        print_introspection()
        return 0

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
