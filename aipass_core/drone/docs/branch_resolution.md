# Drone Branch Resolution System

Technical documentation for Drone's branch resolution and registry lookup system.

---

## Overview

Drone provides centralized branch resolution, converting friendly names like `@flow` or `flow` into absolute paths before passing them to modules. This allows all branches to reference each other consistently without hardcoding paths.

**Core Capability:** Any branch can resolve any other branch's location using simple @ notation.

---

## BRANCH_REGISTRY.json

The central source of truth for all AIPass branches, located at `/home/aipass/BRANCH_REGISTRY.json`.

### Structure

```json
{
  "metadata": {
    "version": "1.0.0",
    "last_updated": "2025-11-27",
    "total_branches": 18
  },
  "branches": [
    {
      "name": "FLOW",
      "path": "/home/aipass/aipass_core/flow",
      "profile": "AIPass Workshop",
      "description": "New branch - purpose TBD",
      "email": "@flow",
      "status": "active",
      "created": "2025-10-30",
      "last_active": "2025-10-30"
    }
  ]
}
```

### Fields

- **name**: Uppercase branch identifier (e.g., "FLOW", "SEED")
- **path**: Absolute filesystem path to branch directory
- **profile**: VSCode profile association
- **description**: Human-readable purpose
- **email**: @ notation identifier (e.g., "@flow")
- **status**: active | inactive | archived
- **created**: ISO date of branch creation
- **last_active**: ISO date of last known activity

---

## Branch Lookup Functions

All lookup functions are located in `/home/aipass/aipass_core/drone/apps/handlers/branch_registry/lookup.py`.

### Import Pattern

```python
from drone.apps.modules.branch_registry import (
    get_all_branches,
    get_branch_by_email,
    get_branch_by_name,
    get_branch_by_path,
    list_branch_names,
    list_branch_emails,
    list_systems,
    get_registry_metadata,
)
```

### Function Signatures

#### get_all_branches()

```python
def get_all_branches() -> List[Dict]:
    """
    Get all registered branches.

    Returns:
        List of branch dicts with name, path, email, etc.
    """
```

**Example:**
```python
branches = get_all_branches()
# Returns: [
#   {"name": "FLOW", "path": "/home/aipass/aipass_core/flow", "email": "@flow", ...},
#   {"name": "SEED", "path": "/home/aipass/seed", "email": "@seed", ...},
#   ...
# ]
```

#### get_branch_by_email(email: str)

```python
def get_branch_by_email(email: str) -> Optional[Dict]:
    """
    Find branch by email address.

    Args:
        email: Email like "@flow" or "flow" (@ is optional)

    Returns:
        Branch dict or None if not found
    """
```

**Example:**
```python
flow = get_branch_by_email("@flow")  # With @
flow = get_branch_by_email("flow")   # Without @
# Returns: {"name": "FLOW", "path": "/home/aipass/aipass_core/flow", ...}
```

#### get_branch_by_name(name: str)

```python
def get_branch_by_name(name: str) -> Optional[Dict]:
    """
    Find branch by name (case-insensitive).

    Args:
        name: Branch name like "flow", "FLOW", "Flow"

    Returns:
        Branch dict or None if not found
    """
```

**Example:**
```python
seed = get_branch_by_name("seed")   # Case-insensitive
seed = get_branch_by_name("SEED")   # Same result
# Returns: {"name": "SEED", "path": "/home/aipass/seed", ...}
```

#### get_branch_by_path(path: Path)

```python
def get_branch_by_path(path: Path) -> Optional[Dict]:
    """
    Find branch by directory path.

    Args:
        path: Absolute path to branch directory

    Returns:
        Branch dict or None if not found
    """
```

**Example:**
```python
from pathlib import Path

drone = get_branch_by_path(Path("/home/aipass/aipass_core/drone"))
# Returns: {"name": "DRONE", "path": "/home/aipass/aipass_core/drone", ...}
```

#### list_branch_names()

```python
def list_branch_names() -> List[str]:
    """
    Get list of all branch names (lowercase).

    Returns:
        List of branch names
    """
```

**Example:**
```python
names = list_branch_names()
# Returns: ["flow", "seed", "drone", "prax", ...]
```

#### list_branch_emails()

```python
def list_branch_emails() -> List[str]:
    """
    Get list of all branch emails.

    Returns:
        List of branch emails
    """
```

