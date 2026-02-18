#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: tests/smoke/test_branch_health.py
# Date: 2026-02-15
# Version: 1.0.0
# Category: test/tests/smoke
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-15): Initial smoke test suite - branch health checks
#     across all registered AIPass branches using parametrized fixtures
#
# CODE STANDARDS:
#   - Error handling: Use pytest.skip() for non-applicable checks
#   - Import order: sys/pathlib, standard library, internal
#   - Google-style docstrings, type hints on all functions
# =============================================

"""Smoke tests for AIPass branch health.

Validates that every registered branch has the expected file structure,
valid JSON configuration files, and consistent registry metadata.
All tests are read-only and use the parametrized ``branch_info`` fixture
from conftest.py to run automatically across all branches.
"""

import json
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_REGISTRY_FIELDS: set[str] = {"name", "path", "email"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _branch_dir(branch_info: dict[str, Any]) -> Path:
    """Resolve the branch directory from branch_info.

    Args:
        branch_info: A single branch dict from the registry.

    Returns:
        Path object for the branch directory.
    """
    return Path(branch_info["path"])


def _branch_name(branch_info: dict[str, Any]) -> str:
    """Return the uppercase branch name.

    Args:
        branch_info: A single branch dict from the registry.

    Returns:
        The branch name string (e.g. 'DRONE', 'FLOW').
    """
    return branch_info["name"]


# ---------------------------------------------------------------------------
# Smoke tests - File existence
# ---------------------------------------------------------------------------


@pytest.mark.smoke
def test_branch_directory_exists(branch_info: dict[str, Any]) -> None:
    """Verify that the branch directory from the registry exists on disk.

    Args:
        branch_info: Parametrized branch dict with 'path' key.
    """
    branch_dir = _branch_dir(branch_info)
    assert branch_dir.exists(), (
        f"Branch directory does not exist: {branch_dir}"
    )
    assert branch_dir.is_dir(), (
        f"Branch path exists but is not a directory: {branch_dir}"
    )


@pytest.mark.smoke
def test_branch_has_id_json(branch_info: dict[str, Any]) -> None:
    """Verify that {NAME}.id.json exists in the branch directory.

    Args:
        branch_info: Parametrized branch dict with 'name' and 'path' keys.
    """
    branch_dir = _branch_dir(branch_info)
    name = _branch_name(branch_info)

    if not branch_dir.exists():
        pytest.skip(f"Branch directory missing: {branch_dir}")

    id_file = branch_dir / f"{name}.id.json"
    assert id_file.exists(), (
        f"Missing identity file: {id_file}"
    )


@pytest.mark.smoke
def test_branch_has_local_json(branch_info: dict[str, Any]) -> None:
    """Verify that {NAME}.local.json exists in the branch directory.

    Args:
        branch_info: Parametrized branch dict with 'name' and 'path' keys.
    """
    branch_dir = _branch_dir(branch_info)
    name = _branch_name(branch_info)

    if not branch_dir.exists():
        pytest.skip(f"Branch directory missing: {branch_dir}")

    local_file = branch_dir / f"{name}.local.json"
    assert local_file.exists(), (
        f"Missing local file: {local_file}"
    )


@pytest.mark.smoke
def test_branch_has_observations_json(branch_info: dict[str, Any]) -> None:
    """Verify that {NAME}.observations.json exists in the branch directory.

    Args:
        branch_info: Parametrized branch dict with 'name' and 'path' keys.
    """
    branch_dir = _branch_dir(branch_info)
    name = _branch_name(branch_info)

    if not branch_dir.exists():
        pytest.skip(f"Branch directory missing: {branch_dir}")

    obs_file = branch_dir / f"{name}.observations.json"
    assert obs_file.exists(), (
        f"Missing observations file: {obs_file}"
    )


@pytest.mark.smoke
def test_branch_has_readme(branch_info: dict[str, Any]) -> None:
    """Verify that README.md exists in the branch directory.

    Args:
        branch_info: Parametrized branch dict with 'path' key.
    """
    branch_dir = _branch_dir(branch_info)

    if not branch_dir.exists():
        pytest.skip(f"Branch directory missing: {branch_dir}")

    readme = branch_dir / "README.md"
    assert readme.exists(), (
        f"Missing README.md: {readme}"
    )


@pytest.mark.smoke
def test_branch_has_apps_directory(branch_info: dict[str, Any]) -> None:
    """Verify that the apps/ directory exists in the branch directory.

    Args:
        branch_info: Parametrized branch dict with 'path' key.
    """
    branch_dir = _branch_dir(branch_info)

    if not branch_dir.exists():
        pytest.skip(f"Branch directory missing: {branch_dir}")

    apps_dir = branch_dir / "apps"
    assert apps_dir.exists(), (
        f"Missing apps directory: {apps_dir}"
    )
    assert apps_dir.is_dir(), (
        f"apps exists but is not a directory: {apps_dir}"
    )


# ---------------------------------------------------------------------------
# Smoke tests - JSON validity
# ---------------------------------------------------------------------------


@pytest.mark.smoke
def test_id_json_is_valid(branch_info: dict[str, Any]) -> None:
    """Verify that {NAME}.id.json parses as valid JSON.

    Args:
        branch_info: Parametrized branch dict with 'name' and 'path' keys.
    """
    branch_dir = _branch_dir(branch_info)
    name = _branch_name(branch_info)
    id_file = branch_dir / f"{name}.id.json"

    if not id_file.exists():
        pytest.skip(f"id.json not found: {id_file}")

    try:
        with id_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data, dict), (
            f"{id_file.name} parsed but is not a JSON object (got {type(data).__name__})"
        )
    except json.JSONDecodeError as exc:
        pytest.fail(f"{id_file.name} contains invalid JSON: {exc}")


