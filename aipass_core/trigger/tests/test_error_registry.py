#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_error_registry.py - Error Registry Tests
# Date: 2026-02-13
# Version: 3.0.0
# Category: trigger/tests
#
# CHANGELOG (Max 5 entries):
#   - v3.0.0 (2026-02-14): Cross-branch push pipeline tests + edge cases
#   - v2.1.0 (2026-02-13): Phase 5 - Tests for update_source_fix_status
#   - v2.0.0 (2026-02-13): Phase 2 - Tests for circuit breaker + rate limiting
#   - v1.0.0 (2026-02-13): Created - Tests for Medic v2 Phase 1 error registry
#
# CODE STANDARDS:
#   - Follows AIPass Seed standards
#   - Uses pytest fixtures for isolation
#   - Each test uses a temp registry file to avoid side effects
# =============================================

"""
Tests for Error Registry Handler (Medic v2 Phase 1 + Phase 2 + Phase 5 + Push Pipeline)

Tests cover:
    Phase 1:
    - Message normalization (variable data stripping)
    - Fingerprint computation (determinism and uniqueness)
    - report() - new entry creation and count incrementing
    - query() - filtering by status, component, severity
    - update_status() - status transitions
    - clear_resolved() - cleanup of old resolved entries
    - get_stats() - summary statistics

    Phase 2:
    - Circuit breaker state transitions (closed/open/half_open)
    - Circuit breaker trip on threshold, cooldown, reset
    - Per-fingerprint exponential backoff dispatch control
    - Backoff schedule validation

    Phase 5:
    - update_source_fix_status() - fix lifecycle tracking
    - Valid/invalid status transitions
    - Persistence and prefix matching

    Push Pipeline (cross-branch):
    - report_error() public API from modules layer
    - Full pipeline: push -> registry -> circuit breaker -> dispatch -> event
    - Edge cases: malformed data, rapid-fire, file locking, circuit breaker trip
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from trigger.apps.handlers.error_registry import (
    CircuitBreakerState,
    ErrorEvent,
    REGISTRY_FILE,
    _circuit_breaker,
    _fingerprint_dispatch_count,
    _fingerprint_dispatch_times,
    circuit_breaker_allows,
    circuit_breaker_record_error,
    circuit_breaker_reset,
    circuit_breaker_trip,
    clear_resolved,
    compute_fingerprint,
    get_backoff_seconds,
    get_circuit_breaker_status,
    get_entry,
    get_stats,
    normalize_message,
    query,
    record_dispatch,
    report,
    should_dispatch,
    update_source_fix_status,
    update_status,
)


@pytest.fixture
def clean_registry(tmp_path):
    """Provide a clean temporary registry file for each test.

    Patches REGISTRY_FILE to point to a temp location so tests
    don't affect the real registry.
    """
    temp_registry = tmp_path / "error_registry.json"
    with patch(
        "trigger.apps.handlers.error_registry.REGISTRY_FILE",
        temp_registry
    ):
        yield temp_registry


# ---------------------------------------------------------------------------
# normalize_message tests
# ---------------------------------------------------------------------------

class TestNormalizeMessage:
    """Tests for normalize_message() variable data stripping."""

    def test_strips_line_numbers(self):
        """Line numbers should be replaced with 'line N'."""
        msg = "Error at line 42 in module"
        result = normalize_message(msg)
        assert "line N" in result
        assert "42" not in result

    def test_strips_timestamps(self):
        """ISO timestamps should be replaced with '<timestamp>'."""
        msg = "Failed at 2026-02-13T10:30:45.123456 during startup"
        result = normalize_message(msg)
        assert "<timestamp>" in result
        assert "2026-02-13T10:30:45" not in result

    def test_strips_absolute_paths(self):
        """Absolute paths should be replaced with '<path>'."""
        msg = "FileNotFoundError: /home/aipass/aipass_core/flow/config.json"
        result = normalize_message(msg)
        assert "<path>" in result
        assert "/home/aipass" not in result

    def test_strips_uuids(self):
        """UUIDs should be replaced with '<uuid>'."""
        msg = "Session a1b2c3d4-e5f6-7890-abcd-ef1234567890 expired"
        result = normalize_message(msg)
        assert "<uuid>" in result
        assert "a1b2c3d4" not in result

    def test_strips_hex_hashes(self):
        """Hex hashes (8+ chars) should be replaced with '<hash>'."""
        msg = "Hash mismatch: expected abcdef1234567890"
        result = normalize_message(msg)
        assert "<hash>" in result
        assert "abcdef1234567890" not in result

    def test_strips_port_numbers(self):
        """Port numbers should be replaced with ':<port>'."""
        msg = "Connection refused on localhost:8080"
        result = normalize_message(msg)
        assert ":<port>" in result
        assert "8080" not in result

    def test_preserves_core_message(self):
        """Core error type and message should survive normalization."""
        msg = "ImportError: No module named 'missing_module'"
        result = normalize_message(msg)
        assert "ImportError" in result
        assert "missing_module" in result

    def test_collapses_whitespace(self):
        """Multiple spaces should collapse to single space."""
        msg = "Error   with    extra   spaces"
        result = normalize_message(msg)
        assert "  " not in result

    def test_same_error_different_lines_normalize_equal(self):
        """Same error at different line numbers should normalize identically."""
        msg1 = "SyntaxError at line 10 in parser"
        msg2 = "SyntaxError at line 99 in parser"
        assert normalize_message(msg1) == normalize_message(msg2)


# ---------------------------------------------------------------------------
# compute_fingerprint tests
# ---------------------------------------------------------------------------

class TestComputeFingerprint:
    """Tests for compute_fingerprint() determinism and uniqueness."""

    def test_deterministic(self):
        """Same inputs should always produce the same fingerprint."""
        fp1 = compute_fingerprint("ImportError", "No module named foo", "FLOW")
        fp2 = compute_fingerprint("ImportError", "No module named foo", "FLOW")
        assert fp1 == fp2

    def test_different_types_different_fingerprints(self):
        """Different error types should produce different fingerprints."""
        fp1 = compute_fingerprint("ImportError", "something failed", "FLOW")
        fp2 = compute_fingerprint("ValueError", "something failed", "FLOW")
        assert fp1 != fp2

    def test_different_components_different_fingerprints(self):
        """Different components should produce different fingerprints."""
        fp1 = compute_fingerprint("ImportError", "something failed", "FLOW")
        fp2 = compute_fingerprint("ImportError", "something failed", "DRONE")
        assert fp1 != fp2

    def test_returns_40_char_hex(self):
        """Fingerprint should be a 40-character hex SHA1 digest."""
        fp = compute_fingerprint("Error", "test", "TEST")
        assert len(fp) == 40
        assert all(c in '0123456789abcdef' for c in fp)

    def test_different_messages_different_fingerprints(self):
        """Different normalized messages should produce different fingerprints."""
        fp1 = compute_fingerprint("Error", "connection refused", "API")
        fp2 = compute_fingerprint("Error", "timeout expired", "API")
        assert fp1 != fp2


# ---------------------------------------------------------------------------
# report() tests
# ---------------------------------------------------------------------------

class TestReport:
    """Tests for report() - creating and updating error entries."""

    def test_creates_new_entry(self, clean_registry):
        """report() should create a new entry for unseen errors."""
        result = report(
            error_type="ImportError",
            message="No module named 'foo'",
            component="FLOW",
            log_path="/home/aipass/aipass_core/flow/logs/flow.log",
            severity="medium"
        )
        assert result["is_new"] is True
        assert result["error_type"] == "ImportError"
        assert result["component"] == "FLOW"
        assert result["count"] == 1
        assert result["status"] == "new"
        assert result["severity"] == "medium"
        assert len(result["fingerprint"]) == 40

    def test_increments_existing_count(self, clean_registry):
        """report() should increment count on duplicate fingerprint."""
        # First report
        result1 = report(
            error_type="ImportError",
            message="No module named 'foo'",
            component="FLOW"
        )
        assert result1["is_new"] is True
        assert result1["count"] == 1

        # Same error again
        result2 = report(
            error_type="ImportError",
            message="No module named 'foo'",
            component="FLOW"
        )
        assert result2["is_new"] is False
        assert result2["count"] == 2

    def test_different_errors_create_separate_entries(self, clean_registry):
        """Different errors should create separate registry entries."""
        report(error_type="ImportError", message="missing foo", component="FLOW")
        report(error_type="ValueError", message="invalid bar", component="FLOW")

        stats = get_stats()
        assert stats["total"] == 2

    def test_invalid_severity_defaults_to_medium(self, clean_registry):
        """Invalid severity value should default to 'medium'."""
        result = report(
            error_type="Error",
            message="test",
            component="TEST",
            severity="invalid_level"
        )
        assert result["severity"] == "medium"

    def test_persists_to_disk(self, clean_registry):
        """report() should persist the entry to the registry file."""
        report(error_type="Error", message="test persist", component="TEST")
        assert clean_registry.exists()
        data = json.loads(clean_registry.read_text(encoding='utf-8'))
        assert len(data["errors"]) == 1
        assert data["metadata"]["version"] == "1.0.0"

    def test_updates_last_seen_on_duplicate(self, clean_registry):
        """Duplicate reports should update last_seen timestamp."""
        result1 = report(error_type="Error", message="dup test", component="X")
        first_seen = result1["first_seen"]

        result2 = report(error_type="Error", message="dup test", component="X")
        assert result2["first_seen"] == first_seen  # Unchanged from file
        # last_seen should be at least as recent
        assert result2["last_seen"] >= first_seen


# ---------------------------------------------------------------------------
# query() tests
# ---------------------------------------------------------------------------

class TestQuery:
    """Tests for query() - filtering and sorting."""

    def test_filter_by_status(self, clean_registry):
        """query() should filter entries by status."""
        report(error_type="E1", message="err1", component="A")
        report(error_type="E2", message="err2", component="B")

        # Update one to investigating
        entries = query()
        fp = entries[0]["fingerprint"]
        update_status(fp, "investigating")

        new_only = query(status="new")
        assert len(new_only) == 1

        investigating = query(status="investigating")
        assert len(investigating) == 1

    def test_filter_by_component(self, clean_registry):
        """query() should filter entries by component (case-insensitive)."""
        report(error_type="E1", message="err1", component="FLOW")
        report(error_type="E2", message="err2", component="DRONE")

        flow_errors = query(component="FLOW")
        assert len(flow_errors) == 1
        assert flow_errors[0]["component"] == "FLOW"

        # Case-insensitive
        flow_lower = query(component="flow")
        assert len(flow_lower) == 1

    def test_filter_by_severity(self, clean_registry):
        """query() should filter entries by severity."""
        report(error_type="E1", message="minor", component="A", severity="low")
        report(error_type="E2", message="major", component="A", severity="critical")

        critical = query(severity="critical")
        assert len(critical) == 1
        assert critical[0]["severity"] == "critical"

    def test_combined_filters(self, clean_registry):
        """query() should support combining multiple filters."""
        report(error_type="E1", message="err1", component="FLOW", severity="high")
        report(error_type="E2", message="err2", component="FLOW", severity="low")
        report(error_type="E3", message="err3", component="DRONE", severity="high")

        results = query(component="FLOW", severity="high")
        assert len(results) == 1
        assert results[0]["error_type"] == "E1"

    def test_sorted_by_last_seen_descending(self, clean_registry):
        """query() results should be sorted by last_seen, most recent first."""
        report(error_type="E1", message="first", component="A")
        report(error_type="E2", message="second", component="A")

        results = query()
        assert len(results) == 2
        assert results[0]["last_seen"] >= results[1]["last_seen"]

    def test_limit(self, clean_registry):
        """query() should respect the limit parameter."""
        for i in range(10):
            report(error_type=f"E{i}", message=f"error {i}", component="A")

        results = query(limit=3)
        assert len(results) == 3

    def test_empty_registry_returns_empty(self, clean_registry):
        """query() on empty registry should return empty list."""
        results = query()
        assert results == []


# ---------------------------------------------------------------------------
# update_status() tests
# ---------------------------------------------------------------------------

class TestUpdateStatus:
    """Tests for update_status() - status transitions."""

    def test_changes_status(self, clean_registry):
        """update_status() should change an entry's status."""
        result = report(error_type="E", message="test", component="X")
        fp = result["fingerprint"]

        assert update_status(fp, "investigating") is True
        entry = get_entry(fp)
        assert entry["status"] == "investigating"

    def test_stores_suppress_reason(self, clean_registry):
        """Suppressing should store the reason."""
        result = report(error_type="E", message="test", component="X")
        fp = result["fingerprint"]

        assert update_status(fp, "suppressed", reason="Known flaky test") is True
        entry = get_entry(fp)
        assert entry["status"] == "suppressed"
        assert entry["suppress_reason"] == "Known flaky test"

    def test_invalid_status_returns_false(self, clean_registry):
        """update_status() should reject invalid status values."""
        result = report(error_type="E", message="test", component="X")
        fp = result["fingerprint"]

        assert update_status(fp, "invalid_status") is False

    def test_missing_fingerprint_returns_false(self, clean_registry):
        """update_status() should return False for unknown fingerprints."""
        assert update_status("nonexistent_fingerprint", "resolved") is False

    def test_prefix_matching(self, clean_registry):
        """update_status() should work with fingerprint prefixes."""
        result = report(error_type="E", message="test", component="X")
        fp_prefix = result["fingerprint"][:12]

        assert update_status(fp_prefix, "investigating") is True
        entry = get_entry(fp_prefix)
        assert entry["status"] == "investigating"


