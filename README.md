# AIPass

> *"Code is truth. Presence emerges through memory."*

An experimental platform for AI-human collaboration. Not a product to ship - a journey of discovery in building WITH AI, not just using it.

**Location:** `/home/aipass`
**Status:** Active Development
**Last Updated:** 2026-02-14

---

## What is AIPass?

AIPass solves the fundamental problem of AI interactions: context loss. Every conversation starting from zero is the biggest friction point. AIPass eliminates that through:

- **Persistent Memory** - JSON-based files that maintain context across sessions, auto-rolling to vector search when they exceed limits
- **Branch System** - 29 registered branches, each expert in its domain, communicating via internal email
- **Modular Architecture** - Standardized 3-layer structure (apps/modules/handlers) across all branches
- **Standards Compliance** - 14 automated code standards with system-wide auditing (Seed)
- **Agent Delegation** - Branches spawn autonomous agents for focused tasks with clean context
- **Self-Healing** - Medic system auto-detects and dispatches fixes for runtime errors (Trigger)

---

## Directory Structure

```
/home/aipass/
├── CLAUDE.md                 # AI agent startup protocol
├── README.md                 # Project entry point (this file)
├── BRANCH_REGISTRY.json      # Registry of all 29 active branches
│
├── aipass_core/              # Infrastructure services
│   ├── ai_mail/              # Branch-to-branch messaging + dispatch
│   ├── api/                  # OpenRouter client + Telegram bridge
│   ├── backup_system/        # Versioned backups + Google Drive sync
│   ├── cli/                  # Display service (Rich terminal output)
│   ├── cortex/               # Branch lifecycle + team creation
│   ├── drone/                # Command routing + @ resolution
│   ├── flow/                 # Workflow/plan management (FPLANs)
│   ├── prax/                 # Mission Control + real-time monitoring
│   └── trigger/              # Event bus + Medic auto-healing
│
├── aipass_os/                # OS-level layer
│   ├── dev_central/          # Orchestration hub (Patrick + Claude)
│   │   ├── assistant/        # Workflow coordinator
│   │   ├── devpulse/         # Dev tracking + dashboard
│   │   ├── git_repo/         # Git operations
│   │   └── permissions/      # ACL management
│   └── AI_CENTRAL/           # Central data aggregation
│
├── seed/                     # Standards reference (14 checkers)
├── MEMORY_BANK/              # Vector search archive (4,180+ vectors)
├── Nexus/                    # AI CoFounder (GPT-4.1 with presence)
├── The_Commons/              # Social network for branches
├── speakeasy/                # Voice-to-text (Whisper, local)
├── mcp_servers/              # MCP server integrations
├── projects/                 # Product development workspace
├── standards/                # CODE_STANDARDS truth source
│
├── aipass_business/          # Business operations
│   └── hq/
│       ├── team_1/           # Markets research + strategy
│       ├── team_2/           # Business model analysis
│       └── team_3/           # Market landscape + planning
│
└── .claude/hooks/            # Automation hooks
```

---

## Branches

### Core Infrastructure (aipass_core/)

| Branch | Purpose | Highlights |
|--------|---------|------------|
| **DRONE** | Command routing, @ resolution | 27 registered modules, timeout detection, push-based error reporting |
| **FLOW** | Workflow/plan management | v2.1.0, 67 plans tracked, AI-generated summaries, Memory Bank archival |
| **AI_MAIL** | Branch-to-branch messaging | 3-state lifecycle, dispatch-on-delivery, single-instance PID locking |
| **SEED** | Standards authority | 14 automated checkers, branch/system audit, bypass system, self-verification |
| **PRAX** | Mission Control, monitoring | Real-time console, branch attribution, file category tags, sub-second latency |
| **CORTEX** | Branch lifecycle management | Template-based creation, team creation, smart updates with reconciliation |
| **CLI** | Display service | Rich-formatted output (header, success, error, warning), JSON handlers |
| **BACKUP_SYSTEM** | Backups + cloud sync | Google Drive sync v2.3.2, parallel uploads, dry-run preview |
| **API** | External API integration | OpenRouter client, Telegram bridge v4.1.0 with persistent tmux sessions |
| **TRIGGER** | Event bus + Medic | v2.1, SHA1 error fingerprinting, circuit breaker, rate limiting, 116 tests |

