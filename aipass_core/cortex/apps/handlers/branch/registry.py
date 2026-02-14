#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: registry.py - Branch Registry Handler
# Date: 2025-11-04
# Version: 1.0.0
# Category: cortex/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-04): Extracted from branch_lib, branch registry functions
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Branch Registry Handler

Functions for managing the branch registry:
- Load and save registry
- Add/remove branch entries
- Find branch entries
- Register new branches
"""

# Standard library imports
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))

# from prax.apps.modules.logger import system_logger as logger
import logging
logger = logging.getLogger(__name__)

MODULE_NAME = "registry"


# =============================================================================
# REGISTRY OPERATIONS (JSON-BASED)
# =============================================================================

def get_branch_registry_path() -> Path:
    """
    Get path to JSON branch registry - single point of change for path migration

    Returns:
        Path to BRANCH_REGISTRY.json at /home/aipass/BRANCH_REGISTRY.json
    """
    registry_path = Path.home() / "BRANCH_REGISTRY.json"
    return registry_path


def load_registry() -> Dict:
    """
    Load branch registry from JSON file

    Returns:
        Dict containing registry data, or empty schema if file doesn't exist
    """
    registry_path = get_branch_registry_path()

    if not registry_path.exists():
        # Return empty schema
        return {
            "metadata": {
                "version": "1.0.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "total_branches": 0
            },
            "branches": []
        }

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"[{MODULE_NAME}] Failed to load registry: {e}")
        # Return empty schema on error
        return {
            "metadata": {
                "version": "1.0.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "total_branches": 0
            },
            "branches": []
        }


def save_registry(data: Dict) -> bool:
    """
    Save registry data to JSON file

    Args:
        data: Registry data dict

    Returns:
        True on success, False on error
    """
    registry_path = get_branch_registry_path()

    # Auto-update last_updated timestamp
    data["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    # Sort branches alphabetically by name
    if "branches" in data:
        data["branches"] = sorted(data["branches"], key=lambda b: b.get("name", ""))

    try:
        # Ensure parent directory exists
        registry_path.parent.mkdir(parents=True, exist_ok=True)

        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except (IOError, TypeError) as e:
        logger.error(f"[{MODULE_NAME}] Failed to save registry: {e}")
        return False


def find_branch_in_registry(branch_name: str) -> Optional[Dict]:
    """
    Find branch entry in registry by name

    Args:
        branch_name: Branch name to search for

    Returns:
        Branch entry dict if found, None otherwise
    """
    registry = load_registry()

    for branch in registry.get("branches", []):
        if branch.get("name") == branch_name:
            return branch

    return None


def add_registry_entry(entry: Dict) -> bool:
    """
    Add new branch entry to registry

    Args:
        entry: Branch entry dict with required fields

    Returns:
        True on success, False on error
    """
    # Validate required fields
    required_fields = ["name", "path", "profile", "description", "email"]
    for field in required_fields:
        if field not in entry:
            logger.error(f"[{MODULE_NAME}] Missing required field '{field}' in registry entry")
            return False

    # Load current registry
    registry = load_registry()

    # Check if already exists
    if find_branch_in_registry(entry["name"]):
        logger.warning(f"[{MODULE_NAME}] Branch '{entry['name']}' already registered")
        return False

    # Add created/last_active dates if not present
    today = datetime.now().strftime("%Y-%m-%d")
    if "created" not in entry:
        entry["created"] = today
    if "last_active" not in entry:
        entry["last_active"] = today
    if "status" not in entry:
        entry["status"] = "active"

    # Add to branches list
    registry["branches"].append(entry)

    # Update total count
    registry["metadata"]["total_branches"] = len(registry["branches"])

    # Save
    return save_registry(registry)


def remove_registry_entry(branch_name: str) -> bool:
    """
    Remove branch entry from registry

    Args:
        branch_name: Branch name to remove

    Returns:
        True if found and removed, False if not found
    """
    registry = load_registry()

    # Find and remove branch
    original_count = len(registry["branches"])
    registry["branches"] = [
        b for b in registry["branches"]
        if b.get("name") != branch_name
    ]

    if len(registry["branches"]) == original_count:
        # Branch not found
        return False

    # Update total count
    registry["metadata"]["total_branches"] = len(registry["branches"])

    # Save
    save_registry(registry)
    return True


def sync_branch_registry() -> Dict:
    """
    Synchronize BRANCH_REGISTRY.json with filesystem reality

    Scans filesystem for directories containing .id.json files and:
    - Removes stale entries (in registry but directory/ID file doesn't exist)
    - Adds missing entries (ID file exists but not in registry)

    Returns:
        Dict with sync results:
            - removed: List of branch names removed (stale entries)
            - added: List of branch names added (new discoveries)
            - kept: List of branch names that were already correct
    """
    import json

    # Load current registry
    registry = load_registry()

    # Track changes
    sync_results = {
        "removed": [],
        "added": [],
        "kept": []
    }

    # Define directories to skip during branch discovery
    # NOTE: These are SYSTEM/CACHE directories that will NEVER contain branches
    # DO NOT include aipass_dev, aipass_core, etc. - those ARE branch locations!
    ignore_dirs = {
        # Backup/archive directories
        ".backup", "backups", "deleted_branches", ".archive",
        # Python
        ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", "*.egg-info",
        # Node/JS
        "node_modules", ".npm", ".npm-global", ".nvm",
        # Build/dist
        "dist", "build",
        # System directories (Desktop, Documents, etc.)
        "Desktop", "Documents", "Downloads", "Music", "Pictures", "Public", "Videos", "Templates",
        # Config/cache directories
        ".cache", ".config", ".local", ".mozilla", ".thunderbird", ".gnome", ".var",
        ".cargo", ".dotnet", ".java", ".pylint.d", ".pyenv", ".pki", ".ssh",
        ".vscode-server", ".claude", ".claude-code-docs",
        # Logs/temp
        "logs", "crash-logs", "system_logs",
        # Other
        "snap", "dropbox", ".dbus", ".gnupg", ".idlerc", ".wget-hsts",
        "mcp_servers",  # MCP servers dir - not a branch location
        "sandbox"
    }

    # Scan filesystem for all .id.json files (these indicate branch directories)
    search_roots = [
        Path.home(),  # /home/aipass
        Path.home() / "aipass_core"  # /home/aipass/aipass_core
    ]

    discovered_branches = {}  # path -> branch_name mapping

    for root in search_roots:
        if not root.exists():
            continue

        # Walk directory tree manually to skip ignored dirs early (much faster than rglob)
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            # Skip ignored directories during walk (don't even traverse them)
            # NOTE: Only filter specific dirs in ignore_dirs (which includes system dotdirs)
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]

            # Check for .id.json files in current directory
            for filename in filenames:
                if not filename.endswith('.id.json'):
                    continue

                branch_dir = Path(dirpath)
                path_str = str(branch_dir)

                # Additional filtering (archives, deleted)
                if '.archive' in path_str or 'archived' in path_str.lower():
                    continue
                if '_DELETED_' in branch_dir.name or '_deleted_' in path_str:
                    continue

                # Extract branch name from directory
                branch_name = branch_dir.name
                branchname_upper = branch_name.upper().replace("-", "_")

                discovered_branches[str(branch_dir)] = {
                    "path": str(branch_dir),
                    "name": branchname_upper,
                    "branch_name_lower": branch_name.lower().replace("-", "_")
                }
                break  # Only need one .id.json per directory

    # Step 1: Remove stale entries (in registry but not on filesystem)
    current_branches = registry.get("branches", [])
    valid_branches = []

    for branch in current_branches:
        branch_path = branch.get("path")
        branch_name = branch.get("name")

        # Check if directory exists
        if not Path(branch_path).exists():
            sync_results["removed"].append(branch_name)
            continue

        # Skip deleted/archived branches (filter same as discovery)
        path_str = str(branch_path)
        if '_DELETED_' in branch_name or 'deleted_branches' in path_str or '.archive' in path_str or 'archived' in path_str.lower():
            sync_results["removed"].append(branch_name)
            continue

        # Check if .id.json file exists in that directory
        id_file_found = False
        branch_dir = Path(branch_path)
        for id_file in branch_dir.glob("*.id.json"):
            id_file_found = True
            break

        if not id_file_found:
            sync_results["removed"].append(branch_name)
            continue

        # Valid - keep it
        valid_branches.append(branch)
        sync_results["kept"].append(branch_name)

    registry["branches"] = valid_branches

    # Step 2: Add missing entries (on filesystem but not in registry)
    for branch_info in discovered_branches.values():
        branch_path = branch_info["path"]
        branchname_upper = branch_info["name"]

        # Check if already in registry
        already_registered = any(
            b.get("name") == branchname_upper
            for b in registry["branches"]
        )

        if not already_registered:
            # Determine profile based on path
            if branch_path.startswith("/home/aipass-business/"):
                profile = "AIPass Business"
            elif branch_path.startswith("/home/input-x/"):
                profile = "Input-X"
            elif branch_path.startswith("/home/aipass/"):
                profile = "AIPass Workshop"
            else:
                profile = "Admin"

            # Derive email
            email = f"@{branch_info['branch_name_lower']}"

            # Create entry
            new_entry = {
                "name": branchname_upper,
                "path": branch_path,
                "profile": profile,
                "description": "New branch - purpose TBD",
                "email": email,
                "status": "active",
                "created": datetime.now().strftime("%Y-%m-%d"),
                "last_active": datetime.now().strftime("%Y-%m-%d")
            }

            registry["branches"].append(new_entry)
            sync_results["added"].append(branchname_upper)

    # Update metadata
    registry["metadata"]["total_branches"] = len(registry["branches"])

    # Save synchronized registry
    save_registry(registry)

    return sync_results


def register_branch(target_dir: Path, branch_name: str, branchname_upper: str) -> Optional[str]:
    """
    Register new branch in JSON registry

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name (lowercase with hyphens)
        branchname_upper: Branch name (uppercase with underscores)

    Returns:
        Status message or None if registration failed
    """
    # Determine profile based on path
    path_str = str(target_dir)
    if path_str.startswith("/home/aipass-business/"):
        profile = "AIPass Business"
    elif path_str.startswith("/home/input-x/"):
        profile = "Input-X"
    elif path_str.startswith("/home/aipass/"):
        profile = "AIPass Workshop"
    else:
        profile = "Admin"

    # Derive email from branch name
    email = f"@{branch_name.lower().replace('-', '_')}"

    # Build registry entry
    entry = {
        "name": branchname_upper,
        "path": str(target_dir),
        "profile": profile,
        "description": "New branch - purpose TBD",
        "email": email,
        "status": "active"
    }

    # Add to registry
    if add_registry_entry(entry):
        return f"Registered in BRANCH_REGISTRY.json as {branchname_upper}"
    else:
        # Check if already registered
        if find_branch_in_registry(branchname_upper):
            return "Already registered"
        return None
