#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: error_handler/result_types.py
# Date: 2025-11-07
# Version: 1.0.0
# Category: cli/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-07): Initial implementation - Result types
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Error Handler Result Types

Data classes for operation results and error categorization.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class OperationStatus(Enum):
    """Status of an operation"""
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


class ErrorCategory(Enum):
    """Categories for error classification"""
    FILESYSTEM = "filesystem"        # File/directory operations
    NETWORK = "network"              # API calls, HTTP requests
    VALIDATION = "validation"        # Data validation failures
    DEPENDENCY = "dependency"        # Missing imports, unavailable modules
    STATE = "state"                  # Invalid state, precondition failures
    CONFIGURATION = "configuration"  # Config file issues
    USER_INPUT = "user_input"        # Invalid parameters from user
    UNKNOWN = "unknown"              # Unrecognized error type


@dataclass
class OperationResult:
    """
    Structured result from an operation

    Attributes:
        success: True if operation succeeded
        status: SUCCESS | SKIPPED | FAILED
        operation: Operation name (function name)
        reason: Why it succeeded/skipped/failed
        details: Additional context (dict)
        error: Exception object if failed (optional)
        error_category: Category of error (optional)
        timestamp: When operation completed

    Examples:
        # Success
        OperationResult(
            success=True,
            status=OperationStatus.SUCCESS,
            operation="create_branch",
            reason="Branch created successfully"
        )

        # Skipped
        OperationResult(
            success=False,
            status=OperationStatus.SKIPPED,
            operation="migrate_key",
            reason="Target key already exists"
        )

        # Failed
        OperationResult(
            success=False,
            status=OperationStatus.FAILED,
            operation="save_registry",
            reason="Permission denied",
            error=PermissionError(...)
        )
    """
    success: bool
    status: OperationStatus
    operation: str
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None
    error_category: ErrorCategory = ErrorCategory.UNKNOWN
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __bool__(self) -> bool:
        """Make OperationResult work with if/else checks

        Returns:
            True if operation succeeded, False otherwise

        Examples:
            result = my_function()
            if result:  # Works! Checks result.success
                print("Success")
        """
        return self.success

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "status": self.status.value,
            "operation": self.operation,
            "reason": self.reason,
            "details": self.details,
            "error": str(self.error) if self.error else None,
            "error_category": self.error_category.value,
            "timestamp": self.timestamp
        }

    @classmethod
    def success_result(cls, operation: str, reason: str = "", **details) -> 'OperationResult':
        """Create a success result"""
        return cls(
            success=True,
            status=OperationStatus.SUCCESS,
            operation=operation,
            reason=reason or f"{operation} completed successfully",
            details=details
        )

    @classmethod
    def skip_result(cls, operation: str, reason: str, **details) -> 'OperationResult':
        """Create a skip result"""
        return cls(
            success=False,
            status=OperationStatus.SKIPPED,
            operation=operation,
            reason=reason,
            details=details
        )

    @classmethod
    def fail_result(cls, operation: str, error: Exception, **details) -> 'OperationResult':
        """Create a failure result with auto-categorized error"""
        category = categorize_error(error)
        return cls(
            success=False,
            status=OperationStatus.FAILED,
            operation=operation,
            reason=str(error),
            details=details,
            error=error,
            error_category=category
        )


def categorize_error(error: Exception) -> ErrorCategory:
    """
    Categorize exception into ErrorCategory

    Args:
        error: Exception to categorize

    Returns:
        ErrorCategory enum value
    """
    error_type = type(error).__name__

    # Filesystem errors
    if error_type in ('FileNotFoundError', 'PermissionError', 'IsADirectoryError',
                      'NotADirectoryError', 'FileExistsError', 'OSError', 'IOError'):
        return ErrorCategory.FILESYSTEM

    # Network errors
    if error_type in ('ConnectionError', 'TimeoutError', 'URLError', 'HTTPError'):
        return ErrorCategory.NETWORK

    # Validation errors
    if error_type in ('ValidationError', 'ValueError', 'TypeError', 'AssertionError'):
        return ErrorCategory.VALIDATION

    # Dependency errors
    if error_type in ('ImportError', 'ModuleNotFoundError'):
        return ErrorCategory.DEPENDENCY

    # State errors
    if error_type in ('RuntimeError', 'AttributeError', 'KeyError', 'IndexError'):
        return ErrorCategory.STATE

    # Configuration errors
    if error_type in ('ConfigError', 'KeyError') and 'config' in str(error).lower():
        return ErrorCategory.CONFIGURATION

    # Default
    return ErrorCategory.UNKNOWN


@dataclass
class CollectedResults:
    """
    Aggregated results from multiple operations

    Attributes:
        results: List of individual OperationResults
        total: Total number of operations
        succeeded: Count of successful operations
        skipped: Count of skipped operations
        failed: Count of failed operations
    """
    results: list[OperationResult]

    @property
    def total(self) -> int:
        """Total number of operations"""
        return len(self.results)

    @property
    def succeeded(self) -> int:
        """Count of successful operations"""
        return sum(1 for r in self.results if r.status == OperationStatus.SUCCESS)

    @property
    def skipped(self) -> int:
        """Count of skipped operations"""
        return sum(1 for r in self.results if r.status == OperationStatus.SKIPPED)

    @property
    def failed(self) -> int:
        """Count of failed operations"""
        return sum(1 for r in self.results if r.status == OperationStatus.FAILED)

    @property
    def all_succeeded(self) -> bool:
        """True if all operations succeeded"""
        return self.failed == 0 and self.skipped == 0

    @property
    def any_failed(self) -> bool:
        """True if any operations failed"""
        return self.failed > 0

    def get_failures(self) -> list[OperationResult]:
        """Get list of failed operations"""
        return [r for r in self.results if r.status == OperationStatus.FAILED]

    def get_skipped(self) -> list[OperationResult]:
        """Get list of skipped operations"""
        return [r for r in self.results if r.status == OperationStatus.SKIPPED]

    def summary(self) -> str:
        """Get summary string"""
        parts = []
        if self.succeeded > 0:
            parts.append(f"✅ {self.succeeded} succeeded")
        if self.skipped > 0:
            parts.append(f"⏭️  {self.skipped} skipped")
        if self.failed > 0:
            parts.append(f"❌ {self.failed} failed")

        return ", ".join(parts) if parts else "No operations"
