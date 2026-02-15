# PRAX Branch

## Overview

**Branch Name:** PRAX
**Role:** The Observer - system-wide monitoring and logging service provider
**Purpose:** AIPass Core Infrastructure
**Location:** `/home/aipass/aipass_core/prax`
**Created:** 2025-11-08
**Sessions:** 29

## What PRAX Does

PRAX provides system-wide logging and monitoring infrastructure. Branches subscribe by importing `from prax.apps.modules.logger import system_logger`. Logs auto-route to `/home/aipass/system_logs/<branch>_<module>.log`. Mission Control gives live visibility into all system activity.

## Architecture

- **Pattern:** Modular (3-layer: entry point / modules / handlers)
- **Orchestrator:** `apps/prax.py` - auto-discovers and routes to modules via importlib
- **Module Interface:** All modules implement `handle_command(args) -> bool`

## Directory Structure

```
prax/
├── apps/
│   ├── prax.py              # Main entry point
│   ├── modules/             # Service modules (auto-discovered)
│   │   ├── logger.py            # Logging service (core export)
│   │   ├── monitor_module.py    # Mission Control (primary feature)
│   │   ├── discover_module.py   # Module discovery
│   │   ├── init_module.py       # System initialization
│   │   ├── run_module.py        # Continuous logging mode
│   │   ├── shutdown_module.py   # System shutdown
│   │   ├── status_module.py     # System status
│   │   └── terminal_module.py   # Terminal output control
│   └── handlers/            # Implementation details
│       ├── monitoring/          # Mission Control components
│       ├── logging/             # Log setup, override, operations
│       ├── discovery/           # Module scanning, filtering, watching
│       ├── config/              # Configuration and ignore patterns
│       ├── json/                # JSON data operations
│       ├── registry/            # Module registry management
│       └── watcher/             # File change monitoring
├── ai_mail.local/           # Local mail storage
├── docs/                    # Technical documentation
├── logs/                    # Branch-local logs
├── tests/                   # Test files
├── PRAX.id.json             # Branch identity
├── PRAX.local.json          # Session history
├── PRAX.observations.json   # Collaboration patterns
└── README.md                # This file
```

## Mission Control

Real-time monitoring console for the autonomous AI workforce. Tracks file changes, log events, and command execution across all branches from a single terminal.

**Key Capabilities:**
- Multi-threaded event monitoring (files, logs, modules)
- Branch attribution on all events (`[PRAX]`, `[SEED]`, `[DRONE]`, etc.)
- CALLER → TARGET detection for command flow visibility
- Compound branch name detection (AI_MAIL, BACKUP_SYSTEM, MEMORY_BANK)
- Claude Code project path → branch name resolution
- File category tags (memory, dashboard, code, config, docs, data)
- Agent activity visibility (parses Claude Code session JSONL for tool use, thinking, text)
- Noise filtering (.claude.json.backup, .tmp atomic writes, .claude/plugins)
- Direct python3 command detection via file indicators
- Sub-second latency, handles high-volume streams

**Usage:**
```bash
drone @prax monitor
# or
python3 apps/prax.py monitor

# Interactive commands:
watch all           # Watch all branches
watch prax          # Watch specific branch
watch errors        # Only show errors
status              # Show current filters
help                # Show commands
quit                # Exit
```

## Commands

| Command | Description |
|---------|-------------|
| `monitor` | Mission Control - unified real-time monitoring |
| `init` | Initialize PRAX logging system |
| `status` | Show PRAX system status |
| `run` | Start continuous logging mode |
| `shutdown` | Shutdown PRAX logging system |
| `discover` | Discover Python modules in ecosystem |
| `terminal` | Enable/disable terminal output |

## Memory System

- **PRAX.id.json** - Branch identity and role
- **PRAX.local.json** - Session history (max 600 lines, auto-rolls to Memory Bank)
- **PRAX.observations.json** - Collaboration patterns (max 600 lines)
- **ai_mail.local/** - Local mail storage (inbox, sent, deleted)

---

*Last Updated: 2026-02-14*
*Managed By: PRAX Branch*