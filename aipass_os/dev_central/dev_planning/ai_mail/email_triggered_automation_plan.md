# Email-Triggered Automation System - Implementation Plan

**Date:** 2025-11-19
**Status:** Planning Phase
**Owner:** AIPASS
**Goal:** Transform AIPass into a self-organizing agent mesh with email-based task automation

---

## Executive Summary

This system enables branches to autonomously execute tasks when they receive email, eliminating manual `claude -p` commands. A watcher service monitors all branch inboxes and triggers autonomous execution when new messages arrive.

**Key Achievement from Testing (2025-11-19):**
- Successfully executed autonomous cleanup tasks across 8 branches (API, DRONE, PRAX, FLOW, BACKUP_SYSTEM, AI_MAIL, CORTEX, DEVPULSE)
- All branches completed error_handler removal autonomously using `claude -p --permission-mode acceptEdits`
- 100% success rate, all tests passed, memories updated, confirmation emails sent

---

## Architecture Overview

### Core Concept: Self-Healing Agent Mesh

Branches become autonomous workers that:
1. Monitor their own inbox for new messages
2. Auto-execute tasks when emails arrive
3. Report completion back via email
4. Log all activity for observability

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Email Automation System                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │ Email Watcher    │────────▶│ Branch Executor  │          │
│  │ Service          │         │ (claude -p)      │          │
│  └──────────────────┘         └──────────────────┘          │
│          │                             │                     │
│          │                             │                     │
│          ▼                             ▼                     │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │ Branch Registry  │         │ Execution Logs   │          │
│  │ (who to watch)   │         │ (what happened)  │          │
│  └──────────────────┘         └──────────────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │         Watched Branch Inboxes               │
        ├─────────────────────────────────────────────┤
        │  /aipass_core/api/ai_mail.local/inbox.json  │
        │  /aipass_core/drone/ai_mail.local/inbox.json│
        │  /aipass_core/prax/ai_mail.local/inbox.json │
        │  ... (all branches)                          │
        └─────────────────────────────────────────────┘
```

---

## Component Details

### 1. Email Watcher Service (NEW)

**Location:** `/home/aipass/aipass_core/prax/apps/modules/email_watcher.py`

**Purpose:** Monitor all branch inboxes and trigger autonomous execution

**Responsibilities:**
- Watch all `ai_mail.local/inbox.json` files for changes
- Detect new unread messages
- Trigger `claude -p` execution for branches with new mail
- Rate limiting to prevent loops
- Logging of all triggers

**Pseudo-code:**
```python
def watch_branch_inboxes():
    for branch in get_registered_branches():
        inbox_path = f"/home/aipass/aipass_core/{branch}/ai_mail.local/inbox.json"

        on_file_change(inbox_path):
            if has_unread_messages(inbox_path):
                if not in_cooldown(branch):
                    trigger_execution(branch)
                    mark_cooldown(branch, duration=300)  # 5 min

def trigger_execution(branch):
    cmd = f"""
    cd /home/aipass/aipass_core/{branch} && \
    claude -p "You have new email. Read ai_mail.local/inbox.json and complete requested tasks. \
    Use agents as needed. Update memories. Send reply when done." \
    --permission-mode acceptEdits &
    """
    subprocess.run(cmd, shell=True)
    log_execution(branch, timestamp, cmd)
```

**Integration with PRAX:**
```bash
# Start watching
python3 /home/aipass/aipass_core/prax/apps/modules/email_watcher.py start

