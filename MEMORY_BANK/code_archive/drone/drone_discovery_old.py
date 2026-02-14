#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: drone_discovery.py - Module Discovery Engine
# Date: 2025-09-22
# Version: 1.0.0
# Category: drone
#
# CHANGELOG:
#   - v1.0.0 (2025-09-22): Initial implementation with prax patterns
# =============================================

"""
Drone Module Discovery Engine

Discovers AIPass modules and generates command metadata.
Based on prax_logger discovery patterns with drone-specific adaptations.

Features:
- Filesystem scanning with intelligent filtering
- Module detection via main() functions
- Command metadata generation
- Registry integration
"""

# =============================================
# IMPORTS
# =============================================

import sys
from pathlib import Path
AIPASS_ROOT = Path.home()
import sys
sys.path.append(str(AIPASS_ROOT))  # To ecosystem root
from prax.prax_logger import system_logger as logger

import json
import os
import ast
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional

# =============================================
# CONSTANTS & CONFIG
# =============================================

def get_project_root():
    """Get project root regardless of execution context - from STANDARDS.md"""
    current_file = Path(__file__).resolve()

    # Look for key project files to identify root
    for parent in current_file.parents:
        if (parent / "README.md").exists() and (parent / "CLAUDE.md").exists():
            return parent

    # Fallback to grandparent (typical for drone module)
    return current_file.parent.parent

MODULE_NAME = "drone_discovery"
ECOSYSTEM_ROOT = get_project_root()
DRONE_JSON_DIR = Path(__file__).parent / "drone_json"

# 3-File JSON Pattern
CONFIG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_log.json"

# Ignore patterns from prax_logger (proven working)
IGNORE_FOLDERS = {
    '.git', '__pycache__', '.venv', 'vendor', 'node_modules',
    'Archive', 'Backups', 'External_Code_Sources', 'WorkShop',
    '.claude-server-commander-logs',
    'backup_system/backups', 'archive.local', '.local/share/Trash'
}

# =============================================
# JSON FILE MANAGEMENT (3-FILE PATTERN)
# =============================================

def create_config_file():
    """Create default config file if it doesn't exist"""
    if CONFIG_FILE.exists():
        return

    default_config = {
        "module_name": MODULE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "enabled": True,
            "version": "1.0.0",
            "scan_patterns": ["*.py"],
            "ignore_patterns": list(IGNORE_FOLDERS),
            "scan_depth": 3,
            "auto_discovery_enabled": True,
            "command_detection_enabled": True,
            "module_validation_enabled": True,
            "discovery_directories": [
                "backup_system",
                "flow",
                "prax",
                "tools",
                "api"
            ]
        }
    }

    try:
        DRONE_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        logger.info(f"[{MODULE_NAME}] Config file created")
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error creating config file: {e}")

def load_config():
    """Load configuration"""
    create_config_file()

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error loading config: {e}")
        return {"config": {"enabled": True}}

def update_data_file(stats):
    """Update data file with current statistics"""
    data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "runtime_state": {
            "discovery_active": True,
            "scan_in_progress": False
        },
        "statistics": stats
    }

    try:
        DRONE_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error updating data file: {e}")

def log_operation(operation: str, success: bool, details: str = "", error: str = ""):
    """Log discovery operations to individual module log file"""
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
# HELPER FUNCTIONS
# =============================================

def should_ignore_path(path: Path) -> bool:
    """Check if path should be ignored based on patterns - from prax_logger"""
    path_parts = path.parts

    # Check against ignore folders
    for part in path_parts:
        if part in IGNORE_FOLDERS:
            return True

    return False

def is_executable_module(py_file: Path) -> bool:
    """Check if Python file looks like an executable command"""
    try:
        file_size = py_file.stat().st_size

        with open(py_file, 'r', encoding='utf-8') as f:
            if file_size < 10000:  # For files under 10KB, read everything
                content = f.read()
            else:
                # For larger files, read first 2KB and last 1KB
                content_start = f.read(2000)
                f.seek(max(0, file_size - 1000))
                content_end = f.read()
                content = content_start + content_end

        # Look for patterns that suggest it's a command
        patterns = [
            'if __name__ == "__main__"',
            'def main(',
            'argparse.ArgumentParser',
            'sys.argv'
        ]

        has_pattern = any(pattern in content for pattern in patterns)
        if has_pattern:
            logger.info(f"[{MODULE_NAME}] Found executable module: {py_file.name}")
        return has_pattern
    except Exception as e:
        logger.warning(f"[{MODULE_NAME}] Could not read {py_file}: {e}")
        return False