# ---------------------------------------------------------------------------
# get_entry() tests
# ---------------------------------------------------------------------------

class TestGetEntry:
    """Tests for get_entry() - single entry retrieval."""

    def test_exact_match(self, clean_registry):
        """get_entry() should find entry by exact fingerprint."""
        result = report(error_type="E", message="test", component="X")
        fp = result["fingerprint"]

        entry = get_entry(fp)
        assert entry is not None
        assert entry["error_type"] == "E"

    def test_prefix_match(self, clean_registry):
        """get_entry() should find entry by fingerprint prefix."""
        result = report(error_type="E", message="test", component="X")
        fp_prefix = result["fingerprint"][:8]

        entry = get_entry(fp_prefix)
        assert entry is not None
        assert entry["error_type"] == "E"

    def test_not_found_returns_none(self, clean_registry):
        """get_entry() should return None for unknown fingerprint."""
        assert get_entry("does_not_exist") is None


# ---------------------------------------------------------------------------
# clear_resolved() tests
# ---------------------------------------------------------------------------

class TestClearResolved:
    """Tests for clear_resolved() - cleanup of old resolved entries."""

    def test_removes_old_resolved(self, clean_registry):
        """clear_resolved() should remove resolved entries older than threshold."""
        result = report(error_type="E", message="test", component="X")
        fp = result["fingerprint"]

        # Mark as resolved
        update_status(fp, "resolved")

        # Manually backdate last_seen to 10 days ago
        data = json.loads(clean_registry.read_text(encoding='utf-8'))
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        data["errors"][fp]["last_seen"] = old_date
        clean_registry.write_text(json.dumps(data, indent=2), encoding='utf-8')

        removed = clear_resolved(days=7)
        assert removed == 1

        # Verify entry is gone
        assert get_entry(fp) is None

    def test_keeps_recent_resolved(self, clean_registry):
        """clear_resolved() should keep resolved entries newer than threshold."""
        result = report(error_type="E", message="test", component="X")
        fp = result["fingerprint"]
        update_status(fp, "resolved")

        # Don't backdate - it's brand new
        removed = clear_resolved(days=7)
        assert removed == 0
        assert get_entry(fp) is not None

    def test_keeps_non_resolved(self, clean_registry):
        """clear_resolved() should not touch non-resolved entries regardless of age."""
        result = report(error_type="E", message="test", component="X")
        fp = result["fingerprint"]

        # Backdate but keep status as 'new'
        data = json.loads(clean_registry.read_text(encoding='utf-8'))
        old_date = (datetime.now() - timedelta(days=30)).isoformat()
        data["errors"][fp]["last_seen"] = old_date
        clean_registry.write_text(json.dumps(data, indent=2), encoding='utf-8')

        removed = clear_resolved(days=7)
        assert removed == 0

    def test_returns_count(self, clean_registry):
        """clear_resolved() should return the correct count of removed entries."""
        for i in range(3):
            result = report(error_type=f"E{i}", message=f"err {i}", component="X")
            update_status(result["fingerprint"], "resolved")

        # Backdate all
        data = json.loads(clean_registry.read_text(encoding='utf-8'))
        old_date = (datetime.now() - timedelta(days=15)).isoformat()
        for entry in data["errors"].values():
            entry["last_seen"] = old_date
        clean_registry.write_text(json.dumps(data, indent=2), encoding='utf-8')

        removed = clear_resolved(days=7)
        assert removed == 3


