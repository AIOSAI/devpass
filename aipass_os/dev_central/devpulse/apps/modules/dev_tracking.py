#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: dev_tracking.py - Development Tracking Module
# Date: 2025-11-16
# Version: 1.0.0
# Category: Module
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-16): Initial version - seed-compliant dev tracking
#
# CODE STANDARDS:
#   - Modules orchestrate, handlers implement
#   - handle_command() interface for drone routing
#   - CLI services for output (no print())
# =============================================

"""
Development Tracking Module

Quick entry system for dev.local.md files across branches.
Supports: add, status, sections commands
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

# Standard library imports
from typing import List

# Infrastructure imports (after sys.path setup, no prefix needed)
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header, success, error

# Handler imports - use full path from home since devpulse is in aipass_os/dev_central/
from aipass_os.dev_central.devpulse.apps.handlers.dev_local import ops as dev_ops
from aipass_os.dev_central.devpulse.apps.handlers.template import ops as template_ops
from aipass_os.dev_central.devpulse.apps.handlers.json import json_handler
from aipass_os.dev_central.devpulse.apps.handlers.central_writer import update_central

# =============================================================================
# MODULE INTERFACE
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle dev tracking commands

    Args:
        command: Command to execute
        args: Command arguments

    Returns:
        True if command was handled, False otherwise
    """
    # Check if this module handles the command
    if command != 'dev':
        return False

    # Handle --help flag
    if args and args[0] == '--help':
        show_help()
        return True

    # Parse subcommand
    if not args:
        show_help()
        return True

    subcommand = args[0]

    if subcommand == 'add':
        return cmd_add(args[1:])
    elif subcommand == 'status':
        return cmd_status(args[1:])
    elif subcommand == 'sections':
        return cmd_sections(args[1:])
    else:
        error(f"Unknown subcommand: {subcommand}")
        console.print("Run 'dev --help' for usage")
        return True


# =============================================================================
# COMMANDS
# =============================================================================

def cmd_add(args: List[str]) -> bool:
    """
    Add entry to dev.local.md

    Usage: dev add @branch "Section" "entry text"
    """
    # Handle --help flag
    if args and args[0] == '--help':
        console.print("\n[bold]USAGE:[/bold]")
        console.print("  dev add @branch \"Section\" \"entry text\"")
        console.print("\n[bold]EXAMPLES:[/bold]")
        console.print("  dev add @flow \"Issues\" \"Registry not syncing\"")
        console.print("  dev add @drone \"Upgrades\" \"Add progress bars\"\n")
        return True

    if len(args) < 3:
        error("Usage: dev add @branch \"Section\" \"entry text\"")
        return True

    branch_arg = args[0]
    section_name = args[1]
    entry_text = args[2]

    # Log operation
    json_handler.log_operation(
        "add_entry",
        {"branch": branch_arg, "section": section_name, "entry": entry_text[:50]}
    )

    # Resolve branch path
    branch_path = dev_ops.resolve_branch(branch_arg)
    if branch_path is None:
        error(f"Branch not found: {branch_arg}")
        return True

    # Write entry
    ok, detail = dev_ops.write_entry_to_dev_local(
        branch_path,
        section_name,
        entry_text
    )

    if ok:
        success(f"Entry added to {detail} in {branch_path.name}/dev.local.md")

        # Update central.json
        try:
            update_central()
        except Exception as e:
            logger.error(f"Failed to update central.json: {e}")
            # Don't break dev add if central update fails
    else:
        error(f"Failed to add entry: {detail}")

    return True


def cmd_status(args: List[str]) -> bool:
    """
    Check template compliance status

    Usage: dev status @branch
    """
    if len(args) < 1:
        error("Usage: dev status @branch")
        return True

    branch_arg = args[0]

    # Resolve branch path
    branch_path = dev_ops.resolve_branch(branch_arg)
    if branch_path is None:
        error(f"Branch not found: {branch_arg}")
        return True

    # Find dev.local.md
    dev_file = dev_ops.find_dev_local_file(branch_path)
    if dev_file is None:
        error(f"dev.local.md not found in {branch_path}")
        return True

    # Check compliance
    is_compliant, missing_sections = template_ops.check_template_compliance(dev_file)

    header(f"Template Compliance: {branch_path.name}")

    if is_compliant:
        success("✓ Fully compliant with template")
    else:
        console.print(f"\n⚠️  Missing {len(missing_sections)} sections:\n")
        for section in missing_sections:
            console.print(f"  - {section}")

    return True


def cmd_sections(args: List[str]) -> bool:
    """
    List available sections from template

    Usage: dev sections
    """
    sections = template_ops.get_available_sections()

    header("Available Sections")

    if sections:
        for section in sections:
            console.print(f"  • {section}")
        console.print(f"\n[dim]Total: {len(sections)} sections[/dim]")
    else:
        error("No sections found in template")

    return True


# =============================================================================
# INTROSPECTION & HELP
# =============================================================================

def print_introspection():
    """Display module info and connected handlers when run directly"""
    console.print()
    console.print("[bold cyan]Dev Tracking Module[/bold cyan]")
    console.print()

    console.print("[yellow]Connected Handlers:[/yellow]")
    console.print()

    # Show handler domains this module uses
    console.print("  [cyan]handlers/dev_local/[/cyan]")
    console.print("    [dim]- ops.py (dev.local.md operations)[/dim]")
    console.print()
    console.print("  [cyan]handlers/template/[/cyan]")
    console.print("    [dim]- ops.py (template parsing)[/dim]")
    console.print()
    console.print("  [cyan]handlers/json/[/cyan]")
    console.print("    [dim]- json_handler.py (operation logging)[/dim]")
    console.print()

    console.print("[dim]Run 'python3 dev_tracking.py --help' for usage[/dim]")
    console.print()


def show_help():
    """Show help information"""
    header("DEVPULSE - Development Tracking")

    console.print("""
[bold]USAGE:[/bold]
  python3 devpulse.py dev <subcommand> [options]

[bold]SUBCOMMANDS:[/bold]
  add @branch "Section" "text"  - Add entry to dev.local.md section
  status @branch                - Check template compliance
  sections                      - List available sections

[bold]EXAMPLES:[/bold]
  python3 devpulse.py dev add @flow "Issues" "Registry not syncing"
  python3 devpulse.py dev add @drone "Upgrades" "Add progress bars"
  python3 devpulse.py dev status @flow
  python3 devpulse.py dev sections

[bold]BRANCH NOTATION:[/bold]
  @flow   - /home/aipass/aipass_core/flow
  @drone  - /home/aipass/aipass_core/drone
  .       - Current working directory

[bold]OPTIONS:[/bold]
  --help  - Show this help message
    """)


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # Show introspection when run without arguments
    if len(sys.argv) == 1:
        print_introspection()
        sys.exit(0)
    
    # Handle help flag
    if sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
        sys.exit(0)
    
    # Execute command
    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    if handle_command(command, args):
        sys.exit(0)
    else:
        console.print()
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print()
        console.print("Run [dim]python3 dev_tracking.py --help[/dim] for usage")
        console.print()
        sys.exit(1)
