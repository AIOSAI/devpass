# Seed Architecture - Technical Reference

**Branch:** SEED
**Created:** 2025-11-29
**Updated:** 2025-11-29

---

## Overview

This document provides a comprehensive technical reference for Seed's 3-layer architecture pattern. Seed serves as AIPass's reference implementation ("showroom") - the living example that demonstrates proper branch structure through executable code.

**Key Concept:** Seed is not just documentation about standards - it IS the standard. Every pattern described here is demonstrated in Seed's own codebase.

---

## The 3-Layer Architecture Pattern

Seed demonstrates AIPass's fundamental architectural principle: **separation of routing, orchestration, and implementation**.

### Layer Structure

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: Entry Point (apps/seed.py)                         │
│ Responsibility: Command routing and module discovery         │
│ ────────────────────────────────────────────────────────── │
│ • Auto-discover modules in apps/modules/                     │
│ • Route commands to appropriate module                       │
│ • Handle --help and introspection                           │
│ • Provide drone-compliant CLI interface                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: Modules (apps/modules/*.py)                        │
│ Responsibility: Workflow orchestration                       │
│ ────────────────────────────────────────────────────────── │
│ • Implement handle_command(command, args) → bool            │
│ • Coordinate multi-step workflows                           │
│ • Call handlers to implement business logic                 │
│ • Log operations via json_handler                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: Handlers (apps/handlers/*/)                        │
│ Responsibility: Business logic implementation                │
│ ────────────────────────────────────────────────────────── │
│ • Pure functions with clear inputs/outputs                   │
│ • Domain-organized (by function, not by tech)               │
│ • Independently testable and transportable                  │
│ • CANNOT import from modules layer (one-way dependency)     │
└─────────────────────────────────────────────────────────────┘
```

### Critical Rules

1. **Import direction flows DOWN only:**
   - Entry → Modules ✓
   - Modules → Handlers ✓
   - Handlers → Handlers (same domain) ✓
   - Handlers → Modules ✗ (BLOCKED - breaks transportability)

2. **Handler independence:**
   - Handlers contain ALL business logic
   - Handlers can import other handlers in same domain package
   - Handlers CANNOT import modules (enforced by `handlers/__init__.py` guard)

3. **Domain organization:**
   - Organize by domain: `handlers/json/`, `handlers/standards/`, `handlers/file/`
   - NOT by technical role: ~~`handlers/utils/`~~, ~~`handlers/helpers/`~~

---

## Layer 1: Entry Point (seed.py)

**File:** `/home/aipass/seed/apps/seed.py`
**Lines:** ~429 lines
**Purpose:** Command routing and module discovery

### Key Functions

```python
def discover_modules() -> List[Any]:
    """
    Auto-discover modules in modules/ directory

    Pattern: Any .py file that implements handle_command()
    gets automatically discovered and registered.

    Benefits:
    - Zero maintenance (no manual registration)
    - Self-documenting (modules announce themselves)
    - Fail-safe (missing modules don't break system)
    """
    modules = []

    for file_path in MODULES_DIR.glob("*.py"):
        if file_path.name.startswith("_"):  # Skip __init__.py
            continue

        module_name = f"seed.apps.modules.{file_path.stem}"

        try:
            module = importlib.import_module(module_name)

            # Duck typing: If it has handle_command(), it's a module
            if hasattr(module, 'handle_command'):
                modules.append(module)
                logger.info(f"Discovered module: {module_name}")
        except Exception as e:
            logger.error(f"Failed to load module {module_name}: {e}")

    return modules
```

```python
def route_command(command: str, args: List[str], modules: List[Any]) -> bool:
    """
    Route command to appropriate module

    Pattern: Each module's handle_command() returns True if it handled the command.
    First module to return True wins.

    Returns:
        True if command was handled, False otherwise
    """
    for module in modules:
        try:
            if module.handle_command(command, args):
                return True
        except Exception as e:
            logger.error(f"Module {module.__name__} error: {e}")

    return False
