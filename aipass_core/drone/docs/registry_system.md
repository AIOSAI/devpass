# Drone Command Registry System

Technical documentation for Drone's command registration and discovery system.

Version: 2.0.0 | Last Updated: 2025-11-29

---

## Overview

The Drone command registry system provides centralized command discovery, registration, and lookup across all AIPass modules. Commands are discovered from each module's command definition files and stored in both module-level registries and a global master registry.

### Key Features

- **Two-tier command storage**: Module-level `registry.json` and `active.json` files plus global master registry
- **Auto-healing**: Automatically repairs missing or corrupted registry structures
- **Global ID assignment**: Unique IDs assigned to every command across the entire system
- **Modular architecture**: Independent handlers for CRUD, registration, lookup, caching, stats, and healing

---

## Directory Structure

```
/home/aipass/aipass_core/drone/
├── commands/                          # Command definitions by module
│   ├── [module_name]/                 # Per-module command directory
│   │   ├── registry.json              # Discovered commands (all commands)
│   │   └── active.json                # Activated commands (subset with descriptions)
│   ├── seed/
│   │   ├── registry.json
│   │   └── active.json
│   ├── flow/
│   │   ├── registry.json
│   │   └── active.json
│   └── ...
├── drone_json/                        # Global registry files
│   ├── drone_registry.json            # Master registry (all modules)
│   ├── drone_registry_config.json     # Registry configuration
│   ├── drone_registry_data.json       # Runtime statistics
│   └── drone_registry_log.json        # Operation logs
└── apps/
    ├── modules/
    │   └── registry.py                # Orchestrator module
    └── handlers/
        └── registry/                  # Implementation handlers
            ├── __init__.py            # Public API exports
            ├── ops.py                 # CRUD operations
            ├── registration.py        # Command registration
            ├── lookup.py              # Command lookup
            ├── cache.py               # Cache management
            ├── stats.py               # Statistics
            └── healing.py             # Auto-healing
```

---

## File Formats

### 1. Module-Level registry.json

**Location**: `/home/aipass/aipass_core/drone/commands/[module_name]/registry.json`

**Purpose**: Stores all discovered commands for a module (discovered state).

**Format**:
```json
{
  "module:command_name": {
    "id": 2,
    "command_name": "architecture",
    "module_name": "seed",
    "help": "",
    "module_path": "/home/aipass/seed/apps/seed.py",
    "registered_date": "2025-11-30T01:14:16.787737+00:00",
    "active": false
  }
}
```

**Fields**:
- `id` (int): Globally unique command ID
- `command_name` (string): Command name without module prefix
- `module_name` (string): Parent module name
- `help` (string): Help text (empty in registry.json, populated in active.json)
- `module_path` (string): Absolute path to module entry point
- `registered_date` (ISO 8601): UTC timestamp of registration
- `active` (boolean): Whether command is activated (always false in registry.json)

**Key Format**: `"module:command"` (e.g., `"seed:architecture"`)

---

### 2. Module-Level active.json

**Location**: `/home/aipass/aipass_core/drone/commands/[module_name]/active.json`

**Purpose**: Stores activated commands with full metadata (active state).

**Format**:
```json
{
  "seed audit": {
    "id": 3,
    "command_name": "audit",
    "description": "Check branch standards compliance",
    "module_path": "/home/aipass/seed/apps/seed.py"
  }
}
```

**Fields**:
- `id` (int): Globally unique command ID (matches registry.json)
- `command_name` (string): Command name without module prefix
- `description` (string): Human-readable command description
- `module_path` (string): Absolute path to module entry point

**Key Format**: `"module command"` (space-separated, e.g., `"seed audit"`)

**Key Differences from registry.json**:
- Key format uses space instead of colon
- Includes `description` field
- Excludes `module_name`, `help`, `registered_date`, `active` fields
- Only contains commands that have been explicitly activated

---

### 3. Global drone_registry.json

**Location**: `/home/aipass/aipass_core/drone/drone_json/drone_registry.json`

**Purpose**: Master registry aggregating all module commands and system metadata.

**Format**:
```json
{
  "version": "1.0.0",
  "created": "2025-11-14T03:17:10.877011+00:00",
  "last_updated": "2025-11-29T22:52:21.589542+00:00",
  "commands": {},
  "modules": {},
  "statistics": {
    "total_commands": 0,
    "total_modules": 0,
    "last_discovery": null,
    "auto_healing_count": 0,
    "total_locations": 0
  },
  "source_files": {
    "registry.json": {
      "last_modified": "2025-11-29T22:47:02.924601+00:00",
      "full_path": "/home/aipass/aipass_core/drone/commands/flow/registry.json",
      "discovered": "auto"
    },
    "active.json": {
      "last_modified": "2025-11-29T22:39:34.834427+00:00",
      "full_path": "/home/aipass/aipass_core/drone/commands/flow/active.json",
      "discovered": "auto"
    }
  },
  "global_id_counter": 88
}
```

