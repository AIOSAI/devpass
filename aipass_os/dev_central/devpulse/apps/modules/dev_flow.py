#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: dev_flow.py - D-PLAN management module (thin orchestrator)
# Date: 2025-12-02
# Version: 2.0.0
# Category: Module
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2025-12-02): Refactored to thin orchestrator - all logic in handlers
#   - v1.0.0 (2025-12-02): Initial version - plan create/list/status commands
#
# CODE STANDARDS:
#   - Modules orchestrate, handlers implement (3-tier architecture)
#   - handle_command() interface for drone routing
#   - Module does the logging, handlers return errors
#   - CLI services for output (no print())
# ==============================================

"""
D-PLAN Management Module - Thin Orchestrator

Routes commands to handlers in handlers/plan/.
Manages numbered, dated planning documents in dev_planning/.
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
from typing import List

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

# Infrastructure imports (module does the logging)
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header, success, error

# Handler imports
from aipass_os.dev_central.devpulse.apps.handlers.plan.create import create_plan
from aipass_os.dev_central.devpulse.apps.handlers.plan.list import list_plans
from aipass_os.dev_central.devpulse.apps.handlers.plan.status import get_status_summary, get_status_icon
from aipass_os.dev_central.devpulse.apps.handlers.plan.display import show_help, print_introspection


# =============================================================================
# MODULE INTERFACE
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle D-PLAN commands - routes to handlers

    Args:
        command: Command to execute ('plan')
        args: Command arguments

    Returns:
        True if command was handled, False otherwise
    """
    if command != 'plan':
        return False

    # Handle --help flag
    if args and args[0] == '--help':
        header("D-PLAN - Development Planning")
        console.print(show_help())
        return True

    # Parse subcommand
    if not args:
        header("D-PLAN - Development Planning")
        console.print(show_help())
        return True

    subcommand = args[0]

    if subcommand == 'create':
        return _handle_create(args[1:])
    elif subcommand == 'list':
        return _handle_list(args[1:])
    elif subcommand == 'status':
        return _handle_status(args[1:])
    else:
        error(f"Unknown subcommand: {subcommand}")
        console.print("Run 'plan --help' for usage")
        return True


# =============================================================================
# COMMAND HANDLERS (orchestration only)
# =============================================================================

def _handle_create(args: List[str]) -> bool:
    """Orchestrate plan creation - delegates to handler"""
    # Handle --help flag
    if args and args[0] == '--help':
        console.print("\n[bold]USAGE:[/bold]")
        console.print("  plan create \"topic name\" [--dir subdirectory]")
        console.print("\n[bold]OPTIONS:[/bold]")
        console.print("  --dir <name>  Create plan in dev_planning/<name>/ subdirectory")
        console.print("\n[bold]EXAMPLES:[/bold]")
        console.print("  plan create \"new feature design\"")
        console.print("  plan create \"api refactoring\"")
        console.print("  plan create \"flow improvements\" --dir flow\n")
        return True

    if len(args) < 1:
        error("Usage: plan create \"topic name\" [--dir subdirectory]")
        return True

    # Parse arguments: topic and optional --dir flag
    topic = args[0]
    subdir = None

    # Check for --dir flag
    if '--dir' in args:
        dir_idx = args.index('--dir')
        if dir_idx + 1 < len(args):
            subdir = args[dir_idx + 1]
        else:
            error("--dir requires a subdirectory name")
            return True

    # Delegate to handler
    ok, result, err = create_plan(topic, subdir=subdir)

    if not ok:
        logger.error(f"[dev_flow] Failed to create plan: {err}")
        error(f"Failed to create plan: {err}")
        return True

    # Log success (module does logging)
    logger.info(f"[dev_flow] Created DPLAN-{result['plan_number']:03d}: {result['filename']}")

    # Log cache warning if any
    if result.get('cache_warning'):
        logger.warning(f"[dev_flow] {result['cache_warning']}")

    # Display result
    console.print()
    success(f"Created DPLAN-{result['plan_number']:03d}")
    console.print(f"  [dim]Topic:[/dim] {result['topic']}")
    console.print(f"  [dim]File:[/dim] {result['path']}")
    console.print()

    return True


def _handle_list(args: List[str]) -> bool:
    """Orchestrate plan listing - delegates to handler"""
    # Delegate to handler
    plans, err = list_plans()

    if err:
        logger.error(f"[dev_flow] Failed to list plans: {err}")
        error(f"Failed to list plans: {err}")
        return True

    # Display results
    console.print()
    header("D-PLANs")
    console.print()

    if not plans:
        console.print("[dim]No plans found[/dim]")
        console.print()
        return True

    for p in plans:
        status_icon = get_status_icon(p["status"])
        console.print(f"  {status_icon} [cyan]DPLAN-{p['number']:03d}[/cyan] | {p['topic'][:35]:<35} | {p['date']}")

    console.print()
    console.print(f"[dim]Total: {len(plans)} plans[/dim]")
    console.print()

    return True


def _handle_status(args: List[str]) -> bool:
    """Orchestrate status display - delegates to handler"""
    # Delegate to handler
    status_counts, total, err = get_status_summary()

    if err:
        logger.error(f"[dev_flow] Failed to get status: {err}")
        error(f"Failed to get status: {err}")
        return True

    # Display results
    console.print()
    header("D-PLAN Status")
    console.print()

    console.print(f"  [yellow]📋 Planning:[/yellow]        {status_counts['planning']}")
    console.print(f"  [blue]🔄 In Progress:[/blue]      {status_counts['in_progress']}")
    console.print(f"  [green]✅ Ready:[/green]            {status_counts['ready']}")
    console.print(f"  [dim]✓ Complete:[/dim]         {status_counts['complete']}")
    console.print(f"  [red]❌ Abandoned:[/red]        {status_counts['abandoned']}")

    if status_counts["unknown"] > 0:
        console.print(f"  [dim]? Unknown:[/dim]          {status_counts['unknown']}")

    console.print()
    console.print(f"[dim]Total: {total} plans[/dim]")
    console.print()

    return True


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Show introspection when run without arguments
    if len(sys.argv) == 1:
        console.print(print_introspection())
        sys.exit(0)

    # Handle help flag
    if sys.argv[1] in ['--help', '-h', 'help']:
        header("D-PLAN - Development Planning")
        console.print(show_help())
        sys.exit(0)

    # Route command: plan create "topic" -> handle_command("plan", ["create", "topic"])
    subcommand = sys.argv[1]
    remaining_args = sys.argv[2:] if len(sys.argv) > 2 else []

    if handle_command('plan', [subcommand] + remaining_args):
        sys.exit(0)
    else:
        console.print()
        console.print("[red]Failed to handle command[/red]")
        console.print()
        sys.exit(1)