**Example:**
```python
emails = list_branch_emails()
# Returns: ["@flow", "@seed", "@drone", "@prax", ...]
```

#### list_systems()

```python
def list_systems() -> Dict[str, Dict]:
    """
    Get all systems with their module paths.

    Returns:
        Dict mapping system name to info dict
    """
```

**Example:**
```python
systems = list_systems()
# Returns: {
#   "flow": {
#     "path": "/home/aipass/aipass_core/flow",
#     "email": "@flow",
#     "module_path": "/home/aipass/aipass_core/flow/apps/flow.py",
#     "status": "active"
#   },
#   ...
# }
```

#### get_registry_metadata()

```python
def get_registry_metadata() -> Dict:
    """
    Get registry metadata (version, last_updated, etc).

    Returns:
        Metadata dict
    """
```

**Example:**
```python
meta = get_registry_metadata()
# Returns: {
#   "version": "1.0.0",
#   "last_updated": "2025-11-27",
#   "total_branches": 18
# }
```

---

## Path Resolution Functions

All path resolution functions are located in `/home/aipass/aipass_core/drone/apps/handlers/paths/resolver.py`.

### Import Pattern

```python
from drone.apps.modules.paths import (
    resolve,
    resolve_target,
    get_branch_path,
    normalize_branch_arg,
    get_module_path,
    branch_exists,
)
```

### Function Signatures

#### resolve_target(target: str)

```python
def resolve_target(target: str) -> Union[Path, str]:
    """
    Resolve @ target to absolute path.

    Args:
        target: String like "@flow", "@seed", "@", "@all"

    Returns:
        Path object or "@all" string for special handling

    Raises:
        ValueError: If target cannot be resolved
    """
```

**Example:**
```python
path = resolve_target("@flow")
# Returns: Path("/home/aipass/aipass_core/flow")

path = resolve_target("@seed")
# Returns: Path("/home/aipass/seed")

path = resolve_target("@")
# Returns: Path("/home/aipass")

all_marker = resolve_target("@all")
# Returns: "@all" (special marker for branch-specific handling)

# Path-like targets (subpaths)
path = resolve_target("@flow/apps/flow.py")
# Returns: Path("/home/aipass/aipass_core/flow/apps/flow.py")
```

#### get_branch_path(branch_name: str)

```python
def get_branch_path(branch_name: str) -> Path:
    """
    Get absolute path for a branch by name.

    Args:
        branch_name: Branch name (case-insensitive)

    Returns:
        Absolute Path to branch directory

    Raises:
        ValueError: If branch not found
    """
```

**Example:**
```python
flow_path = get_branch_path("flow")
# Returns: Path("/home/aipass/aipass_core/flow")

seed_path = get_branch_path("SEED")  # Case-insensitive
# Returns: Path("/home/aipass/seed")
```

**Resolution Strategy:**
1. Check BRANCH_REGISTRY.json for exact name match
2. Check BRANCH_REGISTRY.json for email match
3. Fallback to standard locations:
   - `/home/aipass/aipass_core/{branch_name}`
   - `/home/aipass/{branch_name}`
4. Raise ValueError if not found

#### normalize_branch_arg(arg: str)

```python
def normalize_branch_arg(arg: str) -> str:
    """
    Convert path or @target to uppercase branch name.

    Args:
        arg: Path string or @target

    Returns:
        Uppercase branch name
    """
```

**Example:**
```python
name = normalize_branch_arg("@flow")
# Returns: "FLOW"

name = normalize_branch_arg("/home/aipass/aipass_core/flow")
# Returns: "FLOW"

name = normalize_branch_arg("/home/aipass/seed")
# Returns: "SEED"

name = normalize_branch_arg("@all")
# Returns: "ALL"
```

**Conversion Logic:**
- `@flow` → Extract after @, uppercase → "FLOW"
- `@all` → Special case → "ALL"
- `/home/aipass/aipass_core/flow` → Extract "flow" after "aipass_core", uppercase → "FLOW"
- `/home/aipass/seed` → Extract "seed" after "aipass", uppercase → "SEED"
- Other paths → Use directory name, uppercase

#### get_module_path(branch_name: str)

```python
def get_module_path(branch_name: str) -> Optional[Path]:
    """
    Get the main module path for a branch.

    Args:
        branch_name: Branch name (case-insensitive)

    Returns:
        Path to main module or None if not found
    """
```

