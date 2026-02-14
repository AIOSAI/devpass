# =============================================
# META DATA HEADER
# Name: hot_reload_skill.py
# Date: 2025-07-26
# Version: 0.2.0
# 
# CHANGELOG:
#   - v0.2.0 (2025-07-26): Migrated to new aipass centralized import system
#   - v0.1.2 (2025-07-12): Added 2-step OpenAI config reload: 999 → "reload openai"
#   - v0.1.1 (2025-07-08): PROVEN WORKING - Truth-based hot reload in production
#   - v0.1.0 (2025-07-08): Independent hot reload skill for Seed AI
# =============================================

"""
Hot Reload Skill

PROVEN: Truth-based hot reload system for live design iteration.
Returns fresh handler list to directly update Seed's skill system.
NOW USING: New centralized aipass import system for cleaner code.

BREAKTHROUGH: No restart needed - edit files, update system, test immediately!
"""

# NEW AIPASS IMPORT PATTERN - Fixed absolute import
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import __init__ as aipass
from __init__ import logger

# Standard imports
import json
import inspect
import importlib
import importlib.util
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Union
import logging

# Test logger immediately
logger.info("hot_reload_skill imported with NEW aipass pattern - logger working")

# OLD LOGGING SYSTEM REMOVED - using global logger only

# =============================================
# SKILL CONFIGURATION
# =============================================

# Skill identity
SKILL_NAME = "hot_reload"

# Auto-detection system for JSON placement
# =============================================
# AUTO-DETECTION SYSTEM
# =============================================

def get_skill_category():
    """Determine which skill category this skill belongs to based on its location"""
    skill_path = Path(__file__)
    
    if "skills_core" in skill_path.parts:
        return "skills_core"
    elif "skills_memory" in skill_path.parts:
        return "skills_memory" 
    elif "skills_mods" in skill_path.parts:
        return "skills_mods"
    elif "skills_api" in skill_path.parts:
        return "skills_api"
    else:
        return "skills_core"  # Default fallback

def get_json_folder_name(skill_category):
    """Convert skill category to corresponding JSON folder name"""
    folder_map = {
        "skills_core": "skills_core_json",
        "skills_memory": "skills_memory_json", 
        "skills_mods": "skills_mods_json",
        "skills_api": "skills_api_json"
    }
    return folder_map.get(skill_category, "skills_core_json")

def get_caller_ai_info():
    """Auto-detect which AI is calling this skill"""
    try:
        stack = inspect.stack()
        for frame_info in stack:
            frame_path = Path(frame_info.filename)
            if "a.i" in frame_path.parts:
                ai_index = frame_path.parts.index("a.i")
                if ai_index + 1 < len(frame_path.parts):
                    ai_name = frame_path.parts[ai_index + 1]
                    ai_path = Path(*frame_path.parts[:ai_index + 2])
                    
                    # Determine skill category and JSON folder
                    skill_category = get_skill_category()
                    json_folder = get_json_folder_name(skill_category)
                    json_folder_path = ai_path / json_folder
                    
                    return ai_name, ai_path, json_folder_path
    except Exception as e:
        # Log AI detection failure but continue with fallback
        logger.info(f"[Hot Reload] AI detection failed: {e} - using fallback paths")
    return None, None, None

# Portable paths
SKILL_FILE_DIR = Path(__file__).parent
AIPASS_ROOT = SKILL_FILE_DIR.parent.parent

# JSON file paths with auto-detection
caller_ai, ai_path, json_folder = get_caller_ai_info()
if json_folder:
    SKILL_CONFIG_FILE = json_folder / f"{SKILL_NAME}_config.json"
    SKILL_DATA_FILE = json_folder / f"{SKILL_NAME}_data.json"
    SKILL_LOG_FILE = json_folder / f"{SKILL_NAME}_log.json"