```

### Command Flow

```
User Input
    │
    ▼
┌──────────────────┐
│ python3 seed.py  │  or  drone @seed architecture
│   architecture   │
└──────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ main() parses args                   │
│ - No args? → print_introspection()   │
│ - --help? → print_help()             │
│ - Command? → proceed to routing      │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ discover_modules()                   │
│ Returns list of all module objects   │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ route_command("architecture", [])    │
│ Iterates through modules             │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ architecture_standard.py             │
│ handle_command("architecture", [])   │
│ Returns True (command handled)       │
└──────────────────────────────────────┘
```

### Entry Point Responsibilities

- **Module Discovery:** Scan `apps/modules/` and load all valid modules
- **Command Routing:** Delegate command handling to modules
- **Help System:** Provide drone-compliant `--help` output
- **Introspection:** Show discovered modules when run without args
- **Error Handling:** Catch and log errors, provide user feedback

---

## Layer 2: Modules (Orchestration)

**Location:** `/home/aipass/seed/apps/modules/`
**Pattern:** One module per standard or feature
**File Count:** 14 modules (11 standards + 3 system tools)

### Module Template

Every module follows this structure:

```python
#!/home/aipass/.venv/bin/python3

# META DATA HEADER
# Name: architecture_standard.py - Architecture Standards Module
# Date: 2025-11-12
# Version: 0.1.0
# Category: seed/standards

"""
Architecture Standards Module

Provides condensed architecture standards for AIPass branches.
Run directly or via: drone @seed architecture
"""

import sys
from pathlib import Path
from typing import List

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))  # For seed package imports

# Service imports
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header

