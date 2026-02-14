# Standards System Architecture

**Branch:** SEED
**Created:** 2025-11-29
**Updated:** 2025-11-29

---

## Overview

The Seed standards system is a comprehensive framework for maintaining code quality across all AIPass branches. It provides queryable standards documentation, automated compliance checking, and a system-wide audit capability. The system consists of 10 core code standards plus 3 special-purpose standards (encapsulation, diagnostics, testing), each implemented through a paired module-handler architecture.

**Key Features:**
- 10 queryable code standards modules
- 12 automated compliance checkers
- 9 content handlers for documentation
- Branch-wide audit system with scoring
- Bypass system for intentional violations
- Integration with Drone for cross-branch queries

---

## The 10 Code Standards

The Seed branch implements 10 core code standards that define how AIPass code should be structured and written:

| # | Standard | Module | Purpose |
|---|----------|--------|---------|
| 1 | **Architecture** | `architecture_standard.py` | 3-layer pattern (entry/modules/handlers), handler independence |
| 2 | **CLI** | `cli_standard.py` | Dual approach (interactive + arguments), service provider pattern |
| 3 | **Documentation** | `documentation_standard.py` | META headers, docstrings, changelog maintenance |
| 4 | **Error Handling** | `error_handling_standard.py` | Fail honestly, CLI service integration, OperationResult pattern |
| 5 | **Handlers** | `handlers_standard.py` | File size limits, domain organization, independence rules |
| 6 | **Imports** | `imports_standard.py` | Import order, AIPASS_ROOT pattern, Path.home() usage |
| 7 | **JSON Structure** | `json_structure_standard.py` | Three-JSON pattern, log rotation, auto-creation |
| 8 | **Modules** | `modules_standard.py` | handle_command() pattern, orchestration vs implementation |
| 9 | **Naming** | `naming_standard.py` | Path = context, name = action, snake_case conventions |
| 10 | **Testing** | `testing_standard.py` | Current approach, debugging patterns, test organization |

### Special-Purpose Standards

In addition to the 10 core standards, the system includes:

- **Encapsulation** (`encapsulation_check.py`) - Validates handler independence, prevents cross-branch imports
- **Diagnostics** (`diagnostics_check.py`) - System health checks, pattern detection
- **Testing** (`testing_check.py`) - Automated test validation (beyond the testing standard documentation)

---

## System Architecture

### The Module-Handler Pattern

Each standard is implemented through a paired architecture:

**Module** (`apps/modules/*_standard.py`)
- Orchestrates the workflow
- Handles CLI routing via `handle_command()`
- Imports and calls content handlers
- Provides help text and introspection
- Logs operations via `json_handler`

**Content Handler** (`apps/handlers/standards/*_content.py`)
- Implements the documentation content
- Returns formatted Rich markup strings
- Pure function - no side effects
- Contains the actual standard text

**Check Handler** (`apps/handlers/standards/*_check.py`)
- Implements compliance checking logic
- Returns structured validation results
- Supports bypass rules via `.seed/bypass.json`
- Scores compliance on 0-100 scale

### Example: Imports Standard

```
imports_standard.py (Module)
├── Orchestrates workflow
├── Calls get_imports_standards() from handler
└── Displays formatted output

imports_content.py (Content Handler)
├── Returns Rich-formatted documentation
└── Shows import order, patterns, examples

imports_check.py (Check Handler)
├── Validates AIPASS_ROOT pattern
├── Checks sys.path setup
├── Verifies Prax logger import
├── Validates import order
└── Returns score and violations
```

---

## How Each Standard Works

### 1. Architecture Standard

**What it checks:**
- 3-layer structure (entry point → modules → handlers)
- Handler independence (handlers cannot import parent modules)
- Proper separation of concerns
- Entry point auto-discovery pattern

**Checker:** `architecture_check.py`
- Validates directory structure
- Checks for proper layer separation
- Ensures handlers don't import from parent modules

### 2. CLI Standard

**What it checks:**
- Dual approach implementation (interactive + arguments)
- Proper use of argparse
- Rich formatting integration
- Service provider pattern adoption

**Checker:** `cli_check.py`
- Validates argparse usage
- Checks for CLI service imports
- Verifies help text availability

### 3. Documentation Standard