else:
    SKILL_CONFIG_FILE = SKILL_FILE_DIR / f"{SKILL_NAME}_config.json"
    SKILL_DATA_FILE = SKILL_FILE_DIR / f"{SKILL_NAME}_data.json"
    SKILL_LOG_FILE = SKILL_FILE_DIR / f"{SKILL_NAME}_log.json"

# =============================================
# LOGGING
# =============================================

def log_skill_operation(operation_details, result_data=None, error=None):
    """Log hot reload operation"""
    # If result_data contains functions, make it JSON-safe
    if result_data and isinstance(result_data, dict) and "handlers" in result_data:
        safe_result_data = {
            "fresh_handlers": result_data.get("fresh_handlers", 0),
            "reloaded": result_data.get("reloaded", []),
            "new": result_data.get("new", []),
            "failed": result_data.get("failed", []),
            "purged_count": len(result_data.get("purged", []))
        }
    else:
        safe_result_data = result_data
        
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation_details,
        "success": error is None,
        "result": safe_result_data if error is None else None,
        "error": str(error) if error else None
    }
    
    try:
        if SKILL_LOG_FILE.exists():
            with open(SKILL_LOG_FILE, "r", encoding="utf-8") as f:
                log = json.load(f)
        else:
            log = []
        
        log.insert(0, entry)
        log = log[:50]  # Keep last 50 entries
        
        with open(SKILL_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)
    except Exception as e:
        logger.error(f"[Hot Reload] Logging error: {e}")

def save_skill_state(reload_results=None):
    """Save current hot reload state using 3-file structure"""
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Always ensure config file exists
        config_data = {
            "skill_name": SKILL_NAME,
            "timestamp": timestamp,
            "config": {
                "auto_reload": True,
                "watch_interval_seconds": 2,
                "max_reload_attempts": 3,
                "purge_cache_on_reload": True,
                "reload_timeout_seconds": 30,
                "exclude_patterns": ["__pycache__", "*.pyc", ".git"]
            }
        }
        SKILL_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SKILL_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
        
        # If reload_results contains functions, extract just the summary data
        if reload_results and "handlers" in reload_results:
            # Create JSON-safe version without function objects
            safe_results = {
                "fresh_handlers": reload_results.get("fresh_handlers", 0),
                "reloaded": reload_results.get("reloaded", []),
                "new": reload_results.get("new", []),
                "failed": reload_results.get("failed", []),
                "purged": reload_results.get("purged", [])
            }
        else:
            safe_results = reload_results
            
        # Save data file
        data_data = {
            "skill_name": SKILL_NAME,
            "timestamp": timestamp,
            "data": {
                "version": "0.1.1",
                "status": "operational",
                "last_reload_results": safe_results,
                "reload_statistics": {
                    "total_reloads": 0,
                    "successful_reloads": 0,
                    "failed_reloads": 0,
                    "modules_reloaded": 0,
                    "cache_purges": 0
                }
            }
        }
        
        SKILL_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SKILL_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data_data, f, indent=2)
            
    except Exception as e:
        logger.error(f"[Hot Reload] State save error: {e}")

# =============================================
# HOT RELOAD FUNCTIONALITY
# =============================================

def purge_module_from_memory(module_name: str) -> bool:
    """Forcibly remove module from memory"""
    try:
        if module_name in sys.modules:
            del sys.modules[module_name]
            return True
        return False
    except Exception:
        return False

def get_all_existing_files() -> Dict[str, Path]:
    """Get all Python files that currently exist in Skills folders"""
    existing_files = {}
    
    skills_folders = [
        AIPASS_ROOT / "skills" / "skills_core",
        AIPASS_ROOT / "skills" / "skills_memory",
        AIPASS_ROOT / "skills" / "skills_mods",
        AIPASS_ROOT / "skills" / "skills_api",
    ]
    
    for folder_path in skills_folders:
        if not folder_path.exists():
            continue
            
        for file_path in folder_path.rglob("*.py"):
            if '__pycache__' in str(file_path) or 'BROKEN' in file_path.name.upper():
                continue
            
            module_name = file_path.stem
            existing_files[module_name] = file_path
    
    return existing_files

