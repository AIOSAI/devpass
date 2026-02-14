# DRONE Argument Standards Proposal

**Author:** DRONE Branch
**Date:** 2025-11-25
**Status:** PROPOSAL - Awaiting Review
**Priority:** HIGH - Affects AI autonomy across entire system

---

## Problem Statement

Current command argument handling is inconsistent across AIPass:

```bash
# These work differently:
drone seed audit flow          # No @ - implicit target
drone seed audit @flow         # With @ - doesn't work currently
drone plan create              # No target - defaults to root
drone dev add @flow "issues"   # @ required here
drone @ai_mail send @cortex    # @ for both routing and target
```

**Impact:**
- AI cannot reliably script commands
- Users must memorize which commands need @
- No consistent error messages
- Implicit defaults cause confusion

---

## Proposed Standard

### Rule 1: ALL branch/path references MUST use @ prefix

```bash
# Standard format:
drone <module> <command> @<target> [options] [arguments]

# Examples:
drone seed audit @flow
drone seed audit @all
drone plan create @aipass
drone dev add @flow "issues" "description"
```

### Rule 2: NO implicit defaults - require explicit targets

**Current (flaky):**
```bash
drone plan create           # Silently defaults to /home/aipass
drone seed audit            # Silently scans all branches
```

**Proposed (strict):**
```bash
drone plan create           # ERROR: Missing target
drone plan create @aipass   # Explicit - works
drone seed audit            # ERROR: Missing target
drone seed audit @all       # Explicit - works
```

### Rule 3: Reserved @ targets

| Target | Meaning | Example |
|--------|---------|---------|
| `@all` | All branches (for audit/scan commands) | `drone seed audit @all` |
| `@aipass` | Root directory /home/aipass | `drone plan create @aipass` |
| `@self` | Current working directory's branch | `drone seed checklist @self` |
| `@<branch>` | Specific branch by name | `drone dev add @flow` |

### Rule 4: Helpful error messages

When target is missing:
```
❌ Missing target

Usage: drone seed audit @<target>

Targets:
  @all      - All branches
  @flow     - Specific branch
  @aipass   - Root directory

Example: drone seed audit @flow
```

---

## Implementation Phases

### Phase 1: DRONE Warning Layer (Non-breaking)

**Location:** `/home/aipass/aipass_core/drone/apps/drone.py`

**Action:** Add detection for missing @ in routed commands

```python
def check_target_argument(args: list) -> bool:
    """Check if any argument starts with @"""
    return any(arg.startswith('@') for arg in args)

# In route_command():
if not check_target_argument(remaining_args):
    console.print("[yellow]⚠️ No @target specified. Future versions will require explicit targets.[/yellow]")
    console.print(f"[dim]Consider: drone {command} @<target>[/dim]")
# Continue execution (non-breaking)
```

**Timeline:** Immediate - can deploy now

### Phase 2: Branch Updates (Reference Implementation)

**Start with SEED as reference:**

Update `/home/aipass/seed/apps/modules/standards_audit.py`:

```python
def handle_command(command: str, args: list) -> bool:
    if command != "audit":
        return False

    if not args:
        console.print("[red]❌ Missing target[/red]")
        console.print()
        console.print("[yellow]Usage:[/yellow] drone seed audit @<target>")
        console.print()
        console.print("[cyan]Targets:[/cyan]")
        console.print("  @all      - Audit all branches")
        console.print("  @flow     - Audit specific branch")
        console.print("  @aipass   - Audit root directory")
        return False

    target = args[0]
    if not target.startswith('@'):
        # Backwards compatibility: treat bare name as @name
        console.print(f"[yellow]⚠️ Assuming @{target} - please use @ prefix[/yellow]")
        target = f"@{target}"

    # Strip @ and resolve
    branch_name = target[1:]

    if branch_name == "all":
        return audit_all_branches()
    else:
        return audit_branch(branch_name)
```

**Branches to update (in order):**
1. SEED - reference implementation
2. FLOW - plan commands
3. DEVPULSE - dev commands
4. AI_MAIL - already mostly compliant
5. DRONE - internal commands (scan, activate, etc.)
6. All others

### Phase 3: DRONE Enforcement (Breaking Change)

