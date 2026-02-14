#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: create_plan.py - PLAN creation module with location awareness
# Date: 2025-11-16
# Version: 1.0.0
# Category: flow/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-16): Refactored from archive_temp, handler-based architecture
#
# CODE STANDARDS:
#   - Seed v3.0 compliant (imports, architecture, error handling)
# ==============================================

"""
Create PLAN Module - Thin Orchestrator

Orchestrates plan creation workflow by delegating to handlers.
Module contains NO business logic - only workflow coordination.

Workflow:
    1. Parse arguments → command_parser handler
    2. Load registry → registry handlers
    3. Auto-cleanup → plan handlers
    4. Validate location → plan handlers
    5. Calculate paths → plan handlers
    6. Get template → template handlers
    7. Create file → plan handlers
    8. Update registry → plan handlers
    9. Update dashboards → dashboard handlers
    10. Display results → display handlers

Usage:
    From flow.py: flow plan create [location] [subject] [template]
    Standalone: python3 create_plan.py [location] [subject] [template]
"""

import sys
from pathlib import Path
from typing import Tuple, List

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
FLOW_ROOT = AIPASS_ROOT / "flow"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))  # For seed package imports

# External: Prax logger
from prax.apps.modules.logger import system_logger as logger

# JSON handler for operation tracking
from flow.apps.handlers.json import json_handler

# CLI services for display
from cli.apps.modules import console

# Registry handlers (cross-domain - OK for modules)
from flow.apps.handlers.registry.load_registry import load_registry
from flow.apps.handlers.registry.save_registry import save_registry

# Template handlers (cross-domain - OK for modules)
from flow.apps.handlers.template.get_template import get_template

# Plan handlers (same-domain)
from flow.apps.handlers.plan.command_parser import parse_create_plan_args
from flow.apps.handlers.plan.auto_cleanup import auto_close_orphaned_plans
from flow.apps.handlers.plan.resolve_location import resolve_plan_location
from flow.apps.handlers.plan.calculate_relative_path import calculate_relative_location
from flow.apps.handlers.plan.create_file import create_plan_file
from flow.apps.handlers.plan.build_registry_entry import build_plan_registry_entry
from flow.apps.handlers.plan.display import display_plan_created, display_plan_result

# Dashboard handlers (cross-domain - OK for modules)
from flow.apps.handlers.dashboard.update_local import update_dashboard_local
from flow.apps.handlers.dashboard.push_central import push_to_plans_central


# =============================================
# CONFIGURATION
# =============================================

MODULE_NAME = "create_plan"
ECOSYSTEM_ROOT = AIPASS_ROOT

# =============================================
# INTROSPECTION
# =============================================

def print_introspection():
    """Display module info and connected handlers"""
    console.print()
    console.print("[bold cyan]create_plan Module[/bold cyan]")
    console.print()

    console.print("[yellow]Connected Handlers:[/yellow]")
    console.print()

    console.print("  [cyan]handlers/plan/[/cyan]")
    console.print("    [dim]- command_parser.py[/dim]")
    console.print("    [dim]- auto_cleanup.py[/dim]")
    console.print("    [dim]- resolve_location.py[/dim]")
    console.print("    [dim]- calculate_relative_path.py[/dim]")
    console.print("    [dim]- create_file.py[/dim]")
    console.print("    [dim]- build_registry_entry.py[/dim]")
    console.print("    [dim]- display.py[/dim]")
    console.print()

    console.print("  [cyan]handlers/registry/[/cyan]")
    console.print("    [dim]- load_registry.py[/dim]")
    console.print("    [dim]- save_registry.py[/dim]")
    console.print()

    console.print("  [cyan]handlers/template/[/cyan]")
    console.print("    [dim]- get_template.py[/dim]")
    console.print()

    console.print("  [cyan]handlers/dashboard/[/cyan]")
    console.print("    [dim]- update_local.py[/dim]")
    console.print("    [dim]- push_central.py[/dim]")
    console.print()

    console.print("[dim]Run 'python3 create_plan.py --help' for usage[/dim]")
    console.print()

def print_help():
    """Print help information for create_plan module"""
    console.print()
    console.print("[bold cyan]create_plan.py[/bold cyan] - Create new PLAN file")
    console.print()
    console.print("[yellow]COMMANDS:[/yellow]")
    console.print("  create, create_plan")
    console.print()
    console.print("[yellow]USAGE:[/yellow]")
    console.print("  python3 create_plan.py create [location] [subject] [template]")
    console.print("  python3 create_plan.py --help")
    console.print()
    console.print("[yellow]EXAMPLES:[/yellow]")
    console.print("  [dim]# Create in current directory[/dim]")
    console.print("  python3 create_plan.py create")
    console.print()
    console.print("  [dim]# Create with location and subject[/dim]")
    console.print("  python3 create_plan.py create @flow \"New feature implementation\"")
    console.print()
    console.print("  [dim]# Create with custom template[/dim]")
    console.print("  python3 create_plan.py create @flow \"Research task\" master")
    console.print()

# =============================================
# ORCHESTRATION WORKFLOWS (No business logic)
# =============================================