def purge_deleted_modules() -> List[str]:
    """Remove modules from memory that no longer exist on disk"""
    existing_files = get_all_existing_files()
    existing_module_names = set(existing_files.keys())
    
    # Find modules in memory that no longer exist on disk
    loaded_modules = [name for name in sys.modules.keys() 
                     if not name.startswith('_') and '.' not in name]
    
    purged_modules = []
    for module_name in loaded_modules:
        # Skip built-in and system modules
        if module_name in ['sys', 'os', 'json', 'pathlib', 'datetime', 'typing', 
                          'importlib', 'inspect', 'hot_reload']:
            continue
            
        # If module is loaded but file doesn't exist, purge it
        if module_name not in existing_module_names:
            if purge_module_from_memory(module_name):
                purged_modules.append(module_name)
    
    return purged_modules

def reload_skill_module(module_name: str, file_path: Path) -> bool:
    """Reload a specific skill module with truth-based cleanup"""
    try:
        # First, purge any existing version
        purge_module_from_memory(module_name)
        
        # Import fresh from disk
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            logger.info(f"[Hot Reload Debug] Successfully reloaded {module_name}")
            return True
        return False
    except Exception as e:
        # If reload fails, ensure broken module is purged
        logger.info(f"[Hot Reload Debug] Failed to reload {module_name}: {e}")
        purge_module_from_memory(module_name)
        return False

def discover_fresh_skills() -> List:
    """Discover and reload all skills, return fresh handler list"""
    results = {
        "handlers": [],
        "reloaded": [],
        "new": [],
        "failed": [],
        "purged": []
    }
    
    # Step 1: Purge deleted modules
    purged_modules = purge_deleted_modules()
    results["purged"] = purged_modules
    
    # Step 2: Get current files and reload them
    existing_files = get_all_existing_files()
    
    for module_name, file_path in existing_files.items():
        # Check if this skill is enabled in Prax registry - same as seed discovery
        from prax.prax_on_off import load_registry
        registry = load_registry()
        skill_enabled = registry.get(module_name, {}).get("enabled", True)
        
        if not skill_enabled:
            logger.info(f"  [-] {module_name} - disabled in Prax registry (skipped)")
            continue
        
        was_loaded = module_name in sys.modules
        
        if reload_skill_module(module_name, file_path):
            # Get the reloaded module
            module = sys.modules[module_name]
            
            # Check if it has handle_command function
            if hasattr(module, 'handle_command'):
                results["handlers"].append(module.handle_command)
                
                if was_loaded:
                    results["reloaded"].append(module_name)
                else:
                    results["new"].append(module_name)
            else:
                results["failed"].append(f"{module_name} (no handle_command)")
        else:
            results["failed"].append(module_name)
    
    # Log results
    logger.info(f"[Hot Reload] System reloaded:")
    logger.info(f"  - Fresh handlers: {len(results['handlers'])}")
    logger.info(f"  - Reloaded: {len(results['reloaded'])}")
    logger.info(f"  - New: {len(results['new'])}")
    logger.info(f"  - Failed: {len(results['failed'])}")
    logger.info(f"  - Purged: {len(results['purged'])}")
    
    if results['purged']:
        logger.info(f"  Purged: {', '.join(results['purged'])}")
    if results['reloaded']:
        logger.info(f"  Reloaded: {', '.join(results['reloaded'])}")
    if results['new']:
        logger.info(f"  New: {', '.join(results['new'])}")
    if results['failed']:
        logger.info(f"  Failed: {', '.join(results['failed'])}")
    
    # Log the reload operation
    log_skill_operation("System reload", results)
    
    # Save current state
    save_skill_state(results)
    
    return results["handlers"]

