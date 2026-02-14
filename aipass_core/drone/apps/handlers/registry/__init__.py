"""
Drone Registry Handlers Package

Provides registry management handlers for drone command registration,
lookup, caching, statistics, and auto-healing.

Public API:
    # Core Operations
    from drone.apps.handlers.registry import load_registry, save_registry

    # Registration
    from drone.apps.handlers.registry import register_module_commands

    # Lookup
    from drone.apps.handlers.registry import get_command, get_module_commands

    # Caching
    from drone.apps.handlers.registry import mark_dirty, mark_clean, get_cached_commands

    # Statistics
    from drone.apps.handlers.registry import get_registry_statistics, get_command_count

    # Healing
    from drone.apps.handlers.registry import heal_registry

Version: 2.0.0 (PILOT MIGRATION - 2025-11-13)
"""

# Core CRUD operations
from .ops import (
    load_registry,
    save_registry,
    create_empty_registry,
    validate_registry_structure,
    should_ignore_module
)

# Registration operations
from .registration import (
    register_module_commands
)

# Lookup operations
from .lookup import (
    get_command,
    get_module_commands,
    get_all_commands,
    get_all_modules
)

# Cache operations
from .cache import (
    mark_dirty,
    mark_clean,
    get_cached_commands,
    register_command_location,
    update_registry_on_change
)

# Statistics operations
from .stats import (
    get_registry_statistics,
    get_command_count,
    get_module_count,
    get_module_stats
)

# Healing operations
from .healing import (
    heal_registry
)

__all__ = [
    # Core ops
    'load_registry',
    'save_registry',
    'create_empty_registry',
    'validate_registry_structure',
    'should_ignore_module',
    # Registration
    'register_module_commands',
    # Lookup
    'get_command',
    'get_module_commands',
    'get_all_commands',
    'get_all_modules',
    # Cache
    'mark_dirty',
    'mark_clean',
    'get_cached_commands',
    'register_command_location',
    'update_registry_on_change',
    # Stats
    'get_registry_statistics',
    'get_command_count',
    'get_module_count',
    'get_module_stats',
    # Healing
    'heal_registry',
]
