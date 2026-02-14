#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: medic.py - Medic Toggle Module
# Date: 2026-02-12
# Version: 1.2.0
# Category: trigger/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.2.0 (2026-02-12): Improved status wording: standby vs stopped, added explanation lines
#   - v1.1.0 (2026-02-12): Added mute/unmute per-branch commands (Phase 2)
#   - v1.0.0 (2026-02-12): Created - Medic on/off/status toggle for error dispatch
#
# CODE STANDARDS:
#   - Follows AIPass Seed standards
#   - Module orchestrates, handler (medic_state.py) contains logic
#   - No direct file operations - delegates to handler
# =============================================

"""
Medic Toggle Module - Control auto-healing error dispatch

Provides on/off/status/mute/unmute commands for the Medic system
(error detection + auto-dispatch chain). When Medic is off, errors
are still detected and logged but NOT dispatched to branches.
Per-branch muting suppresses dispatch for specific branches only.

Commands: on, off, status, mute, unmute
Architecture: Module orchestrates, medic_state handler manages persistence
"""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

from trigger.apps.handlers.medic_state import (
    is_enabled,
    set_enabled,
    get_muted_branches,
    mute_branch,
    unmute_branch,
    get_suppression_stats,
    get_rate_limit_stats,
)


def _extract_branch_name(raw: str) -> str:
    """
    Extract branch name from raw argument.

    Handles both direct names (@speakeasy, speakeasy) and
    drone-resolved paths (/home/aipass/aipass_core/speakeasy).

    Args:
        raw: Raw argument from command line

    Returns:
        Lowercase branch name (e.g., 'speakeasy')
    """
    cleaned = raw.lstrip('@')
    # If it looks like a path, take the last directory component
    if '/' in cleaned:
        cleaned = Path(cleaned).name
    return cleaned.lower()


def print_help() -> None:
    """Print module help."""
    from cli.apps.modules import console
    from rich.panel import Panel

    console.print(Panel("Medic - Auto-Healing Error Dispatch", style="bold"))
    console.print()
    console.print("Auto-healing error dispatch system. Watches branch logs for errors")
    console.print("and dispatches fix-it emails to affected branches automatically.")
    console.print()
    console.rule("USAGE")
    console.print()
    console.print("  drone @trigger medic <command>")
    console.print("  python3 trigger.py medic <command>")
    console.print()
    console.rule("COMMANDS")
    console.print()
    console.print("  [bold]on[/bold]                 Enable error dispatch (starts log watcher if needed)")
    console.print("  [bold]off[/bold]                Disable error dispatch globally (errors still logged)")
    console.print("  [bold]status[/bold]             Show current state, muted branches, and statistics")
    console.print("  [bold]mute[/bold] @branch       Suppress dispatch for a specific branch")
    console.print("  [bold]unmute[/bold] @branch     Resume dispatch for a muted branch")
    console.print("  [bold]help[/bold]               Show this help")
    console.print()
    console.rule("OFF vs MUTE")
    console.print()
    console.print("  [yellow]off[/yellow]    Global kill switch. ALL error dispatch stops. No branch")
    console.print("         receives auto-healing emails. Errors still logged to")
    console.print("         medic_suppressed.log for review.")
    console.print()
    console.print("  [yellow]mute[/yellow]   Per-branch suppress. Only the muted branch stops receiving")
    console.print("         dispatch. All other branches continue normally. Muted errors")
    console.print("         logged to medic_suppressed.log.")
    console.print()
    console.rule("EXAMPLES")
    console.print()
    console.print("  [dim]# Enable Medic (starts watching logs for errors)[/dim]")
    console.print("  drone @trigger medic on")
    console.print()
    console.print("  [dim]# Disable all error dispatch globally[/dim]")
    console.print("  drone @trigger medic off")
    console.print()
    console.print("  [dim]# Mute a noisy branch while debugging[/dim]")
    console.print("  drone @trigger medic mute @speakeasy")
    console.print()
    console.print("  [dim]# Resume dispatch for that branch[/dim]")
    console.print("  drone @trigger medic unmute @speakeasy")
    console.print()
    console.print("  [dim]# Check what's happening[/dim]")
    console.print("  drone @trigger medic status")
    console.print()
    console.rule("HOW IT WORKS")
    console.print()
    console.print("  Trigger watches branch logs  ->  fires error_detected event")
    console.print("  ->  handler checks medic_enabled  ->  checks branch mute list")
    console.print("  ->  dispatches fix-it email to affected branch (or suppresses)")
    console.print()
    console.print("  Suppressed errors: trigger/logs/medic_suppressed.log")
    console.print()


