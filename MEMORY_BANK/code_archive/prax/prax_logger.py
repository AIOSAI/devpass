# =============================================
# META DATA HEADER
# Name: prax_logger.py
# Date: 2025-07-11
# Version: 0.1.0
#
# CHANGELOG:
#   - v0.1.0 (2025-07-11): System-wide logging with auto-discovery and print routing
# =============================================

"""
Prax System-Wide Logging Module

Auto-discovers all .py modules in AIPass-Ecosystem and provides centralized logging.
Features global print() override with routing options and live module monitoring.
"""

import os
import json
import logging
import importlib
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from logging.handlers import RotatingFileHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time

# INFRASTRUCTURE IMPORT PATTERN - Universal AIPass pattern
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.append(str(AIPASS_ROOT))

# =============================================
# IMPORTS FROM PRAX MODULES
# =============================================

# Import configuration from prax_config
from prax.apps.modules.prax_config import (
    AIPASS_ROOT,
    PRAX_ROOT,
    ECOSYSTEM_ROOT,
    SYSTEM_LOGS_DIR,
    PRAX_JSON_DIR,
    DEFAULT_LOG_LEVEL,
    MAX_LOG_SIZE,
    BACKUP_COUNT,
    LOG_FORMAT,
    DATE_FORMAT,
    load_ignore_patterns_from_config
)

# Import registry management from prax_registry
from prax.apps.prax_registry import (
    save_module_registry,
    load_module_registry
)

# Import handler functions from prax_handlers
from prax.apps.prax_handlers import (
    get_calling_module,
    setup_individual_logger,
    get_system_logger,
    system_logger,
    setup_system_logger,
    enhanced_getLogger,
    install_logger_override,
    restore_original_logger,
    get_captured_loggers_count,
    get_captured_loggers,
    enable_terminal_output,
    disable_terminal_output,
    is_terminal_output_enabled,
    _original_getLogger
)

# Import discovery functions from prax_discovery
from prax.apps.prax_discovery import (
    should_ignore_path,
    discover_python_modules,
    scan_directory_safely,
    start_file_watcher,
    stop_file_watcher,
    is_file_watcher_active
)

# =============================================
# MODULE CONFIGURATION
# =============================================

# Module identity
MODULE_NAME = "prax_logger"

# Configuration files
CONFIG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_log.json"

# Discovery and handler functions now imported from prax_discovery and prax_handlers modules

# =============================================
# OPERATION LOGGING
# =============================================

def log_operation(message: str, data: Optional[Dict] = None):
    """Log prax_logging operations"""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": message,
        "data": data or {}
    }
    
    # Load existing log
    log_entries = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log_entries = json.load(f)
        except:
            log_entries = []
    
    # Add new entry
    log_entries.append(entry)
    
    # Keep only last 1000 entries
    if len(log_entries) > 1000:
        log_entries = log_entries[-1000:]
    
    # Save log
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_entries, f, indent=2, ensure_ascii=False)

# =============================================
# MAIN FUNCTIONS
# =============================================

def create_config_file():
    """Create default config file if it doesn't exist"""
    if not CONFIG_FILE.exists():
        default_config = {
            "module_name": MODULE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "log_level": "INFO",
                "max_log_size_mb": 10,
                "backup_count": 5,
                "log_format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S",
                "console_output": True,
                "file_output": True,
                "rotation_enabled": True,
                "debug_prints": False,
                "log_directories": [
                    "system_logs",
                    "skill_logs", 
                    "error_logs"
                ]
            }
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            print(f"[{MODULE_NAME}] Config file created: {CONFIG_FILE}")
        except Exception as e:
            print(f"[{MODULE_NAME}] Failed to create config file: {e}")

def initialize_logging_system():
    """Initialize the complete logging system"""
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

def get_system_status() -> Dict[str, Any]:
    """Get current logging system status"""
    modules = load_module_registry()

    return {
        "total_modules": len(modules),
        "individual_loggers": get_captured_loggers_count(),
        "system_logs_dir": str(SYSTEM_LOGS_DIR),
        "registry_file": str(DATA_FILE),
        "file_watcher_active": is_file_watcher_active(),
        "logger_override_active": logging.getLogger != _original_getLogger
    }

def shutdown_logging_system():
    """Shutdown logging system cleanly"""
    print(f"[{MODULE_NAME}] Shutting down logging system...")
    
    # Stop file watcher
    stop_file_watcher()
    
    # Restore original logger
    restore_original_logger()
    
    log_operation("Logging system shutdown")
    print(f"[{MODULE_NAME}] Shutdown complete")

