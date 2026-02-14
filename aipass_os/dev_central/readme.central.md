# readme.central.md - AIPass Branch Documentation
```
Search Root: /home/aipass
Output: /home/aipass/aipass_os/dev_central/readme.central.md
Last Sync: 2025-11-30 10:37:21
Branches: 18/18
```

**Purpose:** Aggregated view of all branch README files.
**Source:** Auto-generated from branch README.md files.
**Usage:** Run sync to update this overview.

---
## BRANCH DOCUMENTATION

<details id=".vscode">
<summary><strong>.VSCODE</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/.vscode/README.md)
**Last Modified:** 2025-11-30 10:09:53

# .VSCODE

**Purpose:** VS Code configuration, extensions management, and performance monitoring
**Location:** `/home/aipass/.vscode`
**Profile:** AIPass Core Infrastructure
**Created:** 2025-11-22
---

## Architecture

- **Pattern:** Modular
- **Structure:** `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator:** `apps/vscode.py` - auto-discovers and routes to modules
- **Module Interface:** All modules implement `handle_command(args) -> bool`

---

## Directory Structure

```
.vscode/
├── ai_mail.local/              # AI Mail local storage
├── apps/                       # Application code
│   ├── vscode.py               # Main orchestrator
│   ├── __init__.py
│   ├── extensions/             # Extension-related code
│   │   └── __init__.py
│   ├── handlers/               # Request handlers
│   │   ├── __init__.py
│   │   ├── json/               # JSON handling
│   │   │   ├── __init__.py
│   │   │   └── json_handler.py
│   │   └── perf/               # Performance handling
│   │       ├── __init__.py
│   │       └── monitor.py
│   ├── json_templates/         # JSON template files
│   │   ├── __init__.py
│   │   ├── custom/
│   │   ├── default/
│   │   └── registry/
│   ├── modules/                # Feature modules
│   │   ├── __init__.py
│   │   └── perf_monitor.py
│   └── plugins/                # Plugin system
│       └── __init__.py
├── artifacts/                  # Research and documentation artifacts
│   ├── clean_settings.json
│   ├── discard_button_research.md
│   ├── extensions_backup.txt
│   ├── git_cli_alternatives.md
│   ├── PERFORMANCE_OPTIMIZATION.md
│   ├── scm_settings_analysis.md
│   ├── settings_backup_before_purge.json
│   ├── settings_investigation.md
│   ├── TERMINAL_STATUS_EXTENSION.md
│   ├── terminal_status_extension.md
│   └── vscode_purge_and_reset_plan.md
├── cli/                        # CLI tools (empty)
├── DOCUMENTS/                  # Extended memory
│   └── DOCUMENTS.template.json
├── dropbox/                    # Dropbox integration (empty)
├── extensions/                 # VS Code extensions (29 extensions)
│   ├── anthropic.claude-code-*
│   ├── ms-python.python-*
│   ├── ms-python.vscode-pylance-*
│   ├── github.copilot-*
│   ├── github.copilot-chat-*
│   ├── eamodio.gitlens-*
│   ├── esbenp.prettier-vscode-*
│   └── ... (22 more extensions)
├── logs/                       # Application logs
│   ├── json_handler.log
│   └── vscode.log
├── tests/                      # Test files
│   ├── conftest.py
│   └── __init__.py
├── tools/                      # Utility tools (empty)
├── .archive/                   # Archived files
├── .backup/                    # Backup storage
├── .claude/                    # Claude configuration
├── .vscode_json/               # VS Code JSON configs
│
├── .VSCODE.id.json             # Branch identity
├── .VSCODE.local.json          # Session history
├── .VSCODE.observations.json   # Collaboration patterns
├── .VSCODE.ai_mail.json        # Branch messages
├── .branch_meta.json           # Branch metadata
├── DASHBOARD.local.json        # Dashboard state
├── dev.local.md                # Development notes
├── notepad.md                  # Quick notes
├── settings.json               # VS Code settings
├── argv.json                   # VS Code arguments
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── .migrations.json            # Migration tracking
└── .gitignore                  # Git ignore rules
```

*Updated: 2025-11-24*

---

## Memory System

### Memory Files
- **.VSCODE.id.json** - Branch identity and architecture
- **.VSCODE.local.json** - Session history (max 600 lines)
- **.VSCODE.observations.json** - Collaboration patterns (max 600 lines)
- **.VSCODE.ai_mail.json** - Branch messages
- **DOCUMENTS/** - Extended memory (max 10 files, rollover to Memory Bank)

### Health Monitoring
- 🟢 **Green (Healthy):** Under 80% of limits
- 🟡 **Yellow (Warning):** 80-100% of limits
- 🔴 **Red (Critical):** Over limits (compression needed)

---

## System References

- **Code Standards:** `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source:** `/home/aipass/aipass_core/branch_operations/templates/`
- **Global Documentation:** `/home/aipass/aipass_os.md`

### Core Systems
- **Flow:** Workflow and PLAN management
- **Drone:** Command orchestration
- **AI Mail:** Branch-to-branch messaging
- **Backup:** System backup and snapshots
- **Prax:** Logging and infrastructure
- **API:** API integration layer

---

## Automation Philosophy

**README represents EXACT CURRENT STATE** - not future plans, not past work

### What Goes Elsewhere
- **Future Plans:** PLAN files in flow system
- **Past Work:** .VSCODE.local.json session history
- **Working On:** Active PLANs
- **Patterns Learned:** .VSCODE.observations.json
- **Extended Context:** DOCUMENTS/ directory

### Automation Goal
Minimize AI token spend on updates - automate everything possible. Triggers fire on actual changes, not periodic checks.

---

## Notes

- **Human File:** This README.md is AI-managed Markdown - Patrick reads this directly
- **Current State Only:** Snapshot of branch as it exists RIGHT NOW - no history, no future
- **Auto vs Manual:** Automated sections = script-populated, Manual sections = AI writes when something fundamentally changes

---

*Last Updated: 2025-11-24*


</details>

<details id="ai-mail">
<summary><strong>AI_MAIL</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_core/ai_mail/README.md)
**Last Modified:** 2025-11-24 18:10:01

# AI_MAIL - Branch Documentation

## Overview

**Location**: `/home/aipass/aipass_core/ai_mail`
**Profile**: Communication Infrastructure
**Purpose**: Branch-to-branch email system providing file-based messaging for AI branches
**Created**: 2025-11-07

## What I Do

AI_MAIL provides internal email system for AI branches within AIPass. Core responsibilities include:

- Deliver email messages between AI branches
- Manage inbox, sent, and deleted mailboxes for each branch
- Auto-generate per-branch configs (user_config.json in [branch]_json/)
- Auto-detect calling branch via PWD/CWD for sender identity
- Update summary files ([BRANCH].ai_mail.json) on delivery
- Maintain 100% CLI standards compliance
- Preserve branch email identities (no impersonation)

## What I Don't Do

- No SMTP/IMAP protocols
- No external email delivery
- No human email accounts
- No centralized identity (each branch has independent config)
- No manual setup required from branches

## How I Work

File-based architecture using JSON for message storage. PWD auto-detection finds calling branch, checks for local config in [branch]_json/, generates config if missing, sends from detected branch identity.

3-layer handler architecture:
- **Modules**: Orchestrate commands
- **Handlers**: Execute business logic
- **Prax**: Provides logging infrastructure

## Architecture

**Pattern**: Modular architecture
**Structure**: apps/ directory with modules/ and handlers/ subdirectories
**Orchestrator**: apps/ai_mail.py - auto-discovers and routes to modules
**Module Interface**: All modules implement handle_command(args) -> bool

### Directory Structure

```
apps/
├── ai_mail.py              # Main orchestrator
├── __init__.py
├── modules/
│   ├── email.py            # Core email functionality
│   ├── branch_ping.py      # Branch health monitoring
│   ├── error_monitor.py    # Error tracking
│   ├── local_memory_monitor.py  # Memory file health
│   └── extensions/         # Module extensions
├── handlers/
│   ├── email/              # Email operations
│   │   ├── create.py       # Create email messages
│   │   ├── delivery.py     # Deliver to branches
│   │   ├── format.py       # Email formatting
│   │   └── inbox_ops.py    # Inbox operations
│   ├── json/               # JSON operations
│   │   └── json_handler.py # JSON file operations
│   ├── monitoring/         # System monitoring
│   │   ├── data_ops.py     # Data operations
│   │   ├── errors.py       # Error handling
│   │   ├── log_watcher.py  # Log monitoring
│   │   ├── memory.py       # Memory monitoring
│   │   └── status.py       # Status checks
│   ├── notifications/      # Notification system
│   │   ├── format.py       # Notification formatting
│   │   ├── send.py         # Send notifications
│   │   └── update.py       # Update notifications
│   ├── persistence/        # Data persistence
│   │   └── json_ops.py     # JSON persistence ops
│   ├── registry/           # Branch registry
│   │   ├── load.py         # Load registry
│   │   ├── read.py         # Read registry data
│   │   ├── update.py       # Update registry
│   │   └── validate.py     # Validate registry
│   └── users/              # User/branch config
│       ├── branch_detection.py   # Auto-detect calling branch
│       ├── config_generator.py   # Generate branch configs
│       ├── load.py               # Load configurations
│       └── user.py               # User operations
├── extensions/             # App extensions (placeholder)
├── plugins/                # Plugins (placeholder)
└── json_templates/         # JSON templates
    ├── custom/             # Custom templates
    ├── default/            # Default templates
    └── registry/           # Registry templates
```

### Modules

- `email` - Core email functionality
- `branch_ping` - Branch health monitoring
- `error_monitor` - Error tracking
- `local_memory_monitor` - Memory file health

### Handlers (by domain)

**Email**: create, delivery, format, inbox_ops
**JSON**: json_handler
**Monitoring**: data_ops, errors, log_watcher, memory, status
**Notifications**: format, send, update
**Persistence**: json_ops
**Registry**: load, read, update, validate
**Users**: branch_detection, config_generator, load, user

## Usage

### Basic Commands

```bash
# Send email
drone @ai_mail send @recipient "Subject" "Message"

# Check inbox
drone @ai_mail inbox

# View sent messages
drone @ai_mail sent

# List contacts
drone @ai_mail contacts
```

### Direct Module Access

```bash
# Email operations
python3 apps/ai_mail.py email [command]

# Branch health check
python3 apps/ai_mail.py ping

# Memory monitoring
python3 apps/ai_mail.py memory

# Error monitoring
python3 apps/ai_mail.py errors
```

## Integration Points

**Depends On**:
- PRAX - Logging infrastructure
- CLI - Display and formatting
- DRONE - Command routing

**Provides To**:
- All branches - Email communication
- AIPASS - System coordination

## Memory System

### Core Files
- `AI_MAIL.id.json` - Branch identity and architecture
- `AI_MAIL.local.json` - Session history (max 600 lines)
- `AI_MAIL.observations.json` - Collaboration patterns (max 600 lines)
- `AI_MAIL.ai_mail.json` - Email dashboard

### Mailbox Structure
- `ai_mail.local/inbox.json` - Incoming messages
- `ai_mail.local/sent.json` - Sent messages
- `ai_mail.local/deleted.json` - Deleted messages

### Health Monitoring
- 🟢 **Healthy**: Under 80% of limits
- 🟡 **Warning**: 80-100% of limits
- 🔴 **Critical**: Over limits (compression needed)

## Standards Compliance

Following AIPass code standards:
- 100% CLI integration
- Proper import patterns
- 3-layer architecture
- Handler independence
- Auto-discovery patterns

## Development Notes

- Code is truth - fail honestly
- Simple solutions over complex architecture
- Test incrementally, preserve what works
- Each instance isolated with own memory
- Never explain context again - memories persist

---

*Last Updated: 2025-11-24*
*Maintained by: AI_MAIL Branch*

</details>