# Handler imports (orchestration layer calls implementation layer)
from seed.apps.handlers.json import json_handler
from seed.apps.handlers.standards.architecture_content import get_architecture_standards


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle 'architecture' command

    Pattern: Return True if this module handles the command, False otherwise
    """
    if command != "architecture":
        return False

    # Log module usage
    json_handler.log_operation(
        "standard_displayed",
        {"command": command}
    )

    print_standard()
    return True


def print_standard():
    """Print architecture standards - orchestrates handler call"""
    console.print()
    header("Architecture Standards")
    console.print()
    console.print(get_architecture_standards())  # Handler does the work
    console.print()


if __name__ == "__main__":
    # Standalone execution support
    if len(sys.argv) == 1:
        print_introspection()
        sys.exit(0)

    if sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    print_standard()
```

### Module Responsibilities

1. **Implement handle_command()**: Return True if command handled, False otherwise
2. **Orchestrate workflow**: Coordinate calls to multiple handlers if needed
3. **Log operations**: Track usage via json_handler
4. **Format output**: Use CLI services for display
5. **Standalone support**: Work when run directly (not just via entry point)

### Module Size Guidelines

From `/home/aipass/seed/apps/handlers/standards/modules_content.py`:

```
<150 lines:  Perfect   (single-purpose, focused)
150-250:     Good      (standard complexity)
250-400:     Acceptable (complex workflows)
400+:        Heavy     (consider splitting)
```

### Current Seed Modules

| Module | Lines | Purpose |
|--------|-------|---------|
| architecture_standard.py | 146 | Architecture patterns |
| cli_standard.py | 124 | CLI usage patterns |
| documentation_standard.py | 133 | Documentation requirements |
| error_handling_standard.py | 128 | Error handling patterns |
| handlers_standard.py | 141 | Handler organization |
| imports_standard.py | 137 | Import patterns |
| json_structure_standard.py | 130 | JSON file structure |
| modules_standard.py | 135 | Module patterns |
| naming_standard.py | 129 | Naming conventions |
| standards_audit.py | 670 | System-wide audit tool |
| standards_checklist.py | 582 | Compliance checking |
| standards_verify.py | 245 | Internal consistency checks |

---

## Layer 3: Handlers (Implementation)

**Location:** `/home/aipass/seed/apps/handlers/`
**Organization:** Domain-based packages
**Protection:** Cross-branch imports blocked by `__init__.py` guard

### Handler Organization

```
handlers/
├── __init__.py                    # Import guard (blocks cross-branch access)
├── json/
│   ├── __init__.py
│   └── json_handler.py           # JSON auto-creation system
├── file/
│   ├── __init__.py
│   └── file_handler.py           # Text file reading abstraction
├── standards/
│   ├── __init__.py
│   ├── architecture_content.py   # Architecture standards text
│   ├── architecture_check.py     # Architecture compliance checker
│   ├── cli_content.py            # CLI standards text
│   ├── cli_check.py              # CLI compliance checker
│   └── ... (10 more standard pairs)
├── config/
│   ├── __init__.py
│   └── ignore_handler.py         # File ignore patterns
└── test/
    ├── violation.py               # Test files for checker validation
    ├── string_test.py
    └── order_test.py
```

### Handler Patterns

#### Content Handlers

Content handlers return formatted strings (Rich markup):

```python
def get_architecture_standards() -> str:
    """
    Return formatted architecture standards content

    Returns:
        str: Formatted standards text with Rich styling
    """
    lines = [
        "[bold cyan]CORE PRINCIPLE:[/bold cyan]",
        "  Separate [yellow]routing[/yellow] ≠ [yellow]orchestration[/yellow] ≠ [yellow]implementation[/yellow]",
        "",
        "[bold cyan]THE 3-LAYER PATTERN:[/bold cyan]",
        "  [dim]apps/branch.py[/dim] (Entry) → Auto-discover modules, route commands",
        # ... more content
    ]

    return "\n".join(lines)
```

#### Check Handlers

Check handlers analyze files for standards compliance:

```python
def check_architecture(file_path: str, branch_root: str) -> Dict[str, Any]:
    """
    Check architecture compliance

    Args:
        file_path: Absolute path to file
        branch_root: Absolute path to branch root

    Returns:
        {
            "score": 0-100,
            "violations": [{
                "line": int,
                "severity": "error"|"warning",
                "message": str
            }]
        }
    """
    violations = []

    # Check for handler importing modules
    if "/handlers/" in file_path:
        if "from .modules" in content or "import modules" in content:
            violations.append({
                "line": line_num,
                "severity": "error",
                "message": "Handlers cannot import modules"
            })

    score = 100 - (len(violations) * 10)
    return {"score": max(0, score), "violations": violations}
```

#### Data Handlers

Data handlers provide pure data operations:

```python
# json_handler.py - Auto-creating JSON system

def log_operation(operation: str, data: Dict[str, Any] | None = None,
                  module_name: str | None = None) -> bool:
    """
    Add entry to module log with automatic rotation

    Auto-detects calling module if module_name not provided.
    Creates JSON files if they don't exist.

    Args:
        operation: Operation name to log
        data: Optional data dict
        module_name: Optional module name (auto-detected if not provided)

    Returns:
        True if successful
    """
    if module_name is None:
        module_name = _get_caller_module_name()

    ensure_module_jsons(module_name)  # Auto-create if missing

    log = load_json(module_name, "log")
    entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation
    }

    if data:
        entry["data"] = data

    log.append(entry)

    # Auto-rotate if exceeds max
    if len(log) > max_entries:
        log = log[-max_entries:]

    return save_json(module_name, "log", log)
```

### Handler Size Guidelines

From `/home/aipass/seed/apps/handlers/standards/handlers_content.py`:

```
<300 lines:  Perfect   (focused, single-domain)
300-500:     Good      (standard complexity)
500-700:     Heavy     (refactor recommended)
700+:        Split it  (multiple concerns)
```

### Handler Independence: The Import Guard

**File:** `/home/aipass/seed/apps/handlers/__init__.py`

This file enforces handler encapsulation by blocking cross-branch handler imports:

```python
def _guard_branch_access():
    """
    Block cross-branch handler imports.

    Only code from within the 'seed' branch can import these handlers.
    External branches must use seed.apps.modules instead.
    """
    caller_file, import_line = _find_real_caller()

    # Check if caller is from our branch
    if "/seed/" in caller_file:
        return  # Same branch, allowed

    # External caller - block access
    caller_branch = _extract_branch_name(caller_file)

    raise ImportError(
        f"\n{'='*60}\n"
        f"ACCESS DENIED: Cross-branch handler import blocked\n"
        f"{'='*60}\n"
        f"  Caller branch: {caller_branch}\n"
        f"  Blocked:       {blocked_import}\n"
        f"\n"
        f"  Handlers are internal to their branch.\n"
        f"  Use the module API instead:\n"
        f"    from seed.apps.modules.<module> import <function>\n"
    )

# Run guard at import time
_guard_branch_access()
```

**Why this matters:**
- Handlers are implementation details (private to the branch)
- Modules are the public API (stable interface for external use)
- This enforces proper architectural boundaries

---

## Module Discovery Mechanism

Seed uses automatic module discovery instead of manual registration. This provides:

- **Zero maintenance:** Add a new module file → automatically discovered
- **Self-documenting:** `python3 seed.py` shows all available modules
- **Fail-safe:** Missing/broken modules don't crash the system

### Discovery Algorithm

```python
MODULES_DIR = Path(__file__).parent / "modules"

def discover_modules() -> List[Any]:
    """Auto-discover modules in modules/ directory"""
    modules = []

    if not MODULES_DIR.exists():
        return modules

    # Scan for .py files
    for file_path in MODULES_DIR.glob("*.py"):
        # Skip private files
        if file_path.name.startswith("_"):
            continue

        module_name = f"seed.apps.modules.{file_path.stem}"

        try:
            # Dynamic import
            module = importlib.import_module(module_name)

            # Duck typing: If it has handle_command(), it's a module
            if hasattr(module, 'handle_command'):
                modules.append(module)
                logger.info(f"Discovered module: {module_name}")
        except Exception as e:
            logger.error(f"Failed to load module {module_name}: {e}")

    return modules
```

### Discovery Contract

For a module to be discovered, it MUST:

1. Be a `.py` file in `apps/modules/`
2. NOT start with `_` (e.g., `__init__.py` is skipped)
3. Implement `handle_command(command: str, args: List[str]) -> bool`

---

## Command Routing Flow

### Full Request Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INPUT                                                │
│    $ drone @seed architecture                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. DRONE ROUTING                                             │
│    - Resolves @seed to /home/aipass/seed/apps/seed.py       │
│    - Executes: python3 seed.py architecture                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. ENTRY POINT (seed.py)                                     │
│    main()                                                    │
│    - Parse args: command="architecture", args=[]            │
│    - discover_modules() → [arch_mod, cli_mod, ...]          │
│    - route_command("architecture", [], modules)             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. MODULE ROUTING                                            │
│    route_command() iterates through modules:                │
│    - architecture_standard.handle_command("architecture")    │
│      → Returns True (command matched)                        │
│    - Stop iteration (command handled)                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. MODULE ORCHESTRATION (architecture_standard.py)          │
│    handle_command("architecture", [])                        │
│    - json_handler.log_operation("standard_displayed")        │
│    - print_standard()                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. HANDLER EXECUTION                                         │
│    print_standard()                                          │
│    - console.print()                                         │
│    - header("Architecture Standards")                        │
│    - get_architecture_standards() → formatted text          │
│    - console.print(formatted_text)                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. HANDLER IMPLEMENTATION (architecture_content.py)         │
│    get_architecture_standards()                              │
│    - Build lines array with Rich markup                      │
│    - Return "\n".join(lines)                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. OUTPUT TO USER                                            │
│    Rich-formatted text displayed in terminal                 │
└─────────────────────────────────────────────────────────────┘
```

### Error Handling Flow

```
Module Error → logger.error() → Continue to next module → Return False
                                                              │
                                                              ▼
                                    No module handled? → Print "Unknown command"
```

---

## Two-Level Introspection Pattern

Seed demonstrates a two-level introspection system for self-documentation:

### Level 1: Main Entry (shows modules)

```bash
$ python3 seed.py
```

Output:
```
Seed - System Education Evolution Development

AIPass Code Standards Showroom

Discovered Modules: 14

  • architecture_standard
  • cli_standard
  • documentation_standard
  • error_handling_standard
  • handlers_standard
  • imports_standard
  • json_structure_standard
  • modules_standard
  • naming_standard
  • standards_audit
  • standards_checklist
  • standards_verify

Run 'python3 seed.py --help' for usage information
```

### Level 2: Individual Module (shows handlers)

```bash
$ python3 architecture_standard.py
```

Output:
```
Architecture Standards Module

Connected Handlers:

  handlers/standards/
    - architecture_content.py

Run 'python3 architecture_standard.py --help' for usage
```

### Why This Matters

**Manual navigation cost:**
- 5-10 minutes to explore file structure
- Context switching burn
- Error-prone (miss files, wrong assumptions)

**Auto-discovery benefit:**
- 5 seconds to see structure
- Zero maintenance (no hardcoded lists)
- Always accurate (reflects actual code)

---

## Why Seed is the "Showroom"

### Reference Implementation Philosophy

Seed is not documentation ABOUT standards - it IS the standard. Every pattern is demonstrated through working code:

1. **Architecture:** Seed's own structure follows the 3-layer pattern
2. **Imports:** Every Seed file demonstrates proper import order
3. **CLI:** All Seed output uses CLI services (console, header)
4. **Handlers:** Seed's handlers are domain-organized and independent
5. **Modules:** Seed modules implement handle_command() pattern
6. **Naming:** All Seed files follow naming conventions
7. **Documentation:** Every Seed file has proper META headers
8. **Error Handling:** Seed uses proper try/except patterns
9. **JSON Structure:** Seed uses json_handler for all JSON operations

### Learning by Example

When a branch asks "How should I structure this?", they:

1. Run `drone @seed <standard>` to read the standard
2. Look at Seed's own code to see it implemented
3. Copy the pattern (because Seed IS the pattern)

**Example:**

```bash
# Learn about handler organization
$ drone @seed handlers

# See it implemented
$ cat /home/aipass/seed/apps/handlers/json/json_handler.py
```

### Compliance Target: 100%

Seed MUST maintain 100% standards compliance because:

- **Credibility:** Can't teach standards you don't follow
- **Trust:** Branches copy Seed's patterns blindly
- **Testing:** Seed validates that standards are achievable

Current Seed compliance: 99% (working toward 100%)

---

## Key Design Patterns

### Pattern 1: Handle Command Contract

Every module implements this interface:

```python
def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle command if this module owns it

    Args:
        command: Primary command name (e.g., "architecture")
        args: Additional arguments

    Returns:
        True if command handled, False if not this module's command
    """
    if command != "my_primary_command":
        return False

    # Do the work
    execute_workflow()

    return True
