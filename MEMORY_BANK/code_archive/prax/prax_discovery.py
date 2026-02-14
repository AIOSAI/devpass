#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: prax_discovery.py - Python Module Discovery & Monitoring
# Date: 2025-10-25
# Version: 1.0.0
# Category: prax
#
# CHANGELOG:
#   - v1.0.0 (2025-10-25): Extracted from prax_logger.py - module discovery and file watching
# =============================================

"""
Prax Module Discovery System

Discovers all Python modules in AIPass ecosystem and monitors for new files.
Provides file watching with watchdog for live module detection.
"""

# =============================================
# IMPORTS
# =============================================

# INFRASTRUCTURE IMPORT PATTERN - Universal AIPass pattern
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.append(str(AIPASS_ROOT))

# Import from prax_config and prax_registry
from prax.apps.prax_config import (
    ECOSYSTEM_ROOT,
    SYSTEM_LOGS_DIR,
    load_ignore_patterns_from_config
)
from prax.apps.prax_registry import (
    save_module_registry,
    load_module_registry
)

# Standard imports
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "prax_discovery"
MODULE_VERSION = "1.0.0"

# 3-File JSON Pattern for this module
PRAX_JSON_DIR = AIPASS_ROOT / "prax" / "prax_json"
CONFIG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_log.json"

# =============================================
# MODULE DISCOVERY FUNCTIONS
# =============================================

def should_ignore_path(path: Path) -> bool:
    """Check if path should be ignored based on patterns from config"""
    path_parts = path.parts  # Keep original case for exact matching

    # Load ignore patterns from config (with fallback to hardcoded)
    ignore_patterns = load_ignore_patterns_from_config()

    # Check against ignore patterns
    for part in path_parts:
        if part in ignore_patterns:
            return True

    return False

def discover_python_modules() -> Dict[str, Dict[str, Any]]:
    """Discover all Python modules in the ecosystem"""
    modules = {}

    print(f"[{MODULE_NAME}] Scanning {ECOSYSTEM_ROOT} for Python modules...")

    # Scan entire ecosystem recursively
    scan_directory_safely(ECOSYSTEM_ROOT, modules)

    print(f"[{MODULE_NAME}] Discovered {len(modules)} Python modules")

    # Log discovery operation
    log_operation("discover_modules", True, f"Discovered {len(modules)} modules")

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
        log_operation("scan_directory", False, f"Permission denied: {directory}")
    except Exception as e:
        print(f"[{MODULE_NAME}] Warning: Error scanning {directory}: {e}")
        log_operation("scan_directory", False, f"Error: {directory} - {e}")

# =============================================
# FILE MONITORING
# =============================================

