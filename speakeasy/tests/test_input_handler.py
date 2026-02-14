#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_input_handler.py - Test input handler functions
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy/tests
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Test file for speakeasy input handler
#   - Mocks pynput and subprocess calls
# =============================================

"""Tests for input_handler.py - text injection functions."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pytest
import subprocess

# Add apps directory to path so 'handlers' package resolves
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

from handlers.input_handler import (
    type_text,
    paste_text,
    _type_with_pynput,
    _type_with_xdotool
)


class TestTypeText:
    """Tests for type_text function."""

    @patch('handlers.input_handler._type_with_pynput')
    def test_uses_pynput_method(self, mock_type_pynput):
        """Test type_text uses pynput method."""
        type_text("hello", method="pynput", key_delay=0.005)
        mock_type_pynput.assert_called_once_with("hello", 0.005)

    @patch('handlers.input_handler._type_with_xdotool')
    def test_uses_xdotool_method(self, mock_type_xdotool):
        """Test type_text uses xdotool method."""
        type_text("hello", method="xdotool", key_delay=0.005)
        mock_type_xdotool.assert_called_once_with("hello", 0.005)

    def test_raises_on_invalid_method(self):
        """Test raises ValueError for unsupported method."""
        with pytest.raises(ValueError, match="Unsupported typing method"):
            type_text("hello", method="invalid")

    @patch('handlers.input_handler._type_with_pynput')
    def test_handles_empty_text(self, mock_type_pynput):
        """Test handles empty text gracefully."""
        type_text("", method="pynput")
        # Should return early without calling type function
        mock_type_pynput.assert_not_called()


class TestPasteText:
    """Tests for paste_text function."""

    @patch('handlers.input_handler.subprocess.Popen')
    @patch('handlers.input_handler.keyboard.Controller')
    @patch('handlers.input_handler.time.sleep')
    def test_pastes_text_successfully(self, mock_sleep, mock_controller_cls, mock_popen):
        """Test successful text paste via clipboard."""
        # Mock xclip process - use MagicMock for context manager support
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process

        # Mock keyboard controller
        mock_controller = MagicMock()
        mock_controller_cls.return_value = mock_controller

        paste_text("hello world")

        # Should call xclip
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert call_args == ['xclip', '-selection', 'clipboard']

        # Should communicate with correct text
        mock_process.communicate.assert_called_once()
        call_kwargs = mock_process.communicate.call_args[1]
        assert call_kwargs['input'] == b"hello world"

        # Should press Ctrl+V (using context manager)
        assert mock_controller.pressed.call_count >= 1

    @patch('handlers.input_handler.subprocess.Popen')
    def test_handles_empty_text(self, mock_popen):
        """Test handles empty text gracefully."""
        paste_text("")
        # Should return early without calling xclip
        mock_popen.assert_not_called()

    @patch('handlers.input_handler.subprocess.Popen')
    def test_raises_on_xclip_failure(self, mock_popen):
        """Test raises RuntimeError when xclip fails."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"error message")
        mock_popen.return_value = mock_process

        with pytest.raises(RuntimeError, match="xclip failed"):
            paste_text("hello")

    @patch('handlers.input_handler.subprocess.Popen')
    def test_raises_on_timeout(self, mock_popen):
        """Test raises RuntimeError on timeout."""
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired("xclip", 2)
        mock_popen.return_value = mock_process

        with pytest.raises(RuntimeError, match="timed out"):
            paste_text("hello")

    @patch('handlers.input_handler.subprocess.Popen')
    def test_raises_on_xclip_not_found(self, mock_popen):
        """Test raises RuntimeError when xclip not installed."""
        mock_popen.side_effect = FileNotFoundError()

        with pytest.raises(RuntimeError, match="xclip not found"):
            paste_text("hello")


