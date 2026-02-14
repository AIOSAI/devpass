#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: module_scanning.py - Module Scanning Handler
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/discovery
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): BEAST MIGRATION - Extracted from drone_discovery.py (2,289 lines)
#   - v1.0.0 (2025-10-16): Original implementation in monolithic file
# =============================================

"""
Module Scanning Handler

Discovery of Python modules with CLI interfaces. Two discovery methods:
1. Runtime --help execution (fast, may truncate long command lists)
2. Source code parsing (reliable, scans handle_command() functions)

Features:
- Runtime --help execution
- Source code command parsing
- @ symbol path resolution
- Module type detection (CLI vs library)
- Directory scanning (apps/ subdirectory aware)
- System name resolution

Usage:
    from drone.apps.handlers.discovery.module_scanning import discover_commands_runtime, discover_commands_from_source, scan_module

    result = scan_module("@flow")
    commands = result['commands']
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

import subprocess
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "module_scanning"
DRONE_ROOT = AIPASS_ROOT / "drone"
ECOSYSTEM_ROOT = Path.home()  # Scan from /home/aipass/ (not just aipass_core)

# =============================================
# MODULE TYPE DETECTION
# =============================================

def detect_module_type(file_path: Path) -> str:
    """
    Detect if a Python file is a CLI module or library module

    Args:
        file_path: Path to Python file

    Returns:
        "cli" if module has CLI patterns (argparse, sys.argv, if __name__ == "__main__")
        "library" if module appears to be a library (no CLI patterns)

    Example:
        >>> module_type = detect_module_type(Path("/home/aipass/flow/flow_plan.py"))
        >>> print(module_type)
        'cli'
    """
    try:
        content = file_path.read_text(encoding='utf-8')

        # CLI indicators
        cli_patterns = [
            'import argparse',
            'from argparse import',
            'ArgumentParser(',
            'add_subparsers(',
            'sys.argv[1',  # sys.argv[1:] or sys.argv[1]
            'subparsers.add_parser(',
            'if __name__ == "__main__"',  # Module intended to be run directly
            'if __name__ == \'__main__\'',  # Alternative quote style
        ]

        # Check for CLI patterns
        for pattern in cli_patterns:
            if pattern in content:
                return "cli"

        return "library"

    except Exception as e:
        logger.warning(f"[{MODULE_NAME}] Could not read {file_path.name} for type detection: {e}")
        return "unknown"

# =============================================
# RUNTIME DISCOVERY
# =============================================

def discover_commands_runtime(module_path: str | Path) -> dict:
    """
    Discover commands by running module with --help and parsing output

    Args:
        module_path: Path to Python module file

    Returns:
        {
            'success': bool,
            'commands': List[str],  # Simple list of command names
            'error': str | None,
            'help_output': str  # Full help text for debugging
        }

    Example:
        >>> result = discover_commands_runtime("/home/aipass/flow/flow_plan.py")
        >>> print(result['commands'])
        ['create', 'list', 'execute']
    """
    result = {
        'success': False,
        'commands': [],
        'error': None,
        'help_output': ''
    }

    module_path = Path(module_path)

    try:
        # Execute module with --help
        proc = subprocess.run(
            ['python3', str(module_path), '--help'],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(module_path.parent)
        )

        result['help_output'] = proc.stdout

        if proc.returncode != 0:
            result['error'] = f"Module returned exit code {proc.returncode}"
            logger.warning(f"[{MODULE_NAME}] {module_path.name} --help failed: {proc.stderr}")
            return result

        # Parse "Commands:" line from output
        for line in proc.stdout.split('\n'):
            stripped = line.strip()
            if stripped.startswith('Commands:'):
                # Extract comma-separated list after "Commands:"
                commands_str = stripped.split(':', 1)[1].strip()
                commands = [cmd.strip() for cmd in commands_str.split(',') if cmd.strip()]

                result['success'] = True
                result['commands'] = commands
                logger.info(f"[{MODULE_NAME}] Discovered {len(commands)} commands in {module_path.name}")
                return result

        # No "Commands:" line found
        result['error'] = 'No "Commands:" line found in --help output'
        logger.warning(f"[{MODULE_NAME}] {module_path.name} missing Commands: line")

    except subprocess.TimeoutExpired:
        result['error'] = "Module --help timed out after 5 seconds"
        logger.error(f"[{MODULE_NAME}] Timeout running {module_path.name} --help")
    except FileNotFoundError:
        result['error'] = f"Module not found: {module_path}"
    except Exception as e:
        result['error'] = f"Runtime discovery failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Error running {module_path.name}: {e}")

    return result

def discover_commands_from_source(branch_path: str | Path) -> dict:
    """
    Discover commands by directly scanning modules/ directory and parsing source

    More reliable than --help parsing. Scans [branch]/apps/modules/*.py files
    and extracts command lists from handle_command() functions.

    Args:
        branch_path: Path to branch (e.g., /home/aipass/seed)

    Returns:
        {
            'success': bool,
            'commands': List[str],  # All unique commands found
            'modules_scanned': int,
            'error': str | None
        }

    Pattern Detection:
        - command not in ["check", "validate"]
        - command != "audit"
        - command == "architecture"
        - command in ["help", "--help"]
    """
    import re
    import importlib.util

    result = {
        'success': False,
        'commands': [],
        'modules_scanned': [],  # Changed from int to list for formatter compatibility
        'error': None
    }

    branch_path = Path(branch_path)

    # Check for main module file first (e.g., seed.py, flow.py)
    main_module = None
    for py_file in branch_path.glob("apps/*.py"):
        if not py_file.name.startswith("_") and py_file.name != "__init__.py":
            main_module = py_file
            break

    # Scan modules/ subdirectory
    modules_dir = branch_path / "apps" / "modules"

    if not modules_dir.exists():
        result['error'] = f"Modules directory not found: {modules_dir}"
        return result

    all_commands = set()
    modules_scanned_count = 0

    for py_file in modules_dir.glob("*.py"):
        if py_file.name.startswith("_"):  # Skip __init__.py
            continue

        try:
            # Read source code
            source = py_file.read_text(encoding='utf-8')

            # Skip if no handle_command function
            if 'def handle_command' not in source:
                continue

            modules_scanned_count += 1

            # Extract primary command from module filename
            # e.g., error_handling_standard.py -> error_handling
            # e.g., standards_checklist.py -> checklist
            filename_stem = py_file.stem  # Remove .py extension

            # Remove common suffixes to find primary command
            primary_command = filename_stem
            primary_command = primary_command.replace('_standard', '')  # error_handling_standard -> error_handling
            primary_command = primary_command.replace('standards_', '')  # standards_checklist -> checklist

            # Verify this command is actually in the module
            all_patterns = []

            # Collect all commands from all patterns
            # Use \b word boundaries to avoid matching 'subcommand' etc.
            pattern1 = r'\bcommand\s+not\s+in\s+\[([^\]]+)\]'
            matches = re.findall(pattern1, source)
            for match in matches:
                all_patterns.extend(re.findall(r'["\']([^"\']+)["\']', match))

            pattern2 = r'\bcommand\s+in\s+\[([^\]]+)\]'
            matches = re.findall(pattern2, source)
            for match in matches:
                all_patterns.extend(re.findall(r'["\']([^"\']+)["\']', match))

            pattern3 = r'\bcommand\s+!=\s+["\']([^"\']+)["\']'
            all_patterns.extend(re.findall(pattern3, source))

            pattern4 = r'\bcommand\s+==\s+["\']([^"\']+)["\']'
            all_patterns.extend(re.findall(pattern4, source))

            # Add ALL commands found (not just one per module)
            # This fixes the issue where modules like standards_checklist.py handle multiple commands
            if all_patterns:
                # Add all unique commands from this module
                commands_found = list(set(all_patterns))  # Remove duplicates
                all_commands.update(commands_found)
                logger.info(f"[{MODULE_NAME}] Scanned {py_file.name} -> commands: {', '.join(commands_found)}")
            else:
                logger.warning(f"[{MODULE_NAME}] No commands found in {py_file.name}")

        except Exception as e:
            logger.warning(f"[{MODULE_NAME}] Error scanning {py_file.name}: {e}")
            continue

    if all_commands:
        result['success'] = True
        result['commands'] = sorted(list(all_commands))

        # Create modules_scanned entry for the main module (formatter expects list of dicts)
        if main_module:
            result['modules_scanned'] = [{
                'file': main_module.name,
                'path': str(main_module),
                'commands': sorted(list(all_commands)),
                'success': True,
                'error': None,
                'module_type': 'cli'
            }]

        logger.info(f"[{MODULE_NAME}] Discovered {len(result['commands'])} commands from {modules_scanned_count} module files")
    else:
        result['error'] = "No commands discovered"

    return result

# =============================================
# PATH RESOLUTION
# =============================================

def resolve_scan_path(path_arg: str) -> Path:
    """
    Universal path resolution - @ required for paths, registered names work without @

    Args:
        path_arg: User's path argument

    Returns:
        Resolved Path object

    Raises:
        FileNotFoundError: If resolved path doesn't exist

    Examples:
        >>> resolve_scan_path("@flow")
        Path('/home/aipass/flow/')

        >>> resolve_scan_path("@flow/flow_plan.py")
        Path('/home/aipass/flow/flow_plan.py')
    """
    # STRATEGY 1: Check if it's a registered system name (no @ required for names)
    try:
        from drone.apps.handlers.registry import load_registry
        registry = load_registry()
        systems = registry.get('systems', {})

        if path_arg in systems:
            # Found a registered system! Get its module_path
            system_data = systems[path_arg]
            module_path = system_data.get('module_path')
            if module_path:
                target = Path(module_path)
                if target.exists():
                    return target
    except Exception:
        pass  # Not a system name, try path resolution

    # STRATEGY 2: @ symbol required for all path operations
    if not path_arg.startswith("@"):
        error_msg = f"❌ Path operations require @ symbol\n\n"
        error_msg += f"💡 Standard format: drone scan @path\n\n"
        error_msg += f"   Supported formats:\n"
        error_msg += f"   @flow              → /home/aipass/flow\n"
        error_msg += f"   @/flow/            → /home/aipass/flow\n"
        error_msg += f"   @/home/aipass/flow → /home/aipass/flow\n"
        error_msg += f"   @flow/flow_plan.py → /home/aipass/flow/flow_plan.py\n\n"

        # Check if @ version would work
        at_version = ECOSYSTEM_ROOT / path_arg
        if at_version.exists():
            error_msg += f"   Try: drone scan @{path_arg}"
        # Search for filename in apps/ subdirectories
        elif "/" not in path_arg and path_arg.endswith(".py"):
            found_in_apps = []
            for branch_dir in ECOSYSTEM_ROOT.iterdir():
                if branch_dir.is_dir() and not branch_dir.name.startswith('.'):
                    apps_path = branch_dir / "apps" / path_arg
                    if apps_path.exists():
                        found_in_apps.append(apps_path)

            if found_in_apps:
                error_msg += f"   File '{path_arg}' found:\n"
                for found_path in found_in_apps[:3]:
                    rel_path = found_path.relative_to(ECOSYSTEM_ROOT)
                    error_msg += f"   drone scan @{rel_path}\n"

        raise FileNotFoundError(error_msg)

    # Extract path after @ symbol
    path_after_at = path_arg[1:]  # Remove @

    # STRATEGY: Check BRANCH_REGISTRY.json first for branch names
    # This handles branches like @devpulse that are not in standard locations
    if "/" not in path_after_at:
        # Simple branch name (not a path) - check registry
        try:
            import json
            registry_path = ECOSYSTEM_ROOT / "BRANCH_REGISTRY.json"
            if registry_path.exists():
                registry_data = json.loads(registry_path.read_text())
                branch_name = path_after_at.lower()
                for branch in registry_data.get("branches", []):
                    # Match by name, email, or aliases
                    aliases = [a.lower().lstrip("@") for a in branch.get("aliases", [])]
                    if (branch.get("name", "").lower() == branch_name or
                        branch.get("email", "").lower() == f"@{branch_name}" or
                        branch.get("email", "").lower() == branch_name or
                        branch_name in aliases):
                        branch_path = Path(branch.get("path", ""))
                        if branch_path.exists():
                            return branch_path
        except Exception:
            pass  # Fall through to filesystem lookups

    # Handle different path formats after @
    if path_after_at.startswith("/home/aipass/"):
        # Full absolute path: @/home/aipass/flow → /home/aipass/flow
        target = Path(path_after_at)
    elif path_after_at.startswith("/"):
        # Leading slash: @/flow/ → /home/aipass/flow
        target = ECOSYSTEM_ROOT / path_after_at.lstrip("/")
    else:
        # Relative: @flow → /home/aipass/flow
        target = ECOSYSTEM_ROOT / path_after_at

    # Try aipass_core/ subdirectory if direct path doesn't exist (core modules location)
    if not target.exists():
        aipass_core_target = ECOSYSTEM_ROOT / "aipass_core" / path_after_at
        if aipass_core_target.exists():
            target = aipass_core_target

    # Try apps/ subdirectory if direct path doesn't exist (post-migration)
    if not target.exists() and "/" in path_after_at:
        path_parts = path_after_at.lstrip("/").split("/", 1)
        if len(path_parts) == 2:
            dir_name, file_path = path_parts
            apps_target = ECOSYSTEM_ROOT / dir_name / "apps" / file_path
            if apps_target.exists():
                target = apps_target

    # Validate path exists - with helpful error messages
    if not target.exists():
        error_msg = f"❌ Path not found: {target}\n"

        path_part = path_arg[1:]  # Remove @ symbol

        # Check if just the directory exists (user might have typo in filename)
        if "/" in path_part:
            # Extract directory part
            dir_part = path_part.lstrip("/").split("/")[0]
            dir_path = ECOSYSTEM_ROOT / dir_part
            if dir_path.exists() and dir_path.is_dir():
                # Directory exists, maybe filename typo
                python_files = list(dir_path.glob("*.py"))
                apps_files = list((dir_path / "apps").glob("*.py")) if (dir_path / "apps").exists() else []

                if python_files or apps_files:
                    error_msg += f"\n💡 Directory '@{dir_part}' exists. Python files found:\n"
                    for f in python_files[:3]:
                        error_msg += f"   drone scan @{dir_part}/{f.name}\n"
                    for f in apps_files[:3]:
                        error_msg += f"   drone scan @{dir_part}/apps/{f.name}\n"
        else:
            # Check if it's a typo of an existing directory
            search_part = path_part.lstrip("/")
            possible_dirs = list(ECOSYSTEM_ROOT.glob(f"{search_part}*"))
            if possible_dirs:
                error_msg += f"\n💡 Similar directories found:\n"
                for d in possible_dirs[:3]:
                    error_msg += f"   drone scan @{d.name}\n"

        raise FileNotFoundError(error_msg)

    return target

def resolve_system_name(input_str: str) -> str:
    """
    Universal system name resolution - accepts system name, @ path, or full path

    Args:
        input_str: User input (system name, @ path, or full path)

    Returns:
        System name string

    Examples:
        >>> resolve_system_name("flow")
        'flow'

        >>> resolve_system_name("@flow/flow_plan.py")
        'flow_plan'
    """
    # STRATEGY 1: Check if it's a registered system (directory exists in commands/)
    commands_dir = DRONE_ROOT / "commands"
    system_dir = commands_dir / input_str
    if system_dir.exists() and system_dir.is_dir():
        # It's a registered system - return as-is
        return input_str

    # STRATEGY 2: Try resolving as path (@ symbol, full path, relative)
    try:
        resolved_path = resolve_scan_path(input_str)

        # Extract system name from resolved path
        if resolved_path.is_file():
            # File → use stem (flow_plan.py → flow_plan)
            return resolved_path.stem
        else:
            # Directory → use name (flow/ → flow)
            return resolved_path.name

    except FileNotFoundError:
        # Path resolution failed - treat as literal system name
        # This handles cases like "drone activate nonexistent"
        pass

    # STRATEGY 3: Fallback - return as-is (will fail later with clear error)
    return input_str

# =============================================
# MODULE SCANNING
# =============================================

def scan_module(module_path: str | Path) -> dict:
    """
    Scan a Python module and detect commands via runtime --help

    Args:
        module_path: Path to Python module file or directory

    Returns:
        {
            'success': bool,
            'module_path': str,
            'commands': List[str],
            'error': str | None,
            'help_output': str,
            'is_directory': bool,  # True if directory scan
            'modules_scanned': [...]  # List of module info if directory
        }

    Example:
        >>> result = scan_module("@flow")
        >>> print(f"Found {len(result['commands'])} commands")
        Found 12 commands
    """
    result = {
        'success': False,
        'module_path': str(module_path),
        'commands': [],
        'error': None,
        'help_output': ''
    }

    try:
        # Resolve path with @ symbol support (convert Path to str if needed)
        try:
            module_path = resolve_scan_path(str(module_path))
            result['module_path'] = str(module_path)
        except FileNotFoundError as e:
            result['error'] = str(e)
            return result

        # If directory provided, scan modules/ subdirectory using source parsing
        if module_path.is_dir():
            # Use source code parsing for directory scans (more reliable than --help)
            source_result = discover_commands_from_source(module_path)

            if source_result['success']:
                result['success'] = True
                result['is_directory'] = True
                result['commands'] = source_result['commands']
                result['modules_scanned'] = source_result['modules_scanned']
                logger.info(f"[{MODULE_NAME}] Found {len(result['commands'])} commands in {module_path}")
                return result

            # Fallback: If source parsing failed, try old runtime method
            logger.warning(f"[{MODULE_NAME}] Source parsing failed, falling back to runtime discovery")

            # Check for apps/ subdirectory first (post-migration layout)
            apps_dir = module_path / "apps"
            if apps_dir.exists() and apps_dir.is_dir():
                python_files = sorted(apps_dir.glob("*.py"))
            else:
                python_files = sorted(module_path.glob("*.py"))

            if not python_files:
                result['error'] = f"No Python files found in {module_path}"
                return result

            # Scan all Python files and aggregate (FALLBACK ONLY)
            result['is_directory'] = True
            result['modules_scanned'] = []
            all_commands = []

            for py_file in python_files:
                # Skip __init__.py and __pycache__
                if py_file.name.startswith('__'):
                    continue

                module_result = discover_commands_runtime(py_file)

                # Detect module type if no commands found
                module_type = None
                if not module_result['commands']:
                    module_type = detect_module_type(py_file)

                module_info = {
                    'file': py_file.name,
                    'path': str(py_file),
                    'commands': module_result['commands'],
                    'success': module_result['success'],
                    'error': module_result['error'],
                    'module_type': module_type  # "cli", "library", or None
                }

                result['modules_scanned'].append(module_info)
                all_commands.extend(module_result['commands'])

            # Set overall result
            result['success'] = len(all_commands) > 0
            result['commands'] = all_commands

            if not all_commands:
                result['error'] = f"No commands found in any Python files in {module_path}"

            return result

        # Verify file exists
        if not module_path.exists():
            result['error'] = f"File not found: {module_path}"
            return result

        # Discover via runtime
        discovery_result = discover_commands_runtime(module_path)

        result['success'] = discovery_result['success']
        result['commands'] = discovery_result['commands']
        result['error'] = discovery_result['error']
        result['help_output'] = discovery_result['help_output']

        # Detect module type if no commands found (for upgrade prompt)
        if not discovery_result['commands']:
            result['module_type'] = detect_module_type(module_path)

        if not discovery_result['success']:
            # Add helpful error message
            if result['error']:
                result['error'] += f"\n\nModule does not follow AIPass CLI standard."
                result['error'] += f"\nStandard: STANDARDS.md section 6.5"
                result['error'] += f"\n\nRequired: Module must implement --help with 'Commands: cmd1, cmd2, cmd3' line"

    except Exception as e:
        result['error'] = f"Scan failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Scan error: {e}")

    return result
