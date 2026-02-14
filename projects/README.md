# PROJECTS

**Purpose:** Experimental workspace for project scaffolding and development experiments
**Location:** `/home/aipass/projects`
**Profile:** Workshop
**Created:** 2025-11-23

---

## Overview

PROJECTS is a workshop branch - a scaffolded template ready for development. Contains base architecture with no active modules, plus external project clones for reference/experimentation.

### What This Branch Does

- Provides auto-discovery module architecture
- Houses experimental code and project scaffolding
- Serves as a development sandbox
- Hosts cloned external projects (e.g., moltbot)

### Current State

**Modules:** 0 discovered (apps/modules/ is empty)
**Status:** Template deployed, awaiting module development
**External Projects:** moltbot (personal AI assistant clone)

---

## Architecture

- **Pattern:** Auto-discovery module orchestration
- **Entry Point:** `apps/projects.py`
- **Module Interface:** Modules in `apps/modules/` implementing `handle_command(command, args) -> bool`

### How It Works

1. `projects.py` scans `apps/modules/` for `.py` files
2. Modules with `handle_command()` are auto-registered
3. Commands route to modules automatically

---

## Directory Structure

```
/home/aipass/projects/
├── apps/
│   ├── projects.py          # Entry point (orchestrator)
│   ├── modules/             # Command modules (empty)
│   ├── handlers/
│   │   └── json/
│   │       └── json_handler.py  # JSON utilities
│   ├── extensions/          # Future extensions
│   ├── plugins/             # Future plugins
│   └── json_templates/      # JSON file templates
│       └── default/
├── artifacts/               # Old/experimental code (create_project_folder.py, projects.py)
├── moltbot/                 # External clone: personal AI assistant project
├── workshop/                # Project workspace (placeholder folders)
├── tests/                   # Test suite (conftest.py only)
├── tools/                   # Empty
├── logs/                    # Log files
├── docs/                    # Documentation (template only)
└── ai_mail.local/           # Branch messaging
```

---

## Usage

```bash
# Show introspection (discovered modules)
python3 apps/projects.py

# Show help
python3 apps/projects.py --help

# Run command (when modules exist)
python3 apps/projects.py <command> [args...]
```

---

## Key Files

| File | Purpose |
|------|---------|
| `apps/projects.py` | Main orchestrator with auto-discovery |
| `apps/handlers/json/json_handler.py` | Self-healing JSON system |
| `PROJECTS.id.json` | Branch identity |
| `PROJECTS.local.json` | Session history |
| `PROJECTS.observations.json` | Collaboration patterns |

---

## Memory System

- **PROJECTS.id.json** - Branch identity (permanent)
- **PROJECTS.local.json** - Session history (max 600 lines, auto-rolls)
- **PROJECTS.observations.json** - Patterns learned (max 600 lines)
- **DASHBOARD.local.json** - System-wide status

---

## Dependencies

- Python 3.12+
- AIPass core infrastructure (prax, cli)
- No external packages required

---

## Development Notes

To add a new module:

1. Create `apps/modules/your_module.py`
2. Implement `handle_command(command: str, args: List[str]) -> bool`
3. Module auto-discovers on next run

---

*Last Updated: 2026-01-30*