**What it checks:**
- META header presence and format
- Shebang line (`#!/home/aipass/.venv/bin/python3`)
- Module-level docstrings
- Changelog maintenance (max 5 entries)

**Checker:** `documentation_check.py`
- Validates META header structure
- Checks required fields (Name, Date, Version, Category)
- Verifies docstring presence

### 4. Error Handling Standard

**What it checks:**
- CLI error service usage
- OperationResult pattern adoption
- Proper exception handling
- Fail honestly principle

**Checker:** `error_handling_check.py`
- Validates error handling patterns
- Checks for CLI service integration
- Ensures proper logging

### 5. Handlers Standard

**What it checks:**
- File size limits (handlers < 600 lines)
- Domain-specific organization
- Independence from parent modules
- Service imports only

**Checker:** `handlers_check.py`
- Validates file size
- Checks independence rules
- Verifies proper imports

### 6. Imports Standard

**What it checks:**
- AIPASS_ROOT pattern (`Path.home() / "aipass_core"`)
- sys.path setup (`sys.path.insert(0, str(AIPASS_ROOT))`)
- Prax logger import (nearly always required)
- Import order: Infrastructure → Stdlib → Prax → Services → Internal

**Checker:** `imports_check.py`
- Validates AIPASS_ROOT presence
- Checks sys.path configuration
- Verifies import ordering
- Ensures Path.home() usage (no hardcoded paths)

### 7. JSON Structure Standard

**What it checks:**
- Three-JSON pattern (config, data, log)
- Auto-creation on first use
- Log rotation (FIFO)
- Template-based generation

**Checker:** `json_structure_check.py`
- Validates JSON structure
- Checks template usage
- Verifies auto-creation logic

### 8. Modules Standard

**What it checks:**
- handle_command() implementation
- Return True/False pattern
- Orchestration vs implementation separation
- Module auto-discovery support

**Checker:** `modules_check.py`
- Validates handle_command() presence
- Checks return pattern
- Ensures proper module structure

### 9. Naming Standard

**What it checks:**
- snake_case for files and functions
- Path = context principle
- Action-based naming
- Consistency across codebase

**Checker:** `naming_check.py`
- Validates naming conventions
- Checks file naming patterns
- Verifies function naming

### 10. Testing Standard

**What it checks:**
- Test file organization
- Current testing approach
- Debugging patterns
- Test coverage expectations

**Checker:** `testing_check.py`
- Validates test structure
- Checks test patterns
- Ensures proper organization

---

## Content Handlers vs Check Handlers

The system distinguishes between two types of handlers:

### Content Handlers (`*_content.py`)

**Purpose:** Provide formatted documentation for human consumption

**Characteristics:**
- Pure functions returning strings
- Rich markup for beautiful CLI output
- No side effects or state changes
- Called by standard modules for display

**Example:**
```python
def get_imports_standards() -> str:
    """Return formatted import standards content with Rich markup"""
    lines = [
        "[bold cyan]STANDARD IMPORT ORDER:[/bold cyan]",
        "",
        "[bold]1. Infrastructure[/bold]",
        "   • AIPASS_ROOT = Path.home() / 'aipass_core'",
        # ... more content
    ]
    return "\n".join(lines)
```

**Used by:**
- Standard modules (when displaying documentation)
- Seed entry point (when querying standards)
- Drone (when routing standard queries)

### Check Handlers (`*_check.py`)

**Purpose:** Validate code compliance programmatically

**Characteristics:**
- Implement validation logic
- Return structured results (dict with score, checks, violations)
- Support bypass rules from `.seed/bypass.json`
- Provide 0-100 scoring

**Example:**
```python
def check_module(module_path: str, bypass_rules: list = None) -> Dict:
    """Check if module follows import standards

    Returns:
        {
            'passed': bool,        # Overall pass/fail
            'checks': [...],       # Individual check results
            'score': int,          # 0-100 percentage
            'standard': str        # Standard name
        }
    """
    # Implementation...
```

**Used by:**
- `standards_checklist.py` (individual file checking)
- `standards_audit.py` (branch-wide audits)
- CI/CD pipelines (automated validation)

---

## How Standards Are Queryable

The standards system provides multiple interfaces for accessing standards:

### 1. Seed Architecture Pattern

