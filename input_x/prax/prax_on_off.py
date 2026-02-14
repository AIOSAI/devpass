# =============================================
# META DATA HEADER
# Name: prax_on_off.py - Python module discovery and toggle control system
# Date: 2025-08-31
# Version: 1.2.0
# Category: prax
# 
# CHANGELOG (Max 5 entries - remove oldest when adding new):
#   - v1.2.0 (2025-08-31): Registry restructure - separated registry from runtime data, fixed ignore patterns
#   - v1.1.0 (2025-08-31): Added comprehensive ignore folder patterns, improved scanning efficiency
#   - v1.0.0 (2025-08-31): Python module registry with enable/disable toggle control
# =============================================

"""
Prax Module Discovery and Toggle Control

Scans the AIPass ecosystem for Python modules and maintains a registry
with enable/disable toggle control, file metadata, and system statistics.

Features:
- Automatic Python file discovery across ecosystem
- Module enable/disable toggle system with import hooks
- Registry separation (prax_registry.json vs prax_on_off_data.json)
- Comprehensive ignore patterns for clean scanning
- Real-time file watching with automatic registry updates
- JSON logging with detailed scan statistics
"""

# =============================================
# IMPORTS
# =============================================
import os
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime, timezone

import sys
sys.path.append(str(Path(__file__).parent.parent))  # Add ecosystem root to find prax module

# Import prax_logger for System_Logs integration
from prax.prax_logger import system_logger as logger

# =============================================
# CONSTANTS & CONFIG
# =============================================
CONFIG_FILE = "prax_on_off_config.json"
DATA_FILE = "prax_on_off_data.json"
LOG_FILE = "prax_on_off_log.json"
REGISTRY_FILE = "prax_registry.json"  # Separate registry file

# Ignore list - modules to never add to registry
IGNORE_LIST = {
    "__init__",
    "prax_on_off",  # Don't track ourselves
    "__pycache__",
    "test_",        # Ignore test files
    "temp_",        # Ignore temp files
    "backup",      # Ignore backup files
}

# Folders to completely ignore
IGNORE_FOLDERS = {
    "admin",
    "archive",
    "mcp_servers", 
    "backup_system",
    "tests",
    "tools",
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".pytest_cache",
    "dist",
    "build",
    ".vscode",
    "mcp-servers",
    "workshop",
    "aipass-help",
    "flow",
    "api",
    "aipass-drone",
    "a.i\\legacy",


}

