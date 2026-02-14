# Automated Standards Checkers

**Branch:** SEED
**Created:** 2025-11-29
**Updated:** 2025-11-29

---

## Overview

The Seed branch automated checking system validates Python modules against AIPass code standards. It provides a unified CLI interface (`drone @seed checklist`) that runs 14 specialized checkers, each scoring 0-100 based on compliance with specific standard categories.

This system is the **enforcement layer** for AIPass standards - it turns documented best practices into measurable, automated validation.

## Key Concepts

- **Orchestrator Pattern**: `standards_checklist.py` orchestrates, individual `*_check.py` handlers implement
- **Uniform Interface**: All checkers use `check_module()` pattern returning standardized results
- **Scoring System**: Each checker scores 0-100, overall score averages all checkers
- **Bypass System**: `.seed/bypass.json` allows per-file, per-standard, per-line exemptions
- **Branch Detection**: Auto-detects branch from file path using `BRANCH_REGISTRY.json`
- **Pass Threshold**: 75% score required to pass each standard

## Architecture

### Orchestrator Module

**File:** `/home/aipass/seed/apps/modules/standards_checklist.py`

The main orchestrator that:
1. Accepts a file path to check
2. Detects which branch owns the file (via `BRANCH_REGISTRY.json`)
3. Loads bypass rules from `.seed/bypass.json` in branch root
4. Calls each checker's `check_module()` function sequentially
5. Displays formatted results with scores and pass/fail status
6. Calculates overall compliance percentage (average of all checkers)

### Individual Checkers

**Location:** `/home/aipass/seed/apps/handlers/standards/*_check.py`

Each checker is an independent handler that:
- Implements `check_module(module_path, bypass_rules) -> Dict` function
- Returns standardized result structure (see below)
- Performs focused validation on one standard category
- Respects bypass rules for specific violations
- Never depends on other checkers (complete independence)

## The check_module() Pattern

Every checker implements this exact pattern:

```python
def check_module(module_path: str, bypass_rules: list | None = None) -> Dict:
    """
    Check if module follows [STANDARD NAME] standards

    Args:
        module_path: Path to Python module to check
        bypass_rules: Optional list of bypass rules to skip violations

    Returns:
        dict: {
            'passed': bool,           # Overall pass/fail (>= 75% = pass)
            'checks': [               # Individual check results
                {
                    'name': str,      # Check name
                    'passed': bool,   # Pass/fail for this check
                    'message': str,   # Details (line numbers, etc.)
                }
            ],
            'score': int,             # 0-100 percentage score
            'standard': str           # Standard name (e.g., 'IMPORTS')
        }
    """
```

**Scoring Logic:**
- Each checker runs multiple individual checks
- Score = (passed_checks / total_checks) × 100
- Overall pass if score >= 75%
- Each check is weighted equally

## The 14 Checkers

### 1. imports_check.py - Import Standards

**What it validates:**
- AIPASS_ROOT = Path.home() / "aipass_core" pattern
- sys.path.insert(0, str(AIPASS_ROOT)) setup
- Prax logger import (conditional - not required for small files)
- Handler independence (handlers must not import parent modules)
- Import order (infrastructure → Prax → services → internal)

**Key checks:**
- AIPASS_ROOT pattern present
- sys.path setup correct
- Prax logger imported early (recommended)
- No handler-to-module imports
- Proper import ordering

### 2. architecture_check.py - Architecture Standards

**What it validates:**
- 3-layer pattern compliance (apps/, apps/modules/, apps/handlers/)
- File size guidelines (< 300 perfect, < 500 good, < 700 acceptable, 700+ fail)
- Handler independence (no imports from parent branch modules)
- Domain organization (handlers in business domains, not technical folders)
- Template baseline verification (for entry points - checks entire branch structure)

**Key checks:**
- File in correct architectural layer
- File size within guidelines
- Handlers don't import parent modules
- Domain-based organization (not utils/, helpers/, etc.)
- Branch structure matches Cortex template registry

### 3. naming_check.py - Naming Standards

**What it validates:**
- File naming conventions (snake_case.py)
- Function naming (snake_case, descriptive)
- Class naming (PascalCase)
- Variable naming (snake_case, not single letters except loops)
- Constant naming (UPPER_SNAKE_CASE)

**Key checks:**
- File name is snake_case
- Functions follow snake_case
- Classes follow PascalCase
- Variables are descriptive
- Constants are UPPER_CASE

### 4. cli_check.py - CLI Standards

**What it validates:**
- Handler separation (handlers must NOT have console output)
- CLI service imports (from cli.apps.modules import console, header)
- No bare print() statements (use console.print() instead)
- --help flag support for executable modules
- No duplicate display functions (use CLI service instead)

**Key checks:**
- Handlers have no console.print() or print()
- Modules import CLI services
- No bare print() (except in __main__ blocks)
- --help flag implemented
- No local header/success/error functions (use CLI service)

**Special handling:** Excludes `if __name__ == '__main__':` blocks (test/debug code allowed)

### 5. handlers_check.py - Handler Standards

