# ===================AIPASS====================
# META DATA HEADER
# Name: __init__.py - Branch Registry Handlers Package
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/handlers/branch_registry
# =============================================

"""
Branch Registry Handlers - Implementation for branch metadata lookups.

Public API:
    from drone.apps.handlers.branch_registry import get_all_branches
"""

from .lookup import (
    get_all_branches,
    get_branch_by_email,
    get_branch_by_name,
    get_branch_by_path,
    list_branch_names,
    list_branch_emails,
    list_systems,
    get_registry_metadata,
)

__all__ = [
    "get_all_branches",
    "get_branch_by_email",
    "get_branch_by_name",
    "get_branch_by_path",
    "list_branch_names",
    "list_branch_emails",
    "list_systems",
    "get_registry_metadata",
]