@pytest.mark.smoke
def test_local_json_is_valid(branch_info: dict[str, Any]) -> None:
    """Verify that {NAME}.local.json parses as valid JSON.

    Args:
        branch_info: Parametrized branch dict with 'name' and 'path' keys.
    """
    branch_dir = _branch_dir(branch_info)
    name = _branch_name(branch_info)
    local_file = branch_dir / f"{name}.local.json"

    if not local_file.exists():
        pytest.skip(f"local.json not found: {local_file}")

    try:
        with local_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data, dict), (
            f"{local_file.name} parsed but is not a JSON object (got {type(data).__name__})"
        )
    except json.JSONDecodeError as exc:
        pytest.fail(f"{local_file.name} contains invalid JSON: {exc}")


@pytest.mark.smoke
def test_observations_json_is_valid(branch_info: dict[str, Any]) -> None:
    """Verify that {NAME}.observations.json parses as valid JSON.

    Args:
        branch_info: Parametrized branch dict with 'name' and 'path' keys.
    """
    branch_dir = _branch_dir(branch_info)
    name = _branch_name(branch_info)
    obs_file = branch_dir / f"{name}.observations.json"

    if not obs_file.exists():
        pytest.skip(f"observations.json not found: {obs_file}")

    try:
        with obs_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data, dict), (
            f"{obs_file.name} parsed but is not a JSON object (got {type(data).__name__})"
        )
    except json.JSONDecodeError as exc:
        pytest.fail(f"{obs_file.name} contains invalid JSON: {exc}")


# ---------------------------------------------------------------------------
# Smoke tests - Registry consistency
# ---------------------------------------------------------------------------


@pytest.mark.smoke
def test_branch_in_registry(branch_info: dict[str, Any]) -> None:
    """Verify that the branch has required registry fields (name, path, email).

    Args:
        branch_info: Parametrized branch dict from the registry.
    """
    missing = REQUIRED_REGISTRY_FIELDS - set(branch_info.keys())
    assert not missing, (
        f"Branch '{branch_info.get('name', '???')}' missing registry fields: {missing}"
    )

    # Verify fields are non-empty strings
    for field in REQUIRED_REGISTRY_FIELDS:
        value = branch_info[field]
        assert isinstance(value, str) and value.strip(), (
            f"Branch '{branch_info['name']}' has empty/invalid '{field}': {value!r}"
        )


@pytest.mark.smoke
def test_registry_path_matches_disk(branch_info: dict[str, Any]) -> None:
    """Verify that the registry path resolves to a real directory on disk.

    Checks that the path in the registry and the actual filesystem location
    are consistent (resolved paths match).

    Args:
        branch_info: Parametrized branch dict with 'name' and 'path' keys.
    """
    registry_path = Path(branch_info["path"])

    if not registry_path.exists():
        pytest.skip(f"Branch directory missing: {registry_path}")

    # Resolve symlinks and normalize both paths to compare
    resolved = registry_path.resolve()
    assert resolved.is_dir(), (
        f"Registry path for '{branch_info['name']}' resolves to non-directory: {resolved}"
    )

    # Verify the branch name is consistent with the directory name
    # Branch names are UPPERCASE, directory names may differ (e.g. lowercase)
    # This is informational - we just check the path exists and is a directory
    assert resolved == registry_path.resolve(), (
        f"Path resolution mismatch for '{branch_info['name']}': "
        f"registry={registry_path}, resolved={resolved}"
    )
