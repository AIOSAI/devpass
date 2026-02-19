#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: post_module.py - Post Orchestration Module
# Date: 2026-02-06
# Version: 2.0.0
# Category: the_commons/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Thin router refactor - moved implementation to handlers/posts/post_ops.py (FPLAN-0356)
#   - v1.0.0 (2026-02-06): Initial creation - post CRUD orchestration
#
# CODE STANDARDS:
#   - Orchestration only - NO business logic
#   - Imports from handlers/ for all data operations
#   - Module interface: handle_command(command, args) -> bool
# =============================================

"""
Post Orchestration Module

Thin router for post workflows. Delegates all implementation
to handlers/posts/post_ops.py.

Handles: post, thread, delete commands.
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

from handlers.posts.post_ops import create_post, view_thread, delete_post


# =============================================================================
# COMMAND ROUTING
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle post-related commands.

    Args:
        command: Command name (post, thread, delete)
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    if command not in ["post", "thread", "delete"]:
        return False

    if command == "post":
        return create_post(args)
    elif command == "thread":
        return view_thread(args)
    elif command == "delete":
        return delete_post(args)

    return False
