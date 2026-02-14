# Plan: Rename aggregate_central.py → plan_central_sync.py

*Created: 2025-11-26*
*Status: Planned*
*Priority: Low (cosmetic, but improves clarity)*

---

## Problem

`aggregate_central.py` is a terrible name - doesn't tell you what it does.

## Solution

Rename to: **`plan_central_sync.py`**

This clearly describes the action: syncing plans to central.

---

## Files to Update

1. **Rename file:**
   - `apps/modules/aggregate_central.py` → `apps/modules/plan_central_sync.py`

2. **Update imports in:**
   - `apps/flow.py` (if importing)
   - `apps/modules/close_plan.py` (if importing)
   - Any other modules that reference it

3. **Update MODULE_NAME constant inside the file:**
   ```python
   MODULE_NAME = "plan_central_sync"
   ```

4. **Update drone command routing (if applicable)**

5. **Update any documentation references**

---

## Command After Rename

```bash
# Current (bad)
python3 apps/modules/aggregate_central.py aggregate

# After (clear)
python3 apps/modules/plan_central_sync.py sync
```

Or via drone:
```bash
drone @flow sync-central
```

---

## Notes

- Part of naming cleanup effort
- Low risk - internal module, not user-facing API
- Do find/replace across codebase for any string references

---

*Future implementation - simple rename task*
