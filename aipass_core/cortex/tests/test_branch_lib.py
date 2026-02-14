#!/usr/bin/env python3
"""
Unit tests for branch_lib.py

Tests core shared functions used by all branch operations modules.
"""

import sys
from pathlib import Path
import json
import pytest

# Standard AIPass import pattern (See code_standards.md Section 9.8)
from apps.branch_lib import (
    get_branch_name,
    detect_profile,
    get_git_repo,
    load_registry,
    save_registry,
    find_branch_in_registry,
    add_registry_entry,
    remove_registry_entry,
    get_branch_registry_path
)


# =============================================================================
# BRANCH NAME TESTS
# =============================================================================

@pytest.mark.unit
class TestGetBranchName:
    """Test get_branch_name() function"""

    def test_simple_branch_name(self, temp_branch_dir):
        """Test extracting branch name from simple path"""
        result = get_branch_name(temp_branch_dir)
        assert result == "test_branch"

    def test_nested_branch_name(self, temp_dir):
        """Test extracting branch name from nested path"""
        nested = temp_dir / "projects" / "my_branch"
        nested.mkdir(parents=True)
        result = get_branch_name(nested)
        assert result == "my_branch"

    def test_branch_name_with_hyphens(self, temp_dir):
        """Test branch name with hyphens converted to underscores"""
        hyphen_branch = temp_dir / "test-branch-name"
        hyphen_branch.mkdir()
        result = get_branch_name(hyphen_branch)
        assert result == "test-branch-name"  # Returns as-is, uppercase conversion happens elsewhere

    def test_root_directory(self, temp_dir):
        """Test getting name from root-like directory"""
        result = get_branch_name(Path("/"))
        assert isinstance(result, str)


# =============================================================================
# PROFILE DETECTION TESTS
# =============================================================================

@pytest.mark.unit
class TestDetectProfile:
    """Test detect_profile() function"""

    def test_workshop_profile(self, temp_dir):
        """Test detecting Workshop profile"""
        aipass_path = temp_dir / "aipass" / "test_branch"
        aipass_path.mkdir(parents=True)
        result = detect_profile(aipass_path)
        assert result == "Workshop"

    def test_business_profile(self, temp_dir):
        """Test detecting Business profile"""
        business_path = temp_dir / "aipass-business" / "test_branch"
        business_path.mkdir(parents=True)
        result = detect_profile(business_path)
        assert result == "Business"

    def test_inputx_profile(self, temp_dir):
        """Test detecting Input-X profile"""
        inputx_path = temp_dir / "input-x" / "test_branch"
        inputx_path.mkdir(parents=True)
        result = detect_profile(inputx_path)
        assert result == "Input-X"

    def test_admin_profile(self):
        """Test detecting Admin profile at root"""
        result = detect_profile(Path("/"))
        assert result == "Admin"

    def test_unknown_profile(self, temp_dir):
        """Test unknown profile returns Unknown"""
        unknown_path = temp_dir / "random" / "test_branch"
        unknown_path.mkdir(parents=True)
        result = detect_profile(unknown_path)
        assert result == "Unknown"


# =============================================================================
# GIT REPO TESTS
# =============================================================================

@pytest.mark.unit
class TestGetGitRepo:
    """Test get_git_repo() function"""

    def test_no_git_repo(self, temp_branch_dir):
        """Test path without git repository"""
        result = get_git_repo(temp_branch_dir)
        assert result == "Not in git repository"

    def test_with_git_repo(self, temp_dir):
        """Test path with git repository"""
        # Create a mock .git directory
        git_dir = temp_dir / ".git"
        git_dir.mkdir()

        branch_dir = temp_dir / "test_branch"
        branch_dir.mkdir()

        result = get_git_repo(branch_dir)
        # Should find git repo in parent
        assert result != "Not in git repository"


# =============================================================================
# REGISTRY TESTS
# =============================================================================

