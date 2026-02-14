#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: error_handler/decorators.py
# Date: 2025-11-07
# Version: 1.0.0
# Category: cli/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-07): Initial implementation - Core decorators
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Error Handler Decorators

Decorators for automatic error handling, logging, and result formatting.

Usage:
    from cli.apps.modules.error_handler import track_operation

    @track_operation
    def my_function(arg):
        # Just write business logic
        return result
"""

import functools
import inspect
from typing import Any, Callable

from rich.console import Console

from .result_types import (
    OperationResult,
    OperationStatus,
    CollectedResults
)
from .logger import (
    log_operation_start,
    log_operation_end,
    log_to_json
)
from .formatters import (
    format_result,
    format_batch_header,
    format_batch_footer
)

# Initialize Rich console
console = Console()


def track_operation(func: Callable) -> Callable:
    """
    Decorator for basic operation tracking

    Automatically:
    - Logs operation start/success/failure
    - Handles exceptions
    - Prints formatted console output
    - Returns OperationResult

    Usage:
        @track_operation
        def create_branch(path):
            do_work(path)
            return True

    Returns:
        OperationResult object
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> OperationResult:
        operation_name = func.__name__

        # Log operation start
        log_operation_start(operation_name)

        try:
            # Execute the function
            result = func(*args, **kwargs)

            # Check if function already returned OperationResult
            if isinstance(result, OperationResult):
                # Log and format the result
                log_operation_end(result)
                log_to_json(result)
                console.print(format_result(result))
                return result

            # Convert boolean/success to OperationResult
            if result is True or result is not None:
                op_result = OperationResult.success_result(operation_name)
                log_operation_end(op_result)
                log_to_json(op_result)
                console.print(format_result(op_result))
                return op_result
            else:
                # None or False = failure
                op_result = OperationResult.fail_result(
                    operation_name,
                    Exception(f"{operation_name} returned None/False")
                )
                log_operation_end(op_result)
                log_to_json(op_result)
                console.print(format_result(op_result))
                return op_result

        except Exception as e:
            # Auto-handle exceptions
            op_result = OperationResult.fail_result(operation_name, e)
            log_operation_end(op_result)
            log_to_json(op_result)
            console.print(format_result(op_result))
            return op_result

    return wrapper


def continue_on_error(func: Callable) -> Callable:
    """
    Decorator for migration-style execution

    Never raises exceptions - always returns OperationResult
    Use for operations that should skip failures and continue

    Usage:
        @continue_on_error
        def migrate_key(data, old, new):
            if new in data:
                return OperationResult.skip_result("migrate_key", "target exists")
            data[new] = data.pop(old)
            return OperationResult.success_result("migrate_key")

    Returns:
        OperationResult (never raises)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> OperationResult:
        operation_name = func.__name__

        try:
            result = func(*args, **kwargs)

            # If function returned OperationResult, use it
            if isinstance(result, OperationResult):
                # Log and format based on status
                log_operation_end(result)
                log_to_json(result)
                console.print(format_result(result))
                return result

            # Convert True/success to OperationResult
            if result is True or result is not None:
                op_result = OperationResult.success_result(operation_name)
                log_operation_end(op_result)
                log_to_json(op_result)
                console.print(format_result(op_result))
                return op_result
            else:
                op_result = OperationResult.fail_result(
                    operation_name,
                    Exception(f"{operation_name} returned None/False")
                )
                log_operation_end(op_result)
                log_to_json(op_result)
                console.print(format_result(op_result))
                return op_result

        except Exception as e:
            # Never raise - convert to OperationResult
            op_result = OperationResult.fail_result(operation_name, e)
            log_operation_end(op_result)
            log_to_json(op_result)
            console.print(format_result(op_result))
            return op_result

    return wrapper


def collect_results(func: Callable) -> Callable:
    """
    Decorator for aggregating multiple operation results

    Function must return list of OperationResults
    Automatically counts and prints summary

    Usage:
        @collect_results
        def update_all_branches():
            results = []
            for branch in branches:
                result = update_branch(branch)
                results.append(result)
            return results
        # Auto-prints: "✅ 5 succeeded, ⏭️ 2 skipped, ❌ 1 failed"

    Returns:
        CollectedResults object
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> CollectedResults:
        operation_name = func.__name__

        try:
            # Execute function - expect list of OperationResults
            results = func(*args, **kwargs)

            # Validate results are list of OperationResults
            if not isinstance(results, list):
                console.print(f"[red]❌ {operation_name} must return list of OperationResults[/red]")
                return CollectedResults(results=[])

            # Filter to only OperationResults
            op_results = [r for r in results if isinstance(r, OperationResult)]

            # Create collected results
            collected = CollectedResults(results=op_results)

            # Print batch header and footer with Rich
            console.print(format_batch_header(operation_name, len(op_results)))
            console.print(format_batch_footer(collected))

            # Log to JSON (each result already logged individually)
            log_operation_start(f"{operation_name}_batch")
            batch_result = OperationResult.success_result(
                f"{operation_name}_batch",
                f"Completed {collected.total} operations",
                succeeded=collected.succeeded,
                skipped=collected.skipped,
                failed=collected.failed
            )
            log_operation_end(batch_result)
            log_to_json(batch_result)

            return collected

        except Exception as e:
            console.print(f"[red]❌ {operation_name} failed: {e}[/red]")
            return CollectedResults(results=[])

    return wrapper


def _get_function_signature(func: Callable) -> dict[str, Any]:
    """
    Get function signature details for logging

    Args:
        func: Function to inspect

    Returns:
        Dict with function metadata
    """
    sig = inspect.signature(func)
    return {
        "name": func.__name__,
        "module": func.__module__,
        "parameters": list(sig.parameters.keys()),
        "return_annotation": str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else None
    }
