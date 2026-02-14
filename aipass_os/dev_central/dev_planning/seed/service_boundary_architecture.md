# Service Boundary Architecture

**Status:** ✅ COMPLETE
**Created:** 2025-11-29
**Updated:** 2025-11-29 (Session 24 - All 18 branches protected, violations fixed)
**Context:** Discussion between Patrick and AIPASS on import boundaries

---

## The Problem

Branches are importing other branches' handlers directly, bypassing entry points. This creates:
- Fragile dependencies (change handler, break unknown consumers)
- No service contract (anyone can reach into your guts)
- Debugging nightmares (why did Flow break when we changed Cortex?)

**Violations found and resolved:** Cortex (2) fixed with Rich Confirm, API (9) were valid infrastructure imports

---

## The Model

### Two Types of Branches

1. **CLI Tools** - Used via command line, not imported
   - Flow, Seed, AI_Mail, Backup_System
   - You run `drone @flow create`, you don't `import flow`

2. **Library Services** - Imported by other code
   - Prax (logging), CLI (formatting), API (LLM calls), Memory Bank (vectors)
   - You `from prax.apps.modules.logger import logger`

---

## Drone's @ Resolution (CRITICAL)

**Rule:** Drone resolves ALL @ symbols BEFORE passing to branches. Branches NEVER handle @.

### How It Works

```
User types:    drone @flow create @seed "Plan name"
                     ↓
Drone:         1. Resolves @flow → routes to Flow
               2. Resolves @seed → /home/aipass/seed
               3. Passes resolved path to Flow
                     ↓
Flow receives: create /home/aipass/seed "Plan name"
```

**Flow never sees `@seed`.** Flow receives `/home/aipass/seed`. Flow has ZERO @ handling code.

### Why This Matters

- **Separation of concerns:** Drone owns @, branches own their domain
- **Independence:** Branches don't need Drone imports to function
- **Simplicity:** No @ handling code scattered across branches
- **Single source of truth:** Only Drone reads BRANCH_REGISTRY.json for @

### Anti-Pattern (WRONG)

```python
# Flow handler importing Drone to resolve @ - WRONG
from drone.apps.modules import resolve_target

def some_handler(location):
    if location.startswith("@"):
        path = resolve_target(location)  # Flow handling @ - NO!
```

If a branch has @ handling code, it's **architectural debt**. The @ should have been resolved by Drone before the branch ever received it.

### Correct Pattern

```python
# Flow handler receives already-resolved path - CORRECT
def some_handler(location):
    path = Path(location)  # Already /home/aipass/seed, not @seed
```

### Status: Flow CLEAN ✅

Flow's Drone imports have been removed (Session 23). Flow now:
- Receives pre-resolved paths from Drone (no @ symbols)
- Has zero @ handling code
- Security guard deployed to handlers/__init__.py

### The Import Hierarchy

```
External Branch
      ↓
  Entry Point (prax.py, drone.py, cli.py)
      ↓
    Modules (prax/apps/modules/*.py)
      ↓
    Handlers (prax/apps/handlers/*/*.py)  ← NEVER EXPOSED
```

**Rule:** External consumers stop at MODULES. They never touch handlers.

### Why Modules, Not Entry Points?

Entry point (`prax.py`) is the CLI interface. But services expose multiple features:
- Prax exposes: logger, watcher, monitor
- Drone exposes: resolve, route, scan
- CLI exposes: header, success, error, warning

So the pattern is:
```python
import prax
from prax.apps.modules.logger import logger  # ✓ Module level

# NOT:
from prax.apps.handlers.logging.file_writer import write_log  # ✗ Handler level
```

---

## Handler Rules

### Within a Branch (Internal) - ALLOWED

Handlers within the SAME BRANCH can import each other freely, even across packages:

```
flow/apps/handlers/plan/create.py
       ↓ can import
flow/apps/handlers/registry/load.py
       ↓ can import
flow/apps/handlers/json/json_handler.py
```

All Flow handlers. All good. They're coworkers in the same branch.

**Rationale:** Handlers are unique and custom to each branch. Trying to enforce package-level isolation adds complexity without benefit. The security boundary is at the BRANCH level.

