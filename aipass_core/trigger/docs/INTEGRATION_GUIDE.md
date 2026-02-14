# Trigger Integration Guide

**How branches integrate with the Trigger event system**

---

## Quick Start

```python
# 1. Import with silent fallback
try:
    from trigger import trigger
    _trigger_available = True
except ImportError:
    _trigger_available = False

# 2. Fire events at appropriate moments
if _trigger_available:
    trigger.fire('my_event', key='value', other_data=123)
```

That's it. Branches just fire events - they don't handle them.

---

## The Rule

**If you're writing code that reacts to events, it belongs in Trigger.**

| Wrong (in branch) | Right (in Trigger) |
|-------------------|-------------------|
| Branch watches files with watchdog | Trigger watches, fires events, branch responds |
| Branch polls for changes | Trigger monitors, fires events |
| Branch coordinates multiple systems | Trigger handler coordinates |
| Branch has event loop | Trigger owns event loops |

---

## Integration Pattern (Same as Prax Logger)

```python
# At module top - import with fallback
try:
    from trigger import trigger
    _trigger_available = True
except ImportError:
    _trigger_available = False

# In your function - fire when appropriate
def create_plan(subject: str, **kwargs):
    # ... do the work ...

    # Fire event at the end
    if _trigger_available:
        trigger.fire('plan_created',
                    plan_id=plan_id,
                    subject=subject,
                    branch=branch_name)

    return result
```

---

## When to Fire Events

Fire events when:
- Something was created (plan_created, memory_saved)
- Something was completed (plan_closed, task_finished)
- State changed (status_updated, error_occurred)
- External action happened (file_changed, user_input)

---

## Event Naming Convention

```
{noun}_{past_tense_verb}
```

Examples:
- `plan_created` (not create_plan)
- `memory_saved` (not save_memory)
- `startup` (exception - system-level event)
- `cli_header_displayed`

---

## What Data to Include

Include everything a handler might need:

```python
trigger.fire('plan_created',
    plan_id='0259',           # Identifier
    subject='New feature',     # Human-readable
    branch='flow',            # Source branch
    file_path='/path/to/plan' # Location
)
```

Don't include:
- Sensitive data (passwords, tokens)
- Huge objects (pass paths, not contents)
- Circular references

---

## Debugging

Check what handlers are registered:

```python
from trigger import trigger
print(trigger.status())
# {'startup': 1, 'plan_created': 1, 'plan_closed': 1}
```

Events are logged to `trigger/logs/core.log`:

```
[TRIGGER] flow fired: plan_created
[TRIGGER] 1 handlers responding
```

---

## Adding New Events

If you need a new event:

1. **Use it** - Just call `trigger.fire('new_event', **data)`
2. **Request handler** - Email @trigger or @dev_central
3. **Handler gets created** - In `trigger/apps/handlers/events/`
4. **Handler gets registered** - In `registry.py`

You can fire events before handlers exist - they'll just have 0 handlers responding.

---

## Don'ts

```python
# DON'T implement your own file watcher
from watchdog.observers import Observer  # This belongs in Trigger

# DON'T handle events in branch code
def on_plan_created(event):  # This belongs in Trigger handlers
    update_dashboard()
    notify_users()

# DON'T coordinate multiple systems
def close_plan():
    update_registry()
    update_dashboard()    # These should be handlers responding
    send_notification()   # to trigger.fire('plan_closed')
```

---

## Do's

```python
# DO fire events and let Trigger handle reactions
trigger.fire('plan_closed', plan_id='0259', reason='completed')

# DO use silent fallback
if _trigger_available:
    trigger.fire('event')

# DO include useful data
trigger.fire('error_occurred',
    module='create_plan',
    error_type='ValidationError',
    message='Invalid plan ID')
```

---

## Reference: Prax Logger Pattern

The integration pattern is identical to Prax logger:

| Prax Logger | Trigger |
|-------------|---------|
| `logger.info('msg')` | `trigger.fire('event', **data)` |
| Branch doesn't know where logs go | Branch doesn't know what reacts |
| Prax owns all logging logic | Trigger owns all event logic |
| Silent if Prax unavailable | Silent if Trigger unavailable |

---

*Last updated: 2026-01-20*