```

**Why:**
- Modules self-identify (no central routing table)
- Simple boolean return (handled or not)
- First match wins (order doesn't matter)

### Pattern 2: Pure Handler Functions

Handlers are pure functions with clear contracts:

```python
def get_architecture_standards() -> str:
    """
    Return formatted standards content

    No side effects. No state. Just input → output.

    Returns:
        str: Rich-formatted text
    """
    lines = [...]
    return "\n".join(lines)
```

**Why:**
- Testable (no mocks needed)
- Transportable (copy to any branch)
- Predictable (same input = same output)

### Pattern 3: Auto-Creating JSON Handler

Modules never check if JSON exists - they just use it:

```python
# Module code - simple
json_handler.log_operation("standard_displayed", {"command": "architecture"})

# Handler - handles all the complexity
def log_operation(operation: str, data: Dict | None = None):
    module_name = _get_caller_module_name()  # Auto-detect
    ensure_module_jsons(module_name)         # Auto-create if missing
    log = load_json(module_name, "log")      # Auto-load
    log.append(entry)                        # Update
    save_json(module_name, "log", log)       # Auto-save with rotation
```

**Why:**
- Zero boilerplate in modules
- Consistent structure everywhere
- Automatic maintenance (rotation, timestamps)

### Pattern 4: Domain-Organized Handlers

```
handlers/
├── json/          # JSON operations domain
│   └── json_handler.py
├── file/          # File operations domain
│   └── file_handler.py
├── standards/     # Standards domain
│   ├── architecture_content.py
│   └── architecture_check.py
└── config/        # Configuration domain
    └── ignore_handler.py
