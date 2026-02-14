#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Terminal UI handlers for Nexus v2 using Rich library"""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from rich.console import Console

console = Console()

def print_startup_banner():
    """Display Nexus startup banner"""
    console.print()
    console.print("[bold magenta]╔═══════════════════════════════════════════════════╗[/bold magenta]")
    console.print("[bold magenta]║[/bold magenta]              [bold white]N E X U S   v 2[/bold white]                  [bold magenta]║[/bold magenta]")
    console.print("[bold magenta]║[/bold magenta]     [dim]Presence over performance. Truth over fluency.[/dim]     [bold magenta]║[/bold magenta]")
    console.print("[bold magenta]╚═══════════════════════════════════════════════════╝[/bold magenta]")
    console.print()

def print_status(message: str, success: bool = True):
    """Print status message with checkmark or X"""
    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")

def print_hint(message: str):
    """Print dim hint text"""
    console.print(f"[dim]{message}[/dim]")

def get_user_input() -> str:
    """Get user input with styled prompt"""
    console.print()
    return console.input("[bold green]You:[/bold green] ")

def print_nexus_response(response: str):
    """Print Nexus response with styling"""
    console.print()
    console.print(f"[bold magenta]Nexus:[/bold magenta] {response}")

def print_error(message: str):
    """Print error message"""
    console.print(f"[red bold]Error:[/red bold] {message}")

def print_goodbye():
    """Print goodbye message"""
    console.print()
    console.print("[magenta]Nexus:[/magenta] [dim]Ending session. Until next time.[/dim]")
    console.print()
