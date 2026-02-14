# Seed Commands Reference

**Branch:** SEED
**Created:** 2025-11-29
**Updated:** 2025-11-29

---

## Overview

Complete reference for all Seed branch commands. Seed is the AIPass Code Standards Showroom - a reference branch that demonstrates proper architecture patterns and provides queryable code standards.

**Total Commands:** 13 (10 standards + 3 system commands)

---

## Quick Reference Table

| Command | Type | Description |
|---------|------|-------------|
| `architecture` | Standard | 3-layer pattern, handler independence |
| `cli` | Standard | Dual approach (interactive + arguments) |
| `imports` | Standard | Import order, AIPASS_ROOT pattern |
| `handlers` | Standard | File sizes, domain organization |
| `modules` | Standard | handle_command(), orchestration |
| `naming` | Standard | Path = context, name = action |
| `json_structure` | Standard | Three-JSON pattern |
| `error_handling` | Standard | Fail honestly, CLI service |
| `documentation` | Standard | META headers, docstrings |
| `testing` | Standard | Current approach, debugging |
| `checklist` | System | Automated standards checker (12/12 checks) |
| `audit` | System | Branch-wide compliance audit |
| `verify` | System | Seed sync verification |
| `diagnostics` | System | Type error detection (pyright) |

---

## Usage Patterns

### Via Drone (Recommended)
```bash
# Query any standard
drone @seed architecture
drone @seed cli
drone @seed imports

# System commands
drone @seed checklist /path/to/file.py
drone @seed audit
drone @seed audit cortex
drone @seed verify
drone @seed diagnostics
```

### Direct Python Execution
```bash
# From anywhere
python3 /home/aipass/seed/apps/seed.py architecture
python3 /home/aipass/seed/apps/seed.py checklist /path/to/file.py

# From /home/aipass/seed/
python3 apps/seed.py architecture
python3 apps/seed.py audit

# Individual module (introspection)
python3 /home/aipass/seed/apps/modules/architecture_standard.py
```

---

## Standards Commands (10)

### 1. architecture

**Purpose:** Display AIPass architecture patterns and standards

**Usage:**
```bash
drone @seed architecture
python3 seed.py architecture
python3 seed.py architecture --help
```

**What it shows:**
- 3-layer pattern (entry → modules → handlers)
- Template baseline compliance requirements
- Handler independence rules
- File size guidelines
- Two-level introspection pattern
- Anti-patterns to avoid

**Reference:** `/home/aipass/standards/CODE_STANDARDS/architecture.md`

**Module:** `/home/aipass/seed/apps/modules/architecture_standard.py`

---

### 2. cli

**Purpose:** Display CLI design patterns for AIPass branches

**Usage:**
```bash
drone @seed cli
python3 seed.py cli
```

**What it shows:**
- Dual-mode approach (interactive + arguments)
- Help flag compliance (`--help`, `-h`)
- CLI services usage (Rich console formatting)
- Command routing patterns
- Error handling in CLI context

**Reference:** `/home/aipass/standards/CODE_STANDARDS/cli.md`

**Module:** `/home/aipass/seed/apps/modules/cli_standard.py`

---

### 3. imports

**Purpose:** Display import organization and ordering standards

**Usage:**
```bash
drone @seed imports
python3 seed.py imports
```

**What it shows:**
- AIPASS_ROOT pattern (always `Path.home()`)
- Import ordering (infrastructure → prax → handlers → CLI)
- Cross-branch import rules
- Service imports vs business logic imports
- Common anti-patterns

**Reference:** `/home/aipass/standards/CODE_STANDARDS/imports.md`

**Module:** `/home/aipass/seed/apps/modules/imports_standard.py`

---

### 4. handlers

**Purpose:** Display handler organization and design standards

**Usage:**
```bash
drone @seed handlers
python3 seed.py handlers
```

**What it shows:**
- Domain-based organization (not technical)
- File size limits (< 300 perfect, 500 max, 700+ split)
- Handler independence (transportability)
- No module imports from handlers
- Package organization patterns

**Reference:** `/home/aipass/standards/CODE_STANDARDS/handlers.md`

**Module:** `/home/aipass/seed/apps/modules/handlers_standard.py`

---

### 5. modules

**Purpose:** Display module orchestration patterns

**Usage:**
```bash
drone @seed modules
python3 seed.py modules
```

