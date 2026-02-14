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
import sys
import json
import logging
import importlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from logging.handlers import RotatingFileHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time

# =============================================
# MODULE CONFIGURATION  
# =============================================

# Module identity
MODULE_NAME = "prax_logger"

# System paths
ECOSYSTEM_ROOT = Path(__file__).parent.parent  # C:\AIPass-Ecosystem
SYSTEM_LOGS_DIR = ECOSYSTEM_ROOT / "system_logs"
PRAX_JSON_DIR = Path(__file__).parent / "prax_json"

# Auto-create directories
SYSTEM_LOGS_DIR.mkdir(exist_ok=True)
PRAX_JSON_DIR.mkdir(exist_ok=True)

# Configuration files
CONFIG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_log.json"

# Ignore folders for module discovery
IGNORE_FOLDERS = {
    '.git', '__pycache__', '.venv', 'vendor', 'node_modules',
    'Archive', 'Backups', 'External_Code_Sources', 'WorkShop',
    '.claude-server-commander-logs',
    'backup_system', 'backups', 'archive.local'  # Stop scanning backup directories
}

# Logging configuration
DEFAULT_LOG_LEVEL = logging.INFO
MAX_LOG_SIZE = 500 * 1024  # 500KB
BACKUP_COUNT = 0  # No backup files - just truncate when full
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Store original logging functions for restoration
_original_getLogger = logging.getLogger
_original_basicConfig = logging.basicConfig

# =============================================
# CONFIG HELPER FUNCTIONS
# =============================================

