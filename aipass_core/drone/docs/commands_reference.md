# Drone Command Reference

Complete command reference for the Drone command routing and discovery system.

---

## Overview

Drone provides two ways to execute commands:

1. **Direct Branch Access** (`@` prefix) - Run branch commands directly
2. **Activated Shortcuts** - Use custom shortcuts configured via scan/activate

---

## Command Categories

### Help & Discovery

#### `drone` (no args)
Display discovered modules and introspection information.

**Usage:**
```bash
drone
```

**Output:**
- Lists all discovered drone modules
- Shows module count
- Displays help hint

---

#### `drone help` / `drone --help` / `drone -h`
Display comprehensive help and usage guide.

**Usage:**
```bash
drone help
drone --help
drone -h
```

**Output:**
- Direct branch access pattern (`@`)
- Activated commands pattern
- Discovery & management commands
- Quick start guide

---

#### `drone systems`
List all registered branch systems with statistics.

**Usage:**
```bash
drone systems
```

**Output:**
- System name
- Number of registered commands
- Number of activated commands
- Registration status

**Example:**
```bash
drone systems

# Output:
# System: flow
#   Registered: 15 commands
#   Activated: 3 shortcuts
#
# System: seed
#   Registered: 8 commands
#   Activated: 2 shortcuts
```

---

#### `drone scan @branch [--all]`
Scan a branch for commands, auto-register them, and prompt for activation.

**Arguments:**
- `@branch` - Branch to scan (e.g., `@flow`, `@seed`, `@prax`)
- `--all` - Optional flag to show Python commands (for debugging/testing)

**Usage:**
```bash
# Scan flow branch
drone scan @flow

# Scan with Python command display
drone scan @devpulse --all

# Scan seed branch
drone scan @seed
```

**Workflow:**
1. Scans branch module for available commands
2. Auto-registers discovered commands to registry
3. Prompts user to activate commands interactively
4. Creates shortcuts for selected commands

**Example Session:**
```bash
$ drone scan @flow

Scanning: /home/aipass/aipass_core/flow
✓ Found 15 commands

✅ Registered 5 new commands (15 total)

Activate commands now? [Y/n]: y

Select commands to activate:
  [1] create - Create new plan
  [2] list - List all plans
  [3] close - Close a plan
  ...

Enter numbers (comma-separated): 1,2

Activated 2 commands:
  plan create -> @flow create
  plan list -> @flow list
```

**Note:** The `--all` flag is primarily for testing/debugging. It shows the full Python command syntax that can be copied and pasted for testing.

---

### Activation & Management

#### `drone activate <system>`
Activate commands interactively from a registered system.

**Arguments:**
- `<system>` - System name (e.g., `flow`, `seed`, `prax`)

**Usage:**
```bash
# Activate flow commands
drone activate flow

# Activate seed commands
drone activate seed
```

**Interactive Workflow:**
1. Shows available commands from system
2. User selects which commands to activate
3. User defines shortcut names for each command
4. Saves activated commands to active.json

**Example Session:**
```bash
$ drone activate flow

Available commands from flow:
  [1] create - Create new plan
  [2] list - List all plans
  [3] close - Close a plan
  [4] remove - Remove a plan

Enter numbers (comma-separated): 1,2

Configure 'create':
  Shortcut command: plan create

Configure 'list':
  Shortcut command: plan list

✅ Activated 2 commands
```

---

#### `drone list [system]`
List activated command shortcuts, optionally filtered by system.

**Arguments:**
- `[system]` - Optional system filter (e.g., `flow`, `@prax`)

**Usage:**
```bash
# List all activated shortcuts
drone list

# List only flow shortcuts
drone list flow

# List only prax shortcuts (@ prefix optional)
drone list @prax
```

**Output:**
```bash
$ drone list

Activated Commands:
  plan create    -> @flow create
  plan list      -> @flow list
  plan close     -> @flow close
  seed audit     -> @seed audit
  email send     -> @ai_mail send

Total: 5 commands

$ drone list flow

Activated Commands (flow):
  plan create    -> @flow create
  plan list      -> @flow list
  plan close     -> @flow close

Total: 3 commands
```

---

#### `drone edit`
Edit an activated command interactively.