# Via drone
drone @prax email-watcher start
drone @prax email-watcher stop
drone @prax email-watcher status
```

---

### 2. Branch Registry (EXISTING - TO EXTEND)

**Location:** `/home/aipass/aipass_core/prax/BRANCH_REGISTRY.json`

**Current Structure:**
```json
{
  "branches": [
    {
      "name": "api",
      "path": "/home/aipass/aipass_core/api",
      "active": true
    }
  ]
}
```

**Extended Structure:**
```json
{
  "branches": [
    {
      "name": "api",
      "path": "/home/aipass/aipass_core/api",
      "active": true,
      "email_automation": {
        "enabled": true,
        "mode": "auto",  // auto | notify | manual
        "priority": "normal",  // high | normal | low
        "cooldown_seconds": 300,
        "max_retries": 0
      }
    }
  ]
}
```

**Fields:**
- `enabled`: Opt-in to email automation
- `mode`:
  - `auto` - Execute immediately on new email
  - `notify` - Send notification, require approval
  - `manual` - No automation (current state)
- `priority`: Execution order when multiple branches have email
- `cooldown_seconds`: Minimum time between auto-executions
- `max_retries`: Retry failed executions (0 = no retry)

---

### 3. PRAX Watcher Integration (EXISTING)

**Already Available:**
- **Branch File Watcher:** `/home/aipass/aipass_core/prax/apps/modules/branch_watcher.py`
  - Monitors all file changes across branches
  - Uses `watchdog` library (FileSystemObserver)
  - Real-time terminal output with colors

- **Watcher Infrastructure:**
  - Monitor handler: `apps/handlers/watcher/monitor.py`
  - Reporter handler: `apps/handlers/watcher/reporter.py`
  - Discovery watcher: `apps/handlers/discovery/watcher.py`

**Reuse Strategy:**
- Email watcher extends existing branch_watcher patterns
- Uses same FileSystemObserver infrastructure
- Adds email-specific event handlers
- Shares logging and reporting mechanisms

---

### 4. Execution Logging (NEW)

**Location:** `/home/aipass/system_logs/email_automation_{date}.log`

**Format:** JSON Lines (one JSON object per line)

**Entry Structure:**
```json
{
  "timestamp": "2025-11-19T05:24:18.920Z",
  "event": "execution_triggered",
  "branch": "api",
  "trigger": "new_email",
  "email_subject": "Error Handler Cleanup",
  "email_from": "@seed",
  "execution_id": "d462d7",
  "status": "started",
  "command": "cd /home/aipass/aipass_core/api && claude -p..."
}
```

```json
{
  "timestamp": "2025-11-19T05:27:08.063Z",
  "event": "execution_completed",
  "branch": "api",
  "execution_id": "d462d7",
  "exit_code": 0,
  "duration_seconds": 172,
  "files_modified": 2,
  "status": "success"
}
```

**Query Examples:**
```bash
# See all executions today
cat /home/aipass/system_logs/email_automation_$(date +%Y-%m-%d).log

# Count successes
cat email_automation_*.log | jq 'select(.status=="success")' | wc -l

# Failed executions
cat email_automation_*.log | jq 'select(.exit_code!=0)'
```

---

## Safety & Control Features

### 1. Rate Limiting

**Problem:** Prevent infinite email loops (branch A emails branch B, B replies, A replies...)

**Solution:**
- Track last execution time per branch
- Enforce minimum cooldown (default: 5 minutes)
- Configurable per branch in registry
- Manual override: `drone @prax email-watcher trigger api --force`

### 2. Execution Modes

**Auto Mode:**
- Execute immediately when email arrives
- Best for: trusted branches, routine tasks
- Risk: errors propagate quickly

**Notify Mode:**
- Send desktop/terminal notification
- Require user approval to execute
- Best for: critical branches, complex tasks
- Command: `approve api` or `reject api`

**Manual Mode:**
- No automation (current state)
- Email watcher ignores this branch
- Best for: development, testing

### 3. Kill Switch

**Global Disable:**
```bash
# Stop all automation
drone @prax email-watcher stop

# Or remove enable file
rm /home/aipass/.aipass/automation_enabled
```

**Per-Branch Disable:**
```json
{
  "name": "api",
  "email_automation": {
    "enabled": false  // Temporarily disable
  }
}
```

### 4. Audit Trail

**All executions logged with:**
- Who triggered (which branch sent email)
- What was requested (email subject/content hash)
- When it ran (timestamp)
- What happened (exit code, files changed, errors)
- How long it took (duration)

**Review commands:**
```bash
# Last 10 executions
drone @prax email-watcher history --limit 10

# Failures only
drone @prax email-watcher history --failed

