# AIPass Scheduled Tasks System - Design Document

**Date:** 2026-02-03
**Author:** @dev_central + Claude
**Status:** DRAFT - Design Proposal

---

## Executive Summary

This document proposes a scheduled task system for AIPass that aligns with existing architectural patterns (event-driven Trigger system, Prax monitoring, lazy-start philosophy, no-daemon preference). The design emphasizes **on-startup catch-up** over persistent schedulers, leveraging existing infrastructure.

---

## Current State Analysis

### Existing Patterns

| Component | Purpose | Pattern |
|-----------|---------|---------|
| **Trigger** | Event bus | Fire events, handlers respond |
| **Prax monitor** | Real-time watching | Persistent daemon (inotify) |
| **Error catch-up** | Missed errors | Scan-on-startup pattern |
| **Memory threshold** | Line count alerts | Event-driven notification |
| **Central writer** | Dashboard stats | Called on mail operations |
| **Log watcher** | Error detection | Lazy-start disabled (inotify exhaustion) |

### Key Constraint: inotify Exhaustion

The lazy-start log watcher pattern was **disabled** (see core.py v1.1.3) because each process starting its own watchers exhausted Linux's inotify instance limit (128 default). Architecture decision: **persistent processes own watching, not lazy-start**.

### Current Gaps

1. **No periodic health checks** - only reactive to events
2. **Memory rollover checks** - placeholder implementation exists but not scheduled
3. **Stale email cleanup** - manual process only
4. **Branch status reports** - no automated summary generation
5. **System metrics** - no periodic collection or aggregation

---

## Design Philosophy

### AIPass Principles Applied

1. **Code is truth** - Running checks beat theoretical schedules
2. **Lazy-start pattern** - Start when needed, not before
3. **Event-driven** - Trigger fires, handlers respond
4. **No daemons (preference)** - Catch-up on startup vs persistent schedulers
5. **Memory persists** - State survives across sessions

### Chosen Approach: Hybrid Model

```
                    +-----------------+
                    |   STARTUP       |
                    |   CATCH-UP      |
                    +-----------------+
                           |
                           v
    +----------------+     |     +------------------+
    |  CRON (hourly) |---->+---->|  TRIGGER EVENTS  |
    +----------------+     |     +------------------+
                           |            |
                           v            v
                    +-----------------+
                    |   PRAX MONITOR  |
                    |   (persistent)  |
                    +-----------------+
```

**Why Hybrid:**
- **Startup catch-up** handles missed events during downtime
- **Cron** provides guaranteed periodic execution without inotify issues
- **Trigger events** enable reactive processing
- **Prax monitor** remains single source for real-time watching

---

## Architecture

### New Component: `/home/aipass/aipass_core/trigger/apps/handlers/scheduled/`

```
trigger/apps/handlers/scheduled/
|-- __init__.py
|-- health_check.py      # Branch health verification
|-- memory_rollover.py   # Memory file line count checks
|-- mail_cleanup.py      # Stale email archival
|-- status_reporter.py   # Daily/hourly status generation
|-- metrics_collector.py # System metrics aggregation
```

### Cron Entry (User Crontab)

```bash
# AIPass scheduled tasks - hourly health sweep
0 * * * * /home/aipass/.venv/bin/python3 /home/aipass/aipass_core/trigger/apps/trigger.py scheduled run

# AIPass daily report - 8 AM
0 8 * * * /home/aipass/.venv/bin/python3 /home/aipass/aipass_core/trigger/apps/trigger.py scheduled daily-report
```

### New Module: `scheduled.py`

Location: `/home/aipass/aipass_core/trigger/apps/modules/scheduled.py`

```python
"""
Scheduled Tasks Module - Periodic system maintenance

Commands:
  run          - Execute hourly health checks
  daily-report - Generate daily status summary
  status       - Show scheduler status

Pattern: Thin orchestration layer for scheduled handlers
"""

def handle_command(command: str, args: List[str]) -> bool:
    if command not in ['run', 'daily-report', 'status']:
        return False

    if command == 'run':
        return run_hourly_checks()
    elif command == 'daily-report':
        return generate_daily_report()
    elif command == 'status':
        return show_status()
```

