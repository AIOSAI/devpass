# =============================================
# META DATA HEADER
# Name: open_terminal_skill.py  
# Date: 2025-07-26
# Version: 0.2.0
# 
# CHANGELOG:
#   - v0.2.0 (2025-07-26): Migrated to new aipass centralized import system
#   - v0.1.0 (2025-07-22): Initial terminal window management skill
# =============================================

"""
Open Terminal Skill

Opens and tracks PowerShell terminal windows.
Provides awareness of terminal state for Seed AI.
NOW USING: New centralized aipass import system for cleaner code.
"""

# NEW AIPASS IMPORT PATTERN - Fixed absolute import
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import __init__ as aipass
from __init__ import logger

# Standard imports
import os
import json
import inspect
import subprocess
import psutil
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Test logger immediately  
logger.info("open_terminal_skill imported with NEW aipass pattern - logger working")

# =============================================
# AUTO-DETECTION SYSTEM
# =============================================

def get_skill_category():
    """
    Determine which skill category this skill belongs to based on its location.
    
    Returns:
        str: Skill category name (skills_core, skills_memory, skills_mods, skills_api)
    """
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
        # Default to skills_mods since that's where this will be deployed
        return "skills_mods"

def get_json_folder_name(skill_category):
    """
    Convert skill category to corresponding JSON folder name.
    
    Args:
        skill_category: skills_core, skills_memory, skills_mods, or skills_api
        
    Returns:
        str: Corresponding JSON folder name
    """
    folder_map = {
        "skills_core": "skills_core_json",
        "skills_memory": "memory_json", 
        "skills_mods": "skills_mods_json",
        "skills_api": "skills_api_json"
    }
    
    return folder_map.get(skill_category, "skills_mods_json")

def get_caller_ai_info():
    """
    Auto-detect which AI is calling this skill and determine JSON storage path.
    
    Returns:
        tuple: (ai_name, ai_path, json_folder_path) or (None, None, None) if detection fails
    """
    try:
        # Get the call stack
        stack = inspect.stack()
        
        # Look through the stack to find the AI caller
        for frame_info in stack:
            frame_path = Path(frame_info.filename)
            
            # Check if this frame is from an AI folder
            if "a.i" in frame_path.parts:
                # Find A.I folder index
                ai_index = frame_path.parts.index("a.i")
                if ai_index + 1 < len(frame_path.parts):
                    # Get AI name (folder after A.I)
                    ai_name = frame_path.parts[ai_index + 1]
                    
                    # Build AI base path
                    ai_path = Path(*frame_path.parts[:ai_index + 2])
                    
                    # Determine skill category and JSON folder
                    skill_category = get_skill_category()
                    json_folder = get_json_folder_name(skill_category)
                    json_folder_path = ai_path / json_folder
                    
                    return ai_name, ai_path, json_folder_path
        
        # No AI found in stack - FAIL HARD (no fallbacks)
        raise ImportError("Open terminal skill must be called from within AIPass ecosystem")
        
    except Exception as e:
        logger.error(f"Error detecting caller: {e}")
        raise ImportError(f"Failed to detect AI caller: {e}")

def get_dynamic_skill_paths():
    """
    Get dynamic paths for skill JSON files based on caller detection.
    
    Returns:
        tuple: (config_file_path, data_file_path, log_file_path) using 3-file structure
    """
    ai_name, ai_path, json_folder_path = get_caller_ai_info()
    
    if json_folder_path:
        # Ensure the JSON folder exists
        json_folder_path.mkdir(parents=True, exist_ok=True)
        
        # Return file paths within the JSON folder
        config_file = json_folder_path / "open_terminal_skill_config.json"
        data_file = json_folder_path / "open_terminal_skill_data.json"
        log_file = json_folder_path / "open_terminal_skill_log.json"
        
        return config_file, data_file, log_file
    
    # Fallback to skill folder (shouldn't happen with proper detection)
    skill_folder = Path(__file__).parent
    config_file = skill_folder / "open_terminal_skill_config.json"
    data_file = skill_folder / "open_terminal_skill_data.json"
    log_file = skill_folder / "open_terminal_skill_log.json"
    
    return config_file, data_file, log_file

