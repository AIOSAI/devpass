#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: backup_utils.py
# Date: 2025-10-14
# Version: 1.0.0
# Category: backup_system
#
# CHANGELOG:
#   - v1.0.0 (2025-10-14): Initial extraction from backup.py
#     * Extracted temporarily_writable() context manager (lines 62-97)
#     * Extracted safe_print() function (lines 127-143)
#     * Linux-focused utilities (no platform complexity for now)
#     * Critical permission handling for Linux read-only enforcement
# =============================================

"""
Backup System Utilities

Linux-focused helper functions and context managers.
Critical utilities used throughout backup operations.
"""

# =============================================
# IMPORTS
# =============================================

import sys
import os
import stat
from pathlib import Path
from contextlib import contextmanager

# Infrastructure import pattern
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))
from prax.apps.prax_logger import system_logger as logger

# =============================================
# CONSTANTS
# =============================================

# Fix console encoding for emojis (Linux/Windows compatibility)
EMOJI_SUPPORT = True
if sys.platform == 'win32':
    try:
        # Try to enable UTF-8 output on Windows
        os.system('chcp 65001 > nul')
        # Use getattr to safely call reconfigure if it exists
        reconfigure_stdout = getattr(sys.stdout, 'reconfigure', None)
        if reconfigure_stdout:
            reconfigure_stdout(encoding='utf-8', errors='replace')
        reconfigure_stderr = getattr(sys.stderr, 'reconfigure', None)
        if reconfigure_stderr:
            reconfigure_stderr(encoding='utf-8', errors='replace')
    except Exception:
        EMOJI_SUPPORT = False

# =============================================
# CONTEXT MANAGERS
# =============================================

@contextmanager
def temporarily_writable(path):
    """Context manager to temporarily make a directory/file writable on Linux.

    This is critical for Linux because it strictly enforces read-only permissions,
    unlike Windows which allows owners to bypass them.

    Used in 10+ locations throughout backup operations for:
    - Creating new directories in read-only backup roots
    - Updating files in protected backup directories
    - Deleting files from read-only locations

    Args:
        path: Path object or string path to make temporarily writable

    Yields:
        Path object with write permissions temporarily enabled

    Example:
        with temporarily_writable(backup_path):
            # Perform operations that need write access
            shutil.copy2(source, target)
        # Permissions automatically restored here
    """
    path_obj = Path(path)
    original_mode = None

    try:
        # Store original permissions if path exists
        if path_obj.exists():
            original_mode = path_obj.stat().st_mode

            # Make writable for owner
            if path_obj.is_dir():
                # Directory: add write and execute permissions for owner
                path_obj.chmod(original_mode | stat.S_IWUSR | stat.S_IXUSR)
            else:
                # File: add write permission for owner
                path_obj.chmod(original_mode | stat.S_IWUSR)

        yield path_obj

    finally:
        # Restore original permissions if we changed them
        if original_mode is not None and path_obj.exists():
            try:
                path_obj.chmod(original_mode)
            except Exception as e:
                logger.warning(f"Could not restore original permissions for {path}: {e}")

# =============================================
# HELPER FUNCTIONS
# =============================================

def safe_print(text):
    """Print text with emoji fallback for systems that don't support them.

    Handles console encoding issues across different platforms.

    Args:
        text: String to print (may contain emoji characters)

    Returns:
        None (prints to stdout)

    Example:
        safe_print("✅ Backup complete!")
        # On systems without emoji support: "[SUCCESS] Backup complete!"
    """
    if not EMOJI_SUPPORT:
        # Replace emojis with text equivalents
        text = text.replace('🔥', '[CRITICAL]')
        text = text.replace('❌', '[ERROR]')
        text = text.replace('⚠️', '[WARNING]')
        text = text.replace('✅', '[SUCCESS]')
        text = text.replace('📁', '[VERSION]')
        text = text.replace('🗑️', '[DELETED]')
        text = text.replace('💡', '[SUGGESTION]')
        text = text.replace('📸', '[SNAPSHOT]')
        text = text.replace('📋', '[INFO]')
        text = text.replace('📄', '[FILE]')
        text = text.replace('📂', '[FOLDER]')
        text = text.replace('📍', '[LATEST]')
    try:
        print(text)
    except UnicodeEncodeError:
        # Final fallback - strip all non-ASCII characters
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(safe_text)

# =============================================
# MODULE INITIALIZATION
# =============================================

# No initialization needed - pure utility functions
