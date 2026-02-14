# Drone Discovery System

Technical documentation for the runtime command discovery system that enables Drone to dynamically discover, register, and activate commands from Python modules across the AIPass ecosystem.

---

## Overview

The discovery system automates the process of making module commands available through the Drone orchestrator. Instead of manually configuring command mappings, discovery scans modules, detects their CLI commands, assigns them unique IDs, and allows interactive activation.

### Core Capabilities

- **Runtime Scanning**: Discovers commands by executing modules with `--help` or parsing source code
- **Global ID Management**: Assigns unique IDs to all commands across the ecosystem
- **Interactive Activation**: User-guided mapping of module commands to Drone command names
- **Duplicate Prevention**: Prevents command name conflicts within and across systems
- **Persistence**: Maintains registration state in `registry.json` and activation state in `active.json`

### Architecture

The system follows a three-phase workflow:

1. **SCAN** - Discover commands from a module
2. **REGISTER** - Assign global IDs and persist metadata
3. **ACTIVATE** - Map commands to Drone command names interactively

---

## Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                        DISCOVERY WORKFLOW                        │
└─────────────────────────────────────────────────────────────────┘

PHASE 1: SCAN
┌──────────────────────────┐
│  drone scan @flow        │
│                          │
│  1. Resolve path         │──→ @flow → /home/aipass/flow/
│  2. Detect module type   │──→ CLI vs Library
│  3. Discover commands    │──→ Runtime --help OR Source parsing
│                          │
│  OUTPUT:                 │
│  ✓ 12 commands found     │
└──────────────────────────┘
           ↓
PHASE 2: REGISTER (Auto-triggered)
┌──────────────────────────┐
│  Auto-registration       │
│                          │
│  1. Load global ID       │──→ Next ID: 042
│  2. Assign IDs           │──→ create:042, list:043, ...
│  3. Save to registry     │──→ commands/flow/registry.json
│  4. Update global ID     │──→ Counter: 054
│                          │
│  OUTPUT:                 │
│  ✓ 12 registered         │
└──────────────────────────┘
           ↓
PHASE 3: ACTIVATE (Prompted)
┌──────────────────────────┐
│  Interactive activation  │
│                          │
│  1. Show registered      │──→ Display ID | Command | Status
│  2. Prompt for ID        │──→ User selects ID
│  3. Get Drone name       │──→ User enters "plan create"
│  4. Check duplicates     │──→ Validate uniqueness
│  5. Save activation      │──→ commands/flow/active.json
│                          │
│  OUTPUT:                 │
│  ✓ drone plan create     │
└──────────────────────────┘
           ↓