# Specific branch
drone @prax email-watcher history --branch api
```

---

## User Workflows

### Scenario 1: Routine Maintenance Task

**User Action:**
```bash
# Send cleanup task to all branches
drone @ai_mail send @all "Update Dependencies" "Run pip list --outdated, update minor versions, test."
```

**System Response:**
1. Email watcher detects 8 new messages
2. Triggers 8 parallel executions (respecting cooldowns)
3. Each branch:
   - Reads email
   - Checks outdated packages
   - Updates safe versions
   - Runs tests
   - Sends confirmation email
4. User receives 8 confirmations
5. Reviews `git diff` to verify changes

**User Effort:** 1 command + review (vs. 8 manual executions)

---

### Scenario 2: Error Notification & Auto-Diagnosis

**Trigger Event:** API throws error "OpenAI API key missing"

**AI_MAIL Action:**
```python
# Automatic error notification
send_email(
    to="@api",
    subject="Error: OpenAI API key missing",
    body="Production error detected. Please diagnose and report."
)
```

**System Response:**
1. Email watcher triggers API branch
2. API reads error notification
3. API checks:
   - Environment variables
   - Config files
   - Vault/secrets
4. API sends diagnostic report:
   ```
   Subject: Re: Error diagnosis complete

   ROOT CAUSE: API key exists in vault but not in .env file
   IMPACT: All OpenAI calls failing since 2025-11-19 04:30
   RECOMMENDATION: Copy key from vault to .env or update config to use vault
   ```
5. User sees report, fixes root cause

**User Effort:** Review + fix (vs. manual diagnosis)

---

### Scenario 3: Branch-to-Branch Delegation

**DRONE needs code review:**
```python
# DRONE sends to SEED
drone @ai_mail send @seed "Code Review Request" \
  "Please review apps/modules/new_discovery.py for standards compliance. \
   Focus on: imports, error handling, documentation."
```

**System Response:**
1. SEED auto-executes
2. SEED reads DRONE's file
3. SEED checks against standards:
   - Imports (seed standard)
   - Error handling (prax logger usage)
   - Documentation (docstrings, headers)
4. SEED sends report:
   ```
   Subject: Re: Code review complete

   VIOLATIONS FOUND: 3
   - Missing module header with metadata
   - Using print() instead of logger
   - No docstring for discover_modules()

   See attached diff for fixes.
   ```
5. DRONE could:
   - Auto-apply simple fixes
   - Escalate complex issues to user
   - Send confirmation back to SEED

**User Effort:** None (fully autonomous) or review only

---

## Implementation Phases

### Phase 1: MVP (Week 1)

**Goal:** Prove the concept with one branch

**Deliverables:**
1. `email_watcher.py` - Basic watcher for API branch only
2. Monitors `/home/aipass/aipass_core/api/ai_mail.local/inbox.json`
3. Triggers `claude -p` on new unread messages
4. Logs to terminal (no file logging yet)
5. Manual start/stop only

**Testing:**
- Send test email to API
- Verify auto-execution
- Confirm completion email sent
- Validate git changes

**Success Criteria:** 3 successful autonomous executions in 24 hours

---

### Phase 2: Production (Week 2)

**Goal:** Roll out to all branches with safety features

**Deliverables:**
1. Watch all branches from BRANCH_REGISTRY
2. Rate limiting (5-minute cooldown)
3. JSON logging to `/home/aipass/system_logs/`
4. Execution modes (auto/notify/manual)
5. Kill switch functionality
6. Error handling and retry logic

**Testing:**
- Parallel execution of 8 branches
- Rate limit enforcement
- Failed execution handling
- Notify mode approval flow

**Success Criteria:**
- 7-day uptime without intervention
- 80%+ success rate on executions
- Zero infinite loops

---

### Phase 3: Intelligence (Week 3-4)

**Goal:** Add smart features and optimization

**Deliverables:**
1. Priority queue (high-priority emails first)
2. Smart retry on transient failures
3. Email threading (reply to conversations)
4. Cross-branch task coordination
5. Systemd service (auto-start on boot)
6. Dashboard for monitoring

**Features:**
- Detect related emails (threading)
- Batch similar tasks
- Learn from failures (avoid repeating)
- Estimate task duration
- Resource management (max parallel executions)

**Success Criteria:**
- Handle 50+ emails/day autonomously
- 95%+ success rate
- User intervention <5% of tasks

---

## Technical Specifications

### Dependencies

**Required (already in PRAX):**
- `watchdog` - File system monitoring
- `subprocess` - Process execution
- `json` - Inbox parsing

**Optional (future):**
- `systemd` - Service management
- `notify-send` - Desktop notifications
- `rich` - Terminal UI for status

### File Structure

```
/home/aipass/aipass_core/prax/
├── apps/
│   └── modules/
│       ├── email_watcher.py          # NEW: Main watcher service
│       └── branch_watcher.py         # EXISTING: File change watcher
├── apps/handlers/
│   └── watcher/
│       ├── monitor.py                # EXISTING: FileSystemObserver
│       ├── reporter.py               # EXISTING: Terminal output
│       └── email_trigger.py          # NEW: Email-specific handler
└── BRANCH_REGISTRY.json              # EXTENDED: Add automation config

