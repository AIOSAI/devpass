# TRIGGER Branch-Local Context

**What happens here:**
- Event registration and dispatch (`trigger.fire`, `trigger.on`)
- Handlers respond when events fire (startup, plan_file_created, memory_saved, etc.)
- All branches fire events here - Trigger owns the reactions

**Key commands:**
```python
from trigger.apps.modules.core import trigger
trigger.fire('event_name', **data)  # Fire an event
trigger.on('event_name', handler)   # Register a handler
trigger.status()                    # Show registered handlers
```

**File locations:**
- `apps/modules/core.py` - Trigger class (event bus)
- `apps/handlers/events/` - All event handlers live here
- `apps/handlers/events/registry.py` - Handler registration on startup

**Adding new events:**
1. Create handler in `apps/handlers/events/new_event.py`
2. Register in `registry.py`: `trigger.on('new_event', handle_new_event)`

**Current events:** startup, memory_saved, cli_header_displayed, plan_file_created/deleted/moved
