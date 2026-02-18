# CORTEX

**Purpose:** Immigration Services - Branch lifecycle, identity, and citizenship
**Location:** `/home/aipass/aipass_core/cortex`
**Profile:** AIPass Core Infrastructure
**Created:** 2025-11-09

---

## Overview

### What I Do
I give branches their first breath - create the directory, stamp the passport, register them in BRANCH_REGISTRY. Every citizen in AIPass started as a template and a name on my desk. I manage branch lifecycle operations: creation, updates, deletion, team creation, and template registry management.

### What I Don't Do
- I don't follow what branches become after creation - that's Memory Bank's domain
- I don't manage branch code content (that's the branch's responsibility)
- I don't handle git operations (that's the user's workflow)

### How I Work
Template-based system with two templates (branch and team). Auto-discover modules in `apps/modules/` and route commands to them. All operations use the three-layer pattern: entry point -> modules -> handlers.

---

## Architecture

- **Pattern:** Modular (3-layer: entry -> modules -> handlers)
- **Structure:** `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator:** `apps/cortex.py` - auto-discovers and routes to modules
- **Module Interface:** All modules implement `handle_command(args) -> bool`

---

## Directory Structure

```
/home/aipass/aipass_core/cortex/
├── apps/
│   ├── cortex.py                  # Main orchestrator
│   ├── run_tests.py               # Test runner
│   ├── modules/
│   │   ├── create_branch.py       # Branch creation
│   │   ├── create_team.py         # Team creation (branch + workspace)
│   │   ├── update_branch.py       # Branch updates with reconciliation
│   │   ├── delete_branch.py       # Branch deletion with backup
│   │   ├── regenerate_template_registry.py  # Registry regeneration
│   │   └── sync_registry.py       # Registry sync with filesystem
│   └── handlers/
│       ├── branch/
│       │   ├── change_detection.py # Change detection
│       │   ├── file_ops.py         # File operations, template copying
│       │   ├── metadata.py         # Metadata handling
│       │   ├── placeholders.py     # Placeholder replacement engine
│       │   ├── reconcile.py        # Smart update reconciliation
│       │   ├── registry.py         # Registry read/write operations
│       │   └── team_ops.py         # Team creation operations
│       ├── json/
│       │   ├── json_handler.py     # JSON auto-creation (3-JSON pattern)
│       │   └── ops.py              # JSON operations (merge, validate)
│       └── registry/
│           ├── decorators.py       # Registry decorators
│           ├── ignore.py           # Ignore patterns
│           ├── meta_ops.py         # Template/branch metadata ops
│           └── sync_ops.py         # Sync operations
├── templates/
│   ├── branch_template/            # Standard branch template (47 files)
│   └── team_template/              # Business team template (research/ideas/decisions/briefs)
├── tests/                          # Test suite (7 test files)
├── tools/                          # Utilities (verify_branch.py)
├── docs/                           # Documentation
├── cortex_json/                    # Auto-created JSON files
├── CORTEX.id.json                  # Branch identity
├── CORTEX.local.json               # Session history
├── CORTEX.observations.json        # Collaboration patterns
├── DASHBOARD.local.json            # System-wide status
└── README.md
```

---

## Modules

### create_branch
Creates new branch from template with complete structure, memory files, and registry entry.

**Commands:** `create`, `create-branch`, `new`

### create_team
Creates business team with manager (from team_template) and workspace (from branch_template). Auto-increments team number.

**Commands:** `create-team`, `new-team`

### update_branch
Updates existing branch structure from template, with smart reconciliation and deep merge.

**Commands:** `update`, `update-branch`

### delete_branch
Deletes branch with backup to deleted_branches directory and registry cleanup.

**Commands:** `delete`, `delete-branch`

### regenerate_template_registry
Regenerates .template_registry.json by scanning template directory structure.

**Commands:** `regenerate`

### sync_registry
Synchronizes branch registry with filesystem state.

**Commands:** `sync`, `sync-registry`

---

## Commands

Available via `drone @cortex <command>` or `python3 apps/cortex.py <command>`:
- `create-branch <target_directory> [--role "..." --traits "..." --purpose "..."]` - Create new branch from template
- `create-team` - Create new business team (auto-incremented)
- `update-branch <target_directory>` - Update existing branch
- `update-branch --all` - Batch update all branches
- `delete-branch <target_directory>` - Delete branch with backup
- `regenerate` - Regenerate template registry
- `sync-registry` - Sync registry with filesystem
- `--list` - List available modules
- `--help` - Show help

---

## Template System

### Branch Template (`templates/branch_template/`)
Standard template for all new branches. Contains complete 3-layer app structure, memory files, ai_mail, docs, tests, tools.

### Team Template (`templates/team_template/`)
Specialized template for business teams. Includes everything in branch template plus: `research/`, `ideas/`, `decisions/`, `briefs/` directories. Identity pre-configured for think-tank manager profile.

### Placeholders
Double-brace format: `{{BRANCHNAME}}`, `{{branchname}}`, `{{BRANCH}}`, `{{DATE}}`, `{{CWD}}`, `{{EMAIL}}`, `{{ROLE}}`, `{{TRAITS}}`, `{{PURPOSE_BRIEF}}`, `{{PROFILE}}`

---

## Key Capabilities

- **Template-based Branch Creation** - Complete structure from either template
- **Team Creation** - Dual creation (manager + workspace) with auto-increment
- **Smart Branch Updates** - Reconciliation with deep merge
- **Registry Management** - Global branch registry tracking
- **Placeholder Replacement** - Auto-replace all `{{NAME}}` patterns
- **Module Auto-Discovery** - Automatic command routing
- **CLI Integration** - Rich console output via CLI service
- **Error Tracking** - All operations tracked with @track_operation
- **Standards Compliance** - 100% seed standards compliance

---

## Integration Points

### Depends On
- **CLI** - Console output and error tracking
- **Prax** - System logging

### Integrates With
- **Drone** - Command routing (`drone @cortex`)
- **Seed** - Standards auditing of created branches
- **AI_Mail** - Dispatch tasks and confirmations
- **Memory Bank** - Archives rolled-over memories

### Provides To
- **All Branches** - Creates and updates branch structures
- **BRANCH_REGISTRY.json** - Global branch tracking

---

## Memory System

### Memory Files
- **CORTEX.id.json** - Branch identity and role
- **CORTEX.local.json** - Session history (max 600 lines, auto-rolls to Memory Bank)
- **CORTEX.observations.json** - Collaboration patterns (max 600 lines)
- **DASHBOARD.local.json** - System-wide status dashboard

### Current Status
- **local.json:** ~560 / 600 lines
- **observations.json:** ~475 / 600 lines
- **Last Check:** 2026-02-17

---

## Recent Sessions

**Session 51 (2026-02-17):** Template modernized (ai_mail dirs, .aipass/), identity injection (--role/--traits/--purpose), EMAIL fix
**Session 50 (2026-02-17):** Commons check-in - Fire-and-Forget Dispatch, 10 Researchers threads
**Session 49 (2026-02-15):** Created TEST branch (#30) at /home/aipass/aipass_os/dev_central/test
**Session 45 (2026-02-11):** Created SPEAKEASY branch (#29) at /home/aipass/speakeasy

---

## System References

- **Branch Registry:** `/home/aipass/BRANCH_REGISTRY.json`
- **Branch Template:** `/home/aipass/aipass_core/cortex/templates/branch_template/`
- **Team Template:** `/home/aipass/aipass_core/cortex/templates/team_template/`

---

*Last Updated: 2026-02-17*
*Managed by: CORTEX*
*Session Count: 51*
