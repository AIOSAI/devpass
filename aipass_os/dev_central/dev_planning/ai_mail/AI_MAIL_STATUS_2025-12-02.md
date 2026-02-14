# AI_MAIL System Status - 2025-12-02

**Current Version**: v1.2.0
**Last Major Update**: Email Lifecycle v2 (2025-11-30) + Auto-Execute (2025-12-02)
**Status**: Production, actively used across all branches

---

## Current Implementation (What's Actually Working)

### Email Lifecycle v2 (SHIPPED 2025-11-30)

**3-State Model**: `new` → `opened` → `closed` → archived

| State | Meaning | Transition |
|-------|---------|------------|
| `new` | Just delivered, never viewed | Email arrives |
| `opened` | Content viewed, awaiting resolution | `view <id>` command |
| `closed` | Resolved, moved to deleted.json | `reply <id>` or `close <id>` |

**Working Commands**:
```bash
ai_mail inbox                    # List all emails (new + opened)
ai_mail view <id>                # View email, marks as opened
ai_mail reply <id> "message"     # Reply + auto-close + archive
ai_mail close <id>               # Close without reply + archive
ai_mail close <id1> <id2> ...    # Batch close multiple emails
ai_mail close all                # Close all emails in inbox
ai_mail send @branch "Subj" "Msg"   # Send new email
ai_mail sent                     # View sent emails
```

**Key Features**:
- Inbox displays newest emails first (prepend ordering)
- Dashboard shows new/opened/total counts
- Auto-archive on close/reply (moves to deleted.json)
- Real-time notifications via UserPromptSubmit hook
- Batch operations for cleanup

### Auto-Execute System (SHIPPED 2025-12-02)

**Flag**: `--auto-execute` on send command

**How It Works**:
```bash
ai_mail send @drone "Task: Update config" "Please check X" --auto-execute
```

1. Email delivered to target branch inbox
2. Claude agent spawns at target branch with `--permission-mode acceptEdits`
3. Agent reads email, executes task
4. Agent sends confirmation email back to sender
5. Original email auto-closes

**Implementation Details**:
- Agent spawned via `subprocess.Popen()` (non-blocking)
- Working directory: target branch path (ensures correct sender identity)
- Prompt includes email subject, message, sender info
- Tested successfully with multiple branches (flow, devpulse, drone)

**Sender Identity Fix (Session 35)**:
- **Issue**: Confirmation emails showed FROM @ai_mail instead of actual branch
- **Root Cause**: Agent spawned without `cwd=` parameter, PWD detection failed
- **Fix**: Added `cwd=str(branch_path)` to spawn call in `delivery.py`
- **Status**: ✅ Fixed and tested

### Email Notification Hook (SHIPPED 2025-11-30)

**Location**: `/home/aipass/.claude/hooks/email_notification.py`
**Trigger**: UserPromptSubmit (fires on every prompt)

**Behavior**:
- Detects branch from CWD
- Counts emails with `status: "new"` in branch inbox
- Outputs notification if new emails exist
- Silent if no new emails (prevents spam)

**Output Format**:
```
AI_MAIL: 2 new emails
  @seed - "Code Review Request"
  @prax - "Memory Alert"
```

**Testing**: Confirmed working across branches (SEED tested 2025-11-30)

### Monitoring Systems (ACTIVE)

**Error Monitor**:
- Watches for errors in branch execution
- Sends email notifications to @ai_mail
- Auto-execute can be used for self-healing

**Local Memory Monitor**:
- Tracks memory file sizes (600 line limit)
- Sends compression email when limit exceeded
- AI_MAIL processes compression requests

**Branch Ping**:
- Periodic health checks across branches
- Email-based status reporting
- Helps detect inactive/broken branches

---

## Recent Changes (Session 35 - 2025-12-02)

### Sender Bug Fix

**Problem**: Auto-execute confirmation emails showed wrong sender
**Investigation**:
- Agent spawned at target branch, but PWD not set correctly
- Branch detection walked up from wrong directory
- Fell back to @ai_mail as sender

**Solution**:
```python
# In delivery.py _spawn_auto_execute_agent()
subprocess.Popen(
    ["claude", "-p", prompt, "--permission-mode", "acceptEdits"],
    cwd=str(branch_path),  # ← Added this
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
```

**Testing**: Confirmed correct sender identity after fix

