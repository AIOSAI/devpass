#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: perf_monitor.py - Performance Monitoring Module
# Date: 2025-11-23
# Version: 1.0.0
# Category: vscode/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-23): Initial module - Pylance/VS Code performance monitoring
#
# CODE STANDARDS:
#   - Module orchestrates, handler implements
#   - Implements handle_command() for auto-discovery
# =============================================

"""
Performance Monitoring Module

Monitors Pylance and VS Code memory usage.
Run directly or via: drone @vscode perf
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Standard library imports
import argparse

# Prax logger
from prax.apps.modules.logger import system_logger as logger

# CLI services
from cli.apps.modules import console, header

# Handler imports
MODULE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MODULE_ROOT))

from handlers.perf.monitor import (
    gather_stats,
    get_health_status,
    get_recommendation
)

# JSON handler for operation tracking
from handlers.json.json_handler import log_operation


def print_introspection():
    """Display module info and connected handlers"""
    console.print()
    console.print("[bold cyan]Performance Monitor Module[/bold cyan]")
    console.print()
    console.print("[yellow]Connected Handlers:[/yellow]")
    console.print("  [cyan]handlers/perf/[/cyan]")
    console.print("    [dim]- monitor.py[/dim]")
    console.print("  [cyan]handlers/json/[/cyan]")
    console.print("    [dim]- json_handler.py[/dim]")
    console.print()
    console.print("[dim]Run 'python3 perf_monitor.py --help' for usage[/dim]")
    console.print()

    # Log introspection display
    log_operation("introspection_displayed", module_name="perf_monitor")


def print_help():
    """Print help output"""
    console.print()
    console.print("[bold cyan]Performance Monitor Module[/bold cyan]")
    console.print("Monitor Pylance and VS Code memory usage")
    console.print()
    console.print("[yellow]COMMANDS:[/yellow]")
    console.print("  [cyan]performance[/cyan] - Display performance stats")
    console.print()
    console.print("[yellow]OPTIONS:[/yellow]")
    console.print("  [cyan]--files, -f[/cyan] - Include Python file count scan")
    console.print()
    console.print("[yellow]USAGE:[/yellow]")
    console.print("  drone @vscode performance")
    console.print("  python3 perf_monitor.py")
    console.print("  python3 perf_monitor.py --files")
    console.print()
    console.print("[yellow]EXAMPLES:[/yellow]")
    console.print("  [dim]# Via drone[/dim]")
    console.print("  drone @vscode performance")
    console.print()
    console.print("  [dim]# Standalone[/dim]")
    console.print("  python3 perf_monitor.py")
    console.print("  python3 perf_monitor.py --files")
    console.print()


def handle_command(args: argparse.Namespace) -> bool:
    """
    Handle performance monitoring commands

    Args:
        args: Parsed command line arguments

    Returns:
        True if command was handled
    """
    if not hasattr(args, 'command'):
        return False

    if args.command != "performance":
        return False

    # Check for --files flag
    include_files = getattr(args, 'files', False)

    display_stats(include_files)
    return True


def display_stats(include_file_count: bool = False):
    """
    Display performance statistics

    Args:
        include_file_count: Whether to scan and count Python files
    """
    console.print()
    header("Pylance & VS Code Memory Monitor")
    console.print()

    # Gather stats
    stats = gather_stats(include_file_count)

    # Log actual performance metrics for tracking over time
    log_data = {
        "system_ram_percent": round(stats["system"]["percent"], 1),
        "system_ram_used_mb": stats["system"]["used_mb"],
        "pylance_mb": round(stats["pylance"]["memory_mb"], 0),
        "pylance_processes": stats["pylance"]["process_count"],
        "vscode_mb": round(stats["vscode"]["memory_mb"], 0),
        "vscode_processes": stats["vscode"]["process_count"]
    }

    if include_file_count and "python_files" in stats:
        log_data["python_files_count"] = stats["python_files"]

    log_operation("performance_check", log_data, module_name="perf_monitor")

    # System RAM
    sys_used = stats["system"]["used_mb"]
    sys_total = stats["system"]["total_mb"]
    sys_percent = stats["system"]["percent"]
    console.print(f"📊 System RAM: {sys_used:,}MB / {sys_total:,}MB ({sys_percent:.1f}%)")
    console.print()

    # Pylance
    pylance_mb = stats["pylance"]["memory_mb"]
    pylance_count = stats["pylance"]["process_count"]

    if pylance_count > 0:
        health = get_health_status(pylance_mb)
        console.print(f"🐍 Pylance: {pylance_mb:.0f}MB ({pylance_count} process)")

        if health == "critical":
            console.print("   [red]⚠️  CRITICAL: Pylance using >700MB (restart recommended)[/red]")
        elif health == "warning":
            console.print("   [yellow]⚠️  WARNING: Pylance using >600MB (may need restart)[/yellow]")
        elif health == "normal":
            console.print("   [yellow]⚡ Normal range (400-600MB)[/yellow]")
        else:  # healthy
            console.print("   [green]✅ Healthy (<400MB)[/green]")
    else:
        console.print("🐍 Pylance: [dim]Not running[/dim]")

    console.print()

    # VS Code
    vscode_mb = stats["vscode"]["memory_mb"]
    vscode_count = stats["vscode"]["process_count"]
    console.print(f"💻 VS Code: {vscode_mb:.0f}MB ({vscode_count} processes)")
    console.print()

    # Python file count (if requested)
    if include_file_count:
        py_count = stats.get("python_files", 0)
        console.print(f"🔍 Python Files: {py_count:,}")
        console.print("   [dim](After pyrightconfig.json exclusions)[/dim]")
        console.print()

    # Recommendation
    recommendation = get_recommendation(stats)
    if recommendation:
        console.print("─" * 60)
        console.print()
        console.print(f"💡 [bold]Recommendation:[/bold] {recommendation}")
        console.print()

    console.print("─" * 60)
    console.print()


if __name__ == "__main__":
    # Show introspection when run without arguments
    if len(sys.argv) == 1:
        print_introspection()
        sys.exit(0)

    # Handle help flag
    if sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    # Confirm logger connection
    logger.info("Prax logger connected to perf_monitor")

    # Parse arguments
    parser = argparse.ArgumentParser(description='Performance Monitor')
    parser.add_argument('--files', '-f', action='store_true', help='Include Python file count')
    args = parser.parse_args()

    # Display stats
    display_stats(args.files)
