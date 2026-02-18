#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: dispatch.py - Dispatch Module
# Date: 2026-02-02
# Version: 2.0.0
# Category: ai_mail/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-17): Add daemon subcommand, move status logic to handler
#   - v1.0.0 (2026-02-02): Initial version - dispatch status tracking
#
# CODE STANDARDS:
#   - Orchestration only - delegates to handlers
#   - Uses json_handler.log_operation()
# =============================================

"""
Dispatch Module

Orchestrates dispatch commands: status tracking and daemon management.
Delegates all business logic to handlers.
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
    """Print help for dispatch commands."""
    help_text = """
Dispatch Module - Agent dispatch management

COMMANDS:
  dispatch status    - Show last 5 dispatch spawns with current status
  dispatch daemon    - Start the continuous dispatch daemon

DAEMON:
  The daemon polls branch inboxes for --dispatch emails and spawns agents.
  Run as: ai_mail dispatch daemon
  Or standalone: python3 apps/handlers/dispatch/daemon.py

  Kill switch: touch /home/aipass/.aipass/autonomous_pause
  Config: safety_config.json

EXAMPLE:
  ai_mail dispatch status

  DISPATCH STATUS
  ────────────────────────────────────
  @flow    PID 108957  RUNNING    2m ago
  @ai_mail PID 85997   COMPLETED  10m ago
  ────────────────────────────────────
  Active: 1  |  Total: 2
"""
    console.print(help_text)


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle dispatch commands.

    Args:
        command: Command name
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command != "dispatch":
        return False

    if args and args[0] in ['--help', '-h', 'help']:
        print_help()
        return True

    if not args:
        print_help()
        return True

    subcommand = args[0]

    if subcommand == "status":
        return _orchestrate_status()
    elif subcommand == "daemon":
        return _orchestrate_daemon()
    else:
        console.print(f"[red]Unknown dispatch subcommand: {subcommand}[/red]")
        print_help()
        return False


def _orchestrate_status() -> bool:
    """Orchestrate dispatch status display."""
    logger.info("[dispatch] Showing dispatch status")

    dispatches = load_dispatch_log()

    if not dispatches:
        console.print("\n[dim]No dispatches recorded yet.[/dim]")
        return True

    recent = dispatches[-5:][::-1]

    console.print("\n[bold]DISPATCH STATUS[/bold]")
    console.print("─" * 50)

    active_count = 0
    for entry in recent:
        branch = entry.get("branch", "unknown")
        pid = entry.get("pid")
        timestamp = entry.get("timestamp", "")
        spawn_status = entry.get("status", "unknown")

        if spawn_status == "spawned" and pid:
            current_status = check_pid_status(pid)
        elif spawn_status == "failed":
            current_status = "FAILED"
        else:
            current_status = "UNKNOWN"

        if current_status == "RUNNING":
            active_count += 1

        age_str = calculate_age(timestamp)

        if current_status == "RUNNING":
            status_display = "[green]RUNNING[/green]"
        elif current_status == "COMPLETED":
            status_display = "[dim]COMPLETED[/dim]"
        elif current_status == "FAILED":
            status_display = "[red]FAILED[/red]"
        else:
            status_display = f"[yellow]{current_status}[/yellow]"

        pid_display = f"PID {pid}" if pid else "NO PID"
        console.print(f"  {branch:<12} {pid_display:<12} {status_display:<18} {age_str}")

    console.print("─" * 50)
    console.print(f"[dim]Active: {active_count}  |  Total: {len(recent)}[/dim]\n")

    return True


def _orchestrate_daemon() -> bool:
    """Orchestrate daemon startup."""
    logger.info("[dispatch] Starting dispatch daemon")
    console.print("\n[bold]Starting dispatch daemon...[/bold]")

    from ai_mail.apps.handlers.dispatch.daemon import run_daemon
    run_daemon()
    return True


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_help()
        sys.exit(0)

    if sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    command = sys.argv[1]
    remaining_args = sys.argv[2:] if len(sys.argv) > 2 else []

    if handle_command(command, remaining_args):
        sys.exit(0)
    else:
        sys.exit(1)