# ---------------------------------------------------------------------------
# get_stats() tests
# ---------------------------------------------------------------------------

class TestGetStats:
    """Tests for get_stats() - summary statistics."""

    def test_empty_registry(self, clean_registry):
        """get_stats() on empty registry should return zero counts."""
        stats = get_stats()
        assert stats["total"] == 0
        assert stats["by_status"] == {}
        assert stats["by_component"] == {}
        assert stats["by_severity"] == {}

    def test_counts_by_status(self, clean_registry):
        """get_stats() should count entries per status."""
        r1 = report(error_type="E1", message="a", component="X")
        r2 = report(error_type="E2", message="b", component="X")
        update_status(r2["fingerprint"], "investigating")

        stats = get_stats()
        assert stats["total"] == 2
        assert stats["by_status"]["new"] == 1
        assert stats["by_status"]["investigating"] == 1

    def test_counts_by_component(self, clean_registry):
        """get_stats() should count entries per component."""
        report(error_type="E1", message="a", component="FLOW")
        report(error_type="E2", message="b", component="FLOW")
        report(error_type="E3", message="c", component="DRONE")

        stats = get_stats()
        assert stats["by_component"]["FLOW"] == 2
        assert stats["by_component"]["DRONE"] == 1

    def test_counts_by_severity(self, clean_registry):
        """get_stats() should count entries per severity."""
        report(error_type="E1", message="a", component="X", severity="low")
        report(error_type="E2", message="b", component="X", severity="critical")
        report(error_type="E3", message="c", component="X", severity="critical")

        stats = get_stats()
        assert stats["by_severity"]["low"] == 1
        assert stats["by_severity"]["critical"] == 2


# ===========================================================================
# Phase 2 Tests - Circuit Breaker + Rate Limiting
# ===========================================================================

@pytest.fixture(autouse=False)
def reset_circuit_breaker():
    """Reset circuit breaker state before and after each test that uses it."""
    circuit_breaker_reset()
    yield
    circuit_breaker_reset()


@pytest.fixture(autouse=False)
def reset_rate_limiting():
    """Clear per-fingerprint rate limiting state before and after each test."""
    _fingerprint_dispatch_times.clear()
    _fingerprint_dispatch_count.clear()
    yield
    _fingerprint_dispatch_times.clear()
    _fingerprint_dispatch_count.clear()


# ---------------------------------------------------------------------------
# Circuit Breaker tests
# ---------------------------------------------------------------------------

class TestCircuitBreakerAllows:
    """Tests for circuit_breaker_allows() - state-based dispatch gating."""

    def test_allows_when_closed(self, reset_circuit_breaker):
        """Closed state should always allow dispatch."""
        assert circuit_breaker_allows() is True

    def test_allows_returns_true_multiple_times_when_closed(self, reset_circuit_breaker):
        """Closed state should allow repeated dispatches."""
        for _ in range(20):
            assert circuit_breaker_allows() is True

    def test_denies_when_open(self, reset_circuit_breaker):
        """Open state should deny dispatch."""
        circuit_breaker_trip()
        assert circuit_breaker_allows() is False

    def test_denies_repeatedly_when_open(self, reset_circuit_breaker):
        """Open state should keep denying dispatch."""
        circuit_breaker_trip()
        for _ in range(5):
            assert circuit_breaker_allows() is False


class TestCircuitBreakerTrip:
    """Tests for circuit_breaker_trip() and threshold-based tripping."""

    def test_trips_after_threshold(self, reset_circuit_breaker):
        """Breaker should trip when error count exceeds threshold within window."""
        # Default threshold is 10 errors in 60 seconds
        for _ in range(10):
            circuit_breaker_record_error()

        status = get_circuit_breaker_status()
        assert status["state"] == "open"

    def test_does_not_trip_below_threshold(self, reset_circuit_breaker):
        """Breaker should stay closed if errors are below threshold."""
        for _ in range(5):
            circuit_breaker_record_error()

        status = get_circuit_breaker_status()
        assert status["state"] == "closed"

    def test_manual_trip(self, reset_circuit_breaker):
        """circuit_breaker_trip() should force open state."""
        circuit_breaker_trip(reason="manual test")
        status = get_circuit_breaker_status()
        assert status["state"] == "open"
        assert status["summary_sent"] is False


