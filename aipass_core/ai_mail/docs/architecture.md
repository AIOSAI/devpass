# AI_MAIL Architecture

**Branch:** AI_MAIL
**Created:** 2025-11-30
**Updated:** 2025-11-30

---

## Overview

AI_MAIL is a file-based email system that enables branch-to-branch communication within the AIPass ecosystem. It provides asynchronous messaging between AI branches without relying on external email protocols (SMTP/IMAP). All communication is stored as JSON files on the local filesystem.

**Core Philosophy:**
- File-based messaging (no external dependencies)
- Auto-detection of sender identity via PWD/CWD
- Zero manual configuration required
- Each branch maintains its own mailbox
- Dashboard integration for visibility

## 3-Layer Architecture

AI_MAIL follows the standard AIPass architecture pattern with three distinct layers:

### Layer 1: Entry Point (Router)

**File:** `/apps/ai_mail.py`

**Responsibilities:**
- Parse command-line arguments
- Auto-discover modules from `/apps/modules/`
- Route commands to appropriate modules
- Display help and introspection information

**Key Pattern:**
```python
# Module auto-discovery
modules = discover_modules()  # Scans modules/ directory

# Command routing
for module in modules:
    if module.handle_command(command, args):
        return True  # Module handled it
```

**Module Interface Contract:**
All modules must implement:
```python
def handle_command(command: str, args: List[str]) -> bool:
    """
    Returns True if command was handled, False otherwise
    """
```

### Layer 2: Modules (Business Logic Orchestration)

**Location:** `/apps/modules/`

**Purpose:** Orchestrate workflows by importing handlers and coordinating their operations. Modules contain NO business logic themselves - they only orchestrate.

**Current Modules:**
- `email.py` - Core email operations (send, inbox, view, reply, close, sent, contacts)
- `branch_ping.py` - Branch health monitoring
- `dispatch.py` - Dispatch status tracking

**Module Pattern:**
```python
def handle_send(args: List[str]) -> bool:
    """Orchestrate email sending workflow"""
    # Import handlers for each step
    from handlers.users.user import get_current_user
    from handlers.email.create import create_email_file
    from handlers.email.delivery import deliver_email_to_branch

    # Orchestrate the workflow
    user_info = get_current_user()
    email_file = create_email_file(to_branch, subject, message, user_info)
    success, error_msg = deliver_email_to_branch(to_branch, email_data)

    return success
```

**Key Characteristics:**
- 135-200 lines target (handles multiple workflows)
- Imports from `handlers/` for all operations
- Uses `json_handler.log_operation()` for tracking
- NO business logic - pure orchestration

### Layer 3: Handlers (Implementation Details)

**Location:** `/apps/handlers/`

**Purpose:** Contain pure business logic for specific operations. Handlers are independent and cannot import from modules or other handler domains.

**Handler Organization (by domain):**

```
handlers/
├── email/              # Email operations
│   ├── create.py       # Create email messages
│   ├── delivery.py     # Deliver to branches
│   ├── format.py       # Email formatting
│   ├── footer.py       # Email footer generation
│   ├── header.py       # Email header generation
│   ├── inbox_ops.py    # Inbox operations
│   ├── inbox_cleanup.py # Archive/delete operations
│   ├── purge.py        # Email purge operations
│   └── reply.py        # Reply handling
│
├── users/              # User/branch configuration
│   ├── branch_detection.py   # Auto-detect calling branch
│   ├── config_generator.py   # Generate branch configs
│   ├── load.py               # Load configurations
│   └── user.py               # User operations
│
├── registry/           # Branch registry
│   ├── load.py         # Load registry
│   ├── read.py         # Read registry data
│   ├── update.py       # Update registry
│   └── validate.py     # Validate registry
│
├── persistence/        # Data persistence
│   └── json_ops.py     # JSON persistence operations
│
├── monitoring/         # System monitoring
│   ├── data_ops.py     # Data operations
│   ├── errors.py       # Error handling
│   └── memory.py       # Memory monitoring
│
├── dispatch/           # Dispatch operations
│   └── status.py       # Dispatch status tracking
│
├── trigger/            # Trigger operations
│   └── error_handler.py # Error handling for triggers
│
├── json_utils/         # JSON operations
│   └── json_handler.py # JSON file operations
│
└── central_writer.py   # Central stats aggregation
```

**Handler Independence Rules:**
- NO cross-domain imports between handlers
- CAN import from Prax modules (logging, services)
- CAN import from AIPASS central services (dashboard)
- Pure business logic only
- Self-contained and testable

