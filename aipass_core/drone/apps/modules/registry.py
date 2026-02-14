#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: registry.py - Registry Management Module
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2025-11-13): PILOT MIGRATION - Orchestrator from drone_registry.py
#
# CODE STANDARDS:
#   - Thin orchestrator pattern - delegates to handlers in drone/apps/handlers/registry/
#   - Type hints on all functions
#   - Google-style docstrings
#   - Prax logger (system_logger as logger)
#   - CLI module for output (Rich console)
#   - Standard try/except error handling
# =============================================

"""
Registry Management Module

Orchestrates registry operations by coordinating multiple handlers.
Provides CLI interface for registry management and status.

Features:
- Load and heal registry
- Display registry status
- Show statistics
- Command line interface

Usage:
    python3 registry.py
    python3 registry.py --help
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header

# Import handlers
from drone.apps.handlers.registry import (
    load_registry,
    heal_registry,
    get_registry_statistics,
    get_command_count,
    get_module_count
)

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "registry"

# =============================================
# INTROSPECTION
# =============================================

def print_introspection():
    """Display module info and connected handlers"""
    console.print()
    console.print("[bold cyan]Registry Module - Command Registry Management[/bold cyan]")
    console.print()

    console.print("[yellow]Connected Handlers:[/yellow]")
    console.print()

    # Auto-discover handler files from handlers/registry/ directory
    handlers_dir = Path(__file__).parent.parent / "handlers" / "registry"

    if handlers_dir.exists():
        console.print("  [cyan]handlers/registry/[/cyan]")
        handler_files = sorted([
            f.name for f in handlers_dir.glob("*.py")
            if not f.name.startswith("_")
        ])
        for handler_file in handler_files:
            console.print(f"    [dim]- {handler_file}[/dim]")
        console.print()

    console.print("[dim]Run 'python3 registry.py --help' for usage information[/dim]")
    console.print()

# =============================================
# ORCHESTRATION
# =============================================

def handle_command(command: str, args: list) -> bool:
    """Handle registry management command

    Args:
        command: Command name
        args: Command arguments

    Returns:
        True if command was handled
    """
    # Registry only handles 'registry' command
    if command != "registry":
        return False

    try:
        # Load and heal registry
        registry = load_registry()
        healed = heal_registry()

        # Get statistics
        stats = get_registry_statistics()
        total_commands = get_command_count()
        total_modules = get_module_count()

        # Display status
        console.print()
        console.print("[green]✓[/green] Registry Status:")
        console.print(f"   [yellow]Commands:[/yellow] {total_commands}")
        console.print(f"   [yellow]Modules:[/yellow] {total_modules}")
        console.print(f"   [yellow]Healed:[/yellow] {'Yes' if healed else 'No'}")
        console.print(f"   [yellow]Total healings:[/yellow] {stats.get('auto_healing_count', 0)}")
        console.print()

        return True
    except Exception as e:
        logger.error(f"Error handling registry command: {e}")
        return False

# =============================================
# CLI ENTRY POINT
# =============================================

def print_help():
    """Display registry help using Rich formatting"""
    console.print()
    console.print("[bold cyan]Drone Registry Management[/bold cyan]")
    console.print()
    console.print("Manages the drone command registry with auto-healing capabilities")
    console.print()
    console.print("[yellow]Commands:[/yellow] registry, --help")
    console.print()
    console.print("[yellow]Usage:[/yellow]")
    console.print("  drone registry")
    console.print("  python3 registry.py")
    console.print("  python3 registry.py --help")
    console.print()
    console.print("[yellow]Features:[/yellow]")
    console.print("  • Load registry with auto-healing")
    console.print("  • Display command and module counts")
    console.print("  • Show healing statistics")
    console.print()

def main():
    """Main entry point for CLI"""
    import argparse

    args = sys.argv[1:]

    # Show introspection when run without arguments
    if len(args) == 0:
        print_introspection()
        sys.exit(0)

    # Show help only for explicit help flags
    if args[0] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    parser = argparse.ArgumentParser(
        description="Drone Registry Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 registry.py           # Show registry status
  python3 registry.py --help    # Show this help

Features:
  - Load registry with auto-healing
  - Display command and module counts
  - Show healing statistics
        """
    )

    args = parser.parse_args()

    success = handle_command("registry", [])
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