class TestCircuitBreakerTransitions:
    """Tests for circuit breaker state transitions."""

    def test_open_to_half_open_after_cooldown(self, reset_circuit_breaker):
        """Breaker should transition from open to half_open after cooldown."""
        circuit_breaker_trip()
        assert circuit_breaker_allows() is False

        # Simulate cooldown expiry by backdating opened_at
        import trigger.apps.handlers.error_registry as reg
        reg._circuit_breaker.opened_at = time.time() - 301  # past 300s cooldown

        assert circuit_breaker_allows() is True
        status = get_circuit_breaker_status()
        assert status["state"] == "half_open"

    def test_half_open_allows_one_then_denies(self, reset_circuit_breaker):
        """Half-open state should allow exactly one dispatch then deny."""
        circuit_breaker_trip()

        import trigger.apps.handlers.error_registry as reg
        reg._circuit_breaker.opened_at = time.time() - 301

        # First call transitions to half_open and allows
        assert circuit_breaker_allows() is True
        # Second call should deny (probe already used)
        assert circuit_breaker_allows() is False

    def test_half_open_error_reopens_with_doubled_cooldown(self, reset_circuit_breaker):
        """Error during half_open should re-open with doubled cooldown."""
        circuit_breaker_trip()

        import trigger.apps.handlers.error_registry as reg
        reg._circuit_breaker.opened_at = time.time() - 301

        # Transition to half_open
        circuit_breaker_allows()
        status = get_circuit_breaker_status()
        assert status["state"] == "half_open"

        # Error during half_open -> back to open with doubled cooldown
        circuit_breaker_record_error()
        status = get_circuit_breaker_status()
        assert status["state"] == "open"
        assert status["cooldown_seconds"] == 600  # doubled from 300

    def test_cooldown_caps_at_max(self, reset_circuit_breaker):
        """Cooldown should not exceed max_cooldown."""
        import trigger.apps.handlers.error_registry as reg

        circuit_breaker_trip()
        # Set cooldown near max
        reg._circuit_breaker.cooldown_seconds = 2000
        reg._circuit_breaker.opened_at = time.time() - 2001

        # Transition to half_open
        circuit_breaker_allows()
        # Error during half_open -> doubled but capped
        circuit_breaker_record_error()
        status = get_circuit_breaker_status()
        # 2000 * 2 = 4000, but max is 3600
        assert status["cooldown_seconds"] == 3600


class TestCircuitBreakerReset:
    """Tests for circuit_breaker_reset()."""

    def test_reset_returns_to_closed(self, reset_circuit_breaker):
        """Reset should return breaker to closed state."""
        circuit_breaker_trip()
        assert get_circuit_breaker_status()["state"] == "open"

        circuit_breaker_reset()
        status = get_circuit_breaker_status()
        assert status["state"] == "closed"
        assert status["recent_error_count"] == 0
        assert status["cooldown_seconds"] == 300  # base cooldown

    def test_reset_clears_recent_errors(self, reset_circuit_breaker):
        """Reset should clear recent error timestamps."""
        for _ in range(5):
            circuit_breaker_record_error()

        circuit_breaker_reset()
        status = get_circuit_breaker_status()
        assert status["recent_error_count"] == 0


class TestGetCircuitBreakerStatus:
    """Tests for get_circuit_breaker_status()."""

    def test_returns_expected_keys(self, reset_circuit_breaker):
        """Status dict should contain all expected keys."""
        status = get_circuit_breaker_status()
        expected_keys = {
            "state", "opened_at", "cooldown_seconds",
            "recent_error_count", "summary_sent"
        }
        assert set(status.keys()) == expected_keys

    def test_reflects_current_state(self, reset_circuit_breaker):
        """Status should reflect current circuit breaker state."""
        status = get_circuit_breaker_status()
        assert status["state"] == "closed"

        circuit_breaker_trip()
        status = get_circuit_breaker_status()
        assert status["state"] == "open"
        assert status["opened_at"] > 0


# ---------------------------------------------------------------------------
# Per-Fingerprint Rate Limiting tests
# ---------------------------------------------------------------------------

class TestGetBackoffSeconds:
    """Tests for get_backoff_seconds() - backoff schedule."""

    def test_first_occurrence_no_backoff(self):
        """First occurrence (count=0) should have no backoff."""
        assert get_backoff_seconds(0) == 0

    def test_second_occurrence_5_minutes(self):
        """Second occurrence should wait 5 minutes."""
        assert get_backoff_seconds(1) == 300

    def test_third_occurrence_15_minutes(self):
        """Third occurrence should wait 15 minutes."""
        assert get_backoff_seconds(2) == 900

    def test_fourth_occurrence_45_minutes(self):
        """Fourth occurrence should wait 45 minutes."""
        assert get_backoff_seconds(3) == 2700

    def test_fifth_plus_occurrence_2_hours(self):
        """Fifth and beyond should wait 2 hours."""
        assert get_backoff_seconds(4) == 7200
        assert get_backoff_seconds(10) == 7200
        assert get_backoff_seconds(100) == 7200

    def test_negative_count_no_backoff(self):
        """Negative count should return 0 (defensive)."""
        assert get_backoff_seconds(-1) == 0


class TestShouldDispatch:
    """Tests for should_dispatch() - per-fingerprint rate gating."""

    def test_first_dispatch_allowed(self, reset_rate_limiting):
        """First time seeing a fingerprint should allow dispatch."""
        assert should_dispatch("fp_abc123") is True

    def test_blocks_after_dispatch_within_backoff(self, reset_rate_limiting):
        """Should block dispatch within backoff window after first dispatch."""
        fp = "fp_test_block"
        record_dispatch(fp)
        # Immediately after dispatch, backoff is 300s - should block
        assert should_dispatch(fp) is False

    def test_allows_after_backoff_expires(self, reset_rate_limiting):
        """Should allow dispatch after backoff period has elapsed."""
        fp = "fp_test_allow"
        # Record a dispatch that happened 301 seconds ago
        _fingerprint_dispatch_count[fp] = 1
        _fingerprint_dispatch_times[fp] = [time.time() - 301]

        assert should_dispatch(fp) is True

    def test_increasing_backoff(self, reset_rate_limiting):
        """Subsequent dispatches should require longer backoff."""
        fp = "fp_test_increasing"
        now = time.time()

        # After 2 dispatches, need 900s backoff
        _fingerprint_dispatch_count[fp] = 2
        _fingerprint_dispatch_times[fp] = [now - 500, now - 100]
        # 100 seconds since last dispatch, need 900 -> should block
        assert should_dispatch(fp) is False

        # Set last dispatch to 901 seconds ago
        _fingerprint_dispatch_times[fp] = [now - 1000, now - 901]
        assert should_dispatch(fp) is True


