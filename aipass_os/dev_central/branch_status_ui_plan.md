# Branch Status UI - Planning Document

*Created: 2026-01-30*
*Status: Research Complete - Ready for Build*

---

## Vision

A small popup/floating UI window showing active running branches. At a glance see which branches have Claude agents running vs idle.

```
+------------------+
| BRANCH STATUS    |
+------------------+
| DRONE      RUNNING |
| FLOW       IDLE    |
| SEED       IDLE    |
| ASSISTANT  RUNNING |
| PRAX       IDLE    |
+------------------+
```

---

## Research Summary (5 agents deployed)

### 1. Process Detection (Best Method)

**Working directory via `/proc/<PID>/cwd` is most reliable:**

```bash
# Get all Claude processes with their branch locations
pgrep -f claude | while read pid; do
    echo "PID: $pid, CWD: $(pwdx $pid | cut -d: -f2)"
done
```

**Why this works:**
- Auto-execute spawns with explicit `cwd=branch_path`
- Each branch has unique path (`/home/aipass/aipass_core/[branch]/`)
- Atomic, no race conditions
- Works without elevated permissions

**Process signature:**
- Binary: `/home/aipass/.local/bin/claude`
- Flag: `--permission-mode bypassPermissions`
- Environment: `CLAUDE_CODE_SSE_PORT=xxxxx`

### 2. Prax Already Has Monitoring Infrastructure

**Existing components we can use:**
- `MonitoringQueue` - Real-time event stream with branch attribution
- `BranchDetector` - Path-to-branch mapping
- `ModuleTracker` - Tracks module start/stop/history
- `prax monitor` - Live terminal-based Mission Control

**MonitoringEvent structure:**
```python
@dataclass
class MonitoringEvent:
    priority: int           # 1=error, 2=warning, 3=info
    timestamp: datetime
    event_type: str         # 'file', 'log', 'module', 'command'
    branch: str             # Which branch
    action: str             # 'created', 'modified', 'executed'
    message: str
    level: str              # 'info', 'warning', 'error'
```

### 3. Auto-Execute PID Tracking (Enhancement Opportunity)

**Current state:** delivery.py spawns agents but discards PID

```python
# Current (PID not captured)
subprocess.Popen(cmd, shell=True, cwd=str(branch_path))

# Could be enhanced to:
proc = subprocess.Popen(...)
pid = proc.pid  # Capture and store this
```

**Storage options:**
- Add to inbox.json: `agent_pid`, `agent_status`
- Central registry: `/home/aipass/aipass_core/ai_mail/ai_mail_json/agent_tracking.json`

### 4. UI Options

| Option | Type | Memory | Dependencies | Best For |
|--------|------|--------|--------------|----------|
| **Rich CLI** | Terminal live-update | ~20MB | rich (have it) | Primary status |
| **PySimpleGUI** | Floating window | ~30MB | PySimpleGUI | Desktop widget |
| **Flask Web** | Browser dashboard | ~50MB | flask | Web access |
| **notify-send** | Desktop alerts | ~1MB | built-in | Supplementary |

**Recommended:** Rich CLI for primary, notify-send for alerts

### 5. notify-send for Alerts

**Viable for:** Supplementary alerts (not primary monitoring)

```bash
# Replaceable notifications (no stacking)
ID=$(notify-send -p "AIPass" "Starting...")
notify-send -r "$ID" "AIPass" "Branch X now RUNNING"

# Urgency levels
notify-send -u critical "Alert" "Seed audit FAILED"  # Red
notify-send -u normal "Status" "Flow started"        # Standard
notify-send -u low "Info" "Routine check"            # Gray
```

---

## Existing Reference: terminal-status.disabled

VSCode extension at `/home/aipass/.vscode/extensions/terminal-status.disabled/`

**Pattern used:**
```typescript
onDidStartTerminalShellExecution → mark busy
onDidEndTerminalShellExecution → mark idle
```

**Why disabled:** Race condition on fast commands, VSCode-specific API

**Lesson:** Process-level detection is more reliable than API-based

---

## Recommended Architecture

```
                    ┌─────────────────────┐
                    │   Status Daemon     │
                    │  (polling process)  │
                    └─────────┬───────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         v                    v                    v
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Process Check  │  │   Prax Events   │  │  File mtime     │
│ pgrep + pwdx    │  │ MonitoringQueue │  │  .local.json    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              v
                    ┌─────────────────────┐
                    │    Status Store     │
                    │   branch_status.json│
                    └─────────┬───────────┘
                              │
         ┌────────────────────┼────────────────────┐
         v                    v                    v
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Rich CLI      │  │  notify-send    │  │ PySimpleGUI     │
│  (primary)      │  │  (alerts)       │  │ (optional)      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Implementation Plan

### Phase 1: Status Detection Core
**Owner:** @prax (has monitoring infrastructure)

1. Add process detection handler
   - `pgrep -f claude` + `pwdx` for PID→branch mapping
   - Poll every 2-3 seconds

2. Output to `branch_status.json`:
   ```json
   {
     "timestamp": "2026-01-30T00:30:00",
     "branches": {
       "drone": {"status": "RUNNING", "pid": 12345},
       "flow": {"status": "IDLE", "pid": null},
       "seed": {"status": "IDLE", "pid": null}
     }
   }
   ```

### Phase 2: CLI Display
**Owner:** @prax or @cli

1. `prax status` command showing live branch status
2. Uses Rich for formatting
3. Auto-refresh option

### Phase 3: Desktop Alerts (Optional)
**Owner:** @prax

1. notify-send integration for state changes
2. Replaceable notifications (no spam)
3. Urgency mapping (RUNNING=normal, STOPPED=low, ERROR=critical)

### Phase 4: Floating Window (Optional)
**Owner:** TBD

1. PySimpleGUI floating widget
2. Always-on-top option
3. Click to expand details

---

## Build Decision

**Recommended approach:** Start with Phase 1-2 (core + CLI), add Phase 3-4 later if needed.

**Who should build:** @prax - owns monitoring infrastructure, has BranchDetector, already does real-time event tracking.

**Alternative:** New dedicated branch `@status` if Prax scope creep is a concern.

---

## Next Steps

1. Send build task to @prax with Phase 1-2 spec
2. Or: Have @assistant coordinate with @prax for design review
3. Seed audit when complete

---

*Research completed Session 46, 2026-01-30*
