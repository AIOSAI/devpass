# AI_MAIL Email Lifecycle v2

**Created**: 2025-11-30
**Branch**: AI_MAIL
**Status**: ✅ WORKING - Minimal Testing (2025-11-30)
**Previous**: ai_mail_improvements.md (2025-11-27)

## Implementation Status

| Phase | Status | Completed |
|-------|--------|-----------|
| Phase 1: Schema + Migration | ✅ COMPLETED | 2025-11-30 |
| Phase 2: View + Close Commands | ✅ COMPLETED | 2025-11-30 |
| Phase 3: Reply Command | ✅ COMPLETED | 2025-11-30 |
| Phase 4: Hook Notification | ⚠️ BUILT - UNTESTED | 2025-11-30 |
| Phase 5: Documentation + Polish | ✅ COMPLETED | 2025-11-30 |

**Email Lifecycle v2 working with minimal testing. Hook needs session restart to test.**

**Testing Notes (2025-11-30):**
- Core commands (view, close, reply) tested and working
- Hook created and registered, needs new session to verify injection
- Inbox now shows message IDs for easy copy-paste
- Same-branch testing can be confusing (reply goes back to own inbox)

---

## What Changed Since v1

| Item | v1 (Nov 27) | v2 (Nov 30) |
|------|-------------|-------------|
| Status field | `read: true/false` | `status: new/opened/closed` |
| Summary files | `[BRANCH].ai_mail.json` | **Deprecated** - dashboard only |
| Notifications | None | UserPromptSubmit hook |
| Reply support | None | `reply <id> "msg"` auto-closes |
| Archive trigger | `read` command | `close` or `reply` command |

---

## The 3-State Model

### States

| State | Meaning | Transition |
|-------|---------|------------|
| `new` | Just delivered, never viewed | Email arrives |
| `opened` | Viewed but not resolved | Branch views inbox |
| `closed` | Resolved, ready for archive | `reply` or `close` command |

### Lifecycle Flow

```
Email sent to @branch
        ↓
    [DELIVERY]
        ↓
inbox.json → status: "new"
        ↓
    [HOOK FIRES]
    "AI_MAIL: 1 new email from @seed"
        ↓
Branch views inbox → status: "opened"
        ↓
    [BRANCH DECIDES]
        ↓
    ┌───────────────────┬────────────────────┐
    │                   │                    │
reply <id> "msg"    close <id>         (do nothing)
    │                   │                    │
status: "closed"   status: "closed"    stays "opened"
+ send reply       (no reply)          (pile up risk)
    │                   │
    └───────────────────┘
              ↓
    [AUTO-ARCHIVE]
    moved to deleted.json
```

---

## Schema Changes

### Current inbox.json
```json
{
  "messages": [
    {
      "id": "abc123",
      "from": "@seed",
      "subject": "Code Review",
      "message": "...",
      "read": false  // <-- OLD: boolean
    }
  ]
}
```

### New inbox.json
```json
{
  "messages": [
    {
      "id": "abc123",
      "from": "@seed",
      "from_name": "SEED Branch",
      "subject": "Code Review",
      "message": "...",
      "status": "new",           // <-- NEW: new/opened/closed
      "timestamp": "2025-11-30 12:00:00",
      "thread_id": null,         // <-- NEW: for reply chains
      "reply_to": null           // <-- NEW: original message id if reply
    }
  ]
}
```

### Migration
- Existing `read: false` → `status: "new"`
- Existing `read: true` → `status: "opened"`
- Migration runs once on first email operation

---

## Commands

### Updated Command Set

| Command | Action | Status Change |
|---------|--------|---------------|
| `inbox` | Lists all emails (new + opened) | None - just viewing list |
| `view <id>` | Shows full email content | `new` → `opened` |
| `reply <id> "msg"` | Sends reply + archives original | `opened` → `closed` → deleted |
| `close <id>` | Closes without reply + archives | `opened` → `closed` → deleted |
| `send @branch "Subj" "Msg"` | Send new email | Creates in recipient inbox |
| `sent` | View sent emails | None |