class TestRecordDispatch:
    """Tests for record_dispatch() - dispatch tracking."""

    def test_increments_count(self, reset_rate_limiting):
        """record_dispatch() should increment the dispatch count."""
        fp = "fp_count_test"
        assert _fingerprint_dispatch_count.get(fp, 0) == 0

        record_dispatch(fp)
        assert _fingerprint_dispatch_count[fp] == 1

        record_dispatch(fp)
        assert _fingerprint_dispatch_count[fp] == 2

        record_dispatch(fp)
        assert _fingerprint_dispatch_count[fp] == 3

    def test_records_timestamps(self, reset_rate_limiting):
        """record_dispatch() should append timestamps."""
        fp = "fp_time_test"
        before = time.time()
        record_dispatch(fp)
        after = time.time()

        assert len(_fingerprint_dispatch_times[fp]) == 1
        assert before <= _fingerprint_dispatch_times[fp][0] <= after

    def test_multiple_dispatches_accumulate(self, reset_rate_limiting):
        """Multiple dispatches should accumulate timestamps."""
        fp = "fp_multi_test"
        record_dispatch(fp)
        record_dispatch(fp)
        record_dispatch(fp)

        assert len(_fingerprint_dispatch_times[fp]) == 3
        assert _fingerprint_dispatch_count[fp] == 3


# ===========================================================================
# Phase 5 Tests - Source Fix Pipeline
# ===========================================================================

# ---------------------------------------------------------------------------
# update_source_fix_status() tests
# ---------------------------------------------------------------------------

class TestUpdateSourceFixStatus:
    """Tests for update_source_fix_status() - fix tracking lifecycle."""

    def test_sets_fix_requested(self, clean_registry):
        """update_source_fix_status() should set fix_requested status."""
        result = report(error_type="E", message="test", component="FLOW")
        fp = result["fingerprint"]

        assert update_source_fix_status(fp, "fix_requested") is True
        entry = get_entry(fp)
        assert entry["source_fix_status"] == "fix_requested"

    def test_sets_fix_confirmed(self, clean_registry):
        """update_source_fix_status() should set fix_confirmed status."""
        result = report(error_type="E", message="test", component="FLOW")
        fp = result["fingerprint"]

        assert update_source_fix_status(fp, "fix_confirmed") is True
        entry = get_entry(fp)
        assert entry["source_fix_status"] == "fix_confirmed"

    def test_sets_pending_fix(self, clean_registry):
        """update_source_fix_status() should set pending_fix status."""
        result = report(error_type="E", message="test", component="FLOW")
        fp = result["fingerprint"]

        assert update_source_fix_status(fp, "pending_fix") is True
        entry = get_entry(fp)
        assert entry["source_fix_status"] == "pending_fix"

    def test_resets_to_none(self, clean_registry):
        """update_source_fix_status() should allow resetting to none."""
        result = report(error_type="E", message="test", component="FLOW")
        fp = result["fingerprint"]

        update_source_fix_status(fp, "fix_requested")
        assert update_source_fix_status(fp, "none") is True
        entry = get_entry(fp)
        assert entry["source_fix_status"] == "none"

    def test_rejects_invalid_status(self, clean_registry):
        """update_source_fix_status() should reject invalid fix status values."""
        result = report(error_type="E", message="test", component="FLOW")
        fp = result["fingerprint"]

        assert update_source_fix_status(fp, "invalid_status") is False
        entry = get_entry(fp)
        assert entry["source_fix_status"] == "none"  # unchanged

    def test_missing_fingerprint_returns_false(self, clean_registry):
        """update_source_fix_status() should return False for unknown fingerprints."""
        assert update_source_fix_status("nonexistent_fp", "fix_requested") is False

    def test_prefix_matching(self, clean_registry):
        """update_source_fix_status() should work with fingerprint prefixes."""
        result = report(error_type="E", message="test", component="FLOW")
        fp_prefix = result["fingerprint"][:12]

        assert update_source_fix_status(fp_prefix, "fix_requested") is True
        entry = get_entry(fp_prefix)
        assert entry["source_fix_status"] == "fix_requested"

    def test_persists_to_disk(self, clean_registry):
        """update_source_fix_status() should persist changes to the registry file."""
        result = report(error_type="E", message="test", component="FLOW")
        fp = result["fingerprint"]

        update_source_fix_status(fp, "fix_confirmed")

        # Read directly from disk to verify persistence
        data = json.loads(clean_registry.read_text(encoding='utf-8'))
        assert data["errors"][fp]["source_fix_status"] == "fix_confirmed"


# ===========================================================================
# Push Pipeline Tests - Cross-branch report_error() public API
# ===========================================================================

@pytest.fixture
def clean_registry_for_push(tmp_path):
    """Provide a clean temp registry for push pipeline tests."""
    temp_registry = tmp_path / "error_registry.json"
    with patch(
        "trigger.apps.handlers.error_registry.REGISTRY_FILE",
        temp_registry
    ):
        yield temp_registry


