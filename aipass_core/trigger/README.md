# TRIGGER

**Purpose:** Central event system - owns ALL event handling across AIPass
**Location:** `/home/aipass/aipass_core/trigger`
**Profile:** Infrastructure Service (like Prax, CLI)
**Created:** 2025-11-30
**Status:** v2.1 - Medic v2 complete, 116 tests

---

## Architectural Role

**Trigger takes FULL CONTROL of event handling** - like Prax owns logging, Drone owns routing, AI_Mail owns messaging.

- Branches do NOT handle their own event logic
- Branches just fire events, Trigger handles what happens
- The Prax Pattern: branches use `trigger.fire()` without knowing what reacts, like `logger.info()` without knowing where logs go

See `docs/ARCHITECTURE.md` for full details.

---

## What Trigger Does

Trigger is the **event bus** for AIPass. Branches announce events, Trigger owns all reactions:

```python
from trigger import trigger

# Branch announces what happened (doesn't care what reacts)
trigger.fire('startup')
trigger.fire('memory_saved', branch='FLOW', lines=450)
```

**Medic** is Trigger's auto-healing system. It watches branch logs for errors, deduplicates them via SHA1 fingerprinting, and dispatches fix-it emails to the affected branch - with circuit breakers and rate limiting to prevent spam.

---

## Quick Start

```python
from trigger import trigger

# Fire an event
trigger.fire('startup')

# Check registered handlers
trigger.status()  # {'startup': 1, 'error_detected': 1, ...}

# Register custom handler
trigger.on('my_event', lambda **kw: print(f"Got: {kw}"))
trigger.fire('my_event', data='hello')
```

**Cross-branch error reporting:**
```python
from trigger.apps.modules.errors import report_error

result = report_error(
    error_type='ImportError',
    message='Module not found: foo',
    component='DRONE',
    log_path='/home/aipass/aipass_core/drone/logs/drone.log'
)
# Returns: {is_new, dispatched, fingerprint, id, count, status}
```

---

## Commands

```bash
# Medic (auto-healing toggle)
drone @trigger medic on             # Enable error dispatch
drone @trigger medic off            # Disable globally
drone @trigger medic status         # Show state + stats
drone @trigger medic mute @branch   # Suppress dispatch for one branch
drone @trigger medic unmute @branch # Resume dispatch for branch

# Error registry
drone @trigger errors list          # Query errors by status/component
drone @trigger errors detail <fp>   # Full error info by fingerprint
drone @trigger errors suppress <fp> # Mark error as suppressed
drone @trigger errors resolve <fp>  # Mark error as resolved
drone @trigger errors clear-resolved # Delete old resolved entries
drone @trigger errors stats         # Summary statistics
drone @trigger errors circuit-breaker # Check global dispatch gate

# Log watchers
drone @trigger branch_log_events start   # Start branch log watcher
drone @trigger branch_log_events stop    # Stop watcher
drone @trigger branch_log_events status  # Show watcher status
drone @trigger branch_log_events reset   # Clear dedup hashes

drone @trigger log_events start    # Start system log watcher
drone @trigger log_events stop     # Stop system log watcher
drone @trigger log_events status   # Show status
```

---

## Architecture

```
trigger/
├── __init__.py                     # Package export: from trigger import trigger
├── apps/
│   ├── trigger.py                  # CLI entry point (auto-discovery routing)
│   ├── modules/
│   │   ├── core.py                 # Trigger class (fire, on, off, status)
│   │   ├── errors.py               # Error registry management + report_error() API
│   │   ├── medic.py                # Medic toggle (on/off/mute/unmute)
│   │   ├── branch_log_events.py    # Branch log watcher control
│   │   └── log_events.py           # System log watcher control
│   └── handlers/
│       ├── error_registry.py       # Error persistence, fingerprinting, circuit breaker
│       ├── log_watcher.py          # Branch log watcher (watchdog-based)
│       ├── medic_state.py          # Medic state persistence
│       ├── watchers/
│       │   └── log_watcher.py      # System log watcher (watchdog-based)
│       └── events/
│           ├── registry.py         # setup_handlers() - wires all handlers
│           ├── startup.py          # Startup checks + error catch-up
│           ├── error_detected.py   # Dispatch fix-it emails (Medic v2)
│           ├── error_logged.py     # Legacy error notification (deprecated)
│           ├── warning_logged.py   # Warning aggregation hook
│           ├── plan_file.py        # PLAN file create/delete/move
│           ├── bulletin_created.py # Propagate bulletins to branches
│           ├── memory_threshold_exceeded.py # Compression notification
│           ├── memory.py           # memory_saved (placeholder)
│           └── cli.py              # cli_header_displayed (placeholder)
├── tests/
│   └── test_error_registry.py      # 116 tests (registry, circuit breaker, pipeline)
├── tools/
│   └── run_branch_log_watcher.py   # Persistent background watcher runner
├── trigger_json/                   # Runtime state
│   ├── error_registry.json         # Error fingerprints and metadata
│   ├── trigger_config.json         # Medic enabled/muted state
│   └── trigger_data.json           # Dedup hashes + catch-up data
├── logs/                           # core.log, medic.log, medic_suppressed.log
└── docs/
    ├── ARCHITECTURE.md             # Event system design patterns
    ├── INTEGRATION_GUIDE.md        # How branches integrate
    └── MIGRATION_TARGETS.md        # Migration status (all phases complete)
```

