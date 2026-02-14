# Audit System Documentation

**Branch:** SEED
**Created:** 2025-11-29
**Updated:** 2025-11-29

---

## Overview

The Seed audit system provides comprehensive code quality and standards compliance checking across all AIPass branches. It combines standards verification (architectural patterns, naming conventions, documentation) with type error detection (pyright) to generate detailed compliance dashboards.

The audit system is the difference between "does this code work?" and "does this code meet our standards?" It's built to catch violations that would accumulate over time - architectural drift, encapsulation leaks, business logic creeping into the wrong layers.

## Key Concepts

- **System-wide scanning** - Discovers and audits all branches from BRANCH_REGISTRY.json
- **Comprehensive checking** - Examines ALL Python files, not just entry points
- **Multi-dimensional scoring** - 12 separate standards, each scored independently
- **Violation reporting** - Detailed file-level issues with clickable paths
- **Type safety** - Integrated pyright diagnostics for type errors

## Commands

### Basic Usage

```bash
# Audit all branches (full system scan)
drone @seed audit

# Audit specific branch
drone @seed audit cortex
drone @seed audit @flow

# Direct execution
python3 /home/aipass/seed/apps/seed.py audit
python3 /home/aipass/seed/apps/seed.py audit drone
```

### Command Options

The `audit` command has two modes:

1. **System-wide audit** - Scans all 18 branches from BRANCH_REGISTRY.json
2. **Single-branch audit** - Focused scan on one branch with detailed output

Both modes check ALL Python files in the branch's `apps/` directory (excluding `__init__.py` and archived files).

## How Branch Discovery Works

The audit system uses a two-tier discovery mechanism:

### Primary: BRANCH_REGISTRY.json

Located at `/home/aipass/BRANCH_REGISTRY.json`, this is the source of truth for all AIPass branches.

```json
{
  "metadata": {
    "version": "1.0.0",
    "total_branches": 18
  },
  "branches": [
    {
      "name": "SEED",
      "path": "/home/aipass/seed",
      "email": "@seed",
      "status": "active"
    }
  ]
}
```

The discovery process:
1. Reads BRANCH_REGISTRY.json
2. For each branch, locates the entry point:
   - Standard: `apps/{branch_name}.py` (lowercase)
   - SEED: `apps/seed.py`
   - MEMORY_BANK: `apps/modules/rollover.py`
   - .VSCODE: `apps/vscode.py`
3. Verifies the path exists
4. Returns list of valid branches

### Fallback: Manual Directory Scan

If BRANCH_REGISTRY.json is missing or unreadable:
- Scans `/home/aipass/aipass_core/*/apps/` for entry points
- Checks known special locations (SEED, MEMORY_BANK)
- Less reliable - registry is the recommended approach

**Result:** Audit finds all 18 active branches consistently.

## What Gets Audited

### File Selection

The audit scans **ALL Python files** in each branch's `apps/` directory:
- Entry point (e.g., `apps/seed.py`)
- All modules in `apps/modules/`
- All handlers in `apps/handlers/`
- All subpackages (recursively)

**Excluded:**
- `__init__.py` files (infrastructure only)
- Files in archived/backup/artifact directories
- Non-Python files

### Standards Checked

Each file is evaluated against 12 independent standards:

| Standard | What It Checks | Handler |
|----------|----------------|---------|
| **Imports** | Import organization, forbidden imports, aipass_core dependencies | `imports_check.py` |
| **Architecture** | 3-layer structure (apps/modules/handlers), required directories | `architecture_check.py` |
| **Naming** | File naming conventions, module naming patterns | `naming_check.py` |
| **CLI** | Forbidden shell commands (rm, sudo, chmod), dangerous operations | `cli_check.py` |
| **Handlers** | Handler implementation patterns, no business logic in handlers | `handlers_check.py` |
| **Modules** | Module orchestration patterns, no implementation details in modules | `modules_check.py` |
| **Documentation** | Header metadata, docstrings, inline comments | `documentation_check.py` |
| **JSON Structure** | Memory file format (id.json, local.json, observations.json) | `json_structure_check.py` |
| **Testing** | Test coverage, test file structure | `testing_check.py` |
| **Error Handling** | Comprehensive try-catch, logging on errors | `error_handling_check.py` |
| **Encapsulation** | No cross-branch handler imports, package boundary enforcement | `encapsulation_check.py` |
| **Type Check** | Pyright type errors, undefined variables, import errors | `diagnostics_check.py` |

### Scoring System

Each standard produces a score (0-100%):
- **100%** - Full compliance, all checks passed
- **75-99%** - Minor issues, mostly compliant
- **0-74%** - Significant violations, needs attention

The **branch average** is the mean of all 12 standard scores.

The **system average** is the mean of all branch averages.

### Special Checks

Some standards have multi-file scope:

**CLI Violations** - Checked across ALL files:
```
Looks for dangerous patterns:
- os.system()
- subprocess with shell=True
- Forbidden commands (rm -rf, sudo, chmod 777)
```

**Modules Violations** - Business logic detection in `apps/modules/`:
```
Modules should orchestrate, not implement.
Flags: Direct string manipulation, database queries, file I/O
```

**Encapsulation Violations** - Cross-branch imports:
```
Handlers are branch-private. Never:
- from drone.apps.handlers import X
- from cortex.apps.handlers.config import Y

Always use modules as public API.
```

**Type Errors** - Pyright diagnostics on entire branch:
```
Runs pyright on branch path, reports:
- Undefined variables
- Type mismatches
- Missing imports
- Argument errors
```

## The Compliance Dashboard

### Branch Summary Output

