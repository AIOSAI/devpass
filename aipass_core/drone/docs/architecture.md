# Drone Architecture

**Branch:** DRONE
**Created:** 2025-11-29
**Updated:** 2025-11-29

---

## Overview

Drone is AIPass's command router and discovery system. It operates as a thin orchestrator that discovers, routes, and executes commands across all branches in the AIPass ecosystem. Drone's architecture follows the universal 3-layer pattern: entry point → modules → handlers.

The core responsibility of Drone is to:
- Route commands to appropriate branches using `@` prefix resolution
- Discover and register available commands from branches
- Manage activated command shortcuts
- Provide unified command execution with timeout management

---

## 3-Layer Pattern

Drone implements the standard AIPass architecture with strict separation of concerns:

### Layer 1: Entry Point (`apps/drone.py`)

**Responsibility:** Command parsing, help display, high-level routing logic

The entry point is the thin orchestrator that:
- Parses command-line arguments
- Displays help and introspection when requested
- Routes to appropriate modules based on command type
- Handles special patterns (`@branch`, `@branch/module`, `branch/module`)
- Never contains business logic

**Key Functions:**
- `main()` - Primary entry point, delegates all routing
- `show_help()` - Inline help display (Seed pattern compliance)
- `show_introspection()` - Module discovery display when run without args

**Import Pattern:**
```python
# Routing logic from modules layer
from drone.apps.modules.routing import (
    preprocess_args,
    discover_modules,
    route_command,
)

# Discovery logic from modules layer
from drone.apps.modules.discovery import (
    resolve_scan_path,
    run_branch_module,
    resolve_slash_pattern,
    is_long_running_command,
)
```

### Layer 2: Modules (`apps/modules/`)

**Responsibility:** Orchestration and public API

Modules coordinate handlers and provide the public interface for other branches. This layer:
- Re-exports handler functions for external use
- Provides high-level orchestration of complex operations
- Maintains the public API contract
- Contains NO implementation details

**Key Modules:**
- `routing.py` - Command routing orchestration
- `discovery.py` - Command discovery orchestration
- `paths.py` - Path resolution services (re-exports from handlers)
- `branch_registry.py` - Branch metadata services (re-exports from handlers)

**Public API Pattern (`modules/__init__.py`):**
```python
# High-level API for @ resolution
from .paths import resolve
from .branch_registry import get_all_branches

# resolve("@flow") → full branch metadata
# resolve("@all") → list of all branches
```

### Layer 3: Handlers (`apps/handlers/`)

**Responsibility:** Implementation details and business logic

Handlers contain all actual implementation:
- Path resolution algorithms
- Command discovery logic
- Registry operations
- JSON file manipulation
- Subprocess execution

**Security:** Handlers are protected by import guards. Cross-branch imports are blocked:

```python
# handlers/__init__.py
def _guard_branch_access():
    """Block cross-branch handler imports"""
    # Only drone/ can import drone/apps/handlers/
    # External branches must use drone.apps.modules
```

**Key Handler Directories:**
- `handlers/routing/` - Command routing implementation
- `handlers/discovery/` - Command scanning and registration
- `handlers/paths/` - @ prefix resolution logic
- `handlers/branch_registry/` - Registry.json operations
- `handlers/json/` - JSON tracking (drone.local.json)

---

## Command Flow

### 1. Direct Branch Access (`@` Pattern)

**Example:** `drone @flow create "My task"`

```
drone.py (entry point)
    ↓
    Detects @ prefix
    ↓
modules/discovery.resolve_scan_path()
    ↓
handlers/paths/ - Resolves @flow → /home/aipass/aipass_core/flow/
    ↓
modules/discovery.run_branch_module()
    ↓
handlers/discovery/ - Executes flow.py with preprocessed args
    ↓
    Subprocess: python3 /home/aipass/aipass_core/flow/apps/flow.py create "My task"
```

**Features:**
- Automatic path resolution via `resolve_scan_path()`
- Argument preprocessing (nested @ resolution)
- Timeout management (30s default, None for long-running)
- Error handling with user-friendly messages

### 2. Branch/Module Pattern (`@branch/module`)

**Example:** `drone @seed/imports`

```
drone.py (entry point)
    ↓
    Detects @seed/imports pattern
    ↓
modules/discovery.resolve_slash_pattern()
    ↓
handlers/discovery/ - Resolves @seed/imports → imports_standard module
    ↓
    Executes: python3 /home/aipass/seed/apps/modules/imports.py
```

### 3. Activated Commands (Shortcuts)

**Example:** `drone plan list` → routes to `@flow list`