**What it shows:**
- `handle_command()` pattern
- Orchestration vs implementation
- Module discovery system
- Command routing rules
- Business logic location

**Reference:** `/home/aipass/standards/CODE_STANDARDS/modules.md`

**Module:** `/home/aipass/seed/apps/modules/modules_standard.py`

---

### 6. naming

**Purpose:** Display file and function naming conventions

**Usage:**
```bash
drone @seed naming
python3 seed.py naming
```

**What it shows:**
- Path = context, name = action rule
- Snake_case for files
- Function naming conventions
- Directory naming patterns
- Common naming mistakes

**Reference:** `/home/aipass/standards/CODE_STANDARDS/naming.md`

**Module:** `/home/aipass/seed/apps/modules/naming_standard.py`

---

### 7. json_structure

**Purpose:** Display JSON file structure and patterns

**Usage:**
```bash
drone @seed json_structure
python3 seed.py json_structure
```

**What it shows:**
- Three-JSON pattern (config, data, log)
- Auto-creation system
- Template-based generation
- Structure validation
- JSON handler usage

**Reference:** `/home/aipass/standards/CODE_STANDARDS/json_structure.md`

**Module:** `/home/aipass/seed/apps/modules/json_structure_standard.py`

---

### 8. error_handling

**Purpose:** Display error handling patterns and practices

**Usage:**
```bash
drone @seed error_handling
python3 seed.py error_handling
```

**What it shows:**
- Fail honestly principle
- CLI services for error display
- Exception handling patterns
- Logging integration
- Error propagation rules

**Reference:** `/home/aipass/standards/CODE_STANDARDS/error_handling.md`

**Module:** `/home/aipass/seed/apps/modules/error_handling_standard.py`

---

### 9. documentation

**Purpose:** Display documentation standards and META headers

**Usage:**
```bash
drone @seed documentation
python3 seed.py documentation
```

**What it shows:**
- META DATA HEADER format
- Docstring conventions
- CHANGELOG format (max 5 entries)
- Module documentation patterns
- Inline comment guidelines

**Reference:** `/home/aipass/standards/CODE_STANDARDS/documentation.md`

**Module:** `/home/aipass/seed/apps/modules/documentation_standard.py`

---

### 10. testing

**Purpose:** Display testing approaches and debugging standards

**Usage:**
```bash
drone @seed testing
python3 seed.py testing
```

**What it shows:**
- Current testing approach
- Debugging strategies
- Manual testing patterns
- Integration testing
- Future testing direction

**Reference:** `/home/aipass/standards/CODE_STANDARDS/testing.md`

**Module:** `/home/aipass/seed/apps/modules/testing_standard.py`

---

## System Commands (4)

### 1. checklist

**Purpose:** Automated standards compliance checker for individual files

**Checks Performed:** 12/12 standards automatically
- Imports standard
- Architecture standard
- Naming standard
- CLI standard
- Handlers standard
- Modules standard
- Documentation standard
- JSON structure standard
- Testing standard
- Error handling standard
- Encapsulation standard (cross-branch imports)
- Template compliance

**Usage:**
```bash
# Check a single file
drone @seed checklist /path/to/file.py
python3 seed.py checklist /path/to/file.py

# Show introspection
python3 seed.py checklist --introspect

# Help
python3 seed.py checklist --help
```

**Output:**
- Per-standard scores (0-100)
- Specific violations with line numbers
- Overall compliance percentage
- Pass/Fail status for each check

**Bypass System:**
- Each branch can create `.seed/bypass.json`
- Allows legitimate exceptions to be documented
- Per-file or per-line bypass rules
- Requires documented reason

**Example:**
```bash
$ python3 seed.py checklist apps/modules/imports_standard.py

Standards Checklist - /home/aipass/seed/apps/modules/imports_standard.py

Branch: SEED
Bypass config: /home/aipass/seed/.seed/bypass.json

IMPORTS STANDARD:
  ✓ AIPASS_ROOT uses Path.home(): Pass
  ✓ Import order: Pass
  ✓ No relative imports: Pass
  Score: 100/100 - PASS

ARCHITECTURE STANDARD:
  ✓ File size: 146 lines (< 500)
  ✓ Handler imports: Valid
  Score: 100/100 - PASS

...

OVERALL: 11/11 standards checked - 98% average compliance
```

