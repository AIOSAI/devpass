#!/home/aipass/.venv/bin/python3

# META DATA HEADER
# Name: unified_stream.py - Unified Display Handler
# Version: 0.1.0
# Created: 2025-11-23
# Purpose: Single point for all monitoring terminal output
# Dependencies: rich console
# Status: Active

"""
Unified Stream Display Handler

Single point for all monitoring terminal output with:
- Event formatting with branch attribution
- Color coding by event type
- Thread-safe console output
- Status displays and headers
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from threading import Lock
import sys

try:
    from cli.apps.modules import console
except ImportError:
    from rich.console import Console
    console = Console()

# Thread safety
_print_lock = Lock()

# Color schemes by event type and level
COLORS = {
    'file_created': 'green',
    'file_modified': 'yellow',
    'file_deleted': 'red',
    'file_moved': 'blue',
    'log_info': 'white',
    'log_warning': 'yellow',
    'log_error': 'red',
    'log_critical': 'bold red',
    'module_loaded': 'cyan',
    'module_error': 'red',
    'system_info': 'blue',
    'system_warning': 'yellow',
    'system_error': 'bold red',
}

# Symbols for different event types
SYMBOLS = {
    'file': '📁',
    'log': '📝',
    'module': '⚡',
    'system': '🔧',
    'error': '❌',
    'warning': '⚠️',
    'success': '✅',
    'info': 'ℹ️',
}

# Branch display width
BRANCH_WIDTH = 8

# Level-based color mapping (simplified)
LEVEL_COLORS = {
    'error': 'red',
    'warning': 'yellow',
    'critical': 'bold red',
    'info': 'white',
    'success': 'green',
}

# Branch-specific colors for visual distinction
BRANCH_COLORS = {
    'SEED': 'green',
    'DRONE': 'cyan',
    'FLOW': 'blue',
    'PRAX': 'magenta',
    'CLI': 'yellow',
    'CORTEX': 'bright_blue',
    'AI_MAIL': 'bright_cyan',
    'BACKUP_SYSTEM': 'bright_green',
    'MEMORY_BANK': 'bright_magenta',
    'DEVPULSE': 'bright_yellow',
    'API': 'bright_red',
    'SECURITY': 'red',
    'AIPASS': 'bold white',
}


def print_event(event_type: str, branch: str, message: str, level: str = 'info'):
    """
    Format and print event with branch attribution

    Format:
    [HH:MM:SS] [BRANCH] Message text

    Color coding:
    - Timestamp: dim
    - Branch name: unique color per branch
    - Message: colored by level (error=red, warning=yellow, info=white)

    Args:
        event_type: Type of event (file, log, module, system)
        branch: Branch name for attribution
        message: Event message
        level: Event level (info, warning, error, critical)
    """
    with _print_lock:
        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Get branch color (unique per branch)
        branch_upper = branch.upper()
        branch_color = BRANCH_COLORS.get(branch_upper, 'white')

        # Format branch with fixed width padding and color
        branch_formatted = f"[{branch_color}][{branch_upper:<{BRANCH_WIDTH}}][/{branch_color}]"

        # Get message color based on level
        msg_color = LEVEL_COLORS.get(level, 'white')

        # Format and print - timestamp, branch colored, message colored by level
        console.print(f"[dim]{timestamp}[/dim] {branch_formatted} [{msg_color}]{message}[/{msg_color}]")


def print_command_separator(branch: str, command: str, caller: Optional[str] = None):
    """
    Print prominent command separator/header with caller attribution.

    Shows when a new command is executed, visually grouping its output.

    Args:
        branch: Branch that executed the command (log location)
        command: The command that was run (e.g., "seed.py audit @prax")
        caller: Branch that initiated the command (optional)
    """
    with _print_lock:
        branch_color = BRANCH_COLORS.get(branch.upper(), 'white')
        console.print()
        console.print(f"[bold {branch_color}]{'─' * 60}[/bold {branch_color}]")

        # Show caller if available
        if caller:
            caller_color = BRANCH_COLORS.get(caller.upper(), 'cyan')
            console.print(f"[{caller_color}]CALLER: {caller}[/{caller_color}]")

        console.print(f"[bold {branch_color}]▶ {command}[/bold {branch_color}]")
        console.print(f"[bold {branch_color}]{'─' * 60}[/bold {branch_color}]")


def print_file_event(event_type: str, branch: str, file_path: str, details: Optional[str] = None):
    """
    Print file system event

    Args:
        event_type: created, modified, deleted, moved
        branch: Branch name
        file_path: Path to file
        details: Optional additional details
    """
    message = f"File {event_type}: {file_path}"
    if details:
        message += f" ({details})"

    # Map file event types to levels for color coding
    level_map = {
        'created': 'success',
        'modified': 'info',
        'deleted': 'warning',
        'moved': 'info'
    }
    level = level_map.get(event_type, 'info')
    print_event('file', branch, message, level)


def print_log_event(branch: str, level: str, message: str, source: Optional[str] = None):
    """
    Print log file event

    Args:
        branch: Branch name
        level: Log level (info, warning, error, critical)
        message: Log message
        source: Optional source file/module
    """
    # Add level prefix for errors and warnings
    if level in ['error', 'critical']:
        log_msg = f"ERROR: {message}"
    elif level == 'warning':
        log_msg = f"WARNING: {message}"
    else:
        log_msg = message

    if source:
        log_msg = f"[{source}] {log_msg}"

    print_event('log', branch, log_msg, level)


def print_module_event(branch: str, module_name: str, status: str, details: Optional[str] = None):
    """
    Print module loading event

    Args:
        branch: Branch name
        module_name: Name of module
        status: loaded, error, reloaded, started, stopped
        details: Optional error or status details
    """
    message = f"Module {status}: {module_name}"
    if details:
        message += f" - {details}"

    # Map status to level for color coding
    level_map = {
        'error': 'error',
        'failed': 'error',
        'loaded': 'success',
        'started': 'success',
        'stopped': 'warning',
        'reloaded': 'info'
    }
    level = level_map.get(status, 'info')
    print_event('module', branch, message, level)


def print_header():
    """Print monitoring system header"""
    with _print_lock:
        console.print("\n[bold cyan]═══════════════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]    PRAX Monitoring System v0.1.0[/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════════════════[/bold cyan]")
        console.print("[dim]Type 'help' for commands, 'quit' to exit[/dim]\n")


def print_status(watched_branches: List[str], verbosity: int, filters: Optional[Dict] = None):
    """
    Display current monitoring status

    Args:
        watched_branches: List of branches being monitored
        verbosity: Current verbosity level (0-2)
        filters: Optional filter configuration
    """
    with _print_lock:
        console.print("\n[bold]Current Status:[/bold]")
        console.print(f"  Watching: [cyan]{', '.join(watched_branches) if watched_branches else 'All branches'}[/cyan]")
        console.print(f"  Verbosity: [yellow]{verbosity}[/yellow]")

        if filters:
            console.print("  Filters:")
            if filters.get('file_types'):
                console.print(f"    File types: {', '.join(filters['file_types'])}")
            if filters.get('log_levels'):
                console.print(f"    Log levels: {', '.join(filters['log_levels'])}")
            if filters.get('exclude_patterns'):
                console.print(f"    Excluded: {', '.join(filters['exclude_patterns'])}")
        console.print()


def print_help():
    """Display help information"""
    with _print_lock:
        console.print("\n[bold]Available Commands:[/bold]")
        console.print("  [cyan]help[/cyan]              - Show this help")
        console.print("  [cyan]status[/cyan]            - Show monitoring status")
        console.print("  [cyan]clear[/cyan]             - Clear screen")
        console.print("  [cyan]filter <type>[/cyan]    - Add filter")
        console.print("  [cyan]verbosity <0-2>[/cyan]  - Set verbosity level")
        console.print("  [cyan]watch <branch>[/cyan]   - Watch specific branch")
        console.print("  [cyan]unwatch <branch>[/cyan] - Stop watching branch")
        console.print("  [cyan]quit/exit[/cyan]        - Exit monitoring\n")


def print_error(message: str, details: Optional[str] = None):
    """
    Print error message

    Args:
        message: Error message
        details: Optional error details
    """
    with _print_lock:
        console.print(f"[bold red]ERROR:[/bold red] {message}")
        if details:
            console.print(f"[dim]{details}[/dim]")


def print_warning(message: str):
    """Print warning message"""
    with _print_lock:
        console.print(f"[yellow]WARNING:[/yellow] {message}")


def print_success(message: str):
    """Print success message"""
    with _print_lock:
        console.print(f"[green]SUCCESS:[/green] {message}")


def print_info(message: str):
    """Print info message"""
    with _print_lock:
        console.print(f"[blue]INFO:[/blue] {message}")


def clear_screen():
    """Clear terminal screen"""
    with _print_lock:
        console.clear()


def print_separator():
    """Print visual separator"""
    with _print_lock:
        console.print("[dim]─────────────────────────────────────────[/dim]")


def format_event_summary(events: Dict[str, int]) -> str:
    """
    Format event summary statistics

    Args:
        events: Dictionary of event type counts

    Returns:
        Formatted summary string
    """
    parts = []
    for event_type, count in events.items():
        if count > 0:
            parts.append(f"{event_type}: {count}")
    return ", ".join(parts) if parts else "No events"