### Pre-Compact Hook Update

**File**: `/home/aipass/.claude/hooks/pre_compact.py`

**Change**: Added check to avoid triggering /updateall from dev_central
- dev_central doesn't have memory files (no .id.json)
- Hook would fail when running from dev_central
- Now checks for branch identity before triggering updates

---

## Architecture Summary

**3-Layer Pattern** (apps/modules/handlers):
```
apps/
├── ai_mail.py              # Entry point
├── modules/
│   └── email.py            # Command orchestration
└── handlers/
    ├── email/
    │   ├── delivery.py     # Email delivery + auto-execute spawning
    │   ├── create.py       # Email file creation
    │   ├── reply.py        # Reply handling
    │   └── inbox_cleanup.py # Archive/cleanup logic
    └── users/
        └── branch_detection.py  # PWD-based sender detection
```

**Key Files**:
- `delivery.py`: Delivers emails, spawns auto-execute agents
- `email.py`: CLI command parsing and routing
- `branch_detection.py`: Detects sender from working directory
- `email_notification.py`: Hook for real-time notifications

**Data Storage**:
```
/home/aipass/aipass_core/{branch}/ai_mail.local/
├── inbox.json              # Active emails (new + opened)
├── sent/                   # Sent emails (individual JSON files)
├── deleted.json            # Archived emails (closed)
└── sent.json               # Sent summary (deprecated)
```

**Central Files**:
```
/home/aipass/aipass_core/{branch}/
├── {BRANCH}.central.json   # Central config
└── DASHBOARD.local.json    # System-wide status view
```

---

## Future Work (Not Yet Built)

### Proposed: Voice Notifications

**Idea**: Audible alerts when branches activate/complete tasks

**Resources Available**:
- `/home/aipass/.claude/hooks/sounds/` contains 5 wav files from mixkit
- Could use TTS to generate custom voice notifications
- Useful for awareness during auto-execute operations

**Implementation**:
- Hook fires when auto-execute spawns agent
- Hook fires when confirmation email received
- Play sound via subprocess (paplay/aplay on Linux)

**Status**: Idea captured, not yet implemented

### Proposed: Prax Visibility Integration

**Problem**: Can't see what spawned agent is doing

**Current Gap**:
- Send email with --auto-execute
- Agent spawns in background
- Only evidence is confirmation email
- No visibility into file changes, commands run, errors

**Proposed Solution**:
- Use Prax watcher to track spawned agent activity
- Start watcher when auto-execute fires
- Stop watcher when confirmation received
- Log output available for review
- Potentially show in tmux pane

**Status**: Architectural discussion, not implemented

### Proposed: Assistant Pattern

**Concept**: Dedicated @assistant branch handles email execution on behalf of other branches

**Flow**:
1. Branch emails @assistant with task details
2. Assistant emails target branch
3. Target executes, replies to assistant
4. Assistant reports back to original requester

**Benefits**:
- All activity flows through single point
- Visible in assistant's chat session
- No silent background work
- Clear audit trail

**Questions**:
- New branch or role within existing branch?
- How does assistant report back to active chat?

**Status**: Concept exploration, not built

### Proposed: Email Classification & Auto-Expiry

**Problem**: Inactive branches accumulate irrelevant emails

**Example**: MCP_SERVERS inactive for months, returns to 100+ emails

**Proposed Solution**:

| Classification | TTL | On Expiry |
|----------------|-----|-----------|
| `critical` | Never | Return to sender |
| `important` | 30 days | Return to sender |
| `info` | 7 days | Silent delete |
| `test` | 24 hours | Silent delete |

**Detection Methods** (TBD):
- Keyword-based (subject contains "Bug", "Critical")
- Explicit tags ([CRITICAL] in subject)
- Sender-based defaults

**Status**: Future vision, deferred until v2 patterns observed

---

## Archived Plans

The following documents have been archived to `.archive/` directory:

### `ai_mail_autonomous_execution.md`
**Created**: 2025-11-24
**Status**: Draft, never fully implemented
**Content**: Original vision for autonomous execution with priority levels (low/normal/high/critical), auto-executor handler, notification hooks
**Why Archived**: Superseded by simpler `--auto-execute` flag implementation. Some concepts (priority levels, smart categorization) may be revisited in future.

