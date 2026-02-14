#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: prax_handlers.py - Prax Logging Handler Management
# Date: 2025-10-25
# Version: 1.0.0
# Category: prax
#
# CHANGELOG:
#   - v1.0.0 (2025-10-25): Extracted from prax_logger.py - logging handler setup and management
# =============================================

"""
Prax Logging Handler Management

Provides logging handler setup, individual module loggers, and global getLogger override.
Manages the routing of log messages to individual module log files.
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
    SYSTEM_LOGS_DIR,
    PRAX_JSON_DIR,
    DEFAULT_LOG_LEVEL,
    MAX_LOG_SIZE,
    BACKUP_COUNT,
    LOG_FORMAT,
    DATE_FORMAT,
    get_debug_prints_enabled,
    load_log_config,
    lines_to_bytes
)

# Standard imports
import json
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler

# Import terminal output support (imported after to avoid circular dependency)
_terminal_module_available = False
try:
    from prax.apps.prax_terminal import (
        create_terminal_handler,
        format_terminal_message,
        should_display_terminal
    )
    _terminal_module_available = True
except ImportError:
    pass  # Terminal module not available yet

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "prax_handlers"
MODULE_VERSION = "1.0.0"

# 3-File JSON Pattern for this module
CONFIG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_log.json"

# Store original logging functions for restoration
_original_getLogger = logging.getLogger
_original_basicConfig = logging.basicConfig

# =============================================
# LOGGING HANDLER MANAGEMENT
# =============================================

# Global state for logging system
_system_logger: Optional[logging.Logger] = None
_captured_loggers: Dict[str, logging.Logger] = {}  # Store individual module loggers
_terminal_output_enabled = False  # Terminal output toggle

def get_calling_module() -> str:
    """Detect calling module from stack trace"""
    import inspect

    frame = inspect.currentframe()
    try:
        # Walk up the stack to find the calling module
        current_frame = frame
        frame_count = 0
        while current_frame and frame_count < 10:  # Limit to prevent infinite loop
            current_frame = current_frame.f_back
            frame_count += 1
            if current_frame:
                module_path = current_frame.f_globals.get('__file__', '')
                if module_path and module_path != __file__:
                    # Skip any frame that's also from prax_logger.py or prax_handlers.py
                    if 'prax_logger.py' not in module_path and 'prax_handlers.py' not in module_path:
                        module_name = Path(module_path).stem
                        return module_name
        return 'unknown_module'
    finally:
        del frame

def get_calling_module_path() -> Optional[str]:
    """Detect calling module path from stack trace"""
    import inspect

    frame = inspect.currentframe()
    try:
        # Walk up the stack to find the calling module
        current_frame = frame
        frame_count = 0
        while current_frame and frame_count < 10:
            current_frame = current_frame.f_back
            frame_count += 1
            if current_frame:
                module_path = current_frame.f_globals.get('__file__', '')
                if module_path and module_path != __file__:
                    # Skip any frame that's also from prax_logger.py or prax_handlers.py
                    if 'prax_logger.py' not in module_path and 'prax_handlers.py' not in module_path:
                        return module_path
        return None
    finally:
        del frame

def detect_branch_from_path(module_path: str) -> Optional[str]:
    """Detect branch name from module file path

    Examples:
        /home/aipass/aipass_core/flow/apps/module.py → "aipass_core/flow"
        /home/aipass/aipass_core/branch_operations/apps/module.py → "aipass_core/branch_operations"
        /home/aipass/aipass_core/prax/apps/module.py → "aipass_core/prax"
        /home/aipass/other_dir/module.py → "other_dir"
    """
    if not module_path:
        return None

    path = Path(module_path)
    parts = path.parts

    # Find /home/aipass in path
    try:
        aipass_idx = parts.index('aipass')

        # Check if this is aipass_core structure
        if aipass_idx + 1 < len(parts) and parts[aipass_idx + 1] == 'aipass_core':
            # For aipass_core, we want aipass_core/module_name format
            # e.g., /home/aipass/aipass_core/flow/apps/module.py → "aipass_core/flow"
            if aipass_idx + 2 < len(parts):
                module_folder = parts[aipass_idx + 2]
                # Make sure it's not just a file in aipass_core root
                if aipass_idx + 3 < len(parts):
                    return f"aipass_core/{module_folder}"
        else:
            # For other structures, return the folder after aipass
            # e.g., /home/aipass/some_project/module.py → "some_project"
            if aipass_idx + 1 < len(parts):
                potential_branch = parts[aipass_idx + 1]
                # Skip if it's a file directly in /home/aipass
                if aipass_idx + 2 < len(parts):
                    return potential_branch
    except ValueError:
        pass

    return None

def setup_individual_logger(module_name: str) -> logging.Logger:
    """Setup individual logger for a specific module with dual logging support"""
    if module_name in _captured_loggers:
        return _captured_loggers[module_name]

    # Log new logger creation
    if '_system_logger' in globals() and _system_logger:
        _system_logger.info(f"Creating logger for module: {module_name}")

    # Create individual logger for this module
    logger = logging.getLogger(f"captured_{module_name}")
    logger.setLevel(DEFAULT_LOG_LEVEL)
    logger.handlers.clear()

    # Load config-driven limits
    log_config = load_log_config()

    # Create formatter (shared by all handlers)
    formatter = logging.Formatter(
        log_config['log_format'],
        log_config['date_format']
    )

    # HANDLER 1: System-wide log (always created)
    system_log_file = SYSTEM_LOGS_DIR / f"{module_name}.log"
    system_limits = log_config['system_logs']
    system_max_bytes = lines_to_bytes(system_limits['max_lines'])
    system_handler = RotatingFileHandler(
        system_log_file,
        maxBytes=system_max_bytes,
        backupCount=system_limits['backup_count'],
        encoding='utf-8'
    )
    system_handler.setFormatter(formatter)
    logger.addHandler(system_handler)

    # HANDLER 2: Branch-local log (if module is in a branch)
    module_path = get_calling_module_path()
    branch = detect_branch_from_path(module_path) if module_path else None

    if branch:
        # Create branch logs directory if it doesn't exist
        # Branch format is now "aipass_core/module" or "project_name"
        branch_logs_dir = Path("/home/aipass") / branch / "logs"
        branch_logs_dir.mkdir(parents=True, exist_ok=True)

        # Create branch-local log file
        branch_log_file = branch_logs_dir / f"{module_name}.log"
        local_limits = log_config['local_logs']
        local_max_bytes = lines_to_bytes(local_limits['max_lines'])
        branch_handler = RotatingFileHandler(
            branch_log_file,
            maxBytes=local_max_bytes,
            backupCount=local_limits['backup_count'],
            encoding='utf-8'
        )
        branch_handler.setFormatter(formatter)
        logger.addHandler(branch_handler)

        # Log to system logger
        if '_system_logger' in globals() and _system_logger:
            _system_logger.info(f"Logger created for {module_name} → system: {system_log_file} ({system_limits['max_lines']} lines), branch: {branch_log_file} ({local_limits['max_lines']} lines)")
    else:
        # Log to system logger
        if '_system_logger' in globals() and _system_logger:
            _system_logger.info(f"Logger created for {module_name} → {system_log_file} ({system_limits['max_lines']} lines)")

    # HANDLER 3: Terminal output (if enabled)
    if _terminal_output_enabled and _terminal_module_available:
        if should_display_terminal(module_name):
            terminal_handler = create_terminal_handler()
            logger.addHandler(terminal_handler)

    # Store for reuse
    _captured_loggers[module_name] = logger

    return logger

# =============================================
# GLOBAL SYSTEM LOGGER
# =============================================

def get_system_logger():
    """Get logger that automatically routes to correct module log file"""
    module_name = get_calling_module()
    return setup_individual_logger(module_name)

# Export global logger FUNCTION for modules to call
# Don't create the logger at import time - create it when called
def system_logger_info(message):
    """Log info message to calling module's log file"""
    logger = get_system_logger()
    logger.info(message)

