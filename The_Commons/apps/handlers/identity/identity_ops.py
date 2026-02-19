#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: identity_ops.py - Identity Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/identity
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation from module refactor (FPLAN-0356 Phase 1)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules
# =============================================

"""
Identity Operations Handler

Implementation logic for branch identity detection, registry lookup,
caller detection, and mention extraction.
Moved from commons_identity.py to follow thin-module architecture.
"""

import sys
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger

# =============================================================================
# CONSTANTS
# =============================================================================

BRANCH_REGISTRY_PATH = Path.home() / "BRANCH_REGISTRY.json"

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))


# =============================================================================
# BRANCH DETECTION
# =============================================================================

def find_branch_root(start_path: Path) -> Optional[Path]:
    """
    Walk up directory tree to find branch root.

    Branch root is a directory containing a [BRANCH_NAME].id.json file.

    Args:
        start_path: Directory to start searching from (usually PWD)

    Returns:
        Path to branch root directory, or None if not found
    """
    current = start_path.resolve()

    for _ in range(10):
        for _file in current.glob("*.id.json"):
            return current

        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def get_branch_info_from_registry(branch_path: Path) -> Optional[Dict[str, Any]]:
    """
    Look up branch information in BRANCH_REGISTRY.json by path.

    Args:
        branch_path: Path to branch directory

    Returns:
        Dict with branch info from registry, or None if not found
    """
    if not BRANCH_REGISTRY_PATH.exists():
        return None

    try:
        with open(BRANCH_REGISTRY_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)

        branch_path_str = str(branch_path.resolve())

        for branch in registry.get("branches", []):
            if str(Path(branch["path"]).resolve()) == branch_path_str:
                return branch

        return None

    except Exception:
        return None


def get_caller_branch() -> Optional[Dict[str, Any]]:
    """
    Detect which branch is calling The Commons based on PWD.

    Walks up from CWD to find branch root, then looks up in BRANCH_REGISTRY.json.
    Auto-registers the branch as a Commons agent if not already present.

    Returns:
        Dict with branch info {"name": "SEED", "path": "...", "email": "@seed", ...}
        or None if no branch detected
    """
    try:
        cwd = Path.cwd()
        branch_root = find_branch_root(cwd)

        if not branch_root:
            logger.warning("[commons] Could not detect branch from PWD")
            return None

        branch_info = get_branch_info_from_registry(branch_root)
        if not branch_info:
            logger.warning(f"[commons] Branch at {branch_root} not in BRANCH_REGISTRY")
            return None

        # Auto-register as Commons agent
        _ensure_agent_registered(branch_info)

        return branch_info

    except Exception as e:
        logger.error(f"[commons] Branch detection failed: {e}")
        return None


def _ensure_agent_registered(branch_info: Dict[str, Any]) -> None:
    """
    Ensure the branch is registered as an agent in The Commons database.

    Args:
        branch_info: Branch dict from BRANCH_REGISTRY
    """
    try:
        from handlers.database.db import get_db, close_db

        name = branch_info.get("name", "")
        if not name:
            return

        conn = get_db()

        existing = conn.execute(
            "SELECT branch_name FROM agents WHERE branch_name = ?", (name,)
        ).fetchone()

        if not existing:
            display_name = name.replace("_", " ").title()
            description = branch_info.get("description", "")
            conn.execute(
                "INSERT OR IGNORE INTO agents (branch_name, display_name, description) "
                "VALUES (?, ?, ?)",
                (name, display_name, description)
            )
            conn.commit()
            logger.info(f"[commons] Auto-registered agent: {name}")

        close_db(conn)

    except Exception as e:
        logger.error(f"[commons] Agent registration failed: {e}")


# =============================================================================
# MENTION EXTRACTION
# =============================================================================

def extract_mentions(content: str) -> list[str]:
    """
    Extract @mention branch names from content.

    Matches patterns like @drone, @flow, @seed_cortex.
    Validates against the agents table to ensure they exist.

    Args:
        content: Text content to search for @mentions

    Returns:
        List of valid branch names that were mentioned (lowercased)
    """
    from handlers.database.db import get_db, close_db

    if not content:
        return []

    # Find all @word patterns (alphanumeric + underscore)
    pattern = r'@(\w+)'
    matches = re.findall(pattern, content)

    if not matches:
        return []

    # Normalize to lowercase
    mentioned = [m.lower() for m in matches]

    # Validate against agents table
    try:
        conn = get_db()
        placeholders = ','.join('?' * len(mentioned))
        query = f"SELECT branch_name FROM agents WHERE LOWER(branch_name) IN ({placeholders})"
        rows = conn.execute(query, mentioned).fetchall()
        close_db(conn)

        valid_mentions = [row[0] for row in rows]
        return valid_mentions

    except Exception as e:
        logger.error(f"[commons] Mention extraction failed: {e}")
        return []
