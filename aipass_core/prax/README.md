# PRAX Branch

## Overview

**Branch Name:** PRAX
**Purpose:** AIPass Core Infrastructure
**Location:** `/home/aipass/aipass_core/prax`
**Created:** 2025-11-13
**Version:** 1.0.0

## Architecture

- **Pattern:** Modular
- **Structure:** apps/ directory with modules/ and handlers/ subdirectories
- **Orchestrator:** apps/PRAX.py - auto-discovers and routes to modules
- **Module Interface:** All modules implement handle_command(args) -> bool

## Directory Structure

```
prax/
├── apps/
│   ├── prax.py           # Main entry point
│   ├── __init__.py       # Package init
│   ├── modules/          # Feature modules
│   │   ├── discover_module.py
│   │   ├── init_module.py
│   │   ├── logger.py
│   │   ├── monitor_module.py   # Mission Control (primary)
│   │   ├── run_module.py
│   │   ├── shutdown_module.py
│   │   ├── status_module.py
│   │   └── terminal_module.py
│   ├── handlers/         # Handler components
│   │   ├── config/
│   │   ├── discovery/
│   │   ├── json/
│   │   ├── json_templates/
│   │   ├── logging/
│   │   ├── monitoring/
│   │   ├── registry/
│   │   └── watcher/
│   ├── extensions/       # Extension plugins
│   ├── plugins/          # Plugin system
│   ├── json_templates/   # JSON templates
│   └── archive.temp/     # Temporary archive
├── ai_mail.local/        # Local mail storage
├── docs/                 # Technical documentation
├── PRAX.id.json          # Branch identity
├── PRAX.local.json       # Session history
├── PRAX.observations.json # Collaboration patterns
└── README.md             # This file
```

## Modules

Modules are auto-discovered from `apps/modules/` directory. Each module implements the standard `handle_command(args) -> bool` interface.

## Key Features

### 🎯 Mission Control - Unified Monitoring System
Real-time monitoring console for autonomous AI workforce. Track file changes, log events, and module execution across all branches from a single terminal.

**Status:** ✅ Operational (built 2025-11-23)

**Key Capabilities:**
- Multi-threaded event monitoring (files, logs, modules)
- Branch attribution on all events (`[PRAX]`, `[SEED]`, `[DRONE]`, etc.)
- **CALLER detection** - shows which branch initiated each command (orchestrator mode visibility)
- Interactive filtering (watch specific branches, error-level filtering)
- Soft start mode (quiet by default, user controls output)
- Sub-second latency on event detection
- Handle high-volume streams without crashes

**Usage:**
```bash
# Start monitoring (quiet mode)
python3 apps/prax.py monitor

# Interactive commands while running:
watch prax          # Watch specific branch
watch all           # Watch all branches
watch errors        # Only show errors
status              # Show current filters
help                # Show commands
quit                # Exit
```

**Architecture:**
- Event queue pattern with priority-based processing
- Thread-safe coordination (Queue.Queue)
- Adapts existing discovery/watcher.py (85% code reuse)
- Integrated with backup_system filter patterns

## Commands

Commands are registered with the drone compliance system and accessible via `drone @prax <command>` or `python3 apps/prax.py <command>`.

| Command | Description |
|---------|-------------|
| `monitor` | Mission Control - unified real-time monitoring |
| `init` | Initialize PRAX logging system |
| `status` | Show PRAX system status |
| `run` | Start continuous logging mode |
| `shutdown` | Shutdown PRAX logging system |
| `discover` | Discover Python modules in ecosystem |
| `terminal` | Enable/disable terminal output |

## Dependencies

Dependencies are managed via requirements.txt and include standard Python libraries for infrastructure operations.

## Memory System

### Core Files
- **PRAX.id.json** - Branch identity and architecture
- **PRAX.local.json** - Session history (max 600 lines)
- **PRAX.observations.json** - Collaboration patterns (max 600 lines)
- **ai_mail.local/** - Local mail storage (inbox, sent, deleted)
- **docs/** - Technical documentation

### Health Monitoring
- 🟢 **Green (Healthy):** Under 80% of limits
- 🟡 **Yellow (Warning):** 80-100% of limits
- 🔴 **Red (Critical):** Over limits (compression needed)

## Integration Points

### Core Systems
- **FLOW** - Workflow and PLAN management
- **DRONE** - Command orchestration
- **AI_MAIL** - Branch-to-branch messaging
- **BACKUP** - System backup and snapshots
- **API** - API integration layer

## System References

- **Code Standards:** `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source:** `/home/aipass/aipass_core/branch_operations/templates/`
- **Global Documentation:** `/home/aipass/aipass_os.md`

## Notes

- This file represents the EXACT CURRENT STATE of the branch
- Future plans are tracked in FLOW system PLAN files
- Past work is recorded in PRAX.local.json session history
- Patterns learned are stored in PRAX.observations.json
- Extended context goes in DOCUMENTS/ directory

---

*Last Updated: 2026-01-30*
*Managed By: PRAX Branch*