```
drone.py (entry point)
    ↓
    Command "plan" not recognized as @ pattern
    ↓
modules/routing.discover_modules()
    ↓
handlers/routing/ - Discovers internal drone modules
    ↓
modules/routing.route_command()
    ↓
    Matches "plan" against activated_commands.json
    ↓
    Resolves to: drone @flow list
    ↓
    Executes flow command
```

**Activation Flow:**
```
1. Scan:     drone scan @flow
2. Register: Automatically registers commands to registry.json
3. Activate: Prompts user to create shortcuts
4. Use:      drone plan list
```

### 4. Internal Drone Commands

**Example:** `drone systems`, `drone scan @branch`

```
drone.py (entry point)
    ↓
modules/routing.discover_modules()
    ↓
handlers/loader/ - Discovers modules in apps/modules/
    ↓
modules/routing.route_command()
    ↓
    Matches command to discovered module
    ↓
    Calls module.handle_command()
    ↓
handlers/discovery/ or handlers/registry/ - Executes logic
```

---

## Directory Structure

```
drone/
├── apps/
│   ├── drone.py              # Entry point (thin orchestrator)
│   ├── modules/              # Layer 2: Orchestration & Public API
│   │   ├── __init__.py       # Public API exports
│   │   ├── routing.py        # Routing orchestration
│   │   ├── discovery.py      # Discovery orchestration
│   │   ├── paths.py          # Path services (re-exports)
│   │   └── branch_registry.py # Registry services (re-exports)
│   ├── handlers/             # Layer 3: Implementation
│   │   ├── __init__.py       # Import guard protection
│   │   ├── routing/          # Command routing logic
│   │   ├── discovery/        # Command scanning logic
│   │   ├── paths/            # @ resolution implementation
│   │   ├── branch_registry/  # Registry operations
│   │   ├── json/             # JSON tracking
│   │   └── display/          # Formatted output
│   └── json_templates/       # JSON structure templates
├── docs/
│   └── architecture.md       # This file
├── DRONE.id.json             # Identity
├── DRONE.local.json          # Session tracking
└── README.md                 # Branch documentation
```

---

## Key Principles

### 1. Handler Independence

**Handlers are internal to their branch.** Cross-branch imports are blocked by import guards.

**Wrong:**
```python
# In flow/apps/modules/planner.py
from drone.apps.handlers.paths import resolve_at_prefix  # BLOCKED!
```

**Right:**
```python
# In flow/apps/modules/planner.py
from drone.apps.modules import resolve  # Public API
```

This enforces:
- **API stability** - Modules are the contract, handlers can refactor freely
- **Encapsulation** - Implementation details stay internal
- **Clear boundaries** - Each branch owns its handlers

### 2. Module Orchestration

Modules coordinate handlers but contain no business logic:

```python
# modules/discovery.py
def handle_command(command: str, args: list) -> bool:
    """Orchestrate discovery handlers"""

    if command == "scan":
        # Delegate to handler
        result = scan_module(args[0])
        # Format output
        format_scan_output(result)
        return True

    return False
```

### 3. Thin Entry Point

`drone.py` routes but doesn't implement:

```python
# drone.py
if command.startswith('@'):
    # Delegate to module
    module_path = resolve_scan_path(command)
    run_branch_module(module_path, remaining_args)
    return
```

### 4. Argument Preprocessing

Drone resolves nested `@` patterns before passing to branches:

```
Input:  drone @flow create @seed "My task"
        ↓
Preprocess: @seed → /home/aipass/seed
        ↓
Execute: flow.py create /home/aipass/seed "My task"
```

This allows branches to receive absolute paths instead of handling `@` resolution themselves.

### 5. Timeout Management

Drone detects long-running commands and disables timeout:

```python
# Long-running patterns: monitor, watch, serve, listen, tail
if is_long_running_command(args):
    timeout = None  # No timeout
else:
    timeout = 30  # 30 second default
```

---

## Integration Points

### For Branch Developers

**Using Drone services in your branch:**

```python
# Get branch paths
from drone.apps.modules import resolve

branch = resolve("@flow")
# → {'name': 'flow', 'path': Path(...), 'email': 'flow@aipass', ...}

all_branches = resolve("@all")
# → List of all branch metadata
```

**Making your branch discoverable:**

1. Implement `handle_command()` in your module
2. Scan: `drone scan @yourbranch`
3. Register: Automatically happens during scan
4. Activate: Follow prompt to create shortcuts

### For System Operations

**Drone tracks operations in `DRONE.local.json`:**

```json
{
  "operations": [
    {
      "timestamp": "2025-11-29T18:00:00",
      "operation": "drone_at_command",
      "data": {"target": "@flow", "args": ["list"]}
    }
  ]
}
```

**Performance data available in `handlers/perf/`**

---

*Part of DRONE branch documentation*
