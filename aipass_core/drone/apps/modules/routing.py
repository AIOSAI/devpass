#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: routing.py - Routing Module Interface
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-29): Module interface for routing handlers
# CODE STANDARDS: Module pattern - re-exports handler functions
# =============================================

"""
Routing Module - Public interface to routing handlers.

Provides entry point access to routing infrastructure without
direct handler imports.

Usage:
    from drone.apps.modules.routing import (
        preprocess_args,
        discover_modules,
        route_command,
    )
"""

# Re-export from handlers (internal)
from drone.apps.handlers.routing import (
    preprocess_args,
    discover_modules,
    route_command,
)

__all__ = [
    "preprocess_args",
    "discover_modules",
    "route_command",
]