---

## Scheduled Tasks Detail

### 1. Hourly Health Checks (`run` command)

**Executes:**
- Memory file line count verification (all branches)
- Stale email detection (opened > 24h, new > 48h)
- Dashboard data freshness check
- Log rotation verification

**Output:**
- Fires `health_check_complete` event
- Sends summary to `@assistant` if issues found
- Updates `/home/aipass/aipass_os/AI_CENTRAL/HEALTH.central.json`

```python
# health_check.py

def check_all_branches() -> Dict[str, Any]:
    """
    Verify health across all registered branches.

    Returns:
        Dict with: healthy_count, warning_count, error_count, details[]
    """
    results = {
        'healthy': 0,
        'warnings': [],
        'errors': [],
        'timestamp': datetime.now().isoformat()
    }

    registry = load_branch_registry()
    for branch in registry['branches']:
        branch_health = check_branch_health(branch)
        if branch_health['status'] == 'healthy':
            results['healthy'] += 1
        elif branch_health['status'] == 'warning':
            results['warnings'].append(branch_health)
        else:
            results['errors'].append(branch_health)

    return results


def check_branch_health(branch: Dict) -> Dict[str, Any]:
    """
    Check individual branch health.

    Verifies:
    - Memory files exist and are under threshold
    - ai_mail.local directory exists
    - README.md exists and is recent (< 30 days modified)
    """
    path = Path(branch['path'])
    issues = []

    # Memory file checks
    for mem_file in ['local.json', 'observations.json']:
        mem_path = path / f"{branch['name'].upper()}.{mem_file}"
        if mem_path.exists():
            lines = count_lines(mem_path)
            if lines > 600:
                issues.append(f"{mem_file}: {lines} lines (threshold: 600)")
            elif lines > 500:
                issues.append(f"{mem_file}: {lines} lines (approaching threshold)")

    # Mail directory check
    if not (path / 'ai_mail.local').exists():
        issues.append("Missing ai_mail.local directory")

    return {
        'branch': branch['name'],
        'status': 'error' if len([i for i in issues if 'Missing' in i]) else
                  'warning' if issues else 'healthy',
        'issues': issues
    }
```

### 2. Memory Rollover Checks

**Trigger:** Hourly via cron, also on startup

**Action:**
- Scan all `*.local.json` and `*.observations.json` files
- Fire `memory_threshold_exceeded` event (existing handler sends email)
- Track processed files to avoid duplicate notifications

```python
# memory_rollover.py

MEMORY_THRESHOLD = 600
WARNING_THRESHOLD = 500
ROLLOVER_DATA_FILE = AIPASS_ROOT / "trigger" / "trigger_json" / "memory_rollover.json"


def check_memory_files() -> List[Dict]:
    """
    Scan all branches for memory files exceeding threshold.

    Returns:
        List of dicts with: branch, file_name, file_path, line_count, threshold
    """
    exceeds = []
    registry = load_branch_registry()

    for branch in registry['branches']:
        branch_path = Path(branch['path'])
        branch_name = branch['name'].upper()

        for pattern in ['*.local.json', '*.observations.json']:
            for mem_file in branch_path.glob(pattern):
                # Skip non-memory files (e.g., DASHBOARD.local.json)
                if 'DASHBOARD' in mem_file.name:
                    continue

                lines = count_lines(mem_file)
                if lines > MEMORY_THRESHOLD:
                    exceeds.append({
                        'branch': branch_name,
                        'file_name': mem_file.name,
                        'file_path': str(mem_file),
                        'line_count': lines,
                        'threshold': MEMORY_THRESHOLD
                    })

    return exceeds


def run_memory_check(fire_event: Callable) -> None:
    """
    Run memory check and fire events for exceeds.

    Args:
        fire_event: Trigger.fire callback
    """
    data = load_rollover_data()
    notified = set(data.get('notified_files', []))

    exceeds = check_memory_files()

    for item in exceeds:
        key = f"{item['branch']}:{item['file_name']}"
        if key not in notified:
            fire_event('memory_threshold_exceeded', **item)
            notified.add(key)

    # Prune old entries (files that no longer exceed)
    current_keys = {f"{i['branch']}:{i['file_name']}" for i in exceeds}
    notified = notified.intersection(current_keys)

    save_rollover_data({'notified_files': list(notified)})
```