def get_debug_prints_enabled() -> bool:
    """Check if debug prints are enabled in config"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('config', {}).get('debug_prints', False)
    except Exception:
        pass
    return False  # Default to False if config missing/invalid

# =============================================
# MODULE DISCOVERY SYSTEM
# =============================================

def should_ignore_path(path: Path) -> bool:
    """Check if path should be ignored based on patterns"""
    path_parts = path.parts  # Keep original case for exact matching
    
    # Check against ignore folders
    for part in path_parts:
        if part in IGNORE_FOLDERS:
            return True
    
    return False

def discover_python_modules() -> Dict[str, Dict[str, Any]]:
    """Discover all Python modules in the ecosystem"""
    modules = {}
    
    print(f"[{MODULE_NAME}] Scanning {ECOSYSTEM_ROOT} for Python modules...")
    
    # Scan entire ecosystem recursively
    scan_directory_safely(ECOSYSTEM_ROOT, modules)
    
    print(f"[{MODULE_NAME}] Discovered {len(modules)} Python modules")
    return modules

def scan_directory_safely(directory: Path, modules: Dict, max_depth: int = 10):
    """Safely scan directory with depth limit"""
    if max_depth <= 0:
        return
    
    try:
        for item in directory.iterdir():
            if should_ignore_path(item):
                continue
            
            if item.is_file() and item.suffix == '.py':
                module_name = item.stem
                relative_path = item.relative_to(ECOSYSTEM_ROOT)
                
                modules[module_name] = {
                    "file_path": str(item),
                    "relative_path": str(relative_path),
                    "log_file": str(SYSTEM_LOGS_DIR / f"{module_name}.log"),
                    "discovered_time": datetime.now(timezone.utc).isoformat(),
                    "size": item.stat().st_size,
                    "modified_time": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                    "enabled": True
                }
                
            elif item.is_dir():
                scan_directory_safely(item, modules, max_depth - 1)
                
    except PermissionError as e:
        # Log permission denied directories for visibility
        print(f"[{MODULE_NAME}] Warning: Permission denied accessing {directory}")
        print(f"[{MODULE_NAME}] Permission denied scanning directory: {directory} - {e}")
    except Exception as e:
        print(f"[{MODULE_NAME}] Warning: Error scanning {directory}: {e}")

def save_module_registry(modules: Dict[str, Dict[str, Any]]):
    """Save module registry to JSON"""
    # Create proper 3-file structure format
    data_structure = {
        "module_name": MODULE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "modules": modules,
            "statistics": {
                "total_modules": len(modules),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "scan_location": str(ECOSYSTEM_ROOT),
                "log_directories": ["system_logs", "skill_logs", "error_logs"]
            }
        }
    }
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_structure, f, indent=2, ensure_ascii=False)

def load_module_registry() -> Dict[str, Dict[str, Any]]:
    """Load module registry from JSON"""
    if not DATA_FILE.exists():
        return {}
        
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle new 3-file structure format
            if isinstance(data, dict) and "data" in data and "modules" in data["data"]:
                return data["data"]["modules"]
            # Handle old format for backward compatibility
            else:
                return data.get('modules', {})
    except Exception as e:
        log_operation(f"Error loading module registry: {e}")
        return {}

# =============================================
# LOGGING SYSTEM
# =============================================

_system_logger: Optional[logging.Logger] = None
_captured_loggers: Dict[str, logging.Logger] = {}  # Store individual module loggers

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
                    # Skip any frame that's also from prax_logger.py
                    if 'prax_logger.py' not in module_path:
                        module_name = Path(module_path).stem
                        return module_name
        return 'unknown_module'
    finally:
        del frame

def setup_individual_logger(module_name: str) -> logging.Logger:
    """Setup individual logger for a specific module"""
    if module_name in _captured_loggers:
        return _captured_loggers[module_name]
    
    # Log new logger creation
    if '_system_logger' in globals() and _system_logger:
        _system_logger.info(f"Creating logger for module: {module_name}")
    
    # Create individual logger for this module
    logger = logging.getLogger(f"captured_{module_name}")
    logger.setLevel(DEFAULT_LOG_LEVEL)
    logger.handlers.clear()
    
    # Create individual log file for this module
    log_file = SYSTEM_LOGS_DIR / f"{module_name}.log"
    
    # Create rotating file handler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    
    # Set formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Store for reuse
    _captured_loggers[module_name] = logger
    
    # Log successful logger setup
    if '_system_logger' in globals() and _system_logger:
        _system_logger.info(f"Logger successfully created for {module_name} → {log_file}")
    
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
    
    # Create prax_logger's own logger
    _system_logger = logging.getLogger("prax_system_logger")
    _system_logger.setLevel(DEFAULT_LOG_LEVEL)
    _system_logger.handlers.clear()
    
    # Create prax_logger's own log file
    log_file = SYSTEM_LOGS_DIR / "prax_logger.log"
    
    # Create rotating file handler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    
    # Set formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    handler.setFormatter(formatter)
    _system_logger.addHandler(handler)
    
    # Log system logger creation
    _system_logger.info("Prax system logger initialized successfully")
    _system_logger.info(f"System logger writing to: {log_file}")
    
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

# =============================================
# FILE MONITORING
# =============================================

class PythonFileWatcher(FileSystemEventHandler):
    """Watch for new Python files being created"""
    
    def on_created(self, event):
        if not event.is_directory and str(event.src_path).endswith('.py'):
            py_file = Path(str(event.src_path))
            
            # Skip ignored paths
            if should_ignore_path(py_file):
                return
                
            print(f"[{MODULE_NAME}] New Python file detected: {py_file.name}")
            self._register_new_module(py_file)
    
    def _register_new_module(self, py_file: Path):
        """Register a newly detected Python module"""
        try:
            # Load existing registry
            modules = load_module_registry()
            
            # Add new module
            module_name = py_file.stem
            relative_path = py_file.relative_to(ECOSYSTEM_ROOT)
            
            modules[module_name] = {
                "file_path": str(py_file),
                "relative_path": str(relative_path),
                "log_file": str(SYSTEM_LOGS_DIR / f"{module_name}.log"),
                "discovered_time": datetime.now(timezone.utc).isoformat(),
                "size": py_file.stat().st_size,
                "modified_time": datetime.fromtimestamp(py_file.stat().st_mtime).isoformat(),
                "enabled": True
            }
            
            # Save updated registry
            save_module_registry(modules)
            
            # Setup logger for new module
            setup_individual_logger(module_name)
            
            log_operation(f"Auto-registered new module: {module_name}")
            
        except Exception as e:
            log_operation(f"Error registering new module {py_file.name}: {e}")

# Global observer instance
_observer = None

def start_file_watcher():
    """Start watching for new Python files"""
    global _observer
    
    if _observer and _observer.is_alive():
        return
    
    _observer = Observer()
    # Type assertion to help type checker
    assert _observer is not None
    _observer.schedule(PythonFileWatcher(), str(ECOSYSTEM_ROOT), recursive=True)
    _observer.start()
    print(f"[{MODULE_NAME}] File watcher started")

def stop_file_watcher():
    """Stop file watcher"""
    global _observer
    
    if _observer and _observer.is_alive():
        _observer.stop()
        _observer.join()
        print(f"[{MODULE_NAME}] File watcher stopped")

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
        "individual_loggers": len(_captured_loggers),
        "system_logs_dir": str(SYSTEM_LOGS_DIR),
        "registry_file": str(DATA_FILE),
        "file_watcher_active": _observer and _observer.is_alive(),
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
    """Start continuous logging in background mode"""
    print(f"[{MODULE_NAME}] Starting continuous logging mode...")
    import sys
    sys.stdout.flush()
    
    # Initialize the logging system
    initialize_logging_system()
    
    # Keep running until interrupted
    try:
        print(f"[{MODULE_NAME}] Logger capture active - monitoring all modules")
        print("Press Ctrl+C to stop logging...")
        sys.stdout.flush()
        counter = 0
        while True:
            import time
            time.sleep(5)  # Check every 5 seconds
            counter += 5
            if counter % 30 == 0:  # Status update every 30 seconds
                status = get_system_status()
                modules_count = status['total_modules']
                loggers_count = status['individual_loggers']
                print(f"[{MODULE_NAME}] Status: {modules_count} modules discovered, {loggers_count} loggers active")
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        print(f"\n[{MODULE_NAME}] Shutting down continuous logging...")
        sys.stdout.flush()
        shutdown_logging_system()
        print(f"[{MODULE_NAME}] Logger capture stopped.")
        sys.stdout.flush()

# =============================================
# SELF-TESTING
# =============================================

if __name__ == "__main__":
    import sys
    
    # Check for test mode argument
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Self-test mode
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
    else:
        # Default: Continuous background logging mode
        start_continuous_logging()