**Top-Level Fields**:
- `version` (string): Registry schema version
- `created` (ISO 8601): Initial creation timestamp
- `last_updated` (ISO 8601): Last modification timestamp
- `commands` (object): All registered commands (aggregated from modules)
- `modules` (object): Module metadata
- `statistics` (object): System-wide statistics
- `source_files` (object): Tracking of discovered registry files
- `global_id_counter` (int): Next available unique ID

---

### 4. drone_registry_config.json

**Location**: `/home/aipass/aipass_core/drone/drone_json/drone_registry_config.json`

**Purpose**: Registry system configuration.

**Format**:
```json
{
  "module_name": "drone_registry",
  "timestamp": "2025-11-14T03:17:10.877011+00:00",
  "config": {
    "enabled": true,
    "version": "1.0.0",
    "auto_healing_enabled": true,
    "registry_monitoring": true,
    "cleanup_orphans": true,
    "max_registry_entries": 1000,
    "ignore_modules": [
      "__main__",
      "script",
      "__pycache__",
      "test",
      "temp",
      "backup_old"
    ]
  }
}
```

---

### 5. drone_registry_data.json

**Location**: `/home/aipass/aipass_core/drone/drone_json/drone_registry_data.json`

**Purpose**: Runtime statistics and state tracking.

**Format**:
```json
{
  "last_updated": "2025-11-29T22:52:21.589542+00:00",
  "runtime_state": {
    "registry_active": true,
    "auto_healing": true,
    "monitoring_enabled": true
  },
  "statistics": {
    "total_commands": 68,
    "total_modules": 12,
    "last_load": "2025-11-29T22:52:21.589542+00:00",
    "auto_healing_enabled": true,
    "registry_size_kb": 0
  }
}
```

---

## Global ID Counter System

### Purpose

Assigns globally unique IDs to every command across all modules to enable consistent referencing and prevent ID collisions.

### Implementation

**Storage**: `global_id_counter` field in `/home/aipass/aipass_core/drone/drone_json/drone_registry.json`

**Mechanism**:
1. Counter initialized at 1 when registry is first created
2. Each new command registration increments the counter
3. ID is assigned to the command and counter is persisted
4. Counter never decrements (even if commands are deleted)

**Location**: Managed in `ops.py` through registry load/save operations

**Thread Safety**: Single-threaded operation assumed (no concurrent registry writes)

### Example Flow

```
Initial state: global_id_counter = 1

Register "seed:architecture" → assigns ID 2, counter → 2
Register "seed:audit" → assigns ID 3, counter → 3
Register "seed:checklist" → assigns ID 4, counter → 4
...
Current state: global_id_counter = 88
```

---

## Command Storage and Retrieval

### Registration Flow

1. **Module declares commands** in its handler or module file
2. **Registration handler** calls `register_module_commands(commands, module_name)`
3. **Registry loads** from `drone_registry.json`
4. **ID assignment** from global_id_counter
5. **Registry saves** updated data back to `drone_registry.json`
6. **Module files updated** in `commands/[module_name]/registry.json`

### Lookup Flow

1. **Caller requests** command via `get_command(command_path)`
2. **Registry loads** from `drone_registry.json` (with auto-healing)
3. **Lookup handler** searches in `commands` dict
4. **Returns** command metadata or None

### Cache Management

Commands can be cached for performance. Cache handlers provide:
- `mark_dirty()`: Invalidate cache
- `mark_clean()`: Validate cache
- `get_cached_commands()`: Retrieve from cache

---

## Key Functions

### Core Operations (`ops.py`)

```python
load_registry() -> Dict
```
Load master registry with auto-healing. Creates new registry if missing.

```python
save_registry(registry: Dict) -> bool
```
Save registry with validation. Updates timestamp and validates structure.

```python
create_empty_registry() -> Dict
```
Create new registry with proper structure and default values.

```python
validate_registry_structure(registry: Dict) -> bool
```
Verify registry has required keys: commands, modules, last_updated, version.

```python
should_ignore_module(module_name: str) -> bool
```
Check if module is in ignore list (e.g., `__pycache__`, `test`, `temp`).

---

### Registration (`registration.py`)

```python
register_module_commands(commands: Dict, module_name: str = None) -> bool
```
Register commands for a module. Auto-detects module name if not provided.

**Parameters**:
- `commands`: Dict of command definitions
- `module_name`: Optional module name (auto-detected from call stack if None)

**Returns**: True if successful

---

### Lookup (`lookup.py`)

```python
get_command(command_path: str) -> Optional[Dict]
```
Get command by path (e.g., 'flow:create', 'seed:audit').

```python
get_module_commands(module_name: str) -> Dict
```
Get all commands for a specific module.

```python
get_all_commands() -> Dict
```
Get all registered commands across all modules.