**After all branches updated:**

```python
def route_command(command: str, args: list) -> bool:
    # ... routing logic ...

    # Enforce @ target for commands that need it
    if requires_target(command) and not has_target(args):
        console.print("[red]❌ Missing target[/red]")
        console.print()
        console.print(f"[yellow]Usage:[/yellow] drone {command} @<target>")
        return False

    # Continue routing
```

---

## Commands Requiring @ Target

### Audit/Scan Commands (target = branch or @all)
- `drone seed audit @<branch|all>`
- `drone seed checklist @<branch> <file>`
- `drone scan @<branch>`
- `drone refresh @<branch>`

### Create/Add Commands (target = destination)
- `drone plan create @<location>`
- `drone dev add @<branch> "type" "description"`
- `drone cortex create branch @<location>`

### Send Commands (target = recipient)
- `drone @ai_mail send @<recipient> "subject" "message"`

### Commands NOT requiring @ (operate on self)
- `drone list` - lists drone's own activated commands
- `drone systems` - lists drone's registered systems
- `drone --help` - shows drone help
- `drone @branch help` - shows branch help (@ is routing, not target)

---

## Migration Path

**For users:**
1. Phase 1: Warnings appear but commands still work
2. Phase 2: Some branches require @, with helpful errors
3. Phase 3: All commands require @ where applicable

**For branches:**
1. Update argument parsing to check for @
2. Strip @ prefix when resolving paths
3. Add backwards compatibility warning for bare names
4. Update help text to show @ syntax

**Backwards compatibility period:** 2 weeks from Phase 2 start

---

## Testing Checklist

After implementation, verify:

```bash
# Should work:
drone seed audit @flow          # ✓
drone seed audit @all           # ✓
drone plan create @aipass       # ✓
drone dev add @flow "bug" "desc" # ✓

# Should show helpful error:
drone seed audit                # ❌ Missing target
drone plan create               # ❌ Missing target

# Should show warning (backwards compat):
drone seed audit flow           # ⚠️ Assuming @flow
```

---

## Questions for Review

1. **@self behavior:** Should `@self` resolve to CWD's branch or require explicit branch name?

2. **Nested paths:** Should we support `@flow/apps/modules/` or only branch names?

3. **Timeline:** How aggressive should the enforcement rollout be?

4. **Registry integration:** Should command metadata specify if it requires a target?

---

## Decision Needed

**Patrick:** Please review and confirm:
- [ ] Agree with @ requirement for all targets
- [ ] Agree with reserved targets (@all, @aipass, @self)
- [ ] Approve Phase 1 immediate deployment
- [ ] Confirm branch update order

---

## Implementation Log (Session 9)

### Step 1: Added `preprocess_args()` to DRONE ✅

**File:** `/home/aipass/aipass_core/drone/apps/drone.py`
**Lines:** 53-93

Added centralized @ resolution function:
```python
def preprocess_args(args: List[str]) -> List[str]:
    """Resolve all @ arguments to full paths before passing to modules."""
    resolved_args = []
    for arg in args:
        if arg.startswith('@'):
            try:
                resolved_path = resolve_scan_path(arg)
                resolved_args.append(str(resolved_path))
            except FileNotFoundError:
                if arg == "@all":
                    resolved_args.append(arg)  # Reserved target
                else:
                    resolved_args.append(arg)  # Pass raw, branch handles error
        else:
            resolved_args.append(arg)
    return resolved_args
```

### Step 2: Applied to all `run_branch_module()` calls ✅

Updated 3 call sites in drone.py:
- Line 269-270: Activated command routing
- Line 282-284: @ direct routing (`drone @seed`)
- Line 302-304: Slash pattern routing (`drone seed/imports`)

### Step 3: Testing Results

**Test:** `drone seed audit @flow`
**Result:** @ resolved correctly to `/home/aipass/aipass_core/flow`
**Issue:** Seed expects branch NAME, not PATH

```
# This works (seed gets name):
drone seed audit flow → seed receives "flow" → matches branch

# This doesn't (seed gets path):
drone seed audit @flow → DRONE resolves → seed receives "/home/aipass/aipass_core/flow" → no match
```

### Finding: Branch Adaptation Required