def system_logger_warning(message):
    """Log warning message to calling module's log file"""
    logger = get_system_logger()
    logger.warning(message)

def system_logger_error(message):
    """Log error message to calling module's log file"""
    logger = get_system_logger()
    logger.error(message)

# Simple logger object that calls the functions
class SystemLogger:
    def info(self, message):
        system_logger_info(message)

    def warning(self, message):
        system_logger_warning(message)

    def error(self, message):
        system_logger_error(message)

# Export the logger object
system_logger = SystemLogger()

def setup_system_logger() -> logging.Logger:
    """Setup prax_logger's own logging"""
    global _system_logger

    if _system_logger:
        return _system_logger

    # Load config-driven limits
    log_config = load_log_config()

    # Create prax_logger's own logger
    _system_logger = logging.getLogger("prax_system_logger")
    _system_logger.setLevel(DEFAULT_LOG_LEVEL)
    _system_logger.handlers.clear()

    # Create prax_logger's own log file
    log_file = SYSTEM_LOGS_DIR / "prax_logger.log"

    # Create rotating file handler with config-driven limits
    system_limits = log_config['system_logs']
    system_max_bytes = lines_to_bytes(system_limits['max_lines'])
    handler = RotatingFileHandler(
        log_file,
        maxBytes=system_max_bytes,
        backupCount=system_limits['backup_count'],
        encoding='utf-8'
    )

    # Set formatter
    formatter = logging.Formatter(
        log_config['log_format'],
        log_config['date_format']
    )
    handler.setFormatter(formatter)
    _system_logger.addHandler(handler)

    # Log system logger creation
    _system_logger.info("Prax system logger initialized successfully")
    _system_logger.info(f"System logger writing to: {log_file} ({system_limits['max_lines']} lines max)")

    return _system_logger

