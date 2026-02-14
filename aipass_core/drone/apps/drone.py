#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: drone.py - Drone Branch Entry Point
# Date: 2025-11-29
# Version: 3.0.0
# Category: drone
#
# CHANGELOG (Max 5 entries):
#   - v3.1.0 (2025-11-29): Moved help/introspection back to entry point (Seed pattern)
#   - v3.0.0 (2025-11-29): Thin orchestrator - logic moved to handlers
#   - v2.0.0 (2025-11-13): Seed compliance - entry point pattern
#   - v1.0.0 (2025-11-08): Initial modular architecture
# CODE STANDARDS: Seed pattern compliance - console.print() for all output
# =============================================

"""
Drone Branch - Command Discovery & Execution

Thin orchestrator that routes commands to handlers and modules.
"""

import sys
from pathlib import Path

# =============================================================================
# INFRASTRUCTURE SETUP
# =============================================================================

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

# JSON handler for drone tracking
from drone.apps.handlers.json import json_handler

# Import routing from modules layer
from drone.apps.modules.routing import (
    preprocess_args,
    discover_modules,
    route_command,
)

# Import discovery from modules layer for @ and / pattern support
from drone.apps.modules.discovery import (
    resolve_scan_path,
    run_branch_module,
    resolve_slash_pattern,
    is_long_running_command,
)


# =============================================================================
# HELP & INTROSPECTION (inline per Seed pattern)
# =============================================================================

def show_help() -> None:
    """Display drone help."""
    console.print()
    console.print("[bold cyan]Drone - Command Router & Discovery[/bold cyan]")
    console.print()
    console.print("[dim]Routes commands to AIPass branches. Two ways to run commands:[/dim]")
    console.print()

    # Two ways to run commands
    console.print("[yellow]1. Direct Branch Access (@):[/yellow]")
    console.print()
    console.print("  drone [cyan]@branch[/cyan] command [args]")
    console.print()
    console.print("  [dim]drone @flow create @seed \"My task\"[/dim]")
    console.print("  [dim]drone @seed audit[/dim]")
    console.print("  [dim]drone @ai_mail send @flow \"Subject\" \"Message\"[/dim]")
    console.print()
    console.print("  [cyan]Module access:[/cyan] drone @branch/module [args]")
    console.print("  [dim]drone @seed/imports[/dim]              -> run imports module")
    console.print("  [dim]drone @seed/diagnostics[/dim]          -> run diagnostics module")
    console.print()

    # Activated commands
    console.print("[yellow]2. Activated Commands (shortcuts):[/yellow]")
    console.print()
    console.print("  drone [cyan]<shortcut>[/cyan] [args]")
    console.print()
    console.print("  [dim]drone plan create @seed \"My task\"[/dim]   -> @flow create")
    console.print("  [dim]drone plan list[/dim]                     -> @flow list")
    console.print("  [dim]drone seed audit[/dim]                    -> @seed audit")
    console.print("  [dim]drone email send @flow \"Hi\" \"Msg\"[/dim]   -> @ai_mail send")
    console.print()
    console.print("  Shortcuts are configured via [dim]drone scan/activate[/dim]")
    console.print()

    # Discovery
    console.print("[yellow]Discovery & Management:[/yellow]")
    console.print()
    console.print("  [dim]drone systems[/dim]           List all registered branches")
    console.print("  [dim]drone list[/dim]              List all activated shortcuts")
    console.print("  [dim]drone list flow[/dim]         Shortcuts for specific system")
    console.print("  [dim]drone scan @branch[/dim]      Scan & register branch commands")
    console.print("  [dim]drone activate <system>[/dim] Activate shortcuts interactively")
    console.print("  [dim]drone @branch --help[/dim]    Branch-specific help")
    console.print()

    # Quick start
    console.print("[yellow]Quick Start:[/yellow]")
    console.print()
    console.print("  1. [dim]drone systems[/dim]        -> see available branches")
    console.print("  2. [dim]drone list[/dim]           -> see activated shortcuts")
    console.print("  3. [dim]drone @branch --help[/dim] -> learn a specific branch")
    console.print()


