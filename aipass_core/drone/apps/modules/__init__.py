# ===================AIPASS====================
# META DATA HEADER
# Name: __init__.py - Drone Modules Package
# Date: 2025-11-29
# Version: 2.0.0
# Category: drone/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2025-11-29): Added service layer exports (paths, branch_registry)
#   - v1.0.0 (2025-11-11): Initial package
# =============================================

"""
Drone Services - Import this for @ resolution and branch lookups

Usage:
    from drone.apps.modules import resolve

    # High-level API (recommended)
    branch = resolve("@flow")    # → dict with name, path, email, exists, module_path
    branches = resolve("@all")   # → list of all branch dicts

    # Low-level functions (if needed)
    path = resolve_target("@flow")  # → Path object only
"""

# =============================================================================
# PATH SERVICES
# =============================================================================

from .paths import (
    resolve,
    resolve_target,
    get_branch_path,
    normalize_branch_arg,
    get_module_path,
    branch_exists,
    AIPASS_HOME,
    AIPASS_ROOT,
)

# =============================================================================
# BRANCH REGISTRY SERVICES
# =============================================================================

from .branch_registry import (
    get_all_branches,
    get_branch_by_email,
    get_branch_by_name,
    get_branch_by_path,
    list_branch_names,
    list_branch_emails,
    list_systems,
    get_registry_metadata,
)

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # High-level API (recommended)
    "resolve",
    # Path services
    "resolve_target",
    "get_branch_path",
    "normalize_branch_arg",
    "get_module_path",
    "branch_exists",
    "AIPASS_HOME",
    "AIPASS_ROOT",
    # Branch registry services
    "get_all_branches",
    "get_branch_by_email",
    "get_branch_by_name",
    "get_branch_by_path",
    "list_branch_names",
    "list_branch_emails",
    "list_systems",
    "get_registry_metadata",
]
