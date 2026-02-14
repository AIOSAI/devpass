# TRIGGER

**Purpose:** Central event system - owns ALL event handling across AIPass
**Location:** `/home/aipass/aipass_core/trigger`
**Profile:** Infrastructure Service (like Prax, CLI)
**Created:** 2025-11-30
**Status:** v1.3 - All migrations complete

---

## Architectural Role

**Trigger takes FULL CONTROL of event handling** - like Prax owns logging, Drone owns routing, AI_Mail owns messaging.

- Branches do NOT handle their own event logic
- Branches just fire events, Trigger handles what happens
- Like a subscription service: branches subscribe by calling `trigger.fire()`

See `docs/ARCHITECTURE.md` for full details.

---

## What Trigger Does

Trigger is the **event bus** for AIPass. Instead of branches having hardcoded trigger logic scattered throughout, they just announce events:

```python
from trigger import trigger

# Branch announces what happened (doesn't care what reacts)
trigger.fire('startup')
trigger.fire('memory_saved', branch='FLOW', lines=450)
```

Trigger owns all the reaction logic:
- Startup → run Memory Bank rollover check
- Memory saved → check line count → rollover if needed (future)

**The Prax Pattern:** Like how branches use `logger.info()` without knowing where logs go, branches use `trigger.fire()` without knowing what reacts.

---

## Quick Start

```python
from trigger import trigger

# Fire an event
trigger.fire('startup')

# Check registered handlers
trigger.status()  # {'startup': 1, 'memory_saved': 1}

# Register custom handler
trigger.on('my_event', lambda **kw: print(f"Got: {kw}"))
trigger.fire('my_event', data='hello')
```

---

## Architecture

```
trigger/
├── __init__.py              # Package export: from trigger import trigger
├── logs/                    # Event logs (core.log)
├── apps/
│   ├── trigger.py           # CLI entry point
│   ├── modules/
│   │   └── core.py          # Trigger class (fire, on, off, status)
│   └── handlers/
│       └── events/
│           ├── registry.py              # setup_handlers() - wires all handlers
│           ├── startup.py               # Memory Bank check
│           ├── memory.py                # memory_saved (placeholder)
│           ├── cli.py                   # cli_header_displayed
│           ├── plan_file.py             # plan_file_created/deleted/moved
│           ├── error_logged.py          # Sends AI_Mail on errors
│           ├── warning_logged.py        # Warning aggregation hook
│           ├── bulletin_created.py      # Propagates bulletins
│           └── memory_threshold_exceeded.py  # Compression notification
```

---

## API

| Method | Description |
|--------|-------------|
| `trigger.fire('event', **data)` | Fire event to all handlers |
| `trigger.on('event', handler)` | Register handler for event |
| `trigger.off('event', handler)` | Remove handler |
| `trigger.status()` | Show registered handlers count |

---

## Current Events

| Event | Handler | Description |
|-------|---------|-------------|
| `startup` | `handle_startup` | Runs Memory Bank rollover check |
| `memory_saved` | `handle_memory_saved` | Placeholder for future |
| `cli_header_displayed` | `handle_cli_header_displayed` | Fires when CLI displays header |
| `plan_created` | - | Fired by Flow when plan created |
| `plan_closed` | - | Fired by Flow when plan closed |
| `plan_file_created` | `handle_plan_file_created` | Updates Flow registry when PLAN file created |
| `plan_file_deleted` | `handle_plan_file_deleted` | Updates Flow registry when PLAN file deleted |
| `plan_file_moved` | `handle_plan_file_moved` | Updates Flow registry when PLAN file moved |
| `error_logged` | `handle_error_logged` | Sends AI_Mail notification on errors |
| `warning_logged` | `handle_warning_logged` | Hook for warning aggregation |
| `bulletin_created` | `handle_bulletin_created` | Propagates bulletins to all branches |
| `memory_threshold_exceeded` | `handle_memory_threshold_exceeded` | Sends compression notification |

---

## Event Logging

All events are logged to `logs/core.log` with caller identification:

```
[TRIGGER] prax fired: startup
[TRIGGER] 1 handlers responding
[TRIGGER] cli fired: cli_header_displayed
[TRIGGER] 1 handlers responding
```

---

## Integration

**Prax Logger Integration:**
Prax logger calls `trigger.fire('startup')` on first log call. This replaced 20 lines of hardcoded imports with a single event fire.

**Auto-initialization:**
Trigger auto-registers handlers on first `fire()` call. No setup required by callers.

---

## Memory Files

- **TRIGGER.id.json** - Branch identity
- **TRIGGER.local.json** - Session history
- **TRIGGER.observations.json** - Patterns learned

---

## Documentation

- `docs/ARCHITECTURE.md` - Architectural role and patterns
- `docs/INTEGRATION_GUIDE.md` - How branches integrate
- `docs/MIGRATION_TARGETS.md` - Code to migrate from other branches

---

## Migration Status

**Phase 1: Filesystem Events** ✅ COMPLETED
- Flow's registry_monitor fires events to Trigger
- Events: plan_file_created, plan_file_deleted, plan_file_moved

**Phase 2: Log Events** ✅ COMPLETED
- Centralized log watching in Trigger
- Events: error_logged, warning_logged

**Phase 3: System Events** ✅ COMPLETED
- Bulletin propagation and memory threshold monitoring
- Events: bulletin_created, memory_threshold_exceeded

**Phase 4: Evaluation** ✅ COMPLETED
- Prax monitor_module: Stays (event consumer)
- Drone activation.py: Stays (command routing)

**Total: 11 handlers registered. Migration scope finalized.**

---

*v1.3 Updated: 2026-02-02*
