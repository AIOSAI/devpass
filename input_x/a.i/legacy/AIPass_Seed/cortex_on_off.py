# cortex_module.py - Simple file registry for Seed modules
import os
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# === CONFIG ===
REGISTRY_FILE = "module_registry.json"

# === File watcher ===
class ModuleWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and self._is_py_file(event.src_path):
            file_path = Path(event.src_path)
            print(f"[Cortex] New module detected: {file_path.name}")
            self._add_module(file_path.stem)
    
    def on_deleted(self, event):
        if not event.is_directory and self._is_py_file(event.src_path):
            file_path = Path(event.src_path)
            print(f"[Cortex] Module deleted: {file_path.name}")
            self._remove_module(file_path.stem)
    
    def _is_py_file(self, file_path):
        return Path(file_path).suffix == ".py"
    
    def _add_module(self, module_name):
        registry = self._load_registry()
        if module_name not in registry:
            registry[module_name] = {"enabled": True}
            self._save_registry(registry)
    
    def _remove_module(self, module_name):
        registry = self._load_registry()
        if module_name in registry:
            del registry[module_name]
            self._save_registry(registry)
    
    def _load_registry(self):
        registry_path = Path(__file__).parent / REGISTRY_FILE
        if registry_path.exists():
            try:
                with open(registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _save_registry(self, registry):
        registry_path = Path(__file__).parent / REGISTRY_FILE
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

# === Registry functions ===
def scan_modules():
    """Scan root folder for .py files and build registry"""
    root_folder = Path(__file__).parent
    
    # Load existing registry to preserve toggle states
    existing_registry = load_registry()
    
    registry = {}
    # Scan root folder AND subdirectories
    for file_path in root_folder.rglob("*.py"):
        # Skip __pycache__ and other hidden folders
        if any(part.startswith('.') or part == '__pycache__' for part in file_path.parts):
            continue
        module_name = file_path.stem
        # Keep existing toggle state, default to True for new files
        registry[module_name] = existing_registry.get(module_name, {"enabled": True})
    
    registry_path = root_folder / REGISTRY_FILE
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    
    return registry

def load_registry():
    """Load module registry"""
    registry_path = Path(__file__).parent / REGISTRY_FILE
    if registry_path.exists():
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def get_enabled_modules():
    """Get list of enabled modules"""
    registry = load_registry()
    return [name for name, config in registry.items() if config.get("enabled", False)]

def toggle_module(module_name, enabled):
    """Toggle module on/off"""
    registry = load_registry()
    if module_name in registry:
        registry[module_name]["enabled"] = enabled
        registry_path = Path(__file__).parent / REGISTRY_FILE
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        return True
    return False

# === Watcher control ===
_observer = None

def start_watcher():
    """Start file watcher"""
    global _observer
    if _observer and _observer.is_alive():
        return
    
    root_folder = Path(__file__).parent
    _observer = Observer()
    _observer.schedule(ModuleWatcher(), str(root_folder), recursive=False)
    _observer.start()
    print(f"[Cortex] Module watcher started")

def stop_watcher():
    """Stop file watcher"""
    global _observer
    if _observer and _observer.is_alive():
        _observer.stop()
        _observer.join()
        print("[Cortex] Module watcher stopped")

if __name__ == "__main__":
    # Initial scan
    registry = scan_modules()
    print(f"[Cortex] Scanned {len(registry)} modules")
    
    # Start watcher
    start_watcher()
    
    try:
        print("Press Ctrl+C to stop...")
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_watcher()
        print("Cortex stopped.")

def apply_global_toggles():
    """Apply toggle controls to all loaded modules"""
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

import sys
import importlib.util
from importlib.abc import MetaPathFinder, Loader

class ToggleImportHook(MetaPathFinder, Loader):
    def find_spec(self, fullname, path, target=None):
        # Check if this module should be disabled
        registry = load_registry()
        module_name = fullname.split('.')[-1]  # Get last part of module name
        
        if not registry.get(module_name, {}).get("enabled", True):
            print(f"[DEBUG] Intercepting disabled module: {fullname}")
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
            module.get_usage_monitor = get_usage_monitor
        
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
        print("[DEBUG] Import hook installed")

def apply_global_toggles():
    """Apply toggle controls by patching modules before they're used"""
    install_import_hook()

# Auto-start when imported  
scan_modules()
start_watcher()
apply_global_toggles()
# Remove apply_global_toggles() from here - main.py will call it