### Across Branches (External) - BLOCKED

**Absolute rule:** Never import another branch's handlers. Hard security block.

```python
# WRONG - reaching into Cortex handlers
from cortex.apps.handlers.error_handler import track_operation
# → ERROR: "flow is trying to access cortex handlers. Access denied."

# RIGHT - import Cortex service, use what it exposes via modules
from cortex.apps.modules.error_tracking import track_operation
```

**Exception:** JSON handler is a common utility. Each branch gets its OWN COPY, not a cross-branch import.

---

## Security Layer

**Goal:** If a branch tries to import your handlers directly, it fails. Period.

### Implementation Status: GUARDS DEPLOYED ✅

**Working guards deployed to:**
- `/home/aipass/aipass_core/prax/apps/handlers/__init__.py` (reference implementation)
- `/home/aipass/aipass_core/drone/apps/handlers/__init__.py` (tested, working)

### How It Works

The guard runs at import time in `handlers/__init__.py`:
1. Walks the stack to find the real caller file
2. Extracts the actual import statement from code context
3. Checks if caller is from the same branch
4. If external → raises `ImportError` with detailed message

### Error Output (Production Ready)

```
============================================================
ACCESS DENIED: Cross-branch handler import blocked
============================================================
  Caller branch: flow
  Caller file:   list_plans.py
  Blocked:       from prax.apps.handlers.logging.setup import get_logger as test_import

  Handlers are internal to their branch.
  Use the module API instead:
    from prax.apps.modules.<module> import <function>

  Example:
    from prax.apps.modules.logger import logger
============================================================
```

### Known Limitation

**Python module caching:** The guard runs ONCE when handlers package is first imported. If a valid internal file (like `logger.py`) imports handlers first, subsequent external imports in the same Python process bypass the guard.

**In practice:** This catches violations at development time when the violating import runs first. Not a runtime security boundary, but effective for catching bad patterns early.

### Guard Code Location

Reference implementation: `/home/aipass/aipass_core/prax/apps/handlers/__init__.py` (~90 lines)

---

## Service Contracts

Each library service defines:
1. **What it exposes** (modules/features available to external consumers)
2. **What it requires** (contracts consumers must meet)

### Examples

| Service | Exposes | Requires |
|---------|---------|----------|
| Prax | logger, watcher | Use logger.info/error/debug in your code |
| CLI | header, success, error, warning | Nothing |
| API | get_response | Valid API key in env |
| Memory Bank | store, search, rollover | Standard memory file format |

**Note:** Drone is NOT a library service. Drone is a CLI router. Branches don't import Drone - they receive commands through Drone with @ already resolved.

---

## Transitive Dependencies

If Prax imports Watcher internally:
- Drone imports Prax
- Drone gets logging
- Drone does NOT import Watcher
- Prax owns that relationship

**You import the service that owns the capability.** You don't care about its internal dependencies.

---

## Next Steps

### Completed ✅
1. [x] POC guard working on Prax handlers
2. [x] Clear error messages showing exact blocked import
3. [x] Handler rules finalized (same branch = allowed, cross branch = blocked)
4. [x] Update Seed standards documentation (2025-11-29)
5. [x] Deploy guard to Drone (tested, working)
6. [x] Seed encapsulation_check.py already detects cross-branch handler imports

### System-Wide Assessment Results (2025-11-29, Session 24 - COMPLETE)

**ALL 18 BRANCHES NOW PROTECTED ✅**

| Branch | Guard | Notes |
|--------|-------|-------|
| Prax | ✅ | Reference implementation |
| Drone | ✅ | Protected |
| Seed | ✅ | Protected |
| CLI | ✅ | Protected |
| AI_Mail | ✅ | Protected |
| Flow | ✅ | Protected (Session 23) |
| Cortex | ✅ | Fixed violations + guard (Session 24) |
| API | ✅ | Guard deployed (Session 24) |
| Backup_System | ✅ | Guard deployed (Session 24) |
| DevPulse | ✅ | Guard deployed (Session 24) |
| Memory_Bank | ✅ | Guard deployed (Session 24) |
| .VSCODE | ✅ | Guard deployed (Session 24) |
| AIPASS | ✅ | Guard deployed (Session 24) |
| AIPASS_CORE | ✅ | Guard deployed (Session 24) |
| GIT_REPO | ✅ | Guard deployed (Session 24) |
| MCP_SERVERS | ✅ | Guard deployed (Session 24) |
| PERMISSIONS | ✅ | Guard deployed (Session 24) |
| PROJECTS | ✅ | Guard deployed (Session 24) |

