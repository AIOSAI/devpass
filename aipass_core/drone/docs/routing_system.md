# Drone Routing System

Technical documentation for Drone's command routing and @ argument resolution.

---

## Table of Contents

1. [Overview](#overview)
2. [@ Argument Resolution](#-argument-resolution)
3. [Command Routing Flow](#command-routing-flow)
4. [Direct vs Activated Commands](#direct-vs-activated-commands)
5. [Reserved @ Targets](#reserved--targets)
6. [Key Files](#key-files)
7. [Code Examples](#code-examples)

---

## Overview

Drone provides two ways to execute commands across the AIPass ecosystem:

1. **Direct Branch Access** - `drone @branch command args`
2. **Activated Commands** - `drone shortcut args` (shortcuts configured via discovery system)

Both methods use the same @ resolution system to convert branch names to absolute paths before execution.

**Core Principle:** Drone is the single source of truth for @ resolution. Branches receive clean absolute paths, never @ symbols.

---

## @ Argument Resolution

### Resolution Process

The `preprocess_args()` function resolves all @ arguments to absolute paths before passing them to branch modules.

```
User Input:     drone @flow create @seed "My task"
After Routing:  flow.py create @seed "My task"
After Resolve:  flow.py create /home/aipass/seed "My task"
```

### Resolution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ preprocess_args(["create", "@seed", "--flag", "@flow"])    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ├─► For each arg:
                   │   ├─► Starts with @?
                   │   │   ├─► YES → resolve_target(arg)
                   │   │   │   ├─► Reserved? (@, @all)
                   │   │   │   │   ├─► YES → Return reserved value
                   │   │   │   │   └─► NO  → Continue
                   │   │   │   │
                   │   │   │   ├─► Has path? (@seed/apps/seed.py)
                   │   │   │   │   ├─► YES → Split + get_branch_path() + sub_path
                   │   │   │   │   └─► NO  → get_branch_path()
                   │   │   │   │
                   │   │   │   └─► get_branch_path(branch_name)
                   │   │   │       ├─► Load BRANCH_REGISTRY.json
                   │   │   │       ├─► Search by name/email
                   │   │   │       ├─► Fallback: aipass_core/name
                   │   │   │       └─► Return: Path object
                   │   │   │
                   │   │   └─► NO  → Pass through unchanged
                   │   │
                   │   └─► Append to resolved_args[]
                   │
                   └─► Return: ["create", "/home/aipass/seed", "--flag", "/home/aipass/aipass_core/flow"]
```

### Implementation

**File:** `/home/aipass/aipass_core/drone/apps/handlers/routing/args.py`

```python
def preprocess_args(args: List[str]) -> List[str]:
    """
    Resolve all @ arguments to full paths before passing to modules.

    Args:
        args: List of arguments that may contain @ prefixes

    Returns:
        List of arguments with @ resolved to full paths
    """
    resolved_args = []

    for arg in args:
        if arg.startswith('@'):
            try:
                # Use paths handler for @ resolution
                resolved = resolve_target(arg)
                # resolve_target returns Path or "@all" string
                if isinstance(resolved, Path):
                    resolved_args.append(str(resolved))
                else:
                    # Pass through special targets like "@all"
                    resolved_args.append(resolved)
            except ValueError:
                # Can't resolve - pass raw (branch will get error)
                resolved_args.append(arg)
        else:
            resolved_args.append(arg)

    return resolved_args
```

### Resolution Priority

`resolve_target()` uses this priority order:

1. **Reserved Targets** - `@`, `@all` (defined in RESERVED_TARGETS)
2. **Path-like Targets** - `@flow/apps/flow.py` (splits on `/`)
3. **Registry Lookup** - Search BRANCH_REGISTRY.json by name/email
4. **Standard Locations** - Fallback to `aipass_core/name` or `aipass/name`

---

## Command Routing Flow

### Complete Routing Pipeline

```
┌───────────────────────────────────────────────────────────────┐
│ User Input: drone plan create @seed "My task"                │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 ├─► drone.py main()
                 │   ├─► Parse: command="plan", args=["create", "@seed", "My task"]
                 │   │
                 │   ├─► Check: @ pattern?
                 │   │   └─► NO (doesn't start with @)
                 │   │
                 │   ├─► Check: / pattern?
                 │   │   └─► NO (no slash)
                 │   │
                 │   ├─► discover_modules()
                 │   │   └─► Returns: [activated_commands, discovery, ...]
                 │   │
                 │   └─► route_command("plan", ["create", "@seed", "My task"], modules)
                 │       │
                 │       └─► For each module in modules:
                 │           ├─► activated_commands.handle_command("plan", ...)
                 │           │   │
                 │           │   ├─► _try_match_command("plan", ["create", ...])
                 │           │   │   ├─► Try: "plan create @seed My" (4 words) → NOT FOUND
                 │           │   │   ├─► Try: "plan create @seed" (3 words) → NOT FOUND
                 │           │   │   ├─► Try: "plan create" (2 words) → FOUND!
                 │           │   │   └─► Returns: {
                 │           │   │       "module_path": "/home/aipass/aipass_core/flow/apps/flow.py",
                 │           │   │       "command_name": "create",
                 │           │   │       "remaining_args": ["@seed", "My task"]
                 │           │   │     }
                 │           │   │
                 │           │   ├─► Build: module_args = ["create", "@seed", "My task"]
                 │           │   │
                 │           │   ├─► preprocess_args(["create", "@seed", "My task"])
                 │           │   │   └─► Returns: ["create", "/home/aipass/seed", "My task"]
                 │           │   │
                 │           │   └─► run_branch_module(flow.py, ["create", "/home/aipass/seed", "My task"])
                 │           │       └─► subprocess.run(["python3", "flow.py", "create", "/home/aipass/seed", "My task"])
                 │           │
                 │           └─► Returns: True (handled)
                 │
                 └─► Done
```

### Direct Branch Routing

For commands starting with `@`:

```
┌───────────────────────────────────────────────────────────────┐
│ User Input: drone @flow create @seed "My task"               │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 ├─► drone.py main()
                 │   ├─► Parse: command="@flow", args=["create", "@seed", "My task"]
                 │   │
                 │   ├─► Check: @ pattern?
                 │   │   └─► YES
                 │   │
                 │   ├─► Check: / in command?
                 │   │   ├─► YES → resolve_slash_pattern()
                 │   │   │   └─► Example: @seed/imports → /home/aipass/seed/apps/modules/imports_standard.py
                 │   │   │
                 │   │   └─► NO → resolve_scan_path()
                 │   │       └─► resolve_scan_path("@flow")
                 │   │           └─► Returns: /home/aipass/aipass_core/flow/apps/flow.py
                 │   │
                 │   ├─► preprocess_args(["create", "@seed", "My task"])
                 │   │   └─► Returns: ["create", "/home/aipass/seed", "My task"]
                 │   │
                 │   └─► run_branch_module(flow.py, ["create", "/home/aipass/seed", "My task"])
                 │       └─► subprocess.run(["python3", "flow.py", "create", "/home/aipass/seed", "My task"])
                 │
                 └─► Done
```

---

## Direct vs Activated Commands

### Direct Commands

**Syntax:** `drone @branch command args`

**Characteristics:**
- Explicit branch targeting
- Always routed to the specified branch
- No configuration required
- Uses @ pattern detection in drone.py

**Example:**
```bash
drone @flow create @seed "My task"
drone @seed audit
drone @ai_mail send @flow "Subject" "Message"
```

**Routing Path:**
```
drone.py → Check @ pattern → resolve_scan_path() → run_branch_module()
```

### Activated Commands (Shortcuts)

**Syntax:** `drone shortcut args`

**Characteristics:**
- Custom shortcuts configured via discovery system
- Mapped to branch commands in activated_commands.json
- Progressive matching (up to 4 words)
- Requires activation via `drone scan` and `drone activate`

**Example:**
```bash
drone plan create @seed "My task"   # → @flow create
drone plan list                     # → @flow list
drone email send @flow "Hi" "Msg"   # → @ai_mail send
```

**Routing Path:**
```
drone.py → route_command() → activated_commands.handle_command() →
lookup_activated_command() → run_branch_module()
```

### Progressive Matching Algorithm

Activated commands use progressive matching to find the longest matching command:

```python
def _try_match_command(command: str, args: list) -> dict | None:
    """
    Tries progressively longer command strings:
    - "plan create @seed My" (4 words)
    - "plan create @seed" (3 words)
    - "plan create" (2 words)  ← MATCH
    - "plan" (1 word)
    """
    max_words = min(4, len(args) + 1)

    for word_count in range(max_words, 0, -1):
        if word_count == 1:
            potential_cmd = command
            remaining_args = args
        else:
            words_to_take = word_count - 1
            potential_cmd = command + " " + " ".join(args[:words_to_take])
            remaining_args = args[words_to_take:]

        cmd_info = lookup_activated_command(potential_cmd)
        if cmd_info:
            cmd_info['remaining_args'] = remaining_args
            return cmd_info

    return None
```

**Why 4 words?** Balances specificity with performance. Most commands are 1-3 words.

### Configuration Storage

Activated commands stored in:
```
/home/aipass/aipass_core/drone/data/activated_commands.json
```

Format:
```json
{
  "commands": {
    "plan create": {
      "system": "flow",
      "module_path": "/home/aipass/aipass_core/flow/apps/flow.py",
      "command_name": "create",
      "original_command": "create",
      "activated_at": "2025-11-29T10:30:00"
    }
  }
}
```

---

## Reserved @ Targets

### Special Targets

| Target | Resolves To | Usage |
|--------|-------------|-------|
| `@` | `/home/aipass` | AIPASS_HOME - root directory |
| `@all` | `"@all"` (string) | Special flag for multi-branch operations |

### Reserved Target Handling

```python
RESERVED_TARGETS = {
    "@": AIPASS_HOME,
    "@all": "@all",
}

def resolve_target(target: str) -> Union[Path, str]:
    if target in RESERVED_TARGETS:
        return RESERVED_TARGETS[target]
    # ... continue with normal resolution
```

### @ vs @all

**`@` (AIPASS_HOME):**
- Returns: `Path("/home/aipass")`
- Used to reference the root directory
- Example: `drone @seed create @ "New branch at root"`

**`@all` (Multi-target flag):**
- Returns: String `"@all"` (not a Path)
- Handled specially by branches to iterate all branches
- Example: `drone @seed audit @all` (audit all branches)

---

## Key Files

### Core Routing

| File | Purpose | Key Functions |
|------|---------|---------------|
| `/home/aipass/aipass_core/drone/apps/drone.py` | Entry point - routes commands | `main()`, `show_help()` |
| `/home/aipass/aipass_core/drone/apps/modules/routing.py` | Module interface | Re-exports routing functions |
| `/home/aipass/aipass_core/drone/apps/handlers/routing/__init__.py` | Handler package | Exports routing handlers |

### @ Resolution

| File | Purpose | Key Functions |
|------|---------|---------------|
| `/home/aipass/aipass_core/drone/apps/handlers/routing/args.py` | @ argument preprocessing | `preprocess_args()` |
| `/home/aipass/aipass_core/drone/apps/handlers/paths/resolver.py` | Path resolution logic | `resolve_target()`, `get_branch_path()`, `resolve()` |

### Command Routing

| File | Purpose | Key Functions |
|------|---------|---------------|
| `/home/aipass/aipass_core/drone/apps/handlers/routing/router.py` | Routes to modules | `route_command()` |
| `/home/aipass/aipass_core/drone/apps/handlers/routing/discovery.py` | Module discovery | `discover_modules()` |

### Activated Commands

| File | Purpose | Key Functions |
|------|---------|---------------|
| `/home/aipass/aipass_core/drone/apps/modules/activated_commands.py` | Handles shortcuts | `handle_command()`, `_try_match_command()` |
| `/home/aipass/aipass_core/drone/apps/handlers/discovery/activation.py` | Command lookup | `lookup_activated_command()` |

### Data Files

| File | Purpose |
|------|---------|
| `/home/aipass/BRANCH_REGISTRY.json` | Branch registry - name, path, email mappings |
| `/home/aipass/aipass_core/drone/data/activated_commands.json` | Activated command shortcuts |

---

## Code Examples

### Example 1: Resolving @ Arguments

```python
from drone.apps.handlers.routing import preprocess_args

# Input with @ arguments
args = ["create", "@seed", "--template", "minimal", "@flow"]

# Resolve
resolved = preprocess_args(args)

# Output
# ["create", "/home/aipass/seed", "--template", "minimal", "/home/aipass/aipass_core/flow"]
```

### Example 2: Direct Branch Routing

```python
# User command
# drone @flow create @seed "My task"

# In drone.py main():
command = "@flow"
args = ["create", "@seed", "My task"]

if command.startswith('@'):
    # Resolve @flow to module path
    module_path = resolve_scan_path("@flow")
    # → /home/aipass/aipass_core/flow/apps/flow.py

    # Resolve @ arguments in args
    resolved_args = preprocess_args(["create", "@seed", "My task"])
    # → ["create", "/home/aipass/seed", "My task"]

    # Execute
    run_branch_module(module_path, resolved_args)
    # → subprocess.run(["python3", "flow.py", "create", "/home/aipass/seed", "My task"])
```

### Example 3: Activated Command Routing

```python
# User command
# drone plan create @seed "My task"

# In drone.py main():
command = "plan"
args = ["create", "@seed", "My task"]

# Discover modules
modules = discover_modules()
# → [activated_commands, discovery, ...]

# Route to modules
for module in modules:
    if module.handle_command(command, args):
        # activated_commands.handle_command() matches "plan create"

        # Looks up in activated_commands.json:
        cmd_info = lookup_activated_command("plan create")
        # → {
        #     "module_path": "/home/aipass/aipass_core/flow/apps/flow.py",
        #     "command_name": "create"
        #   }

        # Build module args
        module_args = ["create", "@seed", "My task"]

        # Resolve @ arguments
        resolved_args = preprocess_args(module_args)
        # → ["create", "/home/aipass/seed", "My task"]

        # Execute
        run_branch_module(module_path, resolved_args)
        # → subprocess.run(["python3", "flow.py", "create", "/home/aipass/seed", "My task"])

        return True
```

### Example 4: Using High-Level resolve()

```python
from drone.apps.handlers.paths import resolve

# Single branch
info = resolve("@flow")
# Returns:
# {
#     "name": "FLOW",
#     "path": Path("/home/aipass/aipass_core/flow"),
#     "email": "@flow",
#     "exists": True,
#     "module_path": Path("/home/aipass/aipass_core/flow/apps/flow.py"),
#     "status": "active"
# }

# All branches
all_branches = resolve("@all")
# Returns: [
#     {"name": "FLOW", "path": Path(...), ...},
#     {"name": "SEED", "path": Path(...), ...},
#     ...
# ]
```

### Example 5: Path-like @ Targets

```python
from drone.apps.handlers.routing import preprocess_args

# Input with path-like @ target
args = ["audit", "@seed/apps/seed.py"]

# Resolve
resolved = preprocess_args(args)

# Output
# ["audit", "/home/aipass/seed/apps/seed.py"]
```

### Example 6: Reserved Target Handling

```python
from drone.apps.handlers.routing import preprocess_args

# Reserved @ target
args = ["create", "@", "new_branch"]
resolved = preprocess_args(args)
# → ["create", "/home/aipass", "new_branch"]

# Special @all target
args = ["audit", "@all"]
resolved = preprocess_args(args)
# → ["audit", "@all"]  # Passed as string, not Path
```

---

## Architecture Notes

### Separation of Concerns

**Entry Point** (`drone.py`)
- Parses command line
- Detects @ and / patterns
- Delegates to routing system

**Routing Module** (`modules/routing.py`)
- Public API interface
- Re-exports handler functions

**Routing Handlers** (`handlers/routing/`)
- Pure implementation
- No CLI output
- Stateless functions

**Path Handlers** (`handlers/paths/`)
- @ resolution logic
- Branch registry lookup
- Path validation

**Activated Commands Module** (`modules/activated_commands.py`)
- Command matching
- Shortcut execution
- Progressive matching algorithm

### Design Decisions

1. **@ Resolution Centralized** - Drone is single source of truth. Branches never resolve @ themselves.

2. **Progressive Matching** - Activated commands try longest match first (up to 4 words) to support compound commands like "plan create" vs "plan".

3. **Reserved Targets** - `@` and `@all` handled specially to prevent conflicts with branch names.

4. **Stateless Handlers** - All resolution functions are pure - no state, no CLI output, fully testable.

5. **Two Routing Paths** - Direct (@ pattern) and Activated (discovery system) coexist without conflict.

---

## Troubleshooting

### Common Issues

**Problem:** `@branch` not found
- Check `BRANCH_REGISTRY.json` for branch registration
- Verify path exists: `ls /home/aipass/aipass_core/branch`
- Try: `drone systems` to list registered branches

**Problem:** Activated command not working
- Check: `drone list` to see activated commands
- Verify: `drone scan @branch` to discover commands
- Activate: `drone activate system` to register shortcuts

**Problem:** @ arguments not resolving
- Verify @ prefix: `@seed` not `seed`
- Check special targets: `@` vs `@all`
- Test resolution: `drone @branch --help` to verify branch exists

---

**Last Updated:** 2025-11-29
**Version:** 1.0.0