/home/aipass/.aipass/
└── automation_enabled                # Kill switch (file presence = enabled)

/home/aipass/system_logs/
├── email_automation_2025-11-19.log   # Execution logs (JSON Lines)
├── email_automation_2025-11-20.log
└── ...
```

### Performance Characteristics

**Watchdog inotify (Linux):**
- Near-zero CPU when idle (<0.1%)
- Event-driven (no polling)
- Instant notification on file change
- Scales to 1000s of watched files

**Execution Overhead:**
- `claude -p` startup: ~2-3 seconds
- Parallel branches: No blocking
- Memory: ~200MB per claude instance
- Max recommended: 10 concurrent executions

**Failure Modes:**
- Inbox parse error → Skip, log warning
- Claude CLI unavailable → Disable automation, alert user
- Branch timeout (>10 min) → Kill process, log failure
- Disk full → Stop watcher, alert user

---

## Configuration Examples

### Minimal (MVP)

```json
{
  "branches": [
    {
      "name": "api",
      "path": "/home/aipass/aipass_core/api",
      "email_automation": {
        "enabled": true
      }
    }
  ]
}
```

### Production (All Features)

```json
{
  "watcher_config": {
    "global_enabled": true,
    "max_parallel_executions": 5,
    "default_cooldown_seconds": 300,
    "log_directory": "/home/aipass/system_logs",
    "notification_enabled": true
  },
  "branches": [
    {
      "name": "api",
      "path": "/home/aipass/aipass_core/api",
      "email_automation": {
        "enabled": true,
        "mode": "auto",
        "priority": "high",
        "cooldown_seconds": 180,
        "max_retries": 1,
        "timeout_seconds": 600
      }
    },
    {
      "name": "cortex",
      "path": "/home/aipass/aipass_core/cortex",
      "email_automation": {
        "enabled": true,
        "mode": "notify",  // Requires approval
        "priority": "normal"
      }
    },
    {
      "name": "dev_testing",
      "path": "/home/aipass/aipass_core/dev_testing",
      "email_automation": {
        "enabled": false,  // Manual only
        "mode": "manual"
      }
    }
  ]
}
```

---

## Command Reference

### Starting/Stopping

```bash
# Start email watcher
drone @prax email-watcher start

# Stop email watcher
drone @prax email-watcher stop

# Check status
drone @prax email-watcher status

# Enable globally
drone @prax email-watcher enable

# Disable globally (kill switch)
drone @prax email-watcher disable
```

### Manual Triggers

```bash
# Force trigger (bypass cooldown)
drone @prax email-watcher trigger api --force

# Trigger multiple branches
drone @prax email-watcher trigger api,drone,prax
```

### Monitoring

```bash
# View recent executions
drone @prax email-watcher history

# Failed only
drone @prax email-watcher history --failed

# Specific branch
drone @prax email-watcher history --branch api --limit 20

# Live monitoring (tail logs)
drone @prax email-watcher monitor
```

### Configuration

```bash
# Set cooldown for branch
drone @prax email-watcher config api --cooldown 600

# Change mode
drone @prax email-watcher config api --mode notify

