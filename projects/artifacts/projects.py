#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: main.py - projects Branch Orchestrator
# Date: 2025-11-08
# Version: 1.0.0
# Category: {{branch_category}}
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-08): Initial version - modular architecture
# =============================================

"""
projects Branch - Main Orchestrator

Modular architecture with auto-discovered modules.
Main handles routing, modules implement functionality.
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))

# Standard library imports
import argparse
import importlib
from typing import Dict, Any, Optional, List

# AIPass infrastructure imports
from prax.apps.prax_logger import system_logger as logger

# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

# Module root
MODULE_ROOT = Path(__file__).parent.parent

# Modules directory
MODULES_DIR = MODULE_ROOT / "modules"

# =============================================================================
# MODULE DISCOVERY
# =============================================================================

def discover_modules() -> List[Any]:
    """
    Auto-discover modules from modules/ directory

    Returns:
        List of module objects with handle_command() function
    """
    modules = []

    if not MODULES_DIR.exists():
        logger.warning(f"Modules directory not found: {MODULES_DIR}")
        return modules

    # Add modules directory to path
    sys.path.insert(0, str(MODULES_DIR))

    logger.info(f"[{Path(__file__).stem}] Discovering modules...")

    for file_path in MODULES_DIR.glob("*.py"):
        # Skip __init__.py and private files
        if file_path.name.startswith("_"):
            continue

        module_name = file_path.stem

        try:
            # Import module
            module = importlib.import_module(module_name)

            # Check for required interface
            if hasattr(module, 'handle_command'):
                modules.append(module)
                logger.info(f"  [+] {module_name}")
            else:
                logger.warning(f"  [!] {module_name} - missing handle_command()")

        except Exception as e:
            logger.error(f"  [-] {module_name} - import error: {e}")

    logger.info(f"[{Path(__file__).stem}] Discovered {len(modules)} modules")
    return modules

# =============================================================================
# COMMAND ROUTING
# =============================================================================

def route_command(args: argparse.Namespace, modules: List[Any]) -> bool:
    """
    Route command to appropriate module

    Args:
        args: Parsed command line arguments
        modules: List of discovered modules

    Returns:
        True if command was handled
    """
    for module in modules:
        try:
            if module.handle_command(args):
                return True
        except Exception as e:
            logger.error(f"Module error: {e}")

    return False

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='projects Branch Operations',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Add your command line arguments here
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Discover modules
    modules = discover_modules()

    if not modules:
        print("❌ ERROR: No modules found")
        return 1

    # Route command
    if route_command(args, modules):
        return 0
    else:
        print(f"❌ ERROR: Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