```

**NOT:**
```
handlers/
├── utils/         # ✗ Technical organization
├── helpers/       # ✗ Vague purpose
└── operations/    # ✗ Generic grouping
```

**Why:**
- Context from path (handlers/json/ = JSON operations)
- Easy to find (domain-based navigation)
- Transportable (copy entire domain package)

---

## Code Flow Diagrams

### Standards Query Flow

```
User: "drone @seed architecture"
  │
  ├─→ Drone resolves @seed to /home/aipass/seed/apps/seed.py
  │
  └─→ Entry Point (seed.py)
      │
      ├─→ discover_modules()
      │   └─→ Returns: [architecture_standard, cli_standard, ...]
      │
      └─→ route_command("architecture", [])
          │
          ├─→ Loop through modules:
          │   │
          │   ├─→ architecture_standard.handle_command("architecture", [])
          │   │   │
          │   │   ├─→ Match! (command == "architecture")
          │   │   │
          │   │   ├─→ json_handler.log_operation()
          │   │   │   └─→ handlers/json/json_handler.py
          │   │   │       ├─→ Auto-detect module: "architecture_standard"
          │   │   │       ├─→ Ensure JSONs exist (auto-create if missing)
          │   │   │       └─→ Append log entry, rotate if needed
          │   │   │
          │   │   └─→ print_standard()
          │   │       │
          │   │       ├─→ console.print() [from CLI service]
          │   │       │
          │   │       ├─→ header("Architecture Standards") [from CLI service]
          │   │       │
          │   │       ├─→ get_architecture_standards()
          │   │       │   └─→ handlers/standards/architecture_content.py
          │   │       │       └─→ Returns Rich-formatted string
          │   │       │
          │   │       └─→ console.print(formatted_text)
          │   │
          │   └─→ Return True (command handled, stop iteration)
          │
          └─→ Command handled successfully
