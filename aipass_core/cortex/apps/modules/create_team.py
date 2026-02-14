#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: create_team.py - Create New Business Team
# Date: 2026-02-08
# Version: 1.0.0
# Category: cortex
# Commands: create-team, new-team, --help
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-08): Initial implementation - team creation with workspace
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Create Team Module

Creates a new AIPass business team from team template with workspace branch.
Workflow: team template copy, file renaming, workspace creation via branch template,
dual registration (team + workspace).
"""

import sys
from pathlib import Path

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Prax logger
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

# Handler imports
HANDLERS_AVAILABLE = True
HANDLER_ERROR = None

try:
    from cortex.apps.handlers.branch.team_ops import (
        create_team,
        get_next_team_number,
        DEFAULT_TEAM_ROOT
    )
    from cortex.apps.handlers.json import json_handler

except ImportError as e:
    create_team = None  # type: ignore
    get_next_team_number = None  # type: ignore
    DEFAULT_TEAM_ROOT = None  # type: ignore
    json_handler = None  # type: ignore
    HANDLERS_AVAILABLE = False
    HANDLER_ERROR = str(e)
    logger.error(f"Handler import failed: {e}")


# =============================================================================
# CONSTANTS
# =============================================================================

HELP_TEXT = """
======================================================================
CREATE TEAM - AIPass Business Team Creation
======================================================================

Creates a new business team with workspace from team template.

USAGE:
  python3 create_team.py [target_directory]
  cortex create-team [target_directory]
  cortex new-team [target_directory]

ARGUMENTS:
  target_directory  Optional. Path for new team directory.
                    If omitted, auto-creates next team under
                    aipass_business/hq/ (team_4, team_5, etc.)

EXAMPLE:
  cortex create-team                                    # Auto: team_4
  cortex create-team /home/aipass/aipass_business/hq/team_5

WHAT IT DOES:
  - Determines next team number (auto-increment)
  - Copies team template (manager layout: research/, ideas/, decisions/, briefs/)
  - Creates workspace/ inside using standard branch template
  - Registers both team and workspace in BRANCH_REGISTRY.json
  - Generates directory tree documentation

======================================================================

Commands: create-team, new-team, --help
"""


# =============================================================================
# ORCHESTRATION
# =============================================================================

def run_create_team(target_dir: Path) -> bool:
    """
    Orchestrate team creation: call handler, display results, log operations.

    Args:
        target_dir: Path where team will be created

    Returns:
        True if successful, False otherwise
    """
    console.print(f"\n=== Create Business Team ===")
    console.print(f"Target: {target_dir}")
    console.print()

    json_handler.log_operation(
        'team_creation_started',
        {'path': str(target_dir)},
        'create_team'
    )

    result = create_team(target_dir)

    if not result['success']:
        console.print(f"\n❌ Error: {result['error']}")
        json_handler.log_operation(
            'team_creation_failed',
            {'path': str(target_dir), 'error': result['error']},
            'create_team'
        )
        return False

    # Display phase results
    for phase in result.get('phases', []):
        console.print(f"  ✅ {phase}")

    # Display completion report
    console.print(f"\n{'='*70}")
    console.print("TEAM CREATION REPORT")
    console.print(f"{'='*70}")
    console.print(f"Team: {result['team_upper']} ({result['team_name']})")
    console.print(f"Path: {result['path']}")
    console.print(f"Team files copied: {len(result.get('team_copied', []))}")
    console.print(f"Team files renamed: {len(result.get('team_renamed', []))}")
    console.print(f"Team registration: {result.get('team_reg')}")
    console.print(f"Workspace: {result['ws_upper']} ({result['ws_name']})")
    console.print(f"Workspace path: {result.get('ws_path')}")
    console.print(f"Workspace files copied: {len(result.get('ws_copied', []))}")
    console.print(f"Workspace files renamed: {len(result.get('ws_renamed', []))}")
    console.print(f"Workspace registration: {result.get('ws_reg')}")
    console.print(f"\n✅ Team ready at: {target_dir}")
    console.print()

    json_handler.log_operation(
        'team_creation_completed',
        {
            'team': result['team_upper'],
            'workspace': result['ws_upper'],
            'success': True,
            'team_files': len(result.get('team_copied', [])),
            'ws_files': len(result.get('ws_copied', []))
        },
        'create_team'
    )
    json_handler.increment_counter('create_team', 'teams_created')

    try:
        from trigger.apps.modules.core import trigger
        trigger.fire('team_created', team=result['team_upper'], path=str(target_dir))
    except ImportError:
        logger.info("Trigger module not available for team_created event")

    return True


# =============================================================================
# MODULE INTERFACE
# =============================================================================

def handle_command(args) -> bool:
    """
    Orchestrator interface for create_team

    Args:
        args: Command arguments (argparse Namespace)

    Returns:
        True if command handled, False otherwise
    """
    if not hasattr(args, 'command') or args.command not in ['create-team', 'new-team']:
        return False

    if not HANDLERS_AVAILABLE:
        console.print(f"[create_team] Handlers unavailable: {HANDLER_ERROR}")
        return True

    # Determine target directory
    if hasattr(args, 'target_directory') and args.target_directory:
        target_dir = Path(args.target_directory).resolve()
    else:
        next_num = get_next_team_number(DEFAULT_TEAM_ROOT)
        target_dir = DEFAULT_TEAM_ROOT / f"team_{next_num}"
        console.print(f"Auto-increment: creating team_{next_num}")

    return run_create_team(target_dir)


# =============================================================================
# DRONE COMPLIANCE - HELP SYSTEM
# =============================================================================

def print_help():
    """Display drone-compliant help output"""
    console.print(HELP_TEXT)


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    if not HANDLERS_AVAILABLE:
        console.print(f"❌ Handlers unavailable: {HANDLER_ERROR}")
        sys.exit(1)

    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1]).resolve()
    else:
        next_num = get_next_team_number(DEFAULT_TEAM_ROOT)
        target_path = DEFAULT_TEAM_ROOT / f"team_{next_num}"
        console.print(f"Auto-increment: creating team_{next_num}")

    success = run_create_team(target_path)
    sys.exit(0 if success else 1)
