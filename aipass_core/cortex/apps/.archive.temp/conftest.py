#!/usr/bin/env python3
"""
pytest configuration and shared fixtures for branch_operations tests

This file provides reusable test fixtures that are automatically available
to all test files in the tests/ directory.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any
import pytest


# =============================================================================
# TEMPORARY DIRECTORY FIXTURES
# =============================================================================

@pytest.fixture
def temp_dir():
    """
    Create a temporary directory that's automatically cleaned up after test.

    Usage in tests:
        def test_something(temp_dir):
            file_path = temp_dir / "test.txt"
            file_path.write_text("content")
            assert file_path.exists()
    """
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def temp_branch_dir(temp_dir):
    """
    Create a temporary directory for a mock branch.
    Returns path to a directory like /tmp/xyz/test_branch/
    """
    branch_dir = temp_dir / "test_branch"
    branch_dir.mkdir(parents=True)
    yield branch_dir
    # Cleanup handled by temp_dir fixture


# =============================================================================
# MOCK BRANCH FIXTURES
# =============================================================================

@pytest.fixture
def sample_branch_structure(temp_branch_dir):
    """
    Create a complete mock branch structure with all standard files.

    Returns dict with paths:
        {
            'root': Path,
            'json': Path,
            'local': Path,
            'observations': Path,
            'ai_mail': Path,
            'readme': Path
        }
    """
    branch_name = "TEST_BRANCH"

    # Create JSON files
    json_file = temp_branch_dir / f"{branch_name}.json"
    local_file = temp_branch_dir / f"{branch_name}.local.json"
    obs_file = temp_branch_dir / f"{branch_name}.observations.json"
    mail_file = temp_branch_dir / f"{branch_name}.ai_mail.json"
    readme_file = temp_branch_dir / "README.md"

    # Sample project JSON
    json_file.write_text(json.dumps({
        "metadata": {
            "name": branch_name,
            "created": "2025-10-29",
            "version": "1.0.0"
        }
    }, indent=2))

    # Sample local JSON
    local_file.write_text(json.dumps({
        "sessions": [
            {
                "session_number": 1,
                "date": "2025-10-29",
                "summary": "Initial session"
            }
        ]
    }, indent=2))

    # Sample observations JSON
    obs_file.write_text(json.dumps({
        "observations": [
            {
                "date": "2025-10-29",
                "entries": [
                    {"observation": "Test observation"}
                ]
            }
        ]
    }, indent=2))

    # Sample AI mail JSON
    mail_file.write_text(json.dumps({
        "metadata": {
            "branch_name": branch_name,
            "email": f"{branch_name.lower()}@aipass.system"
        },
        "inbox": [],
        "sent": [],
        "summary": {
            "inbox": {"total": 0, "unread": 0},
            "sent": {"total": 0}
        }
    }, indent=2))

    # Sample README
    readme_file.write_text(f"# {branch_name}\n\nTest branch for pytest")

    return {
        'root': temp_branch_dir,
        'json': json_file,
        'local': local_file,
        'observations': obs_file,
        'ai_mail': mail_file,
        'readme': readme_file
    }


@pytest.fixture
def empty_branch_dir(temp_dir):
    """
    Create an empty directory for testing branch creation.
    """
    empty_dir = temp_dir / "empty_branch"
    empty_dir.mkdir()
    return empty_dir


# =============================================================================
# MOCK REGISTRY FIXTURES
# =============================================================================

@pytest.fixture
def mock_registry(temp_dir):
    """
    Create a mock BRANCH_REGISTRY.json file.

    Returns tuple: (registry_path, registry_dict)
    """
    registry_path = temp_dir / "BRANCH_REGISTRY.json"

    registry_data = {
        "metadata": {
            "version": "1.0.0",
            "last_updated": "2025-10-29"
        },
        "branches": [
            {
                "name": "TEST_BRANCH_1",
                "path": str(temp_dir / "test_branch_1"),
                "email": "test_branch_1@aipass.system",
                "description": "Test branch 1",
                "created": "2025-10-29",
                "last_active": "2025-10-29",
                "status": "active"
            },
            {
                "name": "TEST_BRANCH_2",
                "path": str(temp_dir / "test_branch_2"),
                "email": "test_branch_2@aipass.system",
                "description": "Test branch 2",
                "created": "2025-10-29",
                "last_active": "2025-10-29",
                "status": "active"
            }
        ]
    }

    registry_path.write_text(json.dumps(registry_data, indent=2))

    return registry_path, registry_data


# =============================================================================
# MOCK TEMPLATE FIXTURES
# =============================================================================

@pytest.fixture
def mock_template_dir(temp_dir):
    """
    Create a mock template directory structure.
    """
    template_dir = temp_dir / "templates"
    template_dir.mkdir()

    # Create sample template files
    (template_dir / "PROJECT.json").write_text(json.dumps({
        "metadata": {"version": "1.0.0"}
    }, indent=2))

    (template_dir / "PROJECT.local.json").write_text(json.dumps({
        "sessions": []
    }, indent=2))

    (template_dir / "PROJECT.observations.json").write_text(json.dumps({
        "observations": []
    }, indent=2))

    (template_dir / "PROJECT.ai_mail.json").write_text(json.dumps({
        "inbox": [],
        "sent": []
    }, indent=2))

    return template_dir


# =============================================================================
# UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def sample_json_file(temp_dir):
    """
    Create a sample JSON file for testing JSON operations.
    """
    json_path = temp_dir / "sample.json"
    data = {"key": "value", "number": 42, "list": [1, 2, 3]}
    json_path.write_text(json.dumps(data, indent=2))
    return json_path, data


# =============================================================================
# CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers.
    """
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual functions"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests across modules"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )
    config.addinivalue_line(
        "markers", "requires_registry: Tests that need BRANCH_REGISTRY.json"
    )
    config.addinivalue_line(
        "markers", "requires_template: Tests that need template files"
    )
