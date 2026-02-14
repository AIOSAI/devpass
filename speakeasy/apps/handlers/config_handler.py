#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: config_handler.py - Configuration management handler
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
# =============================================

"""
Configuration Handler - Pure functions for config management

Provides:
- Config loading/saving (YAML)
- Default config generation
- Config merging and validation
- No dependencies on Prax or AIPass infrastructure
"""

import yaml
from pathlib import Path
from typing import Dict, Tuple, List, Optional, Any


# =============================================================================
# DEFAULT CONFIG STRUCTURE
# =============================================================================

def get_default_config() -> Dict[str, Any]:
    """
    Returns default configuration dictionary with all settings

    Returns:
        Dict containing complete default configuration
    """
    return {
        'model': {
            'name': 'base.en',
            'device': 'auto',
            'compute_type': 'default',
            'language': 'en',
            'temperature': 0.0,
            'vad_filter': True,
        },
        'recording': {
            'activation_key': 'ctrl+space',
            'recording_mode': 'press_to_toggle',
            'sample_rate': 16000,
            'silence_duration': 900,
            'min_duration': 100,
            'vad_aggressiveness': 2,
        },
        'input': {
            'method': 'pynput',
            'key_delay': 0.005,
            'paste_threshold': 50,
        },
        'post_processing': {
            'remove_trailing_period': False,
            'add_trailing_space': True,
            'remove_capitalization': False,
        },
        'cursor_lock': {
            'enabled': True,
        },
        'ui': {
            'show_status_window': True,
            'show_notifications': True,
            'sound_on_start': True,
            'sound_on_complete': True,
        }
    }


# =============================================================================
# CONFIG FILE OPERATIONS
# =============================================================================

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to config file (default: /home/aipass/speakeasy/config.yaml)

    Returns:
        Configuration dictionary (merges user config over defaults)

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file has invalid YAML
    """
    if config_path is None:
        config_path = Path.home() / "speakeasy" / "config.yaml"

    config_path = Path(config_path)

    # Start with defaults
    defaults = get_default_config()

    # If no user config exists, return defaults
    if not config_path.exists():
        return defaults

    # Load and merge user config
    with open(config_path, 'r', encoding='utf-8') as f:
        user_config = yaml.safe_load(f) or {}

    return merge_configs(defaults, user_config)


def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """
    Save configuration to YAML file

    Args:
        config: Configuration dictionary to save
        config_path: Path to config file (default: /home/aipass/speakeasy/config.yaml)

    Raises:
        OSError: If unable to write to file
    """
    if config_path is None:
        config_path = Path.home() / "speakeasy" / "config.yaml"

    config_path = Path(config_path)

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Save with pretty formatting
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


# =============================================================================
# CONFIG MERGING
# =============================================================================

def merge_configs(defaults: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge user config over defaults

    Args:
        defaults: Default configuration dictionary
        user_config: User configuration dictionary

    Returns:
        Merged configuration (user values override defaults)
    """
    result = defaults.copy()

    for key, value in user_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursive merge for nested dicts
            result[key] = merge_configs(result[key], value)
        else:
            # Direct override
            result[key] = value

    return result


# =============================================================================
# CONFIG VALIDATION
# =============================================================================

