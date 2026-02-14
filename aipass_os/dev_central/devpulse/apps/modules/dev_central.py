#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: dev_central.py - Central Aggregation Module
# Date: 2025-11-24
# Version: 0.1.1
# Category: aipass/central
#
# CHANGELOG (Max 5 entries):
#   - v0.1.1 (2025-11-24): Standards fixes - logger, CLI service, handle_command
#   - v0.1.0 (2025-11-24): Initial structure - central aggregation
#
# CODE STANDARDS:
#   - Aggregates branch data to central files
#   - Manages devpulse.central.md, readme.central.md
# =============================================

"""
Central Aggregation Module

Aggregates branch data up to central files at AIPASS level.
Manages: devpulse.central.md, readme.central.md, PLANS.central.json

Run directly or via: python3 apps/modules/dev_central.py
"""

import sys
from pathlib import Path
from typing import Dict, List

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

# Infrastructure imports (after sys.path setup, no prefix needed)
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

# Handler imports (devpulse internal handlers)
from aipass_os.dev_central.devpulse.apps.handlers.central.aggregation import aggregate_devpulse, aggregate_plans
from aipass_os.dev_central.devpulse.apps.handlers.central.sync import sync_readmes, sync_notepads, sync_plans
from aipass_os.dev_central.devpulse.apps.handlers.central.branch_list import get_branch_list

# ============================================
# PATHS
# ============================================
AI_CENTRAL = AIPASS_ROOT / "aipass_os" / "AI_CENTRAL"
DEV_CENTRAL = AIPASS_ROOT / "aipass_os" / "dev_central"
BRANCH_REGISTRY = AIPASS_ROOT / "BRANCH_REGISTRY.json"

# Central files this module manages
DEVPULSE_CENTRAL = DEV_CENTRAL / "devpulse.central.md"
PLANS_CENTRAL = AI_CENTRAL / "PLANS.central.json"
BULLETIN_CENTRAL = AI_CENTRAL / "BULLETIN_BOARD_central.json"


# ============================================
# CLI INTERFACE
# ============================================
def print_introspection():
    """Display module info and connected handlers"""
    console.print()
    console.print("[bold cyan]Central Aggregation Module[/bold cyan]")
    console.print()
    console.print("[yellow]Central Files Managed:[/yellow]")
    console.print(f"  - {DEVPULSE_CENTRAL.name}")
    console.print(f"  - {PLANS_CENTRAL.name}")
    console.print(f"  - {BULLETIN_CENTRAL.name}")
    console.print()
    console.print("[dim]Run 'python3 dev_central.py --help' for usage[/dim]")
    console.print()


def print_help():
    """Print drone-compliant help output"""
    console.print()
    console.print("[bold cyan]Central Aggregation Module[/bold cyan]")
    console.print("Aggregates branch data to central files")
    console.print()
    console.print("[yellow]COMMANDS:[/yellow]")
    console.print("  devpulse    - Aggregate branch status to devpulse.central.md")
    console.print("  plans       - Aggregate active plans to PLANS.central.json")
    console.print("  readmes     - Sync README summaries")
    console.print("  notepads    - Sync notepad summaries")
    console.print("  plans-md    - Sync plans to markdown")
    console.print("  status      - Show central files status")
    console.print()
    console.print("[yellow]USAGE:[/yellow]")
    console.print("  python3 apps/modules/dev_central.py --help")
    console.print("  python3 apps/modules/dev_central.py status")
    console.print("  python3 apps/modules/dev_central.py devpulse")
    console.print()


def print_status():
    """Show status of central files"""
    console.print()
    console.print("[bold]Central Files Status[/bold]")
    console.print("=" * 40)

    files = [
        ("DEVPULSE", DEVPULSE_CENTRAL),
        ("PLANS", PLANS_CENTRAL),
        ("BULLETIN", BULLETIN_CENTRAL),
    ]

    for name, path in files:
        exists = path.exists()
        status = "[green]exists[/green]" if exists else "[red]missing[/red]"
        console.print(f"  {name}: {status}")

    console.print()
    branches = get_branch_list()
    console.print(f"Registered branches: {len(branches)}")
    console.print()


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle drone-routed commands

    Args:
        command: The command to execute
        args: Additional arguments

    Returns:
        True if command handled, False otherwise
    """
    MODULE_NAME = "dev_central"

    try:
        if command == "status":
            print_status()
            return True
        elif command == "devpulse":
            result = aggregate_devpulse()
            console.print(f"Devpulse aggregation: {result}")
            logger.info(f"[{MODULE_NAME}] Devpulse aggregation completed")
            return True
        elif command == "plans":
            result = aggregate_plans()
            console.print(f"Plans aggregation: {result}")
            logger.info(f"[{MODULE_NAME}] Plans aggregation completed")
            return True
        elif command == "readmes":
            result = sync_readmes()
            console.print(f"README sync: {result}")
            logger.info(f"[{MODULE_NAME}] README sync completed")
            return True
        elif command == "notepads":
            result = sync_notepads()
            console.print(f"Notepad sync: {result}")
            logger.info(f"[{MODULE_NAME}] Notepad sync completed")
            return True
        elif command == "plans-md":
            result = sync_plans()
            console.print(f"Plans sync: {result}")
            logger.info(f"[{MODULE_NAME}] Plans markdown sync completed")
            return True
        return False
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Command '{command}' failed: {e}")
        console.print(f"[red]Error: {e}[/red]")
        return True  # Command was handled, even if it failed


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