```
CORTEX (23 files checked)
  Imports         100% ✅  Architecture     85% ⚠️
  Naming          100% ✅  Cli             100% ✅
  Handlers        100% ✅  Modules          75% ⚠️
  Documentation    90% ✅  Json_structure  100% ✅
  Testing          50% ❌  Error_handling   90% ✅
  Encapsulation   100% ✅  Type_check        0% ❌
  Overall:         87% ⚠️

  └─ Architecture violations (3 missing):
     Missing directories (1):
       ✗ apps/handlers/
     Missing files (2):
       ✗ apps/handlers/__init__.py
       ✗ README.md

  ✓ All 23 files pass CLI standard

  TYPE ERRORS (45 errors):
    ✗ /home/aipass/aipass_core/cortex/apps/cortex.py (12 errors)
      L34: Cannot assign member "foo" for type "Bar"
      L56: Argument of type "str" cannot be assigned to parameter...
```

### System Summary Output

```
─────────────────────────────────────────────────────────────────
SYSTEM SUMMARY:
  Total branches:        18
  Average compliance:    83%
  Branches ≥90%:         8 ✅
  Branches 75-89%:       6 ⚠️
  Branches <75%:         4 ❌
  Type errors:           342 (12 branches)

STANDARD AVERAGES:
  Architecture     78% ⚠️   Cli             95% ✅
  Documentation    72% ⚠️   Encapsulation   88% ⚠️
  Error_handling   85% ⚠️   Handlers        92% ✅
  Imports          96% ✅   Json_structure  65% ❌
  Modules          81% ⚠️   Naming          94% ✅
  Testing          45% ❌   Type_check      33% ❌

TOP IMPROVEMENT AREAS:
  1. Type_check      (avg: 33%, 12 branches <75%)
  2. Testing         (avg: 45%, 15 branches <75%)
  3. Json_structure  (avg: 65%, 8 branches <75%)
─────────────────────────────────────────────────────────────────
```

## Auditing Specific Branches vs @all

### Single Branch Mode

When you specify a branch:
```bash
drone @seed audit cortex
```

**Behavior:**
- Scans only the specified branch
- Shows detailed violations for all standards
- Lists ALL failing files (no truncation)
- No system summary (not relevant for single branch)
- Useful for focused debugging

**Use cases:**
- After making changes to a branch
- Investigating specific failures
- Pre-commit compliance check
- Detailed violation analysis

### System-wide Mode

When you run without arguments:
```bash
drone @seed audit
```

**Behavior:**
- Scans all 18 branches from registry
- Shows per-branch summaries
- Displays system-wide averages
- Identifies top improvement areas
- Takes 2-3 minutes for full system scan

**Use cases:**
- Weekly compliance review
- Architecture health check
- Identifying system-wide patterns
- Prioritizing cleanup work

## Score Calculation Details

### Individual Standard Score

Each checker returns:
```python
{
    'passed': bool,          # Overall pass/fail
    'score': int,            # 0-100
    'checks': [              # Individual checks
        {
            'name': str,
            'passed': bool,
            'message': str   # Failure reason
        }
    ]
}
```

Score calculation varies by standard:
- **Binary standards** (CLI, Imports): 100% if all checks pass, 0% otherwise
- **Weighted standards** (Architecture): Points for each check, averaged
- **Type check**: 100% if 0 errors, 0% if any errors exist

### Branch Average

```python
branch_average = sum(standard_scores) / 12
```

All 12 standards weighted equally. This means:
- Type errors have same weight as naming issues
- Documentation gaps count as much as architecture violations
- Testing deficits impact overall score

### System Average

```python
system_average = sum(branch_averages) / num_branches
```

Each branch weighted equally, regardless of size or complexity.

### Bypass System

Branches can bypass specific checks using `BYPASS.json`:
```json
{
  "standards_bypass": {
    "architecture": {
      "reason": "Legacy branch, no apps/ structure",
      "approved_by": "Patrick",
      "date": "2025-11-20"
    }
  }
}
```

Bypassed standards automatically score 100% without checking.

## Integration Points

### Prax Logging

All audit operations log to Prax:
```python
logger.info("Prax logger connected to standards_audit")
```

Events logged:
- `standards_audit_started` - Audit initiated
- `standards_audit_completed` - Results available
- Individual checker errors

### JSON Tracking (SEED.local.json)

Operations recorded:
```python
json_handler.log_operation(
    "standards_audit_completed",
    {
        "branches_audited": 18,
        "average_compliance": 83
    }
)
```

### Drone Integration

The audit module integrates with Drone's routing:
- `@seed audit` - Routes to standards_audit.py
- Branch name normalization via `normalize_branch_arg()`
- Registry discovery via `get_all_branches()`

## Files

| File | Purpose |
|------|---------|
| `/home/aipass/seed/apps/modules/standards_audit.py` | Main audit orchestration module |
| `/home/aipass/seed/apps/modules/diagnostics_audit.py` | Type error diagnostics (pyright) |
| `/home/aipass/seed/apps/handlers/standards/*.py` | Individual standard checkers (12 total) |
| `/home/aipass/seed/apps/handlers/config/ignore_handler.py` | File exclusion patterns |
| `/home/aipass/BRANCH_REGISTRY.json` | Branch discovery source of truth |
| `/home/aipass/seed/.seed/bypass.json` | Per-branch bypass rules |

## Related

- [Standards System](./standards_system.md) - Quick check mode
- [README](../README.md) - Seed branch overview
- [Architecture Standard](/home/aipass/standards/CODE_STANDARDS/architecture.md) - 3-layer pattern
- [Handlers Standard](/home/aipass/standards/CODE_STANDARDS/handlers.md) - Handler implementation rules

---

*Part of SEED branch documentation*