# =============================================
# SKILL INTERFACE FUNCTIONS
# =============================================

def get_prompt():
    """Return prompt text for LLM integration"""
    return """Hot Reload Skill:
- Live hot reloading without restart
- Commands: 'update system', 'reload system'
- Returns fresh skill handlers to replace current ones
"""

def get_skill_context():
    """Return current skill context"""
    return "Hot Reload: Ready for system updates"

def handle_command(user_input: str) -> Union[bool, List]:
    """Handle hot reload commands - returns fresh handlers list or False"""
    user_input = user_input.strip().lower()
    
    # System reload commands
    if user_input in ["999", "update system", "reload system", "refresh system"]:
        logger.info(f"Hot reload command received: {user_input}")
        logger.info("Reloading entire system...")
        
        # Return fresh skill handlers list (this is the key!)
        fresh_handlers = discover_fresh_skills()
        
        # Refresh API usage monitor cache to pick up skill changes
        try:
            from prax.prax_api_usage_monitor import get_usage_monitor
            monitor = get_usage_monitor()
            if monitor and hasattr(monitor, 'refresh_skill_cache'):
                monitor.refresh_skill_cache()
                logger.info("[Hot Reload] API usage monitor cache refreshed")
        except Exception as e:
            logger.warning(f"[Hot Reload] Could not refresh API monitor cache: {e}")
        
        print(f"[Hot Reload] System refreshed: {len(fresh_handlers)} skills reloaded")
        
        logger.info(f"Returning {len(fresh_handlers)} fresh handlers to Seed")
        
        return fresh_handlers  # <- This replaces Seed's skill_handlers
    
    # OpenAI config reload command
    elif user_input in ["reload openai", "refresh openai", "openai reload"]:
        logger.info(f"OpenAI config reload requested")
        
        # Force reload OpenAI config
        try:
            # Import openai_skill to trigger config reload
            if 'openai_skill' in sys.modules:
                openai_module = sys.modules['openai_skill']
                if hasattr(openai_module, 'load_config'):
                    openai_module.load_config()
                    print("[Hot Reload] ✓ OpenAI config reloaded - model settings updated")
                    logger.info("OpenAI config successfully reloaded")
                else:
                    print("[Hot Reload] ⚠ OpenAI skill found but no load_config function")
            else:
                print("[Hot Reload] ⚠ OpenAI skill not found")
        except Exception as e:
            print(f"[Hot Reload] ✗ OpenAI config reload failed: {e}")
            logger.error(f"OpenAI config reload failed: {e}")
        
        return False  # Don't return handlers, just reload config
    
    return False

def get_skill_info():
    """Return skill information"""
    return {
        "name": SKILL_NAME,
        "version": "0.1.2",
        "description": "Independent hot reload system for Seed AI with OpenAI config refresh",
        "commands": ["999", "update system", "reload system", "refresh system", "reload openai", "refresh openai", "openai reload"]
    }

# =============================================
# INITIALIZATION
# =============================================

# Initialize JSON files
save_skill_state()
log_skill_operation("Hot reload skill initialized")

logger.info(f"[Hot Reload] Skill loaded - JSON files initialized")

# =============================================
# TESTING (when run directly)
# =============================================

if __name__ == "__main__":
    """Test the hot reload skill when run directly"""
    print("\n=== Testing Hot Reload Skill ===\n")
    
    # Test system reload
    print("1. Testing 'update system':")
    result = handle_command("update system")
    print(f"   Returned: {type(result)} with {len(result) if isinstance(result, list) else 'N/A'} handlers\n")
    
    # Test unknown command
    print("2. Testing unknown command:")
    result = handle_command("hello world")
    print(f"   Returned: {result}\n")
    
    # Show skill info
    print("3. Skill info:")
    info = get_skill_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    print("\n=== Test Complete ===")
    print("Skill ready for Seed auto-discovery")