**Usage:**
```bash
drone edit
```

**Interactive Workflow:**
1. Shows list of activated commands
2. User selects command to edit
3. User provides new shortcut name
4. Updates active.json

**Example Session:**
```bash
$ drone edit

Select command to edit:
  [1] plan create -> @flow create
  [2] plan list -> @flow list
  [3] seed audit -> @seed audit

Select command: 1

Current shortcut: plan create
New shortcut: task create

✅ Updated: task create -> @flow create
```

---

#### `drone remove <drone_command>`
Remove an activated command shortcut.

**Arguments:**
- `<drone_command>` - The shortcut command to remove (e.g., `plan create`)

**Usage:**
```bash
# Remove single-word shortcut
drone remove plan

# Remove multi-word shortcut
drone remove "plan create"
```

**Example:**
```bash
$ drone remove "plan create"

✅ Removed: plan create -> @flow create
```

---

#### `drone refresh @system`
Re-scan a system to update the command registry.

**Arguments:**
- `@system` - System to refresh (e.g., `@flow`, `@seed`)

**Usage:**
```bash
# Refresh flow system
drone refresh @flow

# Refresh seed system
drone refresh @seed
```

**When to Use:**
- After updating branch command structure
- After adding new commands to a branch
- When registry appears out of sync

**Example:**
```bash
$ drone refresh @flow

Refreshing: flow
✓ Re-scanned module
✓ Updated registry
✅ Refresh complete: 15 commands registered
```

---

### Command Routing

#### Direct Branch Access: `drone @branch [command] [args]`
Execute commands directly on a branch without activation.

**Pattern:**
```bash
drone @<branch> <command> [args]
```

**Arguments:**
- `@branch` - Target branch (e.g., `@flow`, `@seed`, `@ai_mail`)
- `command` - Branch-specific command
- `args` - Command arguments (supports `@branch` notation)

**Usage:**
```bash
# Flow commands
drone @flow help
drone @flow create @seed "My task"
drone @flow list
drone @flow close --all

# Seed commands
drone @seed help
drone @seed audit
drone @seed audit @flow
drone @seed checklist

# AI_Mail commands
drone @ai_mail send @flow "Subject" "Message"
drone @ai_mail inbox
drone @ai_mail read 1

# Prax commands
drone @prax status
drone @prax file watcher start
```

**@ Argument Resolution:**
Drone automatically resolves `@branch` arguments to full paths before passing to branch modules.

**Examples:**
```bash
# @seed resolves to /home/aipass/seed
drone @flow create @seed "My task"

# @flow resolves to /home/aipass/aipass_core/flow
drone seed audit @flow

# @ai_mail resolves to /home/aipass/aipass_core/ai_mail
drone @ai_mail send @drone "Subject" "Message"
```

**Reserved @ Targets:**
| Target | Resolves To |
|--------|-------------|
| `@flow` | `/home/aipass/aipass_core/flow` |
| `@seed` | `/home/aipass/seed` |
| `@drone` | `/home/aipass/aipass_core/drone` |
| `@ai_mail` | `/home/aipass/aipass_core/ai_mail` |
| `@prax` | `/home/aipass/aipass_core/prax` |
| `@cortex` | `/home/aipass/aipass_core/cortex` |
| `@devpulse` | `/home/aipass/aipass_core/devpulse` |
| `@cli` | `/home/aipass/aipass_core/cli` |
| `@aipass` | `/home/aipass` |
| `@` | `/home/aipass` (root) |
| `@all` | Passed as-is (special handling in branches) |

---

#### Nested Branch Access: `drone @branch/module [args]`
Execute specific modules within a branch using slash notation.

**Pattern:**
```bash
drone @<branch>/<module> [args]
```

**Arguments:**
- `@branch/module` - Branch and module path
- `args` - Module arguments

**Usage:**
```bash
# Run seed imports module
drone @seed/imports audit @flow

# Run seed handlers module
drone @seed/handlers audit @prax
```

**How It Works:**
1. Strips `@` prefix from command
2. Resolves slash pattern to module path
3. Executes module with provided arguments

**Example:**
```bash
$ drone @seed/imports audit @flow

# Resolves to:
# /home/aipass/seed/apps/modules/imports_standard.py audit /home/aipass/aipass_core/flow
```

