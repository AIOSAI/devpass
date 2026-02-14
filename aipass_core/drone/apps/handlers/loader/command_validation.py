#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: command_validation.py - Command Data Validation
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/loader
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): MIGRATION - Standalone handler from drone_loader.py
# =============================================

"""
Command Data Validation Handler

Validates command data structures and required fields.

Features:
- Required field validation
- Command structure validation
- Data type checking
- Path validation integration

Usage:
    from drone.apps.handlers.loader.command_validation import validate_command_data

    cmd_data = {"path": "seed/apps/seed.py", "args": []}
    if validate_command_data(cmd_data):
        print("Command data is valid")
"""

# =============================================
# IMPORTS
# =============================================

import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from typing import Dict, Any

from prax.apps.modules.logger import system_logger as logger

# Same-package import allowed
from .path_validation import validate_command_path

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "loader_command_validation"

# Required fields for command data
REQUIRED_FIELDS = ["path"]
OPTIONAL_FIELDS = ["args", "description", "cwd", "env", "timeout"]

# =============================================
# FUNCTIONS
# =============================================

def validate_command_data(cmd_data: Dict[str, Any]) -> bool:
    """Validate command data structure

    Checks:
    1. Must have 'path' field
    2. Path must exist or be system command
    3. Data structure must be dict

    Args:
        cmd_data: Command data dictionary

    Returns:
        True if valid, False otherwise

    Example:
        >>> cmd = {"path": "python3", "args": ["-V"]}
        >>> validate_command_data(cmd)
        True
        >>> cmd = {"args": []}  # Missing path
        >>> validate_command_data(cmd)
        False
    """
    try:
        # Check required fields
        if not validate_required_fields(cmd_data):
            return False

        # Check command structure
        if not validate_command_structure(cmd_data):
            return False

        # Validate path exists
        path = cmd_data["path"]
        working_dir = cmd_data.get("cwd")

        if not validate_command_path(path, working_dir):
            logger.warning(f"[{MODULE_NAME}] Command path not found: {path}")
            return False

        logger.info(f"[{MODULE_NAME}] Command data validated: {path}")
        return True

    except Exception as e:
        logger.warning(f"[{MODULE_NAME}] Error validating command data: {e}")
        return False


def validate_required_fields(cmd_data: Dict[str, Any]) -> bool:
    """Validate command has required fields

    Args:
        cmd_data: Command data dictionary

    Returns:
        True if all required fields present, False otherwise

    Example:
        >>> cmd = {"path": "test.py"}
        >>> validate_required_fields(cmd)
        True
    """
    try:
        if not isinstance(cmd_data, dict):
            logger.warning(f"[{MODULE_NAME}] Command data is not a dict")
            return False

        for field in REQUIRED_FIELDS:
            if field not in cmd_data:
                logger.warning(f"[{MODULE_NAME}] Missing required field: {field}")
                return False

        return True

    except Exception as e:
        logger.warning(f"[{MODULE_NAME}] Error validating required fields: {e}")
        return False


def validate_command_structure(cmd_data: Dict[str, Any]) -> bool:
    """Validate command structure is correct

    Args:
        cmd_data: Command data dictionary

    Returns:
        True if structure valid, False otherwise

    Example:
        >>> cmd = {"path": "test.py", "args": ["--help"]}
        >>> validate_command_structure(cmd)
        True
    """
    try:
        # Check data types of known fields
        if "path" in cmd_data and not isinstance(cmd_data["path"], str):
            logger.warning(f"[{MODULE_NAME}] 'path' must be string")
            return False

        if "args" in cmd_data and not isinstance(cmd_data["args"], list):
            logger.warning(f"[{MODULE_NAME}] 'args' must be list")
            return False

        if "description" in cmd_data and not isinstance(cmd_data["description"], str):
            logger.warning(f"[{MODULE_NAME}] 'description' must be string")
            return False

        if "cwd" in cmd_data and not isinstance(cmd_data["cwd"], str):
            logger.warning(f"[{MODULE_NAME}] 'cwd' must be string")
            return False

        return True

    except Exception as e:
        logger.warning(f"[{MODULE_NAME}] Error validating command structure: {e}")
        return False