def extract_module_metadata(py_file: Path) -> Dict[str, str]:
    """Extract metadata from module header"""
    metadata = {
        "name": py_file.stem,
        "description": "No description available",
        "version": "1.0.0",
        "category": "unknown"
    }

    try:
        with open(py_file, 'r') as f:
            content = f.read(3000)  # Read header section

        lines = content.split('\n')
        for line in lines:
            if '# Name:' in line:
                metadata["description"] = line.split('# Name:')[1].strip()
            elif '# Version:' in line:
                metadata["version"] = line.split('# Version:')[1].strip()
            elif '# Category:' in line:
                metadata["category"] = line.split('# Category:')[1].strip()

    except Exception as e:
        logger.warning(f"Could not extract metadata from {py_file}: {e}")

    return metadata

# =============================================
# COMMAND DETECTION (AST PARSING)
# =============================================

def detect_commands_ast(module_path: str) -> dict:
    """
    Detect commands in a Python module using AST parsing

    Uses proven AST approach from Phase 0 testing:
    - Works for 95%+ of CLI modules
    - Safe (no code execution)
    - Handles nested subparsers, edge cases, multiple parsers

    Limitations (documented):
    - Cannot resolve dynamic choices from variables
    - Cannot detect loop-generated commands

    Returns:
        {
            'success': bool,
            'commands': [{'name': str, 'help': str}, ...],
            'error': str | None
        }
    """
    result = {
        'success': False,
        'commands': [],
        'error': None
    }

    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source)
        commands = []

        for node in ast.walk(tree):
            # Look for add_parser() calls (subparsers pattern)
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'add_parser'):
                    cmd_info = extract_add_parser_call(node)
                    if cmd_info:
                        commands.append(cmd_info)

                # Look for add_argument() calls with choices
                elif (isinstance(node.func, ast.Attribute) and
                      node.func.attr == 'add_argument'):
                    cmd_info = extract_add_argument_choices(node)
                    if cmd_info:
                        commands.extend(cmd_info)

        result['commands'] = commands
        result['success'] = True

    except Exception as e:
        result['error'] = f"AST parsing failed: {str(e)}"
        logger.warning(f"[{MODULE_NAME}] Could not parse {module_path}: {e}")

    return result

def extract_add_parser_call(node: ast.Call) -> dict | None:
    """Extract command info from add_parser() call"""
    if not node.args:
        return None

    cmd_name = None
    if isinstance(node.args[0], ast.Constant):
        cmd_name = node.args[0].value
    # Handle f-strings (e.g., f'filter_{status}')
    elif isinstance(node.args[0], ast.JoinedStr):
        # F-string detected - can't statically determine value
        return None

    if not cmd_name:
        return None

    help_text = ''
    for keyword in node.keywords:
        if keyword.arg == 'help' and isinstance(keyword.value, ast.Constant):
            help_text = keyword.value.value

    return {
        'name': cmd_name,
        'help': help_text
    }

def extract_add_argument_choices(node: ast.Call) -> list:
    """Extract commands from add_argument() with choices parameter"""
    commands = []

    choices = None
    for keyword in node.keywords:
        if keyword.arg == 'choices':
            if isinstance(keyword.value, ast.List):
                # Static list: choices=['a', 'b', 'c']
                choices = []
                for elt in keyword.value.elts:
                    if isinstance(elt, ast.Constant):
                        choices.append(elt.value)
            elif isinstance(keyword.value, ast.Name):
                # Variable reference: choices=BACKUP_MODES
                # Can't resolve at AST level - return empty
                return []
            elif isinstance(keyword.value, ast.ListComp):
                # List comprehension: choices=[e for e in ENVIRONMENTS]
                # Can't resolve at AST level - return empty
                return []
            elif isinstance(keyword.value, ast.Call):
                # Function call: choices=get_formats()
                # Can't resolve at AST level - return empty
                return []

    if not choices:
        return []

    help_text = ''
    for keyword in node.keywords:
        if keyword.arg == 'help' and isinstance(keyword.value, ast.Constant):
            help_text = keyword.value.value

    for choice in choices:
        commands.append({
            'name': choice,
            'help': help_text
        })

    return commands