class PythonFileWatcher(FileSystemEventHandler):
    """Watch for new Python files and log file activity"""

    def __init__(self):
        super().__init__()
        # Track file positions for log tailing
        self.log_positions = {}
        # Track last command execution for separators
        self.last_command = None
        self.last_log_time = None

    def on_created(self, event):
        if not event.is_directory and str(event.src_path).endswith('.py'):
            py_file = Path(str(event.src_path))

            # Skip ignored paths
            if should_ignore_path(py_file):
                return

            module_name = py_file.stem

            # Skip if already in registry
            modules = load_module_registry()
            if module_name in modules:
                return

            # Add new module to registry
            try:
                relative_path = py_file.relative_to(ECOSYSTEM_ROOT)
            except ValueError:
                # File is outside ECOSYSTEM_ROOT, skip
                return

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

            print(f"[{MODULE_NAME}] NEW MODULE DETECTED: {module_name}", flush=True)
            log_operation("new_module_detected", True, f"{module_name} at {relative_path}")

    def on_modified(self, event):
        """Watch for log file modifications and display new entries"""
        if event.is_directory:
            return

        file_path = str(event.src_path)

        # Only watch .log files
        if not file_path.endswith('.log'):
            return

        # Only watch files in system_logs directory
        if str(SYSTEM_LOGS_DIR) not in file_path:
            return

        try:
            # Get current file size
            current_size = Path(file_path).stat().st_size

            # Get last known position
            last_pos = self.log_positions.get(file_path, 0)

            # If file shrunk (rotated), reset position
            if current_size < last_pos:
                last_pos = 0

            # Read new content
            if current_size > last_pos:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_pos)
                    new_lines = f.read()

                    if new_lines.strip():
                        # Extract module name from log file path
                        module_name = Path(file_path).stem

                        # Display new log lines (with filtering and color-coding)
                        for line in new_lines.strip().split('\n'):
                            if line.strip():
                                # Check if this is a new command execution
                                command_info = self._extract_command_info(line)
                                if command_info:
                                    self._print_command_separator(command_info)

                                # Filter out initialization noise
                                if self._should_display_log(line):
                                    formatted_line = self._format_log_with_color(module_name, line)
                                    print(formatted_line, flush=True)

                    # Update position
                    self.log_positions[file_path] = f.tell()

        except Exception as e:
            # Silently ignore errors (file might be locked, etc.)
            pass

    def _should_display_log(self, log_line: str) -> bool:
        """Filter out initialization noise - only show meaningful task logs"""
        # Common initialization patterns to skip
        noise_patterns = [
            "Initializing ",
            "Module initialized",
            "Module initialization completed",
            "Configuration loaded",
            "Data loaded",
            "Registry loaded",
            "loaded config from",
            "Cleanup completed - Removed 0",
        ]

        for pattern in noise_patterns:
            if pattern in log_line:
                return False

        return True

    def _format_log_with_color(self, module_name: str, log_line: str) -> str:
        """Format log line with ANSI color codes based on log level"""
        # ANSI color codes
        RED = '\033[91m'
        YELLOW = '\033[93m'
        RESET = '\033[0m'

        # Detect log level and apply color
        if ' - ERROR - ' in log_line or ' ERROR ' in log_line or '[ERROR]' in log_line:
            return f"{RED}[LOG] {module_name}: {log_line}{RESET}"
        elif ' - WARNING - ' in log_line or ' WARNING ' in log_line or '[WARNING]' in log_line:
            return f"{YELLOW}[LOG] {module_name}: {log_line}{RESET}"
        else:
            # INFO and other levels - no color
            return f"[LOG] {module_name}: {log_line}"

    def _extract_command_info(self, log_line: str) -> str | None:
        """Extract command information from log line if it's a new command execution"""
        import re

        # Pattern 1: Drone commands - "Drone started with args: ['close', 'plan', '0098']"
        if "Drone started with args:" in log_line or "[drone] Drone started with args:" in log_line:
            match = re.search(r"args:\s*\[([^\]]+)\]", log_line)
            if match:
                args = match.group(1).replace("'", "").replace('"', '')
                return f"drone {args}"

        # Pattern 2: Flow plan commands - check if different from last command
        if "FLOW_PLAN]" in log_line and ("Creating" in log_line or "Closing" in log_line or "Opening" in log_line):
            # Extract the action
            if "Creating" in log_line:
                return "flow create plan"
            elif "Closing" in log_line:
                match = re.search(r"PLAN(\d+)", log_line)
                if match:
                    return f"flow close plan {match.group(1)}"
            elif "Opening" in log_line:
                match = re.search(r"PLAN(\d+)", log_line)
                if match:
                    return f"flow open plan {match.group(1)}"

        # Pattern 3: Module initialization/start patterns
        # Detect common initialization keywords that indicate command execution
        initialization_keywords = [
            "Initializing", "Starting", "Running", "Executing",
            "Processing", "Loading", "Scanning", "Analyzing"
        ]

        for keyword in initialization_keywords:
            if keyword in log_line:
                # Extract module name from log format: "[MODULE_NAME] Initializing..."
                module_match = re.search(r"\[([A-Z_]+)\]\s+" + keyword, log_line)
                if module_match:
                    module_name = module_match.group(1).lower().replace('_', ' ')
                    # Extract what follows the keyword
                    after_keyword = log_line.split(keyword, 1)[1].strip()
                    # Take first few words as command description
                    desc_words = after_keyword.split()[:4]
                    desc = ' '.join(desc_words).rstrip('.')
                    return f"{module_name}: {keyword.lower()} {desc}"

        return None

    def _print_command_separator(self, command: str) -> None:
        """Print a green separator header for new command execution"""
        # Skip if same command as last one (avoid duplicate separators)
        if command == self.last_command:
            return

        self.last_command = command

        # ANSI color codes
        GREEN = '\033[92m'
        BOLD = '\033[1m'
        RESET = '\033[0m'

        # Print separator
        separator = "=" * 80
        print(f"\n{GREEN}{BOLD}{separator}{RESET}", flush=True)
        print(f"{GREEN}{BOLD}>>> COMMAND EXECUTED: {command}{RESET}", flush=True)
        print(f"{GREEN}{BOLD}{separator}{RESET}\n", flush=True)

# Global observer instance
_observer: Optional[Any] = None

def start_file_watcher():
    """Start watching for new Python files and log activity"""
    global _observer

    if _observer and _observer.is_alive():
        return

    # Create watcher instance
    watcher = PythonFileWatcher()

    # Initialize log positions to END of existing files (only show NEW entries)
    if SYSTEM_LOGS_DIR.exists():
        for log_file in SYSTEM_LOGS_DIR.glob("*.log"):
            try:
                watcher.log_positions[str(log_file)] = log_file.stat().st_size
            except:
                pass

    new_observer = Observer()
    new_observer.schedule(watcher, str(ECOSYSTEM_ROOT), recursive=True)
    new_observer.start()
    _observer = new_observer
    print(f"[{MODULE_NAME}] File watcher started", flush=True)
    log_operation("start_watcher", True, "File watcher started monitoring")

