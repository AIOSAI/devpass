#!/home/aipass/.venv/bin/python3
"""
TEST MODULE: Edge case - ALL_CAPS constants with data
Are ALL_CAPS constants acceptable or violations?
"""

from pathlib import Path

MODULE_NAME = "sample_edge_constants"

# ALL_CAPS - Python convention says "this is a constant"
# Should this be allowed or flagged?
DEFAULT_PATTERNS = [
    'pattern_a',
    'pattern_b',
    'pattern_c'
]

SUPPORTED_FORMATS = {
    'json': '.json',
    'yaml': '.yaml',
    'toml': '.toml'
}

def handle_command(command: str, args: list) -> bool:
    """Standard drone routing"""
    if command == "list":
        return list_formats()
    return False

def list_formats():
    """Uses the constants"""
    for fmt in SUPPORTED_FORMATS:
        print(fmt)
    return True