**Example:**
```python
module = get_module_path("flow")
# Returns: Path("/home/aipass/aipass_core/flow/apps/flow.py")

module = get_module_path("seed")
# Returns: Path("/home/aipass/seed/apps/seed.py")
```

**Discovery Strategy:**
1. Look for standard pattern: `apps/{branch_name}.py`
2. Fallback: First non-`__init__` .py file in apps directory
3. Return None if apps directory doesn't exist

#### branch_exists(branch_name: str)

```python
def branch_exists(branch_name: str) -> bool:
    """
    Check if a branch exists by name.

    Args:
        branch_name: Branch name (case-insensitive)

    Returns:
        True if branch exists, False otherwise
    """
```

**Example:**
```python
if branch_exists("flow"):
    print("Flow exists!")

if not branch_exists("nonexistent"):
    print("Branch not found")
```

#### resolve(target: str)

High-level resolution API that returns complete branch information.

```python
def resolve(target: str) -> Union[dict, list]:
    """
    High-level resolution - returns complete branch info.

    Args:
        target: "@flow", "flow", "@all", or path

    Returns:
        For single target: dict with name, path, email, exists, module_path
        For "@all": list of all branch dicts
    """
```

**Example:**
```python
# Single branch
info = resolve("@flow")
# Returns: {
#   "name": "FLOW",
#   "path": Path("/home/aipass/aipass_core/flow"),
#   "email": "@flow",
#   "exists": True,
#   "module_path": Path("/home/aipass/aipass_core/flow/apps/flow.py"),
#   "status": "active"
# }

# @ is optional
info = resolve("flow")  # Same as "@flow"

# All branches
all_branches = resolve("@all")
# Returns: [
#   {"name": "FLOW", "path": Path(...), ...},
#   {"name": "SEED", "path": Path(...), ...},
#   ...
# ]

# Not found
info = resolve("@nonexistent")
# Returns: {
#   "name": "NONEXISTENT",
#   "path": None,
#   "email": "@nonexistent",
#   "exists": False,
#   "module_path": None,
#   "status": "not_found",
#   "error": "Branch not found: nonexistent"
# }
```

---

## @ Notation Resolution

### How @branch Resolves to Paths

The @ notation is Drone's core abstraction for branch references. All @ arguments are resolved to absolute paths BEFORE passing to modules.

#### Reserved Targets

```python
RESERVED_TARGETS = {
    "@": Path("/home/aipass"),              # AIPass home
    "@all": "@all",                          # Special marker (not resolved)
}
```

#### Resolution Flow

```
User Input: @flow
    ↓
1. Check if starts with @ → Yes
2. Check reserved targets → No
3. Extract branch name → "flow"
4. Check for path separator → No
5. Call get_branch_path("flow")
    ↓
6. Search BRANCH_REGISTRY.json
    ↓
7. Find match: {"name": "FLOW", "path": "/home/aipass/aipass_core/flow", ...}
    ↓
8. Return Path("/home/aipass/aipass_core/flow")
```

#### Subpath Resolution

```
User Input: @flow/apps/flow.py
    ↓
1. Check if starts with @ → Yes
2. Extract branch name → "flow"
3. Detect path separator → Yes
4. Split into base ("flow") and subpath ("apps/flow.py")
5. Resolve base → Path("/home/aipass/aipass_core/flow")
6. Join with subpath → Path("/home/aipass/aipass_core/flow/apps/flow.py")
7. Verify exists → Yes
8. Return Path("/home/aipass/aipass_core/flow/apps/flow.py")
```

### Common Resolution Examples

```python
# Branch references
"@flow"     → Path("/home/aipass/aipass_core/flow")
"@seed"     → Path("/home/aipass/seed")
"@drone"    → Path("/home/aipass/aipass_core/drone")
"@prax"     → Path("/home/aipass/aipass_core/prax")
"@ai_mail"  → Path("/home/aipass/aipass_core/ai_mail")

# Special targets
"@"         → Path("/home/aipass")
"@all"      → "@all" (passed as-is to modules)

# Subpaths
"@flow/apps"              → Path("/home/aipass/aipass_core/flow/apps")
"@seed/README.md"         → Path("/home/aipass/seed/README.md")
"@drone/apps/drone.py"    → Path("/home/aipass/aipass_core/drone/apps/drone.py")

# Case-insensitive
"@FLOW"     → Path("/home/aipass/aipass_core/flow")
"@Flow"     → Path("/home/aipass/aipass_core/flow")
"@flow"     → Path("/home/aipass/aipass_core/flow")
```