def create_plan(
    location: str | None = None,
    subject: str = "",
    template_type: str = "default"
) -> Tuple[bool, int, str, str, str]:
    """
    Orchestrate plan creation workflow

    THIN ORCHESTRATOR - delegates all business logic to handlers.
    This function only coordinates the workflow and passes data between handlers.

    Workflow Steps:
        1. Load registry → registry handler
        2. Auto-cleanup → plan handler
        3. Resolve location → plan handler
        4. Calculate relative path → plan handler
        5. Get template → template handler
        6. Create file → plan handler
        7. Build registry entry → plan handler
        8. Update registry → registry handler
        9. Update dashboards → dashboard handlers
        10. Log and return results

    Args:
        location: Target directory for plan (@folder syntax supported)
        subject: Plan subject/title
        template_type: Template to use (default, master, etc.)

    Returns:
        (success, plan_number, location_description, template_type, error_message)
    """
    try:
        # STEP 1: Load registry
        registry = load_registry()

        # STEP 2: Auto-cleanup orphaned plans
        registry, auto_closed_count = auto_close_orphaned_plans(registry)
        if auto_closed_count > 0:
            save_registry(registry)
            console.print(f"[dim][AUTO-CLEANUP] Closed {auto_closed_count} orphaned plan(s)[/dim]")

        # STEP 3: Get next plan number
        NEXT_NUM = registry["next_number"]

        # STEP 4: Resolve location (@folder syntax support)
        success, target_dir, error_msg = resolve_plan_location(location, ECOSYSTEM_ROOT)
        if not success:
            return False, 0, "", "", error_msg

        # STEP 5: Calculate relative path for display
        RELATIVE_LOCATION = calculate_relative_location(target_dir, ECOSYSTEM_ROOT)

        # STEP 6: Build plan file path
        PLAN_FILE = target_dir / f"FPLAN-{NEXT_NUM:04d}.md"

        # STEP 7: Get template content
        try:
            CONTENT = get_template(
                template_type,
                number=NEXT_NUM,
                location=RELATIVE_LOCATION,
                subject=subject
            )
        except Exception as e:
            error_msg = f"Failed to load template '{template_type}': {e}"
            logger.error(f"[{MODULE_NAME}] {error_msg}")
            return False, 0, "", "", error_msg

        # STEP 8: Create plan file
        success, error_msg = create_plan_file(PLAN_FILE, CONTENT)
        if not success:
            return False, 0, "", "", error_msg

        # STEP 9: Build registry entry
        if "plans" not in registry:
            registry["plans"] = {}

        registry["plans"][f"{NEXT_NUM:04d}"] = build_plan_registry_entry(
            NEXT_NUM, target_dir, RELATIVE_LOCATION, subject, PLAN_FILE, template_type
        )
        registry["next_number"] = NEXT_NUM + 1

        # STEP 10: Save updated registry
        if not save_registry(registry):
            error_msg = "Failed to save registry after plan creation"
            logger.error(f"[{MODULE_NAME}] {error_msg}")
            console.print(f"[yellow][WARNING] {error_msg}[/yellow]")

        # STEP 11: Update dashboards (3-tier: modules log, handlers don't)
        dashboard_success = update_dashboard_local()
        central_success = push_to_plans_central()

        # Log dashboard update results
        if not dashboard_success:
            logger.warning(f"[{MODULE_NAME}] Failed to update DASHBOARD.local.json")
        if not central_success:
            logger.warning(f"[{MODULE_NAME}] Failed to update PLANS.central.json")


        # STEP 12: Log success
        logger.info(f"[{MODULE_NAME}] Created FPLAN-{NEXT_NUM:04d} in {RELATIVE_LOCATION}")

        # Display success messages
        display_msg = display_plan_created(NEXT_NUM, RELATIVE_LOCATION, subject, template_type)
        console.print(display_msg)

        # Fire trigger event for plan creation
        try:
            from trigger.apps.modules.core import trigger
            trigger.fire('plan_created', plan_number=NEXT_NUM, location=RELATIVE_LOCATION, subject=subject)
        except ImportError:
            pass  # Trigger not available, silent fallback

        return True, NEXT_NUM, RELATIVE_LOCATION, template_type, ""

    except Exception as e:
        error_msg = f"Error creating plan: {e}"
        logger.error(f"[{MODULE_NAME}] {error_msg}")
        return False, 0, "", "", error_msg


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle command routing for create_plan module

    THIN ORCHESTRATOR - delegates to handlers for all operations.

    Workflow:
        1. Parse arguments → command_parser handler
        2. Execute create_plan workflow
        3. Display results → display handler

    Args:
        command: Command name
        args: Additional arguments

    Returns:
        bool indicating success or failure of command handling
    """
    # Check if this is our command
    if command != "create":
        return False

    # Log the operation
    json_handler.log_operation(
        "plan_created",
        {"command": command, "args": args}
    )

    # STEP 1: Parse arguments (delegate to handler)
    location, subject, template_type = parse_create_plan_args(args)

    # STEP 2: Execute workflow
    success, num, loc, tmpl, error = create_plan(location, subject, template_type)

    # STEP 3: Display results (delegate to display handler)
    result_msg = display_plan_result(success, num, loc, tmpl, error)
    console.print(result_msg)

    # Return boolean result
    if success:
        return True
    else:
        return False


# =============================================
# STANDALONE EXECUTION (for testing)
# =============================================

if __name__ == "__main__":
    # Show introspection when run without arguments
    if len(sys.argv) == 1:
        print_introspection()
        sys.exit(0)

    # Handle help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    # Confirm logger connection
    logger.info("Prax logger connected to create_plan")

    # Log standalone execution
    json_handler.log_operation(
        "plan_created",
        {"command": "standalone"}
    )

    # Call handle_command with default
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    if args and args[0] not in ['create', 'create_plan']:
        # If first arg is not command, assume it's location (backward compatibility)
        args.insert(0, 'create')

    result = handle_command(args[0] if args else 'create', args[1:] if args else [])
    if result:
        sys.exit(0)
    else:
        sys.exit(1)
