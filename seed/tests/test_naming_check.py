#!/home/aipass/.venv/bin/python3

"""
Test script for naming_check.py
Tests the checker against itself and other edge cases
"""

import sys
from pathlib import Path

# Add apps to path for correct imports
SEED_ROOT = Path.home() / "seed"
sys.path.insert(0, str(SEED_ROOT / "apps"))

from handlers.standards.naming_check import check_module

# Test 1: Check naming_check.py itself
print("=" * 80)
print("TEST 1: Checking naming_check.py against itself")
print("=" * 80)
result = check_module(str(SEED_ROOT / "apps/handlers/standards/naming_check.py"))
print(f"\nOverall Pass: {result['passed']}")
print(f"Score: {result['score']}/100")
print(f"Standard: {result['standard']}")
print("\nDetailed Checks:")
for check in result['checks']:
    status = "✅ PASS" if check['passed'] else "❌ FAIL"
    print(f"  {status} - {check['name']}: {check['message']}")

# Test 2: Check json_handler.py (should pass as documented exception)
print("\n" + "=" * 80)
print("TEST 2: Checking json_handler.py (documented exception)")
print("=" * 80)
result2 = check_module(str(SEED_ROOT / "apps/handlers/json/json_handler.py"))
print(f"\nOverall Pass: {result2['passed']}")
print(f"Score: {result2['score']}/100")
print("\nDetailed Checks:")
for check in result2['checks']:
    status = "✅ PASS" if check['passed'] else "❌ FAIL"
    print(f"  {status} - {check['name']}: {check['message']}")

# Test 3: Create a test file with violations
print("\n" + "=" * 80)
print("TEST 3: Testing violations detection")
print("=" * 80)

test_file = SEED_ROOT / "test_violations.py"
test_content = """
# Test file with violations

# Bad function names
def BadFunctionName():
    pass

def anotherBadOne():
    pass

# Bad class names
class bad_class_name:
    pass

class Another_Bad_Class:
    pass

# Bad constant (should be UPPER_CASE)
module_constant = "value"

# Good examples
def good_function_name():
    pass

class GoodClassName:
    pass

GOOD_CONSTANT = "value"
"""

with open(test_file, 'w') as f:
    f.write(test_content)

result3 = check_module(str(test_file))
print(f"\nOverall Pass: {result3['passed']}")
print(f"Score: {result3['score']}/100")
print("\nDetailed Checks:")
for check in result3['checks']:
    status = "✅ PASS" if check['passed'] else "❌ FAIL"
    print(f"  {status} - {check['name']}: {check['message']}")

# Cleanup
test_file.unlink()

# Test 4: Test false positives from comments/strings
print("\n" + "=" * 80)
print("TEST 4: Testing false positive protection (comments/strings)")
print("=" * 80)

test_file2 = SEED_ROOT / "test_false_positives.py"
test_content2 = """
# This comment mentions def BadFunction() but should be ignored
# class BadClass should also be ignored in comments
MY_CONSTANT = "This string has def badFunction() which should be ignored"

def good_function():
    '''
    Docstring mentions class BadClass and def AnotherBad()
    These should be ignored
    '''
    some_string = "def NotAFunction(): pass"
    return True

class GoodClass:
    '''class BadClass in docstring should be ignored'''
    pass
"""

with open(test_file2, 'w') as f:
    f.write(test_content2)

result4 = check_module(str(test_file2))
print(f"\nOverall Pass: {result4['passed']}")
print(f"Score: {result4['score']}/100")
print("\nDetailed Checks:")
for check in result4['checks']:
    status = "✅ PASS" if check['passed'] else "❌ FAIL"
    print(f"  {status} - {check['name']}: {check['message']}")

# Cleanup
test_file2.unlink()

print("\n" + "=" * 80)
print("TESTING COMPLETE")
print("=" * 80)
