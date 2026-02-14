# DRONE - Command Routing & Module Discovery System

## Overview

**Branch**: DRONE
**Location**: `/home/aipass/aipass_core/drone`
**Purpose**: Command orchestration and module discovery for the AIPass ecosystem
**Created**: 2025-11-13
**Last Updated**: 2026-02-14

## Architecture

- **Pattern**: Modular (3-layer: entry point -> modules -> handlers)
- **Structure**: `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator**: `apps/drone.py` - auto-discovers and routes to modules
- **Module Interface**: All modules implement `handle_command(command, args) -> bool`
- **Cross-Branch Guard**: Handler `__init__.py` files prevent external imports

## Core Functions

### What DRONE Does
- Routes commands to appropriate branches and modules (supports N-word commands)
- **Centralized @ argument resolution** - resolves `@branch` to full paths before passing to modules
- Discovers and registers available commands across all branches
- Auto-registers commands during scan (streamlined workflow)
- Manages command activation/deactivation (merges, doesn't overwrite)
- Executes branch modules via `run_branch_module()` with intelligent timeout detection
- Push-based error reporting to Trigger's error registry on command failures
- Routes to The Commons social network via `drone commons` shortcut
- Professional CLI formatting with Rich panels

### What DRONE Doesn't Do
- Execute branch-specific logic (delegates to branches)
- Store application data (branches handle their own data)
- Manage workflows (FLOW handles that)
- Handle messaging (AI_MAIL handles that)

## Commands

```bash
# Help & discovery
drone help                      # Comprehensive usage guide
drone systems                   # Show all registered systems with stats
drone scan @branch              # Scan module for commands (auto-registers)
drone scan @branch --all        # Also show Python commands (for testing)

# Activation & management
drone activate <system>         # Activate commands interactively
drone list                      # List all activated commands
drone list @branch              # List activated commands for specific system
drone edit                      # Edit activated command interactively
drone remove <drone_command>    # Remove activated command
drone refresh @branch           # Re-scan system for changes

# Command routing (supports N-word commands)
drone <command> [args]          # Route to activated command
drone @branch command [args]    # Direct branch access

# The Commons
drone commons feed              # View community feed
drone commons thread <id>       # Read a conversation
drone commons post "room" "Title" "Content"  # Share something

# Direct Python execution (path resolution)
drone run python3 <module> [args]  # Resolves module path automatically
drone run python3 flow.py list     # -> ~/aipass_core/flow/apps/flow.py list

# Examples
drone scan @prax                # Scan prax, register, prompt to activate
drone list @flow                # Show only flow commands
drone prax file watcher start   # N-word command support
drone seed audit @flow          # @ resolved to path, passed to seed
drone @ai_mail send @drone "Subject" "Message"
```

## @ Argument Resolution

DRONE provides **centralized @ argument resolution** via `preprocess_args()`.

### How It Works
1. All `@branch` arguments are resolved to full paths BEFORE passing to modules
2. Works for both direct commands (`drone @flow create`) AND activated shortcuts (`drone plan create @seed`)
3. Branches receive clean paths (e.g., `/home/aipass/aipass_core/flow`)
4. Branches adapt to handle paths using normalization functions

### Reserved @ Targets
| Target | Resolves To |
|--------|-------------|
| `@flow` | `/home/aipass/aipass_core/flow` |
| `@seed` | `/home/aipass/seed` |
| `@all` | Passed as-is (special handling in branches) |
| `@` | `/home/aipass` (root) |
| `@branch/path` | Nested paths supported |

### Branch Adaptation Pattern
Branches receiving resolved paths use `normalize_branch_arg()` from drone's branch_registry module:
```python
from drone.apps.modules.branch_registry import normalize_branch_arg

