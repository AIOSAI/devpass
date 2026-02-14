#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: paths.py - Drone Path Services (Module API)
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
Drone Path Services - Importable by all branches

Thin API layer that re-exports path resolution functions from handlers.
Pure functions for @ target resolution and path utilities.

Usage:
    from drone.apps.modules.paths import resolve_target, get_branch_path

    path = resolve_target("@flow")  # -> Path("/home/aipass/aipass_core/flow")
    path = resolve_target("@seed")  # -> Path("/home/aipass/seed")
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

from drone.apps.handlers.paths import (
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
    "logger",
]
