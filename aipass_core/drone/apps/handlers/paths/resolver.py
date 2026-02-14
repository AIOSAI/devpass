#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: resolver.py - Path Resolution Handler
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/handlers/paths
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-29): Initial - path resolution implementation
#
# CODE STANDARDS:
#   - Handler pattern - pure implementation, no CLI
#   - Stateless functions for @ resolution
# =============================================

"""
Path Resolution Handler - Implementation for @ target resolution.

Pure functions - no CLI output, no state.
"""

import sys
from pathlib import Path
from typing import Union, Optional
import json

# =============================================================================
# INFRASTRUCTURE SETUP
# =============================================================================

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

AIPASS_HOME = Path.home()

# Special reserved targets
RESERVED_TARGETS = {
    "@": AIPASS_HOME,
    "@all": "@all",
}

# =============================================================================
# PATH RESOLUTION
# =============================================================================

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
    if not target.startswith("@"):
        path = Path(target)
        if path.exists():
            return path
        raise ValueError(f"Path does not exist: {target}")

    if target in RESERVED_TARGETS:
        return RESERVED_TARGETS[target]

    branch_name = target[1:].lower()

    # Handle path-like targets: @flow/apps/flow.py
    if "/" in branch_name:
        parts = branch_name.split("/", 1)
        base_branch = parts[0]
        sub_path = parts[1]
        branch_path = get_branch_path(base_branch)
        full_path = branch_path / sub_path
        if full_path.exists():
            return full_path
        raise ValueError(f"Path does not exist: {target}")

    return get_branch_path(branch_name)


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
    branch_name = branch_name.lower()

    registry = _load_branch_registry()

    for branch in registry.get("branches", []):
        if branch.get("name", "").lower() == branch_name:
            path = Path(branch["path"])
            if path.exists():
                return path
        email = branch.get("email", "").lower()
        if email == f"@{branch_name}" or email == branch_name:
            path = Path(branch["path"])
            if path.exists():
                return path

    # Fallback: standard locations
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

    Uses registry as source of truth. No fallback guessing.

    Args:
        arg: Path string or @target

    Returns:
        Uppercase branch name

    Raises:
        ValueError: If path doesn't match any registered branch
    """
    if arg.startswith("@"):
        if arg == "@all":
            return "ALL"
        return arg[1:].upper()

    if arg.startswith("/"):
        # Use registry to find branch by path - no guessing
        registry = _load_branch_registry()
        path = Path(arg).resolve()

        for branch in registry.get("branches", []):
            branch_path = Path(branch.get("path", "")).resolve()
            if path == branch_path:
                return branch.get("name", "").upper()

        # No match found - fail with clear error
        raise ValueError(f"Path '{arg}' does not match any registered branch. Check BRANCH_REGISTRY.json")

    return arg.upper()


def get_module_path(branch_name: str) -> Optional[Path]:
    """
    Get the main module path for a branch.

    Args:
        branch_name: Branch name (case-insensitive)

    Returns:
        Path to main module or None if not found
    """
    try:
        branch_path = get_branch_path(branch_name)
    except ValueError:
        return None

    module_path = branch_path / "apps" / f"{branch_name.lower()}.py"
    if module_path.exists():
        return module_path

    apps_dir = branch_path / "apps"
    if apps_dir.exists():
        for py_file in apps_dir.glob("*.py"):
            if py_file.stem != "__init__":
                return py_file

    return None


def branch_exists(branch_name: str) -> bool:
    """
    Check if a branch exists by name.

    Args:
        branch_name: Branch name (case-insensitive)

    Returns:
        True if branch exists, False otherwise
    """
    try:
        get_branch_path(branch_name)
        return True
    except ValueError:
        return False


# =============================================================================
# PRIVATE HELPERS
# =============================================================================

def _load_branch_registry() -> dict:
    """Load BRANCH_REGISTRY.json from AIPASS_HOME."""
    registry_path = AIPASS_HOME / "BRANCH_REGISTRY.json"
    if registry_path.exists():
        try:
            return json.loads(registry_path.read_text())
        except (json.JSONDecodeError, IOError):
            return {"branches": []}
    return {"branches": []}


# =============================================================================
# HIGH-LEVEL API
# =============================================================================

def resolve(target: str) -> Union[dict, list]:
    """
    High-level resolution - returns complete branch info.

    This is the primary API for branches to use drone services.
    No need to understand internals - just call resolve().

    Args:
        target: "@flow", "flow", "@all", or path

    Returns:
        For single target: dict with name, path, email, exists, module_path
        For "@all": list of all branch dicts

    Examples:
        resolve("@flow") → {"name": "FLOW", "path": Path(...), ...}
        resolve("flow")  → same (@ is optional)
        resolve("@all")  → [{"name": "FLOW", ...}, {"name": "SEED", ...}]
    """
    # Handle @all - return all branches
    if target == "@all" or target == "all":
        return _get_all_branches_info()

    # Normalize target
    if not target.startswith("@") and not target.startswith("/"):
        target = f"@{target}"

    # Build branch info dict
    try:
        if target.startswith("/"):
            # Path target
            path = Path(target)
            branch_name = normalize_branch_arg(target)
            return {
                "name": branch_name,
                "path": path if path.exists() else None,
                "email": f"@{branch_name.lower()}",
                "exists": path.exists(),
                "module_path": get_module_path(branch_name),
                "status": "active" if path.exists() else "not_found",
            }

        # @ target
        branch_name = normalize_branch_arg(target)
        branch_path = get_branch_path(branch_name.lower())

        return {
            "name": branch_name,
            "path": branch_path,
            "email": f"@{branch_name.lower()}",
            "exists": True,
            "module_path": get_module_path(branch_name.lower()),
            "status": "active",
        }

    except ValueError as e:
        # Branch not found
        branch_name = target[1:].upper() if target.startswith("@") else target.upper()
        return {
            "name": branch_name,
            "path": None,
            "email": f"@{branch_name.lower()}",
            "exists": False,
            "module_path": None,
            "status": "not_found",
            "error": str(e),
        }


def _get_all_branches_info() -> list:
    """Get all branches with full info."""
    registry = _load_branch_registry()
    branches = []

    for branch in registry.get("branches", []):
        name = branch.get("name", "")
        path_str = branch.get("path", "")
        path = Path(path_str) if path_str else None

        branches.append({
            "name": name.upper() if name else "UNKNOWN",
            "path": path,
            "email": branch.get("email", f"@{name.lower()}"),
            "exists": path.exists() if path else False,
            "module_path": get_module_path(name.lower()) if name else None,
            "status": branch.get("status", "active"),
        })

    return branches
