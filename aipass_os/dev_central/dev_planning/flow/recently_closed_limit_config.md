# Plan: Recently Closed Plans Limit - Move to Config

*Created: 2025-11-26*
*Status: Planned*
*Priority: Low*

---

## Problem

`recently_closed` limit is hardcoded as `5` in 6+ places:

| File | Line | Code |
|------|------|------|
| `write_plan_outputs.py` | 207 | `closed_entries[-5:]` |
| `write_plan_outputs.py` | 211 | `min(len(closed_entries), 5)` |
| `aggregate_central.py` | 415 | `all_closed[:5]` |
| `push_central.py` | 121 | `closed[:5]` |
| `update_local.py` | 229 | `closed[-5:]` |

---

## Solution

Add to `flow_json/flow_dashboard_config.json`:

```json
{
  "module_name": "flow_dashboard",
  "version": "1.0.0",
  "config": {
    "recently_closed_limit": 5,
    "display_settings": {
      "show_closed_reason": false,
      "show_timestamps": true
    }
  }
}
```

Then update all handlers to read from config instead of hardcoded `5`.

---

## Files to Modify

1. Create `flow_json/flow_dashboard_config.json`
2. Update `write_plan_outputs.py` - read limit from config
3. Update `aggregate_central.py` - read limit from config
4. Update `push_central.py` - read limit from config
5. Update `update_local.py` - read limit from config

---

## Notes

- Part of larger "move hardcoded values to config" effort
- See: `FLOW-handler-config-extraction-2025-11-26.md` for full audit
- Default should remain 5 (current behavior)

---

*Future implementation - not urgent*
