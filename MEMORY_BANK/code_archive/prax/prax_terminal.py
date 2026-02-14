#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: prax_terminal.py - Terminal Output Management
# Date: 2025-10-25
# Version: 1.0.0
# Category: prax
#
# CHANGELOG:
#   - v1.0.0 (2025-10-25): Created - terminal output formatting and management
# =============================================

"""
Prax Terminal Output Module

Provides live terminal output for logging with branch-aware formatting.
Filters noise and displays logs in real-time for debugging.
"""

# =============================================
# IMPORTS
# =============================================

# INFRASTRUCTURE IMPORT PATTERN - Universal AIPass pattern
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.append(str(AIPASS_ROOT))

# Import from prax_config
from prax.apps.prax_config import (
    PRAX_JSON_DIR,
    DEFAULT_LOG_LEVEL
)

# Standard imports
import json
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "prax_terminal"
MODULE_VERSION = "1.0.0"

# 3-File JSON Pattern for this module
CONFIG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_log.json"

# Default modules to filter (prax internal modules)
DEFAULT_FILTERED_MODULES = {
    'prax_logger', 'prax_handlers', 'prax_config',
    'prax_registry', 'prax_discovery', 'prax_terminal'
}

# Terminal output state
_terminal_enabled = False
_terminal_handler: Optional[logging.StreamHandler] = None

# =============================================
# TERMINAL OUTPUT FORMATTING
# =============================================

def detect_branch_from_logger_name(logger_name: str) -> Optional[str]:
    """
    Detect branch from logger name

    Logger names follow pattern: captured_{module_name}
    We need to check if the module has a branch in its path
    """
    # This will be enhanced when we have access to module registry
    # For now, return None (will show as SYSTEM)
    return None

def format_terminal_message(record: logging.LogRecord, branch: Optional[str] = None) -> str:
    """
    Format log record for terminal output

    Format: [BRANCH] module - LEVEL: message
    Example: [prax] test_module - INFO: Test message
    """
    # Extract module name from logger name
    # Logger names are like "captured_{module_name}"
    logger_name = record.name
    if logger_name.startswith("captured_"):
        module_name = logger_name[9:]  # Remove "captured_" prefix
    else:
        module_name = logger_name

    # Determine branch label
    branch_label = branch if branch else "SYSTEM"

    # Format level name (fixed width for alignment)
    level = record.levelname

    # Format message
    return f"[{branch_label}] {module_name} - {level}: {record.getMessage()}"

def should_display_terminal(module_name: str, filtered_modules: Optional[Set[str]] = None) -> bool:
    """
    Determine if module should be displayed in terminal output

    Filters out prax internal modules by default
    """
    if filtered_modules is None:
        filtered_modules = load_filtered_modules()

    return module_name not in filtered_modules

def load_filtered_modules() -> Set[str]:
    """Load filtered modules from config"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return set(config.get('filtered_modules', DEFAULT_FILTERED_MODULES))
        except:
            pass

    return DEFAULT_FILTERED_MODULES

# =============================================
# TERMINAL HANDLER MANAGEMENT
# =============================================

class TerminalFormatter(logging.Formatter):
    """Custom formatter for terminal output with branch information"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """Format the record for terminal output"""
        # Extract module name
        logger_name = record.name
        if logger_name.startswith("captured_"):
            module_name = logger_name[9:]
        else:
            module_name = logger_name

        # Check if should display
        if not should_display_terminal(module_name):
            return ""  # Skip this message

        # Format and return
        return format_terminal_message(record)

def create_terminal_handler() -> logging.StreamHandler:
    """Create StreamHandler for terminal output"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(DEFAULT_LOG_LEVEL)

    # Use custom formatter
    formatter = TerminalFormatter()
    handler.setFormatter(formatter)

    return handler

def is_terminal_enabled() -> bool:
    """Check if terminal output is currently enabled"""
    return _terminal_enabled

def get_terminal_handler() -> Optional[logging.StreamHandler]:
    """Get current terminal handler"""
    return _terminal_handler

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
            "terminal_enabled": False,
            "filtered_modules": list(DEFAULT_FILTERED_MODULES),
            "show_timestamps": False,
            "color_output": False
        }
    }

def create_default_data() -> Dict[str, Any]:
    """Create default data structure"""
    return {
        "module_name": MODULE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime_stats": {
            "terminal_enabled": False,
            "messages_displayed": 0,
            "messages_filtered": 0
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
# CLI COMMANDS
# =============================================

def handle_test():
    """Run module test - verify terminal formatting"""
    print(f"{MODULE_NAME} v{MODULE_VERSION}")
    print("=" * 60)

    # Ensure JSON files exist
    ensure_json_files_exist()

    # Test formatting
    print(f"\nTesting terminal output formatting...")

    # Create a mock log record
    import logging
    record = logging.LogRecord(
        name="captured_test_module",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )

    formatted = format_terminal_message(record, branch="prax")
    print(f"Formatted output: {formatted}")

    # Test filtering
    print(f"\nTesting filter logic...")
    print(f"  test_module should display: {should_display_terminal('test_module')}")
    print(f"  prax_logger should filter: {not should_display_terminal('prax_logger')}")
    print(f"  flow_plan should display: {should_display_terminal('flow_plan')}")

    # Test handler creation
    print(f"\nTesting handler creation...")
    handler = create_terminal_handler()
    print(f"✓ StreamHandler created: {type(handler).__name__}")
    print(f"✓ Level: {handler.level}")

    # Log operation
    log_operation("module_test", True, "Terminal module tested successfully")

    print("\n" + "=" * 60)
    print("✓ prax_terminal.py initialized successfully")
    print(f"✓ 3-file JSON pattern created in {PRAX_JSON_DIR}")
    return 0

def handle_show_config():
    """Show current configuration"""
    print(f"{MODULE_NAME} Configuration")
    print("=" * 60)

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(json.dumps(config, indent=2))
    else:
        print("No configuration file found. Run 'test' command to create.")
        return 1

    return 0

def handle_show_filtered():
    """Show filtered modules list"""
    filtered = load_filtered_modules()
    print(f"{MODULE_NAME} - Filtered Modules")
    print("=" * 60)
    print(f"Total filtered: {len(filtered)}\n")

    for i, module in enumerate(sorted(filtered), 1):
        print(f"{i:2}. {module}")

    return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Prax Terminal Module - Live terminal output for logging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: test, show-config, show-filtered

  test          - Run module test and verify terminal formatting
  show-config   - Display current configuration
  show-filtered - Show list of filtered modules

EXAMPLES:
  python3 prax_terminal.py test
  python3 prax_terminal.py show-config
  python3 prax_terminal.py show-filtered
        """
    )

    parser.add_argument('command',
                       choices=['test', 'show-config', 'show-filtered'],
                       help='Command to execute')

    args = parser.parse_args()

    # Route to command handlers
    if args.command == 'test':
        return handle_test()
    elif args.command == 'show-config':
        return handle_show_config()
    elif args.command == 'show-filtered':
        return handle_show_filtered()

if __name__ == "__main__":
    import sys
    sys.exit(main() or 0)
