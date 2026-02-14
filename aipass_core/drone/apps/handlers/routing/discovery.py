#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: discovery.py - Module Discovery Handler
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/handlers/routing
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-29): Extracted from drone.py lines 105-133
# CODE STANDARDS: Handler pattern - no prax, no CLI
# =============================================

"""
Module discovery - auto-discovers modules in drone's modules/ directory.
"""

from pathlib import Path
from typing import List, Any, Optional
import importlib


# Default modules directory (can be overridden via parameter)
DEFAULT_MODULES_DIR = Path(__file__).parent.parent.parent / "modules"


def discover_modules(modules_dir: Optional[Path] = None) -> List[Any]:
    """
    Auto-discover modules in modules/ directory.

    Args:
        modules_dir: Optional path to modules directory.
                     Defaults to drone/apps/modules/

    Returns:
        List of module objects with handle_command() method
    """
    if modules_dir is None:
        modules_dir = DEFAULT_MODULES_DIR

    modules = []

    if not modules_dir.exists():
        return modules

    for file_path in modules_dir.glob("*.py"):
        if file_path.name.startswith("_"):
            continue

        module_name = f"drone.apps.modules.{file_path.stem}"

        try:
            module = importlib.import_module(module_name)

            if hasattr(module, 'handle_command'):
                modules.append(module)
        except Exception:
            # Continue on import failure - invalid modules are skipped
            # Caller should handle logging if needed
            continue

    return modules