EXECUTION
┌──────────────────────────┐
│  drone plan create       │
│                          │
│  1. Lookup in active     │──→ active.json["plan create"]
│  2. Resolve module path  │──→ /home/aipass/flow/flow_plan.py
│  3. Execute command      │──→ python3 flow_plan.py create
└──────────────────────────┘
```

---

## Command Scanning

### Discovery Methods

The system uses two complementary approaches to discover commands:

#### 1. Runtime --help Execution (Fast)

Executes the module with `--help` flag and parses the output for a `Commands:` line.

**Advantages:**
- Fast execution
- Works for any module following AIPass CLI standards

**Limitations:**
- Requires module to have `--help` support
- May truncate long command lists
- Requires working module dependencies

**Example Output Pattern:**
```
Commands: create, list, edit, delete, execute
```

#### 2. Source Code Parsing (Reliable)

Scans `apps/modules/*.py` files and extracts commands from `handle_command()` function patterns.

**Advantages:**
- More reliable for complex modules
- No module execution required
- Captures all commands regardless of length

**Limitations:**
- Slower for large codebases
- Requires standard code patterns

**Detected Patterns:**
```python
if command == "create":          # Direct equality
if command in ["list", "edit"]:  # List membership
if command not in ["help"]:      # Exclusion list
if command != "internal":        # Inequality
```

### Module Type Detection

The system distinguishes between CLI modules and library modules:

**CLI Indicators:**
- `import argparse` or `from argparse import`
- `ArgumentParser(` usage
- `sys.argv[1` access
- `add_subparsers(` calls
- `if __name__ == "__main__"` blocks

**Classification:**
- `cli` - Module has CLI interface
- `library` - Module is library code
- `unknown` - Could not detect type

---

## Registration

### Global ID Assignment

Every command across the entire ecosystem receives a unique global ID from a centralized counter.

**ID Counter Location:**
```
/home/aipass/aipass_core/drone/drone_json/drone_registry.json
```

**Counter Schema:**
```json
{
  "global_id_counter": 54,
  "systems": { ... }
}
```

### Registry Files

Each system gets its own registry file storing command metadata.

**Registry Location:**
```
/home/aipass/aipass_core/drone/commands/[system_name]/registry.json
```

**Registry Schema:**
```json
{
  "flow_plan:create": {
    "id": 42,
    "command_name": "create",
    "module_name": "flow_plan",
    "help": "",
    "module_path": "/home/aipass/flow/flow_plan.py",
    "registered_date": "2025-11-29T10:30:00Z",
    "active": false
  }
}
```

**Registry Key Format:**
- Single file: `module:command` (e.g., `flow_plan:create`)
- Directory scan: `module:command` for each module (e.g., `task_manager:list`, `workflow:execute`)

### Registration Process

1. **Scan Module** - Discover all commands
2. **Check Existing** - Load existing registry (if present)
3. **Assign IDs** - New commands get next global ID, existing keep their ID
4. **Save Registry** - Persist command metadata
5. **Increment Counter** - Update global ID counter

---

## Activation

### Interactive Workflow

The activation phase maps registered commands to user-friendly Drone command names.

**Activation Interface:**
```
┌──────────────────────────────────────────────────┐
│ Activate commands for: flow                      │
└──────────────────────────────────────────────────┘

ID      Command                             Active    Drone Command
----    ---------------------------------   ------    --------------
042     flow_plan:create                    No        n/a
043     flow_plan:list                      YES       plan list
044     flow_plan:edit                      No        n/a
045     flow_plan:execute                   YES       plan run

2 active / 4 total

Enter command ID to activate (or 'done' to finish):
```

**User Interaction:**
1. Display all registered commands with IDs and status
2. Prompt for command ID to activate
3. Request Drone command name (e.g., `plan create`)
4. Optionally request description
5. Validate uniqueness and save activation
6. Repeat until user enters 'done'

### Duplicate Prevention

The system prevents command name conflicts at two levels:

#### 1. Within Session
Prevents activating the same Drone command name multiple times during a single activation session.

```python
# Check if already used in this session
duplicate_in_session = any(
    cmd_entry['drone_command'] == drone_cmd and cmd_entry['active']
    for cmd_entry in commands
)
```

#### 2. Across Systems
Prevents conflicts with commands already activated in other systems.

```python
# Check all active.json files
existing_activation = lookup_activated_command(drone_cmd)
if existing_activation:
    print(f"Already active in system '{existing_activation['system']}'")
```

### Active Files

Activation state is persisted in system-specific `active.json` files.

**Active File Location:**
```
/home/aipass/aipass_core/drone/commands/[system_name]/active.json
```

**Active File Schema:**
```json
{
  "plan create": {
    "id": 42,
    "command_name": "create",
    "description": "Create a new plan",
    "module_path": "/home/aipass/flow/flow_plan.py"
  },
  "plan list": {
    "id": 43,
    "command_name": "list",
    "description": "List all plans",
    "module_path": "/home/aipass/flow/flow_plan.py"
  }
}
```

**Active File Updates:**
- Merges with existing data (doesn't overwrite)
- Adds new activations
- Removes deactivated commands
- Preserves previous activations

---

## Key Files

| File | Location | Purpose |
|------|----------|---------|
| **discovery.py** | `/home/aipass/aipass_core/drone/apps/modules/` | Main orchestrator - delegates to handlers |
| **module_scanning.py** | `/home/aipass/aipass_core/drone/apps/handlers/discovery/` | Path resolution, module scanning, command detection |
| **command_parsing.py** | `/home/aipass/aipass_core/drone/apps/handlers/discovery/` | Registration, global ID management, registry files |
| **activation.py** | `/home/aipass/aipass_core/drone/apps/handlers/discovery/` | Interactive activation, duplicate prevention, active files |
| **drone_registry.json** | `/home/aipass/aipass_core/drone/drone_json/` | Global ID counter and system metadata |
| **registry.json** | `/home/aipass/aipass_core/drone/commands/[system]/` | System-specific command registry |
| **active.json** | `/home/aipass/aipass_core/drone/commands/[system]/` | System-specific activation state |

---

## Usage Examples

### Basic Workflow

**Scan and activate a module:**
```bash
# Scan module - auto-registers and prompts for activation
drone scan @flow

# Output shows:
# ✓ 12 commands found
# ✓ Registered 12 new commands
# Activate commands now? [Y/n]:
```

**Activate specific commands:**
```
Enter command ID to activate (or 'done' to finish): 42
Drone command name (e.g., 'test create', 'backup snap'): plan create
Description (optional, press Enter to skip): Create a new workflow plan
✅ Activated 042 as 'drone plan create'

Enter command ID to activate (or 'done' to finish): 43
Drone command name: plan list
Description: List all plans
✅ Activated 043 as 'drone plan list'

Enter command ID to activate (or 'done' to finish): done
```

### Path Resolution

The system supports multiple path formats:

```bash
# Relative path (@ required)
drone scan @flow                    # → /home/aipass/flow/

# Specific file
drone scan @flow/flow_plan.py       # → /home/aipass/flow/flow_plan.py

# Full absolute path
drone scan @/home/aipass/flow       # → /home/aipass/flow/

# Core module
drone scan @drone                   # → /home/aipass/aipass_core/drone/
```

### List Commands

**View all activated commands:**
```bash
drone list
```

**Filter by system:**
```bash
drone list @prax
drone list prax    # @ optional for list
```

### Manual Steps (Optional)

The scan command now auto-registers and prompts for activation, but individual steps can still be run:

```bash
# 1. Scan only (deprecated - use scan)
drone scan @flow

# 2. Register only (deprecated - scan auto-registers)
drone register @flow

# 3. Activate commands
drone activate flow
```

### View Systems

**List all registered systems:**
```bash
drone systems

# Output:
# System           Commands    Active
# ────────────────────────────────────
# flow             12          4
# prax             8           3
# seed             15          7
```

### Remove Activation

**Deactivate a command:**
```bash
drone remove "plan create"
```

### Refresh System

**Re-scan and update registry:**
```bash
drone refresh flow
```

---

## Technical Details

### Path Resolution Logic

1. **Registered System Check** - If input matches a registered system name, use its module path
2. **@ Symbol Validation** - Path operations require @ prefix
3. **Path Format Detection**:
   - `@/home/aipass/flow` → Full absolute path
   - `@/flow/` → Relative with leading slash
   - `@flow` → Simple relative path
4. **Fallback Search** - Try `aipass_core/` subdirectory if not found
5. **Apps Directory Check** - Try `apps/` subdirectory for post-migration layout

### Command Lookup

When executing `drone [command]`, the system:

1. Searches all `active.json` files in `commands/*/` directories
2. Finds matching Drone command name
3. Returns execution metadata:
   - `module_path` - Full path to Python module
   - `command_name` - Original command name
   - `system` - System name
   - `id` - Global command ID

### Error Handling

**Module Not Found:**
```
❌ Path not found: /home/aipass/nonexistent

