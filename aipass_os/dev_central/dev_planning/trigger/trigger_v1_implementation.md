# Trigger v1 Implementation Plan

**Created:** 2025-11-30
**Status:** Planning
**Owner:** DEV_CENTRAL
**Target Branch:** `/home/aipass/aipass_core/trigger`
**Reference:** `planning/system/unified_trigger_system.md`

---

## Goal

Build a simple event-based trigger system that branches can import. Branches fire events, trigger module handles reactions. Like Prax logger but for events.

---

## Decision: Option D (Event-Based)

From research, we're going with:
- **Pattern:** Event-based (fire/on/off)
- **Start:** Custom ~50 lines (not Blinker yet)
- **API:** `trigger.fire('event', **data)`

---

## What We're Building

### Core API

```python
from aipass_core.trigger import trigger

# Branches fire events (announce what happened)
trigger.fire('memory_saved', branch='FLOW', lines=450)
trigger.fire('plan_closed', plan_id='PLAN0123')
trigger.fire('startup')

# Handlers registered in trigger module
trigger.on('memory_saved', handle_memory_check)
trigger.on('startup', run_startup_hooks)
```

### File Structure

```
/home/aipass/aipass_core/trigger/
├── apps/
│   ├── trigger.py              # Entry point (CLI)
│   ├── modules/
│   │   └── core.py             # Trigger class (fire, on, off)
│   └── handlers/
│       └── events/
│           ├── __init__.py
│           ├── startup.py      # Startup event handlers
│           ├── memory.py       # Memory event handlers
│           └── registry.py     # Setup all handlers
```

---

## Implementation Steps

### Phase 1: Core Trigger Class

**File:** `apps/modules/core.py`

```python
class Trigger:
    _handlers = {}
    _history = []  # Optional: track recent events

    @classmethod
    def on(cls, event: str, handler: callable):
        """Register handler for event"""
        cls._handlers.setdefault(event, []).append(handler)

    @classmethod
    def off(cls, event: str, handler: callable):
        """Remove handler"""
        if event in cls._handlers and handler in cls._handlers[event]:
            cls._handlers[event].remove(handler)

    @classmethod
    def fire(cls, event: str, **data):
        """Fire event to all registered handlers"""
        for handler in cls._handlers.get(event, []):
            try:
                handler(**data)
            except Exception as e:
                # Log error but don't crash
                print(f"[trigger] Handler error for {event}: {e}")

    @classmethod
    def status(cls) -> dict:
        """Show registered handlers"""
        return {event: len(handlers) for event, handlers in cls._handlers.items()}

trigger = Trigger()
```

**Tasks:**
- [ ] Create `apps/modules/core.py` with Trigger class
- [ ] Export from `apps/modules/__init__.py`
- [ ] Test: `trigger.on('test', lambda: print('fired'))` then `trigger.fire('test')`

---

### Phase 2: Handler Registry

**File:** `apps/handlers/events/registry.py`

```python
from ..modules.core import trigger

def setup_handlers():
    """Register all event handlers on startup"""
    from .startup import handle_startup
    from .memory import handle_memory_saved

    trigger.on('startup', handle_startup)
    trigger.on('memory_saved', handle_memory_saved)
```

**File:** `apps/handlers/events/startup.py`

```python
def handle_startup(**kwargs):
    """Run startup checks - replaces Prax logger's hardcoded calls"""
    # Memory Bank check
    try:
        from MEMORY_BANK.apps.handlers.monitor.memory_watcher import check_and_rollover
        check_and_rollover()
    except ImportError:
        pass

    # Bulletin propagation
    try:
        from apps.handlers.bulletin.propagation import check_and_propagate
        check_and_propagate()
    except ImportError:
        pass
```

**Tasks:**
- [ ] Create `apps/handlers/events/` directory
- [ ] Create `registry.py` with setup_handlers()
- [ ] Create `startup.py` with handle_startup()
- [ ] Create `memory.py` placeholder

---

### Phase 3: Wire Into Prax Logger

**File to modify:** `/home/aipass/aipass_core/prax/apps/modules/logger.py`

Replace lines 99-117 (hardcoded imports) with:

```python
def _ensure_watcher(self):
    """Lazy-start triggers on first logger use"""
    if not SystemLogger._watcher_started:
        # Start prax watcher
        if not is_file_watcher_active():
            start_file_watcher()

        # Fire startup event (trigger handles the rest)
        try:
            from trigger.apps.modules.core import trigger
            trigger.fire('startup')
        except ImportError:
            # Fallback if trigger not available
            pass

        SystemLogger._watcher_started = True
```

**Tasks:**
- [ ] Update Prax logger to use trigger.fire('startup')
- [ ] Test: Any branch logging → triggers startup hooks
- [ ] Verify Memory Bank rollover still works

---

### Phase 4: Export for Branch Import

**File:** `/home/aipass/aipass_core/trigger/__init__.py`

```python
from .apps.modules.core import trigger

__all__ = ['trigger']
```

Now branches can do:
```python
from trigger import trigger
trigger.fire('my_event', data='value')
```

**Tasks:**
- [ ] Create package-level `__init__.py`
- [ ] Verify import works from other branches
- [ ] Add to BRANCH_REGISTRY.json if not already

---

## Testing Plan

1. **Unit test core:**
   ```python
   trigger.on('test', lambda **kw: print('fired'))
   trigger.fire('test')  # Should print 'fired'
   ```

2. **Integration test startup:**
   ```python
   # From any branch
   from prax.apps.modules.logger import system_logger as logger
   logger.info("test")  # Should trigger startup hooks via trigger.fire('startup')
   ```

3. **Verify backwards compatibility:**
   - Memory Bank rollover still works
   - Bulletin propagation still works
   - No broken imports

---

## Success Criteria

- [ ] `trigger.fire()`, `trigger.on()`, `trigger.off()` work
- [ ] Prax logger uses trigger instead of hardcoded imports
- [ ] Memory Bank rollover triggers correctly
- [ ] Other branches can import and use trigger
- [ ] No performance regression

---

## Future (Not This Plan)

- Upgrade to Blinker if needed
- Add more events (plan_created, plan_closed, error_logged)
- Move more trigger logic from branches to trigger handlers
- Event history/replay
- Async support

---

## Dependencies

- Prax logger (will be modified)
- Memory Bank (startup check moves to trigger handler)
- Bulletin system (propagation moves to trigger handler)

---

## Notes

- Keep it simple - ~50 lines of core code
- Don't over-engineer
- Branches should just fire events, not know about handlers
- All handler logic centralizes in trigger module

---

*Plan created: 2025-11-30*
*Ready for implementation*
