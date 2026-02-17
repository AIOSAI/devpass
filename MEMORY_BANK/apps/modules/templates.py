#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: templates.py - Living Template Orchestration Module
# Date: 2026-02-14
# Version: 1.0.0
# Category: memory_bank/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-14): Initial version - Phase 3 of FPLAN-0340
#     * push-templates: Push living template updates to all branches
#     * diff-templates: Show template diffs per branch
#     * template-status: Show template version and push status
#
# CODE STANDARDS:
#   - Thin orchestration: Delegate all logic to handlers
#   - No business logic: Only coordinate workflow
#   - handle_command() pattern
# =============================================

"""
Living Template Orchestration Module

Coordinates template management workflow by calling handlers:
1. Push template structural updates to branches (pusher)
2. Diff template vs branch state (differ)
3. Show template version and push status (pusher)

Purpose:
    Thin orchestration layer - no business logic implementation.
    All domain logic lives in handlers (pusher.py, differ.py).
"""

import sys
from pathlib import Path
from typing import List

# Infrastructure setup
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))  # For MEMORY_BANK package imports

# Service imports
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header

# Handler imports (domain-organized)
from MEMORY_BANK.apps.handlers.templates.pusher import push_templates, get_template_status
from MEMORY_BANK.apps.handlers.templates.differ import diff_template_vs_branch
from MEMORY_BANK.apps.handlers.json.json_handler import read_memory_file_data