**Module:** `/home/aipass/seed/apps/modules/standards_checklist.py`

**Version:** v0.3.0 (95%+ accuracy, false positives eliminated)

---

### 2. audit

**Purpose:** Branch-wide standards audit - checks all files across all branches

**Scope:**
- Scans all 11+ AIPass branches
- Checks ALL Python files in each branch (not just entry points)
- Full compliance dashboard
- System-wide health metrics

**Usage:**
```bash
# Full system audit (all branches, all files)
drone @seed audit
python3 seed.py audit

# Audit specific branch
drone @seed audit cortex
python3 seed.py audit flow

# Help
python3 seed.py audit --help
```

**What it checks:**
- All 11 standards per file
- CLI violations across all files
- Business logic in modules (violations)
- Handler encapsulation (cross-branch imports)
- Type errors (pyright diagnostics)

**Output:**
```
SEED (42 files checked)
  Imports         95% ✅   Architecture    98% ✅
  Naming          92% ✅   Cli             100% ✅
  Handlers        88% ⚠️   Modules         100% ✅
  Documentation   85% ⚠️   Json_structure  100% ✅
  Testing         75% ⚠️   Error_handling  90% ✅
  Encapsulation   100% ✅  Type_check      100% ✅
  Overall:        93% ✅

  ✓ All 42 files pass CLI standard
  ✓ No type errors

──────────────────────────────────────────────────
SYSTEM SUMMARY:
  Total branches:        11
  Average compliance:    87%
  Branches ≥90%:         6 ✅
  Branches 75-89%:       4 ⚠️
  Branches <75%:         1 ❌
  Type errors:           0 ✓

STANDARD AVERAGES:
  Architecture    92% ✅   Cli             85% ⚠️
  Documentation   78% ⚠️   Encapsulation   94% ✅
  ...

TOP IMPROVEMENT AREAS:
  1. Documentation    (avg: 78%, 5 branches <75%)
  2. Testing          (avg: 72%, 6 branches <75%)
  3. CLI              (avg: 85%, 3 branches <75%)
```

**Features:**
- Comprehensive file scanning (ALL .py files)
- Clickable file paths (VS Code integration)
- Per-branch detailed results
- System-wide aggregation
- Top improvement areas identification

**Module:** `/home/aipass/seed/apps/modules/standards_audit.py`

**Version:** v0.4.0 (always checks ALL files - audit = comprehensive)

---

### 3. verify

**Purpose:** Seed internal sync verification - checks for stale patterns and outdated docs

**Checks Performed:**
1. **Stale Patterns** - Searches for deprecated patterns in Seed codebase
2. **File Freshness** - Compares modification dates of key files
3. **Help Consistency** - Verifies help text accuracy

**Usage:**
```bash
# Run verification
drone @seed verify
python3 seed.py verify

# Help
python3 seed.py verify --help
```

**What it detects:**
- Deprecated flags (`--verbose`, `--full`) in code or docs
- Outdated README.md (not updated when code changes)
- Stale SEED.local.json (not updated today)
- Help text mentioning removed features

**Example Output:**
```
SEED SYNC VERIFICATION

Running verification checks...

✓ Stale Patterns
  → Searched for: --verbose, --full

✓ File Freshness
  → SEED.local.json updated: 2025-11-29
  → README.md updated: 2025-11-29

✓ Help Consistency
  → Scanned seed.py for: --verbose, --full

──────────────────────────────────────────────────
SUMMARY: 3/3 checks passed ✓
```

**Module:** `/home/aipass/seed/apps/modules/standards_verify.py`

**Version:** v0.1.0

---

### 4. diagnostics

**Purpose:** System-wide type error detection using pyright

**Scope:**
- Runs pyright on all AIPass branches
- Detects type errors, undefined variables, import errors
- Shows detailed diagnostics with line numbers

**Usage:**
```bash
# Scan all branches
drone @seed diagnostics
python3 seed.py diagnostics

# Scan specific branch
drone @seed diagnostics flow
python3 seed.py diagnostics cortex

# Help
python3 seed.py diagnostics --help
```

**What it checks:**
- Type errors (Pylance/pyright)
- Undefined variables
- Import errors
- Argument type mismatches
- Missing type annotations (if configured)

