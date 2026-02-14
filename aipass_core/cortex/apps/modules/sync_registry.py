#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: sync_registry.py - Sync Branch Registry
# Date: 2025-11-22
# Version: 1.0.0
# Category: cortex
# Commands: sync, sync-registry, --help
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-22): Initial implementation - sync registry with filesystem
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Sync Branch Registry

Synchronizes BRANCH_REGISTRY.json with filesystem reality:
- Scans for all .id.json files (branch markers)
- Removes stale entries (in registry but directory no longer exists)
- Adds missing entries (directory exists but not registered)
- Reports changes made

Usage:
    python3 apps/cortex.py sync
    python3 apps/cortex.py sync-registry
"""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Prax logger
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

from cortex.apps.handlers.branch.registry import sync_branch_registry


def sync_registry():
    """
    Synchronize branch registry with filesystem

    Scans filesystem for .id.json files and updates BRANCH_REGISTRY.json:
    - Removes branches that no longer exist
    - Adds newly discovered branches
    - Reports all changes made

    Returns:
        bool: True on success, False on error
    """
    console.print("\n[bold cyan]Synchronizing Branch Registry...[/bold cyan]\n")

    try:
        # Run sync
        results = sync_branch_registry()

        # Display results
        console.print("[bold green]Sync Complete![/bold green]\n")

        if results["removed"]:
            console.print(f"[yellow]Removed ({len(results['removed'])}):[/yellow]")
            for branch in results["removed"]:
                console.print(f"  - {branch}")
            console.print()

        if results["added"]:
            console.print(f"[green]Added ({len(results['added'])}):[/green]")
            for branch in results["added"]:
                console.print(f"  + {branch}")
            console.print()

        if results["kept"]:
            console.print(f"[dim]Kept ({len(results['kept'])} unchanged)[/dim]")

        # Summary
        total_changes = len(results["removed"]) + len(results["added"])
        if total_changes > 0:
            console.print(f"\n[bold]Total changes: {total_changes}[/bold]")
        else:
            console.print("\n[dim]No changes needed - registry already in sync[/dim]")

        # Fire trigger event
        try:
            from trigger.apps.modules.core import trigger
            trigger.fire('registry_synced',
                        added=results["added"],
                        removed=results["removed"],
                        kept_count=len(results["kept"]))
        except ImportError:
            pass  # Silent fallback

        return True

    except Exception as e:
        logger.error(f"Registry sync failed: {e}")
        console.print(f"[red]ERROR: Registry sync failed: {e}[/red]")
        return False


def print_help():
    """Print help message for sync_registry module"""
    help_text = """
[bold cyan]Sync Registry - Synchronize BRANCH_REGISTRY.json with filesystem[/bold cyan]

[bold]Commands:[/bold] sync, sync-registry

[bold]Description:[/bold]
    Scans the filesystem for all .id.json files (branch markers) and updates
    BRANCH_REGISTRY.json to match reality:

    - Removes stale entries (directory no longer exists)
    - Adds missing entries (new branches discovered)
    - Reports all changes made

[bold]Usage:[/bold]
    python3 apps/cortex.py sync
    python3 apps/cortex.py sync-registry

[bold]Use Cases:[/bold]
    - Renamed/removed .id.json files (to exclude branches from registry)
    - Manually deleted branch directories
    - Discovered new branches not yet registered
    - General registry cleanup

[bold]Example Workflow:[/bold]
    1. Rename FLOW.id.json to FLOW.id.json.disabled
    2. Run: python3 apps/cortex.py sync
    3. FLOW is removed from registry (no .id.json found)

[bold]Notes:[/bold]
    - Safe to run anytime - only syncs, doesn't delete files
    - Automatically runs during branch updates
    - Respects .archive, deleted_branches, and system directories
"""
    console.print(help_text)


def handle_command(args) -> bool:
    """
    Handle sync-registry command routing

    Args:
        args: Command line arguments

    Returns:
        bool: True on success, False on error
    """
    # Check if this module should handle the command
    if not hasattr(args, 'command') or args.command != 'sync-registry':
        return False

    # Run sync
    return sync_registry()


if __name__ == "__main__":
    # Allow direct execution for testing
    success = sync_registry()
    sys.exit(0 if success else 1)