**Violation Fixes (Session 24):**
- Cortex (2): Changed `prax.apps.handlers.cli.prompts` → `rich.prompt.Confirm`
- API (9): Confirmed as **VALID** infrastructure imports (CLI console for display)

### Completed Session 24 ✅
7. [x] Deploy guards to all 12 remaining branches - DONE
8. [x] Fix Cortex violations (Rich Confirm replacement)
9. [x] Cortex template updated for new branches
10. [x] All 18 branches protected

### Completed Session 23 ✅
8. [x] Flow @ handling debt FIXED:
   - Removed `drone.apps.modules.resolve_target` import from Flow
   - Removed dead `validate_plan_location()` function
   - Security guard deployed to Flow handlers/__init__.py
   - Flow now receives pre-resolved paths only
9. [x] Fixed broken activated commands (`drone plan create` etc):
   - Created `/home/aipass/aipass_core/drone/apps/modules/activated_commands.py`
   - Restored shortcut command routing
10. [x] Fixed `drone list @api` filter bug (accepts both @api and api)
11. [x] Fixed scanner regex - added word boundaries to avoid `subcommand` matching `command`
12. [x] Fixed Flow registry_monitor command name mismatch (monitor → registry)

### @ Handling Audit (Session 23 - CORRECTED)

System-wide check for unnecessary @ handling code now that Drone pre-resolves:

| Branch | Finding | Status |
|--------|---------|--------|
| AI_Mail | delivery.py:154-177 path→email conversion | ✅ VALID - needed for email system |
| DevPulse | ops.py:91-106 hybrid resolver | ✅ VALID - supports both @ and path inputs |
| API | None | ✅ Clean |
| Backup_System | None | ✅ Clean |
| CLI | None | ✅ Clean |
| Cortex | Only @email formatting | ✅ Clean |
| Prax | normalize_branch_arg() - defensive | ✅ VALID |
| Memory_Bank | None | ✅ Clean |
| Seed | Uses drone.apps.modules correctly | ✅ VALID |
| Flow | Cleaned Session 23 | ✅ Clean |

**Correction:** Earlier audit flagged AI_Mail and DevPulse code as "DEAD" - detailed analysis shows both are VALID:
- AI_Mail needs path→email conversion because it works with @ addresses internally
- DevPulse hybrid resolver allows both direct user calls (`@branch`) and Drone calls (paths)

### Pending Tasks - Agent Execution Guide

---

## IMPORTANT: Directories to IGNORE

When deploying agents, instruct them to **SKIP** these directories:
- `artifacts/` - Old code being preserved
- `backups/` - Backup files
- `.backup/` - Hidden backups
- `.archive/` - Archived code
- `.archive.temp/` - Temporary archives
- `code_archive/` - Memory Bank archived code
- `__pycache__/` - Python cache
- `.venv/` - Virtual environments
- `node_modules/` - Node dependencies

These contain legacy/backup code, not active implementations.

---

## PHASE 1: Deploy Guards to Clean Branches (Ready Now)

**Total: 10 branches ready** (no violations to fix first)
**Reference:** `/home/aipass/aipass_core/prax/apps/handlers/__init__.py` (~90 lines)

### Step 1.1: Deploy to aipass_core branches (3 agents)
```
Agent 1: Backup_System → /home/aipass/aipass_core/backup_system/apps/handlers/__init__.py
Agent 2: DevPulse → /home/aipass/aipass_core/devpulse/apps/handlers/__init__.py
Agent 3: Memory_Bank → /home/aipass/MEMORY_BANK/apps/handlers/__init__.py
```

