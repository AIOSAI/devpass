#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: load.py
# Date: 2025-11-07
# Version: 1.0.1
# Category: prax/handlers/config
# CODE STANDARDS: Seed v1.1
#
# CHANGELOG:
#   - v1.0.1 (2026-02-02): Added self-healing SYSTEM_LOGS_DIR auto-creation
#   - v1.0.0 (2025-11-07): Extracted from prax_config.py - logging configuration loading
# =============================================

"""
Load Logging Configuration Handler

Loads logging configuration from prax_logger_config.json.
Returns configuration for system logs and local logs with fallback to defaults.

Features:
- Loads log config from prax_logger_config.json
- Returns system_logs and local_logs settings
- Fallback to code defaults if config missing
- Includes log_format and date_format
- Self-healing: auto-creates SYSTEM_LOGS_DIR if missing

Usage:
    from prax.apps.handlers.config.load import load_log_config

    config = load_log_config()
    system_logs = config['system_logs']
    max_lines = system_logs['max_lines']
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
PRAX_ROOT = AIPASS_ROOT / "prax"
sys.path.insert(0, str(AIPASS_ROOT))

# =============================================
# CONFIGURATION
# =============================================

MODULE_NAME = "load"

# Directory paths (exported for other handlers)
ECOSYSTEM_ROOT = AIPASS_ROOT
SYSTEM_LOGS_DIR = AIPASS_ROOT.parent / "system_logs"
PRAX_JSON_DIR = PRAX_ROOT / "prax_json"

# Self-healing: ensure SYSTEM_LOGS_DIR exists
SYSTEM_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Config file
PRAX_LOGGER_CONFIG_FILE = PRAX_JSON_DIR / "prax_logger_config.json"

# Default configuration constants
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_SYSTEM_LOGS = {
    "max_lines": 1000,
    "backup_count": 1,
    "log_level": "INFO"
}

DEFAULT_LOCAL_LOGS = {
    "max_lines": 250,
    "backup_count": 1,
    "log_level": "INFO"
}

# =============================================
# HANDLER FUNCTIONS
# =============================================

def lines_to_bytes(num_lines: int, avg_line_length: int = 200) -> int:
    """Convert number of lines to approximate bytes for log rotation

    Args:
        num_lines: Number of lines to convert
        avg_line_length: Average line length in characters (default 200)

    Returns:
        Approximate number of bytes
    """
    return num_lines * avg_line_length

def get_debug_prints_enabled() -> bool:
    """Check if debug prints are enabled in config

    Returns:
        True if debug prints enabled, False otherwise
    """
    try:
        if PRAX_LOGGER_CONFIG_FILE.exists():
            with open(PRAX_LOGGER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('config', {}).get('debug_prints_enabled', False)
    except (json.JSONDecodeError, OSError) as e:
        logging.debug(f"Config load error (using defaults): {e}")
    return False

def load_log_config() -> Dict[str, Any]:
    """Load logging config from JSON, fallback to defaults

    Returns:
        Dict with system_logs and local_logs settings:
        {
            "system_logs": {
                "max_lines": 1000,
                "backup_count": 1,
                "log_level": "INFO"
            },
            "local_logs": {
                "max_lines": 250,
                "backup_count": 1,
                "log_level": "INFO"
            },
            "log_format": "%(asctime)s - ...",
            "date_format": "%Y-%m-%d %H:%M:%S"
        }

    If config file missing or invalid, returns code defaults.

    Example:
        >>> config = load_log_config()
        >>> max_lines = config['system_logs']['max_lines']
        >>> print(f"System logs max lines: {max_lines}")
    """
    try:
        if PRAX_LOGGER_CONFIG_FILE.exists():
            with open(PRAX_LOGGER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)

                # Extract system and local log settings
                system_logs = config.get('config', {}).get('system_logs', DEFAULT_SYSTEM_LOGS)
                local_logs = config.get('config', {}).get('local_logs', DEFAULT_LOCAL_LOGS)

                return {
                    'system_logs': system_logs,
                    'local_logs': local_logs,
                    'log_format': config.get('config', {}).get('log_format', LOG_FORMAT),
                    'date_format': config.get('config', {}).get('date_format', DATE_FORMAT)
                }
    except (json.JSONDecodeError, OSError) as e:
        logging.debug(f"Log config load error (using defaults): {e}")

    # Fallback to code defaults
    return {
        'system_logs': DEFAULT_SYSTEM_LOGS,
        'local_logs': DEFAULT_LOCAL_LOGS,
        'log_format': LOG_FORMAT,
        'date_format': DATE_FORMAT
    }
