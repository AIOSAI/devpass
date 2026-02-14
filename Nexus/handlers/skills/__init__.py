#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Skill auto-discovery for Nexus v2"""

import sys
import importlib
import logging
from pathlib import Path
from typing import List, Any, Optional

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent

def discover_skills() -> List[Any]:
    """
    Auto-discover skills in this directory

    Pattern: Any .py file that implements handle_request() gets registered.
    Files starting with _ are skipped (disabled).

    Returns:
        List of skill modules with handle_request() method
    """
    skills = []

    for file_path in SKILLS_DIR.glob("*.py"):
        # Skip __init__.py, __pycache__, and disabled skills (underscore prefix)
        if file_path.name.startswith("_") or file_path.name == "__init__.py":
            continue

        module_name = f"handlers.skills.{file_path.stem}"

        try:
            module = importlib.import_module(module_name)

            # Duck typing: if it has handle_request(), it's a skill
            if hasattr(module, 'handle_request'):
                skills.append(module)
        except Exception as e:
            logger.error(f"Skill load error {file_path.stem}: {e}")

    return skills

def get_skill_names() -> List[str]:
    """Get names of all discovered skills"""
    return [s.__name__.split('.')[-1] for s in discover_skills()]

def route_to_skill(user_input: str, skills: List[Any]) -> Optional[str]:
    """
    Check if any skill wants to handle this input

    Args:
        user_input: The user's message
        skills: List of discovered skill modules

    Returns:
        Skill response if handled, None if no skill matched
    """
    for skill in skills:
        try:
            result = skill.handle_request(user_input)
            if result is not None:
                return result
        except Exception as e:
            logger.error(f"Skill error {skill.__name__}: {e}")

    return None
