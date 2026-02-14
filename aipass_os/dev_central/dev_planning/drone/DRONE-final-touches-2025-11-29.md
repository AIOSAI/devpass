# Drone Final Touches - Planning Document

**Date:** 2025-11-29
**Session:** 24
**Status:** Planning
**Source:** 20-Agent Fresh Eyes Exploration

---

## Overview

Drone has reached near-completion. This document captures findings from deploying 20 agents with zero context to explore the branch and identify remaining issues. These represent the "final touches" before Drone can be considered complete.

**Current Compliance:** 100% (with bypasses)

---

## Critical Bug

### 1. Activated Commands Don't Resolve @ Arguments

**Priority:** CRITICAL
**File:** `apps/handlers/discovery/activated_commands.py`

**Problem:**
```python
# Line 62 - imports preprocess_args
from drone.apps.handlers.routing import preprocess_args

# Line 198 - NEVER CALLS IT!
run_branch_module(module_path, module_args)  # @ args passed literally!
```

**Impact:**
- `drone plan create @seed "task"` passes `@seed` literally to Flow
- Flow receives the string "@seed" instead of the resolved path
- Only direct `drone @flow` access works correctly
- Activated shortcuts are broken for @ argument passing

**Fix:**
```python
# Before run_branch_module, add:
resolved_args = preprocess_args(module_args)
run_branch_module(module_path, resolved_args)
```

**Verification:**
```bash
drone plan create @seed "Test task"
# Should resolve @seed to /home/aipass/seed
```

---

## Data Cleanup

### 2. Test Data Pollution in DRONE.local.json

**Priority:** LOW
**File:** `DRONE.local.json`

**Problem:**
- Sessions 997-1014 contain fake test data
- Values like "Line V1", "Line W2", etc.
- Left over from rollover testing

**Fix:**
- Remove sessions 997-1014 from local.json
- Or run fresh rollover to clean naturally

---

## Code Quality

### 3. Silent Exception Handling

**Priority:** MEDIUM
**Files:** Multiple handlers

**Problem:**
```python
try:
    # operation
except:
    pass  # Errors silently swallowed
```

**Agents Reporting:** 8 of 20

**Fix:**
- Replace `except: pass` with proper error handling
- At minimum, log the exception:
```python
except Exception as e:
    logger.error(f"Operation failed: {e}")
```

**Files to Check:**
- `apps/handlers/discovery/system_operations.py`
- `apps/handlers/routing/discovery.py`
- Any file with bare `except:`

---

### 4. Large Handler Files

**Priority:** LOW (User Decision: Not Splitting)
**File:** `apps/handlers/discovery/system_operations.py` (878 lines)

**Status:** User decided NOT to split. Branch is near-complete and file won't grow further.

**Note:** If future work requires expansion, consider splitting into:
- `system_list.py` - list operations
- `system_refresh.py` - refresh operations
- `system_edit.py` - edit operations

---

### 5. Duplicate JSON Handlers

**Priority:** LOW
**Files:** 3 versions of JSON handlers exist

**Agents Reporting:** 3 of 20

**Investigation Needed:**
- Identify which versions exist
- Determine if consolidation is needed
- May be legitimate (different purposes)

---

## Documentation

### 6. Architecture Decision Documentation

**Priority:** LOW
**Agents Reporting:** 5 of 20

**Gaps Identified:**
- Why modules re-export handlers (encapsulation pattern)
- Why display handlers are exempt from CLI standard
- Handler security guard design rationale

**Suggested Locations:**
- `/home/aipass/aipass_core/drone/README.md`
- Or inline in module docstrings

---

### 7. Test File Contains No Real Tests

**Priority:** LOW
**Agents Reporting:** 4 of 20

**Investigation Needed:**
- Locate test files in drone
- Determine if placeholder or intentionally empty
- Add actual tests if needed

---

## Positive Findings (No Action Required)

The agents confirmed these are working well:

1. **3-Layer Architecture** - Clean separation (entry point → modules → handlers)
2. **Handler Security Guard** - Stack inspection blocks cross-branch handler imports
3. **@ Resolution** - Elegant and centralized in routing handlers
4. **Bypass System** - Properly configured for legitimate exceptions
5. **Help/Introspection** - Now inline in entry point (Seed pattern)

---

## Action Plan

### Phase 1: Critical Fix
- [ ] Fix activated_commands.py - Call preprocess_args() before run_branch_module()
- [ ] Test with `drone plan create @seed "test"`

### Phase 2: Quality Improvements
- [ ] Audit silent exception handlers
- [ ] Add proper error logging where needed
- [ ] Clean test data from DRONE.local.json (optional)

### Phase 3: Documentation (Optional)
- [ ] Document architecture decisions
- [ ] Investigate duplicate JSON handlers
- [ ] Review test file coverage

---

## Completion Criteria

Drone will be considered "complete" when:

1. Activated commands resolve @ arguments correctly
2. No silent exception swallowing in critical paths
3. 100% compliance maintained

Optional nice-to-haves:
- Architecture documentation
- Clean local.json
- Real test coverage

---

*Document created from 20-agent fresh eyes exploration - Session 24*
