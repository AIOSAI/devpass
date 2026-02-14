#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_integration.py - Integration tests for speakeasy modules
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy/tests
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Integration tests for module-level orchestration
#   - Tests module imports and handle_command interfaces
# =============================================

"""Integration tests for speakeasy modules - tests orchestration layer."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

# Add aipass_core for prax imports
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Mock prax logger before importing modules
mock_logger = Mock()
sys.modules['prax'] = type(sys)('prax')
sys.modules['prax.apps'] = type(sys)('prax.apps')
sys.modules['prax.apps.modules'] = type(sys)('prax.apps.modules')
sys.modules['prax.apps.modules.logger'] = type(sys)('prax.apps.modules.logger')
sys.modules['prax.apps.modules.logger'].system_logger = mock_logger


class TestModuleImports:
    """Test that all modules can be imported without errors."""

    def test_audio_module_imports(self):
        """Test audio_module can be imported."""
        try:
            from modules import audio_module
            assert audio_module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import audio_module: {e}")

    def test_config_module_imports(self):
        """Test config_module can be imported."""
        try:
            from modules import config_module
            assert config_module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import config_module: {e}")

    def test_input_module_imports(self):
        """Test input_module can be imported."""
        try:
            from modules import input_module
            assert input_module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import input_module: {e}")

    def test_ui_module_imports(self):
        """Test ui_module can be imported."""
        # Mock PyQt5 first
        sys.modules['PyQt5'] = MagicMock()
        sys.modules['PyQt5.QtWidgets'] = MagicMock()
        sys.modules['PyQt5.QtGui'] = MagicMock()
        sys.modules['PyQt5.QtCore'] = MagicMock()

        try:
            from modules import ui_module
            assert ui_module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import ui_module: {e}")


class TestHandlerImports:
    """Test that all handlers can be imported without errors."""

    def test_audio_handler_imports(self):
        """Test audio_handler can be imported."""
        try:
            from handlers import audio_handler
            assert audio_handler is not None
        except ImportError as e:
            pytest.fail(f"Failed to import audio_handler: {e}")

    def test_transcription_handler_imports(self):
        """Test transcription_handler can be imported."""
        try:
            from handlers import transcription_handler
            assert transcription_handler is not None
        except ImportError as e:
            pytest.fail(f"Failed to import transcription_handler: {e}")

    def test_hotkey_handler_imports(self):
        """Test hotkey_handler can be imported."""
        try:
            from handlers import hotkey_handler
            assert hotkey_handler is not None
        except ImportError as e:
            pytest.fail(f"Failed to import hotkey_handler: {e}")

    def test_input_handler_imports(self):
        """Test input_handler can be imported."""
        try:
            from handlers import input_handler
            assert input_handler is not None
        except ImportError as e:
            pytest.fail(f"Failed to import input_handler: {e}")

    def test_cursor_lock_handler_imports(self):
        """Test cursor_lock_handler can be imported."""
        try:
            from handlers import cursor_lock_handler
            assert cursor_lock_handler is not None
        except ImportError as e:
            pytest.fail(f"Failed to import cursor_lock_handler: {e}")

    def test_config_handler_imports(self):
        """Test config_handler can be imported."""
        try:
            from handlers import config_handler
            assert config_handler is not None
        except ImportError as e:
            pytest.fail(f"Failed to import config_handler: {e}")

    def test_ui_handler_imports(self):
        """Test ui_handler can be imported."""
        # Mock PyQt5 first
        sys.modules['PyQt5'] = MagicMock()
        sys.modules['PyQt5.QtWidgets'] = MagicMock()
        sys.modules['PyQt5.QtGui'] = MagicMock()
        sys.modules['PyQt5.QtCore'] = MagicMock()

        try:
            from handlers import ui_handler
            assert ui_handler is not None
        except ImportError as e:
            pytest.fail(f"Failed to import ui_handler: {e}")


class TestModuleHandleCommand:
    """Test that modules have handle_command functions with correct signatures."""

    def test_audio_module_has_handle_command(self):
        """Test audio_module has handle_command function."""
        from modules import audio_module
        assert hasattr(audio_module, 'handle_command')
        assert callable(audio_module.handle_command)

    def test_config_module_has_handle_command(self):
        """Test config_module has handle_command function."""
        from modules import config_module
        assert hasattr(config_module, 'handle_command')
        assert callable(config_module.handle_command)

    def test_input_module_has_handle_command(self):
        """Test input_module has handle_command function."""
        from modules import input_module
        assert hasattr(input_module, 'handle_command')
        assert callable(input_module.handle_command)

    def test_ui_module_has_handle_command(self):
        """Test ui_module has handle_command function."""
        # Mock PyQt5 first
        sys.modules['PyQt5'] = MagicMock()
        sys.modules['PyQt5.QtWidgets'] = MagicMock()
        sys.modules['PyQt5.QtGui'] = MagicMock()
        sys.modules['PyQt5.QtCore'] = MagicMock()

        from modules import ui_module
        assert hasattr(ui_module, 'handle_command')
        assert callable(ui_module.handle_command)


class TestAudioModuleIntegration:
    """Integration tests for audio_module."""

    @patch('modules.audio_module.audio_handler')
    @patch('modules.audio_module.transcription_handler')
    def test_handle_unknown_command_returns_false(self, mock_trans, mock_audio):
        """Test handle_command returns False for unknown commands."""
        from modules import audio_module

        result = audio_module.handle_command("unknown-command", {})
        assert result is False

    @patch('modules.audio_module.audio_handler.test_microphone')
    def test_handle_test_audio_command(self, mock_test_mic):
        """Test handle_command processes test-audio command."""
        from modules import audio_module

        mock_test_mic.return_value = {
            'success': True,
            'max_amplitude': 1000,
            'rms_level': 500.0
        }

        result = audio_module.handle_command("test-audio", {'duration': 3})
        assert result is True
        mock_test_mic.assert_called_once_with(duration=3)


class TestConfigModuleIntegration:
    """Integration tests for config_module."""

    def test_handle_unknown_command_returns_false(self):
        """Test handle_command returns False for unknown commands."""
        from modules import config_module

        result = config_module.handle_command("unknown-command", {})
        assert result is False

    @patch('modules.config_module.config_handler.load_config')
    @patch('modules.config_module.config_handler.get_default_config')
    def test_handle_load_command(self, mock_default, mock_load):
        """Test handle_command processes config show command."""
        from modules import config_module

        mock_load.return_value = {'test': 'config'}
        mock_default.return_value = {'test': 'default'}

        # config module needs "config" command with subcommand
        result = config_module.handle_command("config", ["show"])
        assert result is True

    @patch('modules.config_module.config_handler.load_config')
    @patch('modules.config_module.config_handler.get_default_config')
    @patch('modules.config_module.config_handler.set_value')
    @patch('modules.config_module.config_handler.save_config')
    @patch('modules.config_module.config_handler.parse_value')
    def test_handle_save_command(self, mock_parse, mock_save, mock_set, mock_default, mock_load):
        """Test handle_command processes config set command."""
        from modules import config_module

        mock_load.return_value = {'model': {'name': 'base.en'}}
        mock_default.return_value = {'model': {'name': 'base.en'}}
        mock_parse.return_value = 'small.en'
        mock_set.return_value = (True, [])

        result = config_module.handle_command("config", ["set", "model.name", "small.en"])
        assert result is True
        mock_save.assert_called_once()


class TestInputModuleIntegration:
    """Integration tests for input_module."""

    def test_handle_unknown_command_returns_false(self):
        """Test handle_command returns False for unknown commands."""
        from modules import input_module

        result = input_module.handle_command("unknown-command", {})
        assert result is False

    @patch('modules.input_module.input_handler.inject_text_smart')
    def test_handle_type_command(self, mock_inject):
        """Test handle_command processes type command."""
        from modules import input_module

        result = input_module.handle_command("type", {'text': 'hello'})
        assert result is True
        mock_inject.assert_called_once()

    @patch('modules.input_module.hotkey_handler.start_listening_with_config')
    def test_handle_listen_command(self, mock_listen):
        """Test handle_command processes listen command."""
        from modules import input_module

        mock_listen.return_value = {'activation_key': 'ctrl+space'}

        result = input_module.handle_command("listen", {'config': {}})
        assert result is True
        mock_listen.assert_called_once()


class TestUIModuleIntegration:
    """Integration tests for ui_module."""

    def test_handle_unknown_command_returns_false(self):
        """Test handle_command returns False for unknown commands."""
        # Mock PyQt5 first
        sys.modules['PyQt5'] = MagicMock()
        sys.modules['PyQt5.QtWidgets'] = MagicMock()
        sys.modules['PyQt5.QtGui'] = MagicMock()
        sys.modules['PyQt5.QtCore'] = MagicMock()

        from modules import ui_module

        result = ui_module.handle_command("unknown-command", {})
        assert result is False

    @patch('modules.ui_module.ui_handler.show_notification')
    def test_handle_notify_command(self, mock_notify):
        """Test handle_command processes notify command."""
        # Mock PyQt5 first
        sys.modules['PyQt5'] = MagicMock()
        sys.modules['PyQt5.QtWidgets'] = MagicMock()
        sys.modules['PyQt5.QtGui'] = MagicMock()
        sys.modules['PyQt5.QtCore'] = MagicMock()

        from modules import ui_module

        mock_notify.return_value = True

        result = ui_module.handle_command("notify", {
            'title': 'Test',
            'message': 'Test message'
        })
        assert result is True
        mock_notify.assert_called_once()


class TestArchitectureCompliance:
    """Test 3-layer architecture compliance."""

    def test_handlers_are_pure_functions(self):
        """Test handlers contain functions, not classes."""
        from handlers import (
            audio_handler,
            transcription_handler,
            hotkey_handler,
            input_handler,
            cursor_lock_handler,
            config_handler
        )

        # Check key functions exist and are callable
        handlers_to_check = [
            (audio_handler, 'record_audio'),
            (transcription_handler, 'transcribe_audio'),
            (hotkey_handler, 'start_listener'),
            (input_handler, 'type_text'),
            (cursor_lock_handler, 'lock_cursor'),
            (config_handler, 'load_config')
        ]

        for handler, func_name in handlers_to_check:
            assert hasattr(handler, func_name), f"{handler.__name__} missing {func_name}"
            assert callable(getattr(handler, func_name)), f"{func_name} is not callable"

    def test_modules_orchestrate_handlers(self):
        """Test modules import and use handlers."""
        from modules import audio_module, config_module, input_module

        # Check modules have handle_command orchestration function
        assert hasattr(audio_module, 'handle_command')
        assert hasattr(config_module, 'handle_command')
        assert hasattr(input_module, 'handle_command')


@pytest.mark.integration
class TestEndToEndFlow:
    """End-to-end integration tests (marked as integration)."""

    @patch('modules.audio_module.audio_handler.record_audio')
    @patch('modules.audio_module.transcription_handler.create_whisper_model')
    @patch('modules.audio_module.transcription_handler.transcribe_audio')
    def test_record_and_transcribe_flow(self, mock_transcribe, mock_create_model, mock_record):
        """Test complete record and transcribe flow."""
        import numpy as np
        from modules import audio_module

        # Mock recording
        mock_record.return_value = np.array([100, 200, 300], dtype=np.int16)

        # Mock model creation
        mock_model = Mock()
        mock_create_model.return_value = mock_model

        # Mock transcription
        mock_transcribe.return_value = "Hello world"

        # Execute
        result = audio_module.handle_command("transcribe", {
            'sample_rate': 16000,
            'model_name': 'base.en'
        })

        # Verify
        assert result is True
        mock_record.assert_called_once()
        mock_transcribe.assert_called_once()

    @patch('modules.config_module.config_handler.load_config')
    @patch('modules.config_module.config_handler.get_default_config')
    def test_load_and_validate_config_flow(self, mock_default, mock_load):
        """Test complete config reload flow."""
        from modules import config_module

        # Mock load
        mock_load.return_value = {'model': {'name': 'base.en'}}
        mock_default.return_value = {'model': {'name': 'base.en'}}

        # Execute reload command
        result = config_module.handle_command("config", ["reload"])

        # Verify
        assert result is True
        # Load should be called at least once (initial + reload)
        assert mock_load.call_count >= 1
