#!/home/aipass/.venv/bin/python3
"""
TEST MODULE: Clean - No business logic violations
This module SHOULD pass - proper orchestration only.
"""

from pathlib import Path
import sys

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Simple constants are OK
MODULE_NAME = "sample_clean"
VERSION = "1.0.0"

def handle_command(command: str, args: list) -> bool:
    """Standard drone routing - orchestration only"""
    if command == "test":
        return run_test(args)
    if command == "help":
        return show_help()
    return False

def run_test(args):
    """Delegates to handler (in real code)"""
    # Would call: from handlers import test_handler
    # test_handler.run(args)
    return True

def show_help():
    """Shows help"""
    print(f"{MODULE_NAME} v{VERSION}")
    return True