def handle_command(command: str, args: list) -> bool:
    """
    Handle medic commands - orchestrate toggle operations.

    Routes on/off/status to handler functions and coordinates
    with branch_log_events module for watcher lifecycle.

    Args:
        command: Module name or subcommand (medic, on, off, status)
        args: Additional arguments

    Returns:
        True if command was handled, False otherwise
    """
    from cli.apps.modules import console

    # Handle module-name routing (drone @trigger medic <subcmd>)
    if command == "medic":
        if not args:
            print_help()
            return True
        if args[0] in ['--help', '-h', 'help']:
            print_help()
            return True
        subcommand = args[0]
        remaining = args[1:]
        return handle_command(subcommand, remaining)

    if command not in ["on", "off", "status", "mute", "unmute"]:
        return False

    if args and args[0] in ['--help', '-h', 'help']:
        print_help()
        return True

    if command == "mute":
        if not args:
            console.print("[red]Missing branch name[/red] - usage: medic mute @branch")
            return True
        branch_name = _extract_branch_name(args[0])
        if not branch_name:
            console.print("[red]Missing branch name[/red] - usage: medic mute @branch")
            return True
        if mute_branch(branch_name):
            logger.info(f"[MEDIC] Muted branch: {branch_name}")
            console.print(f"[yellow]Muted @{branch_name}[/yellow] - errors logged but not dispatched")
        else:
            console.print(f"[red]Failed to mute @{branch_name}[/red] - check trigger_config.json")
        return True

    if command == "unmute":
        if not args:
            console.print("[red]Missing branch name[/red] - usage: medic unmute @branch")
            return True
        branch_name = _extract_branch_name(args[0])
        if not branch_name:
            console.print("[red]Missing branch name[/red] - usage: medic unmute @branch")
            return True
        if unmute_branch(branch_name):
            logger.info(f"[MEDIC] Unmuted branch: {branch_name}")
            console.print(f"[green]Unmuted @{branch_name}[/green] - dispatch resumed")
        else:
            console.print(f"[red]Failed to unmute @{branch_name}[/red] - check trigger_config.json")
        return True

    if command == "on":
        if set_enabled(True):
            logger.info("[MEDIC] Medic ENABLED - error dispatch active")
            # Start log watcher if not running
            try:
                from trigger.apps.modules.branch_log_events import start, status
                watcher_info = status()
                if not watcher_info.get('active', False):
                    start()
                    logger.info("[MEDIC] Log watcher started")
            except Exception as exc:
                logger.warning(f"[MEDIC] Could not start log watcher: {exc}")
            console.print("[green]Medic ENABLED[/green] - error dispatch active")
            console.print("  Errors detected in branch logs will be dispatched to affected branches")
        else:
            console.print("[red]Failed to enable Medic[/red] - check trigger_config.json")

    elif command == "off":
        if set_enabled(False):
            logger.info("[MEDIC] Medic DISABLED - error dispatch suppressed")
            console.print("[yellow]Medic DISABLED[/yellow] - error dispatch suppressed")
            console.print("  Errors still detected and logged to medic_suppressed.log")
        else:
            console.print("[red]Failed to disable Medic[/red] - check trigger_config.json")

    elif command == "status":
        enabled = is_enabled()
        # Get watcher status
        watcher_active = False
        try:
            from trigger.apps.modules.branch_log_events import status
            watcher_info = status()
            watcher_active = watcher_info.get('active', False)
        except Exception:
            logger.warning("[MEDIC] Could not get watcher status")

        suppression = get_suppression_stats()
        rate_limits = get_rate_limit_stats()
        muted = get_muted_branches()

        state_color = "green" if enabled else "yellow"
        state_text = "ENABLED" if enabled else "DISABLED"
        if watcher_active:
            watcher_text = "running"
        elif enabled:
            watcher_text = "standby - lazy start"
        else:
            watcher_text = "stopped"
        muted_text = ", ".join(f"@{b}" for b in muted) if muted else "none"

        console.print("Medic Status")
        console.print(f"  State:           [{state_color}]{state_text}[/{state_color}]")
        console.print(f"  Log watcher:     {watcher_text}")
        console.print(f"  Muted branches:  {muted_text}")
        console.print(f"  Suppressed:      {suppression['suppressed_count']}")
        console.print(f"  Last suppressed: {suppression['last_suppressed']}")
        console.print(f"  Rate limited:    {rate_limits['rate_limited_count']}")
        console.print(f"  Last rate limit: {rate_limits['last_rate_limited']}")
        console.print()
        if enabled and not watcher_active:
            console.print("  [dim]Medic will activate when branch sessions start[/dim]")
        elif not enabled:
            console.print("  [dim]All error dispatch suppressed. Errors logged to medic_suppressed.log[/dim]")

    return True


if __name__ == "__main__":
    from cli.apps.modules import console

    if len(sys.argv) == 1 or sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    handle_command(sys.argv[1], sys.argv[2:])