**Example Handler:**
```python
# handlers/users/branch_detection.py
def detect_branch_from_pwd() -> Dict | None:
    """
    Detect which branch is calling based on PWD.
    Walks up directory tree to find [BRANCH].id.json file.
    """
    cwd = Path.cwd()
    branch_root = find_branch_root(cwd)
    return get_branch_info_from_registry(branch_root)
```

## Directory Structure

```
/home/aipass/aipass_core/ai_mail/
├── apps/
│   ├── ai_mail.py              # Entry point orchestrator
│   ├── __init__.py
│   ├── modules/                # Layer 2: Business logic orchestration
│   │   ├── email.py
│   │   ├── branch_ping.py
│   │   ├── dispatch.py
│   │   └── extensions/
│   ├── handlers/               # Layer 3: Implementation details
│   │   ├── email/
│   │   ├── users/
│   │   ├── registry/
│   │   ├── persistence/
│   │   ├── monitoring/
│   │   ├── dispatch/
│   │   ├── trigger/
│   │   ├── json_utils/
│   │   └── central_writer.py
│   ├── extensions/             # App extensions (future)
│   ├── plugins/                # Plugins (future)
│   └── json_templates/         # JSON templates
│       ├── custom/
│       ├── default/
│       └── registry/
├── docs/                       # Documentation
│   ├── _template.md
│   └── architecture.md         # This file
├── ai_mail.local/              # AI_MAIL's own mailbox
│   ├── inbox.json
│   ├── deleted.json
│   └── sent/
├── AI_MAIL.id.json             # Branch identity
├── AI_MAIL.local.json          # Session history
├── AI_MAIL.observations.json   # Collaboration patterns
├── AI_MAIL.ai_mail.json        # Email dashboard
├── DASHBOARD.local.json        # System-wide status
└── README.md                   # Branch documentation
```

## Email Lifecycle v2

AI_MAIL implements a 3-state email model:

### Email States

1. **new** - Email just delivered, never viewed
2. **opened** - Email content has been viewed, awaiting resolution
3. **closed** - Email resolved (replied or dismissed), archived to deleted

### State Transitions

```
┌─────────────────────────────────────────┐
│  Email arrives → inbox (status: "new")  │
└─────────────────┬───────────────────────┘
                  │
                  ↓
         [view <id>] command
                  │
                  ↓
        status: "opened" (stays in inbox)
                  │
          ┌───────┴───────┐
          ↓               ↓
  [reply <id> "msg"]   [close <id>]
          ↓               ↓
   Sends reply      Closes without reply
          ↓               ↓
  Auto-closes original   │
          └───────┬───────┘
                  ↓
         status: "closed"
                  ↓
    Archived to deleted.json
```

### Commands

```bash
# View inbox (shows new + opened emails)
ai_mail inbox

# View email content (new → opened)
ai_mail view <message_id>

# Reply to email (sends reply + auto-closes original)
ai_mail reply <message_id> "Your message here"

# Close email without replying (opened → closed → archived)
ai_mail close <message_id>

# Close multiple emails
ai_mail close <id1> <id2> <id3>

# Close all emails in inbox
ai_mail close all
```

### Email Schema (v2)

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

## Key Design Decisions

### 1. PWD-Based Sender Detection

**Problem:** How does AI_MAIL know which branch is sending an email?

**Solution:** Auto-detect calling branch by examining the current working directory (PWD/CWD).

**Implementation:**
1. Get current working directory
2. Walk up directory tree to find `[BRANCH].id.json` file
3. Look up branch path in `BRANCH_REGISTRY.json`
4. Return branch info (name, email, path, display_name)

**Benefits:**
- Zero configuration required
- No risk of branch impersonation
- Works automatically for all branches
- Fails honestly if caller is not in a branch directory

**Code Location:** `/apps/handlers/users/branch_detection.py`

### 2. No Fallbacks - Fail Honestly

**Philosophy:** If something is wrong, fail explicitly rather than guessing.

**Examples:**
- Unknown recipient email? Return error, don't guess
- Can't detect sender branch? Fail, don't default to "unknown"
- Missing inbox file? Return error, don't create it

**Benefits:**
- Easier debugging (errors are explicit)
- No silent failures
- Forces proper setup
- Prevents corruption from invalid assumptions

### 3. File-Based Architecture

**Why files instead of database?**
- Simple and transparent
- Easy to inspect/debug
- Version control friendly
- No database dependencies
- Works offline
- Survives system restarts

**File Patterns:**
```
[branch]/ai_mail.local/
├── inbox.json          # Current messages (new + opened)
├── deleted.json        # Archived messages (closed)
└── sent/               # Sent messages (one file per email)
    ├── <uuid>.json
    └── <uuid>.json
```

### 4. Auto-Configuration Generation

**Problem:** Branches need configs to send/receive email, but manual setup is error-prone.

**Solution:** Auto-generate `user_config.json` in `[branch]_json/` directory on first use.

