#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: resolver.py - Module Path Resolution Handler
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/handlers/routing
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-29): Extracted from drone.py lines 164-193
# CODE STANDARDS: Handler pattern - no prax, no CLI
# =============================================

"""
Module path resolution - finds modules by name across the ecosystem.
"""

from pathlib import Path
from typing import Optional


# Ecosystem root for searching
ECOSYSTEM_ROOT = Path.home()  # /home/aipass


def resolve_module_path(module_name: str) -> Optional[Path]:
    """
    Find a module by name, searching known locations.

    Args:
        module_name: e.g., "flow.py" or "seed.py"

    Returns:
        Full path to module or None if not found

    Searches:
        - /home/aipass/*/apps/
        - /home/aipass/aipass_core/*/apps/
    """
    # Strip .py if present for searching
    base_name = module_name.replace('.py', '')
    search_name = f"{base_name}.py"

    # Search locations
    search_paths = [
        ECOSYSTEM_ROOT,
        ECOSYSTEM_ROOT / "aipass_core"
    ]

    for root in search_paths:
        if not root.exists():
            continue
        for branch_dir in root.iterdir():
            if branch_dir.is_dir() and not branch_dir.name.startswith('.'):
                apps_path = branch_dir / "apps" / search_name
                if apps_path.exists():
                    return apps_path

    return None
