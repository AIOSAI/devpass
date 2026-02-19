#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: display.py - D-PLAN display handler
# Date: 2025-12-02
# Version: 1.0.0
# Category: devpulse/handlers/plan
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-12-02): Extracted from dev_flow.py module
#
# CODE STANDARDS:
#   - Handler independence: NO cross-domain imports
#   - NO Prax logging (per 3-tier: modules log, handlers don't)
#   - Returns display content, module handles output
# ==============================================

"""
Display Handler - D-PLAN Help and Introspection

Provides help text and introspection information.
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

# NOTE: Handlers do NOT import Prax logger (per 3-tier standard)

# =============================================================================
# CONFIGURATION
# =============================================================================

DEV_PLANNING_ROOT = Path.home() / "aipass_os" / "dev_central" / "dev_planning"
DEVPULSE_ROOT = Path.home() / "aipass_os" / "dev_central" / "devpulse"
COUNTER_FILE = DEV_PLANNING_ROOT / "counter.json"
TEMPLATE_FILE = DEVPULSE_ROOT / "templates" / "dplan_default.md"

HELP_TEXT = """
[bold]USAGE:[/bold]
  drone @devpulse plan <subcommand> [options]

[bold]SUBCOMMANDS:[/bold]
  create "topic" [--tag tag] [--dir name]  - Create new D-PLAN document
  list [--tag tag] [--status status]       - List D-PLANs (with filters)
  status                                   - Quick overview of plan counts
  close <number>                           - Close plan and archive
  close --all                              - Close all open plans

[bold]EXAMPLES:[/bold]
  drone @devpulse plan create "new feature design"
  drone @devpulse plan create "API upgrade" --tag upgrade
  drone @devpulse plan create "flow improvements" --dir flow
  drone @devpulse plan list
  drone @devpulse plan list --tag idea
  drone @devpulse plan list --status planning
  drone @devpulse plan status
  drone @devpulse plan close 3
  drone @devpulse plan close --all

[bold]TAGS:[/bold]
  idea, upgrade, proposal, bug, research, seed, infrastructure

[bold]STATUS VALUES:[/bold]
  📋 Planning      - Initial state
  🔄 In Progress   - Actively working on design
  ✅ Ready         - Ready for execution (send to Flow)
  ✓  Complete      - Design work done
  ❌ Abandoned     - No longer pursuing

[bold]OPTIONS:[/bold]
  --help         - Show this help message
  --tag <tag>    - Filter by tag (list) or set tag (create)
  --status <s>   - Filter by status (list only)
  --dir <name>   - Create in dev_planning/<name>/ subdirectory
"""


# =============================================================================
# HANDLER FUNCTIONS
# =============================================================================

def get_help_text() -> str:
    """
    Get help information text

    Returns:
        Formatted help text string (Rich markup)
    """
    return HELP_TEXT


def show_help() -> str:
    """
    Get formatted help content for display

    Returns:
        Help text string (caller should use CLI header + print)
    """
    return get_help_text()


def get_introspection_data() -> dict:
    """
    Get module introspection data

    Returns:
        Dictionary with configuration info
    """
    return {
        "name": "D-PLAN Management Module",
        "description": "Manages numbered planning documents in dev_planning/",
        "planning_dir": str(DEV_PLANNING_ROOT),
        "counter_file": str(COUNTER_FILE),
        "template_file": str(TEMPLATE_FILE)
    }


def print_introspection() -> str:
    """
    Get introspection display text

    Returns:
        Formatted introspection text (caller handles output)
    """
    data = get_introspection_data()

    lines = [
        "",
        "[bold cyan]D-PLAN Management Module[/bold cyan]",
        "",
        f"[dim]{data['description']}[/dim]",
        "",
        "[yellow]Configuration:[/yellow]",
        f"  [dim]Planning dir:[/dim] {data['planning_dir']}",
        f"  [dim]Counter file:[/dim] {data['counter_file']}",
        f"  [dim]Template:[/dim] {data['template_file']}",
        "",
        "[dim]Run 'python3 dev_flow.py --help' for usage[/dim]",
        ""
    ]

    return "\n".join(lines)
