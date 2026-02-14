 #!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# FILE: help_display.py
# DESCRIPTION: Help display handler for registered systems and modules.
#              Supports multi-strategy resolution (registered system, directory,
#              file) and executes --help on discovered modules.
#
# DEPENDENCIES:
#   - drone.apps.handlers.registry (load_registry)
#   - drone.apps.handlers.discovery.module_scanning (resolve_scan_path)
#   - prax.apps.modules.logger (system logging)
#   - subprocess (--help execution)
#
# CODE STANDARDS:
#   - Handler independence (minimal cross-handler imports)
#   - No orchestration (handlers don't call modules)
#   - No CLI output (handlers are pure implementation)
#   - Type hints on all functions
#   - Multi-strategy target resolution (4 strategies)
#   - Same-package imports allowed for discovery handlers
#
# CHANGELOG:
#   - v2.0.1 (2025-11-16): Fixed handler standards violations:
#                          - Moved registry import from function to module level
#                          - Replaced silent failures with proper logging
#                          - Replaced error print() with logger.error()
#   - v2.0.0 (2025-11-13): BEAST MIGRATION - Extracted from drone_discovery.py (2,289 lines)
#   - v1.0.0 (2025-10-16): Original implementation in monolithic file
# ==============================================

"""
Help Display Handler

Shows --help output for registered systems and modules. Supports multiple strategies
for finding and displaying help text.

Features:
- System help display (all modules in a system)
- Module help display (single module)
- Multi-strategy resolution (registered system, directory, file)
- --help execution and output capture

Usage:
    from drone.apps.handlers.discovery.help_display import show_help_for_target

    success = show_help_for_target("flow")
    # Returns True if help was shown, False otherwise
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

import subprocess
from typing import Optional

# Same-package imports allowed
from .module_scanning import resolve_scan_path

# Cross-handler imports (registry is a stable public API)
from drone.apps.handlers.registry import load_registry

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "help_display"
DRONE_ROOT = AIPASS_ROOT / "drone"
ECOSYSTEM_ROOT = Path.home()

# =============================================
# HELP DISPLAY
# =============================================

def show_help_for_target(target: str) -> bool:
    """
    Show help output for a system or module

    Tries multiple strategies to find and display help:
    1. Check if it's a registered system
    2. Check if it's a directory in ecosystem
    3. Check if it's a module file
    4. Try @ symbol path resolution

    Args:
        target: System name, module name, or path

    Returns:
        True if help was shown, False if target not found

    Examples:
        >>> show_help_for_target("flow")  # Shows help for flow system
        True

        >>> show_help_for_target("backup_cli.py")  # Shows help for specific module
        True

        >>> show_help_for_target("@flow/flow_plan.py")  # Shows help via @ path
        True
    """
    # STRATEGY 1: Check if it's a registered system
    registry_data = load_registry()
    systems = registry_data.get('systems', {})

    if target in systems:
        # It's a registered system - get module path
        system_data = systems[target]
        module_path = system_data.get('module_path', '')

        if not module_path:
            logger.error(f"System '{target}' has no module path in registry")
            return False

        module_path_obj = Path(module_path)

        # If it's a directory, show help for all modules
        if module_path_obj.is_dir():
            console.print("=" * 70)
            console.print(f"HELP: {target} (System)")
            console.print("=" * 70)
            console.print()

            # Get all Python modules (check apps/ subdirectory first, then root)
            apps_dir = module_path_obj / "apps"
            if apps_dir.exists() and apps_dir.is_dir():
                python_files = sorted([f for f in apps_dir.glob("*.py") if not f.name.startswith('__')])
            else:
                python_files = sorted([f for f in module_path_obj.glob("*.py") if not f.name.startswith('__')])

            for i, py_file in enumerate(python_files):
                if i > 0:
                    console.print("\n" + "=" * 70 + "\n")

                # Run --help on each module
                try:
                    result = subprocess.run(
                        ['python3', str(py_file), '--help'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        console.print(f"Module: {py_file.name}")
                        console.print("-" * 70)
                        console.print(result.stdout)
                    else:
                        # Module doesn't have --help
                        logger.info(f"Module {py_file.name} doesn't support --help (exit code {result.returncode})")

                except subprocess.TimeoutExpired:
                    logger.error(f"Timeout running --help for {py_file.name}")
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    logger.error(f"Error running --help for {py_file.name}: {e}")

            return True
        else:
            # It's a single file - show its help
            try:
                result = subprocess.run(
                    ['python3', str(module_path_obj), '--help'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    console.print("=" * 70)
                    console.print(f"HELP: {target}")
                    console.print("=" * 70)
                    console.print()
                    console.print(result.stdout)
                    return True
                else:
                    logger.error(f"Failed to run --help for {target} (exit code {result.returncode})")
                    return False

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error(f"Error running --help for {target}: {e}")
                return False

    # STRATEGY 2: Check if it's a directory name in ecosystem
    potential_dir = ECOSYSTEM_ROOT / target
    if potential_dir.exists() and potential_dir.is_dir():
        console.print("=" * 70)
        console.print(f"HELP: {target} (Directory)")
        console.print("=" * 70)
        console.print()

        # Check apps/ subdirectory first (post-migration standard), then root
        apps_dir = potential_dir / "apps"
        if apps_dir.exists() and apps_dir.is_dir():
            python_files = sorted([f for f in apps_dir.glob("*.py") if not f.name.startswith('__')])
        else:
            python_files = sorted([f for f in potential_dir.glob("*.py") if not f.name.startswith('__')])

        if not python_files:
            console.print(f"No Python modules found in {target}")
            return True

        for i, py_file in enumerate(python_files):
            if i > 0:
                console.print("\n" + "=" * 70 + "\n")

            try:
                result = subprocess.run(
                    ['python3', str(py_file), '--help'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    console.print(f"Module: {py_file.name}")
                    console.print("-" * 70)
                    console.print(result.stdout)
                else:
                    logger.info(f"Module {py_file.name} doesn't support --help (exit code {result.returncode})")

            except subprocess.TimeoutExpired:
                logger.error(f"Timeout running --help for {py_file.name}")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error(f"Error running --help for {py_file.name}: {e}")

        return True

    # STRATEGY 3: Check if it's a module file in ecosystem
    # Try resolving as a file name (e.g., "backup_cli.py")
    potential_paths = []

    # Search common locations
    for system_dir in ECOSYSTEM_ROOT.iterdir():
        if system_dir.is_dir() and not system_dir.name.startswith('.'):
            potential_file = system_dir / target
            if potential_file.exists() and potential_file.suffix == '.py':
                potential_paths.append(potential_file)

    if potential_paths:
        # Found matching file(s) - show help for first match
        module_path = potential_paths[0]

        try:
            result = subprocess.run(
                ['python3', str(module_path), '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                console.print("=" * 70)
                console.print(f"HELP: {target} ({module_path.parent.name})")
                console.print("=" * 70)
                console.print()
                console.print(result.stdout)
                return True
            else:
                logger.error(f"Module '{target}' doesn't support --help (exit code {result.returncode})")
                return False

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Error running --help for module '{target}': {e}")
            return False

    # STRATEGY 4: Check if it's a path (absolute or @ symbol)
    try:
        resolved_path = resolve_scan_path(target)

        if resolved_path.is_file():
            # It's a file
            try:
                result = subprocess.run(
                    ['python3', str(resolved_path), '--help'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    console.print("=" * 70)
                    console.print(f"HELP: {resolved_path.name}")
                    console.print("=" * 70)
                    console.print()
                    console.print(result.stdout)
                    return True
                else:
                    logger.error(f"Module doesn't support --help (exit code {result.returncode})")
                    return False

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error(f"Error running --help: {e}")
                return False

        elif resolved_path.is_dir():
            # It's a directory - show help for all modules
            console.print("=" * 70)
            console.print(f"HELP: {resolved_path.name} (Directory)")
            console.print("=" * 70)
            console.print()

            python_files = sorted([f for f in resolved_path.glob("*.py") if not f.name.startswith('__')])

            for i, py_file in enumerate(python_files):
                if i > 0:
                    console.print("\n" + "=" * 70 + "\n")

                try:
                    result = subprocess.run(
                        ['python3', str(py_file), '--help'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        console.print(f"Module: {py_file.name}")
                        console.print("-" * 70)
                        console.print(result.stdout)
                    else:
                        logger.info(f"Module {py_file.name} doesn't support --help (exit code {result.returncode})")

                except subprocess.TimeoutExpired:
                    logger.error(f"Timeout running --help for {py_file.name}")
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    logger.error(f"Error running --help for {py_file.name}: {e}")

            return True

    except FileNotFoundError:
        # Not a valid path - this is expected for invalid targets
        logger.info(f"Target '{target}' is not a valid path")

    # Target not found
    return False
