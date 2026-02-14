# =============================================
# META DATA HEADER
# Name: live_chat_context_skill.py
# Date: 2025-07-26
# Version: 0.3.0
# 
# CHANGELOG:
#   - v0.3.0 (2025-07-26): Migrated to new aipass centralized import system
#   - v0.2.0 (2025-07-08): Fresh rebuild with working conversation memory
#   - v0.1.0 (2025-07-05): Initial version
# =============================================

"""
Live Chat Context Skill

Manages conversation memory and context for contextual AI conversations.
Maintains rolling 20-message buffer with automatic memory reset on exit.
NOW USING: New centralized aipass import system for cleaner code.
"""

# NEW AIPASS IMPORT PATTERN - Fixed absolute import
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import __init__ as aipass
from __init__ import logger

# Standard imports
import sys
import json
import inspect
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict
import logging

# Test logger immediately
logger.info("live_chat_context_skill imported with NEW aipass pattern - logger working")

# OLD LOGGING SYSTEM REMOVED - using global logger only

# Import openai_skill from skills_api - CHECK PRAX REGISTRY FIRST
# Using NEW aipass pattern for registry access
from __init__ import load_registry

# Check if openai_skill AND api_connect are enabled before importing
registry = load_registry()
openai_enabled = registry.get("openai_skill", {}).get("enabled", True)
api_connect_enabled = registry.get("api_connect", {}).get("enabled", True)

# Need both openai_skill and api_connect to be enabled for chat functionality
if openai_enabled and api_connect_enabled:
    # Now import using the full package path
    from skills.skills_api import openai_skill
    logger.info("Successfully imported openai_skill using absolute import")
    OPENAI_AVAILABLE = True
else:
    logger.error("openai_skill or api_connect disabled in Prax registry - live_chat_context_skill cannot function")
    raise ImportError("openai_skill or api_connect disabled in Prax registry")


# =============================================
# AUTO-DETECTION SYSTEM
# =============================================

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
                    skill_category = get_skill_category()
                    json_folder = get_json_folder_name(skill_category)
                    json_folder_path = ai_path / json_folder
                    return ai_name, ai_path, json_folder_path
        return None, None, None
    except Exception as e:
        logger.error(f"[Live Chat Context] Error detecting caller: {e}")
        return None, None, None

def get_skill_category():
    """Determine skill category from file location"""
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
        return "skills_memory"  # Default for this skill

def get_json_folder_name(skill_category):
    """Convert skill category to JSON folder name"""
    folder_map = {
        "skills_core": "skills_core_json",
        "skills_memory": "memory_json", 
        "skills_mods": "skills_mods_json",
        "skills_api": "skills_api_json"
    }
    return folder_map.get(skill_category, "memory_json")

def get_dynamic_skill_paths():
    """Get dynamic paths based on caller detection - NEW 3-FILE STRUCTURE"""
    ai_name, ai_path, json_folder_path = get_caller_ai_info()
    if json_folder_path:
        json_folder_path.mkdir(parents=True, exist_ok=True)
        config_file = json_folder_path / f"{SKILL_NAME}_config.json"
        data_file = json_folder_path / f"{SKILL_NAME}_data.json"
        log_file = json_folder_path / f"{SKILL_NAME}_log.json"
        logger.info(f"[Live Chat Context] Using {ai_name} storage: {json_folder_path}")
        return config_file, data_file, log_file
    else:
        logger.info(f"[Live Chat Context] Using fallback storage: {SKILL_FILE_DIR}")
        fallback_config = SKILL_FILE_DIR / f"{SKILL_NAME}_config.json"
        fallback_data = SKILL_FILE_DIR / f"{SKILL_NAME}_data.json"
        fallback_log = SKILL_FILE_DIR / f"{SKILL_NAME}_log.json"
        return fallback_config, fallback_data, fallback_log

# =============================================
# SKILL CONFIGURATION
# =============================================

# Skill identity
SKILL_NAME = "live_chat_context"

# Portable paths
SKILL_FILE_DIR = Path(__file__).parent

# Dynamic skill file paths (auto-detect caller) - NEW 3-FILE STRUCTURE
SKILL_CONFIG_FILE, SKILL_DATA_FILE, SKILL_LOG_FILE = get_dynamic_skill_paths()

# Conversation memory storage
conversation_memory = []

# =============================================
# LOGGING
# =============================================

def log_skill_operation(operation_details, result_data=None, error=None):
    """Log skill operation"""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation_details,
        "success": error is None,
        "result": result_data if error is None else None,
        "error": str(error) if error else None
    }
    
    try:
        if SKILL_LOG_FILE.exists():
            with open(SKILL_LOG_FILE, "r", encoding="utf-8") as f:
                log = json.load(f)
        else:
            log = []
        
        log.insert(0, entry)  # Newest first
        log = log[:50]  # Keep last 50 entries
        
        with open(SKILL_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)
    except Exception as e:
        logger.error(f"[Live Chat Context] Logging error: {e}")

def get_ai_identity():
    """Get the calling AI's name from their main file (seed.py, nexus.py, etc.)"""
    try:
        ai_name, ai_path, json_folder_path = get_caller_ai_info()
        if ai_name and ai_path:
            # Look for the main AI file (seed.py, nexus.py, etc.)
            main_file = ai_path / f"{ai_name.lower()}.py"
            if main_file.exists():
                # Read the file and extract SYSTEM_NAME
                content = main_file.read_text(encoding="utf-8")
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('SYSTEM_NAME = '):
                        # Extract the name from SYSTEM_NAME = "TestBot"
                        name_part = line.split('=', 1)[1].strip()
                        # Remove quotes and clean up
                        ai_display_name = name_part.strip('"\'')
                        return ai_display_name
                
                # Fallback to folder name if SYSTEM_NAME not found
                return ai_name
            else:
                # Fallback to folder name if main file doesn't exist
                return ai_name
        else:
            # Fallback if detection fails
            return "AI"
    except Exception as e:
        logger.error(f"[Live Chat Context] Error getting AI identity: {e}")
        return "AI"

