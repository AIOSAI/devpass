#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: loader.py - Command Loader Module
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/modules
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2025-11-13): MIGRATION - Orchestrator from drone_loader.py
#   - v1.0.0 (2025-09-22): Original implementation
#
# CODE STANDARDS:
#   - Orchestrator pattern - coordinates handlers from drone/apps/handlers/loader/ and registry/
#   - Type hints on all functions
#   - Google-style docstrings
#   - Prax logger (system_logger as logger)
#   - CLI module for output (Rich console)
#   - Standard try/except error handling
#   - 3-file JSON pattern for state management (config, data, log)
# =============================================

"""
Drone Command Loader Module

Orchestrates command loading from JSON files and builds command tree.

Features:
- Command discovery and loading
- Command validation
- Tree building and caching
- Registry integration

Usage:
    from drone.apps.modules.loader import get_command_tree

    commands = get_command_tree()
    for name, data in commands.items():
        # logger.info(f"{name}: {data['path']}")
"""

# =============================================
# IMPORTS
# =============================================

import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from prax.apps.modules.logger import system_logger as logger

# Import CLI modules
from cli.apps.modules import console, header

# Import handlers
from drone.apps.handlers.loader import (
    discover_command_files,
    load_json_commands,
    extract_commands_from_json,
    validate_command_data,
    validate_command_path,
    resolve_command_path
)

# Import registry handlers
from drone.apps.handlers.registry import (
    load_registry,
    save_registry,
    get_cached_commands,
    mark_clean,
    mark_dirty
)

# Import JSON handler
from drone.apps.handlers.json import json_handler

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "drone_loader"
ECOSYSTEM_ROOT = Path.home()
DRONE_JSON_DIR = AIPASS_ROOT / "drone" / "drone_json"
COMMANDS_DIR = AIPASS_ROOT / "drone" / "commands"

# 3-File JSON Pattern
CONFIG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_log.json"

# =============================================
# JSON FILE MANAGEMENT (3-FILE PATTERN)
# =============================================

def load_config():
    """Load configuration from JSON."""
    config = json_handler.load_json(MODULE_NAME, "config")
    if config is None:
        return {"config": {"enabled": True}}
    return config


def update_data_file(stats):
    """Update data file with new stats."""
    try:
        return json_handler.update_data_metrics(
            MODULE_NAME,
            statistics=stats,
            runtime_state={"last_update": datetime.now().isoformat()}
        )
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error updating data file: {e}")
        return False


def log_operation_local(operation: str, success: bool, details: str = "", error: str = ""):
    """Log operation to local log file."""
    log_data = {
        "success": success,
        "details": details,
        "error": error
    }
    try:
        return json_handler.log_operation(operation, log_data, MODULE_NAME)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error logging operation: {e}")
        return False

# =============================================
# ORCHESTRATION FUNCTIONS
# =============================================

def build_command_tree() -> Dict:
    """Build complete command tree from all sources

    Orchestrates the command loading workflow:
    1. Discover command files
    2. Load and parse each file
    3. Validate commands
    4. Update registry
    5. Return command tree

    Returns:
        Dictionary of command_name -> command_data
    """
    # Load config
    config = load_config()
    loader_config = config.get("config", {})

    if not isinstance(loader_config, dict):
        loader_config = {}

    if not loader_config.get("enabled", True):
        log_operation_local("loading_skipped", True, "Loading disabled in config")
        return {}

    log_operation_local("tree_building_started", True, "Building command tree")
    logger.info(f"[{MODULE_NAME}] Building command tree...")

    # Discover command files
    command_files = discover_command_files()
    logger.info(f"[{MODULE_NAME}] Discovered {len(command_files)} command files")

    # Load and validate commands
    command_tree = {}
    for json_file in command_files:
        file_commands = load_json_commands(json_file)

        # Extract commands from JSON structure
        commands_data = extract_commands_from_json(file_commands)

        # Validate and add each command
        for cmd_name, cmd_data in commands_data.items():
            if validate_command_data(cmd_data):
                command_tree[cmd_name] = cmd_data
                logger.info(f"[{MODULE_NAME}] Added command: {cmd_name}")
            else:
                logger.warning(f"[{MODULE_NAME}] Invalid command data for: {cmd_name}")

    # Update registry
    registry = load_registry()
    registry["commands"] = command_tree
    registry["source_files"] = {}

    # Track source files
    for json_file in command_files:
        file_name = Path(json_file).name
        file_mtime = os.path.getmtime(json_file)
        file_modified = datetime.fromtimestamp(file_mtime, timezone.utc)
        registry["source_files"][file_name] = {
            "last_modified": file_modified.isoformat(),
            "full_path": str(json_file),
            "discovered": "auto"
        }

    # Update statistics
    registry["statistics"]["total_commands"] = len(command_tree)
    registry["statistics"]["total_locations"] = len(registry.get("scan_locations", []))
    save_registry(registry)

    # Update local statistics
    stats = {
        "total_commands_loaded": len(command_tree),
        "source_files_processed": len(command_files),
        "last_build": datetime.now(timezone.utc).isoformat(),
        "validation_enabled": loader_config.get("validation_enabled", True),
        "build_duration_ms": 0
    }

    update_data_file(stats)
    log_operation_local("tree_building_completed", True, f"Built command tree with {len(command_tree)} commands")

    logger.info(f"[{MODULE_NAME}] Command tree built: {len(command_tree)} commands")
    return command_tree