**What it validates:**
- Handler independence (no cross-handler imports except defaults)
- Auto-detection pattern (if handler accepts module_name parameter)
- No orchestration logic (handlers shouldn't import modules)

**Key checks:**
- No cross-handler imports (except json_handler)
- Auto-detection using inspect.stack() if needed
- No imports from apps/modules/ (except services)

**Allowed imports:**
- `from seed.apps.handlers.json import json_handler` (default handler)
- `from .decorators import catch_errors` (same package)
- Service imports (prax.apps.modules.logger, cli.apps.modules)

**Forbidden imports:**
- Cross-handler imports (from seed.apps.handlers.error import error_handler)
- Module imports (from seed.apps.modules import some_module)

### 6. modules_check.py - Module Standards

**What it validates:**
- handle_command() pattern for drone routing
- Thin orchestration (modules orchestrate, don't implement)
- No business logic in modules (no hardcoded data structures)
- File size compliance (same as architecture)

**Key checks:**
- handle_command() pattern implemented
- Module calls handlers (not implementing logic)
- No hardcoded lists/dicts (belongs in handlers/JSON)
- Clean orchestration layer

### 7. documentation_check.py - Documentation Standards

**What it validates:**
- Shebang line (#!/home/aipass/.venv/bin/python3)
- META DATA HEADER block with required fields
- Module-level docstring
- Function docstrings for public functions
- Inline comments for complex logic

**Key checks:**
- Shebang present and correct
- META header with Name, Date, Version, Category, Changelog
- Module docstring present
- Public functions have docstrings
- Complex sections commented

### 8. json_structure_check.py - JSON Standards

**What it validates:**
- Proper use of json_handler for JSON operations
- No manual JSON file creation
- Template-based JSON structure
- Auto-creation and self-healing patterns

**Key checks:**
- Uses json_handler from seed.apps.handlers.json
- No manual json.dump() for module JSONs
- Follows template patterns
- Implements auto-creation

### 9. testing_check.py - Testing Standards

**What it validates:**
- Presence of test files
- Test coverage for public functions
- pytest usage and patterns
- Test file naming (test_*.py or *_test.py)

**Key checks:**
- Test files exist
- Tests cover main functionality
- Using pytest framework
- Proper test organization

### 10. error_handling_check.py - Error Handling Standards

**What it validates:**
- Try/except blocks for risky operations
- Specific exception catching (not bare except:)
- Prax logger usage for error logging
- Proper error propagation

**Key checks:**
- Try/except around file I/O, network, JSON
- Specific exception types caught
- Errors logged via Prax
- Graceful failure handling

### 11. encapsulation_check.py - Handler Encapsulation

**What it validates:**
- Handlers don't import cross-branch/cross-package
- Proper service boundaries
- No circular dependencies
- Clean separation between branches

**Key checks:**
- No cross-branch handler imports
- Service imports only (prax, cli)
- No circular dependencies detected
- Proper encapsulation boundaries

### 12. trigger_check.py - Trigger Event Standards

**What it validates:**
- Event-worthy functions have trigger.fire() calls
- Lifecycle, messaging, state change patterns detected
- Inline filesystem operations (.unlink(), .rename()) flagged
- 10 pattern categories for comprehensive detection

**Key checks:**
- FileSystemEventHandler methods (on_created, on_deleted, etc.)
- Lifecycle functions (create_*, close_*, delete_*, restore_*)
- Central functions (update_central, aggregate_central)
- Repair/recovery functions (auto_close_*, recover_*, heal_*)
- Inline .unlink() and .rename() operations

### 13. diagnostics_check.py - Type Error Diagnostics

**What it validates:**
- Type errors via pyright (same engine as Pylance)
- Undefined variables
- Missing attributes
- Import errors

**Key checks:**
- Function return type mismatches
- Argument type mismatches
- Using variables before assignment
- Missing module imports

### 14. log_level_check.py - Log Level Hygiene

**What it validates:**
- ERROR level reserved for real system failures only
- User input errors use WARNING not ERROR
- Command routing failures use WARNING not ERROR

**Key checks:**
- `logger.error()` not used for user input patterns (unknown command, invalid argument, etc.)
- Command routing failures (`route_command`, `handle_command`) logged as WARNING
- AST-aware docstring tracking to avoid false positives from code examples

## Usage

### Via Drone (Recommended)

```bash
# Check a seed module
drone @seed checklist /home/aipass/seed/apps/modules/standards_checklist.py

# Check a module from another branch
drone @seed checklist /home/aipass/aipass_core/api/apps/api.py

# Check a handler
drone @seed checklist /home/aipass/seed/apps/handlers/standards/imports_check.py
```

### Standalone Execution

```bash
# Direct execution
python3 /home/aipass/seed/apps/modules/standards_checklist.py /path/to/file.py

# Show help
python3 /home/aipass/seed/apps/modules/standards_checklist.py --help

# Show json_handler introspection
python3 /home/aipass/seed/apps/modules/standards_checklist.py --introspect
```

## Scoring System

### Individual Checker Scoring

Each checker runs multiple checks (typically 3-6) and calculates:

```
score = (passed_checks / total_checks) × 100
```

**Example:**
- Imports checker runs 5 checks
- 4 pass, 1 fails
- Score: (4/5) × 100 = 80/100

**Pass threshold:** 75% or higher = PASS

### Overall Score

The orchestrator averages all checker scores:

```
overall_score = sum(all_checker_scores) / 14
```

**Example output:**
```
IMPORTS STANDARD:
  ✓ AIPASS_ROOT pattern: Found on line 34
  ✓ sys.path setup: Found on line 35
  ✓ Prax logger import: Found on line 43
  ✗ Import order: Prax logger should be before internal imports
  Score: 75/100 - PASS

ARCHITECTURE STANDARD:
  ✓ 3-layer pattern: Module layer (apps/modules/)
  ✓ File size: 751 lines (acceptable but getting heavy)
  Score: 100/100 - PASS

...

OVERALL: 11/11 standards checked - 87% average compliance
```

## Bypass System

### Location

Each branch has a `.seed/bypass.json` file in its root:
```
/home/aipass/seed/.seed/bypass.json
/home/aipass/aipass_core/api/.seed/bypass.json
```

### Structure

```json
{
  "metadata": {
    "version": "1.0.0",
    "created": "2025-11-12T10:00:00",
    "description": "Standards bypass configuration for this branch"
  },
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

### Fields

- **file**: Relative path from branch root (required)
- **standard**: Standard name - cli, imports, naming, etc. (required)
- **lines**: Optional - specific line numbers to bypass
- **pattern**: Optional - pattern to match (e.g., 'if __name__')
- **reason**: Required - why this bypass exists

### Bypass Matching

The system checks bypasses in this order:
1. Does the file path match?
2. Does the standard name match?
3. If lines specified: does the line number match?
4. If no lines specified: bypass entire standard for this file

### Auto-Creation

The orchestrator automatically creates `.seed/bypass.json` if missing when checking a file from a branch.

## Branch Detection

The system auto-detects which branch owns a file using `/home/aipass/BRANCH_REGISTRY.json`:

```python
# Example: checking /home/aipass/aipass_core/api/apps/api.py
# Detects: branch = 'api', path = '/home/aipass/aipass_core/api'
# Loads: /home/aipass/aipass_core/api/.seed/bypass.json
```

This enables:
- Branch-specific bypass rules
- Correct path resolution
- Per-branch configuration

## Output Format

### Terminal Output

Uses Rich console formatting:
- ✓ Green checkmarks for passed checks
- ✗ Red X marks for failed checks
- Color-coded scores (green PASS / red FAIL)
- Line numbers for violations
- Summary statistics

### Machine-Readable Output

Each checker returns structured JSON:
```python
{
    'passed': True,
    'checks': [
        {'name': 'AIPASS_ROOT pattern', 'passed': True, 'message': 'Found on line 34'},
        {'name': 'sys.path setup', 'passed': True, 'message': 'Found on line 35'}
    ],
    'score': 100,
    'standard': 'IMPORTS'
}
```

## Implementation Details

### Docstring Filtering

Checkers filter out docstrings before analysis to prevent false positives from code examples in documentation:

```python
def filter_docstrings(lines: List[str]) -> List[str]:
    """Remove docstrings to prevent false positives from import examples"""
    # Handles both single-line and multi-line docstrings
    # Prevents import examples in docstrings from being detected as actual imports
```

### Import Section Detection

Checkers only analyze actual import sections (stops at first `def` or `class`):

```python
def find_import_section_end(lines: List[str]) -> int:
    """Find where imports end (first def/class)"""
    # Prevents false positives from matching patterns in code/comments
```

### __main__ Block Exclusion

CLI checker excludes `if __name__ == '__main__':` blocks from console output checks (test/debug code allowed):

```python
# Tracks indentation to detect entering/exiting __main__ block
# Skips checking lines inside these blocks
```

## Related Files

| File | Purpose |
|------|---------|
| `/home/aipass/seed/apps/modules/standards_checklist.py` | Main orchestrator module |
| `/home/aipass/seed/apps/handlers/standards/*_check.py` | Individual checker handlers |
| `/home/aipass/seed/.seed/bypass.json` | Bypass rules for Seed branch |
| `/home/aipass/BRANCH_REGISTRY.json` | Branch detection registry |
| `/home/aipass/seed/docs/standards/` | Standard documentation |

## Best Practices

### When to Use Bypasses

Bypass rules should be **rare** and **justified**. Use only when:
- Circular dependencies prevent compliance
- Legacy code requires gradual migration
- Framework limitations force violations
- Test/debug code needs special handling

**Always include a clear reason in bypass rules.**

### Gradual Adoption

For existing codebases:
1. Run checklist to establish baseline
2. Fix easy violations first
3. Create bypass rules for complex issues
4. Gradually remove bypasses as code improves

### CI/CD Integration

Can be integrated into pre-commit hooks or CI pipelines:
```bash
# Example: Check all modified Python files
git diff --name-only --diff-filter=AM | grep '\.py$' | while read file; do
    drone @seed checklist "$file"
done
```

---

*Part of SEED branch documentation - the reference implementation for AIPass standards*