**Example Output:**
```
AIPASS TYPE ERROR DIAGNOSTICS

Running pyright on all branches (this may take a moment)...
Found 11 branches to scan...

✓ SEED
  Files: 42 analyzed, 0 with errors
  Errors: 0  Warnings: 0

⚠ FLOW
  Files: 28 analyzed, 3 with errors
  Errors: 5  Warnings: 2
  Top files with errors:
    ✗ /home/aipass/aipass_core/flow/apps/modules/create_plan.py (3 errors)
      L45: Argument of type "str | None" cannot be assigned...
      L67: "data" is not defined
      L89: Cannot access member "get" for type "None"

──────────────────────────────────────────────────
SYSTEM DIAGNOSTICS SUMMARY:
  Total branches:        11
  Clean branches:        8 ✓
  Branches with errors:  3 ✗

  Files analyzed:        387
  Files with errors:     12
  Total errors:          28
  Total warnings:        8

BRANCHES BY ERROR COUNT:
  FLOW            5 errors
  API             3 errors
  DRONE           2 errors
```

**Features:**
- Fast parallel scanning
- Clickable file paths with line numbers
- Top error files per branch
- System-wide error summary
- Detailed diagnostics per error

**Module:** `/home/aipass/seed/apps/modules/diagnostics_audit.py`

**Version:** v0.1.0

---

## Command Arguments and Flags

### Help Flags (All Commands)
```bash
--help, -h, help
```
Shows command-specific help and usage information.

**Examples:**
```bash
python3 seed.py architecture --help
python3 seed.py checklist --help
python3 seed.py audit --help
```

### Checklist Arguments
```bash
python3 seed.py checklist <file_path>          # Check specific file
python3 seed.py checklist --introspect         # Show json_handler introspection
```

### Audit Arguments
```bash
python3 seed.py audit                          # Full system audit
python3 seed.py audit <branch_name>            # Specific branch
```

**Branch name resolution:**
- Accepts: `cortex`, `@cortex`, `CORTEX`
- Normalizes to: `CORTEX`

### Diagnostics Arguments
```bash
python3 seed.py diagnostics                    # All branches
python3 seed.py diagnostics <branch_name>      # Specific branch
```

---

## File Locations

### Entry Point
```
/home/aipass/seed/apps/seed.py
```

### Modules (Standards)
```
/home/aipass/seed/apps/modules/
  ├── architecture_standard.py
  ├── cli_standard.py
  ├── imports_standard.py
  ├── handlers_standard.py
  ├── modules_standard.py
  ├── naming_standard.py
  ├── json_structure_standard.py
  ├── error_handling_standard.py
  ├── documentation_standard.py
  └── testing_standard.py
```

### Modules (System)
```
/home/aipass/seed/apps/modules/
  ├── standards_checklist.py
  ├── standards_audit.py
  ├── standards_verify.py
  └── diagnostics_audit.py
```

### Handlers (Standards Content)
```
/home/aipass/seed/apps/handlers/standards/
  ├── architecture_content.py      # Rich-formatted standards text
  ├── cli_content.py
  ├── imports_content.py
  └── ... (other content handlers)
```

### Handlers (Standards Checkers)
```
/home/aipass/seed/apps/handlers/standards/
  ├── imports_check.py             # Validation logic
  ├── architecture_check.py
  ├── naming_check.py
  ├── cli_check.py
  ├── handlers_check.py
  ├── modules_check.py
  ├── documentation_check.py
  ├── json_structure_check.py
  ├── testing_check.py
  ├── error_handling_check.py
  ├── encapsulation_check.py
  └── diagnostics_check.py
```

### Reference Documentation
```
/home/aipass/standards/CODE_STANDARDS/
  ├── architecture.md
  ├── cli.md
  ├── imports.md
  ├── handlers.md
  ├── modules.md
  ├── naming.md
  ├── json_structure.md
  ├── error_handling.md
  ├── documentation.md
  └── testing.md
```

---

## Module Pattern

All Seed standard modules follow this pattern:

### 1. Introspection Mode (no arguments)
```bash
$ python3 architecture_standard.py

Architecture Standards Module

Connected Handlers:
  handlers/standards/
    - architecture_content.py

Run 'python3 architecture_standard.py --help' for usage
```

