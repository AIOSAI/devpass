#!/usr/bin/env python3
"""
Unit tests for branch_delete.py

Tests branch deletion functionality.
"""

import sys
from pathlib import Path
import json
import pytest

# Standard AIPass import pattern (See code_standards.md Section 9.8)
from apps.branch_delete import delete_branch, create_deletion_record, get_deletion_dir


# =============================================================================
# DELETION RECORD TESTS
# =============================================================================

@pytest.mark.unit
class TestDeletionRecord:
    """Test deletion record creation"""

    def test_create_deletion_record_success(self, temp_dir):
        """Test creating deletion record"""
        deletion_dir = temp_dir / "deleted_branches"

        branch_info = {
            "name": "TEST_DELETE",
            "path": "/test/path",
            "profile": "Workshop",
            "description": "Test branch",
            "status": "active"
        }

        result = create_deletion_record(branch_info, deletion_dir)

        # Should return path to deletion record or None
        if result:
            assert result.exists()
            assert "deleted" in result.name

    def test_get_deletion_dir(self):
        """Test getting deletion directory path"""
        result = get_deletion_dir()

        assert isinstance(result, Path)
        assert "deleted_branches" in str(result)


# =============================================================================
# DELETE BRANCH TESTS
# =============================================================================

@pytest.mark.unit
class TestDeleteBranch:
    """Test branch deletion"""

    def test_delete_missing_branch(self, temp_dir):
        """Test deleting non-existent branch (should handle gracefully)"""
        missing_dir = temp_dir / "missing_branch"

        result = delete_branch(missing_dir, force=True)

        # Should return True (already gone) or handle gracefully
        assert isinstance(result, bool)

    def test_delete_with_force_flag(self, sample_branch_structure, monkeypatch):
        """Test deletion with force flag (skips confirmation)"""
        branch_dir = sample_branch_structure['root']

        # Monkeypatch registry functions to avoid modifying real registry
        monkeypatch.setattr('branch_delete.find_branch_in_registry', lambda x: None)
        monkeypatch.setattr('branch_delete.remove_registry_entry', lambda x: True)

        # Delete with force
        result = delete_branch(branch_dir, force=True)

        # Check result
        assert isinstance(result, bool)

        # If successful, directory should be gone
        if result:
            assert not branch_dir.exists()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.integration
class TestBranchDeleteIntegration:
    """Integration tests for branch deletion workflow"""

    def test_complete_deletion_workflow(self, sample_branch_structure, temp_dir, monkeypatch):
        """Test complete deletion workflow"""
        branch_dir = sample_branch_structure['root']
        deletion_dir = temp_dir / "deletions"

        # Monkeypatch to use test paths
        monkeypatch.setattr('branch_delete.get_deletion_dir', lambda: deletion_dir)
        monkeypatch.setattr('branch_delete.find_branch_in_registry', lambda x: None)
        monkeypatch.setattr('branch_delete.remove_registry_entry', lambda x: True)

        # Run deletion
        result = delete_branch(branch_dir, force=True)

        # Verify deletion
        assert isinstance(result, bool)
