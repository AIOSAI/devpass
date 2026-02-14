#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: close_plan.py - PLAN closure module with registry cleanup
# Date: 2025-11-25
# Version: 2.4.0
# Category: flow/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.4.0 (2026-01-30): FIX close_all EOF error - handle non-interactive stdin in bulk close
#   - v2.3.0 (2025-11-25): RE-ADDED template deletion - empty templates now deleted instead of archived
#   - v2.2.0 (2025-11-22): Added proper error handling - surface mbank failures instead of hiding them
#   - v2.1.0 (2025-11-22): CRITICAL FIX - Removed template deletion logic, all plans now archived
#   - v2.0.0 (2025-11-21): Renamed from delete_plan, refactored --all flag, correct terminology
#
# CODE STANDARDS:
#   - Seed v3.0 compliant (imports, architecture, error handling)
# ==============================================

"""
Close PLAN Module

Thin orchestrator for plan closure workflow.
All business logic delegated to handlers.

Usage:
    From flow.py: flow close <number>
    From flow.py: flow close --all
    Standalone: python3 close_plan.py <number>
"""

import sys
from pathlib import Path
from typing import List
from datetime import datetime, timezone

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
FLOW_ROOT = AIPASS_ROOT / "flow"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))  # For seed package imports

# External: Prax logger
from prax.apps.modules.logger import system_logger as logger

# JSON handler for operation tracking
from flow.apps.handlers.json import json_handler

# CLI services for display and error handling
from cli.apps.modules import console

# Internal: Registry handlers
from flow.apps.handlers.registry.load_registry import load_registry
from flow.apps.handlers.registry.save_registry import save_registry

# Internal: Plan handlers
from flow.apps.handlers.plan.get_open_plans import get_open_plans
from flow.apps.handlers.plan.validator import normalize_plan_number, validate_plan_exists
from flow.apps.handlers.plan.confirmation import confirm_plan_deletion
from flow.apps.handlers.plan.display import (
    format_plan_deletion_header,
    format_plan_error,
    format_plan_deletion_success,
    format_registry_removal_status,
    format_deletion_cancelled,
    format_delete_usage_error
)

# Internal: Dashboard handlers
from flow.apps.handlers.dashboard.update_local import update_dashboard_local
from flow.apps.handlers.dashboard.push_central import push_to_plans_central


# Internal: Summary and memory bank handlers
from flow.apps.handlers.summary.generate import generate_summaries
from flow.apps.handlers.mbank.process import process_closed_plans, is_template_content

# =============================================
# CONFIGURATION
# =============================================

MODULE_NAME = "close_plan"

# =============================================
# INTROSPECTION
# =============================================

def print_introspection():
    """Display module info and connected handlers"""
    console.print()
    console.print("[bold cyan]close_plan Module[/bold cyan]")
    console.print()

    console.print("[yellow]Connected Handlers:[/yellow]")
    console.print()

    console.print("  [cyan]handlers/plan/[/cyan]")
    console.print("    [dim]- get_open_plans.py[/dim]")
    console.print("    [dim]- command_parser.py[/dim]")
    console.print("    [dim]- confirmation.py[/dim]")
    console.print("    [dim]- validator.py[/dim]")
    console.print("    [dim]- display.py[/dim]")
    console.print("    [dim]- file_ops.py[/dim]")
    console.print("    [dim]- update_registry.py[/dim]")
    console.print()

    console.print("  [cyan]handlers/registry/[/cyan]")
    console.print("    [dim]- load_registry.py[/dim]")
    console.print("    [dim]- save_registry.py[/dim]")
    console.print()

    console.print("  [cyan]handlers/dashboard/[/cyan]")
    console.print("    [dim]- update_local.py[/dim]")
    console.print("    [dim]- push_central.py[/dim]")
    console.print()

    console.print("[dim]Run 'python3 close_plan.py --help' for usage[/dim]")
    console.print()

# =============================================
# CLOSE PLAN WORKFLOW
# =============================================

