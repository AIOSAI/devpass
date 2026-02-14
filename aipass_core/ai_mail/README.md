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
- Track email lifecycle: new → opened → closed
- Support reply chains with auto-close behavior
- Auto-generate per-branch configs (user_config.json in [branch]_json/)
- Auto-detect calling branch via PWD/CWD for sender identity
- Update dashboard on delivery (DASHBOARD.local.json)
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
│   ├── dispatch.py         # Dispatch status tracking
│   └── extensions/         # Module extensions
├── handlers/
│   ├── central_writer.py   # Central file updates
│   ├── dispatch/           # Dispatch operations
│   │   └── status.py       # Dispatch log and status
│   ├── email/              # Email operations
│   │   ├── create.py       # Create email messages
│   │   ├── delivery.py     # Deliver to branches
│   │   ├── format.py       # Email formatting
│   │   ├── footer.py       # Auto-footer for outgoing emails
│   │   ├── header.py       # Email header formatting
│   │   ├── inbox_cleanup.py # Inbox cleanup operations
│   │   ├── inbox_ops.py    # Inbox operations
│   │   ├── purge.py        # Auto-purge sent/deleted when >10 items
│   │   └── reply.py        # Reply handling
│   ├── json_utils/         # JSON operations
│   │   └── json_handler.py # JSON file operations
│   ├── monitoring/         # System monitoring
│   │   ├── data_ops.py     # Data operations
│   │   ├── errors.py       # Error handling
│   │   └── memory.py       # Memory health checks
│   ├── persistence/        # Data persistence
│   │   └── json_ops.py     # JSON persistence ops
│   ├── registry/           # Branch registry
│   │   ├── load.py         # Load registry
│   │   ├── read.py         # Read registry data
│   │   ├── update.py       # Update registry
│   │   └── validate.py     # Validate registry
│   ├── trigger/            # Event consumers
│   │   └── error_handler.py # Handle error_detected events
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

- `email` - Core email functionality (send, inbox, view, reply, close, sent, contacts)
- `branch_ping` - Branch memory health monitoring
- `dispatch` - Dispatch status tracking and log

### Handlers (by domain)

**Dispatch**: status
**Email**: create, delivery, footer, format, header, inbox_cleanup, inbox_ops, purge, reply
**JSON Utils**: json_handler
**Monitoring**: data_ops, errors, memory
**Persistence**: json_ops
**Registry**: load, read, update, validate
**Trigger**: error_handler
**Users**: branch_detection, config_generator, load, user

## Usage

### Email Lifecycle v2

AI_MAIL uses a 3-state email model:

**States:**
- `new` - Email just delivered, never viewed
- `opened` - Email content has been viewed, awaiting resolution
- `closed` - Email resolved (replied or dismissed), archived to deleted

**Flow:**
```
Email sent → inbox (status: "new")
           ↓
        view <id> → status: "opened"
           ↓
    ┌──────────┴──────────┐
    ↓                     ↓
reply <id> "msg"      close <id>
    ↓                     ↓
auto-closes           closes
    └──────────┬──────────┘
               ↓
        archived to deleted.json
```

### Basic Commands

```bash
# Send email
drone @ai_mail send @recipient "Subject" "Message"

# Broadcast to all branches
drone @ai_mail send @all "Announcement" "Message"

# Check inbox (shows new + opened emails)
drone @ai_mail inbox

# View email content (marks as opened)
drone @ai_mail view <message_id>

# Reply to email (sends reply + auto-closes original)
drone @ai_mail reply <message_id> "Your reply message"

# Close email without replying (archives to deleted)
drone @ai_mail close <message_id>

# View sent messages
drone @ai_mail sent

# List contacts
drone @ai_mail contacts
```

### Backward Compatibility

```bash
# 'read' command now behaves like 'view'
# (marks as opened, does NOT archive)
drone @ai_mail read <message_id>
```

### Direct Module Access

```bash
# Email operations
python3 apps/ai_mail.py email [command]

# Branch health check
python3 apps/ai_mail.py ping

# Dispatch status
python3 apps/ai_mail.py dispatch status
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
- `ai_mail.local/inbox.json` - Incoming messages (new + opened status)
- `ai_mail.local/sent/` - Sent messages (including replies)
- `ai_mail.local/deleted/` - Closed/archived messages (individual files)

**Email Schema (v2):**
```json
{
  "id": "abc123",
  "from": "@sender",
  "from_name": "SENDER Branch",
  "to": "@recipient",
  "subject": "Subject line",
  "message": "Message body",
  "status": "new",           // new | opened | closed
  "timestamp": "2025-11-30 12:00:00",
  "thread_id": null,         // For future threading
  "reply_to": null           // Original message ID if reply
}
```

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

## Changelog

**2026-02-07 - Archived local_memory_monitor**
- Archived entire local_memory_monitor subsystem (redundant with Memory Bank auto-rollover)
- Archived: module, notifications/ handlers, monitoring/status.py, config files
- Kept shared handlers used by branch_ping: monitoring/memory.py, registry/

**2026-02-06 - Commons Notification Hooks**
- Created notify.py in The Commons for @mention and reply notifications
- Integrated with ai_mail delivery for cross-system notifications

**2026-02-04 - Deleted Directory Migration + Auto-Purge**
- Migrated deleted.json to deleted/ directory (individual files)
- Added auto-purge for sent/ and deleted/ (keeps 10 most recent, archives rest)

**2026-01-29 - Auto-Footer**
- Added footer.py handler for auto-appending task checklist to outgoing emails
- Footer reminds branches: Seed check, memory update, FPLAN close, confirmation

**2025-11-30 - Email Lifecycle v2**
- Implemented 3-state email model: new → opened → closed
- Added `view`, `reply`, `close` commands
- Deprecated `read all` (bulk archive removed)
- `read <id>` now behaves like `view` (backward compat)
- Reply auto-closes original email
- Updated email schema with status field

**2025-11-27 - v1 Improvements**
- Added `read` command for archiving emails
- Improved inbox cleanup workflows

**2025-11-15 - Initial Release**
- Core email functionality: send, inbox, sent, contacts
- PWD-based sender detection
- Auto-config generation

---

*Last Updated: 2026-02-07*
*Maintained by: AI_MAIL Branch*