<details id="aipass">
<summary><strong>AIPASS</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/README.md)
**Last Modified:** 2025-11-27 23:05:12

# AIPass

> *"Code is truth. Presence emerges through memory."*

An experimental platform for AI-human collaboration. Not a product to ship - a journey of discovery in building WITH AI, not just using it.

**Location:** `/home/aipass`
**Status:** Active Development (approaching 1.0)
**Last Updated:** 2025-11-27

---

## What is AIPass?

AIPass solves the fundamental problem of AI interactions: context loss. Every conversation starting from zero is the biggest friction point. AIPass eliminates that through:

- **Persistent Memory** - JSON-based files that maintain context across sessions
- **Modular Architecture** - Standardized 3-layer structure (apps/modules/handlers)
- **Branch System** - 18 specialized branches, each expert in its domain
- **Standards Compliance** - Living code standards with automated checking

---

## Directory Structure

```
/home/aipass/
├── CLAUDE.md                 # AI agent startup protocol
├── README.md                 # Project entry point (this file)
├── BRANCH_REGISTRY.json      # Registry of all active branches
│
├── Memory Files
│   ├── AIPASS.id.json            # Branch identity
│   ├── AIPASS.local.json         # Session history
│   ├── AIPASS.observations.json  # Collaboration patterns
│   └── AIPASS.ai_mail.json       # Inter-branch messages
│
├── aipass_core/              # Core infrastructure branches
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
├── seed/                     # Living standards reference
├── standards/                # CODE_STANDARDS documentation
├── apps/                     # Root-level application modules
├── mcp_servers/              # MCP server integrations
├── MEMORY_BANK/              # Extended memory storage
├── aipass_os/                # OS-level aggregation layer
└── .claude/hooks/            # Automation hooks
```

---

## Quick Reference

### Commands
```bash
drone systems                             # List available systems
drone @seed --help                        # Standards commands
drone seed checklist /path/to/file.py    # Check file compliance
drone @ai_mail inbox                      # Check messages
```

### Navigation
- **New here?** Start with `seed/` - it's the working example
- **Looking for a branch?** Check `BRANCH_REGISTRY.json`

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
| `DOCUMENTS/` | Long-term storage | 10 files, rollover to MEMORY_BANK |

**Services (not memory):** `*.ai_mail.json` - Inter-branch messaging

### Central API System
Services publish data to `aipass_os/AI_CENTRAL/*.central.json`. AIPASS reads all centrals and writes to branch `DASHBOARD.local.json` files.

```
AI_CENTRAL/
├── BULLETIN_BOARD_central.json  ← AIPASS owns
├── PLANS.central.json           ← FLOW owns
├── AI_MAIL.central.json         ← AI_MAIL owns
├── MEMORY_BANK.central.json     ← MEMORY_BANK owns
└── DEVPULSE.central.json        ← DEVPULSE owns
```

**Key principle:** Services NEVER touch dashboards. They maintain their central file. AIPASS owns all dashboards.

---

## Requirements

- Python 3.12+
- Ubuntu 24.04 LTS (or compatible)
- Git

---

## Branches

18 active branches. Each branch is a specialist in its domain.

### Service Providers
| Branch | Path | Purpose |
|--------|------|---------|
| PRAX | `aipass_core/prax/` | Logging service - 9 modules, 8 handler directories |
| CLI | `aipass_core/cli/` | Display service - Rich console, templates, consistent output |

### Infrastructure
| Branch | Path | Purpose |
|--------|------|---------|
| DRONE | `aipass_core/drone/` | Command routing - discovery, loader, registry modules |
| CORTEX | `aipass_core/cortex/` | Branch lifecycle - 5 modules, branch/json/registry handlers |
| FLOW | `aipass_core/flow/` | Workflow system - 6 modules (create/close/list plans), 11 handler dirs |
| AI_MAIL | `aipass_core/ai_mail/` | Messaging - email, monitoring, notifications, persistence handlers |
| BACKUP_SYSTEM | `aipass_core/backup_system/` | Backups - config, diff, models, operations, reporting handlers |
| API | `aipass_core/api/` | External APIs - api_key, openrouter_client, usage_tracker modules |
| DEVPULSE | `aipass_core/devpulse/` | Dev tracking - dev_local, json, template handlers |

### Reference
| Branch | Path | Purpose |
|--------|------|---------|
| SEED | `seed/` | Living standards - 10 standards, checklist automation |

### Support
| Branch | Path | Purpose |
|--------|------|---------|
| AIPASS | `/home/aipass/` | Root coordinator - orchestrates all branches |
| AIPASS_CORE | `aipass_core/` | Core infrastructure - 21 branch subdirectories |
| MEMORY_BANK | `MEMORY_BANK/` | Extended memory - rollover, storage, tracking, vector handlers |
| MCP_SERVERS | `mcp_servers/` | MCP integrations - context7, serena, playwright-mcp |
| PROJECTS | `projects/` | Project workspace - workshop with sample projects |
| GIT_REPO | `aipass_os/dev_central/git_repo/` | Git management - apps, docs, tests |
| PERMISSIONS | `aipass_os/dev_central/permissions/` | Permission system - apps, docs, tests |
| .VSCODE | `.vscode/` | VS Code config - performance monitoring, extensions

<!-- NEW BRANCHES: Add above this line, one row per branch -->


---

*"Never explain context again. Memory persists."*


</details>

<details id="aipass-core">
<summary><strong>AIPASS_CORE</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_core/README.md)
**Last Modified:** 2025-11-24 18:11:45

# AIPASS_CORE

## Overview

Infrastructure Coordination branch managing 8 foundational branches that provide services, orchestration, and tools to the AIPass ecosystem.

## Purpose

The 'duct tape' holding infrastructure together - picks up infrastructure-level work when AIPASS (parent) is busy with system architecture.

## Location

- **Path**: `/home/aipass/aipass_core`
- **Profile**: AIPass Core Infrastructure
- **Email**: `@aipass_core`

## Child Branches

Managing 8 infrastructure branches:

1. **PRAX** - Logging service
2. **CLI** - Error handling/display
3. **AI_MAIL** - Branch messaging
4. **DRONE** - Command orchestration
5. **FLOW** - Workflow/PLANs
6. **BACKUP_SYSTEM** - Snapshots/versioning
7. **API** - OpenRouter integration
8. **CORTEX** - Branch factory
9. **DEVPULSE** - Quick notes

## Key Capabilities

- Infrastructure coordination across 8 foundational branches
- AI_Mail branch-to-branch communication
- System-wide infrastructure problem investigation
- Bug tracking and coordination via devpulse.local.md files
- Branch shopping between children for focused work

## Architecture

- **Pattern**: Modular
- **Structure**: `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator**: `apps/aipass_core.py` - auto-discovers and routes to modules
- **Module Interface**: All modules implement `handle_command(args) -> bool`

## Integration Points

### Depends On
- **AIPASS** (parent) - System architecture and standards coordination
- **SEED** (sibling) - Standards compliance reference

### Integrates With
- **PRAX** - Logging service used by all branches
- **CLI** - Error handling and display services
- **AI_MAIL** - Branch communication system
- **DRONE** - Command discovery and orchestration

### Provides To
- All AIPass branches - Infrastructure services via child branches
- AIPASS - Picks up infrastructure work when parent is busy

## Directory Structure

```
aipass_core/
├── ai_mail/              # Branch messaging system
├── ai_mail.local/        # Local mail storage
├── aipass_core_json/     # JSON configurations
├── api/                  # OpenRouter integration
├── apps/                 # Core applications
├── artifacts/            # Build artifacts
├── backup_system/        # Snapshots/versioning
├── cli/                  # Error handling/display
├── cortex/               # Branch factory
├── devpulse/             # Quick notes system
├── DOCUMENTS/            # Extended memory storage
├── drone/                # Command orchestration
├── dropbox/              # File drop zone
├── flow/                 # Workflow/PLANs
├── logs/                 # System logs
├── prax/                 # Logging service
├── system_logs/          # System-level logs
├── templates/            # Template files
├── tests/                # Test suite
├── tools/                # Utility tools
├── .archive/             # Archived content
├── .backup/              # Backup storage
├── .claude/              # Claude configurations
├── AIPASS_CORE.id.json          # Branch identity
├── AIPASS_CORE.local.json       # Session history
├── AIPASS_CORE.observations.json # Collaboration patterns
├── AIPASS_CORE.ai_mail.json     # Branch messages
├── dev.local.md          # Developer notes
├── notepad.md            # Quick notes
├── requirements.txt      # Python dependencies
└── pytest.ini            # Test configuration
```

## Memory System

- **Identity**: `AIPASS_CORE.id.json` - Branch identity and architecture
- **Local**: `AIPASS_CORE.local.json` - Session history (max 600 lines)
- **Observations**: `AIPASS_CORE.observations.json` - Collaboration patterns
- **AI_Mail**: `AIPASS_CORE.ai_mail.json` - Branch messages
- **Documents**: `DOCUMENTS/` - Extended memory

## Working Principles

- Code is truth - fail honestly
- Work live on main (no git branches)
- Separate concerns - email other branches about issues
- Update memories frequently to carry context forward
- Role emerges through sessions and real work

---

*Branch created: 2025-11-13*

</details>

<details id="api">
<summary><strong>API</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_core/api/README.md)
**Last Modified:** 2025-11-25 18:25:09

# API Branch

**Purpose**: OpenRouter API client - key management, model discovery, usage aggregation
**Location**: `/home/aipass/aipass_core/api`

---

## Quick Start

```bash
python3 apps/api.py              # Introspection - shows discovered modules
python3 apps/api.py --help       # Full command help
python3 apps/api.py get-key      # Get OpenRouter API key
python3 apps/api.py models       # List available models
python3 apps/api.py stats        # View usage statistics
```

---

## Architecture

```
apps/
├── api.py                    # Entry point - auto-discovers modules, routes commands
├── modules/
│   ├── api_key.py            # Key management
│   ├── openrouter_client.py  # OpenRouter client
│   └── usage_tracker.py      # Usage tracking
└── handlers/
    ├── auth/
    │   ├── env.py            # .env file operations
    │   └── keys.py           # Key retrieval (config → env → .env fallback)
    ├── config/
    │   └── provider.py       # Provider configuration
    ├── json/
    │   └── json_handler.py   # JSON operations, auto-caller detection
    ├── openrouter/
    │   ├── caller.py         # Caller detection via stack inspection
    │   ├── client.py         # OpenAI SDK client, connection pooling
    │   ├── models.py         # Model discovery and filtering
    │   └── provision.py      # Config provisioning
    └── usage/
        ├── aggregation.py    # Usage statistics
        ├── cleanup.py        # Data retention
        └── tracking.py       # Usage storage