# =============================================
# FILE WATCHER CLASS
# =============================================
class ModuleWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and self._is_py_file(event.src_path):
            file_path = Path(str(event.src_path))
            print(f"[Prax_on_off] New module detected: {file_path.name}")
            self._add_module(file_path.stem)
    
    def on_deleted(self, event):
        if not event.is_directory and self._is_py_file(event.src_path):
            file_path = Path(str(event.src_path))
            print(f"[Prax_on_off] Module deleted: {file_path.name}")
            self._remove_module(file_path.stem)
    
    def _is_py_file(self, file_path):
        return Path(file_path).suffix == ".py"
    
    def _add_module(self, module_name):
        # Skip if module should be ignored
        if should_ignore_module(module_name):
            return
            
        registry = self._load_registry()
        if module_name not in registry:
            # Find the file to get its info
            root_folder = Path(__file__).parent
            file_path = None
            for fp in root_folder.rglob(f"{module_name}.py"):
                file_path = fp
                break
                
            if file_path:
                # Keep existing toggle state, default to True for new files
                existing_entry = registry.get(module_name, {})
                enabled_state = existing_entry.get("enabled", True)
                
                registry[module_name] = {
                    "enabled": enabled_state,
                    "file_path": str(file_path),
                    "relative_path": str(file_path.relative_to(root_folder)),
                    "folder": file_path.parent.name,
                    "size_kb": round(file_path.stat().st_size / 1024, 2) if file_path.exists() else 0
                }
                self._save_registry(registry)
    
    def _remove_module(self, module_name):
        registry = self._load_registry()
        if module_name in registry:
            del registry[module_name]
            self._save_registry(registry)
    
    def _load_registry(self):
        registry_path = Path(__file__).parent / "prax_json" / REGISTRY_FILE
        if registry_path.exists():
            try:
                with open(registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _save_registry(self, registry):
        json_dir = Path(__file__).parent / "prax_json"
        json_dir.mkdir(exist_ok=True)
        registry_path = json_dir / REGISTRY_FILE
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

# === Registry functions ===
def should_ignore_module(module_name):
    """Check if module should be ignored"""
    # Check exact matches
    if module_name in IGNORE_LIST:
        return True
    
    # Check prefix matches (for patterns like test_, temp_)
    for ignore_pattern in IGNORE_LIST:
        if ignore_pattern.endswith('_') and module_name.startswith(ignore_pattern):
            return True
    
    return False

def scan_modules():
    """Scan root folder for .py files and build registry"""
    # Scan from AIPass-Ecosystem root (go up one level from Prax folder)
    root_folder = Path(__file__).parent.parent
    
    logger.info(f"Scanning from: {root_folder}")
    
    # Load existing registry to preserve toggle states
    existing_registry = load_registry()
    
    registry = {}
    # Scan root folder AND subdirectories
    for file_path in root_folder.rglob("*.py"):
        # Skip __pycache__ and other hidden folders
        if any(part.startswith('.') or part == '__pycache__' for part in file_path.parts):
            continue
            
        # EMERGENCY: Skip ignored folders (prevents 50k module scan!)
        if any(folder in str(file_path) for folder in IGNORE_FOLDERS):
            continue
            
        module_name = file_path.stem
        
        # Skip modules in ignore list
        if should_ignore_module(module_name):
            continue
            
        # Keep existing toggle state, default to True for new files
        existing_entry = existing_registry.get(module_name, {})
        enabled_state = existing_entry.get("enabled", True)
        
        # Add file info to registry entry
        registry[module_name] = {
            "enabled": enabled_state,
            "file_path": str(file_path),
            "relative_path": str(file_path.relative_to(root_folder)),
            "folder": file_path.parent.name,
            "size_kb": round(file_path.stat().st_size / 1024, 2) if file_path.exists() else 0
        }
    
    # Sort registry alphabetically by module name (case-insensitive)
    registry = dict(sorted(registry.items(), key=lambda x: x[0].lower()))
    
    # Save registry in separate prax_registry.json file
    json_dir = Path(__file__).parent / "prax_json"
    json_dir.mkdir(exist_ok=True)
    registry_path = json_dir / REGISTRY_FILE
    
    # Calculate folder statistics
    folder_stats = {}
    for module_data in registry.values():
        folder = module_data.get("folder", "unknown")
        folder_stats[folder] = folder_stats.get(folder, 0) + 1
    
    # Create the registry structure
    registry_structure = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "module_states": registry,
        "system_info": {
            "total_modules": len(registry),
            "enabled_modules": sum(1 for m in registry.values() if m.get("enabled", True)),
            "disabled_modules": sum(1 for m in registry.values() if not m.get("enabled", True)),
            "last_scan": datetime.now(timezone.utc).isoformat(),
            "folders": folder_stats
        }
    }
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry_structure, f, indent=2, ensure_ascii=False)
    
    # Also update the data file with runtime statistics
    data_path = json_dir / DATA_FILE
    data_structure = {
        "module_name": "prax_on_off",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "last_scan": datetime.now(timezone.utc).isoformat(),
            "scan_statistics": {
                "directories_scanned": len(folder_stats),
                "python_files_found": len(registry),
                "modules_registered": len(registry),
                "scan_duration_ms": 0  # Would need timing logic to fill this
            },
            "runtime_state": {
                "watcher_active": False,
                "auto_scan_enabled": True,
                "last_operation": "registry_scan",
                "operation_status": "success"
            },
            "registry_location": f"prax/prax_json/{REGISTRY_FILE}"
        }
    }
    
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data_structure, f, indent=2, ensure_ascii=False)
    
    return registry

