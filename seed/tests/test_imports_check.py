#!/home/aipass/.venv/bin/python3

"""Test imports_check.py for bugs and false positives"""

import sys
from pathlib import Path

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from seed.apps.handlers.standards.imports_check import check_module

# Test 1: Check itself
print("=" * 60)
print("TEST 1: Check imports_check.py itself")
print("=" * 60)
result = check_module('/home/aipass/seed/apps/handlers/standards/imports_check.py')
print(f"Passed: {result['passed']}")
print(f"Score: {result['score']}")
for check in result['checks']:
    print(f"  {check['name']}: {'✓' if check['passed'] else '✗'} - {check['message']}")
print()

# Test 2: File with imports in comments (false positive test)
test_file_2 = '/tmp/test_imports_comments.py'
with open(test_file_2, 'w') as f:
    f.write('''#!/home/aipass/.venv/bin/python3

"""
Example docstring
from seed.apps.modules.bad_import import should_not_trigger
"""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

# Comment: from seed.apps.modules.bad_import import should_not_trigger

def example():
    # from seed.apps.modules.another_bad import also_should_not_trigger
    pass
''')

print("=" * 60)
print("TEST 2: False positive - imports in comments/docstrings")
print("=" * 60)
result2 = check_module(test_file_2)
print(f"Passed: {result2['passed']}")
print(f"Score: {result2['score']}")
for check in result2['checks']:
    print(f"  {check['name']}: {'✓' if check['passed'] else '✗'} - {check['message']}")
print()

# Test 3: Handler importing from parent module (should fail)
test_file_3 = '/tmp/test_handler_violation.py'
with open(test_file_3, 'w') as f:
    f.write('''#!/home/aipass/.venv/bin/python3

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from seed.apps.modules.bad_import import something  # VIOLATION

def example():
    pass
''')

print("=" * 60)
print("TEST 3: Handler independence violation")
print("=" * 60)
result3 = check_module(test_file_3)
print(f"Passed: {result3['passed']}")
print(f"Score: {result3['score']}")
for check in result3['checks']:
    print(f"  {check['name']}: {'✓' if check['passed'] else '✗'} - {check['message']}")
print()

# Test 4: Small file - Prax logger should be optional
test_file_4 = '/tmp/test_small_file.py'
with open(test_file_4, 'w') as f:
    f.write('''#!/home/aipass/.venv/bin/python3

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

def simple():
    return True
''')

print("=" * 60)
print("TEST 4: Small file - Prax logger should be optional")
print("=" * 60)
result4 = check_module(test_file_4)
print(f"Passed: {result4['passed']}")
print(f"Score: {result4['score']}")
for check in result4['checks']:
    print(f"  {check['name']}: {'✓' if check['passed'] else '✗'} - {check['message']}")
print()

# Test 5: Service imports should be allowed in handlers
test_file_5 = '/tmp/test_service_imports.py'
with open(test_file_5, 'w') as f:
    f.write('''#!/home/aipass/.venv/bin/python3

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header

def example():
    pass
''')

print("=" * 60)
print("TEST 5: Service imports (prax, cli) should be allowed")
print("=" * 60)
result5 = check_module(test_file_5)
print(f"Passed: {result5['passed']}")
print(f"Score: {result5['score']}")
for check in result5['checks']:
    print(f"  {check['name']}: {'✓' if check['passed'] else '✗'} - {check['message']}")
print()

# Test 6: Import order check
test_file_6 = '/tmp/test_import_order.py'
with open(test_file_6, 'w') as f:
    f.write('''#!/home/aipass/.venv/bin/python3

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from seed.apps.handlers.json import json_handler
from prax.apps.modules.logger import system_logger as logger  # WRONG ORDER

def example():
    pass
''')

print("=" * 60)
print("TEST 6: Import order - Prax should come before internal")
print("=" * 60)
result6 = check_module(test_file_6)
print(f"Passed: {result6['passed']}")
print(f"Score: {result6['score']}")
for check in result6['checks']:
    print(f"  {check['name']}: {'✓' if check['passed'] else '✗'} - {check['message']}")
print()

# Test 7: String literals with import patterns (false positive test)
test_file_7 = '/tmp/test_string_imports.py'
with open(test_file_7, 'w') as f:
    f.write('''#!/home/aipass/.venv/bin/python3

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

def example():
    example_code = "from seed.apps.modules.bad_import import something"
    return example_code
''')

print("=" * 60)
print("TEST 7: False positive - imports in string literals")
print("=" * 60)
result7 = check_module(test_file_7)
print(f"Passed: {result7['passed']}")
print(f"Score: {result7['score']}")
for check in result7['checks']:
    print(f"  {check['name']}: {'✓' if check['passed'] else '✗'} - {check['message']}")
print()

print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"TEST 1 (self-check): {'PASS' if result['passed'] else 'FAIL'} - {result['score']}/100")
print(f"TEST 2 (comments): {'PASS' if result2['passed'] else 'FAIL'} - {result2['score']}/100")
print(f"TEST 3 (violation): {'FAIL EXPECTED' if not result3['passed'] else 'UNEXPECTED PASS'} - {result3['score']}/100")
print(f"TEST 4 (small file): {'PASS' if result4['passed'] else 'FAIL'} - {result4['score']}/100")
print(f"TEST 5 (services): {'PASS' if result5['passed'] else 'FAIL'} - {result5['score']}/100")
print(f"TEST 6 (order): {'FAIL EXPECTED' if not result6['passed'] else 'UNEXPECTED PASS'} - {result6['score']}/100")
print(f"TEST 7 (strings): {'PASS' if result7['passed'] else 'FAIL'} - {result7['score']}/100")
