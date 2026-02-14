#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Template Skill for Nexus v2

To create a new skill:
1. Copy this file
2. Remove the leading underscore from filename
3. Implement your logic in handle_request()

Skills are auto-discovered - just drop the file and restart Nexus.
"""

from typing import Optional

# Skill metadata
SKILL_NAME = "template"
SKILL_DESCRIPTION = "Template skill - copy and customize"
SKILL_TRIGGERS = ["template", "test skill"]  # Keywords that activate this skill

def handle_request(user_input: str) -> Optional[str]:
    """
    Handle user input if this skill matches

    Args:
        user_input: The user's message

    Returns:
        Response string if this skill handles it, None to pass to next skill/LLM
    """
    # Check if this skill should handle the input
    lower_input = user_input.lower()

    for trigger in SKILL_TRIGGERS:
        if trigger in lower_input:
            return f"[Template Skill] Triggered by: {trigger}"

    # Return None to let other skills or LLM handle it
    return None

def get_help() -> str:
    """Return help text for this skill"""
    return f"{SKILL_NAME}: {SKILL_DESCRIPTION}"