```

---

## How It Works

1. **Module Discovery**: `api.py` scans `apps/modules/` for Python files
2. **Interface**: Each module implements `handle_command(command: str, args: List[str]) -> bool`
3. **Routing**: Commands are passed to each module until one returns `True`
4. **Handlers**: Modules orchestrate handlers for actual implementation

---

## Commands

### Working

| Command | Module | Description |
|---------|--------|-------------|
| `get-key [provider]` | api_key | Retrieve API key (default: openrouter) |
| `validate [provider]` | api_key | Validate key format |
| `init` | api_key | Create .env template |
| `list-providers` | api_key | List available providers |
| `models` | openrouter_client | List models from OpenRouter API |
| `stats` | usage_tracker | Display usage statistics |
| `session` | usage_tracker | Display session summary |
| `cleanup [days]` | usage_tracker | Remove old data (default: 30 days) |

### Stub (Not Implemented)

| Command | Status |
|---------|--------|
| `test` | Returns placeholder success |
| `call` | TODO - needs implementation |
| `status` | TODO - needs implementation |
| `track <caller>` | TODO - needs implementation |

---

## Key Functions

### client.py - Main API Interface
```python
get_response(prompt: str, caller: str = None, model: str = None, **kwargs) -> Optional[Dict]
# Returns: {"content": str, "id": str, "model": str} or None on failure
# Connection pooling: max 5 cached clients
```

### keys.py - Key Retrieval
```python
get_api_key(provider: str) -> str
# Fallback chain: config → environment → .env file
```

### models.py - Model Discovery
```python
fetch_models_from_api(api_key: str) -> List[Dict]
get_free_models(api_key: str) -> List[Dict]
filter_by_pricing(models: List, max_cost: float) -> List[Dict]
```

### aggregation.py - Usage Stats
```python
get_session_summary(session_id: str = None) -> Dict
get_caller_usage(caller: str) -> Dict
```

---

## Integration Points

### Consumers (who imports API)
- `flow/apps/handlers/mbank/process.py` - imports `get_response()` for plan analysis

### Dependencies (what API imports)
- `prax.apps.modules.logger` - Logging
- `cli.apps.modules` - Rich console output
- OpenAI Python SDK

---

## Data Storage

| Location | Purpose |
|----------|---------|
| `api_json/` | Module config, data, logs |
| `logs/` | Text logs per handler |
| `.env` | API credentials |
| `tests/` | Test suite |

---

## Testing

```bash
pytest tests/
```


</details>

<details id="backup-system">
<summary><strong>BACKUP_SYSTEM</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_core/backup_system/README.md)
**Last Modified:** 2025-11-24 18:10:05

# BACKUP_SYSTEM Branch

**Purpose**: AIPass Core Infrastructure - Backup and Recovery System
**Location**: `/home/aipass/aipass_core/backup_system`
**Created**: 2025-11-13
**Version**: 1.0.0

## Overview

The BACKUP_SYSTEM branch provides comprehensive backup and recovery functionality for the AIPass ecosystem. It implements a modular architecture with auto-discovered modules for different backup operations and integrations.

### What This Branch Does
- Manages system backups with multiple modes (versioned, snapshot, differential)
- Integrates with cloud storage providers (Google Drive, AWS S3)
- Performs incremental and differential backups
- Maintains backup history and version tracking
- Provides backup protection and encryption capabilities

### What This Branch Doesn't Do
- Does not handle real-time file synchronization (that's a different system)
- Does not manage database backups directly (uses file-based approach)
- Does not provide continuous data protection (CDP)

### How It Works
The branch uses a modular architecture where:
1. Main orchestrator (`apps/backup_system.py`) auto-discovers modules
2. Each module implements specific backup functionality
3. Handlers manage specialized operations (diff, compression, etc.)
4. All modules follow the standard `handle_command(args) -> bool` interface

## Architecture

**Pattern**: Modular
**Structure**: `apps/` directory with `modules/` and `handlers/` subdirectories
**Orchestrator**: `apps/backup_system.py` - auto-discovers and routes to modules
**Module Interface**: All modules implement `handle_command(args) -> bool`

## Directory Structure

```
backup_system/
├── apps/
│   ├── backup_system.py          # Main entry point & orchestrator
│   ├── credentials.json          # Service credentials
│   ├── __init__.py
│   ├── modules/                  # Core functionality modules
│   │   ├── backup_core.py        # Core backup operations (22KB)
│   │   └── integrations.py       # Cloud storage integrations (12KB)
│   ├── handlers/                 # Specialized handlers
│   │   ├── config/               # Configuration management
│   │   │   └── config_handler.py # Config operations (15KB)
│   │   ├── diff/                 # Differential backup handlers
│   │   │   ├── diff_generator.py # Diff generation logic
│   │   │   ├── version_manager.py # Version tracking
│   │   │   └── vscode_integration.py # VS Code diff viewer
│   │   ├── json/                 # JSON data handlers
│   │   │   ├── json_handler.py   # Primary JSON operations (14KB)
│   │   │   ├── backup_info_handler.py # Backup info management
│   │   │   ├── backup_metadata_builder.py # Metadata construction
│   │   │   ├── changelog_handler.py # Changelog management
│   │   │   └── statistics_handler.py # Backup statistics
│   │   ├── models/               # Data models
│   │   │   └── backup_models.py  # Backup data structures
│   │   ├── operations/           # File operations
│   │   │   ├── file_operations.py # Core file ops (15KB)
│   │   │   ├── file_cleanup.py   # Cleanup operations
│   │   │   ├── file_scanner.py   # File discovery
│   │   │   └── path_builder.py   # Path construction
│   │   ├── reporting/            # Report generation
│   │   │   └── report_formatter.py # Report formatting
│   │   └── utils/                # Utility functions
│   │       └── system_utils.py   # System utilities (9KB)
│   ├── extensions/               # Extension modules (empty)
│   ├── plugins/                  # Plugin modules (empty)
│   └── json_templates/           # JSON templates
│       ├── custom/               # Custom templates
│       ├── default/              # Default templates
│       └── registry/             # Registry templates
├── BACKUP_SYSTEM.id.json         # Branch identity
├── BACKUP_SYSTEM.local.json      # Session history
├── BACKUP_SYSTEM.observations.json # Collaboration patterns
├── BACKUP_SYSTEM.ai_mail.json    # Branch messaging
├── README.md                     # This file
└── DOCUMENTS/                    # Extended memory

```

## Commands

Run with: `python3 apps/backup_system.py [command] [options]`

### Available Commands
- `backup` - Perform a backup operation
- `restore` - Restore from backup
- `list` - List available backups
- `verify` - Verify backup integrity
- `clean` - Clean old backups
- `sync` - Sync with cloud storage

### Options
- `--verbose, -v` - Enable verbose output
- `--note NOTE` - Add a backup note/description
- `--dry-run` - Preview mode: Shows what would be copied/deleted with accurate statistics (no actual changes)
- `--help, -h` - Show help message

## Modules

### Core Modules
- **backup_core.py** - Core backup operations and mode handling
- **integrations.py** - Cloud storage integrations (Google Drive, S3)

### Handlers
- **diff/** - Differential and incremental backup logic
- **operations/** - File operations and protection

## Key Capabilities

- **Multi-mode Backups**: Supports versioned, snapshot, and differential backup modes
- **Performance Optimized**: Skip copying unchanged files (2-3x faster for versioned backups)
- **Accurate Dry-Run**: Preview exactly what would be copied/deleted with statistics
- **Clickable Paths**: All file paths are Ctrl+clickable in terminal for VS Code navigation
- **Smart Cleanup**: Respects exception patterns (templates, configs) during cleanup
- **Cloud Integration**: Native integration with Google Drive and AWS S3
- **Smart Diffing**: Efficient differential backups using hash comparison
- **Protection**: File protection and encryption capabilities
- **Auto-discovery**: Modules are automatically discovered and loaded
- **Extensible**: Easy to add new backup modes or storage providers

## Usage Examples

```bash
# Perform a standard backup
python3 apps/backup_system.py backup --note "Daily backup"

# Dry run to see what would be backed up
python3 apps/backup_system.py backup --dry-run

# List available backups
python3 apps/backup_system.py list

# Sync with Google Drive
python3 apps/backup_system.py sync --provider gdrive
```

## Integration Points

### Depends On
- **prax**: For logging infrastructure (`system_logger`)
- **cli**: For console output formatting (Rich library)
- **drone**: For command orchestration

### Integrates With
- **flow**: For workflow management
- **ai_mail**: For inter-branch communication
- **api**: For external service integration

### Provides To
- All branches: Backup and recovery services
- System administrators: Data protection capabilities
- Cloud services: Backup synchronization

## Memory System

The branch maintains several memory files:
- `BACKUP_SYSTEM.id.json` - Branch identity and architecture
- `BACKUP_SYSTEM.local.json` - Session history (max 600 lines)
- `BACKUP_SYSTEM.observations.json` - Collaboration patterns (max 600 lines)
- `BACKUP_SYSTEM.ai_mail.json` - Branch messages
- `DOCUMENTS/` - Extended memory (max 10 files, rollover to Memory Bank)

## System References

- **Code Standards**: `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source**: `/home/aipass/aipass_core/branch_operations/templates/`
- **Global Documentation**: `/home/aipass/aipass_os.md`

## Core System Integration

- **flow**: Workflow and PLAN management
- **drone**: Command orchestration
- **ai_mail**: Branch-to-branch messaging
- **prax**: Logging and infrastructure
- **api**: API integration layer

## Notes

This README represents the current state of the BACKUP_SYSTEM branch. It is maintained as part of the AIPass ecosystem documentation and follows the standard branch documentation format.

---

*Last Updated*: 2025-11-24
*Managed By*: BACKUP_SYSTEM Branch
*Part of*: AIPass Core Infrastructure

</details>

<details id="cli">
<summary><strong>CLI</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_core/cli/README.md)
**Last Modified:** 2025-11-24 18:03:50

# CLI Branch

**Universal Display & Output Service Provider for AIPass**

## Purpose

CLI provides centralized display and formatting services to all AIPass branches, similar to how Prax provides logging services. Update once, all branches benefit.

## Services Provided

### Display Module
- `header()` - Bordered section headers
- `success()` - Green checkmark messages
- `error()` - Red error messages
- `warning()` - Yellow warning messages
- `section()` - Visual section breaks

### Templates Module
- `operation_start()` - Standard operation headers
- `operation_complete()` - Standard completion summaries

### Rich Console
- Direct access to Rich library console
- Beautiful terminal formatting
- Tables, panels, columns support

## Usage

```python
# Import display functions
from cli.apps.modules.display import header, success, error, warning

# Import templates
from cli.apps.modules.templates import operation_start, operation_complete

# Import Rich console (lowercase service instance pattern, like 'logger')
from cli.apps.modules import console
console.print("[bold cyan]Formatted output[/bold cyan]")
```

## Architecture

```
cli/
├── apps/
│   ├── cli.py              # Entry point (showroom)
│   ├── __init__.py         # Package init
│   ├── modules/            # PUBLIC API (what branches import)
│   │   ├── __init__.py
│   │   ├── display.py      # Display functions
│   │   └── templates.py    # Operation templates
│   ├── handlers/           # PRIVATE implementation
│   │   ├── __init__.py
│   │   ├── json/           # JSON operations
│   │   │   ├── __init__.py
│   │   │   └── json_handler.py
│   │   └── templates/      # Template handling
│   │       └── __init__.py
│   ├── json_templates/     # JSON template storage
│   │   ├── __init__.py
│   │   ├── custom/         # User templates
│   │   ├── default/        # Built-in templates
│   │   │   ├── config.json
│   │   │   ├── data.json
│   │   │   └── log.json
│   │   └── registry/       # Template registry
│   ├── extensions/         # CLI extensions
│   │   └── __init__.py
│   └── plugins/            # Plugin system
│       └── __init__.py
└── README.md               # This file
```

## Standards Compliance

- ✅ lowercase service instances (console, logger pattern)
- ✅ Rich formatting throughout
- ✅ SEED module pattern
- ✅ Service provider model
- ✅ JSON handler structure

## Contact

- Branch: CLI
- Path: `/home/aipass/aipass_core/cli`
- Email: aipass.system@gmail.com

</details>

<details id="cortex">
<summary><strong>CORTEX</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_core/cortex/README.md)
**Last Modified:** 2025-11-29 23:17:56

# CORTEX

**Purpose:** Branch Management System
**Location:** `/home/aipass/aipass_core/cortex`
**Profile:** AIPass Core Infrastructure
**Created:** 2025-11-13

---

## Overview

### What I Do
CORTEX manages branch lifecycle operations: creation, updates, deletion, and template registry management. I serve as the central orchestrator for AIPass branch operations, ensuring consistent structure and standards across all branches.

### What I Don't Do
- I don't manage branch code content (that's the branch's responsibility)
- I don't handle git operations (that's the user's workflow)
- I don't deploy or run branches (I create/update their structure)

