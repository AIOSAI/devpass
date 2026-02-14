#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: dashboard.py - Dashboard Section Utilities
# Date: 2025-11-24
# Version: 0.1.1
# Category: aipass/central
#
# CHANGELOG (Max 5 entries):
#   - v0.1.1 (2025-11-24): Standards fixes - logger, CLI service, handle_command
#   - v0.1.0 (2025-11-24): Initial structure - dashboard utilities
#
# CODE STANDARDS:
#   - Provides dashboard section update utilities
#   - Used by services to update their dashboard sections
# =============================================

"""
Dashboard Section Utilities

Provides utilities for services to update their sections in branch
DASHBOARD.local.json files. Each service manages only its own section.

Run directly or via: python3 apps/modules/dashboard.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

# Import handlers
from aipass_os.dev_central.devpulse.apps.handlers.dashboard import (
    load_dashboard,
    save_dashboard,
    update_section as handler_update_section,
    get_dashboard_path,
    calculate_quick_status,
    get_branch_paths
)

# Import refresh handler - exposed as public API
from aipass_os.dev_central.devpulse.apps.handlers.dashboard.refresh import (
    refresh_all_dashboards,
    refresh_single_dashboard
)


# ============================================
# DASHBOARD SCHEMA
# ============================================
DASHBOARD_TEMPLATE = {
    "branch": "",
    "last_updated": "",
    "sections": {
        "flow": {
            "managed_by": "flow",
            "active_plans": 0,
            "recently_closed": [],
            "last_sync": ""
        },
        "ai_mail": {
            "managed_by": "ai_mail",
            "unread": 0,
            "total": 0,
            "recent_preview": [],
            "last_sync": ""
        },
        "memory_bank": {
            "managed_by": "memory_bank",
            "vectors_stored": 0,
            "archives_count": 0,
            "last_rollover": "",
            "last_sync": ""
        },
        "bulletin_board": {
            "managed_by": "aipass",
            "active_bulletins": 0,
            "pending": [],
            "last_sync": ""
        }
    },
    "quick_status": {
        "unread_mail": 0,
        "active_plans": 0,
        "pending_bulletins": 0,
        "action_required": False,
        "summary": ""
    }
}


# ============================================
# MODULE-LEVEL WRAPPER FUNCTIONS
# ============================================
def update_section(
    branch_path: Path,
    section_name: str,
    section_data: Dict
) -> bool:
    """
    Update a specific section in branch dashboard

    Args:
        branch_path: Path to branch root
        section_name: Section to update (flow, ai_mail, etc)
        section_data: New data for section

    Returns:
        True if updated successfully
    """
    try:
        return handler_update_section(
            branch_path,
            section_name,
            section_data,
            DASHBOARD_TEMPLATE,
            calculate_quick_status
        )
    except Exception as e:
        logger.error(f"Failed to update section {section_name}: {e}")
        return False


# ============================================
# CLI INTERFACE
# ============================================
def print_introspection():
    """Display module info"""
    console.print()
    console.print("[bold cyan]Dashboard Section Utilities[/bold cyan]")
    console.print()
    console.print("[yellow]Template Sections:[/yellow]")
    for section in DASHBOARD_TEMPLATE["sections"]:
        console.print(f"  - {section}")
    console.print()
    console.print("[dim]Run 'python3 dashboard.py --help' for usage[/dim]")
    console.print()


def print_help():
    """Print drone-compliant help output"""
    console.print()
    console.print("[bold cyan]Dashboard Section Utilities[/bold cyan]")
    console.print("Utilities for updating branch dashboard sections")
    console.print()
    console.print("[yellow]COMMANDS:[/yellow]")
    console.print("  status      - Show dashboard status for all branches")
    console.print("  template    - Show dashboard template structure")
    console.print()
    console.print("[yellow]USAGE:[/yellow]")
    console.print("  python3 apps/modules/dashboard.py --help")
    console.print("  python3 apps/modules/dashboard.py status")
    console.print("  python3 apps/modules/dashboard.py template")
    console.print()
    console.print("[yellow]PROGRAMMATIC:[/yellow]")
    console.print("  from apps.modules.dashboard import update_section")
    console.print("  update_section(branch_path, 'ai_mail', {'unread': 3})")
    console.print()


def print_status():
    """Show dashboard status for all branches"""
    try:
        branches = get_branch_paths()
    except Exception as e:
        console.print(f"[red]Error loading branches: {e}[/red]")
        return

    console.print()
    console.print(f"[bold]Dashboard Status ({len(branches)} branches)[/bold]")
    console.print("=" * 50)

    for branch_path in branches:
        dashboard_path = get_dashboard_path(branch_path)
        exists = dashboard_path.exists()
        status = "[green]exists[/green]" if exists else "[red]missing[/red]"
        console.print(f"  {branch_path.name}: {status}")

    console.print()


def print_template():
    """Show dashboard template"""
    console.print()
    console.print("[bold]Dashboard Template Structure[/bold]")
    console.print("=" * 50)
    console.print(json.dumps(DASHBOARD_TEMPLATE, indent=2))
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
    if command == "status":
        print_status()
        return True
    elif command == "template":
        print_template()
        return True
    return False


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