---

## Event Bus API

| Method | Description |
|--------|-------------|
| `trigger.fire('event', **data)` | Fire event to all registered handlers |
| `trigger.on('event', handler)` | Register handler for event |
| `trigger.off('event', handler)` | Remove handler |
| `trigger.status()` | Show registered handler counts |

Auto-initializes on first `fire()` call. Handles nested event firing via deferred queue.

---

## Current Events

| Event | Handler | Description |
|-------|---------|-------------|
| `startup` | `handle_startup` | Startup checks + error catch-up from last 24h |
| `error_detected` | `handle_error_detected` | Medic v2: dispatch fix-it emails with circuit breaker |
| `error_logged` | `handle_error_logged` | Legacy notification (deprecated by error_detected) |
| `warning_logged` | `handle_warning_logged` | Hook for future warning aggregation |
| `plan_file_created` | `handle_plan_file_created` | Updates Flow registry on PLAN creation |
| `plan_file_deleted` | `handle_plan_file_deleted` | Updates Flow registry on PLAN deletion |
| `plan_file_moved` | `handle_plan_file_moved` | Updates Flow registry on PLAN move |
| `bulletin_created` | `handle_bulletin_created` | Propagates bulletins to all branch dashboards |
| `memory_threshold_exceeded` | `handle_memory_threshold_exceeded` | Sends compression notification |
| `memory_saved` | `handle_memory_saved` | Placeholder for future rollover check |
| `cli_header_displayed` | `handle_cli_header_displayed` | Placeholder for UI events |

**11 handlers registered.**

---

## Medic System (Auto-Healing)

Medic watches branch logs for errors and dispatches fix-it emails to the affected branch.

**Pipeline:** Log error detected → SHA1 fingerprint → registry dedup → dispatch threshold (count >= 2) → circuit breaker check → rate limit check → Medic enabled check → branch mute check → dispatch email

**Key features:**
- **Error Registry** - SHA1 fingerprinting deduplicates errors. Same error 1000x = 1 entry with count=1000
- **Dispatch Threshold** - First occurrence is registered silently. Second occurrence triggers dispatch (confirms pattern, not fluke)
- **Circuit Breaker** - Global dispatch gate. Pauses all dispatch when error rate exceeds threshold. Three states: closed (normal), open (paused), half_open (testing)
- **Rate Limiting** - Per-fingerprint exponential backoff prevents spam for recurring errors
- **Medic Toggle** - Global on/off kill switch (`medic on/off`)
- **Branch Muting** - Suppress dispatch for specific branches (`medic mute @branch`)
- **Source Fix Pipeline** - Suppressed errors auto-email the source branch with log-level fix recommendations

**Cross-branch push API:**
```python
from trigger.apps.modules.errors import report_error

report_error(
    error_type='ValueError',
    message='Invalid input',
    component='API',
    log_path='/path/to/log',
    severity='error',
    fire_event=True  # Set False for silent registration
)
```

---

## Integration

**Prax Logger Integration:**
Prax logger calls `trigger.fire('startup')` on first log call - replaced 20 lines of hardcoded imports with a single event fire.

**Auto-initialization:**
Trigger auto-registers handlers on first `fire()` call. No setup required by callers.

**Silent Handler Pattern:**
Event handlers cannot import Prax logger (prevents circular deps). Handlers fail silently - event logging is handled by core.py.

---

## Testing

116 tests covering:
- Error registry (fingerprinting, report, query, status transitions)
- Circuit breaker (state machine, exponential cooldown)
- Rate limiting (per-fingerprint backoff)
- Cross-branch push API (report_error edge cases)
- Dispatch threshold (count-based gating)
- Full pipeline integration

```bash
cd /home/aipass/aipass_core/trigger && python3 -m pytest tests/ -v
```

---

## Memory Files

- **TRIGGER.id.json** - Branch identity
- **TRIGGER.local.json** - Session history
- **TRIGGER.observations.json** - Patterns learned

---

## Documentation

- `docs/ARCHITECTURE.md` - Architectural role and patterns
- `docs/INTEGRATION_GUIDE.md` - How branches integrate
- `docs/MIGRATION_TARGETS.md` - Migration status (all phases complete)

---

*v2.1 Updated: 2026-02-14*
