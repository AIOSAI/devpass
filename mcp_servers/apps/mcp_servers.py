#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: mcp_servers.py - MCP_SERVERS Branch Orchestrator
# Date: 2025-11-22
# Version: 1.1.0
# Category: integration/mcp
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2025-11-22): Fixed META header - correct filename, category, and standards
#   - v1.0.0 (2025-11-08): Initial version - modular architecture
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
# =============================================

"""
mcp_servers Branch - Main Orchestrator

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
from cli.apps.modules import console, header
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

# Modules directory (apps/modules/)
MODULES_DIR = Path(__file__).parent / "modules"

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
    """Display discovered modules (no handlers shown at main level)"""
    console.print()
    console.print("[bold cyan]MCP_SERVERS - MCP Server Management[/bold cyan]")
    console.print()
    console.print("[dim]Model Context Protocol Server Integrations[/dim]")
    console.print()

    # Discover modules
    modules = discover_modules()

    console.print(f"[yellow]Discovered Modules:[/yellow] {len(modules)}")
    console.print()

    for module in modules:
        module_name = module.__name__.split('.')[-1]
        console.print(f"  [cyan]•[/cyan] {module_name}")

    console.print()
    console.print("[dim]Run 'python3 apps/mcp_servers.py --help' for usage information[/dim]")
    console.print()


# =============================================================================
# HELP DISPLAY
# =============================================================================

def print_help():
    """Display help information using Rich formatting"""

    header("MCP_SERVERS - MCP Server Management")
    console.print()

    console.print("[bold cyan]WHAT IS MCP_SERVERS?[/bold cyan]")
    console.print()
    console.print("The MCP_SERVERS branch manages Model Context Protocol (MCP) server")
    console.print("integrations within the AIPass ecosystem. It provides tools and")
    console.print("infrastructure for working with various MCP servers.")
    console.print()
    console.print("─" * 70)
    console.print()

    console.print("[bold cyan]AVAILABLE MCP SERVERS:[/bold cyan]")
    console.print()

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("Server", style="green")
    table.add_column("Description", style="white")

    table.add_row("Serena", "Project management and code navigation")
    table.add_row("Context7", "Documentation and library access")
    table.add_row("Playwright", "Browser automation")
    table.add_row("Sequential Thinking", "Step-by-step reasoning")

    console.print(table)
    console.print()
    console.print("─" * 70)
    console.print()

    console.print("[bold cyan]USAGE:[/bold cyan]")
    console.print()

    usage_examples = [
        "[yellow]Direct:[/yellow]\n  [dim]python3 apps/mcp_servers.py --help[/dim]",
        "[yellow]Via Drone:[/yellow]\n  [dim]drone @mcp_servers help[/dim]",
        "[yellow]Check Config:[/yellow]\n  [dim]cat /home/aipass/.mcp.json[/dim]"
    ]

    console.print(Columns(usage_examples, equal=True, expand=True))
    console.print()
    console.print("─" * 70)
    console.print()

    console.print("[bold cyan]CONFIGURATION:[/bold cyan]")
    console.print()
    console.print("  Global MCP config: [dim]/home/aipass/.mcp.json[/dim]")
    console.print("  Local branch path: [dim]/home/aipass/mcp_servers[/dim]")
    console.print()
    console.print("─" * 70)
    console.print()

    # Commands line required for drone discovery
    console.print("[dim]Commands: help, --help, -h[/dim]")
    console.print()

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point"""

    # Parse arguments manually to handle help before argparse
    args = sys.argv[1:]

    # Show introspection when run without arguments
    if len(args) == 0:
        print_introspection()
        return 0

    # Show help only for explicit help flags
    if args[0] in ['--help', '-h', 'help']:
        print_help()
        return 0

    # Parse remaining arguments with argparse
    parser = argparse.ArgumentParser(
        description='mcp_servers Branch Operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False  # Disable automatic help to use our custom handler
    )

    # Add your command line arguments here
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    parsed_args = parser.parse_args(args)

    # Discover modules
    modules = discover_modules()

    if not modules:
        console.print("❌ ERROR: No modules found")
        return 1

    # Route command
    if route_command(parsed_args, modules):
        return 0
    else:
        console.print(f"❌ ERROR: Unknown command: {parsed_args.command}")
        console.print()
        console.print("Run [dim]python3 apps/mcp_servers.py --help[/dim] for available commands")
        console.print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