```python
get_all_modules() -> Dict
```
Get all registered modules with metadata.

---

### Statistics (`stats.py`)

```python
get_registry_statistics() -> Dict
```
Get comprehensive registry statistics.

```python
get_command_count() -> int
```
Get total number of registered commands.

```python
get_module_count() -> int
```
Get total number of registered modules.

```python
get_module_stats(module_name: str) -> Dict
```
Get statistics for a specific module.

---

### Healing (`healing.py`)

```python
heal_registry() -> bool
```
Auto-heal registry structure. Repairs missing keys, validates structure, updates statistics.

**Returns**: True if healing was performed

---

### Cache (`cache.py`)

```python
mark_dirty()
```
Invalidate command cache.

```python
mark_clean()
```
Validate command cache.

```python
get_cached_commands() -> Dict
```
Retrieve commands from cache if valid.

```python
register_command_location(command_path: str, file_path: str)
```
Register physical file location for a command.

```python
update_registry_on_change(file_path: str)
```
Update registry when a command file changes.

---

## Ignored Modules

The following modules are excluded from registry:

```python
IGNORED_MODULES = {
    "__main__",
    "script",
    "update_package_json",
    "validate_packages",
    "update_ext_version",
    "__pycache__",
    "test",
    "temp",
    "backup_old",
    "drone_discovery",
    "drone_registry",
    "drone_loader"
}
```

**Defined in**: `/home/aipass/aipass_core/drone/apps/handlers/registry/ops.py`

---

## Usage Examples

### Import and Load Registry

```python
from drone.apps.handlers.registry import load_registry, get_command

# Load registry (auto-heals if needed)
registry = load_registry()
print(f"Commands: {len(registry['commands'])}")
print(f"Modules: {len(registry['modules'])}")
```

### Register Commands

```python
from drone.apps.handlers.registry import register_module_commands

commands = {
    "scan": {
        "path": "/home/aipass/aipass_core/drone/apps/drone.py",
        "args": [],
        "description": "Scan for commands"
    },
    "load": {
        "path": "/home/aipass/aipass_core/drone/apps/drone.py",
        "args": [],
        "description": "Load command"
    }
}

# With explicit module name
register_module_commands(commands, "drone")

# Or with auto-detection
register_module_commands(commands)
```

### Lookup Commands

```python
from drone.apps.handlers.registry import get_command, get_module_commands

# Get specific command
cmd = get_command("seed:audit")
if cmd:
    print(f"Description: {cmd['description']}")
    print(f"Path: {cmd['module_path']}")

# Get all commands for a module
seed_commands = get_module_commands("seed")
for cmd_name, cmd_data in seed_commands.items():
    print(f"{cmd_name}: {cmd_data['description']}")
```

### Get Statistics

```python
from drone.apps.handlers.registry import (
    get_registry_statistics,
    get_command_count,
    get_module_count
)

stats = get_registry_statistics()
print(f"Total commands: {get_command_count()}")
print(f"Total modules: {get_module_count()}")
print(f"Auto-healing count: {stats['auto_healing_count']}")
```

---

## Architecture Notes

### Handler Independence

All handlers are designed for independence:
- No cross-handler imports (except within registry package)
- No CLI output (pure implementation)
- No orchestration (handlers don't call modules)
- Type hints on all functions

### Dependency Injection

Handlers use dependency injection via `ops.py`:
- `load_registry()` and `save_registry()` centralize registry access
- Other handlers import from `ops.py` for consistency
- Enables testing and modularity

### Auto-Healing

Registry automatically heals on load:
1. Validates structure
2. Adds missing required keys
3. Sets default values
4. Increments healing counter
5. Logs healing operations

### Logging

Operations are logged to:
- **Prax system logger**: System-wide event logging
- **drone_registry_log.json**: Registry-specific operation log (last 1000 entries)

---

## File Locations Reference

| File | Path |
|------|------|
| Master Registry | `/home/aipass/aipass_core/drone/drone_json/drone_registry.json` |
| Registry Config | `/home/aipass/aipass_core/drone/drone_json/drone_registry_config.json` |
| Registry Data | `/home/aipass/aipass_core/drone/drone_json/drone_registry_data.json` |
| Registry Log | `/home/aipass/aipass_core/drone/drone_json/drone_registry_log.json` |
| Module Commands | `/home/aipass/aipass_core/drone/commands/[module]/registry.json` |
| Active Commands | `/home/aipass/aipass_core/drone/commands/[module]/active.json` |
| Orchestrator | `/home/aipass/aipass_core/drone/apps/modules/registry.py` |
| Handlers | `/home/aipass/aipass_core/drone/apps/handlers/registry/*.py` |

---

## Version History

- **v2.0.0** (2025-11-13): PILOT MIGRATION - Modular handler architecture
- **v1.0.0** (2025-11-07): Initial registry system with basic CRUD operations

---

*Code is truth. Systems speak through behavior.*
