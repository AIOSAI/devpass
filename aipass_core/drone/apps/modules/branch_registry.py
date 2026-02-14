#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: branch_registry.py - Drone Branch Registry Services (Module API)
# Date: 2025-11-29
# Version: 2.0.0
# Category: drone/modules/services
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2025-11-29): Refactored to thin API layer (imports from handlers)
#   - v1.0.0 (2025-11-29): Initial service layer - pure functions, no CLI
#
# CODE STANDARDS:
#   - Module pattern: thin API layer that imports from handlers
#   - Follows Seed's prax/logger.py pattern
#   - Modules orchestrate, handlers implement
# =============================================

"""
Drone Branch Registry Services - Importable by all branches

Thin API layer that re-exports branch registry functions from handlers.
Pure functions for branch metadata lookups from BRANCH_REGISTRY.json.

Usage:
    from drone.apps.modules.branch_registry import get_all_branches, get_branch_by_email

    branches = get_all_branches()
    flow = get_branch_by_email("@flow")
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path

AIPASS_HOME = Path.home()
AIPASS_ROOT = AIPASS_HOME / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

# =============================================================================
# PUBLIC API - Re-exported from handlers
# =============================================================================

from drone.apps.handlers.branch_registry import (
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
    "logger",
]
