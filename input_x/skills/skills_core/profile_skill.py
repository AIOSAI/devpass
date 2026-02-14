# =============================================
# META DATA HEADER
# Name: profile_skill.py - AI Profile System Skill
# Date: 2025-07-26
# Version: 1.1.0
# 
# CHANGELOG (Max 5 entries - remove oldest when adding new):
#   - v1.1.0 (2025-07-26): Migrated to new aipass centralized import system
#   - v1.0.0 (2025-07-22): Simple profile skill based on proven Nexus/Seed pattern
# =============================================

"""
AI Profile System Skill

Provides AI profile/identity functionality by loading profile.json from calling AI.
Based on proven working pattern from Nexus system_awareness.py.
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
from pathlib import Path
from typing import Dict, Any, Optional

# Test logger immediately
logger.info("profile_skill imported with NEW aipass pattern - logger working")

# =============================================
# MAIN SKILL FUNCTIONS
# =============================================

def get_prompt():
    """
    Return AI profile prompt for OpenAI skill system message collection
    Based on proven Nexus system_awareness.get_system_prompt() pattern
    
    Returns:
        String containing AI's identity and behavioral guidelines
    """
    # Auto-detect which AI is calling by walking the call stack
    ai_path = None
    ai_name = None
    
    for frame_info in inspect.stack():
        frame_path = Path(frame_info.filename)
        if "a.i" in frame_path.parts:
            try:
                ai_index = frame_path.parts.index("a.i")
                if ai_index + 1 < len(frame_path.parts):
                    # Get the AI name (the folder after a.i)
                    ai_name = frame_path.parts[ai_index + 1]
                    # Build path to the AI directory
                    ai_path = Path(*frame_path.parts[:ai_index + 2])
                    logger.info(f"[profile_skill] Detected AI: {ai_name} at {ai_path}")
                    break
            except (ValueError, IndexError):
                continue
    
    if not ai_path or not ai_name:
        logger.warning("[profile_skill] Could not determine AI path - no profile available")
        return ""
    
    # Look for profile.json in the AI directory (following Nexus pattern)
    profile_path = ai_path / "profile_json" / "profile.json"
    logger.info(f"[profile_skill] Looking for profile at: {profile_path}")
    
    if not profile_path.exists():
        logger.info(f"[profile_skill] No profile.json found at {profile_path}")
        return ""
    
    try:
        # Load profile.json directly (exact Nexus pattern)
        with profile_path.open("r", encoding="utf-8") as f:
            profile_data = json.load(f)
        
        # Basic identity from profile (exact Nexus pattern)
        parts = [f"You are {profile_data.get('name', 'Assistant')}, {profile_data.get('persona', 'an AI assistant')}."]
        
        if traits := profile_data.get("traits"):
            parts.append("Traits: " + ", ".join(traits) + ".")
            
        if rules := profile_data.get("rules"):
            parts.append("Rules: " + " · ".join(rules) + ".")
        
        profile_prompt = "\n".join(parts)
        logger.info(f"[profile_skill] Profile prompt provided for {profile_data.get('name', 'AI')}")
        return profile_prompt
        
    except Exception as e:
        logger.error(f"[profile_skill] Error loading profile: {e}")
        return ""

def handle_command(user_input: str) -> bool:
    """
    Handle profile-related commands
    
    Args:
        user_input: User's command input
        
    Returns:
        True if command was handled, False otherwise
    """
    if user_input.lower() in ["profile", "show profile", "my profile", "who am i"]:
        profile_prompt = get_prompt()
        if profile_prompt:
            print(f"[Profile]\n{profile_prompt}")
        else:
            print("[Profile] No profile configured")
        logger.info("[profile_skill] Profile displayed to user")
        return True
    
    return False

def get_skill_info():
    """
    Return information about this skill
    
    Returns:
        Dict containing skill metadata
    """
    return {
        "name": "AI Profile Skill",
        "description": "Provides AI profile/identity functionality",
        "commands": ["profile", "show profile", "my profile", "who am i"],
        "version": "1.0.0",
        "category": "skills_core"
    }
