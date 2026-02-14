#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: cortex.py - Cortex Main Orchestrator
# Date: 2025-11-15
# Version: 2.2.0
# Category: cortex
# Commands: create, update, delete, regenerate, --list, --help
#
# CHANGELOG (Max 5 entries):
#   - v2.2.0 (2025-11-15): Added drone compliance (Commands line in help)
#   - v2.1.0 (2025-11-04): Renamed from branch_operations to cortex
#   - v2.0.0 (2025-11-03): Restructured with modular architecture
#   - v1.0.0 (2025-10-29): Initial version
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Cortex - Main Orchestrator

Manages branch creation, updates, deletion, cleaning, and merging.
Modular architecture with auto-discovered modules.
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Standard library imports
import argparse
import importlib
from typing import List, Any

# Prax logger
from prax.apps.modules.logger import system_logger as logger

# CLI services for display
from cli.apps.modules import console

# JSON handler for cortex tracking
from cortex.apps.handlers.json import json_handler

# =============================================================================
# CONSTANTS
# =============================================================================

MODULE_ROOT = Path(__file__).parent.parent
MODULES_DIR = Path(__file__).parent / "modules"

# =============================================================================
# MODULE DISCOVERY
# =============================================================================

def discover_modules() -> List[Any]:
    """Auto-discover modules from modules/ directory (flat structure only)

    Modules must implement handle_command(args) -> bool

    Returns:
        List of module objects with handle_command function
    """
    modules = []

    if not MODULES_DIR.exists():
        logger.warning(f"[CORTEX] Modules directory not found: {MODULES_DIR}")
        return modules

    # Add modules directory to path
    sys.path.insert(0, str(MODULES_DIR))

    # Discover all .py files in modules/ directory (flat structure only)
    for file_path in MODULES_DIR.glob("*.py"):
        if file_path.name.startswith("_"):
            continue

        module_name = file_path.stem

        try:
            module = importlib.import_module(module_name)

            # Check if module has handle_command function
            if hasattr(module, 'handle_command'):
                modules.append(module)
                logger.info(f"[CORTEX] Loaded module: {module_name}")
            else:
                logger.info(f"[CORTEX] Skipped {module_name} - no handle_command()")

        except Exception as e:
            logger.error(f"[CORTEX] Failed to load module {module_name}: {e}")

    return modules

# =============================================================================
# COMMAND ROUTING
# =============================================================================

def route_command(args, modules: List[Any]) -> bool:
    """Route command to appropriate module

    Args:
        args: Command line arguments
        modules: List of discovered modules

    Returns:
        True if command was handled, False otherwise
    """
    # Check if help requested for specific module
    if args.command and ('--help' in sys.argv or '-h' in sys.argv):
        # Map commands to module names for direct lookup
        command_to_module = {
            'create-branch': 'create_branch',
            'create-team': 'create_team',
            'new-team': 'create_team',
            'update-branch': 'update_branch',
            'delete-branch': 'delete_branch',
            'regenerate-template-registry': 'regenerate_template_registry',
            'sync-registry': 'sync_registry',
        }

        # Find the module name for this command
        target_module_name = command_to_module.get(args.command)

        if target_module_name:
            # Find the module object and call its print_help
            for module in modules:
                if module.__name__ == target_module_name and hasattr(module, 'print_help'):
                    module.print_help()
                    return True

        # If no module matched, fall through to normal error handling
        return False

    # Normal command routing
    for module in modules:
        try:
            if module.handle_command(args):
                return True
        except Exception as e:
            logger.error(f"[CORTEX] Error in {module.__name__}: {e}")
            continue

    return False

# =============================================================================
# INTROSPECTION DISPLAY
# =============================================================================

def print_introspection():
    """Display discovered modules when run without arguments"""
    console.print()
    console.print("[bold cyan]CORTEX - Branch Management System[/bold cyan]")
    console.print()
    console.print("[dim]Manages branch creation, updates, deletion, and template registry[/dim]")
    console.print()

    # Discover modules
    modules = discover_modules()

    console.print(f"[yellow]Discovered Modules:[/yellow] {len(modules)}")
    console.print()

    for module in modules:
        module_name = module.__name__
        # Get description from module docstring if available
        description = module.__doc__.strip().split('\n')[0] if module.__doc__ else "No description"
        console.print(f"  [cyan]•[/cyan] {module_name} - [dim]{description}[/dim]")

    console.print()
    console.print("[dim]Run 'python3 cortex.py --help' for usage information[/dim]")
    console.print()