def get_command_tree() -> Dict:
    """Get current command tree (cached or rebuild)

    Uses reactive pattern - checks cache first, rebuilds if dirty.

    Returns:
        Dictionary of commands
    """
    try:
        # Check cache first
        cached_commands = get_cached_commands()
        if cached_commands is not None:
            log_operation_local("cache_hit", True, f"Using cached commands: {len(cached_commands)}")
            logger.info(f"[{MODULE_NAME}] Using cached commands: {len(cached_commands)}")
            return cached_commands

        # Cache miss - rebuild
        log_operation_local("cache_miss", True, "Registry dirty, rebuilding commands")
        logger.info(f"[{MODULE_NAME}] Registry dirty - rebuilding command tree")

        command_tree = build_command_tree()

        # Mark registry clean
        mark_clean()
        log_operation_local("rebuild_complete", True, f"Command tree rebuilt: {len(command_tree)} commands")
        logger.info(f"[{MODULE_NAME}] Command tree rebuilt and registry marked clean")

        return command_tree

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get command tree: {e}")
        log_operation_local("get_tree_failed", False, f"Failed to get command tree: {e}", str(e))
        return {}


def resolve_command(command_path: str) -> Optional[Dict]:
    """Resolve a command by path

    Args:
        command_path: Command name (e.g., 'run_seed')

    Returns:
        Command data dictionary or None
    """
    try:
        command_tree = get_command_tree()
        return command_tree.get(command_path)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to resolve command {command_path}: {e}")
        return None


def get_available_commands() -> List[str]:
    """Get list of all available commands

    Returns:
        List of command names
    """
    try:
        command_tree = get_command_tree()
        return list(command_tree.keys())
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to get available commands: {e}")
        return []

# =============================================
# CLI/EXECUTION
# =============================================

def print_introspection():
    """Display module info and connected handlers"""
    console.print()
    console.print("[bold cyan]Loader Module - Command Loading & Tree Building[/bold cyan]")
    console.print()

    console.print("[yellow]Connected Handlers:[/yellow]")
    console.print()

    # Auto-discover from multiple domains
    domains = ["loader", "registry"]
    for domain in domains:
        handlers_dir = Path(__file__).parent.parent / "handlers" / domain
        if handlers_dir.exists():
            console.print(f"  [cyan]handlers/{domain}/[/cyan]")
            handler_files = sorted([
                f.name for f in handlers_dir.glob("*.py")
                if not f.name.startswith("_")
            ])
            for handler_file in handler_files:
                console.print(f"    [dim]- {handler_file}[/dim]")
            console.print()

    console.print("[dim]Run 'python3 loader.py --help' for usage information[/dim]")
    console.print()


def main():
    """Main loader function for testing"""
    import sys

    # Check for introspection flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--introspect', '-i', '--info']:
        print_introspection()
        return {}

    try:
        logger.info(f"[{MODULE_NAME}] Testing command loader...")

        # Build command tree
        command_tree = build_command_tree()

        # Show results
        logger.info(f"[{MODULE_NAME}] Command tree test complete:")
        logger.info(f"  - Total commands: {len(command_tree)}")

        # Show some commands
        for i, (cmd_name, cmd_data) in enumerate(list(command_tree.items())[:5]):
            logger.info(f"  - {cmd_name}: {cmd_data.get('path', 'No path')}")

        return command_tree

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Loader test failed: {e}")
        raise


def print_help():
    """Display loader help using Rich formatting"""
    console.print()
    console.print("[bold cyan]Drone Command Loader Module[/bold cyan]")
    console.print()
    console.print("Orchestrates command loading from JSON files and builds command tree.")
    console.print()
    console.print("[yellow]Commands:[/yellow] load, loader, --help")
    console.print()
    console.print("[yellow]Usage:[/yellow]")
    console.print("  drone load")
    console.print("  python3 loader.py")
    console.print("  python3 loader.py --help")
    console.print()
    console.print("[yellow]Features:[/yellow]")
    console.print("  • Discovers command files from drone_json/")
    console.print("  • Validates command structure")
    console.print("  • Builds complete command tree")
    console.print("  • Caches results for performance")
    console.print("  • Integrates with registry")
    console.print()


def handle_command(command: str, args: list) -> bool:
    """Handle loader commands

    Args:
        command: Command name
        args: Command arguments

    Returns:
        True if command was handled
    """
    # Loader only handles 'load' command
    if command != "load":
        return False

    # Check for help flag
    if len(args) > 0 and args[0] in ['--help', '-h', 'help']:
        print_help()
        return True

    result = main()
    console.print(f"✅ Command loader: {len(result)} commands loaded")
    return True


if __name__ == "__main__":
    import sys

    # Show introspection when run without arguments
    if len(sys.argv) == 1:
        print_introspection()
    # Show help for help flags
    elif sys.argv[1] in ['--help', '-h', 'help']:
        console.print()
        console.print("[bold cyan]Loader Module - Command Loading & Tree Building[/bold cyan]")
        console.print()
        console.print("Builds command tree from all activated drone commands")
        console.print()
        console.print("[yellow]Commands:[/yellow] load, loader, --help")
        console.print()
        console.print("[yellow]Usage:[/yellow]")
        console.print("  drone load")
        console.print("  python3 loader.py")
        console.print("  python3 loader.py --help")
        console.print()
        console.print("[yellow]Description:[/yellow]")
        console.print("  Scans all active.json files and builds command tree")
        console.print("  Shows command count and sample commands")
        console.print()
    # Run test for other arguments
    else:
        result = main()
        console.print(f"✅ Command loader test: {len(result)} commands loaded")
        for cmd_name in list(result.keys())[:10]:
            console.print(f"  - {cmd_name}")