---

## normalize_branch_arg Pattern

The `normalize_branch_arg()` function is the inverse of path resolution - it converts paths or @ targets back to uppercase branch names. This is commonly used in CLI tools and logging.

### Pattern

```python
def normalize_branch_arg(arg: str) -> str:
    """Convert various branch reference formats to uppercase name."""
```

### Use Cases

1. **CLI Argument Normalization** - Convert user input to consistent format
2. **Logging** - Display branch names consistently in logs
3. **Comparison** - Normalize before comparing branch references
4. **Display** - Show user-friendly branch names

### Examples

```python
# @ notation
normalize_branch_arg("@flow")     # → "FLOW"
normalize_branch_arg("@seed")     # → "SEED"
normalize_branch_arg("@all")      # → "ALL"

# Full paths
normalize_branch_arg("/home/aipass/aipass_core/flow")    # → "FLOW"
normalize_branch_arg("/home/aipass/seed")                # → "SEED"
normalize_branch_arg("/home/aipass/aipass_core/drone")   # → "DRONE"

# Plain names
normalize_branch_arg("flow")      # → "FLOW"
normalize_branch_arg("seed")      # → "SEED"
```

### Implementation Logic

```python
if arg.startswith("@"):
    if arg == "@all":
        return "ALL"
    return arg[1:].upper()  # Remove @, uppercase

if arg.startswith("/"):
    path = Path(arg)
    # Extract branch name from path structure
    if "aipass_core" in path.parts:
        idx = path.parts.index("aipass_core")
        return path.parts[idx + 1].upper()  # Next part after aipass_core
    if "aipass" in path.parts:
        idx = path.parts.index("aipass")
        return path.parts[idx + 1].upper()  # Next part after aipass
    return path.name.upper()  # Use directory name

return arg.upper()  # Plain name
```

---

## Registered Branches

Current branches registered in BRANCH_REGISTRY.json (as of 2025-11-27):

| Name | Path | Email |
|------|------|-------|
| .VSCODE | /home/aipass/.vscode | @.vscode |
| AIPASS | /home/aipass | @aipass |
| AIPASS_CORE | /home/aipass/aipass_core | @aipass_core |
| AI_MAIL | /home/aipass/aipass_core/ai_mail | @ai_mail |
| API | /home/aipass/aipass_core/api | @api |
| BACKUP_SYSTEM | /home/aipass/aipass_core/backup_system | @backup_system |
| CLI | /home/aipass/aipass_core/cli | @cli |
| CORTEX | /home/aipass/aipass_core/cortex | @cortex |
| DEVPULSE | /home/aipass/aipass_core/devpulse | @devpulse |
| DRONE | /home/aipass/aipass_core/drone | @drone |
| FLOW | /home/aipass/aipass_core/flow | @flow |
| GIT_REPO | /home/aipass/aipass_os/dev_central/git_repo | @git_repo |
| MCP_SERVERS | /home/aipass/mcp_servers | @mcp_servers |
| MEMORY_BANK | /home/aipass/MEMORY_BANK | @memory_bank |
| PERMISSIONS | /home/aipass/aipass_os/dev_central/permissions | @permissions |
| PRAX | /home/aipass/aipass_core/prax | @prax |
| PROJECTS | /home/aipass/projects | @projects |
| SEED | /home/aipass/seed | @seed |

**Total:** 18 branches

---

## Integration Examples

### Example 1: Resolve Branch in Another Module

```python
from drone.apps.modules.paths import resolve_target

def process_branch(branch_arg: str):
    """Process a branch by @ reference or path."""
    try:
        branch_path = resolve_target(branch_arg)
        print(f"Processing: {branch_path}")
        # Do work with branch_path
    except ValueError as e:
        print(f"Error: {e}")

# Usage
process_branch("@flow")     # Works with @ notation
process_branch("flow")      # @ is optional in resolve_target
```

### Example 2: Lookup Branch Metadata

```python
from drone.apps.modules.branch_registry import get_branch_by_email

def send_message_to_branch(email: str, message: str):
    """Send message to a branch by email."""
    branch = get_branch_by_email(email)
    if not branch:
        print(f"Branch not found: {email}")
        return

    print(f"Sending to {branch['name']} at {branch['path']}")
    # Send message logic here

# Usage
send_message_to_branch("@flow", "Hello Flow!")
```