def enhanced_getLogger(name: Optional[str] = None) -> logging.Logger:
    """Enhanced getLogger that redirects to our individual module loggers"""
    # Only print debug info if enabled in config
    if get_debug_prints_enabled():
        print(f"[DEBUG] enhanced_getLogger called with name: {name}")

    # Get the original logger first
    original_logger = _original_getLogger(name)

    # Get calling module for our routing
    module_name = get_calling_module()
    if get_debug_prints_enabled():
        print(f"[DEBUG] Detected calling module: {module_name}")

    # If we can detect the module, add our custom handler
    if module_name != 'unknown_module':
        if get_debug_prints_enabled():
            print(f"[DEBUG] Setting up individual logger for: {module_name}")
        # Clear existing handlers to prevent console output
        original_logger.handlers.clear()

        # Get or create our individual logger for this module
        individual_logger = setup_individual_logger(module_name)

        # Copy the handler from our individual logger to the original logger
        for handler in individual_logger.handlers:
            original_logger.addHandler(handler)

        # Set appropriate level
        original_logger.setLevel(DEFAULT_LOG_LEVEL)

        # Prevent propagation to root logger (stops console output)
        original_logger.propagate = False

    return original_logger

def install_logger_override():
    """Install the enhanced getLogger function globally"""
    logging.getLogger = enhanced_getLogger
    print(f"[{MODULE_NAME}] Global logger override installed")

def restore_original_logger():
    """Restore original getLogger function"""
    logging.getLogger = _original_getLogger
    print(f"[{MODULE_NAME}] Original logger function restored")

def get_captured_loggers_count() -> int:
    """Get count of captured loggers"""
    return len(_captured_loggers)

def get_captured_loggers() -> Dict[str, logging.Logger]:
    """Get dictionary of captured loggers"""
    return _captured_loggers.copy()

def enable_terminal_output():
    """Enable terminal output for all future loggers"""
    global _terminal_output_enabled
    _terminal_output_enabled = True
    print(f"[{MODULE_NAME}] Terminal output enabled")

