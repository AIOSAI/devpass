#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: error_handling_check.py - Error Handling Standards Checker Handler
# Date: 2025-11-16
# Version: 0.1.0
# Category: seed/standards/checkers
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-16): Initial implementation - error handling standards checking
#
# CODE STANDARDS:
#   - Handler implements checking logic, module orchestrates
# =============================================

"""
Error Handling Standards Checker Handler

Validates module compliance with AIPass error handling standards.
Checks for @track_operation decorator on entry points (route_command functions).

MANDATORY STANDARD (as of 2025-11-16):
- All branch entry points MUST use @track_operation decorator
- Import: from cli.apps.modules.error_handler import track_operation
- Usage: @track_operation on route_command() function
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from seed.apps.handlers.json import json_handler


def check_module(module_path: str) -> Dict:
    """
    Check if module follows error handling standards

    Args:
        module_path: Path to Python module to check

    Returns:
        dict: {
            'passed': bool,           # Overall pass/fail
            'checks': [               # Individual check results
                {
                    'name': str,      # Check name
                    'passed': bool,   # Pass/fail
                    'message': str,   # Details (line number, etc.)
                }
            ],
            'score': int,             # 0-100 percentage
            'standard': str           # Standard name
        }
    """
    # Log check start
    logger.info(f"Checking error handling standards for: {module_path}")
    json_handler.log_operation(
        "error_handling_check_started",
        {"module_path": module_path}
    )

    checks = []
    path = Path(module_path)

    # Validate file exists
    if not path.exists():
        return {
            'passed': False,
            'checks': [{'name': 'File exists', 'passed': False, 'message': f'File not found: {module_path}'}],
            'score': 0,
            'standard': 'ERROR_HANDLING'
        }

    # Read file
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return {
            'passed': False,
            'checks': [{'name': 'File readable', 'passed': False, 'message': f'Error reading file: {e}'}],
            'score': 0,
            'standard': 'ERROR_HANDLING'
        }

    # Filter out docstrings to prevent false positives
    filtered_lines = filter_docstrings(lines)

    # Determine file type - only check entry points (branch main files)
    is_entry_point = (
        path.name.endswith('.py') and
        'apps' in path.parts and
        path.parent.name == 'apps' and
        not path.name.startswith('_')
    )

    # Check 1: Import statement (required for all files that use error handling)
    import_check = check_track_operation_import(filtered_lines)
    if import_check:
        checks.append(import_check)

    # Check 2: Decorator usage on route_command (only for entry points)
    if is_entry_point:
        decorator_check = check_decorator_usage(filtered_lines)
        if decorator_check:
            checks.append(decorator_check)

    # If not an entry point and no import found, this is informational
    if not is_entry_point and len(checks) == 0:
        checks.append({
            'name': 'Error handling pattern (optional)',
            'passed': True,
            'message': 'Not an entry point - error handling is optional'
        })

    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = int((passed_checks / total_checks * 100)) if total_checks > 0 else 100

    # Overall pass if score >= 75%
    overall_passed = score >= 75

    # Log completion
    logger.info(f"Error handling check completed for {module_path}: {score}/100 ({'PASS' if overall_passed else 'FAIL'})")
    json_handler.log_operation(
        "error_handling_check_completed",
        {
            "module_path": module_path,
            "score": score,
            "passed": overall_passed,
            "total_checks": total_checks,
            "passed_checks": passed_checks
        }
    )

    return {
        'passed': overall_passed,
        'checks': checks,
        'score': score,
        'standard': 'ERROR_HANDLING'
    }


def filter_docstrings(lines: List[str]) -> List[str]:
    """
    Filter out docstrings from lines to prevent false positives.

    This prevents import examples in module docstrings from being
    detected as actual imports.

    Returns:
        List of lines with docstrings removed
    """
    filtered_lines = []
    in_docstring = False
    docstring_marker = None

    for line in lines:
        stripped = line.strip()

        # Check for docstring start/end
        if '"""' in stripped or "'''" in stripped:
            # Determine which marker we're looking for
            if '"""' in stripped:
                marker = '"""'
            else:
                marker = "'''"

            # Count occurrences of the marker
            marker_count = stripped.count(marker)

            if not in_docstring:
                # Starting a docstring
                if marker_count == 2:
                    # Single-line docstring - skip this line entirely
                    continue
                elif marker_count == 1:
                    # Multi-line docstring starting
                    in_docstring = True
                    docstring_marker = marker
                    continue
            else:
                # Potentially ending a docstring
                if marker == docstring_marker and marker_count >= 1:
                    # Multi-line docstring ending
                    in_docstring = False
                    docstring_marker = None
                    continue

        # Skip lines inside docstrings
        if in_docstring:
            continue

        # Keep non-docstring lines
        filtered_lines.append(line)

    return filtered_lines


def check_track_operation_import(lines: List[str]) -> Optional[Dict]:
    """
    Check for track_operation import from CLI error handler

    Required import:
        from cli.apps.modules.error_handler import track_operation
    """
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            continue

        # Look for the specific import
        if 'from cli.apps.modules.error_handler import' in line and 'track_operation' in line:
            return {
                'name': 'track_operation import',
                'passed': True,
                'message': f'Found on line {i}'
            }

    # Import not found
    return {
        'name': 'track_operation import',
        'passed': False,
        'message': 'Missing: from cli.apps.modules.error_handler import track_operation'
    }


def check_decorator_usage(lines: List[str]) -> Optional[Dict]:
    """
    Check for @track_operation decorator on route_command function

    This is the MANDATORY entry point pattern (as of 2025-11-16).
    All branch entry points must use this decorator on route_command().
    """
    # Find route_command function
    route_command_line = None
    decorator_line = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            continue

        # Look for route_command function definition
        if stripped.startswith('def route_command('):
            route_command_line = i

            # Check if previous non-empty, non-comment line is @track_operation
            for j in range(i-2, -1, -1):  # Go backwards from line before def
                prev_line = lines[j].strip()

                # Skip empty lines and comments
                if not prev_line or prev_line.startswith('#'):
                    continue

                # Check if this line is the decorator
                if prev_line == '@track_operation':
                    decorator_line = j + 1  # Convert to 1-indexed
                    break
                else:
                    # Found a non-empty, non-comment line that's not the decorator
                    break

            break  # Only check first route_command found

    # Evaluate results
    if route_command_line:
        if decorator_line:
            return {
                'name': '@track_operation decorator on route_command',
                'passed': True,
                'message': f'Found @track_operation on line {decorator_line}, route_command on line {route_command_line}'
            }
        else:
            return {
                'name': '@track_operation decorator on route_command',
                'passed': False,
                'message': f'route_command found on line {route_command_line}, but missing @track_operation decorator (MANDATORY as of 2025-11-16)'
            }

    # No route_command found - not necessarily an error (might not be entry point)
    return {
        'name': '@track_operation decorator (entry point)',
        'passed': True,
        'message': 'No route_command found (not an entry point - decorator not required)'
    }