---

#### Activated Shortcuts: `drone <shortcut> [args]`
Use custom shortcuts configured via `drone scan` and `drone activate`.

**Pattern:**
```bash
drone <shortcut> [args]
```

**Supports Multi-Word Commands:**
Drone supports 1-4 word command shortcuts (e.g., `plan`, `plan create`, `prax file watcher start`).

**Arguments:**
- `<shortcut>` - Activated command shortcut (1-4 words)
- `args` - Command arguments

**Usage:**
```bash
# Single-word shortcuts
drone plan              # If activated as single command
drone audit             # If activated as single command

# Two-word shortcuts
drone plan create @seed "My task"
drone plan list
drone seed audit

# Three-word shortcuts
drone prax file watcher start

# Four-word shortcuts
drone dev add task "description"
```

**How Matching Works:**
Drone tries progressively longer command strings to find a match:
1. Try 4-word match: `prax file watcher start`
2. Try 3-word match: `prax file watcher`
3. Try 2-word match: `prax file`
4. Try 1-word match: `prax`

**Example:**
```bash
# Assuming these shortcuts are activated:
#   "plan create" -> @flow create
#   "plan list" -> @flow list
#   "seed audit" -> @seed audit

$ drone plan create @seed "Implement feature X"
# Executes: flow.py create /home/aipass/seed "Implement feature X"

$ drone plan list
# Executes: flow.py list

$ drone seed audit @flow
# Executes: seed.py audit /home/aipass/aipass_core/flow
```

---

### Direct Execution

#### `drone run python3 <module> [args]`
Execute Python modules with automatic path resolution.

**Arguments:**
- `<module>` - Module filename (e.g., `flow.py`, `seed.py`)
- `[args]` - Module arguments

**Usage:**
```bash
# Run flow module
drone run python3 flow.py close --all

# Run seed module
drone run python3 seed.py checklist

# Run with help flag
drone run python3 backup_system.py --help
```

**Path Resolution:**
Drone searches for modules in these locations:
- `~/*/apps/` (e.g., `~/seed/apps/seed.py`)
- `~/aipass_core/*/apps/` (e.g., `~/aipass_core/flow/apps/flow.py`)

**Example:**
```bash
$ drone run python3 flow.py list

-> python3 aipass_core/flow/apps/flow.py list

# Output from flow.py list command...
```

**When to Use:**
- Testing modules directly without activation
- Running one-off commands
- Debugging module execution
- When you know the exact module filename

---

## Advanced Features

### Long-Running Commands
Drone automatically detects long-running commands and removes timeouts.

**Detected Commands:**
- `start` - Start services
- `run` - Run processes
- `watch` - File watching
- `monitor` - Monitoring operations
- `serve` - Server processes
- `daemon` - Daemon processes

**Example:**
```bash
# No timeout applied
drone @prax file watcher start

# No timeout applied
drone run python3 server.py start
```

---

### Command Validation
Drone validates all activated commands before execution:
- Module path exists
- Command is properly formatted
- Arguments are properly resolved
- Branch supports the command

---

### Registry Management
Drone maintains a centralized command registry:

**Registry Structure:**
```
drone/commands/
├── flow/
│   ├── registry.json    # All discovered commands
│   └── active.json      # Activated shortcuts
├── seed/
│   ├── registry.json
│   └── active.json
└── prax/
    ├── registry.json
    └── active.json
```

**Files:**
- `registry.json` - All commands discovered during scan
- `active.json` - User-activated command shortcuts

---

## Common Workflows

### First-Time Setup
```bash
# 1. See available systems
drone systems

# 2. Scan a branch
drone scan @flow

# 3. Activate commands (prompted automatically after scan)
# Select desired commands interactively

# 4. Verify activation
drone list

# 5. Use shortcuts
drone plan create @seed "My first task"
```

---

### Adding a New Branch
```bash
# 1. Scan the new branch
drone scan @newbranch

# 2. Review discovered commands
# (shown during scan)

# 3. Activate desired commands
# (prompted after scan, or run manually)
drone activate newbranch

# 4. Verify
drone list @newbranch
```

---