def disable_terminal_output():
    """Disable terminal output"""
    global _terminal_output_enabled
    _terminal_output_enabled = False
    print(f"[{MODULE_NAME}] Terminal output disabled")

def is_terminal_output_enabled() -> bool:
    """Check if terminal output is enabled"""
    return _terminal_output_enabled

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
            "system_logs_dir": str(SYSTEM_LOGS_DIR),
            "max_log_size_kb": MAX_LOG_SIZE // 1024,
            "backup_count": BACKUP_COUNT,
            "log_level": "INFO"
        }
    }

def create_default_data() -> Dict[str, Any]:
    """Create default data structure"""
    return {
        "module_name": MODULE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime_stats": {
            "loggers_created": 0,
            "override_installed": False,
            "last_logger_created": None
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
    """Run module test - verify handler functions"""
    print(f"{MODULE_NAME} v{MODULE_VERSION}")
    print("=" * 60)

    # Ensure JSON files exist
    ensure_json_files_exist()

    # Test handler setup
    print(f"\nSystem logs directory: {SYSTEM_LOGS_DIR}")
    print(f"System logs directory exists: {SYSTEM_LOGS_DIR.exists()}")

    # Test system logger setup
    print(f"\nTesting system logger setup...")
    sys_logger = setup_system_logger()
    print(f"✓ System logger created: {sys_logger.name}")

    # Test individual logger creation
    print(f"\nTesting individual logger creation...")
    test_logger = setup_individual_logger("test_module")
    print(f"✓ Individual logger created for: test_module")

    # Test logger override
    print(f"\nTesting logger override functions...")
    print(f"✓ install_logger_override available")
    print(f"✓ restore_original_logger available")

    # Log this operation
    log_operation("module_test", True, "Handler module tested successfully")

    print("\n" + "=" * 60)
    print("✓ prax_handlers.py initialized successfully")
    print(f"✓ 3-file JSON pattern created in {PRAX_JSON_DIR}")
    print(f"✓ Handler functions ready for use")
    return 0

def handle_list_loggers():
    """List all captured loggers"""
    loggers = get_captured_loggers()
    print(f"{MODULE_NAME} - Active Loggers")
    print("=" * 60)
    print(f"Total loggers: {len(loggers)}\n")

    if not loggers:
        print("No loggers created yet. Run prax_logger.py init first.")
        return 0

    for i, (name, logger) in enumerate(sorted(loggers.items()), 1):
        print(f"{i:3}. {name:40} Level: {logger.level}")

    return 0

def handle_show_config():
    """Show handler configuration"""
    print(f"{MODULE_NAME} Configuration")
    print("=" * 60)
    print(f"System logs directory: {SYSTEM_LOGS_DIR}")
    print(f"Default log level:     {DEFAULT_LOG_LEVEL}")
    print(f"Max log size:          {MAX_LOG_SIZE:,} bytes ({MAX_LOG_SIZE // 1024 // 1024} MB)")
    print(f"Backup count:          {BACKUP_COUNT}")
    print(f"\nLog format:   {LOG_FORMAT}")
    print(f"Date format:  {DATE_FORMAT}")
    print(f"\nDebug prints enabled: {get_debug_prints_enabled()}")
    return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Prax Handlers Module - Logging handler setup and management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: test, list-loggers, show-config

  test         - Run module test and verify handler functions
  list-loggers - List all captured loggers
  show-config  - Display handler configuration settings

EXAMPLES:
  python3 prax_handlers.py test
  python3 prax_handlers.py list-loggers
  python3 prax_handlers.py show-config
        """
    )

    parser.add_argument('command',
                       choices=['test', 'list-loggers', 'show-config'],
                       help='Command to execute')

    args = parser.parse_args()

    # Route to command handlers
    if args.command == 'test':
        return handle_test()
    elif args.command == 'list-loggers':
        return handle_list_loggers()
    elif args.command == 'show-config':
        return handle_show_config()

if __name__ == "__main__":
    import sys
    sys.exit(main() or 0)