def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate configuration values

    Args:
        config: Configuration dictionary to validate

    Returns:
        Tuple of (valid: bool, errors: list of error messages)
    """
    errors = []

    # Validate model section
    if 'model' in config:
        model = config['model']

        # Model name must be valid
        valid_models = ['tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en',
                       'medium', 'medium.en', 'large', 'large-v1', 'large-v2', 'large-v3']
        if 'name' in model and model['name'] not in valid_models:
            errors.append(f"Invalid model name: {model['name']} (must be one of {valid_models})")

        # Device must be valid
        valid_devices = ['auto', 'cuda', 'cpu']
        if 'device' in model and model['device'] not in valid_devices:
            errors.append(f"Invalid device: {model['device']} (must be one of {valid_devices})")

        # Compute type must be valid
        valid_compute = ['default', 'float32', 'float16', 'int8']
        if 'compute_type' in model and model['compute_type'] not in valid_compute:
            errors.append(f"Invalid compute_type: {model['compute_type']} (must be one of {valid_compute})")

        # Temperature must be 0.0-1.0
        if 'temperature' in model:
            temp = model['temperature']
            if not isinstance(temp, (int, float)) or temp < 0.0 or temp > 1.0:
                errors.append(f"Invalid temperature: {temp} (must be 0.0-1.0)")

    # Validate recording section
    if 'recording' in config:
        recording = config['recording']

        # Recording mode must be valid
        valid_modes = ['continuous', 'voice_activity_detection', 'press_to_toggle', 'hold_to_record']
        if 'recording_mode' in recording and recording['recording_mode'] not in valid_modes:
            errors.append(f"Invalid recording_mode: {recording['recording_mode']} (must be one of {valid_modes})")

        # Sample rate must be positive integer
        if 'sample_rate' in recording:
            rate = recording['sample_rate']
            if not isinstance(rate, int) or rate <= 0:
                errors.append(f"Invalid sample_rate: {rate} (must be positive integer)")

        # Durations must be positive integers
        for key in ['silence_duration', 'min_duration']:
            if key in recording:
                value = recording[key]
                if not isinstance(value, int) or value < 0:
                    errors.append(f"Invalid {key}: {value} (must be non-negative integer)")

        # VAD aggressiveness must be 0-3
        if 'vad_aggressiveness' in recording:
            vad = recording['vad_aggressiveness']
            if not isinstance(vad, int) or vad < 0 or vad > 3:
                errors.append(f"Invalid vad_aggressiveness: {vad} (must be 0-3)")

    # Validate input section
    if 'input' in config:
        input_cfg = config['input']

        # Input method must be valid
        valid_methods = ['pynput', 'ydotool', 'dotool']
        if 'method' in input_cfg and input_cfg['method'] not in valid_methods:
            errors.append(f"Invalid input method: {input_cfg['method']} (must be one of {valid_methods})")

        # Key delay must be non-negative float
        if 'key_delay' in input_cfg:
            delay = input_cfg['key_delay']
            if not isinstance(delay, (int, float)) or delay < 0:
                errors.append(f"Invalid key_delay: {delay} (must be non-negative number)")

        # Paste threshold must be positive integer
        if 'paste_threshold' in input_cfg:
            threshold = input_cfg['paste_threshold']
            if not isinstance(threshold, int) or threshold <= 0:
                errors.append(f"Invalid paste_threshold: {threshold} (must be positive integer)")

    return (len(errors) == 0, errors)


# =============================================================================
# CONFIG VALUE ACCESS
# =============================================================================

def get_value(config: Dict[str, Any], section: str, key: str) -> Any:
    """
    Get specific configuration value

    Args:
        config: Configuration dictionary
        section: Config section (e.g., 'model', 'recording')
        key: Config key within section

    Returns:
        Configuration value or None if not found
    """
    if section not in config:
        return None

    if key not in config[section]:
        return None

    return config[section][key]


def set_value(config: Dict[str, Any], section: str, key: str, value: Any) -> Tuple[bool, List[str]]:
    """
    Set configuration value (modifies config in place)

    Args:
        config: Configuration dictionary to modify
        section: Config section
        key: Config key within section
        value: New value to set

    Returns:
        Tuple of (success: bool, errors: list of error messages)
    """
    if section not in config:
        return (False, [f"Section not found: {section}"])

    # Set the value
    config[section][key] = value

    # Validate config
    valid, errors = validate_config(config)
    if not valid:
        return (False, errors)

    return (True, [])


def parse_value(value_str: str) -> Any:
    """
    Parse string value into appropriate type (bool, int, float, or str)

    Args:
        value_str: String to parse

    Returns:
        Parsed value in appropriate type
    """
    # Handle booleans
    if value_str.lower() in ('true', 'yes', 'on'):
        return True
    elif value_str.lower() in ('false', 'no', 'off'):
        return False
    # Handle integers
    elif value_str.isdigit():
        return int(value_str)
    # Handle floats
    elif value_str.replace('.', '', 1).isdigit():
        return float(value_str)
    # Return as string
    else:
        return value_str
