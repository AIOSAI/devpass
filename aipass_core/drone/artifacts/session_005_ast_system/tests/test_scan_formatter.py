#!/usr/bin/env python3
"""Quick test of scan formatter"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from drone_discovery import scan_module, format_scan_output

# Test with working module
result = scan_module('test_modules/subparsers.py')
output = format_scan_output(result)
print(output)
