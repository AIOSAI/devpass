#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: error_handler/logger.py
# Date: 2025-11-07
# Version: 1.0.0
# Category: cli/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-07): Initial implementation - Logging integration
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Error Handler Logging Integration

Integrates with prax system logger and provides JSON logging.
"""

import json
import inspect
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

from rich.console import Console

from .result_types import OperationResult

# Initialize Rich console
console = Console()

# Prax logger integration (graceful fallback if not available)
try:
    from prax.apps.modules.logger import system_logger as prax_logger
    PRAX_AVAILABLE = True
except ImportError:
    import logging
    prax_logger = logging.getLogger(__name__)
    PRAX_AVAILABLE = False


# JSON log directory (follows 3-file pattern)
ERROR_HANDLER_JSON_DIR = Path.home() / "aipass_core" / "cli" / "cli_json" / "error_handler_json"
ERROR_HANDLER_LOG_FILE = ERROR_HANDLER_JSON_DIR / "error_handler_log.json"

# Max log entries (prevent unbounded growth)
MAX_LOG_ENTRIES = 1000


def get_calling_module() -> str:
    """
    Detect calling module via stack inspection

    Returns:
        Module name (e.g., "create_branch", "update_branch")
    """
    # Walk up the stack to find the actual calling module
    frame = inspect.currentframe()
    try:
        # Skip error_handler frames to find actual caller
        for _ in range(10):  # Max depth to search
            if frame is None:
                break
            frame = frame.f_back
            if frame is None:
                break

            # Get module name from frame
            module_name = frame.f_globals.get('__name__', '')

            # Skip error_handler internals
            if 'error_handler' in module_name:
                continue

            # Found actual calling module
            if module_name and module_name != '__main__':
                # Extract just the module name (last part)
                return module_name.split('.')[-1]

        # Fallback
        return "unknown_module"

    finally:
        del frame  # Avoid reference cycles


def log_operation_start(operation: str, module: Optional[str] = None):
    """
    Log operation start

    Args:
        operation: Operation name
        module: Module name (auto-detected if not provided)
    """
    if module is None:
        module = get_calling_module()

    if PRAX_AVAILABLE:
        prax_logger.info(f"[{module}] {operation} started")
    else:
        console.print(f"[dim][[LOG]][/dim] [[blue]{module}[/blue]] {operation} started")


def log_operation_end(result: OperationResult, module: Optional[str] = None):
    """
    Log operation completion

    Args:
        result: OperationResult object
        module: Module name (auto-detected if not provided)
    """
    if module is None:
        module = get_calling_module()

    operation = result.operation
    status = result.status.value

    if result.success:
        if PRAX_AVAILABLE:
            prax_logger.info(f"[{module}] {operation} succeeded: {result.reason}")
        else:
            console.print(f"[dim][[LOG]][/dim] [[green]{module}[/green]] {operation} [green]succeeded[/green]")
    else:
        if result.status.value == "skipped":
            if PRAX_AVAILABLE:
                prax_logger.info(f"[{module}] {operation} skipped: {result.reason}")
            else:
                console.print(f"[dim][[LOG]][/dim] [[yellow]{module}[/yellow]] {operation} [yellow]skipped[/yellow]: {result.reason}")
        else:
            if PRAX_AVAILABLE:
                prax_logger.error(f"[{module}] {operation} failed: {result.reason}")
            else:
                console.print(f"[dim][[LOG]][/dim] [[red]{module}[/red]] {operation} [red]failed[/red]: {result.reason}")


def log_to_json(result: OperationResult) -> bool:
    """
    Log operation result to JSON file (3-file pattern)

    Args:
        result: OperationResult to log

    Returns:
        True if logged successfully, False otherwise
    """
    try:
        # Ensure directory exists
        ERROR_HANDLER_JSON_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing logs
        logs = []
        if ERROR_HANDLER_LOG_FILE.exists():
            try:
                with open(ERROR_HANDLER_LOG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logs = data.get('log', [])
            except Exception:
                # Corrupted log file - start fresh
                logs = []

        # Create log entry
        log_entry = result.to_dict()

        # Add to logs
        logs.append(log_entry)

        # Keep last MAX_LOG_ENTRIES
        if len(logs) > MAX_LOG_ENTRIES:
            logs = logs[-MAX_LOG_ENTRIES:]

        # Save with metadata
        log_data = {
            "module_name": "error_handler",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "log": logs,
            "summary": {
                "total_entries": len(logs),
                "last_entry": logs[-1]["timestamp"] if logs else None
            }
        }

        with open(ERROR_HANDLER_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        # Graceful degradation - don't fail operation because logging failed
        if PRAX_AVAILABLE:
            prax_logger.error(f"[error_handler] Failed to log to JSON: {e}")
        else:
            console.print(f"[red][[LOG ERROR]][/red] Failed to log to JSON: {e}")
        return False


def get_recent_errors(limit: int = 10) -> list[dict[str, Any]]:
    """
    Get recent error log entries

    Args:
        limit: Maximum number of entries to return

    Returns:
        List of error log entries (most recent first)
    """
    try:
        if not ERROR_HANDLER_LOG_FILE.exists():
            return []

        with open(ERROR_HANDLER_LOG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logs = data.get('log', [])

        # Filter to only errors
        errors = [
            log for log in logs
            if log.get('status') == 'failed'
        ]

        # Return most recent first
        return list(reversed(errors[-limit:]))

    except Exception:
        return []


def clear_logs() -> bool:
    """
    Clear all log entries

    Returns:
        True if cleared successfully
    """
    try:
        if ERROR_HANDLER_LOG_FILE.exists():
            ERROR_HANDLER_LOG_FILE.unlink()
        return True
    except Exception:
        return False
