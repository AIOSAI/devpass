#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: prax_registry.py - Prax Module Registry Management
# Date: 2025-10-25
# Version: 1.0.0
# Category: prax
#
# CHANGELOG:
#   - v1.0.0 (2025-10-25): Extracted from prax_logger.py - module registry management
# =============================================

"""
Prax Module Registry Management

Manages the system-wide module discovery registry (prax_registry.json).
Provides load/save functions for module states and statistics.
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
    ECOSYSTEM_ROOT
)

# Standard imports
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, Any

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "prax_registry"
MODULE_VERSION = "1.0.0"

# 3-File JSON Pattern for this module
CONFIG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = PRAX_JSON_DIR / f"{MODULE_NAME}_log.json"

# System Registry File (4th file exception - system-wide module discovery)
REGISTRY_FILE = PRAX_JSON_DIR / "prax_registry.json"

# =============================================
# REGISTRY MANAGEMENT FUNCTIONS
# =============================================

def save_module_registry(modules: Dict[str, Dict[str, Any]]):
    """Save module registry to prax_registry.json (system registry)"""
    registry_structure = {
        "registry_version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modules": modules,
        "statistics": {
            "total_modules": len(modules),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "scan_location": str(ECOSYSTEM_ROOT)
        }
    }

    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry_structure, f, indent=2, ensure_ascii=False)

    # Log operation
    log_operation("save_registry", True, f"Saved {len(modules)} modules to registry")

def load_module_registry() -> Dict[str, Dict[str, Any]]:
    """Load module registry from prax_registry.json (system registry)"""
    if not REGISTRY_FILE.exists():
        return {}

    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            modules = data.get('modules', {})
            log_operation("load_registry", True, f"Loaded {len(modules)} modules from registry")
            return modules
    except Exception as e:
        error_msg = f"Error loading module registry: {e}"
        log_operation("load_registry", False, error_msg)
        print(f"[{MODULE_NAME}] {error_msg}")
        return {}

def get_registry_statistics() -> Dict[str, Any]:
    """Get statistics about the module registry"""
    if not REGISTRY_FILE.exists():
        return {
            "total_modules": 0,
            "registry_exists": False
        }

    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('statistics', {
                "total_modules": len(data.get('modules', {}))
            })
    except Exception as e:
        print(f"[{MODULE_NAME}] Error getting statistics: {e}")
        return {"total_modules": 0, "error": str(e)}

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
            "registry_file": str(REGISTRY_FILE),
            "auto_save": True,
            "statistics_enabled": True
        }
    }

def create_default_data() -> Dict[str, Any]:
    """Create default data structure"""
    return {
        "module_name": MODULE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime_stats": {
            "last_save": None,
            "last_load": None,
            "total_saves": 0,
            "total_loads": 0
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
    """Run module test - verify registry loading and operations"""
    print(f"{MODULE_NAME} v{MODULE_VERSION}")
    print("=" * 60)

    # Ensure JSON files exist
    ensure_json_files_exist()

    # Test registry loading
    print(f"\nRegistry file: {REGISTRY_FILE}")
    print(f"Registry exists: {REGISTRY_FILE.exists()}")

    modules = load_module_registry()
    print(f"Modules in registry: {len(modules)}")

    # Get statistics
    stats = get_registry_statistics()
    print(f"\nRegistry statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test saving (if registry exists, save it back)
    if modules:
        print(f"\nTesting registry save...")
        save_module_registry(modules)
        print(f"✓ Registry saved successfully")

    # Log this operation
    log_operation("module_test", True, "Registry module tested successfully")

    print("\n" + "=" * 60)
    print("✓ prax_registry.py initialized successfully")
    print(f"✓ 3-file JSON pattern created in {PRAX_JSON_DIR}")
    print(f"✓ Manages system registry: {REGISTRY_FILE}")
    return 0

def handle_stats():
    """Display registry statistics"""
    stats = get_registry_statistics()
    print(f"{MODULE_NAME} Statistics")
    print("=" * 60)
    for key, value in stats.items():
        print(f"{key:30} {value}")
    return 0

def handle_list(args):
    """List all modules in registry"""
    modules = load_module_registry()
    print(f"{MODULE_NAME} - Module List")
    print("=" * 60)
    print(f"Total modules: {len(modules)}\n")

    if not modules:
        print("No modules in registry. Run prax_logger.py init to discover modules.")
        return 1

    # Sort by name
    sorted_modules = sorted(modules.items())

    for i, (name, info) in enumerate(sorted_modules, 1):
        if args.verbose:
            print(f"{i}. {name}")
            print(f"   Path: {info.get('relative_path', 'N/A')}")
            print(f"   Size: {info.get('size', 0):,} bytes")
            print(f"   Modified: {info.get('modified_time', 'N/A')}")
            print()
        else:
            print(f"{i:3}. {name:40} {info.get('relative_path', '')}")

    return 0

def handle_show(args):
    """Show details for a specific module"""
    modules = load_module_registry()

    if args.module not in modules:
        print(f"Module '{args.module}' not found in registry")
        return 1

    info = modules[args.module]
    print(f"Module: {args.module}")
    print("=" * 60)
    for key, value in info.items():
        print(f"{key:20} {value}")

    return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Prax Registry Module - Manages system-wide module discovery registry',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: test, stats, list, show

  test  - Run module test and verify registry operations
  stats - Display registry statistics
  list  - List all modules in registry
  show  - Show details for a specific module

EXAMPLES:
  python3 prax_registry.py test
  python3 prax_registry.py stats
  python3 prax_registry.py list
  python3 prax_registry.py list --verbose
  python3 prax_registry.py show prax_logger
        """
    )

    parser.add_argument('command',
                       choices=['test', 'stats', 'list', 'show'],
                       help='Command to execute')

    parser.add_argument('module', nargs='?',
                       help='Module name (for show command)')

    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show verbose output')

    args = parser.parse_args()

    # Route to command handlers
    if args.command == 'test':
        return handle_test()
    elif args.command == 'stats':
        return handle_stats()
    elif args.command == 'list':
        return handle_list(args)
    elif args.command == 'show':
        if not args.module:
            print("Error: 'show' command requires a module name")
            return 1
        return handle_show(args)

if __name__ == "__main__":
    import sys
    sys.exit(main() or 0)
