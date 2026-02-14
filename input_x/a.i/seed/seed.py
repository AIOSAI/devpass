/home/aipass/input_x/a.i/seed# =============================================
# META DATA HEADER
# Name: seed.py - Seed AI System Orchestrator
# Date: 2025-07-08
# Version: 3.1.0
# 
# CHANGELOG (Max 5 entries - remove oldest when adding new):
#   - v3.1.0 (2025-07-08): BREAKTHROUGH - Truth-based hot reload working! Live design iteration achieved
#   - v3.0.0 (2025-07-08): Streamlined - removed redundant OpenAI code (openai_skill.py handles this)
#   - v2.0.0 (2025-07-05): Created from main_module_template.py for Seed AI
# =============================================

"""
Seed AI - Skill-Based System Orchestrator

A modular AI assistant that auto-discovers and loads skill modules,
routes commands to appropriate skills, and maintains conversation context.
"""

import sys
import os
import json
import importlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable
import logging

# Import global system logger for new logging
sys.path.append(str(Path(__file__).parent.parent.parent))
from prax.prax_logger import system_logger as logger
from prax.prax_on_off import load_registry

# Test global logger
logger.info("seed.py imported and global logger working")
logger.info("Logger import successful, info() called")

# OLD LOGGING SYSTEM REMOVED - using global logger only
# Always log to the dedicated skill log file in the JSON folder
# log_path = Path(__file__).parent / "seed.log"
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# if logger.hasHandlers():
#     logger.handlers.clear()
# file_handler = logging.FileHandler(log_path, encoding='utf-8')
# file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
# logger.addHandler(file_handler)


# Skills discovered dynamically - no hardcoded imports needed
# Auto-discovery will find all skills from main Skills folders

# Check if seed is enabled
# Use 'seed' directly since __name__ is '__main__' when run directly
ENABLED = load_registry().get("seed", {}).get("enabled", True)

if not ENABLED:
    # Module disabled - don't execute
    raise ImportError("seed disabled in Prax registry")

# =============================================
# SYSTEM CONFIGURATION
# =============================================

# System identity
SYSTEM_NAME = "Seed"
SYSTEM_VERSION = "3.1.0"
SYSTEM_DISPLAY_NAME = "Seed AI - Skill-Based System"

# Portable paths - works from any location
MAIN_FILE_DIR = Path(__file__).parent
CUSTOM_SKILLS_FOLDER = MAIN_FILE_DIR / "custom_skills"

# System files
SYSTEM_LOG_FILE = MAIN_FILE_DIR / "seed_log.json"
SYSTEM_STATE_FILE = MAIN_FILE_DIR / "seed_state.json"

# No core dependencies needed - skills handle their own dependencies

# =============================================
# LOGGING UTILITIES
# =============================================

