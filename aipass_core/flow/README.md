# FLOW - FPLAN Management System

**Purpose:** FPLAN management system for AIPass - creates, tracks, and manages workflow tasks with template-based automation
**Location:** `/home/aipass/aipass_core/flow`
**Profile:** AIPass Core Infrastructure
**Created:** 2025-11-13
**Last Updated:** 2026-01-30
**Version:** 2.1.0

## Overview

Flow provides workflow orchestration through numbered FPLAN documents (e.g., FPLAN-0001, FPLAN-0042). Each FPLAN is a trackable task with metadata, location awareness, and template-based initialization. Registry system maintains plan state (open/closed) and auto-cleanup of orphaned plans.

**Format:** `FPLAN-XXXX` (with hyphen, 4-digit zero-padded number)
- Consistent with DevPulse DPLAN-XXX convention
- Migration from PLAN0XXX format completed 2025-12-02

### What I Do
- Create/delete/manage FPLAN documents
- Maintain registry of all plans
- Provide location-aware plan creation (@folder syntax)
- Auto-close orphaned plans
- Integrate with template system for initialization

### What I Don't Do
- Execute plan tasks (plans are documentation)
- Manage git operations
- Handle file backups
- Provide IDE integration

### How I Work
Thin orchestrator pattern - flow.py auto-discovers modules, modules coordinate handlers, handlers implement business logic. 95% Seed standards compliant with handler independence and CLI services integration.

## Architecture

- **Pattern:** Handler-based modular architecture (Seed standards compliant)
- **Structure:** apps/ with flow.py orchestrator, modules/ for commands, handlers/ for business logic
- **Orchestrator:** apps/flow.py - auto-discovers modules via importlib, routes commands, CLI services integration
- **Module Interface:** `handle_command(command: str, args: List[str]) -> bool`
- **Handler Pattern:** Thin modules orchestrate, handlers implement (26 handlers across 8 domains, 100% domain independence)
- **Compliance:** 100% Seed standards - error_handler 100%, imports 100%, architecture 100%, modules with OperationResult pattern

### Directory Structure

```
apps/
├── flow.py              # Main orchestrator
├── __init__.py
├── modules/             # Command modules
│   ├── aggregate_central.py
│   ├── close_plan.py
│   ├── create_plan.py
│   ├── list_plans.py
│   ├── registry_monitor.py
│   └── restore_plan.py
├── handlers/            # Business logic handlers (26 total)
│   ├── config/          # Configuration handlers (1)
│   ├── dashboard/       # Dashboard display handlers (2)
│   ├── json/            # JSON operations handlers (1)
│   ├── mbank/           # Memory Bank integration (1)
│   ├── plan/            # Core PLAN handlers (14)
│   ├── registry/        # Registry management handlers (3)
│   ├── summary/         # Summary generation handlers (2)
│   └── template/        # Template handlers (2)
├── extensions/          # Optional extensions
├── json_templates/      # JSON template files
├── plugins/             # Plugin system
└── archive_temp/        # Temporary archive storage
```

## Key Capabilities

- Create numbered FPLAN documents with auto-increment (FPLAN-0001, FPLAN-0002, etc.)
- Delete plans with confirmation and registry cleanup
- Location-aware plan creation (@folder syntax for contextual placement)
- Template-based plan initialization (default, master templates)
- Registry maintenance with metadata tracking (location, subject, status, timestamps)
- CLI services integration (Rich-formatted output, color-coded messages)
- Handler independence (26 focused handlers, single-responsibility design)
- 100% Seed standards compliant

## Usage Instructions

### Basic Usage
```bash
python3 apps/flow.py <command> [args]  # Auto-discovery pattern finds all modules
```

### Common Workflows
- **Create plan:** `flow.py create . 'subject' [template]`
- **Close plan:** `flow.py close <plan_number> --yes`
- **List plans:** `flow.py list`
- **View help:** `flow.py --help`

### Examples
```bash
flow.py create . 'Add authentication'
flow.py close 0042 --yes
flow.py close FPLAN-0042 --yes  # Both formats accepted
flow.py list
```

## Integration Points

### Depends On
- prax (logging system)
- cli (console, header, error, success services)
- template system (.cached_templates/)

### Integrates With
- Registry system (apps/handlers/registry/)
- Template handlers (apps/handlers/template/)
- JSON operations (tracking and logging)

### Provides To
- AIPass ecosystem (PLAN workflow management)
- Other branches (reference implementation for Seed compliance)
- Users (numbered task tracking system)

## System References

- **Code Standards:** `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source:** `/home/aipass/aipass_core/branch_operations/templates/`
- **Global Documentation:** `/home/aipass/aipass_os.md`

### Core Systems
- **flow:** Workflow and PLAN management
- **drone:** Command orchestration
- **ai_mail:** Branch-to-branch messaging
- **backup:** System backup and snapshots
- **prax:** Logging and infrastructure
- **api:** API integration layer

## Memory System

### Files
- **Identity:** `FLOW.id.json` - Branch identity and architecture
- **Local:** `FLOW.local.json` - Session history (max 600 lines)
- **Observations:** `FLOW.observations.json` - Collaboration patterns (max 600 lines)
- **AI Mail:** `FLOW.ai_mail.json` - Branch messages
- **Documents:** `DOCUMENTS/` - Extended memory (max 10 files, rollover to Memory Bank)

### Health Monitoring
- 🟢 **Green (Healthy):** Under 80% of limits
- 🟡 **Yellow (Warning):** 80-100% of limits
- 🔴 **Red (Critical):** Over limits (compression needed)

## Status

- **Health:** Healthy
- **Auto Update Enabled:** Yes
- **Last Auto Update:** 2026-01-30
- **Last Health Check:** 2026-01-30
- **Standards Compliance:** 100% (after recent improvements)

---

*This document is automatically maintained and represents the EXACT CURRENT STATE of the FLOW branch.*