### Updating Branch Commands
```bash
# 1. Refresh the system
drone refresh @flow

# 2. Re-activate commands
drone activate flow

# 3. Verify changes
drone list flow
```

---

### Testing Branch Commands
```bash
# 1. Scan with --all flag to see full Python commands
drone scan @flow --all

# 2. Copy and test commands directly
python3 /home/aipass/aipass_core/flow/apps/flow.py list

# 3. Or use direct branch access
drone @flow list

# 4. Or use activated shortcuts
drone plan list
```

---

## Tips & Best Practices

### Use @ Prefix for Clarity
Always use `@branch` notation when referencing branches in arguments:
```bash
# Good
drone plan create @seed "Task description"
drone seed audit @flow

# Avoid (may work but less explicit)
drone plan create seed "Task description"
```

---

### Leverage Multi-Word Shortcuts
Use descriptive multi-word shortcuts for clarity:
```bash
# Activate as: "plan create", "plan list", "plan close"
# Instead of: "create", "list", "close"

drone plan create @seed "My task"    # Clear what this does
drone create @seed "My task"          # Less clear
```

---

### Check Help First
Every branch provides help via the `@branch --help` pattern:
```bash
drone @flow --help
drone @seed --help
drone @prax --help
```

---

### Use Systems Command
Regularly check `drone systems` to see what's registered:
```bash
drone systems
```

---

### Scan with --all for Debugging
When testing or debugging, use `--all` to see full Python commands:
```bash
drone scan @flow --all

# Copy the Python command and test directly:
python3 /home/aipass/aipass_core/flow/apps/flow.py list
```

---

## Error Handling

### Unknown Command
If drone doesn't recognize a command, it suggests using `@` prefix:
```bash
$ drone foobar

Unknown command: foobar

Tip: Use @ for branch access: drone @foobar ...

Run drone --help for available commands
```

---

### Module Not Found (@ access)
If a branch module isn't found:
```bash
$ drone @nonexistent help

Error: Branch module not found at /home/aipass/aipass_core/nonexistent/apps/nonexistent.py
```

---

### Invalid Scan Target
Scan requires `@` prefix:
```bash
$ drone scan flow

Usage: drone scan @module [--all]

Got: 'flow' (missing @ prefix)

Examples:
  drone scan @devpulse
  drone scan @flow --all
```

---

## Command Summary

| Command | Purpose | Example |
|---------|---------|---------|
| `drone` | Show introspection | `drone` |
| `drone help` | Display help | `drone help` |
| `drone systems` | List registered systems | `drone systems` |
| `drone scan @branch` | Scan & register branch | `drone scan @flow` |
| `drone activate <sys>` | Activate shortcuts | `drone activate flow` |
| `drone list [sys]` | List shortcuts | `drone list flow` |
| `drone edit` | Edit shortcut | `drone edit` |
| `drone remove <cmd>` | Remove shortcut | `drone remove plan` |
| `drone refresh @sys` | Refresh system | `drone refresh @flow` |
| `drone @branch cmd` | Direct branch access | `drone @flow list` |
| `drone @branch/mod` | Nested module access | `drone @seed/imports audit` |
| `drone <shortcut>` | Use activated shortcut | `drone plan create` |
| `drone run python3` | Execute module directly | `drone run python3 flow.py` |

---

## Quick Reference Card

```
DISCOVERY:
  drone systems              List all registered branches
  drone scan @branch         Scan and register branch commands
  drone list [system]        List activated shortcuts

ACTIVATION:
  drone activate <system>    Activate commands interactively
  drone edit                 Edit activated shortcut
  drone remove <command>     Remove activated shortcut
  drone refresh @system      Re-scan system for updates

ROUTING:
  drone @branch cmd [args]   Direct branch access
  drone @branch/module       Nested module access
  drone <shortcut> [args]    Use activated shortcut
  drone run python3 <mod>    Execute module directly

HELP:
  drone help                 Show this guide
  drone @branch --help       Branch-specific help
  drone systems              Show available systems
```

---

## Related Documentation

- **README.md** - Branch overview and architecture
- **DRONE.id.json** - Branch identity
- **DRONE.local.json** - Session history
- **/home/aipass/standards/CODE_STANDARDS/** - System standards

---

*Generated for Drone v3.0+ - Command Router & Discovery System*