def format_scan_output(result: dict) -> str:
    """
    Format scan results for display with letters (a, b, c...)

    Args:
        result: Output from scan_module()

    Returns:
        Formatted string ready for console display
    """
    output = []

    output.append("=" * 70)
    output.append(f"Scanning: {result['module_path']}")
    output.append("=" * 70)

    if result['error']:
        output.append(f"\n❌ Error: {result['error']}")
        return "\n".join(output)

    if not result['success']:
        output.append("\n❌ Scan failed")
        return "\n".join(output)

    # Show notes if any
    if result['notes']:
        output.append("\nℹ️  Notes:")
        for note in result['notes']:
            output.append(f"  {note}")

    if not result['commands']:
        output.append("\n⚠️  No commands detected")
        output.append("\nPossible reasons:")
        output.append("  - Module uses dynamic command generation (variables, loops)")
        output.append("  - Module doesn't use argparse")
        output.append("  - See NOTE_FROM_DRONE_BRANCH.md for compatibility info")
        return "\n".join(output)

    # Display commands with letters
    output.append(f"\n✅ Commands detected via argparse:")
    output.append("")
    output.append(f"{'Letter':<8}{'Command':<20}{'Description'}")
    output.append(f"{'-' * 6}  {'-' * 18}  {'-' * 40}")

    for i, cmd in enumerate(result['commands']):
        letter = chr(97 + i)  # a, b, c, ...
        cmd_name = cmd['name']
        help_text = cmd['help'][:60] if cmd['help'] else '(no description)'
        output.append(f"{letter:<8}{cmd_name:<20}{help_text}")

    output.append("")
    output.append(f"{len(result['commands'])} commands found")
    output.append("\n💡 Use 'drone reg <module>' to register commands")

    return "\n".join(output)

