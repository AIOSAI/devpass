#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: bulletin_board.py - Bulletin Board Module
# Date: 2025-11-24
# Version: 0.2.0
# Category: aipass/central
#
# CHANGELOG (Max 5 entries):
#   - v0.2.0 (2025-11-24): Refactored to 3-layer architecture - handlers extracted
#   - v0.1.1 (2025-11-24): Standards fixes - logger, CLI service, handle_command
#   - v0.1.0 (2025-11-24): Initial structure - bulletin management
#
# CODE STANDARDS:
#   - Module orchestrates, handlers implement
#   - Business logic in handlers/bulletin/
#   - CLI output functions only in module
# =============================================

"""
Bulletin Board Module

Manages system-wide announcements and propagates to branches.
Creates bulletins at AIPASS level, pushes to branch dashboards.

Run directly or via: python3 apps/modules/bulletin_board.py
"""

import sys
from pathlib import Path
from typing import List

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

# Import handlers (business logic)
from aipass_os.dev_central.devpulse.apps.handlers.bulletin import (
    load_bulletins,
    save_bulletins,
    create_bulletin,
    list_bulletins,
    acknowledge_bulletin,
    propagate_to_branches
)

# ============================================
# PATHS (for introspection display)
# ============================================
AI_CENTRAL = AIPASS_ROOT / "aipass_os" / "AI_CENTRAL"
BULLETIN_CENTRAL = AI_CENTRAL / "BULLETIN_BOARD_central.json"


# ============================================
# CLI INTERFACE
# ============================================
def print_introspection():
    """Display module info"""
    console.print()
    console.print("[bold cyan]Bulletin Board Module[/bold cyan]")
    console.print()
    console.print("[yellow]Connected Handlers:[/yellow]")
    console.print("  handlers/bulletin/")
    console.print("    - storage.py")
    console.print("    - crud.py")
    console.print("    - propagation.py")
    console.print()
    console.print("[yellow]Central File:[/yellow]")
    console.print(f"  - {BULLETIN_CENTRAL.name}")
    console.print()
    console.print("[dim]Run 'python3 bulletin_board.py --help' for usage[/dim]")
    console.print()


def print_help():
    """Print drone-compliant help output"""
    console.print()
    console.print("[bold cyan]Bulletin Board Module[/bold cyan]")
    console.print("System-wide announcements and branch propagation")
    console.print()
    console.print("[yellow]COMMANDS:[/yellow]")
    console.print("  list        - List active bulletins")
    console.print("  create      - Create new bulletin")
    console.print("  ack         - Acknowledge a bulletin")
    console.print("  propagate   - Push to branch dashboards")
    console.print()
    console.print("[yellow]USAGE:[/yellow]")
    console.print("  python3 apps/modules/bulletin_board.py --help")
    console.print("  python3 apps/modules/bulletin_board.py list")
    console.print('  python3 apps/modules/bulletin_board.py create "Subject" "Message"')
    console.print()


def print_bulletins():
    """Print active bulletins"""
    try:
        bulletins = list_bulletins("active")
        console.print()
        console.print(f"[bold]Active Bulletins: {len(bulletins)}[/bold]")
        console.print("=" * 50)

        if not bulletins:
            console.print("  [dim]No active bulletins[/dim]")
        else:
            for b in bulletins:
                console.print(f"  [cyan][{b.get('id')}][/cyan] {b.get('subject')}")
                console.print(f"    Priority: {b.get('priority')} | Type: {b.get('type')}")
                console.print(f"    Acks: {len(b.get('acknowledgements', []))}")
                console.print()
    except Exception as e:
        logger.error(f"Failed to list bulletins: {e}")
        console.print(f"[red]Error loading bulletins: {e}[/red]")


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle drone-routed commands

    Args:
        command: The command to execute
        args: Additional arguments

    Returns:
        True if command handled, False otherwise
    """
    try:
        if command == "list":
            print_bulletins()
            return True
        elif command == "create":
            if len(args) >= 2:
                result = create_bulletin(args[0], args[1])
                if result.get("success"):
                    console.print(f"[green]Bulletin created: {result.get('id')}[/green]")
                    logger.info(f"Created bulletin: {result.get('id')}")
                else:
                    console.print(f"[red]Failed: {result.get('error')}[/red]")
                    logger.error(f"Failed to create bulletin: {result.get('error')}")
            else:
                console.print('[yellow]Usage: create "Subject" "Message"[/yellow]')
            return True
        elif command == "ack":
            if len(args) >= 2:
                result = acknowledge_bulletin(args[0], args[1])
                if result.get("success"):
                    if result.get("acknowledged"):
                        console.print(f"[green]Branch '{args[1]}' acknowledged {args[0]}[/green]")
                        logger.info(f"Branch '{args[1]}' acknowledged bulletin {args[0]}")
                        if result.get("completed"):
                            console.print(f"[cyan]Bulletin {args[0]} completed![/cyan]")
                            logger.info(f"Bulletin {args[0]} completed - all targets acknowledged")
                    else:
                        console.print(f"[yellow]{result.get('reason')}[/yellow]")
                else:
                    console.print(f"[red]Failed: {result.get('error')}[/red]")
                    logger.error(f"Failed to acknowledge bulletin: {result.get('error')}")
            else:
                console.print("[yellow]Usage: ack BULLETIN_0001 BRANCH_NAME[/yellow]")
            return True
        elif command == "propagate":
            result = propagate_to_branches()
            console.print(f"Propagation status: {result.get('status')}")
            console.print(f"Branches updated: {result.get('branches_updated')}")
            errors = result.get("errors")
            if errors and isinstance(errors, list):
                console.print(f"[yellow]Errors: {', '.join(errors)}[/yellow]")
            return True
        return False
    except Exception as e:
        logger.error(f"Command '{command}' failed: {e}")
        console.print(f"[red]Command failed: {e}[/red]")
        return True


def main():
    """Main entry point"""
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # No args = show introspection
    if not args:
        print_introspection()
        return

    # --help = show commands
    if "--help" in args or "-h" in args:
        print_help()
        return

    command = args[0].lower()
    remaining_args = args[1:]

    if not handle_command(command, remaining_args):
        console.print(f"[red]Unknown command: {command}[/red]")
        print_help()


if __name__ == "__main__":
    main()