@pytest.mark.unit
@pytest.mark.requires_registry
class TestRegistryOperations:
    """Test registry load/save/find functions"""

    def test_load_registry_success(self, mock_registry, monkeypatch):
        """Test loading valid registry"""
        registry_path, expected_data = mock_registry

        # Monkeypatch get_branch_registry_path to return our test path
        monkeypatch.setattr('branch_lib.get_branch_registry_path', lambda: registry_path)

        result = load_registry()
        assert result is not None
        assert "branches" in result
        assert len(result["branches"]) == 2

    def test_load_registry_missing_file(self, temp_dir, monkeypatch):
        """Test loading non-existent registry returns empty structure"""
        missing_path = temp_dir / "missing_registry.json"
        monkeypatch.setattr('branch_lib.get_branch_registry_path', lambda: missing_path)

        result = load_registry()
        assert result is not None
        assert "branches" in result
        assert len(result["branches"]) == 0

    def test_save_registry_success(self, temp_dir, monkeypatch):
        """Test saving registry"""
        registry_path = temp_dir / "test_registry.json"
        monkeypatch.setattr('branch_lib.get_branch_registry_path', lambda: registry_path)

        test_data = {
            "metadata": {"version": "1.0.0"},
            "branches": [{"name": "TEST", "path": "/test"}]
        }

        result = save_registry(test_data)
        assert result is True
        assert registry_path.exists()

        # Verify content
        loaded = json.loads(registry_path.read_text())
        assert loaded["branches"][0]["name"] == "TEST"

    def test_find_branch_in_registry(self, mock_registry, monkeypatch):
        """Test finding branch in registry"""
        registry_path, _ = mock_registry
        monkeypatch.setattr('branch_lib.get_branch_registry_path', lambda: registry_path)

        result = find_branch_in_registry("TEST_BRANCH_1")
        assert result is not None
        assert result["name"] == "TEST_BRANCH_1"
        assert result["status"] == "active"

    def test_find_branch_not_found(self, mock_registry, monkeypatch):
        """Test finding non-existent branch"""
        registry_path, _ = mock_registry
        monkeypatch.setattr('branch_lib.get_branch_registry_path', lambda: registry_path)

        result = find_branch_in_registry("NONEXISTENT")
        assert result is None


# =============================================================================
# REGISTRY MODIFICATION TESTS
# =============================================================================

@pytest.mark.unit
@pytest.mark.requires_registry
class TestRegistryModifications:
    """Test registry add/remove/update operations"""

    def test_add_registry_entry(self, mock_registry, monkeypatch):
        """Test adding new branch to registry"""
        registry_path, _ = mock_registry
        monkeypatch.setattr('branch_lib.get_branch_registry_path', lambda: registry_path)

        new_entry = {
            "name": "NEW_BRANCH",
            "path": "/test/new_branch",
            "email": "new_branch@aipass.system",
            "description": "New test branch",
            "status": "active"
        }

        result = add_registry_entry(new_entry)
        assert result is True

        # Verify entry was added
        found = find_branch_in_registry("NEW_BRANCH")
        assert found is not None
        assert found["name"] == "NEW_BRANCH"

    def test_remove_registry_entry(self, mock_registry, monkeypatch):
        """Test removing branch from registry"""
        registry_path, _ = mock_registry
        monkeypatch.setattr('branch_lib.get_branch_registry_path', lambda: registry_path)

        result = remove_registry_entry("TEST_BRANCH_1")
        assert result is True

        # Verify entry was removed
        found = find_branch_in_registry("TEST_BRANCH_1")
        assert found is None

    def test_remove_nonexistent_entry(self, mock_registry, monkeypatch):
        """Test removing non-existent branch returns False"""
        registry_path, _ = mock_registry
        monkeypatch.setattr('branch_lib.get_branch_registry_path', lambda: registry_path)

        result = remove_registry_entry("NONEXISTENT")
        assert result is False

    # Note: update_registry_entry doesn't exist in branch_lib.py
    # Updates would be done by remove + add pattern if needed


# =============================================================================
# PATH GETTER TESTS
# =============================================================================

@pytest.mark.unit
class TestPathGetters:
    """Test path getter functions"""

    def test_get_branch_registry_path(self):
        """Test getting registry path"""
        result = get_branch_registry_path()
        assert isinstance(result, Path)
        assert "BRANCH_REGISTRY.json" in str(result)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.integration
class TestBranchLibIntegration:
    """Integration tests combining multiple functions"""

    def test_complete_registry_workflow(self, temp_dir, monkeypatch):
        """Test complete workflow: add, find, update, remove"""
        registry_path = temp_dir / "workflow_registry.json"
        monkeypatch.setattr('branch_lib.get_branch_registry_path', lambda: registry_path)

        # Start with empty registry
        registry = load_registry()
        assert len(registry["branches"]) == 0

        # Add entry
        entry = {
            "name": "WORKFLOW_TEST",
            "path": str(temp_dir / "workflow_branch"),
            "email": "workflow@aipass.system",
            "description": "Workflow test",
            "status": "active"
        }
        add_registry_entry(entry)

        # Find entry
        found = find_branch_in_registry("WORKFLOW_TEST")
        assert found is not None
        assert found["status"] == "active"

        # Update entry
        def update_registry_entry(branch_name, updates):
            entry = find_branch_in_registry(branch_name)
            if entry is None:
                return False
            entry.update(updates)
            registry = load_registry()
            for branch in registry.get("branches", []):
                if branch.get("name") == branch_name:
                    branch.update(updates)
            save_registry(registry)
            return True

        update_registry_entry("WORKFLOW_TEST", {"status": "testing"})
        found = find_branch_in_registry("WORKFLOW_TEST")
        assert found is not None
        assert found["status"] == "testing"

        # Remove entry
        remove_registry_entry("WORKFLOW_TEST")
        found = find_branch_in_registry("WORKFLOW_TEST")
        assert found is None