def close_plan(plan_num: str | None = None, confirm: bool = True, all_plans: bool = False) -> bool:
    """
    Orchestrate plan closure workflow (thin orchestrator)

    Delegates all business logic to handlers:
    - Validation: validator handler
    - Registry ops: registry handlers
    - File ops: file_ops handler
    - Confirmation: confirmation handler
    - Display: display handler

    Args:
        plan_num: Plan number (e.g., "0001" or "1" or "42") - required if all_plans=False
        confirm: Whether to ask for confirmation (default True)
        all_plans: If True, close all open plans (default False)

    Returns:
        True if successful, False otherwise
    """
    # Handle --all flag
    if all_plans:
        return close_all_plans(confirm)

    # Single plan closure
    if not plan_num:
        logger.warning(f"[{MODULE_NAME}] Plan number required for single plan closure")
        console.print(format_plan_error("invalid_number", ""))
        return False

    try:
        # 1. VALIDATE: Normalize plan number (handler)
        plan_key = normalize_plan_number(plan_num)

        # 2. LOAD DATA: Get registry (service)
        registry = load_registry()

        # 3. VALIDATE: Check plan exists (handler)
        exists, error_msg = validate_plan_exists(plan_key, registry)
        if not exists:
            logger.warning(f"[{MODULE_NAME}] {error_msg}")
            console.print(format_plan_error("not_found", plan_key))
            return False

        plan_info = registry["plans"][plan_key]
        plan_file = Path(plan_info.get("file_path", ""))

        # 4. IDEMPOTENCY CHECK: Prevent double-closing
        if plan_info['status'] == 'closed':
            closed_date = plan_info.get('closed', 'unknown')
            console.print(f"[yellow]FPLAN-{plan_key} already closed on {closed_date}[/yellow]")
            console.print("[dim]Nothing to do - plan is already archived[/dim]")
            return False

        # 5. TEMPLATE CHECK: Auto-delete empty templates (don't archive)
        try:
            with open(plan_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if is_template_content(content):
                console.print(f"\n[yellow]FPLAN-{plan_key} is empty template - deleting (not archiving)[/yellow]")

                # Delete the file
                plan_file.unlink()
                logger.info(f"[{MODULE_NAME}] Deleted empty template file: {plan_file}")

                # Remove from registry
                del registry["plans"][plan_key]
                save_registry(registry)
                logger.info(f"[{MODULE_NAME}] Removed FPLAN-{plan_key} from registry")

                console.print(f"[green]Empty template deleted - FPLAN-{plan_key} removed from system[/green]\n")
                return True

        except Exception as e:
            logger.warning(f"[{MODULE_NAME}] Failed to check if FPLAN-{plan_key} is template: {e}")
            console.print(f"[yellow]Warning: Could not check template status, continuing with normal processing[/yellow]")

        # 6. DISPLAY: Show plan info (handler)
        console.print(format_plan_deletion_header(plan_key, plan_info))

        # 7. CONFIRM: Ask user if needed (handler)
        if confirm:
            if not confirm_plan_deletion(plan_key):
                console.print(format_deletion_cancelled())
                logger.info(f"[{MODULE_NAME}] Closure cancelled by user for PLAN{plan_key}")
                return False

        # 8. MARK AS CLOSED: Update registry status
        plan_info['status'] = 'closed'
        plan_info['closed'] = datetime.now(timezone.utc).isoformat()
        save_registry(registry)
        logger.info(f"[{MODULE_NAME}] Marked FPLAN-{plan_key} as closed")

        # 9. GENERATE SUMMARIES: AI summarization before archival (handler)
        try:
            summary_result = generate_summaries()
            if summary_result.get('success'):
                logger.info(f"[{MODULE_NAME}] Generated summaries for closed plans")
            else:
                error_msg = summary_result.get('error', 'Unknown error')
                logger.error(f"[{MODULE_NAME}] Summary generation failed: {error_msg}")
                console.print(f"\n[red]ERROR: Summary generation failed - plan NOT closed[/red]")
                console.print(f"[red]Details: {error_msg}[/red]")
                console.print(f"[yellow]Plan status remains: {plan_info.get('status', 'unknown')}[/yellow]\n")
                return False
        except Exception as e:
            error_msg = f"Failed to generate summaries: {e}"
            logger.error(f"[{MODULE_NAME}] {error_msg}")
            console.print(f"\n[red]ERROR: Summary generation failed - plan NOT closed[/red]")
            console.print(f"[red]Details: {error_msg}[/red]")
            console.print(f"[yellow]Plan status remains: {plan_info.get('status', 'unknown')}[/yellow]\n")
            return False

        # 10. PROCESS TO MEMORY BANK: Archive closed plan (handler)
        try:
            mbank_result = process_closed_plans()

            # Check for actual processing success
            processed_count = mbank_result.get('processed', 0)
            error_count = mbank_result.get('errors', 0)
            results = mbank_result.get('results', [])

            if not mbank_result.get('success'):
                # Handler-level failure
                error_msg = mbank_result.get('error', 'Unknown error')
                logger.error(f"[{MODULE_NAME}] Memory bank processing failed: {error_msg}")
                console.print(f"\n[red]ERROR: Memory bank processing failed[/red]")
                console.print(f"[red]Details: {error_msg}[/red]")
                console.print(f"[yellow]Plan marked as closed but NOT archived[/yellow]\n")
                return False

            if processed_count == 0 and error_count > 0:
                # Processing ran but all plans failed
                # Extract error details from results
                error_details = []
                for result in results:
                    if result.get('status') == 'error':
                        plan_name = result.get('plan', 'unknown')
                        error_msg = result.get('error', 'unknown error')
                        error_details.append(f"{plan_name}: {error_msg}")

                full_error = "; ".join(error_details) if error_details else "Unknown errors occurred"
                logger.error(f"[{MODULE_NAME}] Memory bank processing failed for all plans: {full_error}")
                console.print(f"\n[red]ERROR: Failed to archive plan to memory bank[/red]")
                console.print(f"[red]Details: {full_error}[/red]")
                console.print(f"[yellow]Plan marked as closed but NOT moved to processed_plans[/yellow]")
                console.print(f"[yellow]File remains at: {plan_file}[/yellow]\n")
                return False

            logger.info(f"[{MODULE_NAME}] Processed {processed_count} plans to memory bank")

        except Exception as e:
            error_msg = f"Failed to process memory bank: {e}"
            logger.error(f"[{MODULE_NAME}] {error_msg}")
            console.print(f"\n[red]ERROR: {error_msg}[/red]")
            console.print(f"[yellow]Plan marked as closed but NOT archived[/yellow]\n")
            return False

        # 11. UPDATE DASHBOARDS: Sync dashboard files (handlers)
        dashboard_success = update_dashboard_local()
        central_success = push_to_plans_central()

        # Log dashboard update results (3-tier: modules log, handlers don't)
        if not dashboard_success:
            logger.warning(f"[{MODULE_NAME}] Failed to update DASHBOARD.local.json")
        if not central_success:
            logger.warning(f"[{MODULE_NAME}] Failed to update PLANS.central.json")


        # 12. DISPLAY: Success message (handler)
        console.print(format_plan_deletion_success(plan_key))

        # Fire trigger event for plan closure (optional - trigger module may not be available)
        try:
            from trigger.apps.modules.core import trigger
            trigger.fire('plan_closed', plan_number=plan_key, location=str(plan_file.parent))
        except ImportError:
            logger.info(f"[{MODULE_NAME}] Trigger module not available, skipping event fire")

        return True

    except ValueError:
        error_msg = f"Invalid plan number: {plan_num}"
        logger.warning(f"[{MODULE_NAME}] {error_msg}")
        console.print(format_plan_error("invalid_number", plan_num))
        return False

    except Exception as e:
        error_msg = f"Error closing plan: {e}"
        logger.error(f"[{MODULE_NAME}] {error_msg}")
        console.print(format_plan_error("general", details=str(e)))
        return False


def close_all_plans(confirm: bool = True) -> bool:
    """
    Close all open plans in one operation

    Args:
        confirm: Whether to ask for bulk confirmation (default True)

    Returns:
        True if at least one plan closed successfully, False otherwise
    """
    try:
        # Get all open plans (handler)
        open_plans = get_open_plans()

        if not open_plans:
            console.print("\n[yellow]No open plans to close[/yellow]\n")
            logger.info(f"[{MODULE_NAME}] close_all: No open plans found")
            return False

        # Show what will be closed
        console.print(f"\n[bold yellow]Found {len(open_plans)} open plan(s) to close:[/bold yellow]")
        for plan_num, plan_info in open_plans:
            subject = plan_info.get("subject", "No subject")
            console.print(f"  • FPLAN-{plan_num}: {subject}")

        # Confirm bulk close
        if confirm:
            console.print(f"\n[bold red]WARNING: This will close all {len(open_plans)} plans![/bold red]")

            # Auto-confirm in non-interactive environments (autonomous workflows)
            if not sys.stdin.isatty():
                console.print("[dim]Non-interactive mode: auto-confirming[/dim]")
                response = "yes"
            else:
                try:
                    response = input("Type 'yes' to confirm: ").strip().lower()
                except EOFError:
                    # Handle EOF when stdin is not available
                    console.print("[dim]EOF detected: auto-confirming[/dim]")
                    response = "yes"

            if response != "yes":
                console.print("\n[yellow]Close all cancelled[/yellow]\n")
                logger.info(f"[{MODULE_NAME}] close_all cancelled by user")
                return False

        console.print(f"\n[bold]Closing all {len(open_plans)} plan(s)...[/bold]")
        console.print("─" * 60)

        # Close each plan
        success_count = 0
        failure_count = 0

        for plan_num, plan_info in open_plans:
            console.print(f"\n[dim]Closing FPLAN-{plan_num}...[/dim]")

            # Call close_plan with confirm=False (skip individual confirmation)
            success = close_plan(plan_num=plan_num, confirm=False, all_plans=False)

            if success:
                success_count += 1
            else:
                failure_count += 1

        # Summary
        console.print("\n" + "═" * 60)
        console.print("[bold green]CLOSE ALL COMPLETE[/bold green]")
        console.print(f"  • Successfully closed: {success_count}")
        console.print(f"  • Failed to close: {failure_count}")
        console.print(f"  • Total processed: {len(open_plans)}")
        console.print("═" * 60 + "\n")

        logger.info(f"[{MODULE_NAME}] close_all completed: {success_count} success, {failure_count} failures")
        return success_count > 0

    except Exception as e:
        error_msg = f"Error in close_all: {e}"
        logger.error(f"[{MODULE_NAME}] {error_msg}")
        console.print(f"\n[bold red]ERROR:[/bold red] {error_msg}\n")
        return False


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle command routing for close_plan module (thin orchestrator)

    Delegates to handlers:
    - Argument parsing: command_parser handler
    - Workflow execution: close_plan orchestrator
    - Error display: display handler

    Args:
        command: Command name
        args: Additional arguments

    Returns:
        bool indicating success or failure
    """
    # Check if this is our command
    if command != "close":
        return False

    # Import parser here (after command check)
    from flow.apps.handlers.plan.command_parser import parse_close_command_args

    # Log the operation
    json_handler.log_operation(
        "plan_closed",
        {"command": command, "args": args}
    )

    # 1. PARSE ARGS: Use command_parser handler
    plan_num, confirm, all_plans, error = parse_close_command_args(args)

    # 2. VALIDATE: Check for parsing errors
    if error:
        console.print(format_delete_usage_error())
        return False

    # 3. EXECUTE: Run workflow orchestrator
    success = close_plan(plan_num=plan_num, confirm=confirm, all_plans=all_plans)

    # 4. RETURN: Result (close_plan already handles all output)
    return success


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
        import argparse
        PARSER = argparse.ArgumentParser(
            description='Close PLAN file',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
COMMANDS:
  close, close_plan      Close a single plan
  close --all            Close all open plans

USAGE:
  python3 close_plan.py close <plan_number> [--yes]
  python3 close_plan.py close --all
  python3 close_plan.py --help

OPTIONS:
  --yes, -y    Skip confirmation prompt (for single close)
  --all        Close all open plans

EXAMPLES:
  # Close with confirmation
  python3 close_plan.py close 42

  # Close without confirmation
  python3 close_plan.py close 42 --yes

  # Close all open plans (requires confirmation)
  python3 close_plan.py close --all
            """
        )
        PARSER.print_help()
        sys.exit(0)

    # Confirm logger connection
    logger.info("Prax logger connected to close_plan")

    # Log standalone execution
    json_handler.log_operation(
        "plan_closed",
        {"command": "standalone"}
    )

    # Call handle_command with default
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    if not args:
        console.print(format_delete_usage_error())
        console.print("Run with --help for usage information")
        console.print()
        sys.exit(1)

    # If first arg is not command, assume it's plan number (backward compatibility)
    if args[0] not in ['close', 'close_plan']:
        args.insert(0, 'close')

    result = handle_command(args[0], args[1:])
    # Result is True on success, False on failure
    if result:
        sys.exit(0)
    else:
        sys.exit(1)
