#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: __init__.py - Routing Handlers Package
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/handlers/routing
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-29): Initial extraction from drone.py
# CODE STANDARDS: Handler pattern - no prax, no CLI
# =============================================

"""
Routing Handlers - Core routing logic extracted from drone.py.

Public API:
    from drone.apps.handlers.routing import (
        preprocess_args,
        discover_modules,
        route_command,
        resolve_module_path,
    )
"""

from .args import preprocess_args
from .discovery import discover_modules
from .router import route_command
from .resolver import resolve_module_path

__all__ = [
    "preprocess_args",
    "discover_modules",
    "route_command",
    "resolve_module_path",
]