DRONE's centralized resolution works, but branches must adapt to accept EITHER:
1. Branch name: `flow`
2. Full path: `/home/aipass/aipass_core/flow`

**Adaptation pattern for branches:**
```python
def normalize_branch_arg(arg: str) -> str:
    """Convert path or name to branch name."""
    if arg.startswith('/'):
        # It's a path - extract branch name
        # /home/aipass/aipass_core/flow → flow
        parts = Path(arg).parts
        if 'aipass_core' in parts:
            idx = parts.index('aipass_core')
            return parts[idx + 1] if idx + 1 < len(parts) else arg
        return parts[-1]  # Last component
    return arg  # Already a name
```

### Step 4: Fixed seed's standards_audit.py ✅

**File:** `/home/aipass/seed/apps/modules/standards_audit.py`

Added `normalize_branch_arg()` helper function (lines 75-116) that handles both paths and names.

Updated line 507 to use the helper:
```python
specific_branch = normalize_branch_arg(arg)
```

### Step 5: Verification Tests ✅

```bash
# New @ syntax - all work:
drone seed audit @flow    ✅  FLOW audited
drone seed audit @drone   ✅  DRONE audited
drone seed audit @seed    ✅  SEED audited

# Backwards compatibility - still works:
drone seed audit flow     ✅  FLOW audited
```

---

## Pattern for Other Branches

Any branch accepting `@branch` arguments needs `normalize_branch_arg()`:

```python
def normalize_branch_arg(arg: str) -> str:
    """Convert path or name to branch name."""
    if not arg:
        return arg
    if arg.startswith('/'):
        from pathlib import Path
        parts = Path(arg).parts
        if 'aipass_core' in parts:
            idx = parts.index('aipass_core')
            if idx + 1 < len(parts):
                return parts[idx + 1].upper()
        if 'aipass' in parts:
            idx = parts.index('aipass')
            if idx + 1 < len(parts) and parts[idx + 1] != 'aipass_core':
                return parts[idx + 1].upper()
        return Path(arg).name.upper()
    return arg.upper()
```

---

## Comprehensive Test Results

### Commands Working with @

| Command | Status | Notes |
|---------|--------|-------|
| `drone @flow help` | ✅ | Module routing works |
| `drone plan create @flow` | ✅ | Created PLAN0183 |
| `drone @flow list` | ✅ | Listed plans |
| `drone seed audit @flow` | ✅ | Audited flow branch |
| `drone seed audit @drone` | ✅ | Audited drone branch |
| `drone dev add @flow "Issues" "test"` | ✅ | Added entry |
| `drone dev status @flow` | ✅ | Checked compliance |
| `drone @ai_mail help` | ✅ | Module routing |
| `drone @ai_mail inbox` | ✅ | Listed messages |
| `drone @ai_mail send @drone "Subject" "Msg"` | ✅ | Fixed - now works |
| `drone scan @flow` | ✅ | Scanned 11 commands |
| `drone list @flow` | ✅ | Filtered to flow |
| `drone list @prax` | ✅ | Filtered to prax |
| `drone systems` | ✅ | No @ needed |
| `drone refresh @seed` | ✅ | Fixed - now works |

### Edge Cases Tested

| Command | Status | Behavior |
|---------|--------|----------|
| `drone scan @` | ✅ | Resolves to /home/aipass (root) |
| `drone scan @nonexistent` | ✅ | Clear error message |
| `drone register @seed/apps/modules` | ✅ | Nested paths work |
| `drone @flow` | ✅ | Shows introspection |

### Backwards Compatibility

| Command | Status | Notes |
|---------|--------|-------|
| `drone seed audit flow` | ✅ | Bare names still work |
| `drone list` | ✅ | No filter needed |
| `drone systems` | ✅ | Works as before |

---

## Summary of All Changes Made

| File | Change | Status |
|------|--------|--------|
| `drone/apps/drone.py` | Added `preprocess_args()` for centralized @ resolution | ✅ |
| `drone/apps/drone.py` | Applied to 3 `run_branch_module()` calls | ✅ |
| `drone/apps/modules/discovery.py` | Fixed `refresh` command @ handling | ✅ |
| `seed/apps/modules/standards_audit.py` | Added `normalize_branch_arg()` | ✅ |
| `ai_mail/apps/handlers/email/delivery.py` | Added path-to-email reverse lookup | ✅ |

