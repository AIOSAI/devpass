#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: smoke.py - Smoke Test Orchestrator Module
# Date: 2026-02-15
# Version: 1.0.0
# Category: test/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-15): Initial module - routes smoke command to runner handler
#
# CODE STANDARDS:
#   - Modules orchestrate, handlers implement
#   - Handlers return status dicts, modules handle display
#   - Google-style docstrings, type hints on all functions
# =============================================

"""Smoke tests - Run pytest smoke suite across all branches."""

import sys
from pathlib import Path
from typing import List

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Prax logger (modules CAN import)
from prax.apps.modules.logger import system_logger as logger

# CLI services for formatted output
from cli.apps.modules import console, header

# Internal handler import
# NOTE: Uses importlib file-based loading because "test" collides with
# Python's stdlib test package, making test.apps.* unresolvable.
import importlib.util as _ilu

_RUNNER_PATH = Path(__file__).parent.parent / "handlers" / "testing" / "runner.py"
_spec = _ilu.spec_from_file_location("test.apps.handlers.testing.runner", str(_RUNNER_PATH))
_runner = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_runner)
run_smoke_tests = _runner.run_smoke_tests


# =============================================================================
# HELP DISPLAY
# =============================================================================


def print_help() -> None:
    """Display Rich-formatted help for the smoke command."""
    console.print()
    header("Smoke Tests")
    console.print()

    console.print("[dim]Run pytest smoke suite across all registered branches[/dim]")
    console.print()
    console.print("[bold]" + "-" * 70 + "[/bold]")
    console.print()

    console.print("[bold cyan]USAGE:[/bold cyan]")
    console.print()
    console.print("  [dim]python3 apps/test.py smoke [BRANCH] [OPTIONS][/dim]")
    console.print("  [dim]drone @test smoke [BRANCH] [OPTIONS][/dim]")
    console.print()
    console.print("[bold]" + "-" * 70 + "[/bold]")
    console.print()

    console.print("[bold cyan]ARGUMENTS:[/bold cyan]")
    console.print()
    console.print("  [green]BRANCH[/green]              [dim]Filter tests to a specific branch (e.g., DRONE, SEED)[/dim]")
    console.print()
    console.print("[bold]" + "-" * 70 + "[/bold]")
    console.print()

    console.print("[bold cyan]OPTIONS:[/bold cyan]")
    console.print()
    console.print("  [green]--verbose[/green]            [dim]Show full pytest output with individual test results[/dim]")
    console.print("  [green]--help[/green]               [dim]Show this help message[/dim]")
    console.print()
    console.print("[bold]" + "-" * 70 + "[/bold]")
    console.print()

    console.print("[bold cyan]EXAMPLES:[/bold cyan]")
    console.print()
    console.print("  [dim]# Run all smoke tests[/dim]")
    console.print("  python3 apps/test.py smoke")
    console.print()
    console.print("  [dim]# Run smoke tests for DRONE branch only[/dim]")
    console.print("  python3 apps/test.py smoke DRONE")
    console.print()
    console.print("  [dim]# Verbose output with individual test results[/dim]")
    console.print("  python3 apps/test.py smoke --verbose")
    console.print()
    console.print("  [dim]# Via drone[/dim]")
    console.print("  drone @test smoke")
    console.print("  drone @test smoke SEED --verbose")
    console.print()


# =============================================================================
# RESULT DISPLAY
# =============================================================================


def display_results(results: dict, branch: str | None = None, verbose: bool = False) -> None:
    """Display formatted test results using Rich console.

    Args:
        results: Status dict returned by the runner handler.
        branch: Branch name filter used (for display context), or None.
        verbose: If True, show full pytest output.
    """
    console.print()

    # Header
    scope = f" ({branch})" if branch else " (all branches)"
    header(f"Smoke Test Results{scope}")
    console.print()

    # Summary counts
    if results["success"]:
        status_text = "[bold green]PASSED[/bold green]"
    else:
        status_text = "[bold red]FAILED[/bold red]"

    console.print(f"  Status:   {status_text}")
    console.print(f"  Total:    [cyan]{results['total']}[/cyan]")
    console.print(f"  Passed:   [green]{results['passed']}[/green]")

    if results["failed"] > 0:
        console.print(f"  Failed:   [red]{results['failed']}[/red]")
    else:
        console.print(f"  Failed:   [dim]{results['failed']}[/dim]")

    if results["skipped"] > 0:
        console.print(f"  Skipped:  [yellow]{results['skipped']}[/yellow]")

    if results["errors"] > 0:
        console.print(f"  Errors:   [red]{results['errors']}[/red]")

    console.print()

    # Verbose: show full output
    if verbose and results["output"]:
        console.print("[bold]" + "-" * 70 + "[/bold]")
        console.print()
        console.print("[bold cyan]PYTEST OUTPUT:[/bold cyan]")
        console.print()
        console.print(results["output"])

    # On failure without verbose, show output to help debug
    if not results["success"] and not verbose and results["output"]:
        console.print("[bold]" + "-" * 70 + "[/bold]")
        console.print()
        console.print("[yellow]Test failures detected. Run with --verbose for full output.[/yellow]")
        console.print()


# =============================================================================
# COMMAND HANDLER (Auto-discovery interface)
# =============================================================================


def handle_command(command: str, args: List[str]) -> bool:
    """Handle the 'smoke' command for test.py auto-discovery.

    Parses arguments, delegates to the runner handler, and displays
    formatted results.

    Args:
        command: The command string (must be "smoke" to handle).
        args: Additional arguments: optional branch name, --verbose, --help.

    Returns:
        True if command was handled, False if not our command.
    """
    if command != "smoke":
        return False

    # Check for help flag
    if "--help" in args or "-h" in args:
        print_help()
        return True

    # Parse arguments
    verbose = "--verbose" in args or "-v" in args
    branch = None

    for arg in args:
        if not arg.startswith("-"):
            branch = arg
            break

    # Log the invocation
    scope_msg = f"branch={branch}" if branch else "all branches"
    logger.info(f"[TEST] Running smoke tests ({scope_msg})")

    # Delegate to handler
    results = run_smoke_tests(branch=branch, verbose=verbose)

    # Display results
    display_results(results, branch=branch, verbose=verbose)

    # Log outcome
    if results["success"]:
        logger.info(f"[TEST] Smoke tests passed: {results['passed']}/{results['total']}")
    else:
        logger.warning(f"[TEST] Smoke tests failed: {results['failed']}/{results['total']} failures")

    return True
