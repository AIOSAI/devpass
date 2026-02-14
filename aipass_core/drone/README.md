# DRONE - Command Routing & Module Discovery System

## Overview

**Branch**: DRONE
**Location**: `/home/aipass/aipass_core/drone`
**Purpose**: Command orchestration and module discovery for the AIPass ecosystem
**Created**: 2025-11-13

## Architecture

- **Pattern**: Modular (3-layer: entry point → modules → handlers)
- **Structure**: `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator**: `apps/drone.py` - auto-discovers and routes to modules
- **Module Interface**: All modules implement `handle_command(command, args) -> bool`

## Core Functions

### What DRONE Does
- Routes commands to appropriate branches and modules (supports N-word commands)
- **Centralized @ argument resolution** - resolves `@branch` to full paths before passing to modules
- Discovers and registers available commands across all branches
- Auto-registers commands during scan (streamlined workflow)
- Manages command activation/deactivation (merges, doesn't overwrite)
- Provides system-wide command orchestration
- Maintains command registry in `commands/` directory
- Filters command lists by system (@branch notation)
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

# Direct Python execution (path resolution)
drone run python3 <module> [args]  # Resolves module path automatically
drone run python3 flow.py list     # → ~/aipass_core/flow/apps/flow.py list
drone run python3 seed.py --help   # → ~/seed/apps/seed.py --help

# Examples
drone scan @prax                # Scan prax, register, prompt to activate
drone scan @flow --all          # Show Python commands for copy-paste testing
drone list @flow                # Show only flow commands
drone prax file watcher start   # 3-word command support
drone seed audit @flow          # @ resolved to path, passed to seed
drone dev add @flow "issues" "bug fix"
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

### Why Centralized Resolution
- **AI Autonomy**: AI can use consistent `@branch` syntax everywhere
- **No implicit defaults**: All targets must be explicit
- **Backwards compatible**: Bare names still work (with warning)

## Directory Structure

```
drone/
├── apps/
│   ├── drone.py              # Main entry point
│   ├── modules/              # Core command modules (thin orchestration)
│   │   ├── activated_commands.py  # Shortcut command routing
│   │   ├── branch_registry.py     # Branch name resolution (normalize_branch_arg)
│   │   ├── discovery.py           # Command discovery & branch module execution
│   │   ├── loader.py              # Module loading system
│   │   ├── paths.py               # Path resolution services
│   │   ├── registry.py            # Registry management
│   │   ├── routing.py             # @ argument preprocessing
│   │   └── run.py                 # Python module execution
│   ├── handlers/             # Implementation details
│   │   ├── branch_registry/  # Branch lookup handlers
│   │   ├── discovery/        # Discovery subsystem
│   │   ├── json/             # JSON handling
│   │   ├── loader/           # Module loader handlers
│   │   ├── paths/            # Path resolution handlers
│   │   ├── registry/         # Registry handlers
│   │   └── routing/          # Routing handlers
│   ├── extensions/           # Extensions (unused)
│   └── plugins/              # Plugin extensions (unused)
├── commands/                 # Command registry (per-branch)
│   └── [branch_name]/
│       ├── registry.json    # Discovered commands
│       └── active.json      # Activated commands
├── DRONE.id.json            # Branch identity
├── DRONE.local.json         # Session history
├── DRONE.observations.json  # Collaboration patterns
└── README.md                # This file
```

## Integration Points

### Depends On
- Python 3.x standard library
- Rich (for console output)
- AIPass core infrastructure

### Integrates With
- **FLOW**: Workflow management
- **AI_MAIL**: Branch messaging
- **SEED**: Standards compliance
- **All Branches**: Command routing

### Provides To
- Unified command interface for all branches
- Command discovery and activation
- System-wide command registry

## Memory System

DRONE maintains memory files per AIPass standard:

- **DRONE.id.json**: Branch identity (permanent, does not roll over)
- **DRONE.local.json**: Session history (max 600 lines, auto-rolls to Memory Bank)
- **DRONE.observations.json**: Collaboration patterns (max 600 lines)

## Usage Examples

### Scan and Activate
```bash
drone scan @seed                # Scan seed, auto-register, prompt to activate
drone activate seed             # Interactive activation menu
drone list                      # See what's activated
```

### Using @ Targets
```bash
drone seed audit @flow          # Audit flow branch
drone seed audit @drone         # Audit drone branch
drone @ai_mail send @flow "Subject" "Message"
drone plan create @aipass       # Create plan at root
```

### Routing Commands
```bash
drone @flow help                # Direct branch help
drone @seed help                # Seed standards help
drone dev add @flow "bug" "description"
```

## Notes

- This README represents the EXACT CURRENT STATE of DRONE
- Registry is the source of truth for branch resolution (no path-parsing fallbacks)
- Future plans are tracked in FLOW system PLANs
- Past work is in DRONE.local.json session history