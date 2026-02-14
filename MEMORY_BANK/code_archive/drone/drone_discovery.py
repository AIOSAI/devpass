#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: drone_discovery.py - Runtime Command Discovery
# Date: 2025-10-16
# Version: 2.0.0
# Category: drone
#
# CHANGELOG:
#   - v2.0.0 (2025-10-16): Complete rewrite - runtime --help parsing only
#   - v1.0.0 (2025-09-22): Initial implementation with AST parsing
# =============================================

"""
Drone Runtime Command Discovery

Discovers commands by executing modules with --help flag and parsing output.
Simple, universal, accurate.

Features:
- Runtime --help execution
- Commands: line parsing
- No AST complexity
- No code execution risks
- Works with any compliant module
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.append(str(AIPASS_ROOT))

from prax.apps.prax_logger import system_logger as logger

import json
import subprocess
from datetime import datetime, timezone
from typing import List

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "drone_discovery"
DRONE_ROOT = AIPASS_ROOT / "drone"
ECOSYSTEM_ROOT = Path.home()  # Scan from /home/aipass/ (not just aipass_core)
DRONE_JSON_DIR = DRONE_ROOT / "drone_json"

# 3-File JSON Pattern
CONFIG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_log.json"

# =============================================
# JSON FILE MANAGEMENT
# =============================================

def log_operation(operation: str, success: bool, details: str = "", error: str = ""):
    """Log discovery operations"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "success": success,
        "details": details,
        "error": error
    }

    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []

    logs.append(log_entry)

    # Keep last 1000 entries
    if len(logs) > 1000:
        logs = logs[-1000:]

    try:
        DRONE_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error saving log: {e}")

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
# RUNTIME DISCOVERY (THE ONLY METHOD)
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
            'help_output': str
        }
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

        # If directory provided, scan ALL Python files
        if module_path.is_dir():
            # Check for apps/ subdirectory first (post-migration layout)
            apps_dir = module_path / "apps"
            if apps_dir.exists() and apps_dir.is_dir():
                python_files = sorted(apps_dir.glob("*.py"))
            else:
                python_files = sorted(module_path.glob("*.py"))

            if not python_files:
                result['error'] = f"No Python files found in {module_path}"
                return result

            # Scan all Python files and aggregate
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
        backup_cli      → Look up in registry (name, not path)
        @flow           → /home/aipass/flow/
        @/flow/         → /home/aipass/flow/
        @/home/aipass/flow → /home/aipass/flow
        @flow/flow_plan.py → /home/aipass/flow/flow_plan.py
    """
    # STRATEGY 1: Check if it's a registered system name (no @ required for names)
    try:
        registry = load_system_registry(path_arg)
        if registry:
            # Found a registered system! Get its module_path
            # Registry structure: {cmd_name: {id, help, module_path, ...}}
            # All commands in a system have the same module_path
            first_cmd = next(iter(registry.values()))
            module_path = first_cmd.get('module_path')
            if module_path:
                target = Path(module_path)
                if target.exists():
                    return target
    except:
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
        flow                          → "flow" (direct system name)
        @flow                         → "flow" (@ symbol resolves to directory name)
        @flow/flow_plan.py            → "flow_plan" (@ symbol resolves to file stem)
        /home/aipass/flow             → "flow" (full path to directory)
        /home/aipass/flow/flow_plan.py → "flow_plan" (full path to file)
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

def format_scan_output(result: dict, show_full_command: bool = False) -> str:
    """Format scan results for display

    Args:
        result: Scan result dictionary
        show_full_command: If True, show Full Command column (default: False)
    """
    output = []

    output.append("=" * 70)
    output.append(f"Scanning: {result['module_path']}")
    output.append("=" * 70)

    if result['error'] and not result.get('is_directory'):
        output.append(f"\n❌ Error: {result['error']}")
        return "\n".join(output)

    # Handle directory scanning
    if result.get('is_directory'):
        modules_scanned = result.get('modules_scanned', [])

        output.append(f"\n📁 Directory scan - found {len(modules_scanned)} Python modules")
        output.append("")

        # Show modules with commands
        modules_with_cmds = [m for m in modules_scanned if m['commands']]
        modules_without_cmds = [m for m in modules_scanned if not m['commands']]

        if modules_with_cmds:
            output.append("✅ Modules with commands:")
            for mod in modules_with_cmds:
                output.append(f"   {mod['file']}: {len(mod['commands'])} commands")

        if modules_without_cmds:
            # Categorize by module type
            library_modules = [m for m in modules_without_cmds if m.get('module_type') == 'library']
            cli_modules = [m for m in modules_without_cmds if m.get('module_type') == 'cli']
            unknown_modules = [m for m in modules_without_cmds if m.get('module_type') not in ['library', 'cli']]

            output.append("")

            # Show library modules (no CLI by design)
            if library_modules:
                output.append("📚 Library modules (no CLI by design):")
                for mod in library_modules:
                    output.append(f"   {mod['file']}")

            # Show CLI modules that need updating
            if cli_modules:
                if library_modules:
                    output.append("")
                output.append("⚠️  CLI modules missing compliance (upgrade recommended):")
                for mod in cli_modules:
                    output.append(f"   {mod['file']}")

            # Show unknown modules
            if unknown_modules:
                if library_modules or cli_modules:
                    output.append("")
                output.append("⚠️  Modules without commands:")
                for mod in unknown_modules:
                    output.append(f"   {mod['file']}")

        if not result['commands']:
            output.append("")
            output.append("❌ No commands found in any module")
            return "\n".join(output)

        # Display aggregated commands
        output.append("")
        output.append(f"📋 Aggregated commands ({len(result['commands'])} total):")
        output.append("")

        # Build command list with module mapping (preserves order, handles duplicates)
        command_module_pairs = []
        for mod in modules_scanned:
            if mod['commands']:
                for cmd in mod['commands']:
                    command_module_pairs.append((cmd, mod['file'], mod['path']))

        # Conditionally show Full Command column
        if show_full_command:
            output.append(f"{'#':<8}{'Command':<24}{'Module':<30}{'Full Command'}")
            output.append(f"{'-' * 6}  {'-' * 22}  {'-' * 28}  {'-' * 50}")
        else:
            output.append(f"{'#':<8}{'Command':<24}{'Module'}")
            output.append(f"{'-' * 6}  {'-' * 22}  {'-' * 28}")

        # Get the base directory for cleaner paths
        base_dir = Path(result['module_path'])

        for i, (cmd, module, module_path) in enumerate(command_module_pairs, start=1):
            num = str(i)  # 1, 2, 3, ...
            if show_full_command:
                # Calculate relative path from base_dir (handles apps/ subdirectory)
                try:
                    rel_path = Path(module_path).relative_to(base_dir)
                    full_cmd = f"cd {base_dir} && python3 {rel_path} {cmd}"
                except ValueError:
                    # Fallback if relative path fails - use absolute path
                    full_cmd = f"python3 {module_path} {cmd}"
                output.append(f"{num:<8}{cmd:<24}{module:<30}{full_cmd}")
            else:
                output.append(f"{num:<8}{cmd:<24}{module}")

        output.append("")
        output.append(f"{len(result['commands'])} commands found across {len(modules_with_cmds)} modules")
        output.append("\n💡 Use 'drone register <module>' to register commands")

        return "\n".join(output)

    # Handle single file scanning
    if not result['success']:
        output.append("\n❌ Scan failed")
        return "\n".join(output)

    if not result['commands']:
        output.append("\n⚠️  No commands detected")
        return "\n".join(output)

    # Display commands
    output.append(f"\n✅ Commands detected via runtime --help:")
    output.append("")

    if show_full_command:
        # Show with Full Command column (for copy-paste testing)
        output.append(f"{'#':<8}{'Command':<25}{'Full Command'}")
        output.append(f"{'-' * 6}  {'-' * 23}  {'-' * 50}")

        # Generate full command paths
        module_path = Path(result['module_path'])
        base_dir = module_path.parent
        relative_path = module_path.relative_to(base_dir) if module_path.is_absolute() else module_path.name

        for i, cmd in enumerate(result['commands'], start=1):
            num = str(i)
            full_cmd = f"cd {base_dir} && python3 {relative_path} {cmd}"
            output.append(f"{num:<8}{cmd:<25}{full_cmd}")
    else:
        # Compact view (default)
        output.append(f"{'#':<8}{'Command'}")
        output.append(f"{'-' * 6}  {'-' * 30}")

        for i, cmd in enumerate(result['commands'], start=1):
            num = str(i)
            output.append(f"{num:<8}{cmd}")

    output.append("")
    output.append(f"{len(result['commands'])} commands found")
    output.append("\n💡 Use 'drone register <module>' to register commands")

    return "\n".join(output)

# =============================================
# REGISTRATION FUNCTIONS (PHASE 2)
# =============================================

def get_next_global_id() -> int:
    """Get next available global ID from registry"""
    from drone_registry import load_registry

    registry = load_registry()
    current_id = registry.get("global_id_counter", 0)
    return current_id + 1

def increment_global_id():
    """Increment global ID counter in registry"""
    from drone_registry import load_registry

    registry = load_registry()
    registry["global_id_counter"] = registry.get("global_id_counter", 0) + 1

    # Save updated registry
    registry_file = DRONE_JSON_DIR / "drone_registry.json"
    try:
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error updating global ID counter: {e}")

def register_module(module_path: str | Path, system_name: str | None = None) -> dict:
    """
    Register a module and assign global IDs to its commands

    Args:
        module_path: Path to Python module
        system_name: Optional system name (defaults to module name)

    Returns:
        {
            'success': bool,
            'system_name': str,
            'commands_registered': int,
            'registry_path': str,
            'commands': [{'id': int, 'name': str, 'help': str}, ...],
            'error': str | None
        }
    """
    result = {
        'success': False,
        'system_name': '',
        'commands_registered': 0,
        'registry_path': '',
        'commands': [],
        'error': None
    }

    try:
        # First, scan the module (this resolves @ symbols)
        scan_result = scan_module(module_path)

        if not scan_result['success']:
            result['error'] = scan_result.get('error', 'Scan failed')
            return result

        if not scan_result['commands']:
            # Check if module is non-compliant CLI module
            module_type = scan_result.get('module_type')
            resolved_path = Path(scan_result['module_path'])

            if module_type == 'cli':
                # Non-compliant CLI module - suggest upgrade
                result['error'] = 'No commands detected to register\n\n'
                result['error'] += '💡 This module appears to be non-compliant (missing --help with Commands: line)\n\n'
                result['error'] += '   Upgrade to compliance:\n'

                # Show path relative to ecosystem root if possible
                try:
                    rel_path = resolved_path.relative_to(ECOSYSTEM_ROOT)
                    result['error'] += f'   drone comply @{rel_path}'
                except ValueError:
                    result['error'] += f'   drone comply {resolved_path}'
            else:
                result['error'] = 'No commands detected to register'

            return result

        # Use resolved path from scan_result
        resolved_path = Path(scan_result['module_path'])

        # Determine system name
        if not system_name:
            if resolved_path.is_file():
                system_name = resolved_path.stem
            else:
                system_name = resolved_path.name

        result['system_name'] = system_name

        # Create registry directory for this system
        commands_dir = DRONE_ROOT / "commands"
        system_dir = commands_dir / system_name
        system_dir.mkdir(parents=True, exist_ok=True)

        registry_file = system_dir / "registry.json"
        result['registry_path'] = str(registry_file)

        # Load existing registry if present
        existing_registry = {}
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    existing_registry = json.load(f)
            except:
                existing_registry = {}

        # Build registry directly from modules_scanned to preserve all module:command combinations
        registry = {}

        if scan_result.get('is_directory') and scan_result.get('modules_scanned'):
            # Directory scan - process each module's commands
            for module_info in scan_result['modules_scanned']:
                module_path_for_cmd = module_info['path']
                module_stem = Path(module_path_for_cmd).stem

                for cmd_name in module_info['commands']:
                    # Create registry key: module:command
                    registry_key = f"{module_stem}:{cmd_name}"

                    # Check if already registered
                    if registry_key in existing_registry:
                        # Keep existing ID
                        existing_id = existing_registry[registry_key]['id']
                        already_reg = True
                    else:
                        # Assign new ID
                        existing_id = get_next_global_id()
                        increment_global_id()
                        already_reg = False

                    registry[registry_key] = {
                        'id': existing_id,
                        'command_name': cmd_name,
                        'module_name': module_stem,
                        'help': '',
                        'module_path': module_path_for_cmd,
                        'registered_date': datetime.now(timezone.utc).isoformat(),
                        'active': False
                    }
        else:
            # Single file scan - no module prefix needed
            for cmd_name in scan_result['commands']:
                module_stem = Path(resolved_path).stem
                registry_key = f"{module_stem}:{cmd_name}"

                # Check if already registered
                if registry_key in existing_registry:
                    existing_id = existing_registry[registry_key]['id']
                    already_reg = True
                else:
                    existing_id = get_next_global_id()
                    increment_global_id()
                    already_reg = False

                registry[registry_key] = {
                    'id': existing_id,
                    'command_name': cmd_name,
                    'module_name': module_stem,
                    'help': '',
                    'module_path': str(resolved_path),
                    'registered_date': datetime.now(timezone.utc).isoformat(),
                    'active': False
                }

        # Rebuild registered_commands from final registry
        final_registered_commands = []
        for registry_key, cmd_data in registry.items():
            # Check if it was already registered (check by registry_key)
            already_reg = registry_key in existing_registry
            final_registered_commands.append({
                'id': cmd_data['id'],
                'name': registry_key,  # Show as "module:command"
                'command_name': cmd_data['command_name'],  # Actual command
                'module_name': cmd_data['module_name'],  # Module name
                'help': cmd_data['help'],
                'already_registered': already_reg
            })

        # Save registry
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

        result['success'] = True
        result['commands'] = final_registered_commands
        result['commands_registered'] = len([c for c in final_registered_commands if not c.get('already_registered', False)])

        logger.info(f"[{MODULE_NAME}] Registered {result['commands_registered']} new commands for {system_name}")

    except Exception as e:
        result['error'] = f"Registration failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Registration error: {e}")

    return result

def format_registration_output(result: dict) -> str:
    """Format registration results for display"""
    output = []

    output.append("=" * 70)
    output.append(f"Registering: {result.get('system_name', 'Unknown')}")
    output.append("=" * 70)

    if result['error']:
        output.append(f"\n❌ Error: {result['error']}")
        return "\n".join(output)

    if not result['success']:
        output.append("\n❌ Registration failed")
        return "\n".join(output)

    # Show commands with IDs and module names
    output.append(f"\n✅ Commands registered:")
    output.append("")
    output.append(f"{'ID':<8}{'Command':<22}{'Module':<30}{'Status':<12}{'Description'}")
    output.append(f"{'-' * 6}  {'-' * 20}  {'-' * 28}  {'-' * 10}  {'-' * 40}")

    new_count = 0
    for cmd in result['commands']:
        id_str = f"{cmd['id']:03d}"
        command_name = cmd.get('command_name', cmd['name'])
        module_name = cmd.get('module_name', '')
        status = "EXISTS" if cmd.get('already_registered') else "NEW"
        if not cmd.get('already_registered'):
            new_count += 1
        help_text = cmd['help'][:40] if cmd['help'] else '(no description)'
        output.append(f"{id_str:<8}{command_name:<22}{module_name:<30}{status:<12}{help_text}")

    output.append("")
    output.append(f"{new_count} new commands registered")
    output.append(f"Registry: {result['registry_path']}")

    return "\n".join(output)

# =============================================
# ACTIVATION FUNCTIONS (PHASE 3)
# =============================================

def load_system_registry(system_name: str) -> dict:
    """Load registry for a system"""
    registry_file = DRONE_ROOT / "commands" / system_name / "registry.json"
    if not registry_file.exists():
        return {}

    try:
        with open(registry_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_system_registry(system_name: str, registry: dict):
    """Save registry for a system"""
    registry_file = DRONE_ROOT / "commands" / system_name / "registry.json"
    try:
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error saving registry: {e}")

def activate_commands_interactive(system_name: str) -> dict:
    """
    Interactive command activation

    Args:
        system_name: System to activate commands for

    Returns:
        {
            'success': bool,
            'activated': int,
            'active_commands': [{'id': int, 'command_name': str, 'drone_command': str}, ...],
            'error': str | None
        }
    """
    result = {
        'success': False,
        'activated': 0,
        'active_commands': [],
        'error': None
    }

    try:
        # Load registry
        registry = load_system_registry(system_name)
        if not registry:
            result['error'] = f"No registry found for system '{system_name}'"
            return result

        # Load active.json to get actual activation state
        active_file = DRONE_ROOT / "commands" / system_name / "active.json"
        active_commands = {}
        if active_file.exists():
            try:
                with open(active_file, 'r', encoding='utf-8') as f:
                    active_data = json.load(f)
                    # Build lookup by ID
                    for drone_cmd, cmd_info in active_data.items():
                        active_commands[cmd_info['id']] = drone_cmd
            except:
                pass

        # Build command list with IDs
        commands = []
        for cmd_name, cmd_data in registry.items():
            cmd_id = cmd_data['id']
            is_active = cmd_id in active_commands
            drone_cmd = active_commands.get(cmd_id, '')

            commands.append({
                'id': cmd_id,
                'name': cmd_name,
                'help': cmd_data.get('help', ''),
                'active': is_active,
                'drone_command': drone_cmd
            })

        # Sort by ID
        commands.sort(key=lambda x: x['id'])

        # Interactive loop
        activated = []

        while True:
            # Display current state
            print(f"\n{'='*70}")
            print(f"Activate commands for: {system_name}")
            print(f"{'='*70}\n")
            print(f"{'ID':<6}  {'Command':<35}  {'Active':<8}  {'Drone Command'}")
            print(f"{'-'*4}  {'-'*33}  {'-'*6}  {'-'*30}")

            for cmd in commands:
                id_str = f"{cmd['id']:03d}"
                active_str = "YES" if cmd['active'] else "No"
                drone_cmd = cmd['drone_command'] if cmd['drone_command'] else "n/a"
                print(f"{id_str:<6}  {cmd['name']:<35}  {active_str:<8}  {drone_cmd}")

            print(f"\n{len([c for c in commands if c['active']])} active / {len(commands)} total")

            # Prompt for ID
            print("\nEnter command ID to activate (or 'done' to finish): ", end='')
            user_input = input().strip().lower()

            if user_input == 'done':
                break

            # Parse ID
            try:
                cmd_id = int(user_input)
            except ValueError:
                print(f"❌ Invalid input. Enter a number or 'done'")
                continue

            # Find command
            target_cmd = None
            for cmd in commands:
                if cmd['id'] == cmd_id:
                    target_cmd = cmd
                    break

            if not target_cmd:
                print(f"❌ Command ID {cmd_id:03d} not found")
                continue

            if target_cmd['active']:
                print(f"⚠️  Command {cmd_id:03d} ({target_cmd['name']}) is already active")
                continue

            # Get drone command name
            print(f"\n{'─'*70}")
            print(f"Activating ID {cmd_id:03d}: {target_cmd['name']}")
            print(f"{'─'*70}")
            print(f"Drone command name (e.g., 'test create', 'backup snap'): ", end='')
            drone_cmd = input().strip()

            if not drone_cmd:
                print("❌ Drone command name required")
                continue

            # Prevent duplicate drone command names within current session
            duplicate_in_session = any(
                cmd_entry['drone_command'] == drone_cmd and cmd_entry['active']
                for cmd_entry in commands
            )
            if duplicate_in_session:
                print(f"⚠️  Drone command '{drone_cmd}' is already in use during this activation session.")
                print("   Choose a unique drone command name.")
                logger.warning(
                    f"[{MODULE_NAME}] Duplicate drone command '{drone_cmd}' blocked in activation session for {system_name}"
                )
                continue

            # Prevent conflicts with commands activated in other systems
            existing_activation = lookup_activated_command(drone_cmd)
            if existing_activation:
                existing_system = existing_activation.get('system', 'unknown')
                existing_id = existing_activation.get('id')
                if isinstance(existing_id, int):
                    id_display = f"{existing_id:03d}"
                else:
                    id_display = str(existing_id) if existing_id is not None else "unknown"
                print(f"⚠️  Drone command '{drone_cmd}' is already active in system '{existing_system}' (ID {id_display}).")
                print("   Choose a unique drone command name.")
                logger.warning(
                    f"[{MODULE_NAME}] Drone command '{drone_cmd}' already active in {existing_system} (ID {id_display}); blocking duplicate for {system_name}"
                )
                continue

            # Optional description
            print(f"Description (optional, press Enter to skip): ", end='')
            description = input().strip()
            if not description:
                description = target_cmd['help']

            # Mark as activated
            target_cmd['active'] = True
            target_cmd['drone_command'] = drone_cmd
            target_cmd['description'] = description

            activated.append({
                'id': cmd_id,
                'command_name': target_cmd['name'],
                'drone_command': drone_cmd,
                'description': description
            })

            print(f"✅ Activated {cmd_id:03d} as 'drone {drone_cmd}'")

        # Save activated commands
        if activated:
            # Update registry
            for cmd in commands:
                if cmd['name'] in registry:
                    registry[cmd['name']]['active'] = cmd['active']
                    if cmd.get('drone_command'):
                        registry[cmd['name']]['drone_command'] = cmd['drone_command']
                    if cmd.get('description'):
                        registry[cmd['name']]['description'] = cmd['description']

            save_system_registry(system_name, registry)

            # Save active.json
            active_file = DRONE_ROOT / "commands" / system_name / "active.json"
            active_data = {}
            for cmd in commands:
                if cmd['active']:
                    # Extract actual command name from registry (not the module:command key)
                    registry_data = registry[cmd['name']]
                    actual_command = registry_data.get('command_name', cmd['name'])

                    active_data[cmd['drone_command']] = {
                        'id': cmd['id'],
                        'command_name': actual_command,  # Use actual command, not registry key
                        'description': cmd.get('description', cmd['help']),
                        'module_path': registry_data.get('module_path', '')
                    }

            with open(active_file, 'w', encoding='utf-8') as f:
                json.dump(active_data, f, indent=2, ensure_ascii=False)

            result['success'] = True
            result['activated'] = len(activated)
            result['active_commands'] = activated
            logger.info(f"[{MODULE_NAME}] Activated {len(activated)} commands for {system_name}")
        else:
            result['success'] = True  # Not an error, just nothing activated
            result['activated'] = 0

    except Exception as e:
        result['error'] = f"Activation failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Activation error: {e}")

    return result

def format_activation_summary(system_name: str, result: dict) -> str:
    """Format activation summary"""
    output = []

    output.append(f"\n{'='*70}")
    output.append(f"Activation Summary: {system_name}")
    output.append(f"{'='*70}\n")

    if result['error']:
        output.append(f"❌ Error: {result['error']}")
        return "\n".join(output)

    if result['activated'] == 0:
        output.append("No new commands activated")
        return "\n".join(output)

    output.append(f"{'ID':<6}{'Command':<20}{'Drone Command':<25}{'Description'}")
    output.append(f"{'-'*4}  {'-'*18}  {'-'*23}  {'-'*30}")

    for cmd in result['active_commands']:
        id_str = f"{cmd['id']:03d}"
        desc = cmd['description'][:30] if cmd['description'] else ''
        output.append(f"{id_str:<6}{cmd['command_name']:<20}{cmd['drone_command']:<25}{desc}")

    output.append(f"\n✅ {result['activated']} commands activated")
    output.append(f"\nYou can now use:")
    for cmd in result['active_commands']:
        output.append(f"  drone {cmd['drone_command']}")

    return "\n".join(output)

# =============================================
# LIST & SYSTEMS FUNCTIONS (PHASE 4)
# =============================================

def list_all_systems() -> dict:
    """
    List all registered systems with statistics

    Returns:
        {
            'success': bool,
            'systems': [
                {
                    'name': str,
                    'registered': int,
                    'activated': int,
                    'module_path': str
                },
                ...
            ],
            'error': str | None
        }
    """
    result = {
        'success': False,
        'systems': [],
        'error': None
    }

    try:
        commands_dir = DRONE_ROOT / "commands"

        if not commands_dir.exists():
            result['error'] = "No systems registered yet"
            return result

        # Scan for system directories
        systems = []
        for system_dir in commands_dir.iterdir():
            if not system_dir.is_dir():
                continue

            registry_file = system_dir / "registry.json"
            if not registry_file.exists():
                continue

            # Load registry
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
            except:
                continue

            # Count registered commands
            total_registered = len(registry)

            # Count activated commands from active.json (not registry.json)
            active_file = system_dir / "active.json"
            total_activated = 0
            if active_file.exists():
                try:
                    with open(active_file, 'r', encoding='utf-8') as f:
                        active_data = json.load(f)
                        total_activated = len(active_data)
                except:
                    total_activated = 0

            # Get module path from any command
            module_path = ""
            if registry:
                first_cmd = next(iter(registry.values()))
                module_path = first_cmd.get('module_path', '')

            systems.append({
                'name': system_dir.name,
                'registered': total_registered,
                'activated': total_activated,
                'module_path': module_path
            })

        # Sort by name
        systems.sort(key=lambda x: x['name'])

        result['success'] = True
        result['systems'] = systems

    except Exception as e:
        result['error'] = f"Failed to list systems: {str(e)}"
        logger.error(f"[{MODULE_NAME}] List systems error: {e}")

    return result

def format_systems_output(result: dict) -> str:
    """Format systems list for display"""
    output = []

    output.append("=" * 80)
    output.append("Registered Systems")
    output.append("=" * 80)

    if result['error']:
        output.append(f"\n❌ Error: {result['error']}")
        return "\n".join(output)

    if not result['systems']:
        output.append("\n⚠️  No systems registered")
        output.append("\n💡 Use 'drone reg <module>' to register a system")
        return "\n".join(output)

    # Display systems table
    output.append(f"\n{'System':<20}{'Registered':<15}{'Activated':<15}{'Module Path'}")
    output.append(f"{'-' * 18}  {'-' * 13}  {'-' * 13}  {'-' * 40}")

    total_reg = 0
    total_act = 0

    for system in result['systems']:
        name = system['name']
        reg = system['registered']
        act = system['activated']
        path = system['module_path']

        # Shorten path if too long
        if len(path) > 40:
            path = "..." + path[-37:]

        output.append(f"{name:<20}  {reg:<15}  {act:<15}  {path}")

        total_reg += reg
        total_act += act

    output.append("")
    output.append(f"{len(result['systems'])} systems | {total_reg} total registered | {total_act} total activated")
    output.append("\n💡 Use 'drone list' to see all activated commands")
    output.append("💡 Use 'drone activate <system>' to activate commands")

    return "\n".join(output)

def list_activated_commands() -> dict:
    """
    List all activated commands across all systems

    Returns:
        {
            'success': bool,
            'commands': [
                {
                    'drone_command': str,
                    'id': int,
                    'system': str,
                    'command_name': str,
                    'description': str,
                    'module_path': str
                },
                ...
            ],
            'error': str | None
        }
    """
    result = {
        'success': False,
        'commands': [],
        'error': None
    }

    try:
        commands_dir = DRONE_ROOT / "commands"

        if not commands_dir.exists():
            result['error'] = "No systems registered yet"
            return result

        # Scan for system directories
        all_commands = []
        for system_dir in commands_dir.iterdir():
            if not system_dir.is_dir():
                continue

            active_file = system_dir / "active.json"
            if not active_file.exists():
                continue

            # Load active commands
            try:
                with open(active_file, 'r', encoding='utf-8') as f:
                    active_data = json.load(f)
            except:
                continue

            # Add system name to each command
            for drone_cmd, cmd_data in active_data.items():
                all_commands.append({
                    'drone_command': drone_cmd,
                    'id': cmd_data.get('id', 0),
                    'system': system_dir.name,
                    'command_name': cmd_data.get('command_name', ''),
                    'description': cmd_data.get('description', ''),
                    'module_path': cmd_data.get('module_path', '')
                })

        # Sort by drone command name
        all_commands.sort(key=lambda x: x['drone_command'])

        result['success'] = True
        result['commands'] = all_commands

    except Exception as e:
        result['error'] = f"Failed to list commands: {str(e)}"
        logger.error(f"[{MODULE_NAME}] List commands error: {e}")

    return result

def format_list_output(result: dict) -> str:
    """Format activated commands list for display"""
    output = []

    output.append("=" * 90)
    output.append("Activated Drone Commands")
    output.append("=" * 90)

    if result['error']:
        output.append(f"\n❌ Error: {result['error']}")
        return "\n".join(output)

    if not result['commands']:
        output.append("\n⚠️  No commands activated")
        output.append("\n💡 Use 'drone systems' to see registered systems")
        output.append("💡 Use 'drone activate <system>' to activate commands")
        return "\n".join(output)

    # Display commands table
    output.append(f"\n{'Drone Command':<25}{'ID':<6}{'System':<15}{'Command':<20}{'Description'}")
    output.append(f"{'-' * 23}  {'-' * 4}  {'-' * 13}  {'-' * 18}  {'-' * 30}")

    for cmd in result['commands']:
        drone_cmd = cmd['drone_command']
        id_str = f"{cmd['id']:03d}"
        system = cmd['system']
        command = cmd['command_name']
        desc = cmd['description'][:30] if cmd['description'] else '(no description)'

        output.append(f"{drone_cmd:<25}{id_str:<6}{system:<15}{command:<20}{desc}")

    output.append("")
    output.append(f"{len(result['commands'])} activated commands")
    output.append("\n💡 Usage: drone <command>")
    output.append("   Example: drone test create")

    return "\n".join(output)

# =============================================
# COMMAND EXECUTION FUNCTIONS (PHASE 5)
# =============================================

def lookup_activated_command(drone_command: str) -> dict | None:
    """
    Look up an activated drone command and return execution info

    Args:
        drone_command: The drone command to look up (e.g., "test create", "backup snap")

    Returns:
        {
            'module_path': str,
            'command_name': str,
            'system': str,
            'id': int
        } or None if not found
    """
    try:
        commands_dir = DRONE_ROOT / "commands"

        if not commands_dir.exists():
            return None

        # Search all active.json files
        for system_dir in commands_dir.iterdir():
            if not system_dir.is_dir():
                continue

            active_file = system_dir / "active.json"
            if not active_file.exists():
                continue

            # Load active commands
            try:
                with open(active_file, 'r', encoding='utf-8') as f:
                    active_data = json.load(f)
            except:
                continue

            # Check if our command is in this system
            if drone_command in active_data:
                cmd_data = active_data[drone_command]
                return {
                    'module_path': cmd_data.get('module_path', ''),
                    'command_name': cmd_data.get('command_name', ''),
                    'system': system_dir.name,
                    'id': cmd_data.get('id', 0)
                }

        return None

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error looking up command: {e}")
        return None

# =============================================
# REMOVE COMMAND (PHASE 6)
# =============================================

def remove_activated_command(drone_command: str) -> dict:
    """
    Remove an activated command

    Args:
        drone_command: The drone command name to remove

    Returns:
        {
            'success': bool,
            'drone_command': str,
            'command_name': str,
            'system': str,
            'id': int,
            'error': str | None
        }
    """
    result = {
        'success': False,
        'drone_command': drone_command,
        'command_name': '',
        'system': '',
        'id': 0,
        'error': None
    }

    try:
        commands_dir = DRONE_ROOT / "commands"

        if not commands_dir.exists():
            result['error'] = "No systems registered"
            return result

        # Search all active.json files for the command
        found_system = None
        found_data = None

        for system_dir in commands_dir.iterdir():
            if not system_dir.is_dir():
                continue

            active_file = system_dir / "active.json"
            if not active_file.exists():
                continue

            # Load active commands
            try:
                with open(active_file, 'r', encoding='utf-8') as f:
                    active_data = json.load(f)
            except:
                continue

            # Check if our command is in this system
            if drone_command in active_data:
                found_system = system_dir.name
                found_data = active_data[drone_command]

                # Remove from active.json
                del active_data[drone_command]

                # Save updated active.json
                with open(active_file, 'w', encoding='utf-8') as f:
                    json.dump(active_data, f, indent=2, ensure_ascii=False)

                # Also update registry.json to mark as inactive
                registry = load_system_registry(found_system)
                if found_data['command_name'] in registry:
                    registry[found_data['command_name']]['active'] = False
                    registry[found_data['command_name']]['drone_command'] = ''
                    save_system_registry(found_system, registry)

                result['success'] = True
                result['command_name'] = found_data.get('command_name', '')
                result['system'] = found_system
                result['id'] = found_data.get('id', 0)

                logger.info(f"[{MODULE_NAME}] Removed command '{drone_command}' from {found_system}")
                break

        if not result['success']:
            result['error'] = f"Command '{drone_command}' not found in any active system"

    except Exception as e:
        result['error'] = f"Remove failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Remove error: {e}")

    return result

def format_remove_output(result: dict) -> str:
    """Format remove results for display"""
    output = []

    output.append("=" * 70)
    output.append(f"Remove Command: {result['drone_command']}")
    output.append("=" * 70)

    if result['error']:
        output.append(f"\n❌ Error: {result['error']}")
        output.append("\n💡 Use 'drone list' to see activated commands")
        return "\n".join(output)

    if not result['success']:
        output.append("\n❌ Remove failed")
        return "\n".join(output)

    output.append(f"\n✅ Command removed successfully")
    output.append("")
    output.append(f"{'Field':<20}{'Value'}")
    output.append(f"{'-' * 18}  {'-' * 40}")
    output.append(f"{'Drone Command':<20}{result['drone_command']}")
    output.append(f"{'Original Command':<20}{result['command_name']}")
    output.append(f"{'System':<20}{result['system']}")
    output.append(f"{'ID':<20}{result['id']:03d}")

    output.append(f"\n💡 Command 'drone {result['drone_command']}' is no longer available")
    output.append(f"💡 Use 'drone activate {result['system']}' to re-activate it")

    return "\n".join(output)

# =============================================
# REFRESH COMMAND (PHASE 7)
# =============================================

def refresh_system(system_name: str) -> dict:
    """
    Re-scan a system's module for new/changed commands

    Args:
        system_name: System to refresh

    Returns:
        {
            'success': bool,
            'system_name': str,
            'new_commands': int,
            'total_commands': int,
            'commands': [{'id': int, 'name': str, 'status': str}, ...],
            'error': str | None,
            'orphaned_commands': List[str]
        }
    """
    result = {
        'success': False,
        'system_name': system_name,
        'new_commands': 0,
        'total_commands': 0,
        'commands': [],
        'error': None,
        'orphaned_commands': []
    }

    try:
        # Load existing registry
        existing_registry = load_system_registry(system_name)
        if not existing_registry:
            result['error'] = f"System '{system_name}' not registered"
            return result

        # Get directory path from registry (look at module_path and go up to directory)
        module_path = None
        if existing_registry:
            first_cmd = next(iter(existing_registry.values()))
            module_path_str = first_cmd.get('module_path', '')
            if module_path_str:
                # If it's a file, get the parent directory
                module_path_obj = Path(module_path_str)
                if module_path_obj.is_file():
                    module_path = str(module_path_obj.parent)
                else:
                    module_path = module_path_str

        if not module_path:
            result['error'] = "Module path not found in registry"
            return result

        # Re-scan the directory (convert to @ format for new standard)
        module_path_obj = Path(module_path)
        if module_path_obj.is_relative_to(ECOSYSTEM_ROOT):
            scan_path = f"@{module_path_obj.relative_to(ECOSYSTEM_ROOT)}"
        else:
            scan_path = f"@{module_path}"

        scan_result = scan_module(scan_path)

        if not scan_result['success']:
            result['error'] = scan_result.get('error', 'Scan failed')
            return result

        if not scan_result['commands']:
            result['error'] = 'No commands detected during refresh'
            return result

        # Build new registry from scan (same logic as register_module)
        new_registry = {}

        # Track existing activations to detect orphans later
        active_file = DRONE_ROOT / "commands" / system_name / "active.json"
        active_data = {}
        if active_file.exists():
            try:
                with open(active_file, 'r', encoding='utf-8') as f:
                    active_data = json.load(f)
            except Exception as e:
                logger.error(f"[{MODULE_NAME}] Failed to load active.json for {system_name}: {e}")
                active_data = {}

        if scan_result.get('is_directory') and scan_result.get('modules_scanned'):
            # Directory scan - process each module's commands
            for module_info in scan_result['modules_scanned']:
                module_path_for_cmd = module_info['path']
                module_stem = Path(module_path_for_cmd).stem

                for cmd_name in module_info['commands']:
                    # Create registry key: module:command
                    registry_key = f"{module_stem}:{cmd_name}"

                    # Check if already registered
                    if registry_key in existing_registry:
                        # Keep existing ID and data
                        new_registry[registry_key] = existing_registry[registry_key]
                        # Update module_path in case it changed
                        new_registry[registry_key]['module_path'] = module_path_for_cmd
                    else:
                        # Assign new ID
                        new_id = get_next_global_id()
                        increment_global_id()

                        new_registry[registry_key] = {
                            'id': new_id,
                            'command_name': cmd_name,
                            'module_name': module_stem,
                            'help': '',
                            'module_path': module_path_for_cmd,
                            'registered_date': datetime.now(timezone.utc).isoformat(),
                            'active': False
                        }

        # Detect orphaned activations (commands still marked active but no longer present)
        if active_data:
            valid_pairs = {
                (cmd_data.get('module_path'), cmd_data.get('command_name'))
                for cmd_data in new_registry.values()
            }

            orphaned_drone_commands = []
            updated_active_data = {}

            for drone_cmd, cmd_info in active_data.items():
                key = (cmd_info.get('module_path'), cmd_info.get('command_name'))
                if key in valid_pairs:
                    updated_active_data[drone_cmd] = cmd_info
                else:
                    orphaned_drone_commands.append(drone_cmd)

            if orphaned_drone_commands:
                logger.warning(
                    f"[{MODULE_NAME}] Removing orphaned activations for system {system_name}: {orphaned_drone_commands}"
                )
                result['orphaned_commands'] = orphaned_drone_commands
                active_data = updated_active_data
            else:
                active_data = updated_active_data

        # Persist healed active.json if changes were made
        if active_data is not None and active_file.exists():
            try:
                with open(active_file, 'w', encoding='utf-8') as f:
                    json.dump(active_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"[{MODULE_NAME}] Failed to write healed active.json for {system_name}: {e}")

        # Build command list for display
        new_command_list = []
        existing_keys = set(existing_registry.keys())
        new_keys = set(new_registry.keys())

        new_commands_found = new_keys - existing_keys

        for registry_key in sorted(new_registry.keys(), key=lambda k: new_registry[k]['id']):
            cmd_data = new_registry[registry_key]
            status = 'NEW' if registry_key in new_commands_found else 'EXISTS'

            new_command_list.append({
                'id': cmd_data['id'],
                'name': registry_key,
                'status': status
            })

        # Save updated registry
        save_system_registry(system_name, new_registry)

        result['success'] = True
        result['new_commands'] = len(new_commands_found)
        result['total_commands'] = len(new_registry)
        result['commands'] = new_command_list

        logger.info(f"[{MODULE_NAME}] Refreshed {system_name}: {len(new_commands_found)} new commands")

    except Exception as e:
        result['error'] = f"Refresh failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Refresh error: {e}")

    return result

def format_refresh_output(result: dict) -> str:
    """Format refresh results for display"""
    output = []

    output.append("=" * 70)
    output.append(f"Refresh System: {result['system_name']}")
    output.append("=" * 70)

    if result['error']:
        output.append(f"\n❌ Error: {result['error']}")
        return "\n".join(output)

    if not result['success']:
        output.append("\n❌ Refresh failed")
        return "\n".join(output)

    if result.get('orphaned_commands'):
        output.append("\n⚠️  Removed orphaned activations (no matching commands detected):")
        for drone_cmd in result['orphaned_commands']:
            output.append(f"   - drone {drone_cmd}")

    # Show all commands with status
    output.append(f"\n✅ System refreshed successfully")
    output.append("")
    output.append(f"{'ID':<8}{'Command':<22}{'Module':<30}{'Status'}")
    output.append(f"{'-' * 6}  {'-' * 20}  {'-' * 28}  {'-' * 15}")

    for cmd in result['commands']:
        id_str = f"{cmd['id']:03d}"
        status = cmd['status']

        # Parse module:command format
        cmd_name = cmd['name']
        if ':' in cmd_name:
            module_name, command_name = cmd_name.split(':', 1)
        else:
            # Legacy format (no module prefix)
            module_name = ''
            command_name = cmd_name

        output.append(f"{id_str:<8}{command_name:<22}{module_name:<30}{status}")

    output.append("")
    output.append(f"Total: {result['total_commands']} commands")
    output.append(f"New: {result['new_commands']} commands")

    if result['new_commands'] > 0:
        output.append(f"\n💡 Use 'drone activate {result['system_name']}' to activate new commands")
    else:
        output.append("\n💡 No new commands detected")

    return "\n".join(output)

# =============================================
# EDIT ACTIVATED COMMAND (PHASE 8)
# =============================================

def edit_activated_command_interactive() -> dict:
    """
    Interactive command editing - list all activated commands, select by ID, edit fields

    Returns:
        {
            'success': bool,
            'edited': bool,
            'command_id': int,
            'drone_command': str,
            'changes': dict,
            'error': str | None
        }
    """
    result = {
        'success': False,
        'edited': False,
        'command_id': None,
        'drone_command': None,
        'changes': {},
        'error': None
    }

    try:
        # Step 1: List all activated commands
        list_result = list_activated_commands()
        if not list_result['success'] or not list_result['commands']:
            result['error'] = list_result.get('error', 'No activated commands found')
            return result

        # Display the list
        print(format_list_output(list_result))
        print()

        # Step 2: Prompt for ID
        print("Enter ID to edit (or press Enter to cancel): ", end='')
        user_input = input().strip()

        if not user_input:
            result['success'] = True  # User cancelled, not an error
            result['error'] = 'Cancelled by user'
            return result

        # Parse ID
        try:
            cmd_id = int(user_input)
        except ValueError:
            result['error'] = f"Invalid ID: {user_input}"
            return result

        # Find the command with this ID
        target_command = None
        for cmd in list_result['commands']:
            if cmd['id'] == cmd_id:
                target_command = cmd
                break

        if not target_command:
            result['error'] = f"Command ID {cmd_id:03d} not found"
            return result

        # Step 3: Edit workflow
        print(f"\n{'='*70}")
        print(f"Editing Command ID: {cmd_id:03d}")
        print(f"{'='*70}\n")

        system_name = target_command['system']
        old_drone_cmd = target_command['drone_command']
        old_description = target_command['description']

        changes = {}

        # Edit drone command name
        print(f"Current drone command: {old_drone_cmd}")
        print(f"New drone command [press Enter to keep]: ", end='')
        new_drone_cmd = input().strip()

        if new_drone_cmd and new_drone_cmd != old_drone_cmd:
            changes['drone_command'] = {'old': old_drone_cmd, 'new': new_drone_cmd}
            print(f"→ Changed to: {new_drone_cmd}")
        else:
            new_drone_cmd = old_drone_cmd
            print(f"→ No change")

        # Edit description
        print(f"\nCurrent description: {old_description}")
        print(f"New description [press Enter to keep]: ", end='')
        new_description = input().strip()

        if new_description and new_description != old_description:
            changes['description'] = {'old': old_description, 'new': new_description}
            print(f"→ Changed to: {new_description}")
        else:
            new_description = old_description
            print(f"→ No change")

        # Step 4: Save changes if any
        if changes:
            # Load active.json for this system
            active_file = DRONE_ROOT / "commands" / system_name / "active.json"

            if not active_file.exists():
                result['error'] = f"Active file not found for system '{system_name}'"
                return result

            with open(active_file, 'r', encoding='utf-8') as f:
                active_data = json.load(f)

            # Update the command
            if old_drone_cmd in active_data:
                # If drone command name changed, need to move the key
                if 'drone_command' in changes:
                    cmd_data = active_data.pop(old_drone_cmd)
                    cmd_data['description'] = new_description
                    active_data[new_drone_cmd] = cmd_data
                else:
                    # Just update description
                    active_data[old_drone_cmd]['description'] = new_description

                # Save back to active.json
                with open(active_file, 'w', encoding='utf-8') as f:
                    json.dump(active_data, f, indent=2, ensure_ascii=False)

                # Also update registry.json
                registry_file = DRONE_ROOT / "commands" / system_name / "registry.json"
                if registry_file.exists():
                    with open(registry_file, 'r', encoding='utf-8') as f:
                        registry = json.load(f)

                    # Find and update the command in registry
                    command_name = target_command['command_name']
                    if command_name in registry:
                        if 'drone_command' in changes:
                            registry[command_name]['drone_command'] = new_drone_cmd
                        if 'description' in changes:
                            registry[command_name]['description'] = new_description

                        with open(registry_file, 'w', encoding='utf-8') as f:
                            json.dump(registry, f, indent=2, ensure_ascii=False)

                result['success'] = True
                result['edited'] = True
                result['command_id'] = cmd_id
                result['drone_command'] = new_drone_cmd
                result['changes'] = changes

                print(f"\n✅ Updated command {cmd_id:03d} ({system_name})")
                logger.info(f"[{MODULE_NAME}] Edited command {cmd_id:03d}: {changes}")
            else:
                result['error'] = f"Command '{old_drone_cmd}' not found in active.json"
                return result
        else:
            result['success'] = True
            result['edited'] = False
            result['command_id'] = cmd_id
            print(f"\n✅ No changes made to command {cmd_id:03d}")

    except Exception as e:
        result['error'] = f"Edit failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Edit command error: {e}")

    return result

def format_edit_output(result: dict) -> str:
    """Format edit command output for display"""
    output = []

    if result['error'] and result['error'] != 'Cancelled by user':
        output.append(f"❌ Error: {result['error']}")
    elif result['error'] == 'Cancelled by user':
        output.append("Cancelled")
    elif result['edited']:
        output.append(f"\n✅ Command {result['command_id']:03d} updated successfully")
        if result['changes']:
            output.append("\nChanges made:")
            for field, change in result['changes'].items():
                output.append(f"  {field}: '{change['old']}' → '{change['new']}'")
    else:
        output.append(f"\nℹ️  No changes made")

    return "\n".join(output)

# =============================================
# CLI/EXECUTION
# =============================================
# SYSTEM/MODULE HELP DISPLAY (CONVENIENCE FEATURE)
# =============================================

def show_help_for_target(target: str) -> bool:
    """
    Show help output for a system or module

    Usage:
        drone backup_system  → shows help for all modules in backup_system
        drone flow           → shows help for flow system
        drone backup_cli.py  → shows help for backup_cli.py module

    Args:
        target: System name, module name, or path

    Returns:
        True if help was shown, False if target not found
    """
    from drone_registry import load_registry

    # STRATEGY 1: Check if it's a registered system
    registry_data = load_registry()
    systems = registry_data.get('systems', {})

    if target in systems:
        # It's a registered system - get module path
        system_data = systems[target]
        module_path = system_data.get('module_path', '')

        if not module_path:
            print(f"Error: System '{target}' has no module path")
            return False

        module_path_obj = Path(module_path)

        # If it's a directory, show help for all modules
        if module_path_obj.is_dir():
            print("=" * 70)
            print(f"HELP: {target} (System)")
            print("=" * 70)
            print()

            # Get all Python modules (check apps/ subdirectory first, then root)
            apps_dir = module_path_obj / "apps"
            if apps_dir.exists() and apps_dir.is_dir():
                python_files = sorted([f for f in apps_dir.glob("*.py") if not f.name.startswith('__')])
            else:
                python_files = sorted([f for f in module_path_obj.glob("*.py") if not f.name.startswith('__')])

            for i, py_file in enumerate(python_files):
                if i > 0:
                    print("\n" + "=" * 70 + "\n")

                # Run --help on each module
                try:
                    result = subprocess.run(
                        ['python3', str(py_file), '--help'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        print(f"Module: {py_file.name}")
                        print("-" * 70)
                        print(result.stdout)
                    else:
                        # Module might not have --help, skip silently
                        pass

                except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                    # Skip modules that fail
                    pass

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
                    print("=" * 70)
                    print(f"HELP: {target}")
                    print("=" * 70)
                    print()
                    print(result.stdout)
                    return True
                else:
                    print(f"Error running --help for {target}")
                    return False

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Error: {e}")
                return False

    # STRATEGY 2: Check if it's a directory name in ecosystem
    potential_dir = ECOSYSTEM_ROOT / target
    if potential_dir.exists() and potential_dir.is_dir():
        print("=" * 70)
        print(f"HELP: {target} (Directory)")
        print("=" * 70)
        print()

        # Check apps/ subdirectory first (post-migration standard), then root
        apps_dir = potential_dir / "apps"
        if apps_dir.exists() and apps_dir.is_dir():
            python_files = sorted([f for f in apps_dir.glob("*.py") if not f.name.startswith('__')])
        else:
            python_files = sorted([f for f in potential_dir.glob("*.py") if not f.name.startswith('__')])

        if not python_files:
            print(f"No Python modules found in {target}")
            return True

        for i, py_file in enumerate(python_files):
            if i > 0:
                print("\n" + "=" * 70 + "\n")

            try:
                result = subprocess.run(
                    ['python3', str(py_file), '--help'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    print(f"Module: {py_file.name}")
                    print("-" * 70)
                    print(result.stdout)

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass

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
                print("=" * 70)
                print(f"HELP: {target} ({module_path.parent.name})")
                print("=" * 70)
                print()
                print(result.stdout)
                return True
            else:
                print(f"Error: Module '{target}' doesn't support --help")
                return False

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error: {e}")
            return False

    # STRATEGY 3: Check if it's a path (absolute or @ symbol)
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
                    print("=" * 70)
                    print(f"HELP: {resolved_path.name}")
                    print("=" * 70)
                    print()
                    print(result.stdout)
                    return True
                else:
                    print(f"Error: Module doesn't support --help")
                    return False

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Error: {e}")
                return False

        elif resolved_path.is_dir():
            # It's a directory - show help for all modules
            print("=" * 70)
            print(f"HELP: {resolved_path.name} (Directory)")
            print("=" * 70)
            print()

            python_files = sorted([f for f in resolved_path.glob("*.py") if not f.name.startswith('__')])

            for i, py_file in enumerate(python_files):
                if i > 0:
                    print("\n" + "=" * 70 + "\n")

                try:
                    result = subprocess.run(
                        ['python3', str(py_file), '--help'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        print(f"Module: {py_file.name}")
                        print("-" * 70)
                        print(result.stdout)

                except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                    pass

            return True

    except FileNotFoundError:
        # Not a valid path
        pass

    # Target not found
    return False

# =============================================

def main():
    """Test runtime discovery"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 drone_discovery.py <module_path>")
        print("\nExample:")
        print("  python3 drone_discovery.py /home/aipass/backup_system/backup_cli.py")
        sys.exit(1)

    module_path = sys.argv[1]

    print(f"Testing runtime discovery on: {module_path}\n")

    result = scan_module(module_path)
    print(format_scan_output(result))

    if result['success']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
