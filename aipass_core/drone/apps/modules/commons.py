#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: commons.py - The Commons Shortcut Module
# Date: 2026-02-06
# Version: 1.0.0
# Category: drone/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-06): Initial creation - routes 'drone commons' to The Commons
#
# CODE STANDARDS:
#   - Thin orchestrator pattern - delegates to handlers
# =============================================

"""
The Commons Shortcut Module

Routes 'drone commons <command>' to The Commons entry point,
so branches can use either 'drone @commons ...' or 'drone commons ...'.
"""

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from drone.apps.handlers.discovery import run_branch_module
from drone.apps.handlers.routing import preprocess_args

COMMONS_PATH = Path("/home/aipass/The_Commons")


def handle_command(command: str, args: list) -> bool:
    """Route 'commons' command to The Commons branch."""
    if command != "commons":
        return False

    resolved_args = preprocess_args(args)
    run_branch_module(COMMONS_PATH, resolved_args)
    return True