# =============================================
# MEMORY MANAGEMENT
# =============================================

def add_to_memory(role: str, content: str):
    """Add message to conversation memory"""
    global conversation_memory
    
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    conversation_memory.append(message)
    
    # Keep last 20 messages
    if len(conversation_memory) > 20:
        conversation_memory = conversation_memory[-20:]
    
    save_memory()

def get_context_messages():
    """Get messages in OpenAI format"""
    return [{"role": msg["role"], "content": msg["content"]} for msg in conversation_memory]

def save_memory():
    """Save memory using new 3-file structure"""
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create config file if it doesn't exist
        if not SKILL_CONFIG_FILE.exists():
            config_data = {
                "skill_name": SKILL_NAME,
                "timestamp": timestamp,
                "config": {
                    "max_memory_entries": 20,
                    "auto_save": True,
                    "clear_on_exit": True,
                    "context_window_size": 10,
                    "enable_summaries": False
                }
            }
            SKILL_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SKILL_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
        
        # Save data file
        data_data = {
            "skill_name": SKILL_NAME,
            "timestamp": timestamp,
            "data": {
                "conversation_memory": conversation_memory,
                "memory_statistics": {
                    "total_messages": len(conversation_memory),
                    "memory_usage_percent": min(100, (len(conversation_memory) / 20) * 100),
                    "last_activity": timestamp
                }
            }
        }
        
        SKILL_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SKILL_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data_data, f, indent=2)
            
    except Exception as e:
        logger.error(f"[Live Chat Context] Save error: {e}")

def load_memory():
    """Load memory from file - handles both old and new data formats"""
    global conversation_memory
    
    try:
        if SKILL_DATA_FILE.exists():
            with open(SKILL_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Handle new nested format
                if "data" in data and "conversation_memory" in data["data"]:
                    conversation_memory = data["data"]["conversation_memory"]
                # Handle old flat format (backward compatibility)
                elif "conversation_memory" in data:
                    conversation_memory = data["conversation_memory"]
                else:
                    conversation_memory = []
        else:
            conversation_memory = []
    except Exception as e:
        logger.error(f"[Live Chat Context] Load error: {e}")
        conversation_memory = []

def clear_memory():
    """Clear all conversation memory"""
    global conversation_memory
    conversation_memory = []
    save_memory()
    
# =============================================
# SKILL INTERFACE FUNCTIONS
# =============================================

def get_prompt():
    """Return prompt text for LLM integration"""
    return f"""Live Chat Context Skill:
- Manages conversation memory and context
- Maintains rolling 20-message buffer
- Commands: 'chat [message]' for contextual conversation
- Current memory: {len(conversation_memory)} messages
"""

def get_skill_context():
    """Return current skill context"""
    return f"Chat Context: {len(conversation_memory)} messages in memory"

def handle_command(user_input: str) -> bool:
    """Handle chat context commands"""
    user_input = user_input.strip()
    
    # Handle "chat [message]" command for contextual conversation
    if user_input.lower().startswith("chat "):
        message = user_input[5:]  # Remove "chat "
        if message:
            logger.info(f"Chat command received: {message}")
            # Add user message to memory
            add_to_memory("user", message)
            
            # Get conversation context 
            messages = get_context_messages()
            logger.info(f"Retrieved {len(messages)} context messages")
            
            # Check if OpenAI is available before making API call
            if not OPENAI_AVAILABLE:
                print("Chat functionality unavailable - openai_skill is disabled")
                logger.warning("Chat request failed - openai_skill disabled in Prax registry")
                return False
            
            # Get response from OpenAI with full context
            response = openai_skill.get_response(messages)
            logger.info(f"OpenAI response received, length: {len(response)} characters")
            
            # Add response to memory
            add_to_memory("assistant", response)
            
            # Get the calling AI's name dynamically
            ai_name = get_ai_identity()
            
            # Print response with correct AI name
            print(f"{ai_name}: {response}")
            
            log_skill_operation("Contextual chat", {"message_length": len(message), "context_messages": len(messages)})
            return True
    
    # Show memory stats
    elif user_input.lower() == "memory stats":
        # Keep this as print since it's user-facing output
        print(f"Conversation Memory: {len(conversation_memory)} messages")
        if conversation_memory:
            print(f"Last message: {conversation_memory[-1]['timestamp']}")
        # Also log it
        logger.info(f"Memory stats: {len(conversation_memory)} messages")
        return True
    
    # Clear memory
    elif user_input.lower() == "clear memory":
        clear_memory()
        # Keep this as print since it's user-facing output
        print("Memory cleared")
        # Also log it
        logger.info("Memory cleared")
        return True
    
    return False

def get_skill_info():
    """Return skill information"""
    return {
        "name": SKILL_NAME,
        "version": "0.2.0",
        "description": "Chat context and memory management with OpenAI",
        "commands": ["chat [message]", "memory stats", "clear memory"]
    }

# =============================================
# INITIALIZATION
# =============================================

# Load memory on import
load_memory()

# Ensure JSON files exist (create if missing)
save_memory()

# Create initial log entry
log_skill_operation("Skill initialized", {"memory_count": len(conversation_memory)})

logger.info(f"[Live Chat Context] Initialized with {len(conversation_memory)} messages")
