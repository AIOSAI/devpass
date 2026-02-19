#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: artifact_module.py - Artifact Orchestration Module
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 3)
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Artifact Orchestration Module

Thin router for artifact workflows. Delegates all implementation
to handlers/artifacts/artifact_ops.py.

Handles: craft, artifacts, inspect commands.
"""

import sys
from pathlib import Path
from typing import List

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.artifacts.artifact_ops import craft_artifact, list_artifacts, inspect_artifact, collab_artifact, sign_artifact


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle artifact-related commands.

    Args:
        command: Command name (craft, artifacts, inspect)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in ["craft", "artifacts", "inspect", "collab", "sign"]:
        return False

    if command == "craft":
        return craft_artifact(args)
    elif command == "artifacts":
        return list_artifacts(args)
    elif command == "inspect":
        return inspect_artifact(args)
    elif command == "collab":
        return collab_artifact(args)
    elif command == "sign":
        return sign_artifact(args)

    return False
