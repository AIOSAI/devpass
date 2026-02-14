#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: dispatch.py - Dispatch Status Module
# Date: 2026-02-02
# Version: 1.0.0
# Category: ai_mail/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-02): Initial version - dispatch status tracking
#
# CODE STANDARDS:
#   - Orchestration only - delegates to handlers
#   - Uses json_handler.log_operation()
# =============================================

"""
Dispatch Status Module

Tracks and displays dispatch (auto-execute) spawn status.
Shows recent dispatches with PID status (RUNNING/COMPLETED/FAILED).
"""

import sys
from pathlib import Path
from typing import List

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console
from ai_mail.apps.handlers.dispatch.status import (
    load_dispatch_log,
    check_pid_status,
    calculate_age
)


def print_help() -> None:
    """Print help for dispatch commands"""
    help_text = """
Dispatch Module - Track spawned agent status

COMMANDS:
  dispatch status    - Show last 5 dispatch spawns with current status

OUTPUT:
  Shows branch, PID, status (RUNNING/COMPLETED/FAILED), and age

EXAMPLE:
  ai_mail dispatch status

  DISPATCH STATUS
  ────────────────────────────────────
  @flow    PID 108957  RUNNING    2m ago
  @ai_mail PID 85997   COMPLETED  10m ago
  @seed    PID 84521   FAILED     15m ago
  ────────────────────────────────────
  Active: 1  |  Total: 3
"""
    console.print(help_text)


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle dispatch commands

    Args:
        command: Command name
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command != "dispatch":
        return False

    # Handle --help flag
    if args and args[0] in ['--help', '-h', 'help']:
        print_help()
        return True

    # Handle subcommands
    if not args:
        print_help()
        return True

    subcommand = args[0]

    if subcommand == "status":
        return handle_status()
    else:
        console.print(f"[red]Unknown dispatch subcommand: {subcommand}[/red]")
        print_help()
        return False


def handle_status() -> bool:
    """Show dispatch status for recent spawns"""
    logger.info("[dispatch] Showing dispatch status")

    # Load dispatch log
    dispatches = load_dispatch_log()

    if not dispatches:
        console.print("\n[dim]No dispatches recorded yet.[/dim]")
        return True

    # Get last 5 dispatches (newest first)
    recent = dispatches[-5:][::-1]

    console.print("\n[bold]DISPATCH STATUS[/bold]")
    console.print("─" * 50)

    active_count = 0
    for dispatch in recent:
        branch = dispatch.get("branch", "unknown")
        pid = dispatch.get("pid")
        timestamp = dispatch.get("timestamp", "")
        spawn_status = dispatch.get("status", "unknown")

        # Check if PID is still running
        if spawn_status == "spawned" and pid:
            current_status = check_pid_status(pid)
        elif spawn_status == "failed":
            current_status = "FAILED"
        else:
            current_status = "UNKNOWN"

        if current_status == "RUNNING":
            active_count += 1

        # Calculate age
        age_str = calculate_age(timestamp)

        # Format status with color
        if current_status == "RUNNING":
            status_display = "[green]RUNNING[/green]"
        elif current_status == "COMPLETED":
            status_display = "[dim]COMPLETED[/dim]"
        elif current_status == "FAILED":
            status_display = "[red]FAILED[/red]"
        else:
            status_display = f"[yellow]{current_status}[/yellow]"

        # Display line
        pid_display = f"PID {pid}" if pid else "NO PID"
        console.print(f"  {branch:<12} {pid_display:<12} {status_display:<18} {age_str}")

    console.print("─" * 50)
    console.print(f"[dim]Active: {active_count}  |  Total: {len(recent)}[/dim]\n")

    return True


if __name__ == "__main__":
    # Show help when run directly
    if len(sys.argv) == 1:
        print_help()
        sys.exit(0)

    # Handle help flag
    if sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    # Execute command
    command = sys.argv[1]
    remaining_args = sys.argv[2:] if len(sys.argv) > 2 else []

    if handle_command(command, remaining_args):
        sys.exit(0)
    else:
        sys.exit(1)
