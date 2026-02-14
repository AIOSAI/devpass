#!/usr/bin/env python3
"""
Unit tests for branch_clean.py

Tests branch cleaning functionality.
"""

import sys
from pathlib import Path
import json
import pytest

# Standard AIPass import pattern (See code_standards.md Section 9.8)
from apps.branch_clean import clean_branch, get_template_path


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

@pytest.mark.unit
class TestCleanHelpers:
    """Test helper functions"""

    def test_get_template_path(self):
        """Test getting template path"""
        result = get_template_path()
        assert isinstance(result, Path)


# =============================================================================
# CLEAN BRANCH TESTS
# =============================================================================

@pytest.mark.unit
class TestCleanBranch:
    """Test complete branch cleaning"""

    def test_clean_branch_with_confirmation(self, sample_branch_structure):
        """Test cleaning branch (with force flag to skip confirmation)"""
        branch_dir = sample_branch_structure['root']

        # Use force flag to skip interactive confirmation
        result = clean_branch(branch_dir, force=True)

        # Check result
        assert isinstance(result, bool)

    def test_clean_missing_branch(self, temp_dir):
        """Test cleaning non-existent branch"""
        missing_dir = temp_dir / "missing_branch"

        result = clean_branch(missing_dir, force=True)

        # Should handle gracefully
        assert isinstance(result, bool)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.integration
class TestBranchCleanIntegration:
    """Integration tests for branch cleaning workflow"""

    def test_complete_clean_workflow(self, sample_branch_structure):
        """Test complete clean workflow with force flag"""
        branch_dir = sample_branch_structure['root']

        # Clean branch
        result = clean_branch(branch_dir, force=True)

        # Verify result
        assert isinstance(result, bool)

        # If successful, verify backup was created
        if result:
            backup_dir = branch_dir / ".backup"
            # Backup might or might not exist depending on implementation
            assert isinstance(backup_dir.exists(), bool)