# Converts path or @name to uppercase branch name via registry lookup
branch = normalize_branch_arg("/home/aipass/seed")  # -> "SEED"
branch = normalize_branch_arg("@flow")              # -> "FLOW"
```
Registry is the source of truth - no path parsing fallbacks.

## Timeout Detection

`system_operations.py` uses a **two-layer timeout system** for branch module execution:

1. **Layer 1** - `is_long_running_command()`: Keyword-based detection (audit, diagnostics, sync, checklist, snapshot, versioned, backup, restore, close). Returns True -> drone.py passes `timeout=None` to allow Layer 2.
2. **Layer 2** - `run_branch_module()` auto-detection: When `timeout=None`, applies 120s for known slow commands (backup_system, checklist, close). Falls back to 30s default otherwise.

Both layers must recognize a slow command. If Layer 1 misses it, drone.py hardcodes 30s and Layer 2 never fires.

## Push-Based Error Reporting

When `run_branch_module()` encounters a failure (env/import error, non-zero exit, timeout, exception), it pushes the error to Trigger's error registry via `_report_to_error_registry()`. This enables Trigger's full dispatch pipeline: circuit breaker -> rate limiting -> email to source branch.

## Directory Structure

```
drone/
├── apps/
│   ├── drone.py                 # Main entry point (thin orchestrator)
│   ├── modules/                 # Core command modules
│   │   ├── activated_commands.py    # Shortcut command routing
│   │   ├── branch_registry.py       # Branch name resolution
│   │   ├── commons.py               # The Commons shortcuts
│   │   ├── discovery.py             # Command discovery & branch module execution
│   │   ├── loader.py                # Module loading system
│   │   ├── paths.py                 # Path resolution services
│   │   ├── registry.py              # Registry management
│   │   ├── routing.py               # Module interface exports
│   │   └── run.py                   # Python module execution
│   └── handlers/                # Implementation details (cross-branch guard)
│       ├── branch_registry/     # Branch lookup by email/name/path
│       ├── discovery/           # Scan, register, activate, system ops
│       ├── display/             # Display formatting (archived)
│       ├── json/                # JSON handler package
│       ├── json_handler.py      # Auto-creating JSON system
│       ├── json_templates/      # JSON templates (config/data/log)
│       ├── loader/              # Command file loading & validation
│       ├── paths/               # @ resolution & path utilities
│       ├── perf/                # Performance monitoring
│       ├── registry/            # Registry CRUD, stats, healing
│       └── routing/             # Module discovery & command routing
├── commands/                    # Command registry (per-branch)
│   └── [branch_name]/
│       ├── registry.json        # Discovered commands
│       └── active.json          # Activated commands
├── DRONE.id.json                # Branch identity
├── DRONE.local.json             # Session history
├── DRONE.observations.json      # Collaboration patterns
└── README.md                    # This file
```

## Integration Points

### Depends On
- Python 3.x standard library
- Rich (for console output)
- Prax (logger)
- CLI (console formatting)

### Integrates With
- **FLOW**: Workflow management (plan shortcuts)
- **AI_MAIL**: Branch messaging (email shortcuts)
- **SEED**: Standards compliance (audit/checklist shortcuts)
- **TRIGGER**: Push-based error reporting to error registry
- **The Commons**: Social network routing (`drone commons`)
- **All Branches**: Command routing via @ resolution

### Provides To
- Unified command interface for all branches
- Command discovery and activation
- System-wide command registry
- Centralized @ argument resolution
- `normalize_branch_arg()` for branch name lookups

## Memory System

DRONE maintains memory files per AIPass standard:

- **DRONE.id.json**: Branch identity (permanent, does not roll over)
- **DRONE.local.json**: Session history (max 600 lines, auto-rolls to Memory Bank)
- **DRONE.observations.json**: Collaboration patterns (max 600 lines)

## Notes

- This README represents the EXACT CURRENT STATE of DRONE
- Registry is the source of truth for branch resolution (no path-parsing fallbacks)
- Future plans are tracked in FLOW system PLANs
- Past work is in DRONE.local.json session history
