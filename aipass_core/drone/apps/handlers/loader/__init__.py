"""
Drone Loader Handlers Package

Provides command loading handlers for drone command discovery,
validation, and tree building.

Public API:
    # File Discovery
    from drone.apps.handlers.loader import discover_command_files

    # JSON Loading
    from drone.apps.handlers.loader import load_json_commands, extract_commands_from_json

    # Path Validation
    from drone.apps.handlers.loader import validate_command_path, resolve_command_path

    # Command Validation
    from drone.apps.handlers.loader import validate_command_data

    # Command Building
    from drone.apps.handlers.loader import flatten_nested_commands, merge_command_sources

Version: 2.0.0 (MIGRATION - 2025-11-13)
"""

# File Discovery
from .file_discovery import (
    discover_command_files,
    scan_commands_directory,
    scan_registry_sources
)

# JSON Loading
from .json_loading import (
    load_json_commands,
    extract_commands_from_json,
    parse_command_structure
)

# Path Validation
from .path_validation import (
    validate_command_path,
    resolve_command_path,
    check_system_command,
    check_file_exists
)

# Command Validation
from .command_validation import (
    validate_command_data,
    validate_required_fields,
    validate_command_structure
)

# Command Building
from .command_builder import (
    flatten_nested_commands,
    build_flat_command_dict,
    merge_command_sources
)

__all__ = [
    # File Discovery
    'discover_command_files',
    'scan_commands_directory',
    'scan_registry_sources',
    # JSON Loading
    'load_json_commands',
    'extract_commands_from_json',
    'parse_command_structure',
    # Path Validation
    'validate_command_path',
    'resolve_command_path',
    'check_system_command',
    'check_file_exists',
    # Command Validation
    'validate_command_data',
    'validate_required_fields',
    'validate_command_structure',
    # Command Building
    'flatten_nested_commands',
    'build_flat_command_dict',
    'merge_command_sources',
]
