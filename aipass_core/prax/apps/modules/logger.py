#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: logger.py - PRAX Public API
# Date: 2025-11-15
# Version: 1.0.0
# Category: prax/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-15): Updated logger module with complete public API
#   - v0.1.0 (2025-11-10): Created modular public API from archive.temp
#
# CODE STANDARDS:
#   - Follows AIPass Prax standards
#   - Public API for system-wide logging
#   - Auto-routing logger for all modules in ecosystem
#   - Provides lifecycle functions: initialize, shutdown, status
# =============================================

"""
PRAX Logger - Public API

This is the main entry point for PRAX logging system.
Other branches import from here:
    from prax.apps.modules.prax_logger import system_logger

Provides:
- system_logger: Auto-routing logger for all modules
- Lifecycle functions: initialize, shutdown
- Status and control functions
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from typing import Dict, Any

# NOTE: Cannot import CLI here - creates circular dependency
# CLI imports prax logger, so prax logger must not import CLI

# Import from handlers - internal implementation
from prax.apps.handlers.logging.setup import (
    setup_system_logger,
    setup_individual_logger,
    get_captured_loggers_count,
    enable_terminal_output as _enable_terminal,
    disable_terminal_output as _disable_terminal,
    is_terminal_output_enabled
)
from prax.apps.handlers.logging.introspection import get_calling_module
from prax.apps.handlers.logging.override import (
    install_logger_override,
    restore_original_logger,
    is_override_active
)
from prax.apps.handlers.logging.operations import (
    log_operation,
    create_config_file
)
from prax.apps.handlers.discovery.scanner import discover_python_modules
from prax.apps.handlers.discovery.watcher import (
    start_file_watcher,
    stop_file_watcher,
    is_file_watcher_active
)
from prax.apps.handlers.registry.save import save_module_registry
from prax.apps.handlers.registry.load import load_module_registry
from prax.apps.handlers.config.load import SYSTEM_LOGS_DIR, PRAX_JSON_DIR

# Module constants
MODULE_NAME = "prax_logger"
DATA_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_data.json"

# =============================================
# SYSTEM LOGGER - THE MAIN EXPORT
# =============================================

def get_system_logger():
    """Get logger that automatically routes to correct module log file"""
    module_name = get_calling_module()
    return setup_individual_logger(module_name)

class SystemLogger:
    """Auto-routing logger that writes to calling module's log file"""

    _watcher_started = False

    def _ensure_watcher(self):
        """Lazy-start file watchers on first logger use"""
        if not SystemLogger._watcher_started:
            # Start prax watcher (Python file discovery)
            # Wrapped in try/except - inotify may be maxed by VS Code
            if not is_file_watcher_active():
                try:
                    start_file_watcher()
                except OSError:
                    pass  # inotify limit reached, continue without watcher
            # Fire startup event (trigger auto-initializes handlers)
            try:
                from trigger.apps.modules.core import trigger
                trigger.fire('startup')
            except (ImportError, OSError):
                pass  # Trigger not available or inotify full, silent fallback
            SystemLogger._watcher_started = True

    def info(self, message, *args, **kwargs):
        """Log info message to calling module's log file"""
        self._ensure_watcher()
        logger = get_system_logger()
        logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """Log warning message to calling module's log file"""
        self._ensure_watcher()
        logger = get_system_logger()
        logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """Log error message to calling module's log file"""
        self._ensure_watcher()
        logger = get_system_logger()
        logger.error(message, *args, **kwargs)

# Export the logger object - this is what other branches import
system_logger = SystemLogger()

# =============================================
# LIFECYCLE FUNCTIONS
# =============================================

def initialize_logging_system():
    """Initialize the complete logging system

    Steps:
    1. Create config file if missing
    2. Discover all Python modules
    3. Save module registry
    4. Setup system logger
    5. Install logger override
    6. Start file watcher
    """
    print(f"[{MODULE_NAME}] Initializing system-wide logging...")

    # Create config file if missing
    create_config_file()

    # Discover all modules
    modules = discover_python_modules()

    # Save registry
    save_module_registry(modules)

    # Setup prax_logger's own logging
    system_logger_instance = setup_system_logger()

    # Log system startup
    system_logger_instance.info("Prax logging system initialized")
    system_logger_instance.info(f"System logs directory: {SYSTEM_LOGS_DIR}")
    system_logger_instance.info(f"Found {len(modules)} modules for logging setup")

    # Install logger override
    install_logger_override()
    system_logger_instance.info("Logger override system installed")

    # Start file watcher
    start_file_watcher()

    log_operation("Logging system initialized", {
        "modules_discovered": len(modules),
        "consolidated_logger": True
    })

    print(f"[{MODULE_NAME}] System initialized - {len(modules)} modules, individual logging")

def shutdown_logging_system():
    """Shutdown logging system cleanly

    Steps:
    1. Stop file watcher
    2. Restore original logger
    3. Log shutdown operation
    """
    print(f"[{MODULE_NAME}] Shutting down logging system...")

    # Stop file watcher
    stop_file_watcher()

    # Restore original logger
    restore_original_logger()

    log_operation("Logging system shutdown", {})
    print(f"[{MODULE_NAME}] Shutdown complete")

def start_continuous_logging():
    """Start continuous logging in background mode with live terminal output

    Enables terminal output and runs until Ctrl+C.
    Displays status updates every 5 minutes.

    MODULE orchestration pattern: Thin wrapper that delegates to handler.
    """
    from prax.apps.handlers.logging.monitoring import run_monitoring_loop

    print(f"[{MODULE_NAME}] Starting continuous logging mode with terminal output...")
    sys.stdout.flush()

    # Enable terminal output for live debugging
    enable_terminal_output()

    # Initialize the logging system
    initialize_logging_system()

    # Delegate to handler for monitoring loop
    try:
        run_monitoring_loop(
            status_callback=get_system_status,
            interval=5,
            status_interval=300
        )
    except KeyboardInterrupt:
        # Handler re-raises KeyboardInterrupt, we handle cleanup here
        disable_terminal_output()
        shutdown_logging_system()
        print(f"[{MODULE_NAME}] Logger capture stopped.")
        sys.stdout.flush()

# =============================================
# STATUS AND CONTROL
# =============================================

def get_system_status() -> Dict[str, Any]:
    """Get current logging system status

    Returns:
        Dict with system status information:
        - total_modules: Number of discovered modules
        - individual_loggers: Number of active loggers
        - system_logs_dir: Path to system logs
        - registry_file: Path to module registry
        - file_watcher_active: Watcher status
        - logger_override_active: Override status
    """
    modules = load_module_registry()

    return {
        "total_modules": len(modules),
        "individual_loggers": get_captured_loggers_count(),
        "system_logs_dir": str(SYSTEM_LOGS_DIR),
        "registry_file": str(DATA_FILE),
        "file_watcher_active": is_file_watcher_active(),
        "logger_override_active": is_override_active()
    }

def enable_terminal_output():
    """Enable terminal output for all future loggers"""
    _enable_terminal()

def disable_terminal_output():
    """Disable terminal output"""
    _disable_terminal()
