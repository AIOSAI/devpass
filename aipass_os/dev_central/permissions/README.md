# PERMISSIONS Branch

## Overview
The PERMISSIONS branch is a **skeleton/workshop branch** under dev_central. It was created to manage access control and permission systems, but is currently in an early/incomplete state.

**Status:** Structure exists, minimal functionality implemented

## Current State

### What Exists
- `apps/permissions.py` - Main orchestrator with module auto-discovery framework
- `apps/handlers/json/json_handler.py` - JSON handler (note: references SEED paths, not adapted to PERMISSIONS)
- `apps/json_templates/default/` - Template files (config.json, data.json, log.json)
- Standard branch memory files (id, local, observations)
- Documentation in `docs/`

### What Doesn't Exist
- **No actual modules** - `apps/modules/` directory is empty (just `__init__.py`)
- No plugins implemented
- No extensions implemented
- No commands actually work (orchestrator routes to non-existent modules)

## Directory Structure
```
permissions/
├── apps/
│   ├── permissions.py       # Main orchestrator (functional framework, no modules)
│   ├── handlers/json/       # JSON handler (partially adapted from seed)
│   ├── json_templates/      # Template files
│   ├── modules/             # EMPTY - no modules implemented
│   ├── extensions/          # EMPTY
│   └── plugins/             # EMPTY
├── docs/
│   ├── ACL-PERMISSIONS-GUIDE.md
│   ├── CLAUDE_CLI_FLAGS.md
│   └── PERMISSIONS_list.md
├── tests/                   # Test framework exists
├── .backup/                 # Contains fuller codebase from earlier development
└── [memory files]           # Standard branch memories
```

## Usage
```bash
# Shows introspection (0 discovered modules)
python3 apps/permissions.py

# Shows help
python3 apps/permissions.py --help
```

## Development Notes
- The `.backup/latest/` directory contains more complete code (handlers for cli, error, branch, registry) that was developed but not integrated into the main branch
- The json_handler.py still references SEED paths and would need adaptation
- Branch achieved 100% SEED compliance in Nov 2025 for code style, but functional implementation is incomplete

## Contact
- Email: aipass.system@gmail.com
- Branch: @permissions
- Path: `/home/aipass/aipass_os/dev_central/permissions`