### Renamed Commands

| Old | New | Reason |
|-----|-----|--------|
| `read <id>` | `view <id>` | "read" implies memory, "view" is action |
| `read all` | Removed | Don't bulk-open, view individually |

### Command Help Output

```
AI_MAIL Commands:

  inbox                              List emails (new + opened)
  view <id>                          View email content (marks as opened)
  reply <id> "message"               Reply to email (closes + archives)
  close <id>                         Close without reply (archives)
  send @branch "Subject" "Message"   Send new email
  send @all "Subject" "Message"      Broadcast to all branches
  sent                               View sent emails
```

### Email Footer (auto-added to each email)

```
---
Actions:
  view abc123          View and mark as opened
  reply abc123 "msg"   Reply to sender
  close abc123         Close without reply
```

---

## Hook: Real-Time Notification

### Location
`/home/aipass/.claude/hooks/email_notification.py`

### Trigger
`UserPromptSubmit` - fires on every prompt

### Behavior
1. Detect branch from CWD (same as identity_injector.py)
2. Find branch's `ai_mail.local/inbox.json`
3. Count messages with `status: "new"` only
4. If `new > 0`, output notification
5. If `new == 0` but `opened > 0`, optional soft reminder

### Output Format

**New emails exist** (always notify):
```
AI_MAIL: 2 new emails
  @seed - "Code Review Request"
  @prax - "Memory Alert"
```

**Only opened emails** (soft reminder, less intrusive):
```
AI_MAIL: 3 open emails awaiting resolution
```

**No action needed** (no output):
- `new == 0` and `opened == 0` → silent

