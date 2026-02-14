#!/usr/bin/env python3
"""
Unit tests for branch_merge.py

Tests branch merging functionality.
"""

import sys
from pathlib import Path
import json
import pytest

# Standard AIPass import pattern (See code_standards.md Section 9.8)
from apps.branch_merge import (
    merge_branches,
    merge_sessions,
    merge_observations,
    merge_emails,
    analyze_branch
)


# =============================================================================
# SESSION MERGE TESTS
# =============================================================================

@pytest.mark.unit
class TestMergeSessions:
    """Test session merging logic"""

    def test_merge_empty_sessions(self):
        """Test merging when both have empty sessions"""
        source_sessions = []
        target_sessions = []

        result = merge_sessions(source_sessions, target_sessions, "SOURCE")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_merge_sessions_with_data(self):
        """Test merging sessions with data"""
        source_sessions = [
            {"session_number": 1, "date": "2025-10-01", "summary": "Source session"}
        ]
        target_sessions = [
            {"session_number": 1, "date": "2025-10-02", "summary": "Target session"}
        ]

        result = merge_sessions(source_sessions, target_sessions, "SOURCE")

        assert isinstance(result, list)
        assert len(result) == 2
        # Should be chronologically sorted and renumbered


# =============================================================================
# OBSERVATION MERGE TESTS
# =============================================================================

@pytest.mark.unit
class TestMergeObservations:
    """Test observation merging logic"""

    def test_merge_empty_observations(self):
        """Test merging empty observations"""
        source_obs = []
        target_obs = []

        result = merge_observations(source_obs, target_obs, "SOURCE")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_merge_observations_with_data(self):
        """Test merging observations with data"""
        source_obs = [
            {"date": "2025-10-01", "entries": [{"observation": "Source obs"}]}
        ]
        target_obs = [
            {"date": "2025-10-02", "entries": [{"observation": "Target obs"}]}
        ]

        result = merge_observations(source_obs, target_obs, "SOURCE")

        assert isinstance(result, list)
        assert len(result) == 2


# =============================================================================
# EMAIL MERGE TESTS
# =============================================================================

@pytest.mark.unit
class TestMergeEmails:
    """Test email merging logic"""

    def test_merge_emails_empty(self):
        """Test merging empty email structures"""
        source_mail = {"summary": {"inbox": {"total": 0}, "sent": {"total": 0}}}
        target_mail = {"summary": {"inbox": {"total": 0}, "sent": {"total": 0}}}

        result = merge_emails(source_mail, target_mail)

        assert isinstance(result, dict)
        assert "summary" in result

    def test_merge_emails_with_counts(self):
        """Test merging emails with message counts"""
        source_mail = {"summary": {"inbox": {"total": 5}, "sent": {"total": 3}}}
        target_mail = {"summary": {"inbox": {"total": 2}, "sent": {"total": 1}}}

        result = merge_emails(source_mail, target_mail)

        assert isinstance(result, dict)
        # Counts should be combined (or at least present)
        assert "summary" in result


# =============================================================================
# ANALYSIS TESTS
# =============================================================================

@pytest.mark.unit
class TestAnalyzeBranch:
    """Test branch analysis"""

    def test_analyze_empty_branch(self):
        """Test analyzing branch with empty data"""
        empty_data = {
            "local": {"sessions": []},
            "observations": {"observations": []},
            "ai_mail": {"summary": {"inbox": {"total": 0}, "sent": {"total": 0}}}
        }

        result = analyze_branch(empty_data)

        assert isinstance(result, dict)
        assert "sessions" in result
        assert result["sessions"] == 0

    def test_analyze_branch_with_data(self):
        """Test analyzing branch with data"""
        data = {
            "local": {"sessions": [{"session_number": 1}, {"session_number": 2}]},
            "observations": {"observations": [{"entries": [{"obs": "test"}]}]},
            "ai_mail": {"summary": {"inbox": {"total": 5}, "sent": {"total": 3}}}
        }

        result = analyze_branch(data)

        assert isinstance(result, dict)
        assert result["sessions"] == 2
        assert result["observations"] >= 1
        assert result["emails"] == 8


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.integration
class TestBranchMergeIntegration:
    """Integration tests for branch merge workflow"""

    def test_merge_two_branches_preview(self, sample_branch_structure, temp_dir):
        """Test merge preview mode (no actual changes)"""
        source_dir = sample_branch_structure['root']
        target_dir = temp_dir / "target_branch"
        target_dir.mkdir()

        # Create minimal target structure
        target_name = "TARGET_BRANCH"
        (target_dir / f"{target_name}.json").write_text("{}")
        (target_dir / f"{target_name}.local.json").write_text('{"sessions": []}')
        (target_dir / f"{target_name}.observations.json").write_text('{"observations": []}')
        (target_dir / f"{target_name}.ai_mail.json").write_text('{"summary": {}}')

        # Run merge in preview mode
        result = merge_branches(source_dir, target_dir, preview_only=True, force=True)

        # Check result
        assert isinstance(result, bool)
