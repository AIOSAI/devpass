# Trigger Architecture

**The Event System for AIPass**

---

## Core Principle

**Trigger owns ALL event handling across the AIPass system.**

Branches do NOT implement their own event logic. They announce what happened, Trigger handles what happens next.

---

## The Pattern (Comparison with Prax Logger)

| Concern | Prax Logger | Trigger |
|---------|-------------|---------|
| What branches call | `logger.info('message')` | `trigger.fire('event', **data)` |
| What branches know | Nothing about formatting, files, output | Nothing about handlers, reactions, side effects |
| Who owns the logic | Prax owns all logging logic | Trigger owns all event handling logic |
| How branches integrate | `from prax.apps.modules.logger import logger` | `from trigger import trigger` |

**If a branch is writing event handling code, it belongs in Trigger.**

---

## What Trigger Owns

1. **Event Registration** - All `trigger.on('event', handler)` calls
2. **Handler Execution** - Running handlers when events fire
3. **Event Logging** - Recording what events fire and who fired them
4. **Reaction Logic** - What happens when an event occurs
5. **Cross-Branch Coordination** - Events that affect multiple systems

---

## What Branches Provide

1. **Event Data** - The payload passed to `trigger.fire()`
2. **Event Timing** - When to fire (at the right moment in their workflow)
3. **Event Names** - Meaningful names that describe what happened

```python
# Branch code (e.g., Flow)
from trigger import trigger

# Branch fires event with data - doesn't care what happens
trigger.fire('plan_created', plan_id='0259', branch='flow', subject='New feature')
```

---

## What Trigger Provides to Branches

```python
from trigger import trigger

# Fire an event
trigger.fire('event_name', **data)

# Check what handlers are registered (debugging)
trigger.status()  # {'startup': 1, 'plan_created': 1, ...}

# Register custom handler (advanced - typically done in registry.py)
trigger.on('event', handler_function)
```

---

## Integration Pattern (Silent Fallback)

Branches use the Prax logger pattern for integration:

```python
# CORRECT - Silent fallback if Trigger unavailable
try:
    from trigger import trigger
    _trigger_available = True
except ImportError:
    _trigger_available = False

# Later in code...
if _trigger_available:
    trigger.fire('event_name', **data)
```

This ensures:
- Branches work even if Trigger is down/unavailable
- No crashes from circular imports during development
- Graceful degradation

---

## Current Events

| Event | Fired By | Handler | Purpose |
|-------|----------|---------|---------|
| `startup` | Prax logger (first log call) | Memory Bank rollover check | Run startup tasks |
| `memory_saved` | (Placeholder) | Line count check | Future: Auto-rollover |
| `cli_header_displayed` | CLI display | (Placeholder) | Future: UI events |
| `plan_created` | Flow | (Placeholder) | Notify of new plans |
| `plan_closed` | Flow | (Placeholder) | Notify of closed plans |

---

## Migration Targets

**Code that belongs in Trigger but currently lives elsewhere:**

### Flow's registry_monitor.py

**What it does:**
- Uses Python `watchdog` to monitor filesystem for PLAN file changes
- Auto-heals registry when files are created/moved/deleted
- Handles duplicate detection and auto-renumbering

**Why it belongs in Trigger:**
- It's event handling (filesystem events)
- Branches shouldn't implement their own event watchers
- Should fire events that handlers respond to, not handle events directly

**Migration path:**
1. Create `trigger.apps.handlers.events.filesystem.py`
2. Move PlanFileWatcher class to Trigger
3. Registry updates become handlers responding to file events
4. Flow just uses the registry - Trigger watches for changes

### Other Potential Migrations

Look for branches that:
- Use `watchdog` or similar file watchers
- Have event loops or polling
- React to external changes
- Coordinate multiple systems

---

## Adding New Events

1. **Define the event** - Choose a clear, meaningful name
2. **Create handler** - Add file to `trigger/apps/handlers/events/`
3. **Register handler** - Add to `registry.py` in `setup_handlers()`
4. **Fire from branch** - Use silent fallback pattern

Example handler template:

```python
#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# Name: my_event.py - My Event Handler
# Date: YYYY-MM-DD
# Version: 0.1.0
# =============================================

"""My Event Handler - Description of what this handles"""

def handle_my_event(**kwargs):
    """Handle my_event

    Args:
        **kwargs: Event data
    """
    # Handler logic here
    pass
```

---

## Architecture Diagram

```
Branch Code (Flow, Seed, etc.)
        │
        │ trigger.fire('event', **data)
        ▼
    ┌───────────────┐
    │    TRIGGER    │  ← Central event bus
    │   core.py     │
    └───────┬───────┘
            │
            │ dispatch to registered handlers
            ▼
    ┌───────────────────────────────────────────┐
    │         EVENT HANDLERS                     │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐     │
    │  │startup  │ │ memory  │ │filesystem│     │
    │  └────┬────┘ └────┬────┘ └────┬────┘     │
    │       │           │           │           │
    │       ▼           ▼           ▼           │
    │   Memory Bank   (future)   Registry       │
    │   rollover               updates          │
    └───────────────────────────────────────────┘
```

---

## Summary

- **Trigger is the subscription service** - branches subscribe by calling `trigger.fire()`
- **Handlers own the reactions** - what happens when events fire
- **Branches stay simple** - just fire events, don't handle them
- **Like Prax Logger** - branches use it without knowing implementation details

*Last updated: 2026-01-20*
