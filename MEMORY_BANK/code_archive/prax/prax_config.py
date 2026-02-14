#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: prax_config.py - Prax Configuration Management
# Date: 2025-10-25
# Version: 1.0.0
# Category: prax
#
# CHANGELOG:
#   - v1.0.0 (2025-10-25): Extracted from prax_logger.py - configuration constants and config loading
# =============================================

"""
Prax Configuration Module

Centralized configuration management for prax system.
Provides path constants, ignore patterns, and configuration loading.
"""

# =============================================
# IMPORTS
# =============================================

# INFRASTRUCTURE IMPORT PATTERN - Universal AIPass pattern
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.append(str(AIPASS_ROOT))

# Standard imports
import json
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, Set

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "prax_config"
MODULE_VERSION = "1.0.0"

# =============================================
# PATHS
# =============================================

PRAX_ROOT = AIPASS_ROOT / "prax"
ECOSYSTEM_ROOT = AIPASS_ROOT
SYSTEM_LOGS_DIR = ECOSYSTEM_ROOT / "system_logs"
PRAX_JSON_DIR = PRAX_ROOT / "prax_json"

# Auto-create directories
SYSTEM_LOGS_DIR.mkdir(exist_ok=True)
PRAX_JSON_DIR.mkdir(exist_ok=True)

# 3-File JSON Pattern for this module
CONFIG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_log.json"

# Prax logger's config file (for loading ignore patterns)
PRAX_LOGGER_CONFIG_FILE = PRAX_JSON_DIR / "prax_logger_config.json"

# =============================================
# DEFAULT CONFIGURATION
# =============================================

# Ignore folders for module discovery (hardcoded fallback)
DEFAULT_IGNORE_FOLDERS = {
    '.git', '__pycache__', '.venv', 'vendor', 'node_modules',
    'Archive', 'Backups', 'External_Code_Sources', 'WorkShop',
    '.claude-server-commander-logs',
    'backup_system', 'backups', 'archive.local'
}

# Logging configuration - DEFAULT VALUES (fallback if config missing/invalid)
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# System logs defaults (comprehensive analysis)
DEFAULT_SYSTEM_LOGS = {
    "max_lines": 1000,
    "backup_count": 1,
    "log_level": "INFO"
}

# Local logs defaults (quick reference)
DEFAULT_LOCAL_LOGS = {
    "max_lines": 250,
    "backup_count": 1,
    "log_level": "INFO"
}

# Legacy constants (kept for backward compatibility - prefer using load_log_config())
# These are loaded from config at module import time
_log_config = None

def _initialize_legacy_constants():
    """Initialize legacy constants from config (called at module import)"""
    global _log_config, MAX_LOG_SIZE, BACKUP_COUNT
    _log_config = load_log_config()
    # Update legacy constants with config values
    MAX_LOG_SIZE = lines_to_bytes(_log_config['system_logs']['max_lines'])
    BACKUP_COUNT = _log_config['system_logs']['backup_count']
    return MAX_LOG_SIZE, BACKUP_COUNT

# Will be set after load_log_config() is defined
MAX_LOG_SIZE = 500 * 1024  # Temporary default, will be updated
BACKUP_COUNT = 1  # Temporary default, will be updated

# =============================================
# CONFIG HELPER FUNCTIONS
# =============================================