def scan_module(module_path: str | Path) -> dict:
    """
    Scan a Python module and detect available commands

    This is the main entry point for the 'drone scan' command.
    Uses AST parsing to detect argparse commands.

    Args:
        module_path: Path to Python module file or directory

    Returns:
        {
            'success': bool,
            'module_path': str,
            'commands': [{'name': str, 'help': str}, ...],
            'error': str | None,
            'notes': list  # Warnings about dynamic commands, etc.
        }
    """
    module_path = Path(module_path)
    result = {
        'success': False,
        'module_path': str(module_path),
        'commands': [],
        'error': None,
        'notes': []
    }

    try:
        # If directory provided, look for main Python file
        if module_path.is_dir():
            # Common patterns: module_name.py, main.py, cli.py, __main__.py, __init__.py
            dir_name = module_path.name
            candidates = [
                module_path / f"{dir_name}.py",
                module_path / "main.py",
                module_path / "cli.py",
                module_path / "__main__.py",
                module_path / "__init__.py",  # Package init file
            ]

            found = None
            for candidate in candidates:
                if candidate.exists():
                    found = candidate
                    break

            if not found:
                result['error'] = f"No main Python file found in {module_path}"
                return result

            module_path = found
            result['notes'].append(f"Scanning {module_path.name} in directory")

        # Verify file exists
        if not module_path.exists():
            result['error'] = f"File not found: {module_path}"
            return result

        # Detect commands using AST
        detection_result = detect_commands_ast(str(module_path))

        if detection_result['success']:
            result['commands'] = detection_result['commands']
            result['success'] = True

            # Add notes about limitations
            if len(result['commands']) == 0:
                result['notes'].append("No commands detected - module may use dynamic generation")
            else:
                result['notes'].append("Note: Commands with dynamic choices may not be detected")
        else:
            result['error'] = detection_result['error']

    except Exception as e:
        result['error'] = f"Scan failed: {str(e)}"
        logger.error(f"[{MODULE_NAME}] Scan error: {e}")

    return result

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
    registry_file = Path(__file__).parent / "drone_json" / "drone_registry.json"
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
        # First, scan the module
        scan_result = scan_module(module_path)

        if not scan_result['success']:
            result['error'] = scan_result.get('error', 'Scan failed')
            return result

        if not scan_result['commands']:
            result['error'] = 'No commands detected to register'
            return result

        # Determine system name
        module_path = Path(module_path)
        if not system_name:
            if module_path.is_file():
                system_name = module_path.stem
            else:
                system_name = module_path.name

        result['system_name'] = system_name

        # Create registry directory for this system
        commands_dir = Path(__file__).parent / "commands"
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

        # Assign IDs to new commands
        from datetime import datetime, timezone
        registered_commands = []

        for cmd in scan_result['commands']:
            # Check if already registered
            cmd_name = cmd['name']
            if cmd_name in existing_registry:
                # Already registered, keep existing ID
                existing_id = existing_registry[cmd_name]['id']
                registered_commands.append({
                    'id': existing_id,
                    'name': cmd_name,
                    'help': cmd['help'],
                    'already_registered': True
                })
            else:
                # New command, assign next ID
                new_id = get_next_global_id()
                increment_global_id()

                registered_commands.append({
                    'id': new_id,
                    'name': cmd_name,
                    'help': cmd['help'],
                    'already_registered': False
                })

        # Build registry structure
        registry = {}
        for cmd in registered_commands:
            registry[cmd['name']] = {
                'id': cmd['id'],
                'help': cmd['help'],
                'module_path': str(module_path),
                'registered_date': datetime.now(timezone.utc).isoformat(),
                'active': False  # Not activated yet
            }

        # Save registry
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

        result['success'] = True
        result['commands'] = registered_commands
        result['commands_registered'] = len([c for c in registered_commands if not c.get('already_registered', False)])

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

    # Show commands with IDs
    output.append(f"\n✅ Commands registered:")
    output.append("")
    output.append(f"{'ID':<6}{'Command':<20}{'Status':<15}{'Description'}")
    output.append(f"{'-' * 4}  {'-' * 18}  {'-' * 13}  {'-' * 40}")

    new_count = 0
    for cmd in result['commands']:
        id_str = f"{cmd['id']:03d}"
        status = "EXISTS" if cmd.get('already_registered') else "NEW"
        if not cmd.get('already_registered'):
            new_count += 1
        help_text = cmd['help'][:40] if cmd['help'] else '(no description)'
        output.append(f"{id_str:<6}{cmd['name']:<20}{status:<15}{help_text}")

    output.append("")
    output.append(f"{new_count} new commands registered")
    output.append(f"Registry: {result['registry_path']}")

    return "\n".join(output)

# =============================================
# ACTIVATION FUNCTIONS (PHASE 3)
# =============================================

