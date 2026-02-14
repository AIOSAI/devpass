#!/home/aipass/.venv/bin/python3
"""
TEST MODULE: Violation - Hardcoded dict at module level
This module SHOULD be flagged as having business logic in a module.
"""

from pathlib import Path

# THIS IS THE VIOLATION - hardcoded dict at module level
config = {
    'timeout': 30,
    'retry_count': 3,
    'debug': False,
    'log_level': 'INFO'
}

# ANOTHER VIOLATION - mapping dict
command_handlers = {
    'create': 'handle_create',
    'delete': 'handle_delete',
    'update': 'handle_update'
}

def handle_command(command: str, args: list) -> bool:
    """Standard drone routing"""
    if command in command_handlers:
        return True
    return False