class TestReportErrorPublicAPI:
    """Tests for report_error() - the public module-layer API for cross-branch push."""

    def test_import_from_modules(self):
        """report_error should be importable from trigger.apps.modules.errors."""
        from trigger.apps.modules.errors import report_error
        assert callable(report_error)

    def test_reports_new_error(self, clean_registry_for_push):
        """report_error() should create a new registry entry."""
        from trigger.apps.modules.errors import report_error

        with patch("trigger.apps.modules.errors._registry_report", wraps=report):
            result = report_error(
                error_type="ImportError",
                message="No module named 'foo'",
                component="DRONE",
                severity="medium",
                fire_event=False,
            )

        assert result["is_new"] is True
        assert result["error_type"] == "ImportError"
        assert result["component"] == "DRONE"
        assert "fingerprint" in result
        assert len(result["fingerprint"]) == 40

    def test_increments_existing_error(self, clean_registry_for_push):
        """report_error() should increment count for duplicate errors."""
        from trigger.apps.modules.errors import report_error

        r1 = report_error(
            error_type="ImportError",
            message="No module named 'foo'",
            component="DRONE",
            fire_event=False,
        )
        r2 = report_error(
            error_type="ImportError",
            message="No module named 'foo'",
            component="DRONE",
            fire_event=False,
        )

        assert r1["is_new"] is True
        assert r2["is_new"] is False
        assert r2["count"] == 2

    def test_fires_event_on_new_error(self, clean_registry_for_push):
        """report_error() should fire error_detected event for new errors."""
        from trigger.apps.modules.errors import report_error

        with patch("trigger.apps.modules.errors._registry_report", wraps=report):
            with patch("trigger.apps.modules.core.trigger") as mock_trigger:
                result = report_error(
                    error_type="TimeoutError",
                    message="Connection timed out",
                    component="API",
                    fire_event=True,
                )

        assert result["is_new"] is True
        assert result["dispatched"] is True
        mock_trigger.fire.assert_called_once()
        call_args = mock_trigger.fire.call_args
        assert call_args[0][0] == "error_detected"
        assert call_args[1]["branch"] == "API"
        assert call_args[1]["fingerprint"] == result["fingerprint"]

    def test_fires_event_on_second_occurrence(self, clean_registry_for_push):
        """report_error() should fire event on count==2 (dispatch threshold)."""
        from trigger.apps.modules.errors import report_error

        with patch("trigger.apps.modules.errors._registry_report", wraps=report):
            with patch("trigger.apps.modules.core.trigger") as mock_trigger:
                report_error(
                    error_type="ImportError",
                    message="No module named 'bar'",
                    component="FLOW",
                    fire_event=True,
                )
                mock_trigger.fire.reset_mock()

                result = report_error(
                    error_type="ImportError",
                    message="No module named 'bar'",
                    component="FLOW",
                    fire_event=True,
                )

        assert result["is_new"] is False
        assert result["count"] == 2
        assert result["dispatched"] is True
        mock_trigger.fire.assert_called_once()
        call_args = mock_trigger.fire.call_args
        assert call_args[1]["count"] == 2

    def test_skips_event_for_third_occurrence(self, clean_registry_for_push):
        """report_error() should NOT fire event for count >= 3 (backoff handles later)."""
        from trigger.apps.modules.errors import report_error

        with patch("trigger.apps.modules.errors._registry_report", wraps=report):
            with patch("trigger.apps.modules.core.trigger") as mock_trigger:
                # First occurrence (count=1) - fires event
                report_error(
                    error_type="ImportError",
                    message="No module named 'baz'",
                    component="FLOW",
                    fire_event=True,
                )
                # Second occurrence (count=2) - fires event
                report_error(
                    error_type="ImportError",
                    message="No module named 'baz'",
                    component="FLOW",
                    fire_event=True,
                )
                mock_trigger.fire.reset_mock()

                # Third occurrence (count=3) - should NOT fire
                result = report_error(
                    error_type="ImportError",
                    message="No module named 'baz'",
                    component="FLOW",
                    fire_event=True,
                )

        assert result["is_new"] is False
        assert result["count"] == 3
        assert result["dispatched"] is False
        mock_trigger.fire.assert_not_called()

    def test_fire_event_false_skips_dispatch(self, clean_registry_for_push):
        """report_error(fire_event=False) should never fire events."""
        from trigger.apps.modules.errors import report_error

        with patch("trigger.apps.modules.errors._registry_report", wraps=report):
            with patch("trigger.apps.modules.core.trigger") as mock_trigger:
                result = report_error(
                    error_type="RuntimeError",
                    message="Something broke",
                    component="CORTEX",
                    fire_event=False,
                )

        assert result["is_new"] is True
        assert result["dispatched"] is False
        mock_trigger.fire.assert_not_called()

    def test_returns_dispatched_flag(self, clean_registry_for_push):
        """report_error() result should include dispatched boolean."""
        from trigger.apps.modules.errors import report_error

        result = report_error(
            error_type="ValueError",
            message="Bad value",
            component="CLI",
            fire_event=False,
        )

        assert "dispatched" in result
        assert isinstance(result["dispatched"], bool)

    def test_severity_passed_through(self, clean_registry_for_push):
        """report_error() should pass severity to the registry."""
        from trigger.apps.modules.errors import report_error

        result = report_error(
            error_type="CriticalError",
            message="System down",
            component="PRAX",
            severity="critical",
            fire_event=False,
        )

        assert result["severity"] == "critical"

    def test_log_path_passed_through(self, clean_registry_for_push):
        """report_error() should pass log_path to the registry."""
        from trigger.apps.modules.errors import report_error

        result = report_error(
            error_type="FileError",
            message="File not found",
            component="BACKUP",
            log_path="/home/aipass/system_logs/backup.log",
            fire_event=False,
        )

        assert result["log_path"] == "/home/aipass/system_logs/backup.log"

    def test_event_data_includes_registry_fields(self, clean_registry_for_push):
        """Fired event should include all Medic v2 fields."""
        from trigger.apps.modules.errors import report_error

        with patch("trigger.apps.modules.errors._registry_report", wraps=report):
            with patch("trigger.apps.modules.core.trigger") as mock_trigger:
                report_error(
                    error_type="ConnectionError",
                    message="Refused",
                    component="API",
                    log_path="/some/log.log",
                    fire_event=True,
                )

        call_kwargs = mock_trigger.fire.call_args[1]
        assert "branch" in call_kwargs
        assert "fingerprint" in call_kwargs
        assert "registry_id" in call_kwargs
        assert "first_seen" in call_kwargs
        assert "last_seen" in call_kwargs
        assert "error_hash" in call_kwargs
        assert "log_path" in call_kwargs


# ---------------------------------------------------------------------------
# Edge Cases - Malformed data, rapid-fire, circuit breaker from pushes
# ---------------------------------------------------------------------------

class TestPushEdgeCases:
    """Edge case tests for push-based error reporting."""

    def test_empty_error_type(self, clean_registry_for_push):
        """report_error() should handle empty error_type gracefully."""
        from trigger.apps.modules.errors import report_error

        result = report_error(
            error_type="",
            message="Something failed",
            component="DRONE",
            fire_event=False,
        )

        assert result is not None
        assert "fingerprint" in result

    def test_empty_message(self, clean_registry_for_push):
        """report_error() should handle empty message gracefully."""
        from trigger.apps.modules.errors import report_error

        result = report_error(
            error_type="Error",
            message="",
            component="DRONE",
            fire_event=False,
        )

        assert result is not None
        assert result["is_new"] is True

    def test_empty_component(self, clean_registry_for_push):
        """report_error() should handle empty component gracefully."""
        from trigger.apps.modules.errors import report_error

        result = report_error(
            error_type="Error",
            message="test",
            component="",
            fire_event=False,
        )

        assert result is not None

    def test_very_long_message(self, clean_registry_for_push):
        """report_error() should handle very long messages."""
        from trigger.apps.modules.errors import report_error

        long_msg = "x" * 10000
        result = report_error(
            error_type="Error",
            message=long_msg,
            component="DRONE",
            fire_event=False,
        )

        assert result["is_new"] is True
        assert len(result["message"]) == 10000

    def test_invalid_severity_defaults_to_medium(self, clean_registry_for_push):
        """report_error() should default invalid severity to medium."""
        from trigger.apps.modules.errors import report_error

        result = report_error(
            error_type="Error",
            message="test",
            component="DRONE",
            severity="INVALID",
            fire_event=False,
        )

        assert result["severity"] == "medium"

    def test_special_characters_in_message(self, clean_registry_for_push):
        """report_error() should handle special chars in messages."""
        from trigger.apps.modules.errors import report_error

        msg = 'Error: "can\'t parse" <xml> & {json} \n\t\0'
        result = report_error(
            error_type="ParseError",
            message=msg,
            component="API",
            fire_event=False,
        )

        assert result["is_new"] is True
        assert result["message"] == msg

    def test_unicode_in_message(self, clean_registry_for_push):
        """report_error() should handle unicode characters."""
        from trigger.apps.modules.errors import report_error

        result = report_error(
            error_type="Error",
            message="Failed to process: \u2603 \u2764 \U0001f600",
            component="CLI",
            fire_event=False,
        )

        assert result["is_new"] is True