def log_system_operation(operation_details, result_data=None, error=None, component="main"):
    """Log system operation with timestamp and details"""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "operation": operation_details,
        "success": error is None,
        "result": result_data if error is None else None,
        "error": str(error) if error else None
    }
    
    try:
        if SYSTEM_LOG_FILE.exists() and SYSTEM_LOG_FILE.stat().st_size > 0:
            with open(SYSTEM_LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    log = json.loads(content)
                else:
                    log = []
        else:
            log = []
        
        log.insert(0, entry)  # Newest first
        log = log[:100]  # Keep more entries for system log
        
        with open(SYSTEM_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)
    except Exception as e:
        # CRITICAL: Do not log this error as it creates infinite loop!
        # Just silently create a new log file
        try:
            with open(SYSTEM_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump([entry], f, indent=2)
        except:
            pass  # If we can't even create the file, give up silently

def clear_system_log():
    """Clear the system log file"""
    try:
        with open(SYSTEM_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
    except Exception as e:
        # Don't log this error - could cause infinite loop
        pass

# =============================================
# SYSTEM STATE MANAGEMENT
# =============================================

system_state = {
    'loaded_skills': [],
    'skill_handlers': [],
    'session_start': datetime.now(timezone.utc).isoformat(),
    'commands_processed': 0,
    'errors_encountered': 0
}

def save_system_state():
    """Save current system state"""
    try:
        state_data = {
            "system_name": SYSTEM_NAME,
            "version": SYSTEM_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": system_state,
            "session_active": True
        }
        
        with open(SYSTEM_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)
            
    except Exception as e:
        logger.error(f"[System] State save error: {e}")

def load_system_state():
    """Load system state from file"""
    try:
        if SYSTEM_STATE_FILE.exists():
            with open(SYSTEM_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"[System] State load error: {e}")
        return None

def clear_system_state():
    """Clear system state (called on exit)"""
    try:
        if SYSTEM_STATE_FILE.exists():
            SYSTEM_STATE_FILE.unlink()
    except Exception as e:
        logger.error(f"[System] State clear error: {e}")

# =============================================
# CORE SYSTEM INITIALIZATION
# =============================================

def initialize_core_systems():
    """Initialize core systems - minimal setup only"""
    logger.info("[*] Initializing core systems...")
    
    # Log initialization
    log_system_operation("System initialization", {"status": "initialized"})
    
    return True

# =============================================
# SKILL DISCOVERY SYSTEM
# =============================================

def discover_skills() -> List[Callable]:
    """Auto-discover skills from all skills folders and custom_skills"""
    all_skill_handlers = []
    loaded_skills = []
    
    logger.info("\n[*] Discovering skills...")
    
    # Main Skills folders to scan
    main_skills_root = Path(__file__).parent.parent.parent / "skills"
    skills_folders = [
        ("skills_core", main_skills_root / "skills_core"),
        ("skills_memory", main_skills_root / "skills_memory"), 
        ("skills_mods", main_skills_root / "skills_mods"),
        ("skills_api", main_skills_root / "skills_api"),
        ("custom_skills", CUSTOM_SKILLS_FOLDER)
    ]
    total_skill_count = 0
    
    for folder_name, folder_path in skills_folders:
        if not folder_path.exists():
            logger.warning(f"[!] {folder_name} folder not found: {folder_path}")
            if folder_name == "custom_skills":
                logger.info("   Creating custom_skills folder...")
                folder_path.mkdir(exist_ok=True)
            continue
        
        logger.info(f"\n[>] Scanning {folder_name}...")
        
        # Add folder to Python path for imports
        sys.path.insert(0, str(folder_path))
        
        folder_skill_count = 0
        for file_path in folder_path.rglob("*.py"):
            # DEBUG: Log every file being processed
            logger.info(f"   [DEBUG] Processing file: {file_path.name}")
            
            # Skip hidden folders, cache, and broken files
            if any(part.startswith('.') or part == '__pycache__' for part in file_path.parts):
                logger.info(f"   [DEBUG] Skipping {file_path.name} - hidden/cache")
                continue
            if 'BROKEN' in file_path.name.upper():
                logger.info(f"   [DEBUG] Skipping {file_path.name} - broken")
                continue
            
            folder_skill_count += 1
            total_skill_count += 1
            
            try:
                # Build module name from filename (no folder prefix for main skills)
                if folder_name == "custom_skills":
                    # Custom skills use full path
                    relative_path = file_path.relative_to(folder_path)
                    # Convert path parts to module notation (cross-platform)
                    module_path = ".".join(relative_path.with_suffix("").parts)
                    module_name = f"custom_skills.{module_path}"
                else:
                    # Main skills use just the filename
                    module_name = file_path.stem
                
                # DEBUG: Show what we're about to check
                logger.info(f"   [DEBUG] About to check module: {module_name}")
                
                # Check if this skill is enabled in Prax registry
                registry = load_registry()
                skill_enabled = registry.get(module_name, {}).get("enabled", True)
                
                # DEBUG: Log registry check details
                logger.info(f"   [DEBUG] Checking {module_name}: enabled={skill_enabled}")
                if module_name in registry:
                    logger.info(f"   [DEBUG] Registry entry: {registry[module_name]}")
                else:
                    logger.info(f"   [DEBUG] Module {module_name} not found in registry, defaulting to enabled")
                
                if not skill_enabled:
                    logger.info(f"   [-] {module_name} - disabled in Prax registry")
                    continue
                
                # Import the skill module
                module = importlib.import_module(module_name)
                
                # Check for required handler function
                if hasattr(module, 'handle_command'):
                    all_skill_handlers.append(module.handle_command)
                    skill_display_name = f"{folder_name}/{module_name}" if folder_name == "custom_skills" else module_name
                    loaded_skills.append(skill_display_name)
                    logger.info(f"   [+] {skill_display_name}")
                    
                    # Track in system state
                    system_state['loaded_skills'].append({
                        'name': skill_display_name,
                        'category': folder_name,
                        'path': str(file_path),
                        'has_info': hasattr(module, 'get_skill_info')
                    })
                else:
                    logger.warning(f"   [!] {file_path.name} - missing handle_command() function")
                    
            except Exception as e:
                logger.error(f"   [-] {file_path.name} - import error: {e}")
                log_system_operation(f"skill load failed: {file_path.name}", error=e)
        
        if folder_skill_count == 0:
            logger.info(f"   [0] No skills found in {folder_name}")
        else:
            logger.info(f"   [=] {folder_skill_count} skills processed in {folder_name}")
    
    save_system_state()
    
    # Log discovery results
    log_system_operation(
        "Skill discovery completed",
        {
            "total_files_scanned": total_skill_count,
            "skills_loaded": len(all_skill_handlers),
            "folders_scanned": [name for name, path in skills_folders if path.exists()],
            "skill_names": loaded_skills
        }
    )
    
    logger.info(f"\n[+] Skills discovery complete: {len(all_skill_handlers)} total skills loaded")
    if loaded_skills:
        logger.info(f"   Loaded skills: {', '.join(loaded_skills)}")
    else:
        logger.warning("   [!] No skills loaded - check skills folders")
    
    return all_skill_handlers

# =============================================
# MAIN CHAT LOOP
# =============================================

def main():
    """Main chat loop - orchestrates the skill-based system"""
    print(f"\n{'=' * 60}")
    print(f"{SYSTEM_DISPLAY_NAME} v{SYSTEM_VERSION}")
    print(f"{'=' * 60}")
    print("Hi! Ready to help. Type 'exit', 'quit', or 'bye' to end session.\n")
    
    # Initialize core systems
    initialize_core_systems()
    
    # Discover and load skills
    skill_handlers = discover_skills()
    logger.info(f"Seed system initialized with {len(skill_handlers)} skill handlers")
    
    # Main conversation loop
    while True:
        try:
            try:
                user_input = input("\nYou: ").strip()
            except EOFError:
                logger.info(f"\n[{SYSTEM_NAME}] Input stream closed - ending session")
                break
                
            logger.info(f"User input: {user_input}")
            
            # Handle exit commands - with memory reset
            if user_input.lower() in {"exit", "quit", "bye"}:
                # Try to clear live chat context memory (if available)
                try:
                    # Find live_chat_context_skill among loaded skills and clear memory
                    memory_cleared = False
                    for handler in skill_handlers:
                        try:
                            if handler("clear memory"):
                                memory_cleared = True
                                break
                        except:
                            pass
                    
                    if memory_cleared:
                        print("[Memory] Chat context cleared for next session")
                except:
                    pass  # If no memory skill available, continue anyway
                
                print(f"\n[{SYSTEM_NAME}] Session ended. Goodbye!")
                break
            
            # Skip empty input
            if not user_input:
                print("(Empty input - type something or 'exit' to quit)")
                continue
            
            # Try to route to skills first
            handled_by_skill = False
            for handler in skill_handlers:
                try:
                    result = handler(user_input)
                    if result:
                        # Check if hot reload returned fresh handlers
                        if isinstance(result, list):
                            logger.info(f"[{SYSTEM_NAME}] Hot reload complete - {len(result)} handlers loaded")
                            skill_handlers = result  # Replace current handlers
                            handled_by_skill = True
                            system_state['commands_processed'] += 1
                            break
                        else:
                            handled_by_skill = True
                            system_state['commands_processed'] += 1
                            break
                except Exception as e:
                    logger.error(f"⚠️  Skill handler error: {e}")
                    system_state['errors_encountered'] += 1
            
            # If no skill handled it, check for default chat handlers
            if not handled_by_skill:
                for handler in skill_handlers:
                    try:
                        # Try with a generic chat prefix - skills can decide if they handle this
                        if handler(f"chat {user_input}"):
                            handled_by_skill = True
                            system_state['commands_processed'] += 1
                            break
                    except:
                        pass
                
                # Final fallback - try to find OpenAI skill among loaded skills
                if not handled_by_skill:
                    try:
                        # Find openai_skill among the loaded skills
                        openai_handler = None
                        for handler in skill_handlers:
                            try:
                                # Test if this handler has get_response method (openai_skill signature)
                                if hasattr(handler.__self__, 'get_response'):
                                    openai_handler = handler.__self__
                                    break
                            except:
                                pass
                        
                        if openai_handler:
                            messages = [{"role": "user", "content": user_input}]
                            response = openai_handler.get_response(messages)
                            # Print response to console so user can see it
                            print(f"{SYSTEM_NAME}: {response}")
                            logger.info(f"{SYSTEM_NAME}: {response}")
                            system_state['commands_processed'] += 1
                        else:
                            # No OpenAI skill found - check if it's disabled in Prax
                            disabled_msg = f"{SYSTEM_NAME}: OpenAI skill disabled in Prax registry. Enable it with Prax on/off system."
                            print(disabled_msg)
                            logger.info(disabled_msg)
                            system_state['commands_processed'] += 1
                    except Exception as e:
                        # If everything fails, fall back to echo
                        logger.error(f"{SYSTEM_NAME}: I received: {user_input} (AI unavailable: {e})")
                        system_state['commands_processed'] += 1
            
        except KeyboardInterrupt:
            logger.info(f"\n[{SYSTEM_NAME}] Session interrupted by user")
            break
        except Exception as e:
            logger.error(f"[{SYSTEM_NAME}] Unexpected error: {e}")
            logger.error(f"[{SYSTEM_NAME}] Error type: {type(e).__name__}")
            log_system_operation("Main loop error", error=f"{type(e).__name__}: {e}")
            system_state['errors_encountered'] += 1
            
            # If it's an EOF error, break instead of continuing
            if isinstance(e, EOFError):
                logger.info(f"\n[{SYSTEM_NAME}] EOF detected - ending session")
                break
            
            logger.info("Continuing...")

# =============================================
# ENTRY POINT
# =============================================

if __name__ == "__main__":
    """Entry point when running seed.py directly"""
    try:
        main()
    except Exception as e:
        logger.error(f"\n[FATAL] System startup error: {e}")
        log_system_operation("Fatal startup error", error=e)
        sys.exit(1)