**Module Auto-Discovery:**
```python
# Entry point discovers all standard modules
modules = discover_modules()
for module in modules:
    if hasattr(module, 'handle_command'):
        if module.handle_command(command, args):
            return  # Module handled it
```

**Command Routing:**
```python
# Each module implements handle_command()
def handle_command(command: str, args: List[str]) -> bool:
    if command != "architecture":
        return False  # Not our command

    print_standard()  # Display content
    return True  # We handled it
```

### 2. Seed CLI

**Direct Execution:**
```bash
# Show all standards
python3 /home/aipass/seed/apps/seed.py

# Query specific standard
python3 /home/aipass/seed/apps/seed.py architecture
python3 /home/aipass/seed/apps/seed.py imports

# Run compliance check
python3 /home/aipass/seed/apps/modules/standards_checklist.py /path/to/file.py
```

### 3. Drone Integration

**Branch-Aware Routing:**
```bash
# From any directory
drone @seed architecture    # Query architecture standard
drone @seed checklist <file> # Run compliance check
drone @seed audit           # System-wide audit
```

Drone resolves `@seed` to `/home/aipass/seed` and routes the command to the appropriate module.

### 4. Programmatic Access

**Import and Use:**
```python
from seed.apps.handlers.standards import imports_content, imports_check

# Get documentation
docs = imports_content.get_imports_standards()
print(docs)

# Run validation
result = imports_check.check_module("/path/to/module.py")
print(f"Score: {result['score']}/100")
```

---

## Relationship Between Modules and Handlers

The module-handler relationship follows the AIPass architecture pattern:

### Modules (Orchestration Layer)

**Responsibilities:**
- Route commands to appropriate handlers
- Manage workflow and state
- Handle user interaction (help text, arguments)
- Log operations via json_handler
- Coordinate multiple handler calls

**Cannot:**
- Implement domain logic directly
- Manipulate data structures
- Perform file operations (use handlers)

### Handlers (Implementation Layer)

**Responsibilities:**
- Implement domain-specific logic
- Perform file operations
- Validate data structures
- Return results to modules

**Cannot:**
- Import parent modules (breaks independence)
- Handle CLI routing
- Manage workflow state
- Call other modules

### The Flow

```
User Command
    ↓
seed.py (Entry Point)
    ↓
Auto-discovers modules
    ↓
Module.handle_command() (Orchestration)
    ↓
Handler.get_content() or Handler.check_module() (Implementation)
    ↓
Returns result to module
    ↓
Module displays/processes result
    ↓
Returns to user
```

---

## The Checklist System

`standards_checklist.py` provides automated compliance checking for individual files.

### Features

**11 Standards Checked:**
- Imports, Architecture, Naming, CLI, Handlers
- Modules, Documentation, JSON Structure, Testing
- Error Handling, Encapsulation

**Bypass System:**
- Per-branch configuration via `.seed/bypass.json`
- Line-specific bypasses
- Pattern matching
- Documented reasons

**Scoring:**
- Each check: Pass/Fail
- Overall score: 0-100%
- Pass threshold: 75%
- Detailed violation reporting

### Usage

```bash
# Check a file
python3 /home/aipass/seed/apps/modules/standards_checklist.py /path/to/file.py

# Via drone
drone @seed checklist /path/to/file.py
```

### Bypass Configuration

Example `.seed/bypass.json`:
```json
{
  "metadata": {
    "version": "1.0.0",
    "created": "2025-11-29",
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

---

## The Audit System

`standards_audit.py` provides branch-wide and system-wide compliance auditing.

### Features

**Branch Discovery:**
- Uses `BRANCH_REGISTRY.json` as source of truth
- Auto-discovers all AIPass branches
- Finds entry points and Python files

**Compliance Scoring:**
- Per-file scores (0-100%)
- Per-standard averages
- Branch overall score
- System-wide metrics

**Reporting:**
- Branch compliance dashboard
- Top violations by standard
- File-level details
- Trend tracking

### Usage

```bash
# Audit entire system
python3 seed.py audit

# Audit specific branch
python3 seed.py audit @drone

# Via drone
drone @seed audit
drone @seed audit @cortex
```

### Output Example

```
SEED BRANCH AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Branch: seed
Files Checked: 42
Average Score: 87%

