#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_config_handler.py - Test config handler functions
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy/tests
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Test file for speakeasy config handler
#   - Tests YAML config loading, saving, merging, validation
# =============================================

"""Tests for config_handler.py - configuration management functions."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest
import yaml
import tempfile

# Add apps directory to path so 'handlers' package resolves
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

from handlers.config_handler import (
    get_default_config,
    load_config,
    save_config,
    merge_configs,
    validate_config
)


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_returns_dict(self):
        """Test returns a dictionary."""
        config = get_default_config()
        assert isinstance(config, dict)

    def test_has_required_sections(self):
        """Test config has all required sections."""
        config = get_default_config()
        required_sections = ['model', 'recording', 'input', 'post_processing', 'cursor_lock', 'ui']
        for section in required_sections:
            assert section in config

    def test_model_section_complete(self):
        """Test model section has expected keys."""
        config = get_default_config()
        model = config['model']
        assert 'name' in model
        assert 'device' in model
        assert 'compute_type' in model
        assert 'language' in model

    def test_recording_section_complete(self):
        """Test recording section has expected keys."""
        config = get_default_config()
        recording = config['recording']
        assert 'activation_key' in recording
        assert 'recording_mode' in recording
        assert 'sample_rate' in recording
        assert 'silence_duration' in recording

    def test_returns_new_dict_each_time(self):
        """Test returns a new dictionary instance each time."""
        config1 = get_default_config()
        config2 = get_default_config()
        assert config1 is not config2


class TestLoadConfig:
    """Tests for load_config function."""

    def test_returns_defaults_when_no_file(self):
        """Test returns default config when file doesn't exist."""
        with patch('handlers.config_handler.Path.exists', return_value=False):
            config = load_config(Path("/nonexistent/config.yaml"))
            assert config == get_default_config()

    def test_loads_yaml_file(self):
        """Test loads YAML file and merges with defaults."""
        user_config = """
model:
  name: small.en
recording:
  sample_rate: 48000
"""
        with patch('builtins.open', mock_open(read_data=user_config)):
            with patch('handlers.config_handler.Path.exists', return_value=True):
                config = load_config(Path("/test/config.yaml"))

                # User values should override defaults
                assert config['model']['name'] == 'small.en'
                assert config['recording']['sample_rate'] == 48000

                # Other defaults should remain
                assert 'device' in config['model']
                assert 'silence_duration' in config['recording']

    def test_handles_empty_yaml_file(self):
        """Test handles empty or null YAML file."""
        with patch('builtins.open', mock_open(read_data="")):
            with patch('handlers.config_handler.Path.exists', return_value=True):
                config = load_config(Path("/test/config.yaml"))
                assert config == get_default_config()

    def test_uses_default_path(self):
        """Test uses default path when none provided."""
        with patch('handlers.config_handler.Path.exists', return_value=False):
            config = load_config()
            assert config == get_default_config()

    def test_raises_on_invalid_yaml(self):
        """Test raises yaml.YAMLError on invalid YAML."""
        invalid_yaml = "invalid: yaml: content: [unclosed"
        with patch('builtins.open', mock_open(read_data=invalid_yaml)):
            with patch('handlers.config_handler.Path.exists', return_value=True):
                with pytest.raises(yaml.YAMLError):
                    load_config(Path("/test/config.yaml"))


class TestSaveConfig:
    """Tests for save_config function."""

    def test_saves_config_to_file(self, temp_test_dir):
        """Test saves configuration to YAML file."""
        config_path = temp_test_dir / "config.yaml"

        config = {
            'model': {'name': 'base.en'},
            'recording': {'sample_rate': 16000}
        }

        save_config(config, config_path)

        assert config_path.exists()

        # Load and verify
        with open(config_path, 'r', encoding='utf-8') as f:
            saved_config = yaml.safe_load(f)

        assert saved_config['model']['name'] == 'base.en'
        assert saved_config['recording']['sample_rate'] == 16000

    def test_creates_parent_directory(self, temp_test_dir):
        """Test creates parent directories if they don't exist."""
        config_path = temp_test_dir / "subdir" / "config.yaml"

        config = {'test': 'data'}
        save_config(config, config_path)

        assert config_path.exists()
        assert config_path.parent.exists()

    def test_overwrites_existing_file(self, temp_test_dir):
        """Test overwrites existing config file."""
        config_path = temp_test_dir / "config.yaml"

        # Create initial file
        config1 = {'value': 1}
        save_config(config1, config_path)

        # Overwrite
        config2 = {'value': 2}
        save_config(config2, config_path)

        # Verify
        with open(config_path, 'r', encoding='utf-8') as f:
            saved_config = yaml.safe_load(f)

        assert saved_config['value'] == 2