# =============================================
# REGISTRY FUNCTIONS
# =============================================

def load_registry():
    """Load module registry from separate prax_registry.json"""
    registry_path = Path(__file__).parent / "prax_json" / REGISTRY_FILE
    if registry_path.exists():
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle new registry format
                if isinstance(data, dict) and "module_states" in data:
                    return data["module_states"]
                # Handle old format for backward compatibility
                else:
                    return data
        except json.JSONDecodeError:
            return {}
    return {}

def get_enabled_modules():
    """Get list of enabled modules"""
    registry = load_registry()
    return [name for name, config in registry.items() if config.get("enabled", False)]

# =============================================
# LOG JSON FUNCTIONS
# =============================================

def load_log_json():
    """Load the log JSON file"""
    log_path = Path(__file__).parent / "prax_json" / LOG_FILE
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"events": []}
    return {"events": []}

def save_log_json(log_data):
    """Save the log JSON file"""
    # Ensure prax_json directory exists
    json_dir = Path(__file__).parent / "prax_json"
    json_dir.mkdir(exist_ok=True)
    
    log_path = json_dir / LOG_FILE
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

def log_event(event_type, details):
    """Add an event to the log JSON"""
    log_data = load_log_json()
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "details": details
    }
    log_data["events"].append(event)
    
    # Keep only last 100 events to prevent file bloat
    if len(log_data["events"]) > 100:
        log_data["events"] = log_data["events"][-100:]
    
    save_log_json(log_data)
    logger.info(f"prax_on_off event: {event_type} - {details}")

def create_config_file():
    """Create default config file if it doesn't exist"""
    config_path = Path(__file__).parent / "prax_json" / CONFIG_FILE
    if not config_path.exists():
        default_config = {
            "module_name": "prax_on_off",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "auto_discovery": True,
                "scan_folders": [
                    "skills/skills_api",
                    "skills/skills_core", 
                    "skills/skills_memory",
                    "skills/skills_mods",
                    "prax",
                    "a.i/seed",
                    "a.i/nexus"
                ],
                "file_extensions": [".py"],
                "exclude_patterns": ["__pycache__", "*.pyc", ".git"],
                "auto_enable_new_modules": True,
                "registry_update_interval": 30,
                "size_monitoring": True
            }
        }
        json_dir = Path(__file__).parent / "prax_json"
        json_dir.mkdir(exist_ok=True)
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"Config file created: {config_path}")
        except Exception as e:
            logger.error(f"Failed to create config file: {e}")

def toggle_module(module_name, enabled):
    """Toggle module on/off"""
    registry = load_registry()
    if module_name in registry:
        registry[module_name]["enabled"] = enabled
        json_dir = Path(__file__).parent / "prax_json"
        registry_path = json_dir / REGISTRY_FILE
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        return True
    return False

# =============================================
# WATCHER CONTROL
# =============================================

_observer = None

def start_watcher():
    """Start file watcher"""
    global _observer
    if _observer and _observer.is_alive():
        return
    
    root_folder = Path(__file__).parent.parent
    _observer = Observer()
    _observer.schedule(ModuleWatcher(), str(root_folder), recursive=False)
    _observer.start()
    logger.info(f"Module watcher started")
    log_event("watcher_started", {"watch_location": str(root_folder)})

def stop_watcher():
    """Stop file watcher"""
    global _observer
    if _observer and _observer.is_alive():
        _observer.stop()
        _observer.join()
        logger.info("Module watcher stopped")

# =============================================
# LEGACY FUNCTIONS
# =============================================

