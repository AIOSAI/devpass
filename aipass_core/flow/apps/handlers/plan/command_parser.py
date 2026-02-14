#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: command_parser.py - Command Argument Parser
# Date: 2025-11-15
# Version: 0.1.0
# Category: flow/handlers/plan
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-15): Initial handler - command argument parsing
#
# CODE STANDARDS:
#   - Pure argument parsing logic
#   - Returns tuples with parsed values
# =============================================

"""
Command Argument Parser

Parses command-line arguments for plan operations.
"""

from typing import List, Tuple


def parse_create_plan_args(args: List[str]) -> Tuple[str | None, str, str]:
    """
    Parse arguments for plan creation

    Args:
        args: List of command arguments

    Returns:
        Tuple of (location, subject, template_type)
        - location: First arg or None
        - subject: Second arg or empty string
        - template_type: Third arg or "default"

    Examples:
        >>> parse_create_plan_args(["@flow", "My task", "master"])
        ("@flow", "My task", "master")

        >>> parse_create_plan_args([])
        (None, "", "default")

        >>> parse_create_plan_args(["@flow"])
        ("@flow", "", "default")
    """
    location = args[0] if len(args) > 0 else None
    subject = args[1] if len(args) > 1 else ""
    template_type = args[2] if len(args) > 2 else "default"

    return location, subject, template_type


def parse_delete_command_args(args: List[str]) -> Tuple[str | None, bool, str | None]:
    """
    Parse arguments for delete command (DEPRECATED - use parse_close_command_args)

    Args:
        args: Command arguments

    Returns:
        Tuple of (plan_num, confirm, error_message)
        - plan_num: Plan number from first arg, or None if missing
        - confirm: False if --yes or -y flag present, True otherwise
        - error_message: None if valid, error string if plan_num missing

    Examples:
        >>> parse_delete_command_args(["42"])
        ("42", True, None)

        >>> parse_delete_command_args(["42", "--yes"])
        ("42", False, None)

        >>> parse_delete_command_args([])
        (None, True, "Plan number required")
    """
    if len(args) < 1:
        return None, True, "Plan number required"

    plan_num = args[0]
    confirm = '--yes' not in args and '-y' not in args

    return plan_num, confirm, None


def parse_close_command_args(args: List[str]) -> Tuple[str | None, bool, bool, str | None]:
    """
    Parse arguments for close command

    Args:
        args: Command arguments

    Returns:
        Tuple of (plan_num, confirm, all_plans, error_message)
        - plan_num: Plan number from first arg, or None if --all or missing
        - confirm: False if --yes or -y flag present, True otherwise
        - all_plans: True if --all flag present, False otherwise
        - error_message: None if valid, error string if invalid args

    Examples:
        >>> parse_close_command_args(["42"])
        ("42", True, False, None)

        >>> parse_close_command_args(["42", "--yes"])
        ("42", False, False, None)

        >>> parse_close_command_args(["--all"])
        (None, True, True, None)

        >>> parse_close_command_args(["--all", "--yes"])
        (None, False, True, None)

        >>> parse_close_command_args([])
        (None, True, False, "Plan number or --all required")
    """
    # Check for --all flag
    all_plans = '--all' in args

    # Check for --yes/-y flag
    confirm = '--yes' not in args and '-y' not in args

    # If --all, plan_num is None
    if all_plans:
        return None, confirm, True, None

    # Otherwise, need plan number
    if len(args) < 1 or args[0].startswith('--'):
        return None, True, False, "Plan number or --all required"

    plan_num = args[0]
    return plan_num, confirm, False, None


def parse_restore_command_args(args: List[str]) -> Tuple[str | None, str | None]:
    """
    Parse arguments for restore command

    Args:
        args: Command arguments

    Returns:
        Tuple of (plan_num, error_message)
        - plan_num: Plan number from first arg, or None if missing
        - error_message: None if valid, error string if plan_num missing

    Examples:
        >>> parse_restore_command_args(["42"])
        ("42", None)

        >>> parse_restore_command_args(["0034"])
        ("0034", None)

        >>> parse_restore_command_args([])
        (None, "Plan number required")
    """
    if len(args) < 1:
        return None, "Plan number required"

    plan_num = args[0]
    return plan_num, None