**Flow:**
1. Branch calls `ai_mail send`
2. AI_MAIL detects calling branch via PWD
3. Checks for `[branch]_json/user_config.json`
4. If missing, generates it automatically
5. Uses generated config for sender identity

**Benefits:**
- Zero manual setup required
- Consistent configuration format
- No risk of typos in manual config
- Each branch's config is independent

**Code Location:** `/apps/handlers/users/config_generator.py`

### 5. Dashboard Integration

**Pattern:** Update `DASHBOARD.local.json` on every email delivery.

**Purpose:** Provide system-wide visibility into email status without requiring branches to check inbox files.

**Data Updated:**
```json
{
  "ai_mail": {
    "new": 3,        // Unviewed emails
    "opened": 2,     // Viewed but unresolved
    "total": 5       // Total in inbox
  }
}
```

**Benefits:**
- Branch managers see unread count on startup
- Central visibility into communication status
- No need to check inbox files manually
- Auto-refreshed from central sources

## Integration Points

### Dependencies

**PRAX** - Logging infrastructure
- Uses `prax.apps.modules.logger.system_logger`
- All operations logged for debugging

**CLI** - Display and formatting
- Uses `cli.apps.modules.console`
- Rich console output for readability

**DRONE** - Command routing
- Accessed via `drone @ai_mail <command>`
- DRONE resolves `@ai_mail` to branch path

**Dashboard Service** - Status updates
- Uses `apps.modules.dashboard.update_section`
- Updates `DASHBOARD.local.json` after delivery

### Provides To

**All Branches:**
- Email communication capability
- Inbox/sent/deleted mailbox management
- Contact directory (branch registry access)

**AIPASS System:**
- Inter-branch coordination
- Async messaging infrastructure
- Audit trail of communications

## Mailbox File Formats

### inbox.json
```json
{
  "messages": [
    {
      "id": "a7b3c9d2",
      "timestamp": "2025-11-30 14:23:15",
      "from": "@seed",
      "from_name": "Seed (Standards Branch)",
      "subject": "Code review requested",
      "message": "Please review the new handler pattern...",
      "status": "new"
    }
  ],
  "total_messages": 1,
  "unread_count": 1
}
```

### deleted.json
```json
{
  "messages": [
    {
      "id": "x9y8z7w6",
      "timestamp": "2025-11-29 09:15:30",
      "from": "@drone",
      "from_name": "Drone (Command Router)",
      "subject": "System update complete",
      "message": "All routes updated successfully.",
      "status": "closed",
      "closed_at": "2025-11-30 08:00:00"
    }
  ],
  "total_messages": 1
}
```

### sent/[uuid].json
```json
{
  "id": "p1q2r3s4",
  "timestamp": "2025-11-30 16:45:22",
  "from": "@ai_mail",
  "from_name": "AI_Mail (Branch Communication)",
  "to": "@flow",
  "subject": "New feature available",
  "message": "Reply functionality now supports auto-close...",
  "status": "new"
}
```

## Standards Compliance

AI_MAIL follows AIPass code standards:

**Architecture:**
- 3-layer pattern (entry → modules → handlers)
- Module auto-discovery from `/apps/modules/`
- Handler independence (no cross-domain imports)

**Import Patterns:**
```python
# Infrastructure imports
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Service imports (allowed in handlers)
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console
```

**Code Standards:**
- Handlers: Pure business logic, no module dependencies
- Modules: Orchestration only, import handlers
- Entry point: Routing only, auto-discovers modules

**CLI Integration:**
- 100% drone-compliant
- Supports `--help` flag
- Introspection mode (no args)
- Proper error codes (0=success, 1=error)

## Development Notes

**Philosophy:**
- Code is truth - fail honestly
- Simple solutions over complex architecture
- Test incrementally, preserve what works
- Each instance isolated with own memory

**Adding New Commands:**
1. Add handler function in appropriate `/handlers/` subdirectory
2. Add orchestration function in `/modules/email.py`
3. Update `handle_command()` to route new command
4. Update help text in `ai_mail.py` and `email.py`

**Testing Pattern:**
- Test handlers independently first
- Test module orchestration second
- Test full command flow third
- Use `python3 apps/ai_mail.py <command>` for direct testing

**Memory Management:**
- Session history: `AI_MAIL.local.json` (max 600 lines, auto-rolls)
- Observations: `AI_MAIL.observations.json` (max 600 lines, auto-rolls)
- Inbox: No size limit (use `close` command to archive)

---

## Related Documentation

- [README](../README.md) - Branch overview and usage
- [_template.md](./_template.md) - Documentation template

---

*Part of AI_MAIL branch documentation*
*Last updated: 2025-11-30*