def show_introspection() -> None:
    """Display discovered modules (shown when drone run with no args)."""
    console.print()
    console.print("[bold cyan]Drone - Command Discovery & Execution[/bold cyan]")
    console.print()
    console.print("[dim]Auto-discovers and manages AIPass commands[/dim]")
    console.print()

    # Discover modules (uses routing.discover_modules)
    modules = discover_modules()

    console.print(f"[yellow]Discovered Modules:[/yellow] {len(modules)}")
    console.print()

    for module in modules:
        module_name = module.__name__.split(".")[-1]
        console.print(f"  [cyan]*[/cyan] {module_name}")

    console.print()
    console.print("[dim]Run 'drone --help' for usage information[/dim]")
    console.print()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point - routes commands or shows help"""

    args = sys.argv[1:]

    # Show introspection when run without arguments
    if len(args) == 0:
        show_introspection()
        json_handler.log_operation("drone_introspection_displayed", {"trigger": "no_args"})
        return

    # Show help only for explicit help flags
    if args[0] in ['--help', '-h', 'help']:
        show_help()
        json_handler.log_operation("drone_help_displayed", {"trigger": args[0]})
        return

    command = args[0]
    remaining_args = args[1:] if len(args) > 1 else []

    # Handle @ arguments (drone @seed, drone @flow, etc.)
    if command.startswith('@'):
        # Check for @branch/module pattern (e.g., @seed/imports)
        if '/' in command:
            # Strip @ and route to slash pattern handler
            # @seed/imports -> seed/imports -> resolve_slash_pattern
            slash_command = command[1:]  # Remove @
            module_path, error = resolve_slash_pattern(slash_command)

            if module_path:
                json_handler.log_operation("drone_at_slash_command", {"command": command, "args": remaining_args})
                timeout = None if is_long_running_command(remaining_args) else 30
                resolved_args = preprocess_args(remaining_args)
                run_branch_module(module_path, resolved_args, timeout=timeout)
                return
            else:
                console.print()
                console.print(f"[red]Error: {error}[/red]")
                console.print()
                return

        # Pure @ pattern (drone @seed, drone @flow)
        try:
            module_path = resolve_scan_path(command)
            json_handler.log_operation("drone_at_command", {"target": command, "args": remaining_args})

            # Check if this is a long-running command
            timeout = None if is_long_running_command(remaining_args) else 30

            # Preprocess @ arguments before passing to branch
            resolved_args = preprocess_args(remaining_args)
            run_branch_module(module_path, resolved_args, timeout=timeout)
            return
        except FileNotFoundError as e:
            console.print()
            console.print(f"[red]{e}[/red]")
            console.print()
            return

    # Handle / slash pattern (drone seed/imports -> run imports_standard module) - LEGACY support
    if '/' in command:
        module_path, error = resolve_slash_pattern(command)

        if module_path:
            json_handler.log_operation("drone_slash_command", {"command": command, "args": remaining_args})

            # Check if this is a long-running command
            timeout = None if is_long_running_command(remaining_args) else 30

            # Preprocess @ arguments before passing to branch
            resolved_args = preprocess_args(remaining_args)
            run_branch_module(module_path, resolved_args, timeout=timeout)
            return
        else:
            console.print()
            console.print(f"[red]Error: {error}[/red]")
            console.print()
            return

    # Discover and route to internal drone modules
    modules = discover_modules()

    if not modules:
        console.print()
        console.print("[red]ERROR: No modules found[/red]")
        console.print()
        return

    # Route command to drone modules
    json_handler.log_operation("drone_command_attempted", {"command": command, "modules_discovered": len(modules)})

    if route_command(command, remaining_args, modules):
        return  # Command handled

    # Unknown command
    console.print()
    console.print(f"[red]Unknown command: {command}[/red]")
    console.print()
    console.print(f"[yellow]Tip:[/yellow] Use @ for branch access: [dim]drone @{command} ...[/dim]")
    console.print()
    console.print("Run [dim]drone --help[/dim] for available commands")
    console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\nOperation cancelled by user")
        sys.exit(0)
    except BrokenPipeError:
        # Pipe closed by reader (e.g. head, automated subprocesses)
        # Silence the error and exit cleanly
        import os
        try:
            sys.stdout.close()
        except Exception:
            pass
        os._exit(0)
    except Exception as e:
        logger.error(f"Drone entry point error: {e}", exc_info=True)
        try:
            console.print(f"\nError: {e}")
        except BrokenPipeError:
            pass
        sys.exit(1)