```

### Standards Checklist Flow

```
User: "python3 seed.py checklist apps/modules/my_module.py"
  │
  └─→ Entry Point (seed.py)
      │
      └─→ route_command("checklist", ["apps/modules/my_module.py"])
          │
          └─→ standards_checklist.handle_command("checklist", [...])
              │
              ├─→ Load bypass config (.seed/bypass.json)
              │   └─→ Direct file read (bootstrap - can't use handler)
              │
              ├─→ Parse file path, validate exists
              │
              ├─→ Run 12 standards checks:
              │   │
              │   ├─→ imports_check.check_imports(file_path, branch_root)
              │   │   └─→ handlers/standards/imports_check.py
              │   │       ├─→ Check AIPASS_ROOT pattern
              │   │       ├─→ Check import order
              │   │       ├─→ Check for bypass rules
              │   │       └─→ Return {"score": 95, "violations": [...]}
              │   │
              │   ├─→ architecture_check.check_architecture(...)
              │   ├─→ naming_check.check_naming(...)
              │   ├─→ cli_check.check_cli(...)
              │   ├─→ ... (8 more checks)
              │   │
              │   └─→ Collect all results
              │
              ├─→ Calculate overall score (weighted average)
              │
              └─→ Display results table (Rich formatting)
                  │
                  ├─→ Standard | Score | Status
                  ├─→ Architecture | 100 | ✓ Pass
                  ├─→ CLI | 90 | ✓ Pass
                  └─→ Overall: 95/100
```

---

## File Paths Reference

### Entry Point
- `/home/aipass/seed/apps/seed.py` - Main entry point (429 lines)

### Modules (Orchestration Layer)
- `/home/aipass/seed/apps/modules/architecture_standard.py` (146 lines)
- `/home/aipass/seed/apps/modules/cli_standard.py` (124 lines)
- `/home/aipass/seed/apps/modules/documentation_standard.py` (133 lines)
- `/home/aipass/seed/apps/modules/error_handling_standard.py` (128 lines)
- `/home/aipass/seed/apps/modules/handlers_standard.py` (141 lines)
- `/home/aipass/seed/apps/modules/imports_standard.py` (137 lines)
- `/home/aipass/seed/apps/modules/json_structure_standard.py` (130 lines)
- `/home/aipass/seed/apps/modules/modules_standard.py` (135 lines)
- `/home/aipass/seed/apps/modules/naming_standard.py` (129 lines)
- `/home/aipass/seed/apps/modules/standards_audit.py` (670 lines - needs splitting)
- `/home/aipass/seed/apps/modules/standards_checklist.py` (582 lines)
- `/home/aipass/seed/apps/modules/standards_verify.py` (245 lines)

### Handlers (Implementation Layer)
- `/home/aipass/seed/apps/handlers/__init__.py` - Import guard (146 lines)
- `/home/aipass/seed/apps/handlers/json/json_handler.py` - Auto-creating JSON (268 lines)
- `/home/aipass/seed/apps/handlers/file/file_handler.py` - Text file reading
- `/home/aipass/seed/apps/handlers/standards/architecture_content.py` (124 lines)
- `/home/aipass/seed/apps/handlers/standards/architecture_check.py` - Compliance checker
- `/home/aipass/seed/apps/handlers/standards/*_content.py` - 10 more content handlers
- `/home/aipass/seed/apps/handlers/standards/*_check.py` - 10 more check handlers

---

## Integration Points

### Dependencies
- **Prax:** System-wide logging (`prax.apps.modules.logger`)
- **CLI:** Display services (`cli.apps.modules.console`, `cli.apps.modules.header`)
- **Drone:** Command routing and cross-branch communication

### Services Provided
- **Standards Reference:** All branches query Seed for standards
- **Compliance Checking:** Automated standards validation
- **Branch Audit:** System-wide compliance dashboard
- **Template Verification:** Cortex template compliance checking

### Communication
- **AI_Mail:** Receives compliance notifications
- **Flow:** Reports work completion
- **Memory Bank:** Archives standards evolution

---

## Summary

Seed demonstrates AIPass's 3-layer architecture through working code:

1. **Entry Point (seed.py):** Auto-discovers modules, routes commands, provides help
2. **Modules (apps/modules/):** Orchestrate workflows, implement handle_command() pattern
3. **Handlers (apps/handlers/):** Implement all business logic, domain-organized, transportable

**Key Principles:**
- Import flow goes DOWN only (Entry → Modules → Handlers)
- Handlers are private (import guard blocks cross-branch access)
- Modules are public API (stable interface)
- Domain organization beats technical organization
- Discovery over registration (zero maintenance)
- Code is truth (standards demonstrated, not just documented)

**Why Seed Matters:**
- Reference implementation that branches learn from
- Living proof that standards are achievable
- Self-documenting through introspection
- 99% compliant (targeting 100%)

---

**Created:** 2025-11-29
**Last Updated:** 2025-11-29
*Part of SEED branch documentation*
