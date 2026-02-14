# FLOW Handler Config Extraction Plan

**Created**: 2025-11-26
**Status**: Future Work
**Priority**: Medium
**Scope**: Flow handlers (6 directories, ~80 hardcoded values)

---

## Overview

Audit completed 2025-11-26 identified ~80+ hardcoded values across Flow's handler directories that should be moved to JSON config files for maintainability and consistency.

---

## Audit Findings Summary

### By Handler Directory

| Directory | Values Found | Priority |
|-----------|--------------|----------|
| summary/ | 25 | HIGH - API settings, word limits |
| plan/ | 20+ | MEDIUM - status strings, format |
| dashboard/ | 7 | HIGH - hardcoded paths! |
| mbank/ | 15+ | MEDIUM - TRL mappings, thresholds |
| json/ | 15+ | LOW - patterns, defaults |
| bulletin/ | 20+ | LOW - status strings |

### Critical Issues (Fix First)

1. **Hardcoded Paths** (dashboard/push_central.py)
   - Lines 95, 225: `"/home/aipass/aipass_core/flow"` as string literal
   - Should use `FLOW_ROOT` constant
   - Risk: Breaks if paths change

2. **Duplicated Template Markers**
   - `4` template indicator threshold in BOTH:
     - `summary/generate.py:308`
     - `mbank/process.py:243`
   - Same 6 marker strings duplicated
   - Risk: Drift between files

3. **Recently Closed Limit**
   - Value `5` appears in 4 places across 3 files
   - Should be single config value

### Magic Numbers to Extract

| Value | Count | Purpose | Target Config |
|-------|-------|---------|---------------|
| `5` | 4x | Recently closed limit | flow_dashboard_config.json |
| `4` | 3x | Plan number digits | flow_plan_config.json |
| `100` | 2x | Max log entries | flow_json_config.json |
| `50` | 3x | Cache/truncate limits | flow_plan_summarizer_config.json |
| `500` | 3x | Char/token limits | flow_plan_summarizer_config.json |
| `120` | 1x | API timeout | api_config.json (already done) |

### Status Strings to Centralize

```python
# Should be in a constants file or config
PLAN_STATUS_OPEN = "open"
PLAN_STATUS_CLOSED = "closed"
CLOSE_REASON_AUTO = "auto_closed_missing_file"
BULLETIN_STATUS_ACTIVE = "active"
BULLETIN_STATUS_COMPLETED = "completed"
```

---

## Proposed Approach

### Phase 1: Critical Fixes (1-2 hours)
- [ ] Fix hardcoded paths in push_central.py
- [ ] Centralize template markers (single source of truth)
- [ ] Extract `recently_closed_limit` to config

### Phase 2: Summary Handler (~2 hours)
- [ ] Move remaining hardcoded values to flow_plan_summarizer_config.json
- [ ] Already partially done (word limits, content max)
- [ ] Add: cache entries, extraction limits

### Phase 3: Plan Handler (~2 hours)
- [ ] Create flow_plan_config.json if needed
- [ ] Extract: plan number format, status strings
- [ ] Consolidate auto-close reason string

### Phase 4: Dashboard/Central (~1 hour)
- [ ] Create flow_dashboard_config.json
- [ ] Extract: recently_closed_limit, path constants

### Phase 5: Lower Priority (~2 hours)
- [ ] mbank TRL mappings (consider: registry vs config)
- [ ] json handler defaults
- [ ] bulletin status strings

---

## Config File Structure Proposal

```
flow/
  flow_json/
    flow_plan_summarizer_config.json  (exists - expand)
    flow_plan_config.json             (new)
    flow_dashboard_config.json        (new)
    flow_constants.json               (new - shared strings)
  apps/handlers/
    json_templates/
      custom/
        api_config.json               (exists)
```

---

## Notes

- Some values are intentional hardcoding (UTF-8 encoding, CLI flags)
- Status strings could be enum/constants vs config (design decision)
- TRL mappings in mbank might be better as registry data than config
- Test each extraction - don't break working code

---

## Session Reference

- Audit performed: Session 10 (2025-11-26)
- 5 parallel agents used for speed
- User decision: Document for future, not immediate fix