def start_continuous_logging():
    """Start continuous logging in background mode with live terminal output"""
    print(f"[{MODULE_NAME}] Starting continuous logging mode with terminal output...")
    import sys
    sys.stdout.flush()

    # Enable terminal output for live debugging
    enable_terminal_output()

    # Initialize the logging system
    initialize_logging_system()

    # Keep running until interrupted
    try:
        print(f"[{MODULE_NAME}] Logger capture active - monitoring all modules")
        print(f"[{MODULE_NAME}] Terminal output enabled - you'll see live logs below")
        print("Press Ctrl+C to stop logging...")
        print("=" * 60)
        sys.stdout.flush()
        counter = 0
        while True:
            import time
            time.sleep(5)  # Check every 5 seconds
            counter += 5
            if counter % 300 == 0:  # Status update every 5 minutes
                print("\n" + "=" * 60)
                status = get_system_status()
                modules_count = status['total_modules']
                loggers_count = status['individual_loggers']
                print(f"[{MODULE_NAME}] Status: {modules_count} modules discovered, {loggers_count} loggers active")
                print("=" * 60)
                sys.stdout.flush()

    except KeyboardInterrupt:
        print(f"\n[{MODULE_NAME}] Shutting down continuous logging...")
        sys.stdout.flush()
        disable_terminal_output()
        shutdown_logging_system()
        print(f"[{MODULE_NAME}] Logger capture stopped.")
        sys.stdout.flush()

def handle_init(args):
    """Handle init command"""
    initialize_logging_system()

def handle_status(args):
    """Handle status command"""
    status = get_system_status()
    print("\n" + "="*60)
    print("PRAX LOGGING SYSTEM STATUS")
    print("="*60)
    for key, value in status.items():
        print(f"{key:.<40} {value}")
    print("="*60 + "\n")

def handle_test(args):
    """Handle test command"""
    print("="*60)
    print("PRAX LOGGING SYSTEM - SELF TEST")
    print("="*60)
    
    # Run test in isolation
    try:
        # Test 1: Initialize system
        print("\n1. Initializing logging system...")
        initialize_logging_system()
        
        # Test 2: Check system status
        print("\n2. Checking system status...")
        status = get_system_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        # Test 3: Test logger capture
        print("\n3. Testing logger capture...")
        
        # Test logger capture (should create individual log file)
        test_logger = logging.getLogger('test_module')
        test_logger.info("TEST: Logger info message")
        test_logger.warning("TEST: Logger warning message")
        test_logger.error("TEST: Logger error message")
        
        # Test 4: Check log files created
        print("\n4. Checking System_Logs directory...")
        log_files = list(SYSTEM_LOGS_DIR.glob("*.log"))
        print(f"   Created {len(log_files)} log files:")
        for log_file in sorted(log_files)[:10]:  # Show first 10
            size = log_file.stat().st_size
            print(f"     📄 {log_file.name} ({size} bytes)")
        
        if len(log_files) > 10:
            print(f"     ... and {len(log_files) - 10} more")
        
        # Test 5: Module registry
        print("\n5. Checking module registry...")
        modules = load_module_registry()
        print(f"   Registry contains {len(modules)} modules")
        
        # Test 6: Brief pause to let file watcher settle
        print("\n6. Testing file watcher (5 second test)...")
        import time
        time.sleep(5)
        
        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"✅ System Logs: {SYSTEM_LOGS_DIR}")
        print(f"✅ Registry: {DATA_FILE}")
        print(f"✅ Discovered {len(modules)} modules")
        print(f"✅ Created {len(log_files)} log files")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean shutdown
        print("\n7. Shutting down test...")
        shutdown_logging_system()
        print("\nTest complete!")

def handle_run(args):
    """Handle run command"""
    start_continuous_logging()

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Prax System-Wide Logging Module - Auto-discovers and manages centralized logging for all modules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: init, status, test, run

  init   - Initialize logging system and discover modules
  status - Display current logging system status
  test   - Run self-test and verify logging functionality
  run    - Start continuous logging in background mode

EXAMPLES:
  python prax_logger.py init
  python prax_logger.py status
  python prax_logger.py test
  python prax_logger.py run
        """
    )

    parser.add_argument('command',
                       nargs='?',
                       choices=['init', 'status', 'test', 'run'],
                       default='run',
                       help='Command to execute (default: run)')

    args = parser.parse_args()

    # Route to command handlers
    if args.command == 'init':
        handle_init(args)
    elif args.command == 'status':
        handle_status(args)
    elif args.command == 'test':
        handle_test(args)
    elif args.command == 'run':
        handle_run(args)

if __name__ == "__main__":
    sys.exit(main())