### Step 1.2: Deploy to other locations (7 agents)
```
Agent 4: .VSCODE → /home/aipass/.vscode/apps/handlers/__init__.py
Agent 5: AIPASS → /home/aipass/apps/handlers/__init__.py
Agent 6: AIPASS_CORE → /home/aipass/aipass_core/apps/handlers/__init__.py
Agent 7: GIT_REPO → /home/aipass/aipass_os/dev_central/git_repo/apps/handlers/__init__.py
Agent 8: MCP_SERVERS → /home/aipass/mcp_servers/apps/handlers/__init__.py
Agent 9: PERMISSIONS → /home/aipass/aipass_os/dev_central/permissions/apps/handlers/__init__.py
Agent 10: PROJECTS → /home/aipass/projects/apps/handlers/__init__.py
```

**For each agent:**
- Read reference guard from prax
- Update branch name in guard code
- Write to target handlers/__init__.py
- Test import works

---

## PHASE 2: Fix Handler Violations

### Step 2.1: Investigate Cortex violations (2)
```
Agent: Find and fix Cortex handler imports
- Grep for "prax.apps.handlers" in /home/aipass/aipass_core/cortex/apps/
- These imports reference non-existent path (prax.apps.handlers.cli.prompts)
- Either: Remove import (if unused) OR change to correct module path
- Report: file, line, current import, recommended fix
```

### Step 2.2: Investigate API violations (9)
```
Agent: Find and fix API handler imports
- Grep for "cli.apps.modules" in /home/aipass/aipass_core/api/apps/handlers/
- Issue: handlers importing modules creates circular risk
- For each: determine if import is needed, suggest alternative
- Report: file, line, current import, recommended fix
```

### Step 2.3: Fix PROJECTS broken imports
```
Agent: Fix broken imports in PROJECTS artifacts/
- File: /home/aipass/projects/artifacts/create_project_folder.py line 133
- Current: from aipass_core.flow.apps.flow_plan import create_plan
- Fix to: from flow.apps.modules.create_plan import create_plan
- Also check artifacts/projects.py for similar issues
```

### Step 2.4: Apply fixes (after investigation)
```
Deploy fix agents based on investigation results
```

---

## PHASE 3: Deploy Guards to Fixed Branches

### Step 3.1: Deploy guards after violations fixed
```
Agent 1: Deploy guard to Cortex (after Step 2.1 complete)
Agent 2: Deploy guard to API (after Step 2.2 complete)
```

---

## PHASE 4: Update Cortex Branch Template

### Step 4.1: Add guard to template
```
Agent: Update Cortex branch template
- Find template location in /home/aipass/aipass_core/cortex/
- Add handlers/__init__.py guard template
- Ensure new branches get guard automatically
```

---

## PHASE 5: Fix UX Issues (8 modules)

### Step 5.1: Deploy 8 agents in parallel
```
Agent 1: Drone discovery.py
- Show subcommands when run without args instead of "Unknown command"

Agent 2: Seed diagnostics_audit.py
- Show usage instead of auto-executing

Agent 3: Prax terminal_module.py
- Add list of valid subcommands to error message

Agent 4: Backup integrations.py
- Fix import error crash, add help output

Agent 5: AI_Mail error_monitor.py
- Replace argparse error with help output

Agent 6: AI_Mail local_memory_monitor.py
- Replace argparse error with help output

Agent 7: CLI display.py
- Fix logic bug making `demo` subcommand unreachable

Agent 8: CLI templates.py
- Fix logic bug making `demo` subcommand unreachable
```

---

## Execution Checklist - COMPLETE ✅

### Phase 1-4: All Complete (Session 24)
| Task | Status |
|------|--------|
| Deploy guard: Backup_System | ✅ |
| Deploy guard: DevPulse | ✅ |
| Deploy guard: Memory_Bank | ✅ |
| Deploy guard: .VSCODE | ✅ |
| Deploy guard: AIPASS | ✅ |
| Deploy guard: AIPASS_CORE | ✅ |
| Deploy guard: GIT_REPO | ✅ |
| Deploy guard: MCP_SERVERS | ✅ |
| Deploy guard: PERMISSIONS | ✅ |
| Deploy guard: PROJECTS | ✅ |
| Fix Cortex violations (2) | ✅ Rich Confirm |
| API violations (9) | ✅ Valid imports |
| Deploy guard: Cortex | ✅ |
| Deploy guard: API | ✅ |
| Update Cortex template | ✅ |

