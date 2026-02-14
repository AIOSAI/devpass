#!/home/aipass/.venv/bin/python3
"""
TEST MODULE: Edge case - Data inside function (local scope)
This is an edge case - data inside functions may be acceptable.
"""

from pathlib import Path

MODULE_NAME = "sample_edge"

def handle_command(command: str, args: list) -> bool:
    """Standard drone routing"""
    if command == "process":
        return process_items()
    return False

def process_items():
    """Has local data - is this OK or violation?"""
    # This is INSIDE a function - local scope
    local_patterns = [
        'temp_item_1',
        'temp_item_2',
        'temp_item_3'
    ]
    for p in local_patterns:
        print(p)
    return True
