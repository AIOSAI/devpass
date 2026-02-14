# DRONE Service Transformation Plan

**Date:** 2025-11-29
**Status:** Planning
**Priority:** High - Architectural Foundation

---

## The Problem

Drone is fragile. Every few sessions, something breaks:
- Import order issues cause silent module discovery failures
- Path setup scattered across handlers creates race conditions
- Complex CLI routing adds layers where errors hide
- Module activation/registration adds state that can get corrupted

Meanwhile, **Prax and CLI never break**. Why?

---

## Why Prax & CLI Work

They're **pure service imports**:

```python
# Prax - just import and use
from prax.apps.modules.logger import system_logger as logger
logger.info("always works")

# CLI - just import and use
from cli.apps.modules import console, header, success
header("always works")
```

**Properties that make them stable:**
1. Stateless functions - no discovery, no activation
2. Single responsibility - logging or display
3. No complex routing - you import what you need
4. Path setup once at module level - not scattered in handlers
5. No silent failures - import works or throws immediately

---

## The Transformation

### Current Drone Architecture (Fragile)

```
drone.py (CLI entry)
├── Module discovery (can fail silently)
├── Command routing (complex matching logic)
├── @ resolution (in preprocess_args)
└── Activation system (stateful, can corrupt)

Other branches:
├── Call `drone @branch command` via subprocess
├── OR implement their own @ resolution (duplication)
└── OR hardcode paths (fragile)
```

### Target Drone Architecture (Stable)

```
drone/apps/modules/
├── paths.py          # Path resolution services
├── registry.py       # Branch registry lookups
└── __init__.py       # Clean public API

drone/apps/drone.py   # Thin CLI wrapper (human-facing only)
```

---

## Service API Design

### paths.py - Core Path Services

```python
"""
Drone Path Services - Importable by all branches

Usage:
    from drone.apps.modules.paths import resolve_target, get_branch_path
"""

from pathlib import Path
from typing import Optional, Union

AIPASS_HOME = Path.home()
AIPASS_ROOT = AIPASS_HOME / "aipass_core"

# Special targets
RESERVED_TARGETS = {
    "@": AIPASS_HOME,
    "@all": "@all",  # Pass through for branch-specific handling
}

def resolve_target(target: str) -> Union[Path, str]:
    """
    Resolve @ target to absolute path.

    Args:
        target: String like "@flow", "@seed", "@", "@all"

    Returns:
        Path object or "@all" string for special handling

    Examples:
        resolve_target("@flow") → Path("/home/aipass/aipass_core/flow")
        resolve_target("@seed") → Path("/home/aipass/seed")
        resolve_target("@") → Path("/home/aipass")
        resolve_target("@all") → "@all"
    """
    if not target.startswith("@"):
        # Not a target, return as-is (might be a path already)
        return Path(target) if "/" in target else target

    if target in RESERVED_TARGETS:
        return RESERVED_TARGETS[target]

    # Strip @ and resolve
    branch_name = target[1:].lower()
    return get_branch_path(branch_name)


def get_branch_path(branch_name: str) -> Path:
    """
    Get absolute path for a branch by name.

    Args:
        branch_name: Branch name (case-insensitive), e.g., "flow", "seed"

    Returns:
        Absolute Path to branch directory

    Raises:
        ValueError: If branch not found in registry
    """
    branch_name = branch_name.lower()

    # Check BRANCH_REGISTRY.json
    registry = _load_registry()

    for branch in registry.get("branches", []):
        if branch.get("name", "").lower() == branch_name:
            return Path(branch["path"])
        if branch.get("email", "").lower() == f"@{branch_name}":
            return Path(branch["path"])

    # Fallback: check standard locations
    standard_paths = [
        AIPASS_ROOT / branch_name,
        AIPASS_HOME / branch_name,
    ]

    for path in standard_paths:
        if path.exists():
            return path

    raise ValueError(f"Branch not found: {branch_name}")


def normalize_branch_arg(arg: str) -> str:
    """
    Convert path or @target to uppercase branch name.

    Args:
        arg: Path string or @target

    Returns:
        Uppercase branch name (e.g., "FLOW", "SEED")

    Examples:
        normalize_branch_arg("@flow") → "FLOW"
        normalize_branch_arg("/home/aipass/aipass_core/flow") → "FLOW"
        normalize_branch_arg("flow") → "FLOW"
    """
    if arg.startswith("@"):
        return arg[1:].upper()

    if arg.startswith("/"):
        parts = Path(arg).parts
        if "aipass_core" in parts:
            idx = parts.index("aipass_core")
            if idx + 1 < len(parts):
                return parts[idx + 1].upper()
        return Path(arg).name.upper()

    return arg.upper()


def _load_registry() -> dict:
    """Load BRANCH_REGISTRY.json"""
    registry_path = AIPASS_HOME / "BRANCH_REGISTRY.json"
    if registry_path.exists():
        import json
        return json.loads(registry_path.read_text())
    return {"branches": []}
```

### registry.py - Branch Information Services

