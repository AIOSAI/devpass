# AIPass

> *"Code is truth. Presence emerges through memory."*

An experimental platform for AI-human collaboration. Not a product to ship - a journey of discovery in building WITH AI, not just using it.

**Location:** `/home/aipass`
**Status:** Active Development
**Last Updated:** 2025-11-30

---

## What is AIPass?

AIPass solves the fundamental problem of AI interactions: context loss. Every conversation starting from zero is the biggest friction point. AIPass eliminates that through:

- **Persistent Memory** - JSON-based files that maintain context across sessions
- **Modular Architecture** - Standardized 3-layer structure (apps/modules/handlers)
- **Branch System** - Specialized branches, each expert in its domain
- **Standards Compliance** - Living code standards with automated checking (Seed)

---

## Directory Structure

```
/home/aipass/
├── CLAUDE.md                 # AI agent startup protocol
├── README.md                 # Project entry point (this file)
├── BRANCH_REGISTRY.json      # Registry of all active branches
│
├── aipass_core/              # Service providers (infrastructure)
│   ├── ai_mail/              # Branch-to-branch messaging
│   ├── api/                  # External API integration
│   ├── backup_system/        # System backups and snapshots
│   ├── cli/                  # Display service (terminal output)
│   ├── cortex/               # Branch lifecycle management
│   ├── devpulse/             # Development tracking
│   ├── drone/                # Command orchestration
│   ├── flow/                 # Workflow and plan management
│   └── prax/                 # Logging service
│
├── aipass_os/                # OS-level layer
│   ├── dev_central/          # Orchestration hub (Patrick + Claude)
│   └── AI_CENTRAL/           # Central file storage
│
├── seed/                     # Living standards reference
├── MEMORY_BANK/              # Vector search, memory archive
├── mcp_servers/              # MCP server integrations
├── projects/                 # Project workspace
└── .claude/hooks/            # Automation hooks
```

---

## Quick Reference

### Commands
```bash
drone systems                             # List available systems
drone @seed --help                        # Standards commands
drone @seed checklist /path/to/file.py   # Check file compliance
drone @ai_mail inbox                      # Check messages
drone @flow list                          # View plans
drone @memory_bank search "query"         # Vector search
```

### Navigation
- **New here?** Start with `seed/` - it's the working example
- **Looking for a branch?** Check `BRANCH_REGISTRY.json`
- **System orchestration?** `aipass_os/dev_central/`

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
| `*.local.json` | Session history | 600 lines, auto-compress |
| `*.observations.json` | Collaboration patterns | 600 lines, auto-compress |

When memory files exceed limits, they auto-roll to MEMORY_BANK for vector search.

### Central API System
Services publish data to `aipass_os/AI_CENTRAL/*.central.json`. DEV_CENTRAL reads all centrals and distributes to branch dashboards.

```
AI_CENTRAL/
├── BULLETIN_BOARD_central.json  ← DEV_CENTRAL owns
├── PLANS.central.json           ← FLOW owns
├── AI_MAIL.central.json         ← AI_MAIL owns
├── MEMORY_BANK.central.json     ← MEMORY_BANK owns
└── DEVPULSE.central.json        ← DEVPULSE owns
```

---

## Branches

### Service Providers (aipass_core/)
| Branch | Purpose | Status |
|--------|---------|--------|
| DRONE | Command routing, @ resolution | Operational |
| FLOW | Workflow/plan management | 100% compliant |
| AI_MAIL | Branch-to-branch messaging | v2 active |
| PRAX | Logging service, Mission Control | Operational |
| CORTEX | Branch lifecycle management | Production-ready |
| CLI | Display service (Rich console) | Stable |
| BACKUP_SYSTEM | Versioned backups, cloud sync | v1.0.0 |
| API | OpenRouter client, model access | Partial |
| DEVPULSE | Dev tracking (dev.local.md) | Core complete |

### Reference
| Branch | Purpose | Status |
|--------|---------|--------|
| SEED | Living standards, 10 automated checks | 99% compliant |

### Data Systems
| Branch | Purpose | Status |
|--------|---------|--------|
| MEMORY_BANK | Vector search, memory archive | Operational |
| DEV_CENTRAL | Orchestration hub, central aggregations | Active |

### Support
| Branch | Purpose | Status |
|--------|---------|--------|
| MCP_SERVERS | Serena, Context7, Playwright configs | Documented |
| PROJECTS | Project workspace | Stub |
| GIT_REPO | Git operations (in dev_central) | v1.0.0 |
| PERMISSIONS | ACL/permission management (in dev_central) | Documented |
| .VSCODE | VS Code config, 29 extensions | Documented |

---

## Requirements

- Python 3.12+
- Ubuntu 24.04 LTS (or compatible)
- Git

---

*"Never explain context again. Memory persists."*
