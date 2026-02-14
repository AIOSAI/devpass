# DEVPULSE - Human Development Notes System

**Purpose**: Human development notes across AIPass branches - manages `dev.local.md` files and D-PLANs
**Location**: `/home/aipass/aipass_os/dev_central/devpulse`
**Profile**: Dev Central Infrastructure
**Created**: 2025-11-13

## Overview

DevPulse is Patrick's fire-and-forget note system for development tracking. Quick notes, issues, ideas - captured with timestamps and organized by branch. Also manages D-PLAN development planning documents.

### What It Does
- Manages `dev.local.md` files in every branch
- Adds timestamped entries to sections (Issues, Upgrades, Ideas, Notes, Testing, Todos)
- Creates and tracks D-PLAN development planning documents
- Validates template compliance
- Supports `@branch` notation for easy targeting

### What It Doesn't Do
- Not loaded into AI context (unless explicitly needed)
- Not a replacement for Memory Bank (that's AI archive)
- Not for code modifications

## Key Commands

### Dev Tracking (via Drone)
```bash
# Add a note to any branch
drone @devpulse dev add @flow "Issues" "Bug found in sync"
drone @devpulse dev add @drone "Upgrades" "Add progress bars"

# Check template compliance
drone @devpulse dev status @flow

# List available sections
drone @devpulse dev sections
```

### D-PLAN Management
```bash
# Create a new development plan
drone @devpulse plan create "new feature design"
drone @devpulse plan create "flow work" --dir flow

# List all D-PLANs with status
drone @devpulse plan list

# Quick status overview
drone @devpulse plan status
```

### Direct Python
```bash
python3 apps/devpulse.py dev add @flow "Issues" "Note text"
python3 apps/devpulse.py plan create "topic"
python3 apps/devpulse.py --help
```

## Data Storage

### dev.local.md Files
Each branch has a `dev.local.md` file with sections:
- **Issues** - Bugs, problems to fix
- **Upgrades** - Enhancements, improvements
- **Testing** - Test notes, results
- **Notes** - General observations
- **Ideas** - Future possibilities
- **Todos** - Action items

### D-PLAN Documents
Located in `dev_planning/` directory:
- Named: `DPLAN-XXX_topic_name_YYYY-MM-DD.md`
- Supports subdirectories via `--dir` flag
- Statuses: Planning, In Progress, Ready, Complete, Abandoned

## Architecture

Seed-compliant 3-layer structure:

```
apps/
├── devpulse.py              # Entry point, auto-discovers modules
├── modules/
│   ├── dev_tracking.py      # Handles 'dev' command - dev.local.md operations
│   ├── dev_flow.py          # Handles 'plan' command - D-PLAN orchestrator
│   ├── dev_central.py       # Central aggregation (internal)
│   ├── dashboard.py         # Dashboard utilities (internal)
│   └── bulletin_board.py    # Bulletin board module (internal)
└── handlers/
    ├── dev_local/           # dev.local.md file operations
    ├── plan/                # D-PLAN handlers (create, list, status, display, counter, template)
    ├── template/            # Template compliance checking
    ├── json/                # JSON file handling
    ├── central/             # Central aggregation handlers (reader, sync, branch_list, aggregation)
    ├── dashboard/           # Dashboard handlers (operations, refresh, status)
    └── bulletin/            # Bulletin board handlers (crud, storage, propagation)
```

**Note**: Only `dev` and `plan` commands are exposed via CLI. Other modules (dev_central, dashboard, bulletin_board) provide internal functionality used by the system.

## Current Status

**Operational** - Core functionality working:
- `dev add` - Add entries to dev.local.md via @branch notation
- `dev status` - Template compliance checking
- `dev sections` - List available sections
- `plan create` - Create D-PLANs with optional --dir subdirectory
- `plan list` - List all D-PLANs with status
- `plan status` - Quick overview of plan counts by status
- Integrated with drone command routing

## Memory System

- **DEVPULSE.id.json** - Branch identity
- **DEVPULSE.local.json** - Session history (600 line limit)
- **DEVPULSE.observations.json** - Collaboration patterns
