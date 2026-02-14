# ===================AIPASS====================
# META DATA HEADER
# Name: __init__.py - Path Handlers Package
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/handlers/paths
# =============================================

"""
Path Handlers - Implementation for @ resolution and path utilities.

Public API:
    from drone.apps.handlers.paths import resolve_target, get_branch_path
"""

from .resolver import (
    resolve,
    resolve_target,
    get_branch_path,
    normalize_branch_arg,
    get_module_path,
    branch_exists,
    AIPASS_HOME,
    AIPASS_ROOT,
)

__all__ = [
    "resolve",
    "resolve_target",
    "get_branch_path",
    "normalize_branch_arg",
    "get_module_path",
    "branch_exists",
    "AIPASS_HOME",
    "AIPASS_ROOT",
]
