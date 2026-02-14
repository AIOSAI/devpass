#!/home/aipass/.venv/bin/python3

# =============================================
# META DATA HEADER
# Name: path_validation.py - Command Path Validation
# Date: 2025-11-13
# Version: 2.0.0
# Category: drone/handlers/loader
#
# CHANGELOG:
#   - v2.0.0 (2025-11-13): MIGRATION - Standalone handler from drone_loader.py
# =============================================

"""
Command Path Validation Handler

Validates and resolves command paths in the Drone system.

Features:
- File existence validation
- System command detection
- Path resolution (relative to absolute)
- Working directory handling

Usage:
    from drone.apps.handlers.loader.path_validation import validate_command_path

    is_valid = validate_command_path("seed/apps/seed.py", "aipass_core")
    if is_valid:
        print("Command path is valid")
"""

# =============================================
# IMPORTS
# =============================================

import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

import shutil
from typing import Optional

from prax.apps.modules.logger import system_logger as logger

# =============================================
# CONSTANTS
# =============================================

MODULE_NAME = "loader_path_validation"
ECOSYSTEM_ROOT = Path.home()

# System commands that don't need file validation
SYSTEM_COMMANDS = ['python3', 'python', 'node', 'npm', 'bash', 'sh']

# =============================================
# FUNCTIONS
# =============================================

def validate_command_path(path: str, working_dir: str | None = None) -> bool:
    """Validate that command path exists

    Checks:
    1. System commands (python3, node, etc.)
    2. File existence at specified path
    3. Commands available in PATH

    Args:
        path: Command path to validate
        working_dir: Optional working directory for relative paths

    Returns:
        True if path is valid, False otherwise

    Example:
        >>> validate_command_path("python3")
        True
        >>> validate_command_path("seed/apps/seed.py")
        True
        >>> validate_command_path("nonexistent/file.py")
        False
    """
    try:
        # Check if it's a known system command
        if check_system_command(path):
            logger.info(f"[{MODULE_NAME}] System command detected: {path}")
            return True

        # Check if file exists
        if check_file_exists(path, working_dir):
            logger.info(f"[{MODULE_NAME}] File exists: {path}")
            return True

        # Check if it's in PATH (for system binaries)
        if shutil.which(path):
            logger.info(f"[{MODULE_NAME}] Command found in PATH: {path}")
            return True

        logger.warning(f"[{MODULE_NAME}] Command path not found: {path}")
        return False

    except Exception as e:
        logger.warning(f"[{MODULE_NAME}] Error validating path {path}: {e}")
        return False


def resolve_command_path(path: str, working_dir: str | None = None) -> str:
    """Resolve command path to absolute path

    Args:
        path: Command path (relative or absolute)
        working_dir: Optional working directory

    Returns:
        Absolute path string

    Example:
        >>> resolve_command_path("seed/apps/seed.py")
        '/home/aipass/seed/apps/seed.py'
        >>> resolve_command_path("python3")
        'python3'
    """
    try:
        # Don't resolve system commands
        if check_system_command(path):
            return path

        # Handle relative paths
        if working_dir:
            full_path = ECOSYSTEM_ROOT / working_dir / path
        else:
            full_path = ECOSYSTEM_ROOT / path

        return str(full_path)

    except Exception as e:
        logger.warning(f"[{MODULE_NAME}] Error resolving path {path}: {e}")
        return path


def check_system_command(path: str) -> bool:
    """Check if path is a system command

    Args:
        path: Command path to check

    Returns:
        True if system command, False otherwise

    Example:
        >>> check_system_command("python3")
        True
        >>> check_system_command("script.py")
        False
    """
    return path in SYSTEM_COMMANDS


def check_file_exists(path: str, working_dir: str | None = None) -> bool:
    """Check if file exists at given path

    Args:
        path: File path to check
        working_dir: Optional working directory

    Returns:
        True if file exists, False otherwise

    Example:
        >>> check_file_exists("seed/apps/seed.py")
        True
    """
    try:
        if working_dir:
            full_path = ECOSYSTEM_ROOT / working_dir / path
        else:
            full_path = ECOSYSTEM_ROOT / path

        exists = full_path.exists()
        if not exists:
            logger.info(f"[{MODULE_NAME}] File not found: {full_path}")
        return exists

    except Exception as e:
        logger.warning(f"[{MODULE_NAME}] Error checking file existence: {e}")
        return False
