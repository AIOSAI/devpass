#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: backup_system.py - BACKUP_SYSTEM Branch Orchestrator
# Date: 2025-11-22
# Version: 1.1.0
# Category: core/backup
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2025-11-22): Fixed META header - correct filename, category, and standards
#   - v1.0.0 (2025-11-08): Initial version - modular architecture
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
# =============================================

"""
backup_system Branch - Main Orchestrator

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
from cli.apps.modules import console


# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

# Module root (same directory as this file)
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

    # Add apps directory to path FIRST so handler imports work
    # Modules use `from handlers.xxx import ...` which requires apps/ in sys.path
    if str(MODULE_ROOT) not in sys.path:
        sys.path.insert(0, str(MODULE_ROOT))

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
    """Display discovered modules - SEED pattern"""
    console.print()
    console.print("[bold cyan]Backup System - Automated File Protection[/bold cyan]")
    console.print()
    console.print("[dim]AIPass backup orchestration and versioning[/dim]")
    console.print()

    # Discover modules
    modules = discover_modules()

    console.print(f"[yellow]Discovered Modules:[/yellow] {len(modules)}")
    console.print()

    for module in modules:
        module_name = module.__name__ if hasattr(module, '__name__') else str(module)
        # Extract just the module filename (last part)
        if '.' in module_name:
            module_name = module_name.split('.')[-1]
        console.print(f"  [cyan]•[/cyan] {module_name}")

    console.print()
    console.print("[dim]Run 'python3 backup_system.py --help' for usage information[/dim]")
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

    # Check for --help flag before argparse to provide custom help
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        parser = argparse.ArgumentParser(
            description='backup_system Branch Operations',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        parser.add_argument('command', nargs='?', help='Command to execute')
        parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        parser.add_argument('--note', type=str, default='No note provided', help='Backup note/description')
        parser.add_argument('--dry-run', action='store_true', help='Scan files without copying (test mode)')
        console.print(parser.format_help())
        console.print("\nCommands: snapshot, versioned, drive-test, drive-sync, drive-stats, drive-clear-tracker\n")
        console.print("  snapshot          Create a system snapshot backup")
        console.print("  versioned         Create a versioned backup")
        console.print("  drive-test        Test Google Drive connectivity")
        console.print("  drive-sync        Sync backups to Google Drive")
        console.print("  drive-stats       Show Drive file tracker statistics")
        console.print("  drive-clear-tracker  Clear Drive file tracker cache")
        return 0

    parser = argparse.ArgumentParser(
        description='backup_system Branch Operations',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Add your command line arguments here
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('path', nargs='?', default=None, help='Path argument (for sync commands)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--note', type=str, default='No note provided', help='Backup note/description')
    parser.add_argument('--dry-run', action='store_true', help='Scan files without copying (test mode)')
    parser.add_argument('--project', type=str, default='AIPass', help='Project name for Drive sync')
    parser.add_argument('--force', action='store_true', help='Force sync all files')

    args = parser.parse_args()

    # Discover modules
    modules = discover_modules()

    if not modules:
        console.print("❌ ERROR: No modules found")
        return 1

    # If no command provided, show introspection
    if not args.command:
        print_introspection()
        return 0

    # Route command
    if route_command(args, modules):
        return 0
    else:
        console.print(f"❌ ERROR: Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
