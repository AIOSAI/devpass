#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: lookup.py - Branch Registry Lookup Handler
# Date: 2025-11-29
# Version: 1.0.0
# Category: drone/handlers/branch_registry
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-29): Initial - branch registry lookups
#
# CODE STANDARDS:
#   - Handler pattern - pure implementation, no CLI
#   - Independent, transportable unit
# =============================================

"""
Branch Registry Lookup Handler - Implementation for branch metadata lookups.

Pure functions - no CLI output, no external dependencies.
"""

from pathlib import Path
from typing import Dict, List, Optional
import json

# =============================================================================
# CONSTANTS
# =============================================================================

AIPASS_HOME = Path.home()
AIPASS_ROOT = AIPASS_HOME / "aipass_core"
REGISTRY_PATH = AIPASS_HOME / "BRANCH_REGISTRY.json"

# =============================================================================
# BRANCH LOOKUPS
# =============================================================================

def get_all_branches() -> List[Dict]:
    """
    Get all registered branches.

    Returns:
        List of branch dicts with name, path, email, etc.
    """
    registry = _load_registry()
    return registry.get("branches", [])


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


def get_branch_by_name(name: str) -> Optional[Dict]:
    """
    Find branch by name.

    Args:
        name: Branch name (case-insensitive)

    Returns:
        Branch dict or None if not found
    """
    name = name.lower()
    for branch in get_all_branches():
        if branch.get("name", "").lower() == name:
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


def list_branch_names() -> List[str]:
    """
    Get list of all branch names.

    Returns:
        List of branch names (lowercase)
    """
    return [b.get("name", "").lower() for b in get_all_branches() if b.get("name")]


def list_branch_emails() -> List[str]:
    """
    Get list of all branch emails.

    Returns:
        List of branch emails (e.g., ["@flow", "@seed", ...])
    """
    return [b.get("email", "") for b in get_all_branches() if b.get("email")]


def list_systems() -> Dict[str, Dict]:
    """
    Get all systems with their module paths.

    Returns:
        Dict mapping system name to info dict
    """
    systems = {}
    for branch in get_all_branches():
        name = branch.get("name", "").lower()
        if name:
            systems[name] = {
                "path": branch.get("path"),
                "email": branch.get("email"),
                "module_path": _find_module_path(branch.get("path") or ""),
                "status": branch.get("status", "unknown"),
            }
    return systems


def get_registry_metadata() -> Dict:
    """
    Get registry metadata (version, last_updated, etc).

    Returns:
        Metadata dict
    """
    registry = _load_registry()
    return registry.get("metadata", {})


# =============================================================================
# PRIVATE HELPERS
# =============================================================================

def _load_registry() -> dict:
    """Load BRANCH_REGISTRY.json."""
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text())
        except (json.JSONDecodeError, IOError):
            return {"branches": [], "metadata": {}}
    return {"branches": [], "metadata": {}}


def _find_module_path(branch_path: str) -> Optional[str]:
    """Find main module path for a branch."""
    if not branch_path:
        return None

    path = Path(branch_path)
    apps_dir = path / "apps"

    if not apps_dir.exists():
        return None

    # Standard pattern: apps/<branch_name>.py
    branch_name = path.name.lower()
    standard_path = apps_dir / f"{branch_name}.py"
    if standard_path.exists():
        return str(standard_path)

    # Fallback: first non-__init__ .py file
    for py_file in sorted(apps_dir.glob("*.py")):
        if py_file.stem != "__init__":
            return str(py_file)

    return None
