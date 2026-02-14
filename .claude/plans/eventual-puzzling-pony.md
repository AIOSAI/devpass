# Plan: Scheduler Single-Instance Lock

## Problem
Scheduler cascade: each dispatched task spawns an agent, which triggers startup, which runs schedule catch-up, which dispatches more tasks... exponential growth.

## Solution: Two-Layer Protection

### Layer 1: Spawned Agent Detection (Primary)
- Set `AIPASS_SPAWNED=1` environment variable when spawning agents via auto_execute
- Startup handler checks this and SKIPS schedule catch-up for spawned agents
- Zero filesystem overhead, no race conditions

### Layer 2: File Lock (Secondary)
- `filelock` library (already in venv) with non-blocking acquisition
- If another process is running run-due, skip gracefully
- Lock file: `assistant_json/schedule.lock`

### Layer 3: Sequential Processing
- Process tasks one at a time
- New status: `dispatching` (prevents re-dispatch during send)
- 1-second delay between dispatches (prevents thundering herd)
- Stale dispatch recovery (reset if stuck > 5 minutes)

## Files to Modify

### 1. `/home/aipass/aipass_core/ai_mail/apps/handlers/email/delivery.py`
Add environment variable to spawn command:
```python
# In _spawn_auto_execute_agent() ~line 341
env = os.environ.copy()
env['AIPASS_SPAWNED'] = '1'
process = subprocess.Popen(
    cmd,
    shell=True,
    env=env,  # Pass modified environment
    ...
)
```

### 2. `/home/aipass/aipass_core/trigger/apps/handlers/events/startup.py`
Re-enable schedule catch-up but gate it:
```python
# In handle_startup() ~line 258
import os
# Skip schedule catch-up for spawned agents (prevents cascade)
if os.environ.get('AIPASS_SPAWNED') != '1':
    _run_schedule_catchup()
```

### 3. `/home/aipass/aipass_os/dev_central/assistant/apps/modules/schedule.py`
Add filelock around run-due:
```python
from filelock import FileLock, Timeout

def _handle_run_due(_args):
    lock = FileLock(ASSISTANT_ROOT / "assistant_json" / "schedule.lock", timeout=0)
    try:
        with lock.acquire(timeout=0):
            return _process_due_tasks_sequential()
    except Timeout:
        console.print("[dim]Schedule already running, skipping.[/dim]")
        return True
```

### 4. `/home/aipass/aipass_os/dev_central/assistant/apps/handlers/schedule/task_registry.py`
Add dispatching status:
```python
def mark_dispatching(task_id: str) -> bool
def mark_pending(task_id: str) -> bool  # For recovery
def recover_stale_dispatches() -> int   # Reset if stuck > 5min
```

## Task Status Flow
```
pending → dispatching → completed
          ↓ (on error)
          pending (retry)
```

## Testing Plan

1. **Manual concurrent test**: Run `schedule run-due` in two terminals simultaneously
   - Second should say "already running, skipping"

2. **Spawn test**: Create test task, run-due, verify ONLY one agent spawns
   - Watch with: `ps aux | grep "claude -p"`

3. **Recovery test**: Kill process mid-dispatch, verify task resets after 5min

## Verification Commands
```bash
# Create test task
drone @assistant schedule create "@dev_central" "Test single instance" "Confirm receipt" "0d"

# Run and watch for cascade
drone @assistant schedule run-due

# Monitor for agent spawns
watch -n1 'ps aux | grep "claude -p" | grep -v grep | wc -l'
```

## Sources
- [filelock PyPI](https://pypi.org/project/filelock/) - Standard Python file locking
- [Real Python Thread Safety](https://realpython.com/python-thread-lock/) - Lock patterns