Standards Breakdown:
✓ IMPORTS:         92%
✓ ARCHITECTURE:    89%
✓ NAMING:          94%
✗ CLI:             68%  (Below threshold)
✓ HANDLERS:        91%

Top Issues:
• CLI standard: 12 violations across 6 files
• Error Handling: 5 violations across 3 files
```

---

## Files

### Modules

| File | Purpose |
|------|---------|
| `apps/modules/architecture_standard.py` | Architecture standard module |
| `apps/modules/cli_standard.py` | CLI standard module |
| `apps/modules/documentation_standard.py` | Documentation standard module |
| `apps/modules/error_handling_standard.py` | Error handling standard module |
| `apps/modules/handlers_standard.py` | Handlers standard module |
| `apps/modules/imports_standard.py` | Imports standard module |
| `apps/modules/json_structure_standard.py` | JSON structure standard module |
| `apps/modules/modules_standard.py` | Modules standard module |
| `apps/modules/naming_standard.py` | Naming standard module |
| `apps/modules/standards_audit.py` | Branch-wide audit system |
| `apps/modules/standards_checklist.py` | Compliance checker + bypass system |
| `apps/modules/standards_verify.py` | Seed sync verification |

### Content Handlers

| File | Purpose |
|------|---------|
| `apps/handlers/standards/architecture_content.py` | Architecture documentation |
| `apps/handlers/standards/cli_content.py` | CLI documentation |
| `apps/handlers/standards/documentation_content.py` | Documentation documentation |
| `apps/handlers/standards/error_handling_content.py` | Error handling documentation |
| `apps/handlers/standards/handlers_content.py` | Handlers documentation |
| `apps/handlers/standards/imports_content.py` | Imports documentation |
| `apps/handlers/standards/json_structure_content.py` | JSON structure documentation |
| `apps/handlers/standards/modules_content.py` | Modules documentation |
| `apps/handlers/standards/naming_content.py` | Naming documentation |

### Check Handlers

| File | Purpose |
|------|---------|
| `apps/handlers/standards/architecture_check.py` | Architecture validation |
| `apps/handlers/standards/cli_check.py` | CLI validation |
| `apps/handlers/standards/diagnostics_check.py` | System diagnostics |
| `apps/handlers/standards/documentation_check.py` | Documentation validation |
| `apps/handlers/standards/encapsulation_check.py` | Handler independence validation |
| `apps/handlers/standards/error_handling_check.py` | Error handling validation |
| `apps/handlers/standards/handlers_check.py` | Handlers validation |
| `apps/handlers/standards/imports_check.py` | Imports validation |
| `apps/handlers/standards/json_structure_check.py` | JSON structure validation |
| `apps/handlers/standards/modules_check.py` | Modules validation |
| `apps/handlers/standards/naming_check.py` | Naming validation |
| `apps/handlers/standards/testing_check.py` | Testing validation |

---

## Usage Examples

### Query a Standard

```bash
# Show imports standard documentation
python3 /home/aipass/seed/apps/seed.py imports

# Via drone from any directory
drone @seed imports
```

### Check File Compliance

```bash
# Check a single file
python3 /home/aipass/seed/apps/modules/standards_checklist.py /home/aipass/seed/apps/seed.py

# Output shows:
# - 11 standards checked
# - Pass/fail for each
# - Score per standard
# - Overall compliance percentage
```

### Run Branch Audit

```bash
# Audit seed branch
python3 /home/aipass/seed/apps/seed.py audit

# Audit different branch
python3 /home/aipass/seed/apps/seed.py audit @drone

# Shows:
# - Files checked
# - Average scores
# - Standards breakdown
# - Top violations
```

### Bypass Violations

```bash
# 1. Create .seed/bypass.json in branch root
# 2. Add bypass entry with file, standard, reason
# 3. Re-run checklist - violation bypassed
```

---

## Related

- [README](../README.md) - Seed branch overview
- [/home/aipass/standards/CODE_STANDARDS/](../../standards/CODE_STANDARDS/) - Full standard docs
- [Architecture](../../standards/CODE_STANDARDS/architecture.md) - 3-layer pattern details
- [Handlers](../../standards/CODE_STANDARDS/handlers.md) - Handler independence rules

---

*Part of SEED branch documentation - The AIPass Standards Showroom*
