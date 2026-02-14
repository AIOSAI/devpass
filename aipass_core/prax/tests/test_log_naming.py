#!/home/aipass/.venv/bin/python3

"""
Test script to verify log file naming uses calling branch
"""

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.append(str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger

def test_from_prax():
    """Test logging from prax itself - should create prax_*.log"""
    print("\n=== TEST 1: Logging from PRAX ===")
    system_logger.info("Test message from PRAX branch")
    print("Expected: prax_test_log_naming.log")
    print("Check: /home/aipass/system_logs/prax_test_log_naming.log")

if __name__ == "__main__":
    test_from_prax()
    print("\n✓ Test complete. Check the log file names in /home/aipass/system_logs/")