def apply_global_toggles_legacy():
    """Apply toggle controls to all loaded modules (legacy version)"""
    import sys
    registry = load_registry()
    
    for module_name, config in registry.items():
        if not config.get("enabled", True):
            # Find and disable the module
            for mod_key in list(sys.modules.keys()):
                if module_name in mod_key:
                    module = sys.modules[mod_key]
                    # Replace all callable attributes with disabled versions
                    for attr_name in dir(module):
                        if not attr_name.startswith('_'):
                            try:
                                attr = getattr(module, attr_name)
                                if callable(attr) and hasattr(module, attr_name):
                                    def disabled_func(*args, **kwargs):
                                        return f"{module_name} module disabled"
                                    setattr(module, attr_name, disabled_func)
                            except:
                                pass

# =============================================
# IMPORT HOOK SYSTEM
# =============================================

import sys
import importlib.util
from importlib.abc import MetaPathFinder, Loader

class ToggleImportHook(MetaPathFinder, Loader):
    def find_spec(self, fullname, path, target=None):
        # Check if this module should be disabled
        registry = load_registry()
        module_name = fullname.split('.')[-1]  # Get last part of module name
        
        if not registry.get(module_name, {}).get("enabled", True):
            logger.info(f"Intercepting disabled module: {fullname}")
            # Log the interception event
            log_event("module_intercepted", {"module": fullname, "reason": "disabled_in_registry"})
            # Create a fake spec for disabled module
            spec = importlib.util.spec_from_loader(fullname, self)
            return spec
        return None
    
    def create_module(self, spec):
        # Create a fake module for disabled modules
        import types
        module = types.ModuleType(spec.name)
        
        # Special handling for usage_monitor
        if spec.name == 'usage_monitor':
            def get_usage_monitor():
                return type('DisabledMonitor', (), {
                    'log_usage': lambda *args, **kwargs: None
                })()
            setattr(module, 'get_usage_monitor', get_usage_monitor)
        
        # Add common function names
        for func_name in ['get_profile_prompt', 'get_system_prompt', 'add_to_context', 'get_context']:
            if not hasattr(module, func_name):
                setattr(module, func_name, lambda *args, **kwargs: f"{spec.name} module disabled")
        
        return module
    
    def exec_module(self, module):
        # Nothing to execute for fake modules
        pass

# Install the import hook
def install_import_hook():
    if not any(isinstance(finder, ToggleImportHook) for finder in sys.meta_path):
        sys.meta_path.insert(0, ToggleImportHook())
        logger.info("Import hook installed")
        log_event("import_hook_installed", {"status": "active"})

def apply_global_toggles():
    """Apply toggle controls by patching modules before they're used"""
    install_import_hook()

# =============================================
# CLI/EXECUTION
# =============================================

if __name__ == "__main__":
    # Initial scan
    registry = scan_modules()
    print(f"[Prax_on_off] Scanned {len(registry)} modules")
    
    # Start watcher
    start_watcher()
    
    try:
        print("Press Ctrl+C to stop...")
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_watcher()
        print("Prax_on_off stopped.")

# =============================================
# AUTO-START INITIALIZATION
# =============================================

# Auto-start when imported  
logger.info("prax_on_off module imported and starting")
logger.info(f"Starting prax_on_off scan from: {Path(__file__).parent.parent}")
create_config_file()  # Create config file if missing
registry = scan_modules()
logger.info(f"Scan complete - found {len(registry)} modules")
logger.info(f"Registry file location: {Path(__file__).parent / 'prax_json' / DATA_FILE}")

# Log the startup event
log_event("system_startup", {
    "scan_location": str(Path(__file__).parent.parent),
    "modules_found": len(registry),
    "registry_location": str(Path(__file__).parent / "prax_json" / DATA_FILE)
})

start_watcher()
# REMOVED: apply_global_toggles() - Don't auto-install import hooks
# Import hooks can interfere with input/output operations
# Call apply_global_toggles() manually if needed