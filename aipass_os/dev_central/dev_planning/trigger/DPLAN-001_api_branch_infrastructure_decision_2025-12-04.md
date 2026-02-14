# DPLAN-001: API Branch Infrastructure Decision

> ~~Should the API branch be treated as infrastructure (like prax/cli) or business logic (requiring trigger events)?~~

## RESOLVED

**The premise was wrong.** Imports are NOT triggers.

## The Confusion

I was scanning cross-branch imports and flagging them as "trigger violations". But:

- `from api... import get_response` → **Service call** (uses API, gets response back)
- `trigger.fire('startup')` → **Trigger event** (fire-and-forget, causes side effects)

These are fundamentally different patterns.

## Key Insight from Investigation

**Prax already uses trigger correctly:**
```python
# prax/apps/modules/logger.py - CURRENT
from trigger.apps.modules.core import trigger
trigger.fire('startup')  # ← Event-based, decoupled
```

The trigger handler then imports and calls Memory Bank. That's the correct pattern!

## Service vs Trigger

| Pattern | Example | What It Is |
|---------|---------|------------|
| **Service call** | `api.get_response(prompt)` → returns data | Using another branch's capability |
| **Trigger event** | `trigger.fire('plan_closed')` | Announcing something happened |

**Services** return data you use. **Triggers** cause side effects you don't wait for.

## Resolution

1. **Removed cross-branch import check from trigger_check.py** (v0.3.0)
2. **Flow's API imports are NOT violations** - they're service calls
3. **Trigger checker now only validates:**
   - Trigger handlers (no logger, no print, correct naming)
   - Files using trigger.fire() (correct import pattern)

## What IS a Trigger Violation?

If code does this (hypothetically):
```python
# BAD - directly triggering another branch's action
from memory_bank.apps.handlers.monitor import check_and_rollover
check_and_rollover()  # ← Hardcoded trigger
```

It should become:
```python
# GOOD - using event system
from trigger import trigger
trigger.fire('startup')  # ← Let trigger route it
```

But this is rare - Prax already migrated to the event pattern. Most cross-branch imports are service calls, not triggers.

## Status
- [ ] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [x] Complete
- [ ] Abandoned

## Notes
- 2025-12-04: Created during trigger standard implementation
- 2025-12-04: RESOLVED - imports ≠ triggers, removed cross-branch check
- trigger_check.py updated to v0.3.0

---
*Created: 2025-12-04*
*Updated: 2025-12-04*
