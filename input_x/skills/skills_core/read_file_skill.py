# =============================================
# META DATA HEADER
# Name: read_file_skill.py
# Date: 2025-07-26
# Version: 0.2.0
# 
# CHANGELOG:
#   - v0.2.0 (2025-07-26): Migrated to new aipass centralized import system
#   - v0.1.0 (2025-07-09): Simple file reading skill following working pattern
# =============================================

"""
Read File Skill

Simple file reading - stores content in read_file_skill.json
NOW USING: New centralized aipass import system for cleaner code.
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
import re
import atexit
from pathlib import Path
from datetime import datetime, timezone

# Test logger immediately
logger.info("read_file_skill imported with NEW aipass pattern - logger working")



# =============================================
# SKILL CONFIGURATION
# =============================================

# Skill identity
SKILL_NAME = "read_file_skill"

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
    return folder_map.get(skill_category, "read_file_skill_json")

# Auto-detection system for JSON placement
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
    except:
        pass
    return None, None, None

# JSON file paths - NEW 3-FILE STRUCTURE
caller_ai, ai_path, json_folder = get_caller_ai_info()
if json_folder:
    SKILL_CONFIG_FILE = json_folder / f"{SKILL_NAME}_config.json"
    SKILL_DATA_FILE = json_folder / f"{SKILL_NAME}_data.json"
    SKILL_LOG_FILE = json_folder / f"{SKILL_NAME}_log.json"
else:
    SKILL_CONFIG_FILE = Path(__file__).parent / f"{SKILL_NAME}_config.json"
    SKILL_DATA_FILE = Path(__file__).parent / f"{SKILL_NAME}_data.json"
    SKILL_LOG_FILE = Path(__file__).parent / f"{SKILL_NAME}_log.json"

# =============================================
# SKILL FUNCTIONS
# =============================================

# Global cleanup flag - persists across module imports
import tempfile
import os

# Create a temporary flag file that persists across imports
_cleanup_flag_file = Path(tempfile.gettempdir()) / "aipass_read_file_cleanup.flag"

def clear_cache_content():
    """CRITICAL: Clear file content on exit - prevent token explosion"""
    global _cleanup_flag_file
    
    try:
        # Check if cleanup already ran this session
        if _cleanup_flag_file.exists():
            return
            
        # Mark that cleanup is running
        _cleanup_flag_file.touch()
        
        if SKILL_DATA_FILE.exists():
            with open(SKILL_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Keep config and metadata, clear content
            cleaned_data = {
                "skill_name": SKILL_NAME,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "config": data.get("config", {"MAX_FILE_ENTRIES": 2, "CLEAR_ON_EXIT": True}),
                "files": {},  # Clear all content
                "metadata": {
                    "last_session_files": len(data.get("files", {})),
                    "cleared_on_exit": True
                }
            }
            
            with open(SKILL_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, indent=2)
                
            print(f"[{SKILL_NAME}] Cache cleared - content purged, metadata preserved")
            logger.info("Cache cleared - content purged, metadata preserved")
            
    except Exception as e:
        print(f"[{SKILL_NAME}] Error clearing cache: {e}")

def cleanup_temp_flag():
    """Remove temp flag on startup"""
    global _cleanup_flag_file
    try:
        if _cleanup_flag_file.exists():
            _cleanup_flag_file.unlink()
    except:
        pass

# Clean any leftover flag from previous session
cleanup_temp_flag()

def save_file_content(file_path, content):
    """Save file content with config and rolloff logic"""
    try:
        SKILL_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing data or create new structure
        if SKILL_DATA_FILE.exists():
            with open(SKILL_DATA_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                # Handle old single-file format
                if "file_path" in existing_data and "content" in existing_data:
                    # Convert old format to new format
                    files = {
                        existing_data["file_path"]: {
                            "content": existing_data["content"],
                            "timestamp": existing_data.get("timestamp", datetime.now(timezone.utc).isoformat())
                        }
                    }
                    config = {"MAX_FILE_ENTRIES": 2, "CLEAR_ON_EXIT": True}
                else:
                    files = existing_data.get("files", {})
                    config = existing_data.get("config", {"MAX_FILE_ENTRIES": 2, "CLEAR_ON_EXIT": True})
        else:
            files = {}
            config = {"MAX_FILE_ENTRIES": 2, "CLEAR_ON_EXIT": True}
        
        # Add or update the new file
        files[file_path] = {
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Enforce MAX_FILE_ENTRIES limit
        max_entries = config.get("MAX_FILE_ENTRIES", 2)
        if len(files) > max_entries:
            # Remove oldest files (by timestamp)
            sorted_files = sorted(files.items(), key=lambda x: x[1]["timestamp"])
            files = dict(sorted_files[-max_entries:])  # Keep newest entries
            print(f"[{SKILL_NAME}] Rolloff: keeping {max_entries} newest files")
        
        # Create new structure
        result_data = {
            "skill_name": SKILL_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": config,
            "files": files,
            "metadata": {
                "total_files": len(files),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }
        
        with open(SKILL_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2)
            
    except Exception as e:
        print(f"[{SKILL_NAME}] Error saving: {e}")

def log_operation(operation, success=True, error=None):
    """Log operation to read_file_skill_log.json"""
    try:
        SKILL_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "success": success,
            "error": str(error) if error else None
        }
        
        # Load existing log
        log_data = []
        if SKILL_LOG_FILE.exists():
            with open(SKILL_LOG_FILE, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        
        # Add new entry
        log_data.insert(0, log_entry)  # Newest first
        log_data = log_data[:50]  # Keep last 50 entries
        
        with open(SKILL_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2)
            
    except Exception as e:
        print(f"[{SKILL_NAME}] Log error: {e}")

# Register exit cleanup
atexit.register(clear_cache_content)

# =============================================
# SKILL INTERFACE FUNCTIONS
# =============================================

def get_prompt():
    """Returns the prompt text for file reading capability"""
    return """
# File Reading

You can read files using:
- `read file <file_path>` - Read file and store content for discussion

The file content will be available for you to reference and discuss.
"""

def handle_command(user_input: str) -> bool:
    """Handle read file commands"""
    user_input = user_input.strip()
    logger.info(f"Command received: {user_input}")
    
    # Cache clear command
    if "clear read file cache" in user_input.lower() or user_input.lower() in ["exit", "quit", "bye"]:
        logger.info("Cache clear command detected")
        clear_cache_content()
        return True
    
    # Simple pattern matching (what was working)
    match = re.match(r"read file (.+)", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        logger.info(f"File path extracted: {file_path}")
        try:
            logger.info(f"Attempting to read file: {file_path}")
            # Read file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"File read successfully, content length: {len(content)} characters")
            
            # Save content to read_file_skill.json
            save_file_content(file_path, content)
            
            # Log success
            log_operation(f"Read file: {file_path}")
            
            print(f"✓ File read: {Path(file_path).name} - content stored")
            logger.info(f"File read: {Path(file_path).name} - content stored")
            return True
            
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            log_operation(f"Failed to read: {file_path}", success=False, error=e)
            print(f"✗ Error reading file: {e}")
            return True
    
    return False

def get_skill_info():
    """Required function for skill registration"""
    return {
        "name": SKILL_NAME,
        "description": "Simple file reading",
        "commands": ["read file <path>"],
        "version": "0.1.0"
    }

# =============================================
# MODULE EXECUTION
# =============================================

if __name__ == "__main__":
    print(f"[{SKILL_NAME}] Testing...")
    test_result = handle_command("read file README.md")
    print(f"Test result: {test_result}")