# =============================================
# GLOBAL VARIABLES
# =============================================

# Terminal configuration
TERMINAL_COMMAND = "powershell.exe"
TERMINAL_ARGS = ["-NoExit"]  # Keep terminal open

# Global state
SKILL_CONFIG_FILE = None
SKILL_DATA_FILE = None
SKILL_LOG_FILE = None
terminal_config = {
    "tracked_terminals": {},
    "last_session_id": None,
    "settings": {
        "auto_track": True,
        "terminal_type": "powershell"
    }
}

def ensure_skill_paths():
    """Ensure skill file paths are initialized"""
    global SKILL_CONFIG_FILE, SKILL_DATA_FILE, SKILL_LOG_FILE
    
    if SKILL_CONFIG_FILE is None or SKILL_DATA_FILE is None or SKILL_LOG_FILE is None:
        SKILL_CONFIG_FILE, SKILL_DATA_FILE, SKILL_LOG_FILE = get_dynamic_skill_paths()
        logger.info(f"[Open Terminal] Config: {SKILL_CONFIG_FILE}")
        logger.info(f"[Open Terminal] Data: {SKILL_DATA_FILE}")
        logger.info(f"[Open Terminal] Log: {SKILL_LOG_FILE}")

# =============================================
# CONFIGURATION MANAGEMENT
# =============================================

