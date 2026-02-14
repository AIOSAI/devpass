#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: error_handler/__init__.py
# Date: 2025-11-07
# Version: 1.0.0
# Category: cli/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-07): Initial implementation - Public API
# =============================================

"""
Error Handler Module - Public API

Provides decorators and result types for automatic error handling.

Usage:
    from cli.apps.modules.error_handler import track_operation

    @track_operation
    def my_function():
        return True
"""

from .result_types import (
    OperationResult,
    OperationStatus,
    ErrorCategory
)

from .decorators import (
    track_operation,
    continue_on_error,
    collect_results
)

__all__ = [
    # Result types
    'OperationResult',
    'OperationStatus',
    'ErrorCategory',

    # Decorators
    'track_operation',
    'continue_on_error',
    'collect_results',
]

__version__ = '1.0.0'