```python
"""
Drone Registry Services - Branch metadata lookups

Usage:
    from drone.apps.modules.registry import get_all_branches, get_branch_by_email
"""

from pathlib import Path
from typing import Dict, List, Optional
import json

AIPASS_HOME = Path.home()
REGISTRY_PATH = AIPASS_HOME / "BRANCH_REGISTRY.json"


def get_all_branches() -> List[Dict]:
    """
    Get all registered branches.

    Returns:
        List of branch dicts with name, path, email, etc.
    """
    if REGISTRY_PATH.exists():
        data = json.loads(REGISTRY_PATH.read_text())
        return data.get("branches", [])
    return []


def get_branch_by_email(email: str) -> Optional[Dict]:
    """
    Find branch by email address.

    Args:
        email: Email like "@flow" or "flow"

    Returns:
        Branch dict or None if not found
    """
    email = email.lower()
    if not email.startswith("@"):
        email = f"@{email}"

    for branch in get_all_branches():
        if branch.get("email", "").lower() == email:
            return branch
    return None


def get_branch_by_path(path: Path) -> Optional[Dict]:
    """
    Find branch by directory path.

    Args:
        path: Absolute path to branch directory

    Returns:
        Branch dict or None if not found
    """
    path_str = str(path)
    for branch in get_all_branches():
        if branch.get("path") == path_str:
            return branch
    return None


def list_systems() -> Dict[str, Dict]:
    """
    Get all systems with their module paths.

    Returns:
        Dict mapping system name to info dict
    """
    # This replaces the complex drone systems command
    systems = {}
    for branch in get_all_branches():
        name = branch.get("name", "").lower()
        if name:
            systems[name] = {
                "path": branch.get("path"),
                "email": branch.get("email"),
                "module_path": _find_module_path(branch.get("path")),
            }
    return systems


def _find_module_path(branch_path: str) -> Optional[str]:
    """Find main module path for a branch."""
    if not branch_path:
        return None
    path = Path(branch_path)
    # Standard pattern: apps/<branch_name>.py
    candidates = list(path.glob("apps/*.py"))
    for c in candidates:
        if c.stem not in ["__init__"]:
            return str(c)
    return None
```

### __init__.py - Clean Public API

```python
"""
Drone Services - Import this for @ resolution and branch lookups

Usage:
    from drone.apps.modules import resolve_target, get_branch_path

    path = resolve_target("@flow")  # → Path object
    branches = get_all_branches()   # → List of dicts
"""

from .paths import (
    resolve_target,
    get_branch_path,
    normalize_branch_arg,
    AIPASS_HOME,
    AIPASS_ROOT,
)

from .registry import (
    get_all_branches,
    get_branch_by_email,
    get_branch_by_path,
    list_systems,
)

__all__ = [
    # Path services
    "resolve_target",
    "get_branch_path",
    "normalize_branch_arg",
    "AIPASS_HOME",
    "AIPASS_ROOT",
    # Registry services
    "get_all_branches",
    "get_branch_by_email",
    "get_branch_by_path",
    "list_systems",
]
```

---

## Migration Steps

### Phase 1: Create Service Layer (No Breaking Changes)

1. Create `drone/apps/modules/paths.py` with path services
2. Create `drone/apps/modules/registry.py` with registry services
3. Update `drone/apps/modules/__init__.py` with clean exports
4. Test services work independently

**Validation:**
```python
from drone.apps.modules import resolve_target
assert resolve_target("@flow") == Path("/home/aipass/aipass_core/flow")
```

### Phase 2: Refactor CLI to Use Services

1. Update `drone.py` to import from services
2. Remove duplicated logic (preprocess_args moves to paths.py)
3. CLI becomes thin wrapper calling service functions
4. Formatters call services for data, then format for display

### Phase 3: Update Other Branches

1. **ai_mail** - Replace custom @ resolution with `from drone.apps.modules import resolve_target`
2. **seed** - Replace `normalize_branch_arg` duplication with import
3. **flow** - Use services for plan location resolution
4. Remove scattered `AIPASS_HOME = Path.home()` from handlers - import from drone

### Phase 4: Cleanup

1. Remove activation system (no longer needed - direct imports)
2. Remove module discovery (branches import directly)
3. Archive old routing logic
4. Update documentation

---

## Benefits After Transformation

| Before | After |
|--------|-------|
| Silent import failures | Import works or throws immediately |
| Path setup in 50+ files | Path constants from one source |
| Complex module discovery | Direct imports |
| Activation state can corrupt | Stateless functions |
| `drone @branch command` subprocess | `from drone.apps.modules import x` |

---

## What CLI Keeps

Human-facing discovery commands stay as CLI:

```bash
drone systems          # → calls list_systems(), formats for terminal
drone help             # → shows usage
drone @branch --help   # → routes to branch help
```

But branches **never** call these - they import services directly.

---

## Risk Mitigation

1. **Backward Compatibility**: Keep old CLI working during transition
2. **Incremental**: Phase 1 adds services without removing anything
3. **Testing**: Each phase has validation criteria before proceeding
4. **Rollback**: Git history preserves old implementation

---

## Success Criteria

After transformation, this should work everywhere without issues:

```python
# Any branch, any handler, any module
from drone.apps.modules import resolve_target, get_branch_path

# Always works - no import order issues, no path problems
path = resolve_target("@flow")
```

And we should never again debug "why isn't drone discovering modules".

---

## Timeline Estimate

- Phase 1: 1 session (create services)
- Phase 2: 1 session (refactor CLI)
- Phase 3: 2-3 sessions (update branches incrementally)
- Phase 4: 1 session (cleanup)

Total: ~5-6 focused sessions

---

*This transformation converts drone from a fragile routing system to a stable service layer like prax and cli.*
