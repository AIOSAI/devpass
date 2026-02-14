#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: activated_commands.py - Activated Commands Orchestrator Module
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-29): Initial creation - handles activated custom commands
#
# CODE STANDARDS:
#   - Thin orchestrator pattern - delegates to handlers in drone/apps/handlers/
#   - Type hints on all functions
#   - Google-style docstrings
#   - Prax logger (system_logger as logger)
#   - CLI module for output (Rich console)
#   - Standard try/except error handling
# =============================================

"""
Activated Commands Orchestrator Module

Thin orchestration layer that handles execution of activated custom commands.
Maps user commands like "plan create" to branch module commands like "@flow create".

This module:
1. Receives a command and arguments from drone.py
2. Tries to match against activated commands in discovery system
3. Executes the mapped branch module if found

Commands are activated via the discovery module (drone scan/activate workflow).

Example:
    User types: drone plan create @seed "My task"
    This module:
    - Looks up "plan create" in activated commands
    - Finds it maps to flow module with command "create"
    - Executes: flow.py create @seed "My task"
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

# CLI services for formatted output
from cli.apps.modules import console

# Import handlers
from drone.apps.handlers.discovery import (
    lookup_activated_command,
    run_branch_module,
)
from drone.apps.handlers.routing import preprocess_args

import json

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "activated_commands"
BRANCH_REGISTRY_PATH = Path.home() / "BRANCH_REGISTRY.json"

# =============================================
# CALLER DETECTION (for Mission Control visibility)
# =============================================

def _detect_caller_branch() -> str:
    """
    Detect which branch is calling based on PWD.

    Returns branch name or 'UNKNOWN' if not detected.
    """
    try:
        cwd = Path.cwd()

        # Walk up to find branch root (has *.id.json)
        current = cwd.resolve()
        for _ in range(10):
            if list(current.glob("*.id.json")):
                # Found branch root - look up in registry
                if BRANCH_REGISTRY_PATH.exists():
                    with open(BRANCH_REGISTRY_PATH, 'r') as f:
                        registry = json.load(f)
                    for branch in registry.get("branches", []):
                        if Path(branch["path"]).resolve() == current:
                            return branch.get("name", "UNKNOWN")
                return current.name.upper()

            parent = current.parent
            if parent == current:
                break
            current = parent
    except Exception:
        pass
    return "UNKNOWN"

# =============================================
# INTROSPECTION
# =============================================

def print_introspection():
    """Display module info and connected handlers"""
    console.print()
    console.print("[bold cyan]Activated Commands Module - Custom Command Execution[/bold cyan]")
    console.print()

    console.print("[yellow]Purpose:[/yellow]")
    console.print("  Handles execution of activated custom commands discovered via 'drone scan'")
    console.print()

    console.print("[yellow]How it works:[/yellow]")
    console.print("  1. User types: drone plan create @seed \"My task\"")
    console.print("  2. This module receives: command='plan', args=['create', '@seed', 'My task']")
    console.print("  3. Tries to match 'plan create' against activated commands")
    console.print("  4. Executes the mapped branch module if found")
    console.print()

    console.print("[yellow]Connected Handlers:[/yellow]")
    console.print("  [cyan]drone/apps/handlers/discovery/activation.py[/cyan]")
    console.print("    [dim]- lookup_activated_command()[/dim]")
    console.print("  [cyan]drone/apps/handlers/discovery/system_operations.py[/cyan]")
    console.print("    [dim]- run_branch_module()[/dim]")
    console.print("  [cyan]drone/apps/handlers/routing/args.py[/cyan]")
    console.print("    [dim]- preprocess_args()[/dim]")
    console.print()

    console.print("[dim]Run 'drone discovery list' to see all activated commands[/dim]")
    console.print()

# =============================================
# COMMAND MATCHING
# =============================================

def _try_match_command(command: str, args: list) -> dict | None:
    """
    Try to match command + args against activated commands

    Tries progressively longer command strings:
    - "plan create @seed My" (4 words)
    - "plan create @seed" (3 words)
    - "plan create" (2 words)
    - "plan" (1 word)

    Args:
        command: First word of command
        args: Remaining arguments

    Returns:
        Command info dict if found, None otherwise

    Example:
        >>> _try_match_command("plan", ["create", "@seed", "My task"])
        {'module_path': '...', 'command_name': 'create', ...}
    """
    # Build potential command strings (up to 4 words)
    max_words = min(4, len(args) + 1)

    for word_count in range(max_words, 0, -1):
        if word_count == 1:
            # Just the command itself
            potential_cmd = command
            remaining_args = args
        else:
            # Command + (word_count - 1) args
            words_to_take = word_count - 1
            potential_cmd = command + " " + " ".join(args[:words_to_take])
            remaining_args = args[words_to_take:]

        # Try lookup
        cmd_info = lookup_activated_command(potential_cmd)
        if cmd_info:
            # Found it! Return with remaining args
            cmd_info['remaining_args'] = remaining_args
            return cmd_info

    return None

# =============================================
# ORCHESTRATION
# =============================================

def handle_command(command: str, args: list) -> bool:
    """
    Handle activated custom commands

    Tries to match the command + args against activated commands in the discovery
    system. If found, executes the mapped branch module.

    Args:
        command: Command name (e.g., "plan")
        args: Command arguments (e.g., ["create", "@seed", "My task"])

    Returns:
        True if command was found and handled, False otherwise

    Example:
        >>> handle_command("plan", ["create", "@seed", "My task"])
        # Looks up "plan create", finds it maps to flow module
        # Executes: flow.py create @seed "My task"
        True
    """
    try:
        # Try to match command
        cmd_info = _try_match_command(command, args)

        if not cmd_info:
            # Not an activated command
            return False

        # Extract info
        module_path = Path(cmd_info['module_path'])
        command_name = cmd_info['command_name']
        remaining_args = cmd_info.get('remaining_args', [])

        # Build full args: [command_name] + remaining_args
        module_args = [command_name] + remaining_args

        # Resolve @ arguments (e.g., @seed → /home/aipass/seed)
        resolved_args = preprocess_args(module_args)

        # Detect caller branch from PWD for Mission Control visibility
        caller_name = _detect_caller_branch()

        # Log execution with caller attribution
        logger.info(
            f"[{MODULE_NAME}] Executing activated command [CALLER:{caller_name}]: "
            f"{module_path.name} {' '.join(resolved_args)}"
        )

        # Execute the branch module (timeout handled by run_branch_module based on command args)
        success = run_branch_module(module_path, resolved_args)

        if not success:
            console.print(f"[red]Command execution failed[/red]")
            logger.error(
                f"[{MODULE_NAME}] Activated command failed: "
                f"{module_path.name} {' '.join(module_args)}"
            )

        return True

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error handling command '{command}': {str(e)}", exc_info=True)
        console.print(f"[red]Error executing activated command: {str(e)}[/red]")
        return True  # We handled it (even if it failed)

# =============================================
# HELP SYSTEM
# =============================================

def print_help():
    """Display help using Rich formatted output"""
    console.print()
    console.print("[bold cyan]Activated Commands Module - Custom Command Execution[/bold cyan]")
    console.print()

    console.print("[yellow]PURPOSE:[/yellow]")
    console.print("  This module automatically executes activated custom commands.")
    console.print("  It runs in the background as part of drone's command routing.")
    console.print()

    console.print("[yellow]HOW IT WORKS:[/yellow]")
    console.print("  1. Commands are discovered via 'drone scan @module'")
    console.print("  2. Commands are activated via 'drone activate <system>'")
    console.print("  3. This module handles execution when you use the activated command")
    console.print()

    console.print("[yellow]EXAMPLE WORKFLOW:[/yellow]")
    console.print("  [cyan]# Discover and activate[/cyan]")
    console.print("  drone scan @flow")
    console.print("  drone activate flow")
    console.print("    → Activate 'plan create' as 'plan create'")
    console.print()
    console.print("  [cyan]# Use the activated command[/cyan]")
    console.print("  drone plan create @seed \"My task\"")
    console.print("    → This module executes: flow.py create @seed \"My task\"")
    console.print()

    console.print("[yellow]MANAGING ACTIVATED COMMANDS:[/yellow]")
    console.print("  [cyan]drone discovery list[/cyan]      View all activated commands")
    console.print("  [cyan]drone discovery remove[/cyan]    Remove an activated command")
    console.print("  [cyan]drone discovery edit[/cyan]      Edit an activated command")
    console.print()

    console.print("[dim]This module is called automatically by drone.py[/dim]")
    console.print()

# =============================================
# MAIN ENTRY
# =============================================

def main():
    """Main entry point for testing"""
    import sys

    # Handle help flags
    args = sys.argv[1:]

    # Show introspection when run without arguments
    if len(args) == 0:
        print_introspection()
        return True

    # Show help only for explicit help flags
    if args[0] in ['--help', '-h', 'help']:
        print_help()
        return True

    # This module doesn't have direct commands - it's called by drone.py
    console.print()
    console.print("[yellow]This module is called automatically by drone.py[/yellow]")
    console.print()
    console.print("To manage activated commands:")
    console.print("  [cyan]drone discovery list[/cyan]      View all activated commands")
    console.print("  [cyan]drone discovery activate[/cyan]  Activate new commands")
    console.print("  [cyan]drone discovery remove[/cyan]    Remove an activated command")
    console.print()

if __name__ == "__main__":
    main()