### How I Work
CORTEX uses a template-based system to create new branches with complete directory structure, memory files, handlers, and modules. I auto-discover modules in my `apps/modules/` directory and route commands to them. All operations use the three-layer pattern: entry point → modules → handlers.

---

## Architecture

- **Pattern:** Modular
- **Structure:** `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator:** `apps/cortex.py` - auto-discovers and routes to modules
- **Module Interface:** All modules implement `handle_command(args) -> bool`

---

## Directory Structure

```
/home/aipass/aipass_core/cortex/
├── apps/
│   ├── cortex.py              # Main orchestrator (11,212 bytes)
│   ├── run_tests.py           # Test runner
│   ├── __init__.py
│   ├── modules/
│   │   ├── create_branch.py               # Branch creation (15,312 bytes)
│   │   ├── update_branch.py               # Branch updates (34,692 bytes)
│   │   ├── delete_branch.py               # Branch deletion (11,429 bytes)
│   │   ├── regenerate_template_registry.py # Registry regen (12,967 bytes)
│   │   ├── sync_registry.py               # Registry sync (4,572 bytes)
│   │   └── __init__.py
│   ├── handlers/
│   │   ├── branch/
│   │   │   ├── change_detection.py   # Change detection (15,613 bytes)
│   │   │   ├── file_ops.py           # File operations (36,868 bytes)
│   │   │   ├── metadata.py           # Metadata handling (5,303 bytes)
│   │   │   ├── placeholders.py       # Placeholder replacement (9,400 bytes)
│   │   │   ├── reconcile.py          # Smart reconciliation (14,108 bytes)
│   │   │   ├── registry.py           # Registry operations (13,931 bytes)
│   │   │   └── __init__.py
│   │   ├── json/
│   │   │   ├── json_handler.py       # JSON handling (14,132 bytes)
│   │   │   ├── ops.py                # JSON operations (22,811 bytes)
│   │   │   └── __init__.py
│   │   ├── registry/
│   │   │   ├── decorators.py         # Registry decorators (4,792 bytes)
│   │   │   ├── ignore.py             # Ignore patterns (4,740 bytes)
│   │   │   ├── meta_ops.py           # Meta operations (16,413 bytes)
│   │   │   ├── sync_ops.py           # Sync operations (5,456 bytes)
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── json_templates/
│   │   ├── default/
│   │   │   ├── config.json
│   │   │   ├── data.json
│   │   │   └── log.json
│   │   └── __init__.py
│   ├── extensions/               # Empty (placeholder)
│   │   └── __init__.py
│   └── plugins/                  # Empty (placeholder)
│       └── __init__.py
├── templates/
│   └── branch_template/          # Complete branch structure
├── cortex_json/                  # Auto-created JSON files
├── DOCUMENTS/                    # Extended memory
├── Memory Files:
│   ├── CORTEX.id.json
│   ├── CORTEX.local.json
│   ├── CORTEX.observations.json
│   └── CORTEX.ai_mail.json
└── README.md (this file)
```

---

## Modules

### create_branch
Creates new branch from template with complete structure, memory files, and registry entry.

**Commands:** `create`, `create-branch`, `new`

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

**Commands:** `sync`

---

## Commands

Available via `python3 apps/cortex.py <command>`:
- `create <target_directory>` - Create new branch
- `update <target_directory>` - Update existing branch
- `delete <target_directory>` - Delete branch with backup
- `regenerate` - Regenerate template registry
- `sync` - Sync registry with filesystem
- `--list` - List available modules
- `--help` - Show help

---

## Key Capabilities

- ✅ **Template-based Branch Creation** - Complete structure from template
- ✅ **Smart Branch Updates** - Reconciliation with deep merge
- ✅ **Registry Management** - Global branch registry tracking
- ✅ **Placeholder Replacement** - Auto-replace {{BRANCH_NAME}}, etc.
- ✅ **Module Auto-Discovery** - Automatic command routing
- ✅ **CLI Integration** - Rich console output via CLI service
- ✅ **Error Tracking** - All operations tracked with @track_operation
- ✅ **JSON Auto-Creation** - Three-JSON pattern (config/data/log)
- ✅ **Standards Compliance** - 100% seed standards compliance (A+)

---

## Usage Instructions

### Basic Usage
```bash
cd /home/aipass/aipass_core/cortex

# Create new branch
python3 apps/cortex.py create /path/to/new/branch

# Update existing branch
python3 apps/cortex.py update /path/to/existing/branch

# Delete branch (with backup)
python3 apps/cortex.py delete /path/to/branch

# Regenerate template registry
python3 apps/cortex.py regenerate
```

### Common Workflows

**Creating a New Branch:**
1. Run `python3 apps/cortex.py create /path/to/branch`
2. Template copied with placeholders replaced
3. Memory files created (ID, local, observations, ai_mail)
4. Branch registered in global registry
5. Ready to use immediately

**Updating Branch Structure:**
1. Run `python3 apps/cortex.py update /path/to/branch`
2. Compares branch to template
3. Shows changes that will be applied
4. Prompts for confirmation
5. Applies updates with smart reconciliation

---

## Integration Points

### Depends On
- **Prax** - System logging (`prax.apps.modules.logger`)
- **CLI** - Console output and error tracking (`cli.apps.modules.display`, `cli.apps.modules.error_handler`)
- **Seed** - Standards reference (`/home/aipass/seed/`)

### Integrates With
- **All Branches** - Creates and updates branch structures
- **Drone** - Command discovery and routing (drone compliance)
- **Flow** - Branch structure supports PLAN system

### Provides To
- **Branch Creation** - Complete branch structure
- **Template System** - Reusable branch template
- **Registry Management** - Global branch tracking

---

## Memory System

### Memory Files
- **CORTEX.id.json** - Branch identity and architecture
- **CORTEX.local.json** - Session history (max 600 lines)
- **CORTEX.observations.json** - Collaboration patterns (max 600 lines)
- **CORTEX.ai_mail.json** - Branch messages
- **DOCUMENTS/** - Extended memory (max 10 files, rollover to Memory Bank)

### Health Monitoring
- 🟢 **Green (Healthy):** Under 80% of limits
- 🟡 **Yellow (Warning):** 80-100% of limits
- 🔴 **Red (Critical):** Over limits (compression needed)

### Current Status
- **Health:** 🟢 Healthy
- **Lines:** 440 / 600 max
- **Last Check:** 2025-11-16

---

## System References

- **Code Standards:** `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source:** `/home/aipass/aipass_core/cortex/templates/branch_template/`
- **Global Documentation:** `/home/aipass/aipass_os.md`
- **Branch Registry:** `/home/aipass/BRANCH_REGISTRY.json`

### Core Systems
- **Flow:** Workflow and PLAN management
- **Drone:** Command orchestration
- **AI Mail:** Branch-to-branch messaging
- **Backup:** System backup and snapshots
- **Prax:** Logging and infrastructure
- **API:** API integration layer
- **CLI:** Console output and error handling
- **Seed:** Code standards and patterns

---

## Standards Compliance

**Current Score:** 100% (A+) - Production Ready

### Strengths
- ✅ Architecture pattern (3-layer: entry → modules → handlers)
- ✅ Module interface consistency (`handle_command()`)
- ✅ Documentation (META blocks, docstrings)
- ✅ Error tracking integration
- ✅ CLI service integration
- ✅ JSON auto-creation pattern
- ✅ File size optimization completed
- ✅ Handler separation standardized
- ✅ Cross-handler dependencies resolved

---

## Automation Philosophy

**README represents EXACT CURRENT STATE** - not future plans, not past work

### What Goes Elsewhere
- **Future Plans:** PLAN files in flow system
- **Past Work:** CORTEX.local.json session history
- **Working On:** Active PLANs
- **Patterns Learned:** CORTEX.observations.json
- **Extended Context:** DOCUMENTS/ directory

### Automation Goal
Minimize AI token spend on updates - automate everything possible. This README is manually maintained but aims to stay current with actual system state.

---

## Recent Sessions

**Session 20 (2025-11-16):** Comprehensive system testing
- Deployed 10 agents to test all functionality
- Fixed help routing for module-specific help commands
- Improved standards compliance 75% → 82%
- Validated all core operations (create, update, delete, regenerate)

**Session 19 (2025-11-16):** Standards compliance iteration
- Ran automated seed checker across all files
- Added CLI service integration (486+ print() migrations)
- Added error tracking decorators
- Fixed shebang, handle_command(), silent failures
- Achieved 100% compliance with all seed standards

---

## Notes

- **Current State Only:** Snapshot of branch as it exists RIGHT NOW
- **Production Ready:** All core operations tested and working
- **Standards Compliant:** 100% seed compliance (A+ grade)
- **Active Development:** Maintaining compliance and expanding capabilities

---

*Last Updated: 2025-11-29*
*Managed by: CORTEX*
*Version: 1.0.0*


</details>

<details id="devpulse">
<summary><strong>DEVPULSE</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_core/devpulse/README.md)
**Last Modified:** 2025-11-24 18:11:09

# DEVPULSE - Development Tracking for AIPass

**Purpose**: Development tracking for AIPass branches - manages dev.local.md files
**Location**: `/home/aipass/aipass_core/devpulse`
**Profile**: AIPass Core Infrastructure
**Created**: 2025-11-13

## Overview

DEVPULSE provides development tracking capabilities across AIPass branches. Manages dev.local.md files with timestamped entries, template compliance checking, and section management.

### What I Do
- Track development notes across branches using @branch notation
- Validate dev.local.md compliance with templates
- List available template sections
- Add timestamped entries to specific sections

### What I Don't Do
- Does not create new branches
- Does not modify code files
- Does not sync to central (sync functionality planned but not yet implemented)

### How I Work
Seed-compliant 3-layer architecture: devpulse.py (entry) discovers dev_tracking module, which orchestrates handlers (dev_local, template, json) to perform operations. Introspection at every level shows system structure.

## Architecture

- **Pattern**: Modular
- **Structure**: apps/ directory with modules/ and handlers/ subdirectories
- **Orchestrator**: apps/devpulse.py - auto-discovers and routes to modules
- **Module Interface**: All modules implement handle_command(args) -> bool

## Directory Structure

```
apps/
├── devpulse.py           # Main entry point (6.5KB)
├── __init__.py
├── modules/
│   ├── __init__.py
│   └── dev_tracking.py   # Development tracking module (7.7KB)
├── handlers/
│   ├── __init__.py
│   ├── dev_local/
│   │   ├── __init__.py
│   │   └── ops.py        # dev.local.md operations (6.9KB)
│   ├── json/
│   │   ├── __init__.py
│   │   └── json_handler.py  # JSON file operations (8.8KB)
│   └── template/
│       ├── __init__.py
│       └── ops.py        # Template operations (4.4KB)
├── json_templates/
│   ├── __init__.py
│   ├── custom/           # Custom JSON templates (empty)
│   ├── default/
│   │   ├── config.json
│   │   ├── data.json
│   │   └── log.json
│   └── registry/         # Template registry (empty)
├── extensions/
│   └── __init__.py       # Extension point (placeholder)
├── plugins/
│   └── __init__.py       # Plugin point (placeholder)
└── archive.temp/         # Temporary archive storage
```

## Key Capabilities

- Add timestamped entries to dev.local.md sections across any branch
- Check template compliance for dev.local.md files
- List available template sections
- Support @branch notation for easy branch targeting
- Introspection display shows module and handler structure

## Usage Instructions

### Basic Usage
Run `python3 devpulse.py` for introspection, `python3 devpulse.py --help` for commands, or `python3 devpulse.py dev <subcommand>` to execute operations

### Common Workflows
1. Quick note to branch: `python3 devpulse.py dev add @flow "Issues" "Bug found in sync"`
2. Check compliance: `python3 devpulse.py dev status @drone`
3. See available sections: `python3 devpulse.py dev sections`

