#!/home/aipass/.venv/bin/python3
"""
TEST MODULE: Edge case - Empty structures
Empty list/dict should NOT be flagged.
"""

from pathlib import Path

MODULE_NAME = "sample_edge_empty"

# Empty structures - should be OK
items = []
config = {}

def handle_command(command: str, args: list) -> bool:
    """Standard drone routing"""
    if command == "add":
        items.append(args[0])
        return True
    return False
