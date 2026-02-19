#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: commons_identity.py - Branch Identity Detection
# Date: 2026-02-06
# Version: 2.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Thin wrapper refactor - moved implementation to handlers/identity/identity_ops.py (FPLAN-0356)
#   - v1.0.0 (2026-02-06): Initial creation - PWD-based branch detection
#
# CODE STANDARDS:
#   - Utility module for branch identity resolution
#   - Thin wrapper re-exporting from handlers/identity/identity_ops.py
#   - Maintains backward compatibility for all importers
# =============================================

"""
Branch Identity Detection for The Commons

Thin wrapper that re-exports identity functions from
handlers/identity/identity_ops.py for backward compatibility.

All modules import from here: `from modules.commons_identity import get_caller_branch`
"""

import sys
from pathlib import Path

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

# Re-export all public functions for backward compatibility
from handlers.identity.identity_ops import (
    find_branch_root,
    get_branch_info_from_registry,
    get_caller_branch,
    extract_mentions,
)

__all__ = [
    "find_branch_root",
    "get_branch_info_from_registry",
    "get_caller_branch",
    "extract_mentions",
]