def load_system_registry(system_name: str) -> dict:
    """Load registry for a system"""
    registry_file = Path(__file__).parent / "commands" / system_name / "registry.json"
    if not registry_file.exists():
        return {}

    try:
        with open(registry_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_system_registry(system_name: str, registry: dict):
    """Save registry for a system"""
    registry_file = Path(__file__).parent / "commands" / system_name / "registry.json"
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

        # Build command list with IDs
        commands = []
        for cmd_name, cmd_data in registry.items():
            commands.append({
                'id': cmd_data['id'],
                'name': cmd_name,
                'help': cmd_data.get('help', ''),
                'active': cmd_data.get('active', False),
                'drone_command': cmd_data.get('drone_command', '')
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
            print(f"{'ID':<6}{'Command':<20}{'Active':<10}{'Drone Command'}")
            print(f"{'-'*4}  {'-'*18}  {'-'*8}  {'-'*30}")

            for cmd in commands:
                id_str = f"{cmd['id']:03d}"
                active_str = "YES" if cmd['active'] else "No"
                drone_cmd = cmd['drone_command'] if cmd['drone_command'] else "n/a"
                print(f"{id_str:<6}{cmd['name']:<20}{active_str:<10}{drone_cmd}")

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
            active_file = Path(__file__).parent / "commands" / system_name / "active.json"
            active_data = {}
            for cmd in commands:
                if cmd['active']:
                    active_data[cmd['drone_command']] = {
                        'id': cmd['id'],
                        'command_name': cmd['name'],
                        'description': cmd.get('description', cmd['help']),
                        'module_path': registry[cmd['name']].get('module_path', '')
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
        commands_dir = Path(__file__).parent / "commands"

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

            # Count registered and activated
            total_registered = len(registry)
            total_activated = len([cmd for cmd in registry.values() if cmd.get('active', False)])

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

        output.append(f"{name:<20}{reg:<15}{act:<15}{path}")

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
        commands_dir = Path(__file__).parent / "commands"

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
        commands_dir = Path(__file__).parent / "commands"

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
# MAIN FUNCTIONS
# =============================================

def scan_directory_safely(directory: Path, modules: Dict, max_depth: int = 8):
    """Safely scan directory with depth limit - from prax_logger pattern"""
    if max_depth <= 0:
        return

    try:
        for item in directory.iterdir():
            if should_ignore_path(item):
                continue

            if item.is_file() and item.suffix == '.py':
                logger.info(f"[{MODULE_NAME}] Checking Python file: {item.name}")
                if is_executable_module(item):
                    module_name = item.stem
                    relative_path = item.relative_to(ECOSYSTEM_ROOT)
                    metadata = extract_module_metadata(item)

                    modules[module_name] = {
                        "file_path": str(item),
                        "relative_path": str(relative_path),
                        "discovered_time": datetime.now(timezone.utc).isoformat(),
                        "size": item.stat().st_size,
                        "modified_time": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                        "enabled": True,
                        "executable": True,
                        "metadata": metadata
                    }
                    logger.info(f"[{MODULE_NAME}] Added module: {module_name}")

            elif item.is_dir():
                scan_directory_safely(item, modules, max_depth - 1)

    except PermissionError:
        logger.warning(f"Permission denied accessing {directory}")
    except Exception as e:
        logger.error(f"Error scanning {directory}: {e}")

def discover_aipass_modules() -> Dict[str, Dict[str, any]]:
    """Discover all executable Python modules in the AIPass ecosystem"""
    # Load config and initialize JSON files
    config = load_config()
    discovery_config = config.get("config", {})

    # Check if discovery is enabled
    if not discovery_config.get("enabled", True):
        log_operation("discovery_skipped", True, "Discovery disabled in config")
        return {}

    modules = {}
    log_operation("discovery_started", True, f"Scanning {ECOSYSTEM_ROOT}")
    logger.info(f"[{MODULE_NAME}] Scanning {ECOSYSTEM_ROOT} for executable modules...")

    # Get directories from config
    discovery_directories = discovery_config.get("discovery_directories", [
        "backup_system", "flow", "prax", "tools", "skills", "api", "a.i"
    ])

    aipass_directories = [ECOSYSTEM_ROOT / dirname for dirname in discovery_directories]

    for directory in aipass_directories:
        if directory.exists():
            logger.info(f"[{MODULE_NAME}] Scanning {directory.name}...")
            scan_directory_safely(directory, modules, max_depth=3)
            logger.info(f"[{MODULE_NAME}] Found {len(modules)} modules so far")
        else:
            logger.warning(f"[{MODULE_NAME}] Directory not found: {directory}")

    # Update statistics and data file
    stats = {
        "total_modules_found": len(modules),
        "directories_scanned": len([d for d in aipass_directories if d.exists()]),
        "last_scan": datetime.now(timezone.utc).isoformat(),
        "scan_duration_ms": 0  # Could add timing if needed
    }

    update_data_file(stats)
    log_operation("discovery_completed", True, f"Discovered {len(modules)} executable modules")
    logger.info(f"[{MODULE_NAME}] Discovered {len(modules)} executable modules")
    return modules

def identify_command_modules(modules: Dict) -> Dict[str, Dict[str, any]]:
    """Identify which modules should have drone commands"""
    command_modules = {}

    # Known command-generating modules (checking actual file names)
    known_modules = {
        'backup': {'category': 'backup', 'commands': ['snapshot', 'versioned', 'incremental']},
        'flow_plan': {'category': 'flow', 'commands': ['create', 'close', 'status', 'show']},
        'flow_plan_summarizer': {'category': 'flow', 'commands': ['summarize']},
        'test_cleanup': {'category': 'tools', 'commands': ['cleanup']},
        'prax_logger': {'category': 'prax', 'commands': ['monitor', 'analyze']},
        'create_project_folder': {'category': 'tools', 'commands': ['create_project']},
    }

    for module_name, module_data in modules.items():
        if module_name in known_modules:
            command_modules[module_name] = {
                **module_data,
                'drone_commands': known_modules[module_name]['commands'],
                'command_category': known_modules[module_name]['category']
            }
        elif 'main(' in str(module_data.get('metadata', {})):
            # Auto-detect potential command modules
            command_modules[module_name] = {
                **module_data,
                'drone_commands': ['run'],  # Default command
                'command_category': 'auto-detected'
            }

    return command_modules

def generate_discovery_report(modules: Dict, command_modules: Dict) -> Dict:
    """Generate comprehensive discovery report"""
    report = {
        "discovery_timestamp": datetime.now(timezone.utc).isoformat(),
        "scan_location": str(ECOSYSTEM_ROOT),
        "total_modules_found": len(modules),
        "command_modules_identified": len(command_modules),
        "modules_by_category": {},
        "potential_commands": [],
        "broken_paths": [],
        "recommendations": []
    }

    # Categorize modules
    for module_name, module_data in command_modules.items():
        category = module_data.get('command_category', 'unknown')
        if category not in report["modules_by_category"]:
            report["modules_by_category"][category] = []
        report["modules_by_category"][category].append(module_name)

    # Identify potential commands
    for module_name, module_data in command_modules.items():
        commands = module_data.get('drone_commands', [])
        for cmd in commands:
            report["potential_commands"].append({
                "module": module_name,
                "command": cmd,
                "path": module_data["relative_path"]
            })

    # Check for broken paths (from current drone.py)
    broken_paths = [
        "a.i/seed/seed.py",
        "a.i/legacy/AIPass_Core/a.i_core/a.i_profiles/Nexus/nexus.py",
        "workshop/claude_workspace/projects/0021_code_learning_typing_tutor/src"
    ]

    for path in broken_paths:
        full_path = ECOSYSTEM_ROOT / path
        if not full_path.exists():
            report["broken_paths"].append(path)

    return report

# =============================================
# CLI/EXECUTION
# =============================================

def main():
    """Main discovery function"""
    try:
        logger.info(f"[{MODULE_NAME}] Starting module discovery")

        # Discover all modules
        all_modules = discover_aipass_modules()

        # Identify command modules
        command_modules = identify_command_modules(all_modules)

        # Generate report
        report = generate_discovery_report(all_modules, command_modules)

        # Log results
        logger.info(f"[{MODULE_NAME}] Discovery complete:")
        logger.info(f"  - Total modules: {len(all_modules)}")
        logger.info(f"  - Command modules: {len(command_modules)}")
        logger.info(f"  - Potential commands: {len(report['potential_commands'])}")

        return {
            "all_modules": all_modules,
            "command_modules": command_modules,
            "report": report
        }

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Discovery failed: {e}")
        raise

if __name__ == "__main__":
    result = main()
    print(f"✅ Discovery complete: {result['report']['total_modules_found']} modules found")
    print(f"✅ Command modules: {result['report']['command_modules_identified']}")

    # Debug: Show some discovered modules
    print("\n🔍 Sample discovered modules:")
    for i, (name, data) in enumerate(list(result['all_modules'].items())[:5]):
        print(f"  - {name}: {data['relative_path']}")

    for category, modules in result['report']['modules_by_category'].items():
        print(f"  - {category}: {', '.join(modules)}")

    # Debug: Show potential commands
    if result['report']['potential_commands']:
        print(f"\n📋 Potential commands found:")
        for cmd in result['report']['potential_commands'][:10]:
            print(f"  - {cmd['module']}.{cmd['command']}: {cmd['path']}")
    else:
        print("\n⚠️ No potential commands identified")