# =============================================================================
# DRONE COMPLIANCE - HELP SYSTEM
# =============================================================================

def print_help():
    """Display drone-compliant help output"""
    console.print()
    console.print("="*70)
    console.print("CORTEX - Branch Management System")
    console.print("="*70)
    console.print()
    console.print("Manages branch creation, updates, deletion, and template registry.")
    console.print()
    console.print("USAGE:")
    console.print("  python3 cortex.py <command> [arguments]")
    console.print()
    console.print("AVAILABLE COMMANDS:")
    console.print("  create-branch                Create new branch from template")
    console.print("  create-team                  Create new business team with workspace")
    console.print("  update-branch                Update existing branch from template")
    console.print("  delete-branch                Delete branch with backup")
    console.print("  regenerate-template-registry Regenerate template registry")
    console.print("  sync-registry                Sync branch registry with filesystem")
    console.print("  --list                       List available modules")
    console.print("  --help                       Show this help message")
    console.print()
    console.print("EXAMPLES:")
    console.print("  python3 cortex.py create-branch /path/to/new/branch")
    console.print("  python3 cortex.py update-branch /path/to/branch")
    console.print("  python3 cortex.py delete-branch /path/to/branch")
    console.print("  python3 cortex.py regenerate-template-registry")
    console.print("  python3 cortex.py sync-registry")
    console.print("  python3 cortex.py --list")
    console.print()
    console.print("="*70)
    console.print()
    console.print("Commands: create-branch, update-branch, delete-branch, regenerate-template-registry, sync-registry, --list, --help")
    console.print()

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point"""

    # Handle help flag before argparse
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        return 0

    parser = argparse.ArgumentParser(
        description='Cortex - Manage AIPass branches',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to use custom print_help()
        epilog="""
Commands: create-branch, update-branch, delete-branch, regenerate-template-registry, sync-registry, --list, --help

EXAMPLES:
  cortex create-branch /path/to/new/branch
  cortex update-branch /path/to/branch
  cortex delete-branch /path/to/branch
  cortex regenerate-template-registry
  cortex sync-registry
  cortex --list
        """
    )

    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('target_directory', nargs='?', help='Target directory for branch operations')
    parser.add_argument('--list', action='store_true', help='List available modules')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--all', dest='all_branches', action='store_true', help='Apply to all branches')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')

    # Parse known args to allow modules to define their own
    args, unknown = parser.parse_known_args()

    # Discover modules
    modules = discover_modules()

    # Log cortex startup
    json_handler.log_operation(
        "cortex_startup",
        {
            "modules_discovered": len(modules),
            "command": args.command if args.command else "introspection"
        },
        "cortex"
    )

    # Show introspection when run without arguments
    if not args.command and not args.list:
        print_introspection()
        return 0

    # Handle --list flag for compatibility
    if args.list:
        console.print("\nCortex - Available Modules:")
        if modules:
            for module in modules:
                module_name = module.__name__
                # Get description from module docstring if available
                description = module.__doc__.strip().split('\n')[0] if module.__doc__ else "No description"
                console.print(f"  {module_name} - {description}")
        else:
            console.print("  No modules found")
        console.print("\nImport modules directly or run with --help for more info")
        return 0

    # Route command to modules
    if route_command(args, modules):
        # Log successful command
        json_handler.log_operation(
            "command_routed_successfully",
            {"command": args.command},
            "cortex"
        )
        json_handler.increment_counter("cortex", "commands_successful")
        return 0
    else:
        # Log failed command
        logger.error(f"[CORTEX] No module handled command: {args.command}")
        console.print(f"Unknown command: {args.command}")
        console.print("Run with --list to see available modules")
        json_handler.log_operation(
            "command_not_handled",
            {"command": args.command},
            "cortex"
        )
        json_handler.increment_counter("cortex", "commands_failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
