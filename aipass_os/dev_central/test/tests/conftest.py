#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: tests/conftest.py
# Date: 2026-02-15
# Version: 2.0.0
# Category: test/tests
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-15): Branch discovery fixtures, registry loading,
#     parametrized branch_info, pytest marker support for smoke/comms/data
#   - v1.0.0 (2025-11-08): Initial implementation - Shared pytest fixtures
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
#   - Import order: sys/pathlib, standard library, internal
#   - Google-style docstrings, type hints on all functions
# =============================================

"""Shared pytest fixtures for the TEST branch.

Provides branch discovery from BRANCH_REGISTRY.json, parametrized fixtures
for cross-branch testing, and utility fixtures for temporary directories.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Generator

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AIPASS_ROOT: Path = Path("/home/aipass")
REGISTRY_PATH: Path = AIPASS_ROOT / "BRANCH_REGISTRY.json"

# ---------------------------------------------------------------------------
# Utility functions (not fixtures)
# ---------------------------------------------------------------------------


def load_branch_registry() -> dict[str, Any]:
    """Load the full BRANCH_REGISTRY.json from disk.

    Returns:
        The parsed registry dict with 'metadata' and 'branches' keys.

    Raises:
        FileNotFoundError: If BRANCH_REGISTRY.json does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    with REGISTRY_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def get_branch_names() -> list[str]:
    """Return a sorted list of branch names from the registry.

    Used for parametrize IDs so pytest output is human-readable.

    Returns:
        Sorted list of branch name strings.
    """
    registry = load_branch_registry()
    return sorted(b["name"] for b in registry["branches"])


# ---------------------------------------------------------------------------
# Fixtures - Branch discovery
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def branch_registry() -> dict[str, Any]:
    """Load the full branch registry (session-scoped, loaded once).

    Returns:
        The complete registry dict including metadata and branches list.
    """
    return load_branch_registry()


@pytest.fixture(scope="session")
def branch_paths(branch_registry: dict[str, Any]) -> list[Path]:
    """Return Path objects for every registered branch directory.

    Args:
        branch_registry: The full registry dict (injected by pytest).

    Returns:
        List of Path objects pointing to each branch's root directory.
    """
    return [Path(b["path"]) for b in branch_registry["branches"]]


def _branch_items() -> list[dict[str, Any]]:
    """Collect branch dicts for parametrize (called at collection time)."""
    registry = load_branch_registry()
    return registry["branches"]


@pytest.fixture(params=_branch_items(), ids=lambda b: b["name"])
def branch_info(request: pytest.FixtureRequest) -> dict[str, Any]:
    """Yield individual branch info dicts, one per registered branch.

    Parametrized automatically across all branches in the registry.
    Each invocation receives a single branch dict with keys:
        name, path, profile, description, email, status, created, last_active.

    Args:
        request: The pytest request object providing the parametrized value.

    Returns:
        A single branch info dictionary.
    """
    return request.param


# ---------------------------------------------------------------------------
# Fixtures - General utilities
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_test_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing; clean up after.

    Yields:
        Path to the temporary directory.
    """
    test_dir = Path(tempfile.mkdtemp())
    yield test_dir
    if test_dir.exists():
        shutil.rmtree(test_dir)


@pytest.fixture
def aipass_root() -> Path:
    """Return the AIPass root path constant.

    Returns:
        Path to /home/aipass.
    """
    return AIPASS_ROOT