# Branch registry for iteration
REGISTRY_PATH = Path.home() / "BRANCH_REGISTRY.json"


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle living template commands

    Commands supported:
    - push-templates: Push template updates to all branches
    - diff-templates: Show template differences per branch
    - template-status: Show template version and push status

    Args:
        command: Command name
        args: Additional arguments

    Returns:
        True if command handled, False otherwise
    """
    if command in ('--help', '-h', 'help'):
        print_help()
        return True

    if command == 'push-templates':
        dry_run = '--dry-run' in args
        try:
            _display_push_results(push_templates(dry_run=dry_run), dry_run)
        except Exception as e:
            console.print(f"[red]Template push crashed: {e}[/red]")
            logger.error(f"[templates] push-templates crashed: {e}")
        return True

    elif command == 'diff-templates':
        # Parse --branch flag
        branch_name: str | None = None
        i = 0
        while i < len(args):
            if args[i] == '--branch' and i + 1 < len(args):
                branch_name = args[i + 1]
                i += 2
            else:
                i += 1
        _display_diff_results(branch_name)
        return True

    elif command == 'template-status':
        try:
            _display_status(get_template_status())
        except Exception as e:
            console.print(f"[red]Template status failed: {e}[/red]")
            logger.error(f"[templates] template-status crashed: {e}")
        return True

    return False


def print_help() -> None:
    """Display templates module help"""
    console.print()
    header("Templates Module - Living Template Management")
    console.print()
    console.print("[bold]USAGE:[/bold]")
    console.print("  python3 templates.py <command>")
    console.print()
    console.print("[bold]COMMANDS:[/bold]")
    console.print("  [cyan]push-templates[/cyan]              Push template updates to all branches")
    console.print("  [cyan]push-templates --dry-run[/cyan]    Preview changes without writing")
    console.print("  [cyan]diff-templates[/cyan]              Show template differences per branch")
    console.print("  [cyan]diff-templates --branch NAME[/cyan]  Diff a specific branch")
    console.print("  [cyan]template-status[/cyan]             Show template version and push status")
    console.print("  [cyan]help[/cyan]                        Show this help message")
    console.print()


# =============================================================================
# DISPLAY: PUSH RESULTS
# =============================================================================

def _display_push_results(result: dict, dry_run: bool) -> None:
    """Format and display push_templates() handler result."""
    console.print()
    mode_label = "DRY RUN" if dry_run else "Push"
    header(f"Memory Bank - Template {mode_label}")
    console.print()

    if dry_run:
        console.print("[yellow]DRY RUN MODE[/yellow] - no files will be modified")
        console.print()

    if not result.get('success'):
        console.print("[red]Template push failed[/red]")
        for err in result.get('errors', []):
            console.print(f"  [red]![/red] {err}")
        logger.error(f"[templates] Push failed: {result.get('errors')}")
        console.print()
        return

    # Summary
    console.print(f"[cyan]Branches scanned:[/cyan]  {result['branches_scanned']}")
    console.print(f"[cyan]Branches updated:[/cyan]  {result['branches_updated']}")
    console.print(f"[cyan]Files modified:[/cyan]    {result['files_modified']}")
    console.print()

    # Change details per branch/file
    changes = result.get('changes', [])
    if changes:
        console.print(f"[yellow]Changes ({len(changes)} files):[/yellow]")
        console.print()
        for entry in changes:
            branch = entry.get('branch', 'UNKNOWN')
            file_name = entry.get('file', 'unknown')
            file_changes = entry.get('changes', [])
            console.print(f"  [bold]{branch}[/bold]/{file_name}:")
            for chg in file_changes:
                console.print(f"    [green]+[/green] {chg}")
            console.print()
    else:
        console.print("[green]All branches are up to date with templates.[/green]")
        console.print()

    # Errors
    errors = result.get('errors', [])
    if errors:
        console.print(f"[red]Errors ({len(errors)}):[/red]")
        for err in errors:
            console.print(f"  [red]![/red] {err}")
        console.print()
        logger.error(f"[templates] Push completed with {len(errors)} errors")

    # Final status
    if result['branches_updated'] > 0 and not dry_run:
        console.print(
            f"[green]Template push complete:[/green] "
            f"{result['branches_updated']}/{result['branches_scanned']} branches updated"
        )
    elif dry_run and changes:
        console.print(
            f"[yellow]Dry run complete:[/yellow] "
            f"{result['branches_updated']} branches would be updated"
        )
    else:
        console.print("[green]No updates needed.[/green]")

    logger.info(
        f"[templates] Push {'(dry run) ' if dry_run else ''}complete: "
        f"{result['branches_updated']}/{result['branches_scanned']} branches, "
        f"{result['files_modified']} files"
    )
    console.print()


# =============================================================================
# DISPLAY: DIFF RESULTS
# =============================================================================

def _display_diff_results(branch_name: str | None = None) -> None:
    """
    Call differ handler for all/specific branches, display results.

    Args:
        branch_name: Optional branch name filter (None = all branches)
    """
    console.print()
    header("Memory Bank - Template Diff")
    console.print()

    # Load registry to get branch paths
    branches = _load_branches_from_registry()
    if branches is None:
        console.print("[red]Failed to load branch registry[/red]")
        logger.error("[templates] Failed to load branch registry for diff")
        console.print()
        return

    # Filter if branch specified
    if branch_name:
        branches = [
            b for b in branches
            if b.get('name', '').upper() == branch_name.upper()
        ]
        if not branches:
            console.print(f"[red]Branch not found:[/red] {branch_name}")
            console.print()
            return
        console.print(f"[cyan]Diffing branch:[/cyan] {branch_name.upper()}")
    else:
        console.print(f"[cyan]Diffing all {len(branches)} active branches...[/cyan]")
    console.print()

    total_diffs = 0
    total_errors = 0

    for branch in branches:
        name = branch.get('name', 'UNKNOWN')
        path = branch.get('path', '')

        if not path or not Path(path).exists():
            console.print(f"  [red]![/red] {name}: path not found ({path})")
            logger.warning(f"[templates] Branch path not found: {name} ({path})")
            total_errors += 1
            continue

        # Call handler
        try:
            result = diff_template_vs_branch(path)
        except Exception as e:
            console.print(f"  [red]![/red] {name}: handler error: {e}")
            logger.error(f"[templates] Diff handler crashed for {name}: {e}")
            total_errors += 1
            continue

        local_diffs = result.get('local', [])
        obs_diffs = result.get('observations', [])
        errors = result.get('errors', [])
        branch_has_diffs = bool(local_diffs or obs_diffs)

        if branch_has_diffs:
            total_diffs += 1
        if errors:
            total_errors += len(errors)

        # Display branch results
        if branch_has_diffs:
            console.print(f"  [bold yellow]{name}[/bold yellow]")
            _display_file_diffs(local_diffs)
            _display_file_diffs(obs_diffs)
            console.print()
        elif not errors:
            console.print(f"  [green]{name}[/green]: up to date")

        for err in errors:
            console.print(f"  [red]![/red] {name}: {err}")
            logger.warning(f"[templates] Diff error for {name}: {err}")

    # Summary
    console.print()
    if total_diffs == 0 and total_errors == 0:
        console.print("[green]All branches are up to date with templates.[/green]")
    else:
        if total_diffs > 0:
            console.print(f"[yellow]{total_diffs} branches have template differences[/yellow]")
            console.print("[dim]Run 'push-templates --dry-run' to preview changes[/dim]")
        if total_errors > 0:
            console.print(f"[red]{total_errors} errors encountered[/red]")

    logger.info(f"[templates] Diff complete: {total_diffs} branches with diffs, {total_errors} errors")
    console.print()


def _display_file_diffs(file_diffs: list) -> None:
    """Display diff entries for a list of files."""
    for entry in file_diffs:
        console.print(f"    [dim]{entry['file']}:[/dim]")
        if entry.get('additions'):
            for a in entry['additions']:
                console.print(f"      [green]+ {a}[/green]")
        if entry.get('removals'):
            for r in entry['removals']:
                console.print(f"      [red]- {r}[/red]")
        if entry.get('modifications'):
            for m in entry['modifications']:
                console.print(f"      [yellow]~ {m}[/yellow]")


# =============================================================================
# DISPLAY: STATUS
# =============================================================================

def _display_status(status: dict) -> None:
    """Format and display get_template_status() handler result."""
    console.print()
    header("Memory Bank - Template Status")
    console.print()

    # Template files
    local_icon = "[green]found[/green]" if status.get('local_template_exists') else "[red]MISSING[/red]"
    obs_icon = "[green]found[/green]" if status.get('observations_template_exists') else "[red]MISSING[/red]"

    console.print(f"[cyan]Templates directory:[/cyan]  {status.get('templates_dir', 'unknown')}")
    console.print(f"[cyan]LOCAL template:[/cyan]      {local_icon}")
    console.print(f"[cyan]OBS template:[/cyan]        {obs_icon}")
    console.print()

    # Version info
    version = status.get('version') or 'unknown'
    last_push = status.get('last_push') or 'never'
    console.print(f"[cyan]Schema version:[/cyan]     {version}")
    console.print(f"[cyan]Last push:[/cyan]          {last_push}")

    # Branches pushed
    pushed = status.get('last_push_branches', [])
    if pushed:
        preview = ', '.join(pushed[:8])
        suffix = f'... (+{len(pushed) - 8} more)' if len(pushed) > 8 else ''
        console.print(f"[cyan]Branches pushed:[/cyan]    {len(pushed)} ({preview}{suffix})")
    else:
        console.print("[cyan]Branches pushed:[/cyan]    none")

    logger.info(f"[templates] Status checked - version: {version}, last push: {last_push}")
    console.print()


# =============================================================================
# HELPERS
# =============================================================================

def _load_branches_from_registry() -> list | None:
    """
    Load active branches from BRANCH_REGISTRY.json via json_handler.

    Returns:
        List of branch dicts or None on error
    """
    if not REGISTRY_PATH.exists():
        return None
    try:
        data = read_memory_file_data(REGISTRY_PATH)
        if data is None:
            return None
        return [b for b in data.get('branches', []) if b.get('status') == 'active']
    except Exception as e:
        logger.error(f"[templates] Failed to load branch registry: {e}")
        return None


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Handle --help before argparse (module standard)
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h', 'help'):
        handle_command('help', [])
        sys.exit(0)

    # Execute command via handle_command
    command = sys.argv[1]
    if not handle_command(command, sys.argv[2:]):
        console.print(f"[red]Unknown command:[/red] {command}")
        console.print("Run with [cyan]help[/cyan] for available commands")
        sys.exit(1)