def get_debug_prints_enabled() -> bool:
    """Check if debug prints are enabled in prax_logger config"""
    try:
        if PRAX_LOGGER_CONFIG_FILE.exists():
            with open(PRAX_LOGGER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('config', {}).get('debug_prints', False)
    except Exception:
        pass
    return False  # Default to False if config missing/invalid

def load_ignore_patterns_from_config() -> Set[str]:
    """Load ignore patterns from prax_logger config file, fallback to hardcoded DEFAULT_IGNORE_FOLDERS"""
    try:
        if PRAX_LOGGER_CONFIG_FILE.exists():
            with open(PRAX_LOGGER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                patterns = config.get('config', {}).get('ignore_patterns', [])
                if patterns:
                    return set(patterns)
    except Exception as e:
        # Log error if we can, but don't fail
        print(f"[{MODULE_NAME}] Warning: Could not load ignore_patterns from config: {e}")

    # Fallback to hardcoded if config missing/invalid
    return DEFAULT_IGNORE_FOLDERS

def load_log_config() -> Dict[str, Any]:
    """Load logging config from JSON, fallback to defaults

    Returns dict with system_logs and local_logs settings.
    If config file missing or invalid, returns code defaults.
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
    except Exception as e:
        print(f"[{MODULE_NAME}] Warning: Could not load log config: {e}")
        print(f"[{MODULE_NAME}] Using code defaults")

    # Fallback to code defaults
    return {
        'system_logs': DEFAULT_SYSTEM_LOGS,
        'local_logs': DEFAULT_LOCAL_LOGS,
        'log_format': LOG_FORMAT,
        'date_format': DATE_FORMAT
    }

def lines_to_bytes(lines: int, avg_bytes_per_line: int = 150) -> int:
    """Convert line count to approximate byte size

    Average log line: ~150 bytes (timestamp + level + module + message)
    Stack traces can be longer but this is a reasonable estimate.
    """
    return lines * avg_bytes_per_line

def ensure_prax_logger_config():
    """Ensure prax_logger_config.json exists with correct schema

    Auto-creates or updates the config file with current schema.
    If file exists but has old schema, overwrites with new schema.
    This is self-healing - module manages its own config structure.
    """
    config_data = {
        "module_name": "prax_logger",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "system_logs": DEFAULT_SYSTEM_LOGS.copy(),
            "local_logs": DEFAULT_LOCAL_LOGS.copy(),
            "log_format": LOG_FORMAT,
            "date_format": DATE_FORMAT,
            "debug_prints": False,
            "ignore_patterns": list(DEFAULT_IGNORE_FOLDERS)
        }
    }

    # Always write - this ensures schema is current
    with open(PRAX_LOGGER_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)

    return config_data

# Initialize legacy constants from config (now that functions are defined)
# Ensure config file exists first
ensure_prax_logger_config()
MAX_LOG_SIZE, BACKUP_COUNT = _initialize_legacy_constants()

# =============================================
# 3-FILE JSON AUTO-GENERATION
# =============================================

def create_default_config() -> Dict[str, Any]:
    """Create default config structure"""
    return {
        "module_name": MODULE_NAME,
        "version": MODULE_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "aipass_root": str(AIPASS_ROOT),
            "prax_root": str(PRAX_ROOT),
            "system_logs_dir": str(SYSTEM_LOGS_DIR),
            "prax_json_dir": str(PRAX_JSON_DIR),
            "log_level": "INFO",
            "max_log_size_kb": MAX_LOG_SIZE // 1024,
            "backup_count": BACKUP_COUNT
        }
    }

def create_default_data() -> Dict[str, Any]:
    """Create default data structure"""
    return {
        "module_name": MODULE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime_stats": {
            "last_loaded": datetime.now(timezone.utc).isoformat(),
            "config_loads": 0,
            "pattern_loads": 0
        }
    }

def create_default_log() -> Dict[str, Any]:
    """Create default log structure"""
    return {
        "module_name": MODULE_NAME,
        "logs": [],
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

def ensure_json_files_exist():
    """Create 3-file JSON pattern if files don't exist"""
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(create_default_config(), f, indent=2)
        print(f"[{MODULE_NAME}] Created: {CONFIG_FILE}")

    if not DATA_FILE.exists():
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(create_default_data(), f, indent=2)
        print(f"[{MODULE_NAME}] Created: {DATA_FILE}")

    if not LOG_FILE.exists():
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(create_default_log(), f, indent=2)
        print(f"[{MODULE_NAME}] Created: {LOG_FILE}")

def log_operation(operation: str, success: bool, details: str = ""):
    """Log operation to module log file"""
    try:
        logs = []
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                logs = log_data.get("logs", [])

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "success": success,
            "details": details
        }
        logs.append(log_entry)

        # Keep last 100 entries
        logs = logs[-100:]

        log_data = {
            "module_name": MODULE_NAME,
            "logs": logs,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)

    except Exception as e:
        print(f"[{MODULE_NAME}] Warning: Could not write to log file: {e}")

# =============================================
# MODULE INITIALIZATION
# =============================================

def handle_test():
    """Run module test - verify configuration loading"""
    print(f"{MODULE_NAME} v{MODULE_VERSION}")
    print("=" * 60)

    # Ensure JSON files exist
    ensure_json_files_exist()

    # Test configuration loading
    print(f"\nAIPASS_ROOT: {AIPASS_ROOT}")
    print(f"PRAX_ROOT: {PRAX_ROOT}")
    print(f"SYSTEM_LOGS_DIR: {SYSTEM_LOGS_DIR}")
    print(f"PRAX_JSON_DIR: {PRAX_JSON_DIR}")

    # Test ignore patterns loading
    patterns = load_ignore_patterns_from_config()
    print(f"\nIgnore patterns loaded: {len(patterns)} patterns")

    # Test debug prints
    debug_enabled = get_debug_prints_enabled()
    print(f"Debug prints enabled: {debug_enabled}")

    # Log this operation
    log_operation("module_test", True, "Configuration module tested successfully")

    print("\n" + "=" * 60)
    print("✓ prax_config.py initialized successfully")
    print(f"✓ 3-file JSON pattern created in {PRAX_JSON_DIR}")

def handle_show_config():
    """Show current configuration values"""
    print(f"{MODULE_NAME} Configuration")
    print("=" * 60)

    # Load config file
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(json.dumps(config, indent=2))
    else:
        print("No configuration file found. Run 'test' command to create.")
        return 1

    return 0

def handle_show_paths():
    """Show all path constants"""
    print(f"{MODULE_NAME} Path Constants")
    print("=" * 60)
    print(f"AIPASS_ROOT:      {AIPASS_ROOT}")
    print(f"PRAX_ROOT:        {PRAX_ROOT}")
    print(f"ECOSYSTEM_ROOT:   {ECOSYSTEM_ROOT}")
    print(f"SYSTEM_LOGS_DIR:  {SYSTEM_LOGS_DIR}")
    print(f"PRAX_JSON_DIR:    {PRAX_JSON_DIR}")
    print(f"\nDefault Settings:")
    print(f"LOG_LEVEL:        {DEFAULT_LOG_LEVEL}")
    print(f"MAX_LOG_SIZE:     {MAX_LOG_SIZE:,} bytes ({MAX_LOG_SIZE // 1024 // 1024} MB)")
    print(f"BACKUP_COUNT:     {BACKUP_COUNT}")
    return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Prax Configuration Module - Manages paths and configuration loading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: test, show-config, show-paths

  test        - Run module test and verify configuration loading
  show-config - Display current configuration from JSON file
  show-paths  - Display all path constants and default settings

EXAMPLES:
  python3 prax_config.py test
  python3 prax_config.py show-config
  python3 prax_config.py show-paths
        """
    )

    parser.add_argument('command',
                       choices=['test', 'show-config', 'show-paths'],
                       help='Command to execute')

    args = parser.parse_args()

    # Route to command handlers
    if args.command == 'test':
        return handle_test()
    elif args.command == 'show-config':
        return handle_show_config()
    elif args.command == 'show-paths':
        return handle_show_paths()

if __name__ == "__main__":
    import sys
    sys.exit(main() or 0)
