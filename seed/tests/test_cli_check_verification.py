#!/home/aipass/.venv/bin/python3
"""
Test file to verify cli_check.py quote counting algorithm and edge cases
"""

import sys
from pathlib import Path

# Setup path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from seed.apps.handlers.standards.cli_check import check_handler_separation


def create_test_file(content: str, filepath: Path):
    """Create a test file with given content"""
    filepath.write_text(content)


def test_quote_counting():
    """Test the quote counting algorithm for various edge cases"""

    test_cases = [
        {
            "name": "Real console.print() call",
            "code": '''
def foo():
    console.print("Hello world")
''',
            "should_fail": True,
            "reason": "Actual console.print() call should be detected"
        },
        {
            "name": "console.print() in single-quoted string",
            "code": '''
def foo():
    pattern = 'console.print('
''',
            "should_fail": False,
            "reason": "console.print( inside single quotes should be skipped"
        },
        {
            "name": "console.print() in double-quoted string",
            "code": '''
def foo():
    pattern = "console.print("
''',
            "should_fail": False,
            "reason": "console.print( inside double quotes should be skipped"
        },
        {
            "name": "console.print() after closing quote",
            "code": '''
def foo():
    msg = "test"
    console.print(msg)
''',
            "should_fail": True,
            "reason": "console.print() after closed string should be detected"
        },
        {
            "name": "Multiple quotes before console.print()",
            "code": '''
def foo():
    a = "test"
    b = 'test'
    console.print("output")
''',
            "should_fail": True,
            "reason": "Even quotes before should not affect - they're closed pairs"
        },
        {
            "name": "console.print() in docstring triple-quoted",
            "code": '''
def foo():
    """
    This function uses console.print() to display
    """
    pass
''',
            "should_fail": False,
            "reason": "console.print() in docstring should be skipped"
        },
        {
            "name": "Escaped quotes before console.print()",
            "code": '''
def foo():
    msg = "He said \\"hello\\" console.print("
''',
            "should_fail": False,
            "reason": "console.print( inside string with escaped quotes should be skipped"
        },
        {
            "name": "String concatenation with console.print()",
            "code": '''
def foo():
    pattern = "console" + ".print("
''',
            "should_fail": False,
            "reason": "console.print( split across concatenation in string context"
        },
        {
            "name": "Checking for console.print pattern",
            "code": '''
def check_console():
    has_console_print = 'console.print(' in content
''',
            "should_fail": False,
            "reason": "String literal assignment should not trigger"
        },
        {
            "name": "Comment with console.print()",
            "code": '''
def foo():
    # Use console.print() here
    pass
''',
            "should_fail": False,
            "reason": "Comments should be skipped"
        },
        {
            "name": "Mixed quotes on same line",
            "code": '''
def foo():
    x = "test"; y = 'test'; console.print("output")
''',
            "should_fail": True,
            "reason": "Even with mixed quotes, last console.print is real code"
        },
        {
            "name": "Nested quotes different types",
            "code": '''
def foo():
    msg = "She said 'use console.print()' here"
''',
            "should_fail": False,
            "reason": "Nested quotes with console.print inside should be skipped"
        },
        {
            "name": "Real world example from cli_check itself",
            "code": '''
        # Look for actual console.print() calls
        # Must be actual code, not in a string
        if 'console.print(' in stripped:
            # Skip if it's in a string literal
            # Check if console.print( appears inside quotes
            before_pattern = line.split('console.print(')[0]
''',
            "should_fail": False,
            "reason": "Comments with pattern should not trigger"
        },
        {
            "name": "Triple-quoted string with console.print",
            "code": '''
def foo():
    """Documentation
    console.print("test")
    """
    pass
''',
            "should_fail": False,
            "reason": "Docstrings tracked by triple-quote toggle"
        },
        {
            "name": "F-string with console.print reference",
            "code": '''
def foo():
    msg = f"Use console.print() function"
''',
            "should_fail": False,
            "reason": "console.print inside f-string should be skipped"
        },
        {
            "name": "Assignment checking for pattern",
            "code": '''
def check():
    has_print = 'console.print(' in line
''',
            "should_fail": False,
            "reason": "String literal in contains check should be skipped (line 190)"
        },
        {
            "name": "Multiple console.print calls",
            "code": '''
def foo():
    console.print("Line 1")
    console.print("Line 2")
''',
            "should_fail": True,
            "reason": "Multiple real calls should all be detected"
        },
        {
            "name": "Bare print() call",
            "code": '''
def foo():
    print("Hello")
''',
            "should_fail": True,
            "reason": "Bare print() should be detected"
        },
    ]

    print("\n" + "="*80)
    print("QUOTE COUNTING ALGORITHM VERIFICATION")
    print("="*80)

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        result = check_handler_separation(test["code"])
        test_passed = result['passed']

        # Invert logic: if should_fail=True, we expect passed=False
        expected_pass = not test["should_fail"]

        if test_passed == expected_pass:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1

        print(f"\nTest {i}: {test['name']}")
        print(f"  Reason: {test['reason']}")
        print(f"  Expected: {'PASS' if expected_pass else 'FAIL (detect violation)'}")
        print(f"  Result: {'PASS' if test_passed else 'FAIL (detected violation)'}")
        print(f"  Message: {result['message']}")
        print(f"  Status: {status}")

    print("\n" + "="*80)
    print(f"RESULTS: {passed}/{len(test_cases)} tests passed, {failed} failed")
    print("="*80)

    return failed == 0


