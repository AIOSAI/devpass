#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: __init__.py - Discovery Handlers Package
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/discovery
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): BEAST MIGRATION - Package created from drone_discovery.py (2,289 lines)
# =============================================

"""
Discovery Handlers Package

Runtime command discovery system for the AIPass drone orchestrator. Discovers Python
modules with CLI interfaces, registers their commands, and manages activation state.

Public API:
    from drone.apps.handlers.discovery import scan_module, register_module, activate_commands_interactive

Handlers:
- module_scanning: Runtime discovery, path resolution, module scanning
- command_parsing: Command registration, global ID management
- activation: Interactive activation workflow, duplicate prevention
- system_operations: List, edit, remove, refresh operations
- formatters: Output formatting for all operations
- help_display: Help text display for systems and modules
"""

# =============================================
# MODULE SCANNING EXPORTS
# =============================================

from .module_scanning import (
    detect_module_type,
    discover_commands_runtime,
    resolve_scan_path,
    resolve_system_name,
    scan_module
)

# =============================================
# COMMAND PARSING EXPORTS
# =============================================

from .command_parsing import (
    get_next_global_id,
    increment_global_id,
    load_system_registry,
    save_system_registry,
    register_module
)

# =============================================
# ACTIVATION EXPORTS
# =============================================

from .activation import (
    lookup_activated_command,
    activate_commands_interactive
)

# =============================================
# SYSTEM OPERATIONS EXPORTS
# =============================================

from .system_operations import (
    list_all_systems,
    list_activated_commands,
    remove_activated_command,
    refresh_system,
    edit_activated_command_interactive,
    run_branch_module,
    resolve_slash_pattern,
    is_long_running_command
)

# =============================================
# FORMATTER EXPORTS
# =============================================

from .formatters import (
    format_scan_output,
    format_registration_output,
    format_activation_summary,
    format_systems_output,
    format_list_output,
    format_remove_output,
    format_refresh_output,
    format_edit_output
)

# =============================================
# HELP DISPLAY EXPORTS
# =============================================

from .help_display import (
    show_help_for_target
)

# =============================================
# PUBLIC API
# =============================================

__all__ = [
    # Module scanning
    'detect_module_type',
    'discover_commands_runtime',
    'resolve_scan_path',
    'resolve_system_name',
    'scan_module',

    # Command parsing
    'get_next_global_id',
    'increment_global_id',
    'load_system_registry',
    'save_system_registry',
    'register_module',

    # Activation
    'lookup_activated_command',
    'activate_commands_interactive',

    # System operations
    'list_all_systems',
    'list_activated_commands',
    'remove_activated_command',
    'refresh_system',
    'edit_activated_command_interactive',
    'run_branch_module',
    'resolve_slash_pattern',
    'is_long_running_command',

    # Formatters
    'format_scan_output',
    'format_registration_output',
    'format_activation_summary',
    'format_systems_output',
    'format_list_output',
    'format_remove_output',
    'format_refresh_output',
    'format_edit_output',

    # Help display
    'show_help_for_target'
]