💡 Similar directories found:
   drone scan @flow
   drone scan @prax
```

**No Commands Detected:**
```
No commands detected to register

💡 This module appears to be non-compliant (missing --help with Commands: line)

   Upgrade to compliance:
   drone comply @flow/flow_plan.py
```

**Duplicate Drone Command:**
```
⚠️  Drone command 'plan create' is already active in system 'flow' (ID 042).
   Choose a unique drone command name.
```

---

## Integration Points

### Dependencies

**Internal Modules:**
- `prax.apps.modules.logger` - System-wide logging
- `cli.apps.modules` - Rich console formatting
- `drone.apps.handlers.registry` - Global registry access

**Standard Library:**
- `subprocess` - Runtime --help execution
- `json` - Registry file I/O
- `pathlib` - Path operations
- `re` - Source code pattern matching

### File System Structure

```
/home/aipass/aipass_core/drone/
├── apps/
│   ├── modules/
│   │   └── discovery.py           # Orchestrator
│   └── handlers/
│       └── discovery/
│           ├── __init__.py         # Public API exports
│           ├── module_scanning.py  # Scanning logic
│           ├── command_parsing.py  # Registration logic
│           └── activation.py       # Activation logic
├── commands/
│   ├── flow/
│   │   ├── registry.json          # Flow command metadata
│   │   └── active.json            # Flow activated commands
│   └── prax/
│       ├── registry.json
│       └── active.json
└── drone_json/
    └── drone_registry.json        # Global ID counter
```

---

## Best Practices

### Module Compliance

For modules to be discoverable, they should:

1. **Implement --help** with `Commands:` line:
   ```
   Commands: create, list, edit, delete
   ```

2. **Use standard `handle_command()` patterns**:
   ```python
   def handle_command(command: str, args: list) -> bool:
       if command == "create":
           # handle create
       elif command in ["list", "ls"]:
           # handle list
   ```

3. **Follow AIPass CLI standards** (STANDARDS.md section 6.5)

### Activation Naming

When activating commands, use descriptive Drone command names:

**Good:**
- `plan create` (clear domain + action)
- `backup snap` (clear noun + verb)
- `test run` (clear context)

**Avoid:**
- `c` (too cryptic)
- `create` (ambiguous - create what?)
- `do_the_thing` (unclear)

### System Management

- **One system per module** - Don't register the same module multiple times
- **Meaningful system names** - Use module/branch name as system name
- **Regular refresh** - Re-scan modules when commands change
- **Clean deactivation** - Remove unused activations to avoid clutter

---

## Troubleshooting

### Scan fails with "missing @ prefix"

**Problem:** Path must start with @
**Solution:** `drone scan @flow` (not `drone scan flow`)

### No commands found

**Problem:** Module doesn't follow CLI standards
**Solution:** Check for `--help` support or use `drone comply` to upgrade

### Duplicate command name

**Problem:** Drone command already active elsewhere
**Solution:** Choose a unique name or deactivate existing command first

### Wrong commands registered

**Problem:** Scan picked up wrong files or patterns
**Solution:** Use `drone refresh [system]` to re-scan

---

*Generated: 2025-11-29*
*Version: 2.0.0*
*Maintainer: Drone*