### Example 3: List All Active Branches

```python
from drone.apps.modules.branch_registry import get_all_branches

def list_active_branches():
    """List all active branches."""
    branches = get_all_branches()
    active = [b for b in branches if b.get("status") == "active"]

    for branch in active:
        print(f"{branch['email']:20} → {branch['path']}")

# Output:
# @flow                → /home/aipass/aipass_core/flow
# @seed                → /home/aipass/seed
# ...
```

### Example 4: Using High-Level resolve()

```python
from drone.apps.modules.paths import resolve

def get_branch_info(target: str):
    """Get complete branch information."""
    info = resolve(target)

    if not info.get("exists"):
        print(f"Branch not found: {target}")
        print(f"Error: {info.get('error', 'Unknown')}")
        return

    print(f"Name:   {info['name']}")
    print(f"Path:   {info['path']}")
    print(f"Email:  {info['email']}")
    print(f"Module: {info.get('module_path', 'Not found')}")

# Usage
get_branch_info("@flow")
get_branch_info("seed")  # @ is optional
```

### Example 5: Normalize User Input

```python
from drone.apps.modules.paths import normalize_branch_arg

def display_branch_status(user_input: str):
    """Display status with normalized branch name."""
    branch_name = normalize_branch_arg(user_input)
    print(f"Status for {branch_name}: Active")

# Usage
display_branch_status("@flow")                           # → "Status for FLOW: Active"
display_branch_status("/home/aipass/seed")               # → "Status for SEED: Active"
display_branch_status("drone")                           # → "Status for DRONE: Active"
```

---

## Error Handling

### ValueError: Branch Not Found

```python
from drone.apps.modules.paths import resolve_target

try:
    path = resolve_target("@nonexistent")
except ValueError as e:
    print(f"Resolution failed: {e}")
    # Output: Resolution failed: Branch not found: nonexistent
```

### None Returns for Optional Lookups

```python
from drone.apps.modules.branch_registry import get_branch_by_email

branch = get_branch_by_email("@nonexistent")
if branch is None:
    print("Branch not found")
```

### Graceful Handling with resolve()

```python
from drone.apps.modules.paths import resolve

info = resolve("@nonexistent")
if not info.get("exists"):
    print(f"Branch not found: {info.get('error', 'Unknown error')}")
else:
    # Proceed with valid branch
    process_branch(info["path"])
```

---

## Architecture Notes

### Module Pattern

Drone follows the standard AIPass 3-layer architecture:

```
drone/
├── apps/
│   ├── drone.py              # Entry point
│   ├── modules/              # Thin API layer (orchestration)
│   │   ├── branch_registry.py
│   │   └── paths.py
│   └── handlers/             # Implementation details
│       ├── branch_registry/
│       │   ├── __init__.py
│       │   └── lookup.py     # Core lookup logic
│       └── paths/
│           ├── __init__.py
│           └── resolver.py   # Core resolution logic
```

**Design Principles:**
- **Modules** (API layer) - Re-export functions from handlers, minimal orchestration
- **Handlers** (implementation) - Pure functions, no CLI dependencies, transportable
- **Separation** - Module API stable, handlers can be refactored without breaking imports

### Stateless Design

All functions are stateless and side-effect-free:
- No global state modification
- No caching (loads fresh from BRANCH_REGISTRY.json each call)
- Thread-safe by design
- Predictable behavior

### Import Safety

The handlers can be imported by any branch:
```python
# Safe from anywhere
from drone.apps.modules.branch_registry import get_branch_by_email
from drone.apps.modules.paths import resolve_target
```

Infrastructure imports are isolated to avoid circular dependencies.

---

## Summary

Drone's branch resolution system provides:

1. **Centralized Registry** - Single source of truth for all branches
2. **Flexible Lookup** - By name, email, or path
3. **@ Notation** - User-friendly branch references
4. **Path Resolution** - Automatic conversion to absolute paths
5. **Normalization** - Consistent branch name handling
6. **Pure Functions** - Stateless, predictable, testable
7. **Error Handling** - Clear failures with helpful messages

This system allows all AIPass branches to reference each other without hardcoding paths, making the ecosystem flexible and maintainable.