def test_edge_cases():
    """Test additional edge cases"""

    print("\n" + "="*80)
    print("EDGE CASE TESTING")
    print("="*80)

    edge_cases = [
        {
            "name": "Empty file",
            "code": "",
            "should_pass": True
        },
        {
            "name": "Only comments",
            "code": "# Just comments\n# console.print() here\n",
            "should_pass": True
        },
        {
            "name": "Only docstring",
            "code": '"""\nModule docstring\nconsole.print() mentioned\n"""\n',
            "should_pass": True
        },
        {
            "name": "Import statement",
            "code": "from cli.apps.modules import console\n",
            "should_pass": True
        },
        {
            "name": "CLI import in handler",
            "code": "from cli.apps.modules import console\nconsole.print('test')\n",
            "should_pass": False
        },
    ]

    passed = 0
    for test in edge_cases:
        result = check_handler_separation(test["code"])
        if result['passed'] == test['should_pass']:
            print(f"✓ {test['name']}: {result['message']}")
            passed += 1
        else:
            print(f"✗ {test['name']}: Expected {'PASS' if test['should_pass'] else 'FAIL'}, got {'PASS' if result['passed'] else 'FAIL'}")
            print(f"  Message: {result['message']}")

    print(f"\nEdge cases: {passed}/{len(edge_cases)} passed")
    return passed == len(edge_cases)


def test_false_positive_risks():
    """Test scenarios that could trigger false positives"""

    print("\n" + "="*80)
    print("FALSE POSITIVE RISK TESTING")
    print("="*80)

    false_positive_tests = [
        {
            "name": "Multi-line string with console.print",
            "code": '''
def foo():
    doc = """
    Example:
        console.print("Hello")
    """
''',
            "should_pass": True,
            "risk": "Triple-quoted strings must be properly tracked"
        },
        {
            "name": "Commented out console.print",
            "code": '''
def foo():
    # console.print("debug")
    pass
''',
            "should_pass": True,
            "risk": "Comments must be properly skipped"
        },
        {
            "name": "String with unbalanced quotes in comment",
            "code": '''
def foo():
    # Don't use print()
    x = "test"
''',
            "should_pass": True,
            "risk": "Comments with quotes should not affect quote counting"
        },
        {
            "name": "Dictionary with console.print key",
            "code": '''
def foo():
    patterns = {
        "console.print(": "display pattern",
    }
''',
            "should_pass": True,
            "risk": "Dictionary keys/values should be treated as strings"
        },
    ]

    passed = 0
    for test in false_positive_tests:
        result = check_handler_separation(test["code"])
        if result['passed'] == test['should_pass']:
            print(f"✓ {test['name']}: No false positive")
            print(f"  Risk mitigated: {test['risk']}")
            passed += 1
        else:
            print(f"✗ {test['name']}: FALSE POSITIVE DETECTED!")
            print(f"  Risk: {test['risk']}")
            print(f"  Message: {result['message']}")

    print(f"\nFalse positive tests: {passed}/{len(false_positive_tests)} passed")
    return passed == len(false_positive_tests)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CLI_CHECK.PY COMPREHENSIVE VERIFICATION")
    print("Testing quote counting fix and edge cases")
    print("="*80)

    all_passed = True

    # Run all test suites
    if not test_quote_counting():
        all_passed = False

    if not test_edge_cases():
        all_passed = False

    if not test_false_positive_risks():
        all_passed = False

    # Final summary
    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL TESTS PASSED - Quote counting algorithm verified")
        print("✓ No bugs found")
        print("✓ No false positive risks detected")
    else:
        print("✗ SOME TESTS FAILED - Review results above")
    print("="*80)

    sys.exit(0 if all_passed else 1)