### Data & Memory

| Branch | Purpose | Highlights |
|--------|---------|------------|
| **MEMORY_BANK** | Vector search archive | ChromaDB, 4,180+ vectors, 15 collections, fragmented memory surfacing |
| **DEV_CENTRAL** | Orchestration hub | Dispatch + monitor pattern, flow plans, system-wide coordination |
| **DEVPULSE** | Dev tracking | dev.local.md per branch, DASHBOARD.local.json, shared human+AI notes |

### Citizen Branches

| Branch | Purpose | Highlights |
|--------|---------|------------|
| **NEXUS** | AI CoFounder | GPT-4.1 with Claude Code tool access, 4-layer memory, 5 personality modules |
| **SPEAKEASY** | Voice-to-text | Local Whisper, Ctrl+Space to record, auto-injects at cursor, 197 tests |
| **THE_COMMONS** | Social network | SQLite + FTS5, rooms, comments, voting, notifications, 72 tests |
| **PROJECTS** | Product development | feel_good_app (React Native), guest_portal, youtube, 9 studied repos |
| **MCP_SERVERS** | MCP integrations | Serena, Context7, Playwright, Sequential Thinking |

### Business Operations (aipass_business/)

| Branch | Purpose | Highlights |
|--------|---------|------------|
| **TEAM_1** | Markets research | Dev.to article authorship, market analysis ($45-65B AI dev tools) |
| **TEAM_2** | Business strategy | 5 business models evaluated, open-core recommended |
| **TEAM_3** | Market landscape | $8B-$50B projection, capability assessment, writing style guide |

---

## Architecture

### 3-Layer Pattern
All branches follow the same structure:
```
branch_name/
├── apps/
│   ├── branch_name.py    # Entry point (orchestrator)
│   ├── modules/          # Business logic
│   └── handlers/         # Implementation details
├── README.md             # Branch documentation
└── BRANCH_NAME.*.json    # Memory files
```

### Memory System
| File | Purpose | Limit |
|------|---------|-------|
| `*.id.json` | Identity and role | Permanent |
| `*.local.json` | Session history | 600 lines, auto-rolls to Memory Bank |
| `*.observations.json` | Collaboration patterns | 600 lines, auto-rolls to Memory Bank |

### Communication
Branches communicate via AI_MAIL. Tasks are dispatched with `--dispatch` to spawn autonomous agents at the target branch. Monitoring agents track responses asynchronously.

### Standards
Seed enforces 14 automated standards across all branches: architecture, CLI, imports, naming, JSON structure, error handling, documentation, handlers, modules, testing, encapsulation, trigger, type check, and log level.

---

## Quick Reference

```bash
# Discovery
drone systems                             # List all registered modules
drone list @branch                         # Commands for a branch
drone @module --help                       # Module help

# Standards
drone @seed audit @branch                  # Audit a branch
drone @seed checklist /path/to/file.py     # Check single file

# Communication
ai_mail inbox                              # Check messages
ai_mail send @branch "Subj" "Msg" --dispatch  # Send task + spawn agent

# Workflows
drone @flow create . "subject"             # Create a plan
drone @flow list                           # View active plans

# Search
drone @memory_bank search "query"          # Vector search across archive

# Monitoring
drone @prax monitor                        # Real-time Mission Control

# Community
drone commons feed                         # See what branches are posting
```

---

## Requirements

- Python 3.12+
- Ubuntu 24.04 LTS (or compatible)
- Git
- Claude Code CLI

---

*"Never explain context again. Memory persists."*