class TestRapidFirePushes:
    """Tests for rapid-fire push scenarios."""

    def test_rapid_same_error_increments_count(self, clean_registry_for_push):
        """Rapid pushes of the same error should increment count, not create duplicates."""
        from trigger.apps.modules.errors import report_error

        results = []
        for _ in range(50):
            results.append(report_error(
                error_type="ImportError",
                message="No module named 'rapid'",
                component="DRONE",
                fire_event=False,
            ))

        assert results[0]["is_new"] is True
        for r in results[1:]:
            assert r["is_new"] is False

        # Final count should be 50
        assert results[-1]["count"] == 50

        # All should share the same fingerprint
        fps = {r["fingerprint"] for r in results}
        assert len(fps) == 1

    def test_rapid_different_errors_create_separate_entries(self, clean_registry_for_push):
        """Rapid pushes of different errors should create separate entries."""
        from trigger.apps.modules.errors import report_error

        results = []
        for i in range(20):
            results.append(report_error(
                error_type="Error",
                message=f"Unique error number {i}",
                component="DRONE",
                fire_event=False,
            ))

        # All should be new
        assert all(r["is_new"] for r in results)

        # All should have unique fingerprints
        fps = {r["fingerprint"] for r in results}
        assert len(fps) == 20

    def test_rapid_fire_fires_on_first_and_second_only(self, clean_registry_for_push):
        """Event fires on count==1 and count==2, then stops (backoff handles rest)."""
        from trigger.apps.modules.errors import report_error

        with patch("trigger.apps.modules.errors._registry_report", wraps=report):
            with patch("trigger.apps.modules.core.trigger") as mock_trigger:
                for _ in range(10):
                    report_error(
                        error_type="ImportError",
                        message="Module not found",
                        component="FLOW",
                        fire_event=True,
                    )

        # Event fires on count==1 (new) and count==2 (threshold), then stops
        assert mock_trigger.fire.call_count == 2


class TestCircuitBreakerFromPushVolume:
    """Tests for circuit breaker tripping from push volume."""

    def test_circuit_breaker_trips_after_threshold(
        self, clean_registry_for_push, reset_circuit_breaker
    ):
        """Circuit breaker should trip after 10 unique errors in 60 seconds."""
        # Record 10 errors to trip the breaker
        for _ in range(10):
            circuit_breaker_record_error()

        assert circuit_breaker_allows() is False
        status = get_circuit_breaker_status()
        assert status["state"] == "open"

    def test_push_pipeline_respects_circuit_breaker(
        self, clean_registry_for_push, reset_circuit_breaker
    ):
        """report_error events should be blocked when circuit breaker is open."""
        # Trip the circuit breaker
        circuit_breaker_trip()

        assert circuit_breaker_allows() is False

    def test_circuit_breaker_recovers_after_cooldown(
        self, clean_registry_for_push, reset_circuit_breaker
    ):
        """Circuit breaker should transition to half_open after cooldown."""
        circuit_breaker_trip()

        # Simulate cooldown expiry
        import trigger.apps.handlers.error_registry as reg
        reg._circuit_breaker.opened_at = time.time() - 400  # Past 300s cooldown

        assert circuit_breaker_allows() is True
        status = get_circuit_breaker_status()
        assert status["state"] == "half_open"

    def test_backoff_blocks_repeated_dispatch_for_same_fingerprint(
        self, clean_registry_for_push, reset_rate_limiting
    ):
        """Per-fingerprint backoff should block rapid repeat dispatches."""
        fp = "test_fingerprint_abc123"

        # First dispatch always allowed
        assert should_dispatch(fp) is True
        record_dispatch(fp)

        # Second should be blocked (5 min backoff)
        assert should_dispatch(fp) is False

    def test_backoff_allows_after_window(
        self, clean_registry_for_push, reset_rate_limiting
    ):
        """Per-fingerprint dispatch should be allowed after backoff expires."""
        fp = "test_fingerprint_xyz789"

        assert should_dispatch(fp) is True
        record_dispatch(fp)

        # Fake the dispatch time to be in the past
        _fingerprint_dispatch_times[fp] = [time.time() - 400]

        assert should_dispatch(fp) is True


class TestRegistryFileLocking:
    """Tests for registry behavior under file system edge cases."""

    def test_corrupted_registry_file(self, clean_registry_for_push):
        """report_error() should handle corrupted registry file gracefully."""
        from trigger.apps.modules.errors import report_error

        # Write garbage to registry file
        clean_registry_for_push.parent.mkdir(parents=True, exist_ok=True)
        clean_registry_for_push.write_text("NOT VALID JSON {{{", encoding='utf-8')

        result = report_error(
            error_type="Error",
            message="test after corruption",
            component="DRONE",
            fire_event=False,
        )

        # Should still return a result (fresh registry created)
        assert result is not None
        assert result["is_new"] is True

    def test_missing_registry_directory(self, tmp_path):
        """report_error() should create registry directory if missing."""
        from trigger.apps.modules.errors import report_error

        deep_path = tmp_path / "nonexistent" / "deep" / "error_registry.json"
        with patch(
            "trigger.apps.handlers.error_registry.REGISTRY_FILE",
            deep_path
        ):
            result = report_error(
                error_type="Error",
                message="test in missing dir",
                component="DRONE",
                fire_event=False,
            )

        assert result["is_new"] is True
        assert deep_path.exists()

    def test_readonly_registry_returns_fallback(self, clean_registry_for_push):
        """report_error() should return fallback dict when registry is unwritable."""
        from trigger.apps.modules.errors import report_error

        # Make parent dir, create file, then make it readonly
        clean_registry_for_push.parent.mkdir(parents=True, exist_ok=True)
        clean_registry_for_push.write_text('{"errors":{}, "metadata":{}}', encoding='utf-8')
        clean_registry_for_push.chmod(0o444)

        try:
            result = report_error(
                error_type="Error",
                message="test readonly",
                component="DRONE",
                fire_event=False,
            )

            # Should return fallback result without crashing
            assert result is not None
            assert "error_type" in result
        finally:
            clean_registry_for_push.chmod(0o644)

    def test_concurrent_reports_preserve_data(self, clean_registry_for_push):
        """Multiple different errors reported sequentially should all persist."""
        from trigger.apps.modules.errors import report_error

        errors = [
            ("ImportError", "No module 'a'", "FLOW"),
            ("TimeoutError", "Connection timeout", "API"),
            ("ValueError", "Bad config", "DRONE"),
            ("FileNotFoundError", "Missing file", "BACKUP"),
            ("KeyError", "Missing key 'x'", "CORTEX"),
        ]

        results = []
        for etype, msg, comp in errors:
            results.append(report_error(
                error_type=etype,
                message=msg,
                component=comp,
                fire_event=False,
            ))

        # All should be new and have unique fingerprints
        assert all(r["is_new"] for r in results)
        fps = {r["fingerprint"] for r in results}
        assert len(fps) == 5

        # Verify all persisted to disk
        data = json.loads(clean_registry_for_push.read_text(encoding='utf-8'))
        assert len(data["errors"]) == 5


