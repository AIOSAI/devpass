#!/home/aipass/.venv/bin/python3
"""
TEST MODULE: Violation - Hardcoded list at module level
This module SHOULD be flagged as having business logic in a module.
"""

from pathlib import Path

# THIS IS THE VIOLATION - hardcoded list at module level
ignore_patterns = [
    '__pycache__',
    'archive',
    '.archive',
    '.backup',
    'artifacts',
    '.temp',
    '.old',
    'deprecated'
]

def handle_command(command: str, args: list) -> bool:
    """Standard drone routing"""
    if command == "test":
        return process_test(args)
    return False

def process_test(args):
    """Uses the hardcoded list"""
    for pattern in ignore_patterns:
        print(pattern)
    return True
