# profile/profile_prompt.py
import json
from pathlib import Path

ENABLED = True

def get_profile_prompt():
    """Generate profile section for system prompt"""
    try:
        profile_path = Path("profile.json")
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        # Basic identity from profile - EXACT pattern from system_awareness.py
        parts = [f"You are {profile_data.get('name', 'Seed')}, {profile_data.get('persona', 'a modular AI system designed to grow autonomously')}."]
        if traits := profile_data.get("traits"):
            parts.append("Traits: " + ", ".join(traits) + ".")
        if rules := profile_data.get("rules"):
            parts.append("Rules: " + " · ".join(rules) + ".")
        
        return "\n".join(parts)
        
    except (FileNotFoundError, json.JSONDecodeError):
        return "You are Seed, a modular AI system designed to grow autonomously."