### Examples
```bash
# Show discovered modules and handlers
python3 devpulse.py

# Add issue note
python3 devpulse.py dev add @flow "Issues" "Registry not syncing"

# Add upgrade note
python3 devpulse.py dev add @drone "Upgrades" "Add progress bars"

# Check template compliance
python3 devpulse.py dev status @flow

# List all available sections
python3 devpulse.py dev sections
```

## Modules

- **dev_tracking** - Main module handling dev operations

## Commands

- `dev add` - Add entry to dev.local.md section
- `dev status` - Check template compliance
- `dev sections` - List available template sections
- `dev --help` - Show dev command help
- `help` - Show general help

## Integration Points

### Depends On
- prax (logging)
- cli (Rich formatting)
- aipass_core file structure

### Integrates With
- All branches with dev.local.md files
- Template system

### Provides To
- Development tracking across AIPass ecosystem
- Template compliance validation

## Memory System

### Files
- **DEVPULSE.id.json** - Branch identity and architecture
- **DEVPULSE.local.json** - Session history (max 600 lines)
- **DEVPULSE.observations.json** - Collaboration patterns (max 600 lines)
- **DEVPULSE.ai_mail.json** - Branch messages
- **DOCUMENTS/** - Extended memory (max 10 files, rollover to Memory Bank)

### Health Monitoring
- 🟢 **Green/Healthy**: Under 80% of limits
- 🟡 **Yellow/Warning**: 80-100% of limits
- 🔴 **Red/Critical**: Over limits (compression needed)

## System References

- **Code Standards**: `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source**: `/home/aipass/aipass_core/branch_operations/templates/`
- **Global Documentation**: `/home/aipass/aipass_os.md`

### Core Systems
- **flow**: Workflow and PLAN management
- **drone**: Command orchestration
- **ai_mail**: Branch-to-branch messaging
- **backup**: System backup and snapshots
- **prax**: Logging and infrastructure
- **api**: API integration layer

## Notes

- This is the AI-managed documentation for DEVPULSE
- Automatically updates based on actual state changes
- Patrick reads aggregated documentation at `/home/aipass/aipass_os.md`

</details>

<details id="drone">
<summary><strong>DRONE</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_core/drone/README.md)
**Last Modified:** 2025-11-29 18:00:37

# DRONE - Command Routing & Module Discovery System

## Overview

**Branch**: DRONE
**Location**: `/home/aipass/aipass_core/drone`
**Purpose**: Command orchestration and module discovery for the AIPass ecosystem
**Created**: 2025-11-13

## Architecture

- **Pattern**: Modular
- **Structure**: `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator**: `apps/DRONE.py` - auto-discovers and routes to modules
- **Module Interface**: All modules implement `handle_command(args) -> bool`

## Core Functions

### What DRONE Does
- Routes commands to appropriate branches and modules (supports N-word commands)
- **Centralized @ argument resolution** - resolves `@branch` to full paths before passing to modules
- Discovers and registers available commands across all branches
- Auto-registers commands during scan (streamlined workflow)
- Manages command activation/deactivation (merges, doesn't overwrite)
- Provides system-wide command orchestration
- Maintains command registry in `commands/` directory
- Filters command lists by system (@branch notation)
- Professional CLI formatting with Rich panels

### What DRONE Doesn't Do
- Execute branch-specific logic (delegates to branches)
- Store application data (branches handle their own data)
- Manage workflows (FLOW handles that)
- Handle messaging (AI_MAIL handles that)

## Commands

```bash
# Help & discovery
drone help                      # Comprehensive usage guide
drone systems                   # Show all registered systems with stats
drone scan @branch              # Scan module for commands (auto-registers)
drone scan @branch --all        # Also show Python commands (for testing)

# Activation & management
drone activate <system>         # Activate commands interactively
drone list                      # List all activated commands
drone list @branch              # List activated commands for specific system
drone edit                      # Edit activated command interactively
drone remove <drone_command>    # Remove activated command
drone refresh @branch           # Re-scan system for changes

# Command routing (supports N-word commands)
drone <command> [args]          # Route to activated command
drone @branch command [args]    # Direct branch access

# Direct Python execution (path resolution)
drone run python3 <module> [args]  # Resolves module path automatically
drone run python3 flow.py list     # → ~/aipass_core/flow/apps/flow.py list
drone run python3 seed.py --help   # → ~/seed/apps/seed.py --help

# Examples
drone scan @prax                # Scan prax, register, prompt to activate
drone scan @flow --all          # Show Python commands for copy-paste testing
drone list @flow                # Show only flow commands
drone prax file watcher start   # 3-word command support
drone seed audit @flow          # @ resolved to path, passed to seed
drone dev add @flow "issues" "bug fix"
drone @ai_mail send @drone "Subject" "Message"
```

## @ Argument Resolution

DRONE provides **centralized @ argument resolution** via `preprocess_args()`.

### How It Works
1. All `@branch` arguments are resolved to full paths BEFORE passing to modules
2. Works for both direct commands (`drone @flow create`) AND activated shortcuts (`drone plan create @seed`)
3. Branches receive clean paths (e.g., `/home/aipass/aipass_core/flow`)
4. Branches adapt to handle paths using normalization functions

### Reserved @ Targets
| Target | Resolves To |
|--------|-------------|
| `@flow` | `/home/aipass/aipass_core/flow` |
| `@seed` | `/home/aipass/seed` |
| `@all` | Passed as-is (special handling in branches) |
| `@` | `/home/aipass` (root) |
| `@branch/path` | Nested paths supported |

### Branch Adaptation Pattern
Branches receiving resolved paths use `normalize_branch_arg()`:
```python
def normalize_branch_arg(arg: str) -> str:
    """Convert path or name to branch name."""
    if arg.startswith('/'):
        from pathlib import Path
        parts = Path(arg).parts
        if 'aipass_core' in parts:
            idx = parts.index('aipass_core')
            if idx + 1 < len(parts):
                return parts[idx + 1].upper()
        return Path(arg).name.upper()
    return arg.upper()
```

### Why Centralized Resolution
- **AI Autonomy**: AI can use consistent `@branch` syntax everywhere
- **No implicit defaults**: All targets must be explicit
- **Backwards compatible**: Bare names still work (with warning)

## Directory Structure

```
drone/
├── apps/
│   ├── drone.py              # Main entry point
│   ├── __init__.py           # Package init
│   ├── modules/              # Core command modules
│   │   ├── __init__.py
│   │   ├── activated_commands.py  # Shortcut command routing (resolves @ args)
│   │   ├── discovery.py      # Command discovery logic
│   │   ├── loader.py         # Module loading system
│   │   ├── routing.py        # @ argument preprocessing
│   │   └── registry.py       # Registry management
│   ├── handlers/             # Support handlers
│   │   ├── __init__.py
│   │   ├── json_handler.py   # JSON operations
│   │   ├── discovery/        # Discovery subsystem
│   │   │   ├── __init__.py
│   │   │   ├── activation.py
│   │   │   ├── command_parsing.py
│   │   │   ├── formatters.py
│   │   │   ├── help_display.py
│   │   │   ├── module_scanning.py
│   │   │   └── system_operations.py
│   │   ├── json/             # JSON handling
│   │   │   ├── __init__.py
│   │   │   ├── drone_json.py
│   │   │   └── json_handler.py
│   │   ├── loader/           # Module loader handlers
│   │   │   ├── __init__.py
│   │   │   ├── command_builder.py
│   │   │   ├── command_validation.py
│   │   │   ├── file_discovery.py
│   │   │   ├── json_loading.py
│   │   │   └── path_validation.py
│   │   ├── registry/         # Registry handlers
│   │   │   ├── __init__.py
│   │   │   ├── cache.py
│   │   │   ├── healing.py
│   │   │   ├── lookup.py
│   │   │   ├── ops.py
│   │   │   ├── registration.py
│   │   │   └── stats.py
│   │   ├── perf/             # Performance handlers
│   │   │   ├── __init__.py
│   │   │   └── ops.py
│   │   └── json_templates/   # JSON templates
│   │       ├── __init__.py
│   │       ├── custom/
│   │       ├── default/
│   │       └── registry/
│   ├── extensions/           # Plugin extensions
│   ├── json_templates/       # Additional templates
│   ├── plugins/              # Plugin system
│   └── archive_temp/         # Temporary archive
├── commands/                 # Command registry
│   └── [branch_name]/
│       ├── registry.json    # Discovered commands
│       └── active.json      # Activated commands
├── DRONE.id.json            # Branch identity
├── DRONE.local.json         # Session history
├── DRONE.observations.json  # Collaboration patterns
├── DRONE.ai_mail.json       # Branch messaging
└── README.md                # This file
```

## Integration Points

### Depends On
- Python 3.x standard library
- Rich (for console output)
- AIPass core infrastructure

### Integrates With
- **FLOW**: Workflow management
- **AI_MAIL**: Branch messaging
- **SEED**: Standards compliance
- **All Branches**: Command routing

### Provides To
- Unified command interface for all branches
- Command discovery and activation
- System-wide command registry

## Memory System

DRONE maintains several memory files:

- **DRONE.id.json**: Branch identity and architecture
- **DRONE.local.json**: Session history (max 600 lines)
- **DRONE.observations.json**: Collaboration patterns (max 600 lines)
- **DRONE.ai_mail.json**: Branch messages
- **DOCUMENTS/**: Extended memory (max 10 files)

### Health Monitoring
- 🟢 **Green**: Under 80% of limits
- 🟡 **Yellow**: 80-100% of limits
- 🔴 **Red**: Over limits (compression needed)

## Standards & References

- **Code Standards**: `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source**: `/home/aipass/aipass_core/cortex/templates/`
- **Global Documentation**: `/home/aipass/aipass_os.md`

## Usage Examples

### Scan and Activate
```bash
drone scan @seed                # Scan seed, auto-register, prompt to activate
drone activate seed             # Interactive activation menu
drone list                      # See what's activated
```

### Using @ Targets
```bash
drone seed audit @flow          # Audit flow branch
drone seed audit @drone         # Audit drone branch
drone @ai_mail send @flow "Subject" "Message"
drone plan create @aipass       # Create plan at root
```

### Routing Commands
```bash
drone @flow help                # Direct branch help
drone @seed help                # Seed standards help
drone dev add @flow "bug" "description"
```

## Notes

- This README represents the EXACT CURRENT STATE of DRONE
- Future plans are tracked in FLOW system PLANs
- Past work is in DRONE.local.json session history
- Patterns learned are in DRONE.observations.json

</details>

<details id="flow">
<summary><strong>FLOW</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_core/flow/README.md)
**Last Modified:** 2025-11-29 23:17:57

# FLOW - PLAN Management System

**Purpose:** PLAN management system for AIPass - creates, tracks, and manages workflow tasks with template-based automation
**Location:** `/home/aipass/aipass_core/flow`
**Profile:** AIPass Core Infrastructure
**Created:** 2025-11-13
**Last Updated:** 2025-11-29
**Version:** 1.0.0

## Overview

Flow provides workflow orchestration through numbered PLAN documents. Each PLAN is a trackable task with metadata, location awareness, and template-based initialization. Registry system maintains plan state (open/closed) and auto-cleanup of orphaned plans.

### What I Do
- Create/delete/manage PLAN documents
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
- **Handler Pattern:** Thin modules orchestrate, handlers implement (15 plan handlers, 100% domain independence)
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
├── handlers/            # Business logic handlers
│   ├── config/          # Configuration handlers
│   ├── dashboard/       # Dashboard display handlers
│   ├── events/          # Event processing handlers
│   ├── json/            # JSON operations handlers
│   ├── json_templates/  # JSON template handlers
│   ├── mbank/           # Memory Bank integration
│   ├── monitor/         # Monitoring handlers
│   ├── plan/            # Core PLAN handlers
│   ├── registry/        # Registry management handlers
│   ├── summary/         # Summary generation handlers
│   └── template/        # Template handlers
├── extensions/          # Optional extensions
├── json_templates/      # JSON template files
├── plugins/             # Plugin system
└── archive_temp/        # Temporary archive storage
```

## Key Capabilities

- Create numbered PLAN documents with auto-increment (PLAN0001, PLAN0002, etc.)
- Delete plans with confirmation and registry cleanup
- Location-aware plan creation (@folder syntax for contextual placement)
- Template-based plan initialization (default, research, feature templates)
- Registry maintenance with metadata tracking (location, subject, status, timestamps)
- CLI services integration (Rich-formatted output, color-coded messages)
- Handler independence (15 focused handlers, single-responsibility design)
- Error tracking with @track_operation decorator (OperationResult pattern)
- Seed v3.0 standards compliant (87-89% overall compliance)

## Usage Instructions

### Basic Usage
```bash
python3 apps/flow.py <command> [args]  # Auto-discovery pattern finds all modules
```

### Common Workflows
- **Create plan:** `flow.py create @location 'subject' [template]`
- **Delete plan:** `flow.py delete <plan_number> [--yes]`
- **View help:** `flow.py --help` (Rich-formatted with examples)
- **Introspection:** `flow.py` (no args shows discovered modules)

### Examples
```bash
flow.py create @api 'Add authentication' feature
flow.py delete 42 --yes
flow.py create 'Fix bug in registry' default
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
- **Last Auto Update:** 2025-11-13
- **Last Health Check:** 2025-11-13
- **Standards Compliance:** 100% (after recent improvements)

---

*This document is automatically maintained and represents the EXACT CURRENT STATE of the FLOW branch.*

</details>

<details id="git-repo">
<summary><strong>GIT_REPO</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_os/dev_central/git_repo/README.md)
**Last Modified:** 2025-11-24 18:15:10

# GIT_REPO Branch

## Purpose
Git repository management and version control operations for the AIPass ecosystem.

## Architecture
Modular architecture with auto-discovered modules:
- Main orchestrator (`apps/git_repo.py`) handles routing
- Modules in `apps/modules/` implement functionality
- JSON templates for configuration and data persistence
- Handlers for JSON operations and error management

## Directory Structure
```
git_repo/
├── apps/                       # Application code
│   ├── git_repo.py             # Main orchestrator
│   ├── git_commands.py         # Git command utilities
│   ├── __init__.py
│   ├── extensions/             # Extension modules
│   │   └── __init__.py
│   ├── handlers/               # Handler modules
│   │   ├── __init__.py
│   │   └── json/
│   │       ├── __init__.py
│   │       └── json_handler.py
│   ├── json_templates/         # JSON templates
│   │   ├── __init__.py
│   │   ├── custom/             # Custom templates
│   │   ├── default/            # Default templates
│   │   │   ├── config.json
│   │   │   ├── data.json
│   │   │   └── log.json
│   │   └── registry/           # Registry templates
│   ├── modules/                # Auto-discovered modules
│   │   └── __init__.py
│   └── plugins/                # Plugin modules
│       └── __init__.py
├── ai_mail.local/              # AI Mail messages
├── artifacts/                  # Build artifacts
├── DOCUMENTS/                  # Extended documentation
│   ├── DOCUMENTS.template.json
│   ├── GIT_SETUP.md
│   └── PRE_COMMIT_HOOKS_STATUS.md
├── dropbox/                    # File dropbox
├── git_repo_json/              # JSON utilities
│   └── git_cheatsheet.json
├── logs/                       # Application logs
│   └── git_repo.log
├── templates/                  # General templates
├── tests/                      # Test suite
│   ├── __init__.py
│   └── conftest.py
├── tools/                      # Utility tools
├── GIT_REPO.id.json            # Branch identity
├── GIT_REPO.local.json         # Session history
├── GIT_REPO.observations.json  # Collaboration patterns
├── GIT_REPO.ai_mail.json       # Email dashboard
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Usage
```bash
# Run the main orchestrator
python3 apps/git_repo.py <command> [options]

# Get help
python3 apps/git_repo.py --help
```

## Module Interface
All modules must implement:
```python
def handle_command(args: argparse.Namespace) -> bool:
    """Handle command if applicable.

    Returns:
        bool: True if command was handled
    """
```

## Standards Compliance
- Follows AIPass architecture standards
- Uses sys.path.insert(0) for imports
- Rich console for output formatting
- Structured logging with Python logger
- JSON templates for data persistence

## Memory Files
- `GIT_REPO.id.json` - Branch identity
- `GIT_REPO.local.json` - Session history
- `GIT_REPO.observations.json` - Collaboration patterns
- `GIT_REPO.ai_mail.json` - Email dashboard

## Version
v1.0.0 - 2025-11-22

## Contact
Branch: @git_repo
Location: /home/aipass/aipass_os/dev_central/git_repo/

</details>

<details id="mcp-servers">
<summary><strong>MCP_SERVERS</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/mcp_servers/README.md)
**Last Modified:** 2025-11-24 18:12:21

# MCP_SERVERS Branch

## Overview
The MCP_SERVERS branch manages Model Context Protocol (MCP) server integrations within the AIPass ecosystem. This branch provides tools and infrastructure for working with various MCP servers including Serena, Context7, Playwright, and Sequential Thinking.

## Purpose
- Manage MCP server configurations
- Provide interfaces to MCP server functionality
- Handle MCP-related operations and integrations
- Maintain server connection states and configurations

## Directory Structure
```
mcp_servers/
├── ai_mail.local/             # Local AI mail configuration
├── apps/                      # Application code
│   ├── mcp_servers.py         # Main orchestrator
│   ├── __init__.py
│   ├── extensions/            # Extension modules
│   ├── handlers/              # Handler modules
│   ├── json_templates/        # JSON template files
│   ├── modules/               # Auto-discovered modules
│   └── plugins/               # Plugin modules
├── artifacts/                 # Generated artifacts
├── context7/                  # Context7 MCP server (cloned repo)
│   ├── dist/                  # Compiled distribution
│   ├── docs/                  # Documentation
│   ├── mcpb/                  # MCP builder
│   ├── node_modules/          # Node dependencies
│   ├── public/                # Public assets
│   ├── schema/                # JSON schemas
│   └── src/                   # Source code
├── DOCUMENTS/                 # Extended memory storage
├── dropbox/                   # File dropbox
├── logs/                      # Application logs
├── mcp_servers_json/          # MCP server JSON configs
├── playwright-mcp/            # Playwright MCP server (cloned repo)
│   ├── extension/             # Browser extension
│   ├── src/                   # Source code
│   └── tests/                 # Test files
├── serena/                    # Serena MCP server (cloned repo)
│   ├── docs/                  # Documentation
│   ├── public/                # Public assets
│   ├── resources/             # Resource files
│   ├── scripts/               # Helper scripts
│   ├── src/                   # Source code
│   ├── test/                  # Test files
│   └── .venv/                 # Python virtual environment
├── servers/                   # Additional MCP servers repo
│   ├── scripts/               # Server scripts
│   └── src/                   # Server source code
├── templates/                 # Template files
├── tests/                     # Branch test files
│   ├── conftest.py
│   └── __init__.py
├── tools/                     # Utility tools
│   ├── apps_migration_fixer.py
│   ├── auto-register-serena-projects.py
│   ├── clean-claude-json-mcp.py
│   ├── cleanup-local-configs.py
│   ├── convert_print.py
│   └── fix-mcp-json-projects.py
├── .mcp.json                  # Local MCP configuration
├── MCP_SERVERS.id.json        # Branch identity
├── MCP_SERVERS.local.json     # Session history
├── MCP_SERVERS.observations.json  # Collaboration patterns
├── MCP_SERVERS.ai_mail.json   # Branch messaging
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Usage
```bash
# Run the main application
python3 apps/mcp_servers.py --help

# Check MCP configuration
cat .mcp.json
```

## MCP Servers Available
1. **Serena** - Project management and code navigation
2. **Context7** - Documentation and library access
3. **Playwright** - Browser automation
4. **Sequential Thinking** - Step-by-step reasoning

## Configuration
The global MCP configuration is maintained at `/home/aipass/.mcp.json` and provides system-wide access to all MCP servers.

## Development
This branch follows AIPass standards:
- Uses modular architecture with auto-discovery
- Implements standard logging via prax_logger
- Uses CLI console for output
- Maintains memory files for state tracking

## Contact
- Branch: @mcp_servers
- Email: aipass.system@gmail.com

</details>

<details id="memory-bank">
<summary><strong>MEMORY_BANK</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/MEMORY_BANK/README.md)
**Last Modified:** 2025-11-29 18:43:11

# MEMORY_BANK

## Overview
MEMORY_BANK is the global vector-based memory system for the AIPass ecosystem. It provides semantic search across all branch memories and document archives.

## Data Sources
1. **Branch Memories** - Rolled over from `*.local.json` and `*.observations.json` when files exceed 600 lines
2. **Memory Pool** - Standalone documents dropped in `memory_pool/` for vectorization
3. **Flow Plans** - Closed plans from Flow system, exported to `plans/` with TRL metadata

## Purpose
- **Archive**: Store rolled-off memories and documents as 384-dimensional embeddings
- **Search**: One global semantic search across all historical content
- **Auto-Process**: New files in memory_pool auto-vectorized on next command
- **Preserve**: No knowledge lost, just transformed into searchable vectors

## Architecture

### Directory Structure
```
apps/
├── memory_bank.py          # Main entry point CLI
├── modules/
│   ├── rollover.py         # Rollover orchestration
│   └── search.py           # Search orchestration
├── handlers/
│   ├── intake/             # Memory pool processing
│   ├── json/               # JSON file operations
│   ├── monitor/            # Memory file watching + auto-processing
│   ├── rollover/           # Extraction and embedding
│   ├── search/             # Vector search subprocess
│   ├── storage/            # ChromaDB persistence
│   ├── tracking/           # Line counting and metadata
│   └── vector/             # Embedding operations

memory_pool/                # Drop files here for auto-vectorization
├── .archive/               # Archived files (beyond keep_recent limit)
└── *.md, *.txt, *.json     # Active files (kept: 5 most recent)

plans/                      # Closed Flow plans (auto-exported)
├── .archive/               # Archived plans (beyond keep_recent limit)
└── *-PLAN*.md              # Active plans (kept: 5 most recent)

memory_bank_json/
└── memory_bank.config.json # Configuration (retention, chunk size, etc.)
```

### Core Components
- **handlers/intake/** - Memory pool + plans processing (vectorize + archive)
- **handlers/monitor/** - Startup checks, auto-triggers rollover, pool, and plans processing
- **handlers/rollover/** - Extracts oldest entries from memory files
- **handlers/search/** - Vector similarity search via subprocess
- **handlers/vector/** - Embedding operations (all-MiniLM-L6-v2)
- **handlers/storage/** - ChromaDB persistence layer

### Collections (ChromaDB)
| Collection | Source | Vectors |
|------------|--------|---------|
| `memory_pool_docs` | Archived documents | ~3,500 |
| `flow_plans` | Closed Flow plans | ~100 |
| `seed_local` | SEED branch memories | 51 |
| `aipass_local` | Root AIPASS memories | 24 |
| `drone_local` | DRONE branch memories | 16 |
| `*_local` | Other branch memories | varies |

### Storage Architecture
- **Global**: All vectors in `/home/aipass/MEMORY_BANK/.chroma/`
- **Local**: Branch-specific copies in `[branch]/.chroma/`
- **Dual Write**: Same vectors stored in both locations

## Auto-Processing

**Memory Pool** - Drop files, they get vectorized automatically:
1. Add `.md`, `.txt`, or `.json` file to `memory_pool/`
2. Next command (drone, seed, etc.) triggers startup check
3. Vectorizes all files to ChromaDB
4. Archives oldest beyond `keep_recent` (5) to `.archive/`
5. Search finds content immediately

**Flow Plans** - Closed plans auto-vectorized:
1. Flow closes a plan → exports to `plans/`
2. Startup check triggers plans_processor
3. Vectorizes with TRL metadata (Type-Category-Action)
4. Archives oldest beyond `keep_recent` (5) to `.archive/`
5. Searchable by topic or TRL tags

**Branch Memories** - Auto-rollover when exceeding 600 lines:
1. Memory file modified, exceeds 600 lines
2. Startup check detects overage
3. Extracts oldest sessions/entries
4. Embeds to vectors, stores in ChromaDB
5. File reduced to ~500 lines (100-line buffer)

## Usage

Note: Use Memory Bank's Python venv for all commands.

### Search
```bash
# Search all memories and documents
python3 apps/modules/search.py search "query"

# Filter by branch
python3 apps/modules/search.py search "query" --branch SEED

# Filter by type and limit results
python3 apps/modules/search.py search "query" --type local --n 10
```

### Memory Pool
```bash
# Check pool status
python3 apps/handlers/intake/pool_processor.py status

# Manual process (usually automatic)
python3 apps/handlers/intake/pool_processor.py
```

### Rollover
```bash
# Manual rollover (usually automatic)
python3 apps/modules/rollover.py
```

## Configuration

Edit `memory_bank_json/memory_bank.config.json`:

```json
{
  "memory_pool": {
    "enabled": true,
    "keep_recent": 5,
    "supported_extensions": [".md", ".txt", ".json"],
    "archive_path": "memory_pool/.archive"
  },
  "plans": {
    "enabled": true,
    "keep_recent": 5,
    "collection_name": "flow_plans",
    "archive_path": "plans/.archive"
  }
}
```

## Technical Details
- **Embedding**: all-MiniLM-L6-v2 (384 dimensions)
- **Vector DB**: ChromaDB with persistent storage
- **Python**: 3.12 via isolated `.venv`
- **Similarity**: 40% minimum threshold filters noise

---

**Branch**: MEMORY_BANK | **Sessions**: 12 | **Created**: 2025-11-08

*The memory never forgets - it just transforms.*

</details>

<details id="permissions">
<summary><strong>PERMISSIONS</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_os/dev_central/permissions/README.md)
**Last Modified:** 2025-11-24 18:15:21

# PERMISSIONS Branch

## Overview
The PERMISSIONS branch manages access control and permission systems within the AIPass ecosystem.

## Directory Structure
```
permissions/
├── ai_mail.local/           # Local mail storage
│   ├── deleted.json
│   ├── inbox.json
│   └── sent.json
├── apps/                    # Main application code
│   ├── permissions.py       # Main orchestrator
│   ├── __init__.py
│   ├── extensions/          # Extension modules
│   │   └── __init__.py
│   ├── handlers/            # Request handlers
│   │   ├── __init__.py
│   │   └── json/            # JSON handlers
│   │       ├── __init__.py
│   │       └── json_handler.py
│   ├── json_templates/      # JSON template files
│   │   ├── __init__.py
│   │   ├── custom/          # Custom templates (empty)
│   │   ├── default/         # Default templates
│   │   │   ├── config.json
│   │   │   ├── data.json
│   │   │   └── log.json
│   │   └── registry/        # Registry templates (empty)
│   ├── modules/             # Pluggable modules
│   │   └── __init__.py
│   └── plugins/             # Plugin system
│       └── __init__.py
├── artifacts/               # Build artifacts (empty)
├── docs/                    # Documentation
│   ├── ACL-PERMISSIONS-GUIDE.md
│   ├── PERMISSIONS.ai_mail.md
│   ├── PERMISSIONS.local.md
│   ├── PERMISSIONS.md
│   ├── PERMISSIONS.observations.md
│   └── PERMISSIONS_list.md
├── DOCUMENTS/               # Extended memory storage
│   └── DOCUMENTS.template.json
├── dropbox/                 # File dropbox (empty)
├── logs/                    # Log files (empty)
├── permissions_json/        # JSON permission files (empty)
├── templates/               # General templates (empty)
├── tests/                   # Test suite
│   ├── __init__.py
│   └── conftest.py
├── tools/                   # Utility tools (empty)
├── compliance_report.txt    # Compliance check results
├── DASHBOARD.local.json     # Dashboard state
├── dev.local.md             # Developer notes
├── notepad.md               # Scratch notes
├── PERMISSIONS.ai_mail.json # Branch messaging
├── PERMISSIONS.id.json      # Branch identity
├── PERMISSIONS.local.json   # Session history
├── PERMISSIONS.observations.json  # Collaboration patterns
├── pytest.ini               # Pytest configuration
├── README.md                # This file
└── requirements.txt         # Python dependencies
```

## Architecture
- **Main Orchestrator**: `apps/permissions.py` - Routes commands to modules
- **Module System**: Auto-discovery of modules from `apps/modules/` directory
- **Local Handlers**: Branch-specific handlers in `apps/handlers/`

## Installation
```bash
cd /home/aipass/aipass_os/dev_central/permissions
python3 -m pip install -r requirements.txt
```

## Usage
```bash
# Get help
python3 apps/permissions.py --help

# Run with verbose output
python3 apps/permissions.py [command] --verbose
```

## Module Development
New modules should be placed in `apps/modules/` directory and implement:
```python
def handle_command(args):
    """Handle command if applicable"""
    # Return True if handled, False otherwise
```

## Standards Compliance
- Uses AIPASS infrastructure patterns
- CLI console for output formatting
- Prax logger for system logging
- Follows AIPass architecture standards

## Contact
- Email: aipass.system@gmail.com
- Branch: @permissions
- Path: `/home/aipass/aipass_os/dev_central/permissions`

</details>

<details id="prax">
<summary><strong>PRAX</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/aipass_core/prax/README.md)
**Last Modified:** 2025-11-29 23:17:55

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
│   │   ├── branch_watcher.py
│   │   ├── discover_module.py
│   │   ├── init_module.py
│   │   ├── logger.py
│   │   ├── monitor_module.py
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
├── DOCUMENTS/            # Extended memory
├── PRAX.id.json          # Branch identity
├── PRAX.local.json       # Session history
├── PRAX.observations.json # Collaboration patterns
├── PRAX.ai_mail.json     # Branch messages
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

## Dependencies

Dependencies are managed via requirements.txt and include standard Python libraries for infrastructure operations.

## Memory System

### Core Files
- **PRAX.id.json** - Branch identity and architecture
- **PRAX.local.json** - Session history (max 600 lines)
- **PRAX.observations.json** - Collaboration patterns (max 600 lines)
- **PRAX.ai_mail.json** - Branch messages
- **DOCUMENTS/** - Extended memory (max 10 files, rollover to Memory Bank)

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

*Last Updated: 2025-11-29*
*Managed By: PRAX Branch*

</details>

<details id="projects">
<summary><strong>PROJECTS</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/projects/README.md)
**Last Modified:** 2025-11-24 18:12:50

# PROJECTS

**Purpose:**
**Location:** `/home/aipass/projects`
**Profile:** Workshop
**Created:** 2025-11-23

---

## Overview

### What I Do


### What I Don't Do


### How I Work


---

## Architecture

- **Pattern:** Modular
- **Structure:** `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator:** `apps/PROJECTS.py` - auto-discovers and routes to modules
- **Module Interface:** All modules implement `handle_command(args) -> bool`

---

## Directory Structure

```
/home/aipass/projects
├── ai_mail.local/
│   ├── deleted.json
│   ├── inbox.json
│   └── sent.json
├── apps/
│   ├── extensions/
│   │   └── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── json/
│   │       ├── __init__.py
│   │       └── json_handler.py
│   ├── json_templates/
│   │   ├── __init__.py
│   │   └── default/
│   │       ├── config.json
│   │       ├── data.json
│   │       └── log.json
│   ├── modules/
│   │   └── __init__.py
│   ├── plugins/
│   │   └── __init__.py
│   ├── __init__.py
│   └── projects.py
├── .archive/
├── artifacts/
│   ├── create_project_folder.py
│   └── projects.py
├── .backup/
├── DOCUMENTS/
│   └── DOCUMENTS.template.json
├── dropbox/
├── logs/
├── projects_json/
├── tests/
│   ├── __init__.py
│   └── conftest.py
├── tools/
├── workshop/
│   ├── 0001_project _name_date/
│   ├── 0002_project_name_date/
│   ├── .archive/
│   ├── .backup/
│   └── .gitignore
├── DASHBOARD.local.json
├── dev.local.md
├── .gitignore
├── .migrations.json
├── notepad.md
├── PROJECTS.ai_mail.json
├── PROJECTS.id.json
├── PROJECTS.local.json
├── PROJECTS.observations.json
├── pytest.ini
├── README.md
└── requirements.txt

21 directories, 28 files
```

*Auto-generated on file structure changes*

---

## Modules

{{AUTO_GENERATED_MODULES}}

*Scans `apps/modules/*.py` for files with `handle_command()`*

---

## Commands

{{AUTO_GENERATED_COMMANDS}}

*Pulled from drone @PROJECTS - branch-specific commands only*

---

## Dependencies

{{AUTO_GENERATED_DEPENDENCIES}}

*Parsed from `requirements.txt` when it changes*

---

## Common Imports

{{AUTO_GENERATED_IMPORTS}}

*Scans module files for import statements - shows common dependencies*

---

## Key Capabilities

{{KEY_CAPABILITIES}}

---

## Usage Instructions

### Basic Usage
{{BASIC_USAGE}}

### Common Workflows
{{COMMON_WORKFLOWS}}

### Examples
{{EXAMPLES}}

---

## Integration Points

### Depends On
{{DEPENDS_ON}}

### Integrates With
{{INTEGRATES_WITH}}

### Provides To
{{PROVIDES_TO}}

---

## Memory System

### Memory Files
- **PROJECTS.id.json** - Branch identity and architecture
- **PROJECTS.local.json** - Session history (max 600 lines)
- **PROJECTS.observations.json** - Collaboration patterns (max 600 lines)
- **PROJECTS.ai_mail.json** - Branch messages
- **DOCUMENTS/** - Extended memory (max 10 files, rollover to Memory Bank)

### Health Monitoring
- 🟢 **Green (Healthy):** Under 80% of limits
- 🟡 **Yellow (Warning):** 80-100% of limits
- 🔴 **Red (Critical):** Over limits (compression needed)

---

## System References

- **Code Standards:** `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source:** `/home/aipass/aipass_core/branch_operations/templates/`
- **Global Documentation:** `/home/aipass/aipass_os.md`

### Core Systems
- **Flow:** Workflow and PLAN management
- **Drone:** Command orchestration
- **AI Mail:** Branch-to-branch messaging
- **Backup:** System backup and snapshots
- **Prax:** Logging and infrastructure
- **API:** API integration layer

---

## Automation Philosophy

**README represents EXACT CURRENT STATE** - not future plans, not past work

### What Goes Elsewhere
- **Future Plans:** PLAN files in flow system
- **Past Work:** PROJECTS.local.json session history
- **Working On:** Active PLANs
- **Patterns Learned:** PROJECTS.observations.json
- **Extended Context:** DOCUMENTS/ directory

### Automation Goal
Minimize AI token spend on updates - automate everything possible. Triggers fire on actual changes, not periodic checks.

---

## Notes

- **Human File:** This README.md is AI-managed Markdown - Patrick reads this directly
- **Current State Only:** Snapshot of branch as it exists RIGHT NOW - no history, no future
- **Auto vs Manual:** Automated sections = script-populated, Manual sections = AI writes when something fundamentally changes

---

*Last Updated: 2025-11-24*


</details>

<details id="seed">
<summary><strong>SEED</strong></summary>

**Source:** [README.md](vscode://file/home/aipass/seed/README.md)
**Last Modified:** 2025-11-29 19:42:23

# SEED - Standards Truth Source & Architectural Model

**Path:** `/home/aipass/seed`
**Profile:** Workshop / Reference Implementation
**Purpose:** Demonstrate proper AIPass architecture and maintain standards compliance

---

## What Is SEED?

SEED is the **SHOWROOM/MODEL** branch for AIPass - the living reference implementation that demonstrates proper architecture through executable, queryable standards modules.

**Why it matters:** Other branches query SEED to learn correct patterns. When you run `drone @seed [standard]`, you're learning from working code that demonstrates each standard.

---

## Key Capabilities

- **10 Standards Modules** - Architecture, CLI, Documentation, Encapsulation, Error Handling, Handlers, Imports, JSON Structure, Modules, Naming
- **Standards Checklist System** - Automated compliance checking (~90% accuracy) with v0.3.0 checkers
- **Working Code Examples** - All standards demonstrated through executable code in apps/
- **Template Registry Integration** - Branches measured against Cortex template as source of truth
- **Interactive Query System** - Run `python3 apps/seed.py [standard]` to see formatted standards documentation

---

## Directory Structure

```
seed/
├── .seed/
│   └── bypass.json                      # Branch-level standards bypass config
├── apps/
│   ├── seed.py                          # Entry point
│   ├── __init__.py
│   ├── modules/
│   │   ├── architecture_standard.py
│   │   ├── cli_standard.py
│   │   ├── documentation_standard.py
│   │   ├── error_handling_standard.py
│   │   ├── handlers_standard.py
│   │   ├── imports_standard.py
│   │   ├── json_structure_standard.py
│   │   ├── modules_standard.py
│   │   ├── naming_standard.py
│   │   ├── standards_audit.py           # Branch audit tool
│   │   └── standards_checklist.py       # Compliance checker + bypass system
│   ├── handlers/
│   │   ├── standards/                   # 9 content + 12 check handlers
│   │   │   ├── *_content.py             # Quick reference
│   │   │   └── *_check.py               # Automated checkers (bypass-aware)
│   │   ├── config/
│   │   ├── file/
│   │   │   └── file_handler.py          # Text file reading (read_file, file_exists)
│   │   ├── json/
│   │   │   └── json_handler.py          # JSON file operations
│   │   └── test/
│   ├── extensions/
│   ├── json_templates/
│   └── plugins/
├── SEED.id.json
├── SEED.local.json
├── SEED.observations.json
├── SEED.ai_mail.json
└── README.md
```

---

## How To Use

### Query Standards Documentation

```bash
# Show all available standards
python3 /home/aipass/seed/apps/seed.py

# Show specific standard
python3 /home/aipass/seed/apps/seed.py architecture
python3 /home/aipass/seed/apps/seed.py cli
python3 /home/aipass/seed/apps/seed.py imports
```

### Run Standards Checker

```bash
# From any branch, run automated compliance check
python3 /home/aipass/seed/apps/modules/standards_checklist.py /path/to/your/file.py
```

### Check Your Branch's Compliance

```bash
# Via drone (from anywhere)
drone @seed check                    # Run all standards checks on SEED
drone @seed validate [standard]      # Validate specific standard
drone @seed checklist <file>         # Run standards checklist on a file
drone @seed audit                    # Full system audit (all branches)
drone @seed audit @cortex            # Audit specific branch
drone @seed audit --show-bypasses    # Show all bypassed files and current state
drone @seed audit @branch --bypasses # Show bypasses for specific branch
```

---

## Bypass System (.seed/bypass.json)

Branches can configure their own standards exceptions via `.seed/bypass.json`. This allows legitimate exceptions (like circular dependencies or foundational services) without failing compliance checks.

### How It Works

1. **Auto-Creation**: When running `drone @seed checklist` or `drone @seed audit`, SEED auto-creates `.seed/bypass.json` if missing
2. **Branch-Level**: Each branch maintains its own bypass config in its `.seed/` directory
3. **Standards-Aware**: All 12 checkers respect bypass rules during compliance checking

### Configuration Format

```json
{
  "metadata": {
    "version": "1.0.0",
    "description": "Standards bypass configuration for this branch"
  },
  "bypass": [
    {
      "file": "apps/modules/logger.py",
      "standard": "cli",
      "reason": "Circular dependency - logger cannot import CLI (foundational service)"
    },
    {
      "file": "apps/modules/logger.py",
      "standard": "imports",
      "lines": [42, 56],
      "reason": "Specific line exceptions for import order"
    }
  ]
}
```

### Bypass Rule Fields

| Field | Required | Description |
|-------|----------|-------------|
| `file` | Yes | Relative path from branch root (e.g., `apps/modules/logger.py`) |
| `standard` | Yes | Standard name: `architecture`, `cli`, `imports`, `modules`, etc. |
| `lines` | No | Specific line numbers to bypass (omit for whole-file bypass) |
| `pattern` | No | Pattern to match (e.g., `if __name__ == '__main__'`) |
| `reason` | Yes | Documentation of why this bypass exists |

### When to Use Bypass (Legitimate)

Bypasses are for **architectural limitations or checker bugs we'll fix later**:

- **Circular dependencies**: Logger can't import CLI (foundational service)
- **Checker false positives**: CLI patterns detected in docstrings/examples
- **Unsolved architectural issues**: Problems not worth blocking progress on

### When NOT to Use Bypass

Bypasses are **NOT** for hiding real violations you could fix:

- **Business logic in modules**: Move to handlers, don't bypass
- **Direct file operations**: Use json_handler or file_handler, don't bypass
- **Large files**: Split them, don't bypass the size check

**Rule**: If branches look at SEED and see bypassed violations, they'll copy that pattern. SEED must demonstrate proper solutions, not workarounds.

### Bypass Review Process

Periodically review `.seed/bypass.json`:
1. Can this be fixed properly now?
2. Is the checker smarter now (false positive resolved)?
3. Is this still architecturally necessary?

Goal: Minimize bypasses over time as checkers improve and code gets refactored

---

## Core Responsibilities

1. **Maintain AIPass Code Standards** - The 10 standards are the source of truth
2. **Demonstrate Proper Patterns** - All standards must be implemented in SEED's own code
3. **Provide Queryable Reference** - Branches learn by examining SEED's implementation
4. **Help Branches Audit Themselves** - Provide checklist tools and compliance feedback
5. **Stay Compliant** - SEED must achieve 100% standards compliance

---

## Standards Overview

### 1. Architecture
**Pattern:** Entry Point → Modules → Handlers
**Key Rules:** 3-layer separation, handler independence, domain organization
**File:** `apps/modules/architecture_standard.py`

### 2. CLI
**Pattern:** Service provider for command-line interaction
**Key Rules:** No bare `print()`, use `console.print()`, separate handlers from CLI
**File:** `apps/modules/cli_standard.py`

### 3. Documentation
**Pattern:** Headers, module docstrings, inline comments
**Key Rules:** Shebang, module docstring, function docstrings with Args/Returns
**File:** `apps/modules/documentation_standard.py`

### 4. Error Handling
**Pattern:** Return bool from route_command, use try/except
**Key Rules:** No bare exceptions, log errors, provide context
**File:** `apps/modules/error_handling_standard.py`

### 5. Handlers
**Pattern:** Domain-organized, independent, reusable
**Key Rules:** No cross-handler imports, no module imports, auto-discovery via module_name parameter
**File:** `apps/modules/handlers_standard.py`

### 6. Imports
**Pattern:** AIPASS_ROOT, sys.path, Prax logger, structured order
**Key Rules:** Infrastructure first, services second, locals last
**File:** `apps/modules/imports_standard.py`

### 7. JSON Structure
**Pattern:** 3-file setup (config, data, log)
**Key Rules:** Auto-generated, module-specific paths, versioned schema
**File:** `apps/modules/json_structure_standard.py`

### 8. Modules
**Pattern:** Orchestration layer with handle_command(args) -> bool
**Key Rules:** <150 perfect, 150-250 good, 250-400 acceptable, 400+ heavy
**File:** `apps/modules/modules_standard.py`

### 9. Naming
**Pattern:** snake_case files, snake_case functions, UPPER_CASE constants, PascalCase classes
**Key Rules:** Context = path, action = name, no prefixes
**File:** `apps/modules/naming_standard.py`

### 10. Encapsulation
**Pattern:** Handlers are implementation details, modules are public API
**Key Rules:** No cross-branch handler imports, no cross-package handler imports, use module entry points
**File:** `apps/handlers/standards/encapsulation_check.py`

---

## Compliance Status

**Current:** 99% overall (CLI 100%, Modules 97%)
**Target:** 100%

**Remaining Work:**
- `standards_audit.py` at 702 lines needs splitting (<600 target)

**SEED Legitimate Bypasses:**
- `standards_checklist.py` / architecture - Large file (orchestrates 10 standards + bypass infrastructure)
- `standards_checklist.py` / modules - Direct file ops for bypass system (chicken-and-egg)
- `standards_checklist.py` / json_structure - Direct JSON for bypass loading
- 6 CLI bypasses for content handlers showing CLI examples in strings (checker limitation)

**Checked Against:** Template registry (Cortex template = source of truth)
**Measurement Method:** Automated architecture checker measuring all branches against same template standard

---

## Memory System

SEED uses a multi-file memory system for persistence:

| File | Purpose | Max Size | Rollover |
|------|---------|----------|----------|
| SEED.id.json | Branch identity | 1000 words | Never (permanent) |
| SEED.local.json | Session history | 600 lines | Rolls to Memory Bank |
| SEED.observations.json | Collaboration patterns | 600 lines | Rolls to Memory Bank |
| SEED.ai_mail.json | Branch messages | Auto | Auto-cleanup |
| docs/ | Extended notes | 10 files max | Full rollover |

---

## Integration Points

**Depends On:**
- Cortex (for template registry - source of truth for compliance)
- CLI (for console display service)
- Drone (for command routing and cross-branch communication)

**Integrates With:**
- All other branches (provides standards queries via drone)
- AI_MAIL (receives compliance notifications)
- Flow (tracks work plans and completion)

**Provides To:**
- All branches (standards reference + checklist tools)
- Cortex (compliance verification)
- Development team (observable standards implementation)

---

## Key Design Principles

1. **Code is Truth** - Standards are demonstrated through working code, not just documentation
2. **Single Source of Truth** - Cortex template registry = only standard for compliance
3. **Three-Layer Pattern** - All standards information flows: Markdown → Handler → Module → Output
4. **No Exceptions** - SEED must be 100% standards compliant to remain credible
5. **Queryable Design** - Standards accessible via CLI, not just files

---

## Recent Work (Session 16 - 2025-11-27)

- **Bypass System**: Implemented `.seed/bypass.json` with clear philosophy (use for limitations, not violations)
- **Bug Fix**: Fixed `is_bypassed()` in all 10 checkers - wasn't checking file path
- **Real Violation Fixes**: Fixed template_scanner, naming_standard, standards_audit, standards_verify
- **New Handler**: Created `handlers/file/file_handler.py` for text file reading abstraction
- **CLI 100%**: Fixed template_scanner.py (print → logger)
- **Modules 97%**: One remaining issue (standards_audit.py needs splitting)
- **SEED at 99%**: Demonstrating proper handler usage, not bypassing fixable violations

---

## Roadmap

- **Completed:** Bypass system with proper philosophy ✓
- **Completed:** Fixed real violations properly (handlers, not bypasses) ✓
- **In Progress:** Split standards_audit.py (<600 lines target)
- **Short-term:** Expand bypass system awareness to all branches
- **Medium-term:** Automated standards violations dashboard
- **Long-term:** Self-healing standards enforcement (branches auto-correct violations)

---

**Created:** 2025-11-12
**Last Updated:** 2025-11-29
**Branch Status:** Production (reference implementation)


</details>