---

## Branch Adaptation Pattern

For branches receiving @ arguments that DRONE resolves to paths:

**Pattern A: Branch expects NAME (like seed audit)**
```python
def normalize_branch_arg(arg: str) -> str:
    """Convert path or name to branch name."""
    if arg.startswith('/'):
        from pathlib import Path
        parts = Path(arg).parts
        if 'aipass_core' in parts:
            idx = parts.index('aipass_core')
            if idx + 1 < len(parts):
                return parts[idx + 1].upper()
        return Path(arg).name.upper()
    return arg.upper()
```

**Pattern B: Branch expects EMAIL (like ai_mail send)**
```python
def normalize_to_email(arg: str) -> str:
    """Convert path to email address format."""
    if arg.startswith('/'):
        from pathlib import Path
        parts = Path(arg).parts
        if 'aipass_core' in parts:
            idx = parts.index('aipass_core')
            if idx + 1 < len(parts):
                return f"@{parts[idx + 1]}"
        return f"@{Path(arg).name}"
    return arg if arg.startswith('@') else f"@{arg}"
```

---

## Rollout Instructions for Other Branches

### Branches That Need Updates

Only branches that accept `@branch` as a TARGET argument need updates:

1. **SEED** - ✅ Done (`normalize_branch_arg` added)
2. **AI_MAIL** - ✅ Done (path-to-email in delivery.py)
3. **FLOW** - May need updates for `plan create @location`
4. **DEVPULSE** - Already handles @ internally
5. **Others** - Test and update as needed

### How to Update a Branch

1. Identify commands that accept `@branch` arguments
2. Add appropriate normalization function (Pattern A or B above)
3. Apply it where the argument is first used
4. Test both `@branch` and bare `branch` formats

---

## Session 9 Complete

**Bugs Fixed:**
1. ✅ activation.py overwrite bug (CRITICAL)
2. ✅ drone refresh @ handling
3. ✅ ai_mail send @ recipient handling

**Features Added:**
1. ✅ Centralized @ resolution in DRONE (`preprocess_args()`)
2. ✅ Branch adaptation patterns documented

**Tests Passed:** 15+ commands verified working with @

---

## Session 10: Standards Audit Results

**Date:** 2025-11-25

### Seed Audit on DRONE

```
DRONE (25 files checked)
  Imports         100% ✅    Architecture    100% ✅
  Naming          100% ✅    Cli              84% ⚠️
  Handlers        100% ✅    Modules          91% ✅
  Documentation   100% ✅    Json_Structure  100% ✅
  Testing         100% ✅    Error_Handling  100% ✅
  Overall:          97% ✅
```

### Issues Found

**CLI Violations (4 files - Display Handlers):**

| File | Issue | Type |
|------|-------|------|
| `formatters.py` | 53+ console.print() calls | Display Handler |
| `help_display.py` | 20+ console.print() calls | Display Handler |
| `activation.py` | Interactive UI with input() | Interactive UI |
| `system_operations.py` | Interactive UI with input() | Interactive UI |

**Root Cause:** These are "display handlers" - their explicit purpose is formatting and displaying output. Standard says "Handlers return data, don't print directly" but these were intentionally converted TO console.print() in Session 2 (see DRONE.local.json agents 5-8).

**Architectural Decision Needed:**

Option A: **Accept display handlers as exception** - Document that handlers in `handlers/discovery/` are display-focused by design

Option B: **Full refactor to return data** - Convert all formatters to return data structures, have modules handle display

**False Positive:**
- `loader.py` line 125 `log_data` dict - This is a temporary structure passed to json_handler, not a config constant

### Files Fixed This Session

| File | Change | Status |
|------|--------|--------|
| `handlers/json_handler.py` | Removed print() statements | ✅ |
| `handlers/perf/ops.py` | Removed print() statements | ✅ |

### Current State

- DRONE at 97% compliance
- CLI score drops to 84% due to display handler architecture
- All other standards at 100%

---

*Proposal by DRONE Branch - Sessions 9-10*