### 3. Stale Email Cleanup

**Trigger:** Hourly via cron

**Rules:**
- Emails with status `new` > 48 hours: auto-open, notify branch
- Emails with status `opened` > 7 days: auto-close, archive

```python
# mail_cleanup.py

NEW_EMAIL_STALE_HOURS = 48
OPENED_EMAIL_STALE_DAYS = 7


def cleanup_stale_emails() -> Dict[str, int]:
    """
    Find and process stale emails across all branches.

    Returns:
        Dict with: auto_opened, auto_closed, errors
    """
    stats = {'auto_opened': 0, 'auto_closed': 0, 'errors': 0}
    registry = load_branch_registry()

    for branch in registry['branches']:
        inbox_path = Path(branch['path']) / 'ai_mail.local' / 'inbox.json'
        if not inbox_path.exists():
            continue

        try:
            inbox = load_inbox(inbox_path)
            messages = inbox.get('messages', [])
            modified = False

            for msg in messages:
                msg_time = datetime.fromisoformat(msg.get('timestamp', ''))
                age = datetime.now() - msg_time

                if msg.get('status') == 'new' and age > timedelta(hours=NEW_EMAIL_STALE_HOURS):
                    msg['status'] = 'opened'
                    msg['auto_opened'] = True
                    msg['auto_opened_at'] = datetime.now().isoformat()
                    stats['auto_opened'] += 1
                    modified = True

                    # Notify branch about stale email
                    send_stale_email_notification(branch['email'], msg)

                elif msg.get('status') == 'opened' and age > timedelta(days=OPENED_EMAIL_STALE_DAYS):
                    # Move to deleted (close without reply)
                    archive_email(inbox_path, msg['id'])
                    stats['auto_closed'] += 1
                    modified = True

            if modified:
                save_inbox(inbox_path, inbox)

        except Exception as e:
            stats['errors'] += 1

    return stats
```

### 4. Daily Status Reports

**Trigger:** Daily at 8 AM via cron

**Output:**
- Aggregated system health summary
- Branch activity metrics (emails sent/received)
- Memory status overview
- Active plans summary (from Flow)
- Sent to `@dev_central`

```python
# status_reporter.py

def generate_daily_report() -> str:
    """
    Generate daily system status report.

    Returns:
        Formatted markdown report string
    """
    report = []
    report.append(f"# AIPass Daily Report - {datetime.now().strftime('%Y-%m-%d')}")
    report.append("")

    # System Health
    health = check_all_branches()
    report.append("## System Health")
    report.append(f"- Healthy branches: {health['healthy']}")
    report.append(f"- Warnings: {len(health['warnings'])}")
    report.append(f"- Errors: {len(health['errors'])}")

    if health['warnings']:
        report.append("\n### Warnings")
        for w in health['warnings']:
            report.append(f"- {w['branch']}: {', '.join(w['issues'])}")

    if health['errors']:
        report.append("\n### Errors")
        for e in health['errors']:
            report.append(f"- {e['branch']}: {', '.join(e['issues'])}")

    # Mail Stats
    mail_stats = load_mail_central()
    report.append("\n## Mail Statistics")
    report.append(f"- Total unread: {mail_stats.get('system_totals', {}).get('total_unread', 0)}")
    report.append(f"- Total messages: {mail_stats.get('system_totals', {}).get('total_messages', 0)}")

    # Memory Status
    exceeds = check_memory_files()
    report.append("\n## Memory Status")
    if exceeds:
        report.append(f"- Files exceeding threshold: {len(exceeds)}")
        for e in exceeds:
            report.append(f"  - {e['branch']}/{e['file_name']}: {e['line_count']} lines")
    else:
        report.append("- All memory files within limits")

    # Active Plans (from Flow)
    plans = load_active_plans()
    report.append("\n## Active Plans")
    report.append(f"- Total active: {len(plans)}")
    for plan in plans[:5]:  # Top 5
        report.append(f"  - {plan.get('plan_id', 'unknown')}: {plan.get('title', 'untitled')}")

    return "\n".join(report)


def send_daily_report() -> bool:
    """Generate and send daily report to @dev_central."""
    report = generate_daily_report()

    from ai_mail.apps.modules.email import send_email_direct
    return send_email_direct(
        to_branch='@dev_central',
        subject=f"[DAILY] System Report - {datetime.now().strftime('%Y-%m-%d')}",
        message=report,
        from_branch='@trigger'
    )
```