# Disable branch
drone @prax email-watcher config api --disable
```

---

## Success Metrics

### Phase 1 (MVP)

- [ ] 1 branch (API) successfully monitored
- [ ] 3 autonomous executions completed
- [ ] 100% success rate
- [ ] Manual start/stop works
- [ ] Logs visible in terminal

### Phase 2 (Production)

- [ ] All 8 branches monitored
- [ ] 7 days uptime without crashes
- [ ] 80%+ execution success rate
- [ ] Rate limiting prevents loops
- [ ] JSON logs parseable

### Phase 3 (Intelligence)

- [ ] 50+ emails/day handled
- [ ] 95%+ success rate
- [ ] <5% require user intervention
- [ ] Auto-start on system boot
- [ ] Dashboard shows real-time status

---

## Risk Mitigation

### Risk 1: Infinite Email Loops

**Scenario:** Branch A emails B, B emails A, repeat forever

**Mitigation:**
- Mandatory cooldown (min 5 minutes)
- Max executions per hour (default: 6)
- Loop detection (same subject line threshold)
- Manual override: Kill switch

### Risk 2: Malicious/Erroneous Tasks

**Scenario:** Email instructs branch to delete files

**Mitigation:**
- `--permission-mode acceptEdits` only (no shell access)
- Branch can reject unsafe operations
- All actions logged with git diff
- User reviews git changes before commit
- Rollback via `git restore`

### Risk 3: System Resource Exhaustion

**Scenario:** 20 branches execute simultaneously, OOM killer

**Mitigation:**
- Max parallel executions (default: 5)
- Priority queue (high-priority first)
- Timeout per execution (default: 10 min)
- Memory monitoring (alert at 80%)

### Risk 4: Watcher Service Crashes

**Scenario:** email_watcher.py dies, no automation

**Mitigation:**
- Systemd auto-restart (Phase 3)
- Heartbeat logging (every 5 min)
- Alert on heartbeat miss (>10 min)
- Fallback to manual mode

---

## Future Enhancements

### Intelligent Scheduling

- Learn optimal execution times (low system load)
- Batch similar tasks
- Defer non-urgent emails to off-peak

### Multi-Agent Coordination

- Task dependencies (A must complete before B)
- Parallel task graphs
- Resource sharing (shared databases, APIs)

### Learning from History

- Predict task duration
- Identify common failures
- Auto-retry transient errors only
- Skip known-bad patterns

### Advanced Notifications

- Slack/Discord integration
- SMS for critical failures
- Daily digest emails
- Executive dashboard

---

## Rollout Plan

### Week 1: Development

- [ ] Build `email_watcher.py` MVP
- [ ] Test with API branch
- [ ] Document usage
- [ ] Create test suite

### Week 2: Testing

- [ ] Add safety features (rate limit, modes)
- [ ] Extend to all 8 branches
- [ ] 7-day burn-in test
- [ ] Fix bugs, tune parameters

### Week 3: Deployment

- [ ] Production rollout
- [ ] Train team on usage
- [ ] Monitor metrics
- [ ] Gather feedback

### Week 4: Optimization

- [ ] Add intelligence features
- [ ] Systemd service
- [ ] Dashboard
- [ ] Documentation

---

## Documentation Needs

### User Guide

- How to write effective task emails
- When to use auto vs notify mode
- Troubleshooting failed executions
- Best practices for branch communication

### Developer Guide

- email_watcher.py architecture
- Adding new automation features
- Testing email triggers
- Debugging execution failures

### Operations Guide

- Starting/stopping service
- Monitoring logs
- Handling incidents
- Backup/recovery procedures

---

## Conclusion

The email-triggered automation system transforms AIPass from a multi-agent system into a **self-organizing agent mesh**. Branches collaborate autonomously, delegating work via email while maintaining human oversight through logs, approvals, and kill switches.

**Key Benefits:**
- 80%+ reduction in manual task execution
- 24/7 autonomous operation
- Scalable to hundreds of branches
- Full audit trail for compliance
- Human-in-loop for critical decisions

**Next Step:** Build Phase 1 MVP and validate with API branch.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-19
**Status:** Ready for Implementation
**Owner:** AIPASS
**Reviewers:** User, PRAX (watcher expert), AI_MAIL (email expert)