class TestTypeWithPynput:
    """Tests for _type_with_pynput function."""

    @patch('handlers.input_handler.keyboard.Controller')
    @patch('handlers.input_handler.time.sleep')
    def test_types_each_character(self, mock_sleep, mock_controller_cls):
        """Test types each character with press/release."""
        mock_controller = Mock()
        mock_controller_cls.return_value = mock_controller

        _type_with_pynput("abc", key_delay=0.01)

        # Should press and release each character
        assert mock_controller.press.call_count == 3
        assert mock_controller.release.call_count == 3

        # Check the characters
        press_calls = mock_controller.press.call_args_list
        assert press_calls[0][0][0] == "a"
        assert press_calls[1][0][0] == "b"
        assert press_calls[2][0][0] == "c"

    @patch('handlers.input_handler.keyboard.Controller')
    @patch('handlers.input_handler.time.sleep')
    def test_applies_key_delay(self, mock_sleep, mock_controller_cls):
        """Test key delay is applied between keystrokes."""
        mock_controller = Mock()
        mock_controller_cls.return_value = mock_controller

        _type_with_pynput("ab", key_delay=0.05)

        # Should sleep after each character
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.05)

    @patch('handlers.input_handler.keyboard.Controller')
    def test_no_delay_when_zero(self, mock_controller_cls):
        """Test no delay when key_delay is 0."""
        mock_controller = Mock()
        mock_controller_cls.return_value = mock_controller

        with patch('handlers.input_handler.time.sleep') as mock_sleep:
            _type_with_pynput("abc", key_delay=0)
            # Sleep should not be called with 0 delay
            mock_sleep.assert_not_called()

    @patch('handlers.input_handler.keyboard.Controller')
    def test_handles_typing_errors_gracefully(self, mock_controller_cls):
        """Test continues on character typing errors."""
        mock_controller = Mock()
        mock_controller_cls.return_value = mock_controller

        # Make press fail on second character
        mock_controller.press.side_effect = [None, Exception("Can't type"), None]

        # Should not raise, just skip the problematic character
        _type_with_pynput("abc", key_delay=0)

        # Should still try to type all characters
        assert mock_controller.press.call_count == 3


class TestTypeWithXdotool:
    """Tests for _type_with_xdotool function."""

    @patch('handlers.input_handler.subprocess.run')
    def test_calls_xdotool_correctly(self, mock_run):
        """Test calls xdotool with correct parameters."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        _type_with_xdotool("hello world", key_delay=0.005)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "xdotool"
        assert call_args[1] == "type"
        assert call_args[2] == "--delay"
        assert "hello world" in call_args

    @patch('handlers.input_handler.subprocess.run')
    def test_converts_delay_to_milliseconds(self, mock_run):
        """Test converts delay from seconds to milliseconds."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        _type_with_xdotool("test", key_delay=0.5)

        call_args = mock_run.call_args[0][0]
        delay_index = call_args.index("--delay")
        delay_value = call_args[delay_index + 1]
        assert delay_value == "500"  # 0.5 seconds = 500ms

    @patch('handlers.input_handler.subprocess.run')
    def test_raises_on_xdotool_failure(self, mock_run):
        """Test raises RuntimeError when xdotool fails."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "error message"
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="xdotool failed"):
            _type_with_xdotool("test", key_delay=0.01)

    @patch('handlers.input_handler.subprocess.run')
    def test_raises_on_xdotool_not_found(self, mock_run):
        """Test raises RuntimeError when xdotool not installed."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(RuntimeError, match="xdotool not found"):
            _type_with_xdotool("test", key_delay=0.01)

    @patch('handlers.input_handler.subprocess.run')
    def test_raises_on_timeout(self, mock_run):
        """Test raises RuntimeError on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("xdotool", 30)

        with pytest.raises(RuntimeError, match="timed out"):
            _type_with_xdotool("test", key_delay=0.01)

    @patch('handlers.input_handler.subprocess.run')
    def test_handles_special_characters(self, mock_run):
        """Test handles special characters in text."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        special_text = "hello@world.com"
        _type_with_xdotool(special_text, key_delay=0.01)

        # Should pass text after -- to prevent interpretation
        call_args = mock_run.call_args[0][0]
        assert "--" in call_args
        assert special_text in call_args