### 5. System Metrics Collection

**Trigger:** Hourly via cron

**Collects:**
- Log file sizes
- Error counts by branch
- Memory file sizes
- Email queue depths

**Output:**
- `/home/aipass/aipass_os/AI_CENTRAL/METRICS.central.json`

```python
# metrics_collector.py

METRICS_FILE = AIPASS_HOME / "aipass_os" / "AI_CENTRAL" / "METRICS.central.json"


def collect_metrics() -> Dict[str, Any]:
    """
    Collect system-wide metrics.

    Returns:
        Dict with timestamp and metric categories
    """
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'logs': collect_log_metrics(),
        'memory': collect_memory_metrics(),
        'mail': collect_mail_metrics(),
        'branches': collect_branch_metrics()
    }

    # Save to central file
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)

    return metrics


def collect_log_metrics() -> Dict[str, Any]:
    """Collect log file statistics."""
    log_dir = AIPASS_HOME / "system_logs"
    if not log_dir.exists():
        return {}

    total_size = 0
    error_count = 0
    warning_count = 0

    for log_file in log_dir.glob("*.log"):
        total_size += log_file.stat().st_size
        # Count recent errors (last hour)
        # ... implementation

    return {
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / 1024 / 1024, 2),
        'file_count': len(list(log_dir.glob("*.log"))),
        'recent_errors': error_count,
        'recent_warnings': warning_count
    }
```

---

## Notification Routing

### Who Gets What

| Event | Recipient | Priority |
|-------|-----------|----------|
| Memory threshold exceeded | Affected branch | Normal |
| Health check errors | @assistant | High |
| Stale email detected | Affected branch | Low |
| Daily report | @dev_central | Normal |
| Critical errors (data loss risk) | @dev_central | Critical |

### Notification Format

```
From: @trigger
Subject: [SCHEDULED] Health Check - 2 Issues Found

## Health Check Summary
Time: 2026-02-03 14:00:00
Branches checked: 19

### Issues Found

**Warning: DRONE**
- DRONE.local.json: 523 lines (approaching threshold)

**Warning: FLOW**
- FLOW.observations.json: 612 lines (threshold: 600)

---
This is an automated health check. For details, run:
drone trigger scheduled status
```

---

## State Management

### State Files

```
/home/aipass/aipass_core/trigger/trigger_json/
|-- trigger_data.json      # Existing (error_catchup)
|-- scheduled_state.json   # NEW: Scheduler state
```

### scheduled_state.json Structure

```json
{
  "last_run": {
    "hourly": "2026-02-03T14:00:00",
    "daily_report": "2026-02-03T08:00:00"
  },
  "memory_rollover": {
    "notified_files": ["DRONE:DRONE.local.json", "FLOW:FLOW.observations.json"],
    "last_check": "2026-02-03T14:00:00"
  },
  "mail_cleanup": {
    "last_run": "2026-02-03T14:00:00",
    "stats": {
      "auto_opened_total": 5,
      "auto_closed_total": 12
    }
  },
  "health_check": {
    "last_run": "2026-02-03T14:00:00",
    "last_status": {
      "healthy": 17,
      "warnings": 2,
      "errors": 0
    }
  }
}
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
1. Create `scheduled/` handler directory structure
2. Implement `scheduled.py` module with `run` command
3. Create `health_check.py` handler
4. Create `scheduled_state.json` management

### Phase 2: Memory & Mail (Week 2)
1. Implement `memory_rollover.py` (builds on existing `memory_threshold_exceeded` event)
2. Implement `mail_cleanup.py`
3. Integration testing with existing handlers

### Phase 3: Reporting & Metrics (Week 3)
1. Implement `status_reporter.py`
2. Implement `metrics_collector.py`
3. Create central files in `AI_CENTRAL/`
4. Add cron entries

### Phase 4: Polish & Docs (Week 4)
1. Add `scheduled status` command output
2. Update README files
3. Add to CLAUDE.md instructions
4. Production testing

---

## Cron Setup

### Installation Script

```bash
#!/bin/bash
# install_scheduler.sh - Add AIPass scheduled tasks to user crontab

