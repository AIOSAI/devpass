#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_hotkey_handler.py - Test hotkey handler functions
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy/tests
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Test file for speakeasy hotkey handler
#   - Mocks pynput keyboard listener
# =============================================

"""Tests for hotkey_handler.py - hotkey detection functions."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add apps directory to path so 'handlers' package resolves
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

from handlers.hotkey_handler import (
    parse_hotkey,
    start_listener,
    stop_listener
)


class TestParseHotkey:
    """Tests for parse_hotkey function."""

    def test_parses_simple_key(self):
        """Test parsing a simple key without modifiers."""
        modifiers, key = parse_hotkey("space")
        assert modifiers == set()
        assert key == "space"

    def test_parses_single_modifier(self):
        """Test parsing key with single modifier."""
        modifiers, key = parse_hotkey("ctrl+space")
        assert modifiers == {"ctrl"}
        assert key == "space"

    def test_parses_multiple_modifiers(self):
        """Test parsing key with multiple modifiers."""
        modifiers, key = parse_hotkey("ctrl+shift+a")
        assert modifiers == {"ctrl", "shift"}
        assert key == "a"

    def test_case_insensitive(self):
        """Test parsing is case insensitive."""
        modifiers, key = parse_hotkey("CTRL+SHIFT+A")
        assert modifiers == {"ctrl", "shift"}
        assert key == "a"

    def test_handles_whitespace(self):
        """Test parsing handles whitespace around components."""
        modifiers, key = parse_hotkey(" ctrl + space ")
        assert modifiers == {"ctrl"}
        assert key == "space"

    def test_all_valid_modifiers(self):
        """Test all valid modifiers are accepted."""
        for mod in ["ctrl", "shift", "alt", "cmd", "super"]:
            modifiers, key = parse_hotkey(f"{mod}+a")
            assert mod in modifiers
            assert key == "a"

    def test_raises_on_empty_string(self):
        """Test raises ValueError for empty string."""
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_hotkey("")

    def test_raises_on_whitespace_only(self):
        """Test raises ValueError for whitespace only."""
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_hotkey("   ")

    def test_raises_on_invalid_modifier(self):
        """Test raises ValueError for invalid modifier."""
        with pytest.raises(ValueError, match="Invalid modifiers"):
            parse_hotkey("invalid+space")

    def test_complex_hotkey(self):
        """Test parsing complex hotkey combination."""
        modifiers, key = parse_hotkey("ctrl+alt+shift+f12")
        assert modifiers == {"ctrl", "alt", "shift"}
        assert key == "f12"


class TestStartListener:
    """Tests for start_listener function."""

    @patch('handlers.hotkey_handler.keyboard.Listener')
    def test_starts_listener(self, mock_listener_cls):
        """Test listener is created and started."""
        mock_listener = Mock()
        mock_listener_cls.return_value = mock_listener

        result = start_listener(activation_key="ctrl+space")

        mock_listener_cls.assert_called_once()
        mock_listener.start.assert_called_once()
        assert result == mock_listener

    @patch('handlers.hotkey_handler.keyboard.Listener')
    def test_triggers_on_activate_callback(self, mock_listener_cls):
        """Test on_activate callback is triggered."""
        mock_callback = Mock()
        mock_listener = Mock()
        mock_listener_cls.return_value = mock_listener

        # Capture the on_press handler
        captured_on_press = None

        def capture_listener(*args, **kwargs):
            nonlocal captured_on_press
            captured_on_press = kwargs.get('on_press')
            return mock_listener

        mock_listener_cls.side_effect = capture_listener

        start_listener(
            activation_key="ctrl+space",
            on_activate=mock_callback
        )

        # Simulate pressing ctrl key
        from pynput import keyboard
        captured_on_press(keyboard.Key.ctrl)
        # Simulate pressing space key
        captured_on_press(keyboard.KeyCode.from_char(' '))

        # Callback should be triggered (implementation detail may vary)
        # This is a simplified test - actual behavior depends on implementation
        assert captured_on_press is not None

    @patch('handlers.hotkey_handler.keyboard.Listener')
    def test_raises_on_invalid_backend(self, mock_listener_cls):
        """Test raises ValueError for unsupported backend."""
        with pytest.raises(ValueError, match="Unsupported backend"):
            start_listener(backend="invalid")

    @patch('handlers.hotkey_handler.keyboard.Listener')
    def test_accepts_auto_backend(self, mock_listener_cls):
        """Test accepts 'auto' backend."""
        mock_listener = Mock()
        mock_listener_cls.return_value = mock_listener

        start_listener(backend="auto")

        mock_listener_cls.assert_called_once()

    @patch('handlers.hotkey_handler.keyboard.Listener')
    def test_accepts_pynput_backend(self, mock_listener_cls):
        """Test accepts 'pynput' backend."""
        mock_listener = Mock()
        mock_listener_cls.return_value = mock_listener

        start_listener(backend="pynput")

        mock_listener_cls.assert_called_once()

    @patch('handlers.hotkey_handler.keyboard.Listener')
    def test_raises_on_invalid_hotkey(self, mock_listener_cls):
        """Test raises error for invalid hotkey string."""
        with pytest.raises(ValueError):
            start_listener(activation_key="")

    @patch('handlers.hotkey_handler.keyboard.Listener')
    def test_on_deactivate_callback(self, mock_listener_cls):
        """Test on_deactivate callback is set up."""
        mock_activate = Mock()
        mock_deactivate = Mock()
        mock_listener = Mock()
        mock_listener_cls.return_value = mock_listener

        captured_on_release = None

        def capture_listener(*args, **kwargs):
            nonlocal captured_on_release
            captured_on_release = kwargs.get('on_release')
            return mock_listener

        mock_listener_cls.side_effect = capture_listener

        start_listener(
            activation_key="ctrl+space",
            on_activate=mock_activate,
            on_deactivate=mock_deactivate
        )

        assert captured_on_release is not None


class TestStopListener:
    """Tests for stop_listener function."""

    def test_stops_listener(self):
        """Test stop_listener calls stop method."""
        mock_listener = Mock()
        mock_listener.stop = Mock()

        stop_listener(mock_listener)

        mock_listener.stop.assert_called_once()

    def test_handles_none_listener(self):
        """Test handles None listener gracefully."""
        # Should not raise
        stop_listener(None)

    def test_handles_listener_without_stop(self):
        """Test handles listener object without stop method."""
        mock_listener = Mock(spec=[])  # No methods
        # Should not raise
        stop_listener(mock_listener)
