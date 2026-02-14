#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: args.py - Argument Preprocessing Handler
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/handlers/routing
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-29): Extracted from drone.py lines 55-96
# CODE STANDARDS: Handler pattern - no prax, no CLI
# =============================================

"""
Argument preprocessing - resolves @ arguments to full paths.

DRONE is the single source of truth for @ resolution.
"""

from pathlib import Path
from typing import List, Union

from drone.apps.handlers.paths import resolve_target


def preprocess_args(args: List[str]) -> List[str]:
    """
    Resolve all @ arguments to full paths before passing to modules.

    This ensures branches receive clean paths, not @ symbols.
    DRONE is the single source of truth for @ resolution.

    Args:
        args: List of arguments that may contain @ prefixes

    Returns:
        List of arguments with @ resolved to full paths

    Examples:
        >>> preprocess_args(["audit", "@flow"])
        ["audit", "/home/aipass/aipass_core/flow"]

        >>> preprocess_args(["create", "@aipass", "--template", "minimal"])
        ["create", "/home/aipass", "--template", "minimal"]
    """
    resolved_args = []

    for arg in args:
        if arg.startswith('@'):
            try:
                # Use paths handler for @ resolution
                resolved = resolve_target(arg)
                # resolve_target returns Path or "@all" string
                if isinstance(resolved, Path):
                    resolved_args.append(str(resolved))
                else:
                    # Pass through special targets like "@all"
                    resolved_args.append(resolved)
            except ValueError:
                # Can't resolve - pass raw (branch will get error)
                resolved_args.append(arg)
        else:
            resolved_args.append(arg)

    return resolved_args