CRON_ENTRIES="
# AIPass Scheduled Tasks
# Hourly health checks (on the hour)
0 * * * * /home/aipass/.venv/bin/python3 /home/aipass/aipass_core/trigger/apps/trigger.py scheduled run >> /home/aipass/system_logs/scheduled.log 2>&1

# Daily report (8 AM)
0 8 * * * /home/aipass/.venv/bin/python3 /home/aipass/aipass_core/trigger/apps/trigger.py scheduled daily-report >> /home/aipass/system_logs/scheduled.log 2>&1
"

# Add to crontab (preserving existing entries)
(crontab -l 2>/dev/null; echo "$CRON_ENTRIES") | crontab -

echo "Cron entries installed. Verify with: crontab -l"
```

### Verification

```bash
# List cron entries
crontab -l

# Check cron log (Ubuntu)
grep CRON /var/log/syslog | tail -20

# Manual test
/home/aipass/.venv/bin/python3 /home/aipass/aipass_core/trigger/apps/trigger.py scheduled run
```

---

## Integration Points

### With Trigger System
- Reuses existing `Trigger.fire()` mechanism
- Handlers registered in `registry.py`
- Events: `health_check_complete`, `memory_threshold_exceeded` (existing), `mail_cleanup_complete`

### With AI_Mail
- Uses `send_email_direct()` for notifications
- Uses existing inbox loading/saving handlers
- Updates `AI_MAIL.central.json`

### With Prax
- Writes to `system_logs/scheduled.log`
- Does NOT start watchers (respects inotify constraint)
- Uses `system_logger` for logging

### With Flow
- Reads active plans for daily report
- Does NOT modify plans

---

## Alternatives Considered

### 1. Python APScheduler
**Rejected:** Requires persistent daemon process (conflicts with no-daemon preference)

### 2. systemd Timers
**Rejected:** More complex than cron, less portable

### 3. Lazy-start Scheduler
**Rejected:** Same inotify exhaustion issues as log watcher

### 4. Pure Event-driven (Startup Only)
**Partially Adopted:** Good for catch-up, but hourly checks need guaranteed execution

---

## Open Questions

1. **Cron user:** Should scheduled tasks run as `aipass` user? (Assumed yes)
2. **Log rotation:** Should `scheduled.log` be rotated? (Recommend logrotate)
3. **Failure alerting:** How to notify if scheduled tasks themselves fail? (Cron MAILTO?)
4. **Metrics retention:** How long to keep historical metrics? (Recommend 7 days)

---

## Appendix: File Locations Summary

| File | Purpose | Created By |
|------|---------|------------|
| `/home/aipass/aipass_core/trigger/apps/modules/scheduled.py` | Module entry point | This design |
| `/home/aipass/aipass_core/trigger/apps/handlers/scheduled/*.py` | Task handlers | This design |
| `/home/aipass/aipass_core/trigger/trigger_json/scheduled_state.json` | Scheduler state | scheduled.py |
| `/home/aipass/aipass_os/AI_CENTRAL/HEALTH.central.json` | Health status | health_check.py |
| `/home/aipass/aipass_os/AI_CENTRAL/METRICS.central.json` | System metrics | metrics_collector.py |
| `/home/aipass/system_logs/scheduled.log` | Execution log | Cron redirect |

---

*Document generated by @dev_central with Claude assistance. Ready for review and implementation.*
