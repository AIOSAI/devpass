#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: error_handling_standard.py - Error Handling Standards Module
# Date: 2025-11-12
# Version: 0.1.0
# Category: seed/standards
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-12): Initial standards module - error handling
#
# CODE STANDARDS:
#   - This module provides error handling standards when queried
# =============================================

"""
Error Handling Standards Module

Provides condensed error handling standards for AIPass branches.
Run directly or via: drone seed errors
"""

import sys
import argparse
from pathlib import Path
from typing import List

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))  # For seed package imports

from prax.apps.modules.logger import system_logger as logger
from seed.apps.handlers.json import json_handler
from seed.apps.handlers.standards.error_handling_content import get_error_handling_standards

# Import CLI services (Rich console + display functions)
from cli.apps.modules import console, header


def print_introspection():
    """Display module info and connected handlers"""
    from pathlib import Path

    console.print()
    console.print("[bold cyan]Error Handling Standards Module[/bold cyan]")
    console.print()

    console.print("[yellow]Connected Handlers:[/yellow]")
    console.print()

    # Auto-discover handler files from handlers/standards/
    handlers_dir = Path(__file__).parent.parent / "handlers" / "standards"

    if handlers_dir.exists():
        # Only show files this module actually uses
        console.print("  [cyan]handlers/standards/[/cyan]")
        console.print("    [dim]- error_handling_content.py[/dim]")
        console.print()

    console.print("[dim]Run 'python3 error_handling_standard.py --help' for usage[/dim]")
    console.print()


def print_help():
    """Print drone-compliant help output"""
    parser = argparse.ArgumentParser(
        description='Error Handling Standards Module - AIPass Error Handling Patterns',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: error_handling, errors, error, --help

  error_handling - Display error handling standards
  errors         - Display error handling standards (alias)
  error          - Display error handling standards (alias)

USAGE:
  drone seed errors
  python3 error_handling_standard.py
  python3 error_handling_standard.py --help

EXAMPLES:
  # Via drone
  drone seed errors

  # Standalone
  python3 error_handling_standard.py

REFERENCE:
  /home/aipass/standards/CODE_STANDARDS/error_handling.md
        """
    )
    parser.print_help()


def handle_command(command: str, args: List[str]) -> bool:
    """Handle 'errors' command"""
    if command not in ["errors", "error", "error_handling"]:
        return False

    # Log module usage - triggers JSON auto-creation
    json_handler.log_operation(
        "standard_displayed",
        {"command": command}
    )

    print_standard()
    return True


def print_standard():
    """Print error handling standards - orchestrates handler call"""
    console.print()
    header("Error Handling Standards")
    console.print()
    console.print(get_error_handling_standards())
    console.print()
    console.print("─" * 70)
    console.print()


if __name__ == "__main__":
    # Show introspection when run without arguments
    if len(sys.argv) == 1:
        print_introspection()
        sys.exit(0)

    # Handle help flag (drone compliance)
    if sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    # Confirm Prax logger connection
    logger.info("Prax logger connected to error_handling_standard")

    # Log standalone execution - triggers JSON auto-creation
    json_handler.log_operation(
        "standard_displayed",
        {"command": "standalone"}
    )
    print_standard()