class TestMergeConfigs:
    """Tests for merge_configs function."""

    def test_merges_nested_dicts(self):
        """Test merges nested dictionaries."""
        defaults = {
            'section1': {'key1': 'default1', 'key2': 'default2'},
            'section2': {'key3': 'default3'}
        }

        user = {
            'section1': {'key1': 'user1'}
        }

        result = merge_configs(defaults, user)

        assert result['section1']['key1'] == 'user1'
        assert result['section1']['key2'] == 'default2'
        assert result['section2']['key3'] == 'default3'

    def test_adds_new_keys(self):
        """Test adds new keys from user config."""
        defaults = {'section1': {'key1': 'value1'}}
        user = {'section2': {'key2': 'value2'}}

        result = merge_configs(defaults, user)

        assert 'section1' in result
        assert 'section2' in result

    def test_deep_merge(self):
        """Test performs deep merge on nested structures."""
        defaults = {
            'level1': {
                'level2': {
                    'key1': 'default',
                    'key2': 'default'
                }
            }
        }

        user = {
            'level1': {
                'level2': {
                    'key1': 'user'
                }
            }
        }

        result = merge_configs(defaults, user)

        assert result['level1']['level2']['key1'] == 'user'
        assert result['level1']['level2']['key2'] == 'default'

    def test_does_not_modify_originals(self):
        """Test does not modify original dicts."""
        defaults = {'key': 'default'}
        user = {'key': 'user'}

        result = merge_configs(defaults, user)

        assert defaults['key'] == 'default'
        assert user['key'] == 'user'
        assert result['key'] == 'user'

    def test_overrides_non_dict_values(self):
        """Test overrides non-dict values completely."""
        defaults = {'key': 'string'}
        user = {'key': {'nested': 'dict'}}

        result = merge_configs(defaults, user)

        assert result['key'] == {'nested': 'dict'}


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_valid_config_passes(self):
        """Test valid configuration passes validation."""
        config = get_default_config()
        valid, errors = validate_config(config)

        assert valid is True
        assert len(errors) == 0

    def test_invalid_model_name(self):
        """Test detects invalid model name."""
        config = get_default_config()
        config['model']['name'] = 'invalid-model'

        valid, errors = validate_config(config)

        assert valid is False
        assert any('Invalid model name' in err for err in errors)

    def test_invalid_device(self):
        """Test detects invalid device."""
        config = get_default_config()
        config['model']['device'] = 'invalid-device'

        valid, errors = validate_config(config)

        assert valid is False
        assert any('Invalid device' in err for err in errors)

    def test_invalid_temperature(self):
        """Test detects invalid temperature."""
        config = get_default_config()
        config['model']['temperature'] = 2.0  # Should be 0.0-1.0

        valid, errors = validate_config(config)

        assert valid is False
        assert any('Invalid temperature' in err for err in errors)

    def test_invalid_recording_mode(self):
        """Test detects invalid recording mode."""
        config = get_default_config()
        config['recording']['recording_mode'] = 'invalid_mode'

        valid, errors = validate_config(config)

        assert valid is False
        assert any('Invalid recording_mode' in err for err in errors)

    def test_invalid_sample_rate(self):
        """Test detects invalid sample rate."""
        config = get_default_config()
        config['recording']['sample_rate'] = -1000

        valid, errors = validate_config(config)

        assert valid is False
        assert any('Invalid sample_rate' in err for err in errors)

    def test_invalid_vad_aggressiveness(self):
        """Test detects invalid VAD aggressiveness."""
        config = get_default_config()
        config['recording']['vad_aggressiveness'] = 10  # Should be 0-3

        valid, errors = validate_config(config)

        assert valid is False
        assert any('Invalid vad_aggressiveness' in err for err in errors)

    def test_invalid_input_method(self):
        """Test detects invalid input method."""
        config = get_default_config()
        config['input']['method'] = 'invalid'

        valid, errors = validate_config(config)

        assert valid is False
        assert any('Invalid input method' in err for err in errors)

    def test_invalid_key_delay(self):
        """Test detects invalid key delay."""
        config = get_default_config()
        config['input']['key_delay'] = -0.5

        valid, errors = validate_config(config)

        assert valid is False
        assert any('Invalid key_delay' in err for err in errors)

    def test_invalid_paste_threshold(self):
        """Test detects invalid paste threshold."""
        config = get_default_config()
        config['input']['paste_threshold'] = 0

        valid, errors = validate_config(config)

        assert valid is False
        assert any('Invalid paste_threshold' in err for err in errors)

    def test_multiple_errors(self):
        """Test reports multiple validation errors."""
        config = get_default_config()
        config['model']['name'] = 'invalid'
        config['model']['device'] = 'invalid'
        config['recording']['sample_rate'] = -1

        valid, errors = validate_config(config)

        assert valid is False
        assert len(errors) >= 3

    def test_valid_all_recording_modes(self):
        """Test all valid recording modes pass validation."""
        valid_modes = ['continuous', 'voice_activity_detection', 'press_to_toggle', 'hold_to_record']

        for mode in valid_modes:
            config = get_default_config()
            config['recording']['recording_mode'] = mode

            valid, errors = validate_config(config)
            assert valid is True, f"Mode {mode} should be valid"

    def test_valid_all_input_methods(self):
        """Test all valid input methods pass validation."""
        valid_methods = ['pynput', 'ydotool', 'dotool']

        for method in valid_methods:
            config = get_default_config()
            config['input']['method'] = method

            valid, errors = validate_config(config)
            assert valid is True, f"Method {method} should be valid"

    def test_empty_config(self):
        """Test empty config passes validation."""
        config = {}
        valid, errors = validate_config(config)

        # Empty config should be valid (no errors)
        assert valid is True
        assert len(errors) == 0
