#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: telegram_chat.py - Telegram Direct Chat Module (Public API)
# Date: 2026-02-15
# Version: 1.0.0
# Category: api/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-15): Initial - public API for direct_chat and telegram_standards
#
# CODE STANDARDS:
#   - Module layer: re-exports handler internals for cross-branch use
#   - This is the PUBLIC API that other branches import from
# =============================================

"""
Telegram Direct Chat Module - Public API

Re-exports shared Telegram utilities from the handler layer so that
other branches (assistant, test, etc.) can import them without
triggering the cross-branch handler guard.

Usage from other branches:
    from api.apps.modules.telegram_chat import run_direct_chat
    from api.apps.modules.telegram_chat import (
        STANDARD_COMMANDS, build_help_text, build_welcome_text,
        build_status_text, parse_command, handle_standard_command,
    )
"""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
if str(AIPASS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIPASS_ROOT))

# Re-export from handlers (allowed: we ARE the api branch)
from api.apps.handlers.telegram.direct_chat import run as run_direct_chat

from api.apps.handlers.telegram.telegram_standards import (
    STANDARD_COMMANDS,
    PROCESSING_MSG,
    ERROR_TEMPLATE,
    HELP_FOOTER,
    build_help_text,
    build_welcome_text,
    build_status_text,
    build_botfather_commands,
    parse_command,
    handle_standard_command,
)

__all__ = [
    "run_direct_chat",
    "STANDARD_COMMANDS",
    "PROCESSING_MSG",
    "ERROR_TEMPLATE",
    "HELP_FOOTER",
    "build_help_text",
    "build_welcome_text",
    "build_status_text",
    "build_botfather_commands",
    "parse_command",
    "handle_standard_command",
]
