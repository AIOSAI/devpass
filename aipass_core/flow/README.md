# FLOW - FPLAN Management System

**Purpose:** FPLAN lifecycle management for AIPass - creates, tracks, closes, summarizes, and archives workflow plans
**Location:** `/home/aipass/aipass_core/flow`
**Profile:** Planning, Orchestration & Ambiguity Navigation
**Created:** 2025-11-13
**Last Updated:** 2026-02-15
**Version:** 2.2.0

## Overview

Flow provides workflow orchestration through numbered FPLAN documents (e.g., FPLAN-0001, FPLAN-0042). Each FPLAN is a trackable task with metadata, location awareness, and template-based initialization. The registry system maintains plan state (open/closed) with auto-cleanup of orphaned plans. On closure, plans receive AI-generated summaries and archive to Memory Bank.

**Format:** `FPLAN-XXXX` (with hyphen, 4-digit zero-padded number)

**Current stats:** 72+ total plans (0 open, 72+ closed)

### What I Do
- Create, close, restore, and list FPLAN documents
- Maintain plan registry with metadata tracking
- Generate AI summaries for closed plans (via OpenRouter API)
- Archive closed plans to Memory Bank with TRL tagging
- Maintain dashboards (local and central aggregation)
- Provide location-aware plan creation (@folder syntax)
- Auto-close orphaned plans via registry monitor
- Template-based plan initialization (default, master, proposal)

### What I Don't Do
- Execute plan tasks (plans are documentation, not execution)
- Enforce standards (that's Seed)
- Monitor system health in real-time (that's Prax)
- Handle inter-branch messaging (that's AI_Mail)

### How I Work
Thin orchestrator pattern - flow.py auto-discovers modules via importlib, modules coordinate handlers, handlers implement business logic. Config-driven architecture with JSON configs in flow_json/.

## Architecture

- **Pattern:** Handler-based modular architecture (Seed standards compliant)
- **Orchestrator:** apps/flow.py - auto-discovers modules, routes commands, CLI services integration
- **Module Interface:** `handle_command(command: str, args: List[str]) -> bool`
- **Handler Pattern:** Thin modules orchestrate, handlers implement (26 handlers across 8 domains)

### Directory Structure

```
flow/
├── apps/
│   ├── flow.py              # Main orchestrator (auto-discovery)
│   ├── modules/             # Command modules (7)
│   │   ├── create_plan.py
│   │   ├── close_plan.py
│   │   ├── list_plans.py
│   │   ├── restore_plan.py
│   │   ├── registry_monitor.py
│   │   ├── aggregate_central.py
│   │   └── post_close_runner.py  # Background: AI summaries + archival
│   ├── handlers/            # Business logic (26 handlers)
│   │   ├── config/          # Configuration (1)
│   │   ├── dashboard/       # Dashboard display (2)
│   │   ├── json/            # JSON operations (1)
│   │   ├── mbank/           # Memory Bank integration (1)
│   │   ├── plan/            # Core PLAN operations (14)
│   │   ├── registry/        # Registry management (3)
│   │   ├── summary/         # AI summary generation (2)
│   │   └── template/        # Template handling (2)
│   ├── extensions/          # Optional extensions
│   ├── json_templates/      # JSON template definitions
│   └── plugins/             # Plugin system
├── templates/               # Plan templates (default, master, proposal)
├── flow_json/               # JSON configs and operation logs (32 files)
├── tests/                   # Test suite
├── docs/                    # Technical documentation
├── logs/                    # Operation logs
└── tools/                   # Utility scripts
```

## Usage

### Via Drone (Standard)
```bash
drone @flow create . "subject"           # Create plan in current directory
drone @flow create . "subject" master    # Create master (multi-phase) plan
drone @flow close <plan_number>           # Close plan (auto-confirms, AI summary in background)
drone @flow list                         # List all plans
drone @flow restore <plan_number>        # Restore a closed plan
drone @flow registry                     # Run registry health check
drone @flow aggregate                    # Aggregate plans to central dashboard
```

### Direct Execution
```bash
python3 apps/flow.py create . "Add authentication"
python3 apps/flow.py close 0042                    # Auto-confirms
python3 apps/flow.py close FPLAN-0042 --confirm     # With interactive prompt
python3 apps/flow.py close --all                     # Close all open plans
python3 apps/flow.py list
python3 apps/flow.py --help
```

## Integration Points

### Depends On
- **prax** - Logging system
- **cli** - Console formatting (header, error, success services)
- **api** - OpenRouter client for AI summary generation

### Provides To
- AIPass ecosystem (PLAN workflow management)
- Memory Bank (archived plan summaries)
- Central dashboard (aggregated plan status)

## Memory System

- **Identity:** `FLOW.id.json` - Branch identity and role
- **Local:** `FLOW.local.json` - Session history (max 600 lines, auto-rollover)
- **Observations:** `FLOW.observations.json` - Collaboration patterns (max 600 lines)
- **Dashboard:** `DASHBOARD.local.json` - System-wide status snapshot

## Status

- **Health:** Healthy
- **Sessions:** 41
- **Last Updated:** 2026-02-15

---

*This document reflects the current state of the FLOW branch.*
