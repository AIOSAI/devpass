#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: status_module.py - PRAX Status Command
# Date: 2025-11-15
# Version: 1.0.0
# Category: prax/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-15): Created with handle_command interface
#
# CODE STANDARDS:
#   - Follows AIPass Prax standards
#   - Implements handle_command(command: str, args: List[str]) -> bool interface
#   - Uses Prax logger for system-wide logging
# =============================================

"""
PRAX Status Module

Implements the 'status' command using handle_command interface.
"""

import sys
from pathlib import Path
from typing import List

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import get_system_status, system_logger as logger
from cli.apps.modules import console, header, success, error


def print_introspection():
    """Display module introspection - shows connected handlers"""
    console.print()
    console.print("[bold cyan]PRAX Status Module[/bold cyan]")
    console.print()
    console.print("[yellow]Connected Handlers:[/yellow]")
    console.print()

    console.print("  [cyan]prax/modules/[/cyan]")
    console.print("    [dim]- logger.py[/dim] (get_system_status, system_logger)")
    console.print()

    console.print("[dim]Run 'python3 status_module.py --help' for usage[/dim]")
    console.print()


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle status command

    Args:
        command: Command name
        args: Command arguments

    Returns:
        True if command was handled
    """
    if command != 'status':
        return False

    status = get_system_status()

    console.print("\n📊 PRAX System Status")
    console.print("=" * 60)
    console.print(f"Total Modules: {status['total_modules']}")
    console.print(f"Active Loggers: {status['individual_loggers']}")
    console.print(f"System Logs Dir: {status['system_logs_dir']}")
    console.print(f"Registry File: {status['registry_file']}")
    console.print(f"File Watcher: {'🟢 Active' if status['file_watcher_active'] else '🔴 Inactive'}")
    console.print(f"Logger Override: {'🟢 Active' if status['logger_override_active'] else '🔴 Inactive'}")
    console.print("=" * 60 + "\n")
    return True


if __name__ == "__main__":
    # Show introspection when run without arguments
    if len(sys.argv) == 1:
        print_introspection()
        sys.exit(0)