def load_config():
    """Load terminal configuration from JSON file"""
    global terminal_config
    
    ensure_skill_paths()
    
    try:
        if SKILL_DATA_FILE and SKILL_DATA_FILE.exists():
            with open(SKILL_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config_data = data.get("config", {})
                
                # Update configuration
                terminal_config.update(config_data)
                
                logger.info(f"[Open Terminal] Config loaded: {len(terminal_config.get('tracked_terminals', {}))} terminals tracked")
                return True
        else:
            logger.info(f"[Open Terminal] No config file found, using defaults")
            return create_default_config()
            
    except Exception as e:
        logger.error(f"[Open Terminal] Error loading config: {e}")
        return create_default_config()

def create_default_config():
    """Create default configuration"""
    global terminal_config
    
    terminal_config = {
        "tracked_terminals": {},
        "last_session_id": None,
        "settings": {
            "auto_track": True,
            "terminal_type": "powershell"
        }
    }
    
    return save_config()

def save_config():
    """Save terminal configuration to JSON file"""
    ensure_skill_paths()
    
    try:
        if SKILL_DATA_FILE:
            # Prepare data for JSON (remove non-serializable objects)
            save_data = {
                "config": {
                    "tracked_terminals": {},
                    "last_session_id": terminal_config.get("last_session_id"),
                    "settings": terminal_config.get("settings", {})
                },
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "skill_info": {
                    "name": "open_terminal",
                    "version": "0.1.0"
                }
            }
            
            # Only save serializable terminal data
            for session_id, terminal_data in terminal_config.get("tracked_terminals", {}).items():
                save_data["config"]["tracked_terminals"][session_id] = {
                    "pid": terminal_data.get("pid"),
                    "status": terminal_data.get("status"),
                    "start_time": terminal_data.get("start_time")
                    # Don't save 'process' object - not serializable
                }
            
            with open(SKILL_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"[Open Terminal] Data saved to {SKILL_DATA_FILE}")
            return True
            
    except Exception as e:
        logger.error(f"[Open Terminal] Error saving config: {e}")
        return False

# =============================================
# CORE TERMINAL FUNCTIONS
# =============================================

def open_terminal(session_name: Optional[str] = None) -> Dict:
    """
    Opens a new PowerShell terminal window and tracks it.
    
    Args:
        session_name: Optional name for this terminal session
        
    Returns:
        Dict with session info and status
    """
    try:
        load_config()  # Ensure config is loaded
        
        # Generate session ID
        session_id = session_name or f"terminal_{int(time.time())}"
        
        # Launch PowerShell in new window
        process = subprocess.Popen(
            [TERMINAL_COMMAND] + TERMINAL_ARGS,
            creationflags=subprocess.CREATE_NEW_CONSOLE  # New window
        )
        
        # Track the terminal
        terminal_config["tracked_terminals"][session_id] = {
            "pid": process.pid,
            "status": "open",
            "start_time": time.time(),
            "process": process  # Keep process object for runtime (won't be saved to JSON)
        }
        
        terminal_config["last_session_id"] = session_id
        
        # Give it a moment to fully open
        time.sleep(0.5)
        
        # Save updated config
        save_config()
        
        logger.info(f"[Open Terminal] Opened PowerShell: {session_id} (PID: {process.pid})")
        
        return {
            "success": True,
            "session_id": session_id,
            "pid": process.pid,
            "action": "opened_terminal"
        }
        
    except Exception as e:
        logger.error(f"[Open Terminal] Failed to open terminal: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "action": "failed_to_open"
        }

def check_terminal_status(session_id: str) -> Dict:
    """Check if a specific terminal is still open."""
    if session_id not in terminal_config["tracked_terminals"]:
        return {
            "exists": False,
            "session_id": session_id,
            "status": "not_found"
        }
    
    terminal_info = terminal_config["tracked_terminals"][session_id]
    pid = terminal_info["pid"]
    
    try:
        process = psutil.Process(pid)
        if process.is_running():
            terminal_config["tracked_terminals"][session_id]["status"] = "open"
            return {
                "exists": True,
                "status": "open",
                "pid": pid,
                "session_id": session_id
            }
        else:
            terminal_config["tracked_terminals"][session_id]["status"] = "closed"
            save_config()
            return {
                "exists": False,
                "status": "closed",
                "session_id": session_id
            }
            
    except psutil.NoSuchProcess:
        terminal_config["tracked_terminals"][session_id]["status"] = "closed"
        save_config()
        return {
            "exists": False,
            "status": "closed",
            "session_id": session_id
        }

def get_terminal_awareness() -> Dict:
    """Get current terminal awareness state."""
    load_config()  # Refresh from JSON
    
    open_terminals = []
    
    for session_id in list(terminal_config["tracked_terminals"].keys()):
        status = check_terminal_status(session_id)
        if status.get("exists", False):
            open_terminals.append(status)
    
    return {
        "can_see_terminals": len(open_terminals) > 0,
        "terminal_count": len(open_terminals),
        "terminals": open_terminals
    }

# =============================================
# SKILL INTERFACE FUNCTIONS
# =============================================

def get_prompt():
    """Return skill description for LLM context"""
    return """Terminal Management: I can open PowerShell terminal windows and track their status. I'm aware of which terminals are open or closed in real-time."""

def handle_command(user_input: str) -> bool:
    """Handle open terminal skill commands"""
    user_input = user_input.strip().lower()
    
    # Open new terminal
    if user_input in ["open terminal", "new terminal", "terminal"]:
        result = open_terminal()
        if result["success"]:
            print(f"✓ Opened PowerShell terminal (Session: {result['session_id']})")
        else:
            print(f"✗ Failed to open terminal: {result['error']}")
        return True
    
    # Check terminal awareness
    elif user_input in ["check terminals", "see terminals", "terminals"]:
        awareness = get_terminal_awareness()
        if awareness["can_see_terminals"]:
            print(f"✓ Can see {awareness['terminal_count']} open terminal(s)")
        else:
            print("✗ No open terminals detected")
        return True
    
    # List terminal details
    elif user_input in ["list terminals", "terminal status"]:
        awareness = get_terminal_awareness()
        if awareness["terminals"]:
            print("Open Terminals:")
            for terminal in awareness["terminals"]:
                print(f"  - {terminal['session_id']} (PID: {terminal['pid']})")
        else:
            print("No open terminals")
        return True
    
    return False

def get_skill_info():
    """Return skill information for registration"""
    return {
        "name": "open_terminal",
        "version": "0.1.0", 
        "description": "Opens and tracks PowerShell terminal windows",
        "commands": ["open terminal", "check terminals", "list terminals"]
    }

# Initialize on import
load_config()

# =============================================