def stop_file_watcher():
    """Stop file watcher"""
    global _observer

    if _observer and _observer.is_alive():
        _observer.stop()
        _observer.join()
        print(f"[{MODULE_NAME}] File watcher stopped")
        log_operation("stop_watcher", True, "File watcher stopped")

def is_file_watcher_active() -> bool:
    """Check if file watcher is currently active"""
    return _observer is not None and _observer.is_alive()

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
            "scan_location": str(ECOSYSTEM_ROOT),
            "max_depth": 10,
            "file_watcher_enabled": True,
            "auto_register_new_modules": True
        }
    }

def create_default_data() -> Dict[str, Any]:
    """Create default data structure"""
    return {
        "module_name": MODULE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime_stats": {
            "last_scan": None,
            "modules_discovered": 0,
            "watcher_active": False
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
    """Run module test - verify discovery and registry operations"""
    print(f"{MODULE_NAME} v{MODULE_VERSION}")
    print("=" * 60)

    # Ensure JSON files exist
    ensure_json_files_exist()

    # Test module discovery
    print(f"\nDiscovering Python modules...")
    modules = discover_python_modules()
    print(f"✓ Found {len(modules)} modules")

    # Save to registry
    save_module_registry(modules)
    print(f"✓ Saved to registry")

    # Test loading
    loaded = load_module_registry()
    print(f"✓ Registry loads: {len(loaded)} modules")

    print("\n" + "=" * 60)
    print("✓ prax_discovery.py initialized successfully")
    print(f"✓ 3-file JSON pattern created")
    print(f"✓ Ready to discover and monitor Python modules")
    return 0

def handle_scan():
    """Scan for Python modules and update registry"""
    print(f"{MODULE_NAME} - Module Scan")
    print("=" * 60)

    print(f"Scanning {ECOSYSTEM_ROOT}...")
    modules = discover_python_modules()
    print(f"\nFound {len(modules)} Python modules")

    # Save to registry
    save_module_registry(modules)
    print(f"✓ Registry updated")

    return 0

def handle_watch():
    """Start file watcher for new Python modules and live log monitoring"""
    print(f"{MODULE_NAME} - File Watcher & Live Log Monitor")
    print("=" * 60)
    print(f"Watching: {ECOSYSTEM_ROOT} (new .py files)")
    print(f"Monitoring: {SYSTEM_LOGS_DIR} (live log output)")
    print("Press Ctrl+C to stop\n")

    try:
        start_file_watcher()
        # Keep running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping file watcher...")
        stop_file_watcher()
        print("✓ File watcher stopped")
        return 0

def handle_show_modules(args):
    """Show discovered modules"""
    modules = load_module_registry()
    print(f"{MODULE_NAME} - Discovered Modules")
    print("=" * 60)
    print(f"Total: {len(modules)}\n")

    if not modules:
        print("No modules discovered. Run 'scan' command first.")
        return 1

    sorted_modules = sorted(modules.items())

    for i, (name, info) in enumerate(sorted_modules, 1):
        if args.verbose:
            print(f"{i}. {name}")
            print(f"   Path: {info.get('file_path', 'N/A')}")
            print(f"   Size: {info.get('size', 0):,} bytes")
            print()
        else:
            print(f"{i:3}. {name}")

    return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Prax Discovery Module - Python module discovery and file monitoring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: test, scan, watch, show-modules

  test         - Run module test and verify discovery operations
  scan         - Scan for Python modules and update registry
  watch        - Start file watcher for new Python modules (Ctrl+C to stop)
  show-modules - Display list of discovered modules

EXAMPLES:
  python3 prax_discovery.py test
  python3 prax_discovery.py scan
  python3 prax_discovery.py watch
  python3 prax_discovery.py show-modules
  python3 prax_discovery.py show-modules --verbose
        """
    )

    parser.add_argument('command',
                       choices=['test', 'scan', 'watch', 'show-modules'],
                       help='Command to execute')

    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show verbose output')

    args = parser.parse_args()

    # Route to command handlers
    if args.command == 'test':
        return handle_test()
    elif args.command == 'scan':
        return handle_scan()
    elif args.command == 'watch':
        return handle_watch()
    elif args.command == 'show-modules':
        return handle_show_modules(args)

if __name__ == "__main__":
    import sys
    sys.exit(main() or 0)