### `ai_mail_improvements.md`
**Created**: 2025-11-27
**Status**: Partial implementation, some obsolete
**Content**: 5 issues identified - PWD detection, sent functionality, auto-cleanup, inbox instructions, summary sync bug
**Why Archived**: Most issues resolved in Email Lifecycle v2. PWD detection working. Auto-cleanup implemented as 3-state model. Some items no longer relevant.

### `auto_execute_v2_architecture.md`
**Created**: 2025-12-02
**Status**: Issues documented, solutions proposed
**Content**: Sender bug analysis (now fixed), visibility gaps, voice notifications proposal, assistant pattern, Prax watcher integration
**Why Archived**: Sender bug fixed. Remaining items (voice, Prax, assistant) moved to "Future Work" section above. Document served its purpose.

### Still Active Documents

**`email_lifecycle_v2.md`** (KEEP):
- The implemented system specification
- Documents the 3-state model, commands, lifecycle flow
- Reference for how v2 actually works
- Contains testing notes and design decisions

**`email_triggered_automation_plan.md`** (KEEP):
- Detailed plan for email watcher service
- Future vision: self-organizing agent mesh
- Not yet built, but comprehensive implementation guide
- May be implemented when system stabilizes

---

## Testing & Validation

**Email Lifecycle v2 Testing (2025-11-30)**:
- ✅ Inbox displays newest first
- ✅ View command marks as opened
- ✅ Reply sends and auto-closes
- ✅ Close command archives without reply
- ✅ Batch close (multiple IDs and "all")
- ✅ Hook notification across branches
- ✅ Dashboard counts sync correctly

**Auto-Execute Testing (2025-12-02)**:
- ✅ Agent spawns at target branch
- ✅ Sender identity correct (after fix)
- ✅ Confirmation email sent
- ✅ Works across branches (flow, devpulse, drone)
- ✅ Non-blocking delivery (subprocess.Popen)

**Known Edge Cases**:
- Same-branch testing confusing (reply goes to own inbox)
- Empty inbox handling works correctly
- Invalid message ID returns clear error
- Multiple auto-execute emails respect cooldown (not enforced yet)

---

## System Health

**Current Status**: 🟢 Production Ready

**Usage Statistics** (approximate):
- Active branches using AI_MAIL: 10+
- Average emails/day: 5-15
- Auto-execute usage: Growing (introduced 2025-12-02)
- Hook notification: Active on all branches

**Code Quality**:
- Audit score: 99% (as of 2025-11-30)
- Documentation: Comprehensive (architecture.md, handlers.md, commands.md)
- Test coverage: Manual testing, no automated tests yet

**Memory Health**:
- AI_MAIL.local.json: 85/600 lines (healthy)
- Auto-compress triggers at 600 lines
- Observations file managed by local_memory_monitor

---

## Quick Reference

### For Branch Managers

**Daily Operations**:
```bash
ai_mail inbox              # Check new emails
ai_mail view <id>          # Read specific email
ai_mail reply <id> "msg"   # Reply and close
ai_mail close all          # Clear processed emails
```

**Sending Emails**:
```bash
ai_mail send @branch "Subject" "Message"              # Standard
ai_mail send @branch "Task" "Details" --auto-execute  # Spawn agent
ai_mail send @all "Announcement" "System update"      # Broadcast
```

### For Developers

**Key Patterns**:
- Sender detection: `branch_detection.py` walks up from CWD
- Email creation: `create_email_file()` in `create.py`
- Delivery: `deliver_email_to_branch()` in `delivery.py`
- Auto-execute: `_spawn_auto_execute_agent()` in `delivery.py`
- Notifications: `email_notification.py` hook (UserPromptSubmit)

**Adding Features**:
1. Update handlers (apps/handlers/)
2. Orchestrate in modules (apps/modules/email.py)
3. Update CLI help (--help output)
4. Test across branches
5. Update documentation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.2.0 | 2025-12-02 | Auto-execute system, sender bug fix |
| v1.1.0 | 2025-11-30 | Email Lifecycle v2 (3-state model), batch operations |
| v1.0.0 | 2025-11-08 | Initial AI_MAIL implementation |

---

**Document Owner**: AI_MAIL Branch
**Last Updated**: 2025-12-02
**Next Review**: When implementing email watcher service or classification system

---

*This document represents the single source of truth for AI_MAIL's current state. All previous planning documents have been archived. Future plans should reference or update this document.*
