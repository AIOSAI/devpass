#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: metadata.py - Branch Metadata Extraction Handler
# Date: 2025-11-04
# Version: 1.0.0
# Category: cortex/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-04): Extracted from branch_lib, metadata extraction functions
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Branch Metadata Extraction Handler

Functions for extracting branch metadata:
- Branch name from path
- Profile detection
- Git repository information
- Directory tree generation
"""

# Standard library imports
import subprocess
from pathlib import Path
from typing import Optional
import sys

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))


# =============================================================================
# METADATA EXTRACTION
# =============================================================================

def get_branch_name(target_path: Path) -> str:
    """
    Extract branch name from target path

    Args:
        target_path: Path to branch directory

    Returns:
        Branch name (last folder in path)
    """
    return Path(target_path).name


def detect_profile(target_path: Path) -> str:
    """
    Detect AIPass profile from path

    Args:
        target_path: Path to branch directory

    Returns:
        Profile name: Admin, Business, Input-X, or Workshop (default)
    """
    path_str = str(target_path)
    if path_str == "/":
        return "Admin"
    elif "/home/aipass-business/" in path_str:
        return "Business"
    elif "/home/input-x/" in path_str:
        return "Input-X"
    elif "/home/aipass/" in path_str:
        return "Workshop"
    else:
        return "Workshop"  # Default


def get_git_repo(target_path: Path) -> str:
    """
    Get git repo URL from target directory

    Args:
        target_path: Path to branch directory

    Returns:
        Git remote origin URL or "Not in git repository"
    """
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=target_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        # Silent fail - return default message
        pass
    return "Not in git repository"


def generate_tree(target_dir: Path) -> str:
    """
    Generate directory tree output

    Args:
        target_dir: Path to directory to generate tree for

    Returns:
        Tree command output or error message
    """
    try:
        result = subprocess.run(
            ["tree", "-L", "2", "-a", str(target_dir)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout
    except Exception as e:
        # Silent fail - return default message
        pass
    return "[Tree command failed - install tree package]"


def validate_branch_path(path: Path) -> tuple[bool, str | None]:
    """
    Validate that path is a valid branch directory.

    Args:
        path: Path to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str | None)
    """
    if not path.exists():
        return (False, f"Directory does not exist: {path}")

    if not path.is_dir():
        return (False, f"Path is not a directory: {path}")

    return (True, None)


def resolve_branch_path(path: Path) -> Path:
    """
    Resolve path to absolute form.

    Args:
        path: Path to resolve

    Returns:
        Resolved absolute path
    """
    return path.resolve()


def normalize_branch_name(name: str, case: str = 'upper') -> str:
    """
    Normalize branch name to standard format.

    Args:
        name: Branch name to normalize
        case: 'upper' or 'lower' for output format

    Returns:
        Formatted branch name (UPPER_CASE or lower_case)
    """
    normalized = name.replace("-", "_")
    return normalized.upper() if case == 'upper' else normalized.lower()


def is_backup_directory(path: Path) -> bool:
    """
    Check if path is a backup directory.

    Args:
        path: Path to check

    Returns:
        True if path is backup directory
    """
    path_str = str(path)
    return "/backups/" in path_str or path_str.endswith("/backups")


def get_json_update_manifest(branch_name: str) -> list[tuple[str, str]]:
    """
    Get list of JSON files to update during branch update.

    Args:
        branch_name: Branch name

    Returns:
        List of (branch_filename, template_filename) tuples
    """
    branchname_upper = normalize_branch_name(branch_name, case='upper')

    return [
        (f"{branchname_upper}.json", "PROJECT.json"),
        (f"{branchname_upper}.id.json", "BRANCH.ID.json"),
        (f"{branchname_upper}.local.json", "LOCAL.json"),
        (f"{branchname_upper}.observations.json", "OBSERVATIONS.json"),
        (f"{branchname_upper}.ai_mail.json", "BRANCH.ai_mail.json"),
    ]