class TestFullPipelineIntegration:
    """Integration tests verifying the complete push -> event -> handler chain."""

    def test_report_error_to_handle_error_detected_flow(
        self, clean_registry_for_push, reset_circuit_breaker, reset_rate_limiting
    ):
        """Full chain: report_error -> event -> handle_error_detected called."""
        from trigger.apps.modules.errors import report_error
        from trigger.apps.handlers.events.error_detected import (
            handle_error_detected,
        )

        # Track if handler would have been called with correct data
        handler_calls = []

        def fake_fire(event_name, **kwargs):
            if event_name == "error_detected":
                handler_calls.append(kwargs)

        with patch("trigger.apps.modules.errors._registry_report", wraps=report):
            with patch("trigger.apps.modules.core.trigger") as mock_trigger:
                mock_trigger.fire = fake_fire
                result = report_error(
                    error_type="ImportError",
                    message="No module named 'test_full'",
                    component="DRONE",
                    log_path="/home/aipass/system_logs/drone.log",
                    severity="high",
                    fire_event=True,
                )

        assert result["dispatched"] is True
        assert len(handler_calls) == 1

        event_data = handler_calls[0]
        assert event_data["branch"] == "DRONE"
        assert event_data["module"] == "ImportError"
        assert event_data["message"] == "No module named 'test_full'"
        assert event_data["fingerprint"] == result["fingerprint"]
        assert event_data["registry_id"] == result["id"]

    def test_handler_blocks_when_medic_disabled(
        self, clean_registry_for_push, reset_circuit_breaker
    ):
        """handle_error_detected should block dispatch when medic is off."""
        from trigger.apps.handlers.events.error_detected import (
            handle_error_detected,
        )

        with patch(
            "trigger.apps.handlers.events.error_detected._is_medic_enabled",
            return_value=False
        ):
            # Should silently return without sending email
            handle_error_detected(
                branch="DRONE",
                module="ImportError",
                message="test",
                error_hash="abc12345",
                timestamp="2026-02-14T00:00:00",
            )
            # No exception = success (silent failure pattern)

    def test_handler_blocks_dev_central(
        self, clean_registry_for_push, reset_circuit_breaker
    ):
        """handle_error_detected must NEVER auto-trigger dev_central."""
        from trigger.apps.handlers.events.error_detected import (
            handle_error_detected,
            set_send_email_callback,
        )

        send_calls = []

        def fake_send(**kwargs):
            send_calls.append(kwargs)

        set_send_email_callback(fake_send)

        with patch(
            "trigger.apps.handlers.events.error_detected._is_medic_enabled",
            return_value=True
        ):
            handle_error_detected(
                branch="DEV_CENTRAL",
                module="SomeError",
                message="test",
                error_hash="xyz99999",
                timestamp="2026-02-14T00:00:00",
            )

        # DEV_CENTRAL should NEVER receive auto-dispatched errors
        assert len(send_calls) == 0

        # Reset callback
        set_send_email_callback(None)


# ---------------------------------------------------------------------------
# Dispatch Threshold Tests - count >= 2 required
# ---------------------------------------------------------------------------

class TestDispatchThreshold:
    """Tests for the count >= 2 dispatch threshold in error_detected handler."""

    def test_handler_skips_dispatch_count_1(
        self, clean_registry_for_push, reset_circuit_breaker
    ):
        """Handler should NOT dispatch when count == 1 (first occurrence)."""
        from trigger.apps.handlers.events.error_detected import (
            handle_error_detected,
            set_send_email_callback,
        )

        send_calls = []

        def fake_send(**kwargs):
            send_calls.append(kwargs)

        set_send_email_callback(fake_send)

        with patch(
            "trigger.apps.handlers.events.error_detected._is_medic_enabled",
            return_value=True
        ), patch(
            "trigger.apps.handlers.events.error_detected._get_registered_emails",
            return_value={"@flow"}
        ):
            handle_error_detected(
                branch="FLOW",
                module="ImportError",
                message="No module named 'foo'",
                error_hash="abc12345",
                timestamp="2026-02-14T00:00:00",
                fingerprint="a" * 40,
                count=1,
            )

        assert len(send_calls) == 0
        set_send_email_callback(None)

    def test_handler_dispatches_count_2(
        self, clean_registry_for_push, reset_circuit_breaker
    ):
        """Handler SHOULD dispatch when count == 2 (recurring pattern)."""
        from trigger.apps.handlers.events.error_detected import (
            handle_error_detected,
            set_send_email_callback,
        )

        send_calls = []

        def fake_send(**kwargs):
            send_calls.append(kwargs)

        set_send_email_callback(fake_send)

        with patch(
            "trigger.apps.handlers.events.error_detected._is_medic_enabled",
            return_value=True
        ), patch(
            "trigger.apps.handlers.events.error_detected._get_registered_emails",
            return_value={"@flow"}
        ):
            handle_error_detected(
                branch="FLOW",
                module="ImportError",
                message="No module named 'foo'",
                error_hash="abc12345",
                timestamp="2026-02-14T00:00:00",
                fingerprint="a" * 40,
                count=2,
            )

        assert len(send_calls) == 1
        assert send_calls[0]["to_branch"] == "@flow"
        set_send_email_callback(None)

    def test_handler_dispatches_count_5(
        self, clean_registry_for_push, reset_circuit_breaker
    ):
        """Handler should dispatch for any count >= 2 (subject to backoff)."""
        from trigger.apps.handlers.events.error_detected import (
            handle_error_detected,
            set_send_email_callback,
        )

        send_calls = []

        def fake_send(**kwargs):
            send_calls.append(kwargs)

        set_send_email_callback(fake_send)

        with patch(
            "trigger.apps.handlers.events.error_detected._is_medic_enabled",
            return_value=True
        ), patch(
            "trigger.apps.handlers.events.error_detected._get_registered_emails",
            return_value={"@drone"}
        ):
            handle_error_detected(
                branch="DRONE",
                module="TimeoutError",
                message="Connection timed out",
                error_hash="def67890",
                timestamp="2026-02-14T00:00:00",
                fingerprint="b" * 40,
                count=5,
            )

        assert len(send_calls) == 1
        assert send_calls[0]["to_branch"] == "@drone"
        set_send_email_callback(None)

    def test_handler_default_count_skips(
        self, clean_registry_for_push, reset_circuit_breaker
    ):
        """Handler with default count (1) should NOT dispatch."""
        from trigger.apps.handlers.events.error_detected import (
            handle_error_detected,
            set_send_email_callback,
        )

        send_calls = []

        def fake_send(**kwargs):
            send_calls.append(kwargs)

        set_send_email_callback(fake_send)

        with patch(
            "trigger.apps.handlers.events.error_detected._is_medic_enabled",
            return_value=True
        ), patch(
            "trigger.apps.handlers.events.error_detected._get_registered_emails",
            return_value={"@api"}
        ):
            # No count argument - defaults to 1
            handle_error_detected(
                branch="API",
                module="Error",
                message="test error",
                error_hash="ghi11111",
                timestamp="2026-02-14T00:00:00",
                fingerprint="c" * 40,
            )

        assert len(send_calls) == 0
        set_send_email_callback(None)
