#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_cursor_lock_handler.py - Test cursor lock handler functions
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy/tests
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Test file for speakeasy cursor lock handler
#   - Mocks subprocess xdotool calls
# =============================================

"""Tests for cursor_lock_handler.py - cursor position locking functions."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest
import subprocess

# Add apps directory to path so 'handlers' package resolves
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

from handlers.cursor_lock_handler import (
    get_active_window,
    lock_cursor,
    unlock_cursor,
    restore_position,
    is_locked
)


class TestGetActiveWindow:
    """Tests for get_active_window function."""

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_gets_window_info_successfully(self, mock_run):
        """Test successfully gets active window information."""
        # Mock window ID call
        window_result = Mock()
        window_result.returncode = 0
        window_result.stdout = "12345678\n"

        # Mock window name call
        name_result = Mock()
        name_result.returncode = 0
        name_result.stdout = "Test Window\n"

        # Mock cursor position call
        cursor_result = Mock()
        cursor_result.returncode = 0
        cursor_result.stdout = "X=100\nY=200\nSCREEN=0\nWINDOW=12345678\n"

        mock_run.side_effect = [window_result, name_result, cursor_result]

        result = get_active_window()

        assert result['window_id'] == 12345678
        assert result['window_name'] == "Test Window"
        assert result['cursor_x'] == 100
        assert result['cursor_y'] == 200

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_handles_missing_window_name(self, mock_run):
        """Test handles failure to get window name."""
        # Window ID succeeds
        window_result = Mock()
        window_result.returncode = 0
        window_result.stdout = "12345678\n"

        # Window name fails
        name_result = Mock()
        name_result.returncode = 1
        name_result.stdout = ""

        # Cursor position succeeds
        cursor_result = Mock()
        cursor_result.returncode = 0
        cursor_result.stdout = "X=100\nY=200\n"

        mock_run.side_effect = [window_result, name_result, cursor_result]

        result = get_active_window()

        assert result['window_id'] == 12345678
        assert result['window_name'] == "Unknown"
        assert result['cursor_x'] == 100

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_raises_on_window_id_failure(self, mock_run):
        """Test raises RuntimeError when can't get window ID."""
        result = Mock()
        result.returncode = 1
        result.stderr = "error"
        mock_run.return_value = result

        with pytest.raises(RuntimeError, match="Failed to get active window"):
            get_active_window()

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_raises_on_cursor_position_failure(self, mock_run):
        """Test raises RuntimeError when can't get cursor position."""
        # Window ID succeeds
        window_result = Mock()
        window_result.returncode = 0
        window_result.stdout = "12345678\n"

        # Window name succeeds
        name_result = Mock()
        name_result.returncode = 0
        name_result.stdout = "Test\n"

        # Cursor position fails
        cursor_result = Mock()
        cursor_result.returncode = 1
        cursor_result.stderr = "error"

        mock_run.side_effect = [window_result, name_result, cursor_result]

        with pytest.raises(RuntimeError, match="Failed to get cursor position"):
            get_active_window()

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_raises_on_xdotool_not_found(self, mock_run):
        """Test raises RuntimeError when xdotool not installed."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(RuntimeError, match="xdotool not found"):
            get_active_window()

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_raises_on_timeout(self, mock_run):
        """Test raises RuntimeError on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("xdotool", 2)

        with pytest.raises(RuntimeError, match="timed out"):
            get_active_window()

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_parses_cursor_position_correctly(self, mock_run):
        """Test correctly parses cursor position from xdotool output."""
        window_result = Mock()
        window_result.returncode = 0
        window_result.stdout = "123\n"

        name_result = Mock()
        name_result.returncode = 0
        name_result.stdout = "Test\n"

        cursor_result = Mock()
        cursor_result.returncode = 0
        cursor_result.stdout = "X=456\nY=789\nSCREEN=0\n"

        mock_run.side_effect = [window_result, name_result, cursor_result]

        result = get_active_window()

        assert result['cursor_x'] == 456
        assert result['cursor_y'] == 789


