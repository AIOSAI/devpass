from pathlib import Path
#!/usr/bin/env python3
"""
Test file to validate Pattern 8 and Pattern 1b
This file intentionally has old patterns that should be auto-fixed.
"""

# Pattern 1b: os.path variant (should be caught by Fix 1.2)
import os
import sys
AIPASS_ROOT = Path.home()
sys.path.append(str(AIPASS_ROOT))

# Pattern 8: Intra-branch imports (should be caught by Fix 1.1)
from drone.apps.drone_loader import get_command_tree
from drone.apps.drone_registry import load_registry

# Also test that we don't double-fix already correct imports

def test_function():
    """Test function."""
    print("Testing new patterns")
    return True

if __name__ == "__main__":
    test_function()
