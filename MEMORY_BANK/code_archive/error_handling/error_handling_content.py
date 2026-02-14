#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: error_handling_content.py - Error Handling Standards Content Handler
# Date: 2025-11-13
# Version: 0.1.0
# Category: seed/standards/handlers
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-13): Initial handler - Error handling standards content
#
# CODE STANDARDS:
#   - Handler provides content, module orchestrates output
#   - Pure function - returns string, no side effects
#
# COMMANDS:
#   - Commands: error_handling, errors, error
# =============================================

"""
Error Handling Standards Content Handler

Provides formatted error handling standards content.
Module orchestrates, handler implements.
"""


def get_error_handling_standards() -> str:
    """Return formatted error handling standards content with Rich markup

    Returns:
        str: Formatted standards text with Rich styling
    """
    lines = [
        "[bold cyan]CORE PRINCIPLE:[/bold cyan]",
        "  [bold]Fail honestly.[/bold] CLI provides error handling as a service.",
        "",
        "[bold cyan]SINGLE IMPORT:[/bold cyan]",
        "  [dim]from cli.apps.modules import ([/dim]",
        "  [dim]    error_handler,              # Service instance[/dim]",
        "  [dim]    OperationResult,            # Result data structure[/dim]",
        "  [dim]    track_operation,            # Decorator for auto-tracking[/dim]",
        "  [dim]    continue_on_error,          # Never raise, always return result[/dim]",
        "  [dim]    collect_results             # Batch aggregation[/dim]",
        "  [dim])[/dim]",
        "",
        "[yellow]MAIN RULES:[/yellow]",
        "",
        "[bold yellow]⚠️  MANDATORY: Entry Point Decorator[/bold yellow]",
        "   [bold]ALL branch entry points MUST use @track_operation on route_command()[/bold]",
        "   • [green]✅ System-wide standard[/green] (deployed to 9/10 branches)",
        "   • Import: [dim]from cli.apps.modules.error_handler import track_operation[/dim]",
        "   • Decorate: [dim]@track_operation[/dim] on [dim]route_command()[/dim] function",
        "   • [yellow]Status:[/yellow] Production (2025-11-16 deployment)",
        "",
        "[bold]1. Use Decorators[/bold]",
        "   • [bold cyan]@track_operation[/bold cyan] - Catches exceptions, formats output, logs to Prax",
        "   • [bold cyan]@continue_on_error[/bold cyan] - Batch operations that continue on failure",
        "   • [bold cyan]@collect_results[/bold cyan] - Aggregate multiple operation results",
        "",
        "[bold]2. Return OperationResult[/bold]",
        "   • [green]OperationResult.success_result()[/green] - Operation succeeded",
        "   • [yellow]OperationResult.skip_result()[/yellow] - Intentionally skipped (not an error)",
        "   • [red]OperationResult.fail_result()[/red] - Operation failed",
        "",
        "[bold]3. Let Exceptions Bubble[/bold]",
        "   • Decorators catch them automatically",
        "   • Auto-categorized (FILESYSTEM, NETWORK, VALIDATION, etc.)",
        "   • Logged to Prax and error handler JSON",
        "",
        "[bold]4. Skip vs Fail[/bold]",
        "   • Skip = intentional bypass (\"already exists\", \"nothing to do\")",
        "   • Fail = actual error (\"permission denied\", \"file not found\")",
        "",
        "[bold cyan]QUICK EXAMPLE:[/bold cyan]",
        "",
        "  [dim]@track_operation[/dim]",
        "  [dim]def create_branch(path: str) -> OperationResult:[/dim]",
        "  [dim]    if Path(path).exists():[/dim]",
        "  [dim]        return OperationResult.skip_result(\"create_branch\", \"already exists\")[/dim]",
        "  [dim][/dim]",
        "  [dim]    Path(path).mkdir(parents=True)  # Exception auto-caught by decorator[/dim]",
        "  [dim]    return OperationResult.success_result(\"create_branch\", f\"Created {path}\")[/dim]",
        "",
        "  [dim]# Output: ✅ create_branch completed[/dim]",
        "  [dim]# OR:     ⏭️  create_branch: already exists[/dim]",
        "  [dim]# OR:     ❌ create_branch failed: Permission denied[/dim]",
        "",
        "[yellow]KEY WARNINGS:[/yellow]",
        "",
        "  [red]❌ DON'T[/red] silently fail (return None/False without logging)",
        "  [red]❌ DON'T[/red] write manual try/except if decorator can handle it",
        "  [red]❌ DON'T[/red] duplicate error handling code - use CLI service",
        "",
        "  [green]✅ DO[/green] return OperationResult for all operations",
        "  [green]✅ DO[/green] provide context in result.details (file paths, counts, etc.)",
        "  [green]✅ DO[/green] use @collect_results for batch operations",
        "",
        "[bold cyan]PRAX INTEGRATION:[/bold cyan]",
        "  Decorators automatically log to Prax - [dim]no explicit logger calls needed[/dim]",
        "",
        "  [dim]from prax.apps.modules.logger import system_logger as logger[/dim]",
        "  [dim]# CLI error handler calls logger.info/error behind the scenes[/dim]",
        "",
        "[bold cyan]BENEFITS:[/bold cyan]",
        "  • Consistent formatting across all branches",
        "  • Update CLI once → affects entire system",
        "  • Automatic error categorization",
        "  • Prax logging integration",
        "  • Rich console output with colors",
        "",
        "[bold cyan]DEMONSTRATION:[/bold cyan]",
        "  [dim]/home/aipass/seed/apps/modules/test_cli_errors.py[/dim]",
        "  Shows all patterns: decorators, manual results, batch operations",
        "",
        "[bold cyan]REFERENCE:[/bold cyan]",
        "  [dim]/home/aipass/standards/CODE_STANDARDS/error_handling.md[/dim]",
        "  Full standard with examples, cookbook, and advanced patterns",
        "",
        "─" * 70,
    ]

    return "\n".join(lines)