### 2. Help Mode (`--help`, `-h`, `help`)
```bash
$ python3 architecture_standard.py --help

Architecture Standards Module
Demonstrates AIPass architecture patterns

COMMANDS:
  Commands: architecture, arch, structure, --help

USAGE:
  drone @seed architecture
  python3 architecture_standard.py
  python3 architecture_standard.py --help

REFERENCE:
  /home/aipass/standards/CODE_STANDARDS/architecture.md
```

### 3. Standard Display Mode (via seed.py)
```bash
$ python3 seed.py architecture

╭────────────────────────╮
│ Architecture Standards │
╰────────────────────────╯

[Rich-formatted standard content]
```

---

## Integration Examples

### From Other Branches
```python
# In another branch's module - query Seed standard
import subprocess

result = subprocess.run(
    ["python3", "/home/aipass/seed/apps/seed.py", "imports"],
    capture_output=True,
    text=True
)
print(result.stdout)
```

### Via Drone Routing
```bash
# Drone automatically resolves @seed
drone @seed architecture

# Equivalent to:
cd /home/aipass/seed && python3 apps/seed.py architecture
```

### In Development Workflow
```bash
# 1. Check file before committing
python3 /home/aipass/seed/apps/seed.py checklist apps/modules/my_module.py

# 2. Run branch audit
python3 /home/aipass/seed/apps/seed.py audit flow

# 3. Check for type errors
python3 /home/aipass/seed/apps/seed.py diagnostics flow

# 4. Verify Seed sync
python3 /home/aipass/seed/apps/seed.py verify

# 5. Query specific standard
drone @seed handlers
```

---

## Output Formats

### Standards Commands
- Rich-formatted text
- Condensed reference content (~100 lines)
- Color-coded sections
- Clear hierarchical structure

### Checklist Command
- Per-standard scores (0-100)
- ✓/✗ indicators for pass/fail
- Line numbers for violations
- Overall compliance percentage

### Audit Command
- Branch summaries with icons (✅⚠️❌)
- Score grids (2 columns)
- Violation details with clickable paths
- System-wide aggregation
- Top improvement areas

### Verify Command
- ✓/✗ per check
- Detailed violation locations
- File:line format for patterns
- Summary score

### Diagnostics Command
- Error/warning counts
- Clickable file paths with line numbers
- Top files with errors
- System-wide summary
- Branch ranking by error count

---

## Best Practices

### When to Use Each Command

**Standards (architecture, cli, etc.):**
- Starting new feature
- Unclear on pattern
- Teaching/onboarding
- Reference during coding

**Checklist:**
- Before committing
- After refactoring
- Learning standards
- Individual file validation

**Audit:**
- Branch health check
- System-wide overview
- Before major releases
- Identifying improvement areas

**Verify:**
- After Seed updates
- When docs may be stale
- Pattern migration checks
- Seed maintenance

**Diagnostics:**
- Before deployment
- After major refactors
- Type safety verification
- Static analysis

### Recommended Workflow
```bash
# 1. Query standard when starting work
drone @seed handlers

# 2. Check file during development
python3 seed.py checklist apps/handlers/my_handler.py

# 3. Run branch audit before PR
python3 seed.py audit my_branch

# 4. Check type errors before commit
python3 seed.py diagnostics my_branch

# 5. Verify Seed sync after updates
python3 seed.py verify
```

---

## Common Issues

### Checklist False Positives
**Issue:** Legitimate code flagged as violation
**Solution:** Add bypass rule to `.seed/bypass.json`

**Example:**
```json
{
  "bypass": [
    {
      "file": "apps/modules/logger.py",
      "standard": "cli",
      "lines": [146, 177],
      "pattern": "if __name__ == '__main__'",
      "reason": "Circular dependency - logger cannot import CLI"
    }
  ]
}
```

### Branch Not Found in Audit
**Issue:** Audit doesn't find branch
**Check:** Branch in `BRANCH_REGISTRY.json`
**Solution:** Update registry or use correct branch name

### Pyright Not Found
**Issue:** Diagnostics command fails
**Check:** `pyright` installed in venv
**Solution:** `pip install pyright`

---

## Related Documentation

- [Seed README](../README.md) - Branch overview and purpose
- [Architecture Standard](../../standards/CODE_STANDARDS/architecture.md) - Full architecture docs
- [Template Documentation](../../standards/TEMPLATES/) - Cortex template reference
- [Branch Registry](../../BRANCH_REGISTRY.json) - All branch definitions

---

*Part of SEED branch documentation - The AIPass Code Standards Showroom*