### Phase 5: Fix UX Issues (8 modules) - COMPLETE ✅
| Task | Status |
|------|--------|
| Fix UX: Drone discovery.py | ✅ Shows 9 subcommands |
| Fix UX: Seed diagnostics_audit.py | ✅ Shows help instead of auto-execute |
| Fix UX: Prax terminal_module.py | ✅ Shows enable/disable subcommands |
| Fix UX: Backup integrations.py | ✅ Fixed import + help |
| Fix UX: AI_Mail error_monitor.py | ✅ Fixed argparse |
| Fix UX: AI_Mail local_memory_monitor.py | ✅ Fixed argparse |
| Fix UX: CLI display.py | ✅ Fixed demo logic bug |
| Fix UX: CLI templates.py | ✅ Fixed demo logic bug |

---

## UX Audit: Subcommand Discoverability (Session 23)

Audit of all 18 branches for modules with poor UX when run without arguments.

### Pattern Required
When a module has subcommands, running without args should show available subcommands (not error or auto-execute).

### Issues Found (8 modules)

| Branch | Module | Issue |
|--------|--------|-------|
| **Drone** | discovery.py | Returns "Unknown command" instead of showing subcommands |
| **Seed** | diagnostics_audit.py | Auto-executes instead of showing usage |
| **Prax** | terminal_module.py | Shows error but no list of valid subcommands |
| **Backup** | integrations.py | Crashes with import error - no help at all |
| **AI_Mail** | error_monitor.py | argparse throws error instead of showing help |
| **AI_Mail** | local_memory_monitor.py | argparse throws error instead of showing help |
| **CLI** | display.py | `demo` subcommand unreachable (logic bug) |
| **CLI** | templates.py | `demo` subcommand unreachable (logic bug) |

### Fixed ✅
- **Flow** registry_monitor.py - Added "Commands: scan | start | stop | status" to output

### Clean Branches
API, Cortex, DevPulse, Memory_Bank - all show help when run without args

---

## Open Questions

1. ~~**Handler-to-handler within same branch but different packages**~~ - **RESOLVED: Allowed.** Same branch = same security domain.
2. ~~**How strict on enforcement?**~~ - **RESOLVED:** Guard in handlers/__init__.py catches first violations. Seed audit catches rest at code review time.
3. ~~**Migration path**~~ - **RESOLVED:** Seed check + guards deployed to all 18 branches.

---

## Discovered Issues (Post-Deployment)

Issues discovered by guards catching violations at runtime:

### Flow close_plan.py - Handler Violation (Session 24) - FIXED ✅
**File:** `/home/aipass/aipass_core/flow/apps/modules/close_plan.py`
**Issue:** Imported `api.apps.handlers.openrouter.client` via `flow/apps/handlers/mbank/process.py`
**Fix Applied:**
1. Added `get_response()` wrapper to `/home/aipass/aipass_core/api/apps/modules/openrouter_client.py`
2. Changed import in `process.py` to use `api.apps.modules.openrouter_client`
3. Flow auto-discovery now loads close_plan (no manual registration needed)
**Result:** `drone @flow close --help` works ✅

---

## Additional Fixes (Session 24)

### Drone @branch/module Pattern - FIXED ✅
**File:** `/home/aipass/aipass_core/drone/apps/drone.py`
**Issue:** `drone @seed/imports` failed - @ handler treated whole string as path
**Fix:** Added check for `/` within @ commands, strips @ and routes to slash handler
**Result:** `drone @seed/module --help` now works correctly
**Patterns working:**
- `drone @seed/standards_checklist --help` ✅
- `drone @flow/list_plans --help` ✅
- `drone @drone/discovery --help` ✅

---

*This is living documentation. Update as design evolves.*