class TestLockCursor:
    """Tests for lock_cursor function."""

    @patch('handlers.cursor_lock_handler.get_active_window')
    def test_locks_cursor_successfully(self, mock_get_window):
        """Test successfully locks cursor position."""
        # Reset lock state
        import handlers.cursor_lock_handler
        handlers.cursor_lock_handler._lock_state = None

        mock_get_window.return_value = {
            'window_id': 123,
            'window_name': 'Test',
            'cursor_x': 100,
            'cursor_y': 200
        }

        result = lock_cursor()

        assert result['window_id'] == 123
        assert result['cursor_x'] == 100
        assert is_locked()

    @patch('handlers.cursor_lock_handler.get_active_window')
    def test_raises_when_already_locked(self, mock_get_window):
        """Test raises RuntimeError when already locked."""
        # Set lock state
        import handlers.cursor_lock_handler
        handlers.cursor_lock_handler._lock_state = {'test': 'data'}

        with pytest.raises(RuntimeError, match="already locked"):
            lock_cursor()

        # Clean up
        handlers.cursor_lock_handler._lock_state = None

    @patch('handlers.cursor_lock_handler.get_active_window')
    def test_returns_copy_of_state(self, mock_get_window):
        """Test returns a copy of lock state, not reference."""
        import handlers.cursor_lock_handler
        handlers.cursor_lock_handler._lock_state = None

        mock_get_window.return_value = {
            'window_id': 123,
            'cursor_x': 100
        }

        result = lock_cursor()

        # Modify returned dict
        result['window_id'] = 999

        # Get the internal state
        assert handlers.cursor_lock_handler._lock_state['window_id'] == 123

        # Clean up
        handlers.cursor_lock_handler._lock_state = None


class TestUnlockCursor:
    """Tests for unlock_cursor function."""

    def test_clears_lock_state(self):
        """Test clears the lock state."""
        import handlers.cursor_lock_handler
        handlers.cursor_lock_handler._lock_state = {'test': 'data'}

        unlock_cursor()

        assert not is_locked()
        assert handlers.cursor_lock_handler._lock_state is None


class TestRestorePosition:
    """Tests for restore_position function."""

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_restores_with_provided_state(self, mock_run):
        """Test restores cursor position with provided lock state."""
        import handlers.cursor_lock_handler
        handlers.cursor_lock_handler._lock_state = None

        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        lock_state = {
            'window_id': 123,
            'window_name': 'Test',
            'cursor_x': 100,
            'cursor_y': 200
        }

        restore_position(lock_state)

        # Should call windowactivate, mousemove, and click
        assert mock_run.call_count == 3

        # Check calls
        calls = mock_run.call_args_list
        assert 'windowactivate' in str(calls[0])
        assert 'mousemove' in str(calls[1])
        assert 'click' in str(calls[2])

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_restores_with_module_state(self, mock_run):
        """Test restores using module-level lock state."""
        import handlers.cursor_lock_handler
        handlers.cursor_lock_handler._lock_state = {
            'window_id': 456,
            'cursor_x': 50,
            'cursor_y': 75
        }

        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        restore_position()

        assert mock_run.call_count == 3

        # Clean up
        handlers.cursor_lock_handler._lock_state = None

    def test_raises_when_no_lock_state(self):
        """Test raises RuntimeError when no lock state available."""
        import handlers.cursor_lock_handler
        handlers.cursor_lock_handler._lock_state = None

        with pytest.raises(RuntimeError, match="No lock state available"):
            restore_position()

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_raises_on_xdotool_not_found(self, mock_run):
        """Test raises RuntimeError when xdotool not installed."""
        mock_run.side_effect = FileNotFoundError()

        lock_state = {'window_id': 123, 'cursor_x': 100, 'cursor_y': 200}

        with pytest.raises(RuntimeError, match="xdotool not found"):
            restore_position(lock_state)

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_raises_on_timeout(self, mock_run):
        """Test raises RuntimeError on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("xdotool", 2)

        lock_state = {'window_id': 123, 'cursor_x': 100, 'cursor_y': 200}

        with pytest.raises(RuntimeError, match="timed out"):
            restore_position(lock_state)

    @patch('handlers.cursor_lock_handler.subprocess.run')
    def test_calls_xdotool_with_correct_params(self, mock_run):
        """Test calls xdotool with correct window ID and coordinates."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        lock_state = {
            'window_id': 999,
            'cursor_x': 250,
            'cursor_y': 350
        }

        restore_position(lock_state)

        calls = mock_run.call_args_list

        # Check windowactivate call has correct window ID
        activate_cmd = calls[0][0][0]
        assert '999' in activate_cmd

        # Check mousemove call has correct coordinates
        mousemove_cmd = calls[1][0][0]
        assert '250' in mousemove_cmd
        assert '350' in mousemove_cmd


class TestIsLocked:
    """Tests for is_locked function."""

    def test_returns_true_when_locked(self):
        """Test returns True when cursor is locked."""
        import handlers.cursor_lock_handler
        handlers.cursor_lock_handler._lock_state = {'test': 'data'}

        assert is_locked() is True

        # Clean up
        handlers.cursor_lock_handler._lock_state = None

    def test_returns_false_when_not_locked(self):
        """Test returns False when cursor is not locked."""
        import handlers.cursor_lock_handler
        handlers.cursor_lock_handler._lock_state = None

        assert is_locked() is False
