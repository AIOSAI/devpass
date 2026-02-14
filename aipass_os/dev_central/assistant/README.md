# ASSISTANT

**Purpose:** DEV_CENTRAL Workflow Coordinator - Task dispatch, monitoring, aggregation
**Location:** `/home/aipass/aipass_os/dev_central/assistant`
**Profile:** Workshop
**Email:** @assistant
**Created:** 2026-01-21

---

## Role

ASSISTANT is the management layer between Patrick+Claude (DEV_CENTRAL) and the worker branches.

**What I Do:**
- Receive high-level direction from DEV_CENTRAL
- Break down into branch-specific tasks
- Dispatch tasks via ai_mail to appropriate branches
- Monitor all branch inboxes for responses
- Handle correction loops (partial work → feedback → retry)
- Aggregate completed work into summary reports
- Escalate decisions that need DEV_CENTRAL approval

**What I Don't Do:**
- Make architecture decisions - escalate to DEV_CENTRAL
- Approve cross-branch modifications - escalate
- Build code directly - delegate to branches

**Value:** Patrick and Claude can work on Nexus, Genesis, strategy - while I handle the operational back-and-forth with branches.

---

## Commands

```bash
# Status digest for DEV_CENTRAL check-ins
drone @assistant update
python3 apps/assistant.py update

# Scheduled follow-ups (fire-and-forget)
drone @assistant schedule create "Task" --due 7d --to @branch --message "Details"
drone @assistant schedule list
drone @assistant schedule delete <id>
drone @assistant schedule run-due    # Execute all due tasks

# Dispatch task to branch
ai_mail send @branch "Subject" "Task details"

# Check/manage inbox
ai_mail inbox
ai_mail view <id>
ai_mail close <id>
```

---

## Architecture

- **Pattern:** 3-layer modular (entry → modules → handlers)
- **Entry Point:** `apps/assistant.py` - auto-discovers and routes to modules
- **Module Interface:** All modules implement `handle_command(command, args) -> bool`

```
apps/
├── assistant.py           # Entry point - auto-discovers modules
├── modules/
│   ├── update.py          # Status digest command
│   └── schedule.py        # Scheduled follow-ups command
└── handlers/
    ├── update/
    │   └── data_loader.py # Inbox/local data loading
    ├── schedule/
    │   └── task_registry.py # Task storage and operations
    └── json/
        └── json_handler.py
```

---

## Modules

| Module | Command | Description |
|--------|---------|-------------|
| `update.py` | `update` | Status digest for DEV_CENTRAL - inbox status, actionable items, session info, escalations |
| `schedule.py` | `schedule` | Fire-and-forget scheduled follow-ups - create, list, delete, run-due |

---

## Memory Files

- **ASSISTANT.id.json** - Branch identity (permanent)
- **ASSISTANT.local.json** - Session history (max 600 lines, auto-rolls)
- **ASSISTANT.observations.json** - Collaboration patterns (max 600 lines, auto-rolls)
- **DASHBOARD.local.json** - System-wide status snapshot

---

## Dependencies

Key imports from aipass_core:
- `prax.apps.modules.logger` - System logging
- `cli.apps.modules` - Console/header formatting

---

*Last Updated: 2026-02-05*