### Key Principle
- **New = active notification** (you haven't seen this)
- **Opened = passive reminder** (you've seen it, decide when to resolve)
- Once you `view <id>`, notification stops for that email

### Configuration
```json
// ~/.claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/home/aipass/.claude/hooks/email_notification.py"
          }
        ]
      }
    ]
  }
}
```

---

## Decisions (2025-11-30)

### 1. Pile-up Prevention
**Decision**: Trust branches to manage their inbox

**Rationale**:
- Branches may not be active for weeks (e.g., git_repo)
- When they come back, they process all pending emails
- Example: MCP_SERVERS had 7 emails, acknowledged 5 outdated, checked 1, discussed 2
- NO auto-close after X days - emails should persist until resolved

**Closed = Auto-Archive**:
- Once status = "closed", immediately move to deleted.json
- Trigger-based cleanup (system has many trigger mechanisms)
- No manual cleanup needed for closed emails

### 2. Notification Behavior
**Decision**: Notify on "new" only, stop when "opened"

**Flow**:
- `new` email → hook fires notification
- Email marked `opened` → notification stops
- Next session: branch sees "X open emails" in inbox check, but no hook notification
- Prevents notification fatigue while surfacing new mail

**Format**: TBD - start minimal, can add subjects later

### 3. Reply Threading
**Decision**: Future implementation

**For now**: Direct back-and-forth replies, no thread linking
**Why defer**: 50 replies = context/token killer. Simple is better for now.

### 4. What Triggers "Opened"?
**Decision**: Viewing the email content (not just listing inbox)

**Why "opened" not "read"**:
- "read" implies AI remembers it - but context doesn't persist
- AI might think "already read, skip it"
- "opened" = "I've seen this exists, may or may not have processed"
- Opens the door for AI to say "let me check my open emails to resolve them"

**Flow**:
- `inbox` command → Lists all emails (new + opened) - NO status change
- `view <id>` command → Shows email content, marks as "opened"
- `reply <id>` → Sends reply + closes + archives
- `close <id>` → Closes without reply + archives

**Key insight**: Viewing inbox ≠ opening emails. Must explicitly view individual email.

**Email instructions**: Each email includes footer with instructions:
- "To mark as opened: `view <id>`"
- "To reply: `reply <id> 'message'`"
- "To close: `close <id>`"

### 5. Terminology
**Decision**: Use these terms consistently

| Term | Meaning |
|------|---------|
| `new` | Just arrived, never viewed |
| `opened` | Content has been viewed, not yet resolved |
| `closed` | Resolved (replied or dismissed), ready for archive |
| `deleted` | Archived storage (closed emails go here) |
| `sent` | Outgoing emails (sends + replies) |

---

## Implementation Phases (Flow Plan Execution)

**Execution Model**: Each phase = Flow sub-plan → Execute → Close → Update memories

---

### Phase 1: Schema + Migration
**Goal**: Change from `read: bool` to `status: new/opened/closed`

**Tasks**:
- [ ] Update `delivery.py` - set `status: "new"` on email creation
- [ ] Create migration handler - converts existing `read` to `status`
- [ ] Update inbox display to show status badges
- [ ] Test: send email, verify `status: "new"` in recipient inbox

**Files to modify**:
- `apps/handlers/email/delivery.py`
- `apps/handlers/email/create.py`
- New: `apps/handlers/email/migration.py`

**Definition of Done**: New emails arrive with `status: "new"`, existing emails migrated

---

### Phase 2: View + Close Commands
**Goal**: Implement `view <id>` and `close <id>` lifecycle commands

**Tasks**:
- [ ] Rename `read` command to `view` in email.py
- [ ] Update `view <id>` to mark `status: "opened"` (no archive)
- [ ] Add `close <id>` command - marks `closed` + archives to deleted.json
- [ ] Update dashboard counts after status changes
- [ ] Test: view email → status changes to opened, close → moves to deleted

**Files to modify**:
- `apps/modules/email.py`
- `apps/handlers/email/inbox_cleanup.py` (refactor for new model)

**Definition of Done**: `view` marks opened, `close` archives, dashboard syncs

---

### Phase 3: Reply Command
**Goal**: Enable `reply <id> "msg"` that sends + auto-closes

**Tasks**:
- [ ] Add `reply <id> "message"` command to email.py
- [ ] Create reply handler - sends email to original sender
- [ ] Auto-close original email after reply sent
- [ ] Add reply to sent folder
- [ ] Test: reply to email → reply in sent, original closed + archived

**Files to modify**:
- `apps/modules/email.py`
- New: `apps/handlers/email/reply.py`

**Definition of Done**: Reply sends to original sender, original email auto-closes

---

### Phase 4: Hook Notification
**Goal**: Real-time mail awareness via UserPromptSubmit hook

**Tasks**:
- [ ] Create `email_notification.py` in ~/.claude/hooks/
- [ ] Implement branch detection (reuse identity_injector pattern)
- [ ] Count `status: "new"` emails, output notification
- [ ] Optional: soft reminder for `opened` emails
- [ ] Register hook in settings.json
- [ ] Test: new email → hook fires notification

**Files to create**:
- `/home/aipass/.claude/hooks/email_notification.py`

**Files to modify**:
- `~/.claude/settings.json`

**Definition of Done**: Hook notifies on new emails, stops when opened

---

### Phase 5: Documentation + Polish
**Goal**: Update all docs, test full lifecycle

**Status**: ✅ COMPLETED (2025-11-30)

**Tasks**:
- [x] Update README.md with new commands
- [x] Update --help output in email.py
- [x] Full lifecycle test: send → view → reply/close → archive
- [x] Edge cases: empty inbox, invalid id, etc.
- [N/A] Update branch_system_prompt.md (file does not exist)

**Definition of Done**: All docs current, full lifecycle works end-to-end

**Notes**:
- README.md updated with Email Lifecycle v2 section, flow diagram, and changelog
- --help output in email.py comprehensively updated with all v2 commands
- Backward compatibility documented (`read` as alias for `view`)
- No branch_system_prompt.md found - not needed (CLAUDE.md serves this purpose)

---

## Files to Modify

**Handlers:**
- `apps/handlers/email/delivery.py` - Set `status: "new"` on delivery
- `apps/handlers/email/inbox_cleanup.py` - Update for 3-state model
- `apps/handlers/email/create.py` - Add reply support

**Module:**
- `apps/modules/email.py` - Add `close` and `reply` commands

**New Files:**
- `/home/aipass/.claude/hooks/email_notification.py`

**Config:**
- `~/.claude/settings.json` - Register hook

---

## Notes

- Dashboard sync still works (updates on delivery)
- Summary files `[BRANCH].ai_mail.json` are deprecated and deleted
- PWD detection for sender identity unchanged
- Deleted.json remains the archive destination
- AI_MAIL already has notification handlers (from error_notification work) - can reuse

---

## Future Vision: P-Prompt Automation (Side Notes)

**Not for now - capturing for future reference**

### Concept: Automated System Healing

Email + P-Prompt triggers could enable:
1. Error detection flags an issue
2. System sends notification email to responsible branch
3. Email flagged with priority: `minor` / `medium` / `critical`
4. Minor flags trigger automatic P-prompt to branch
5. Background agent spawns to fix the bug
6. Response email sent back: "Bug fixed" or "Needs attention"

### Example Flow
```
Error in DRONE detected
    ↓
AI_MAIL sends: "@drone - Minor bug in route handler" [priority: minor]
    ↓
P-Prompt trigger sees [minor] flag
    ↓
Spawns DRONE agent in background: "Fix the bug described in email"
    ↓
Agent investigates, fixes, responds
    ↓
Email back to sender: "Fixed - see commit abc123"
```

### Priority Levels
- `minor` - Auto-fix with background agent
- `medium` - Notify, wait for human decision
- `critical` - Immediate attention, multiple notifications

### Why This Matters
- Self-healing system
- Reduces manual intervention
- Branches can fix issues without human in the loop
- Human reviews the fix, not the bug

**Status**: Vision captured. Implement after email lifecycle v2 is stable.

---

## Future Vision: Email Classification & Auto-Expiry

**Added**: 2025-11-30 (from SEED feedback session)
**Status**: Ideas captured for future implementation

### Problem Statement
Branches that are inactive for long periods (e.g., MCP_SERVERS going months without activity) accumulate many emails. When returning, the branch faces 100+ emails, most of which are no longer relevant.

### Proposed Solution: Classification-Based Auto-Expiry

#### Email Classifications

| Classification | Examples | TTL | On Expiry |
|----------------|----------|-----|-----------|
| `critical` | Bug reports, issues, action required | Never | Return to sender |
| `important` | Feedback, requests | 30 days | Return to sender |
| `info` | System updates, compliance reports | 7 days | Silent delete |
| `test` | Test emails, debugging | 24 hours | Silent delete |

#### Detection Methods (TBD)
- **Keyword-based**: Subject contains "Bug", "Critical", "Issue" → `critical`
- **Explicit tags**: Sender specifies `[CRITICAL]` in subject
- **Sender-based**: Emails from certain branches default to certain classifications

#### Return-to-Sender for Expired Critical Emails
```
→ Auto-send notification to original sender
→ "Your email to @mcp_servers was not read after 30 days"
→ "Subject: Bug Report - Memory Leak"
→ "Reply 'resend' to send again"
```

### Batch Operations (Implemented 2025-11-30)

```bash
close <id>                  # Close single email
close <id1> <id2> <id3>     # Close multiple emails
close all                   # Close all emails in inbox
```

### Open Questions
1. How to configure TTLs per branch? (some branches more active than others)
2. Should classification be automatic or require sender to specify?
3. How to handle edge cases (critical email sent to wrong branch)?

### Why Defer
- Need to observe natural email patterns first
- v2 lifecycle just launched - see how it works in practice
- Classification system adds complexity - only build if truly needed

**Next Step**: Observe system for 2-4 weeks, collect feedback on email pile-up patterns
