#!/home/aipass/.venv/bin/python3

"""Comprehensive bug testing for imports_check.py"""

import sys
from pathlib import Path

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from seed.apps.handlers.standards.imports_check import (
    check_module,
    find_import_section_end,
    check_handler_independence
)

print("=" * 80)
print("BUG TEST SUITE FOR imports_check.py")
print("=" * 80)

# BUG 1: Handler independence not detecting violations
print("\n[BUG 1] Handler independence - path detection")
print("-" * 80)

# Create a proper handler file path
handler_test_file = '/home/aipass/seed/apps/handlers/test/violation.py'
Path(handler_test_file).parent.mkdir(parents=True, exist_ok=True)
with open(handler_test_file, 'w') as f:
    f.write('''#!/home/aipass/.venv/bin/python3

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from seed.apps.modules.bad_import import something  # SHOULD FAIL

def example():
    pass
''')

result = check_module(handler_test_file)
print(f"File: {handler_test_file}")
print(f"Result: {'PASS' if result['passed'] else 'FAIL'} - Score: {result['score']}")
for check in result['checks']:
    print(f"  {check['name']}: {'✓' if check['passed'] else '✗'} - {check['message']}")

handler_check = [c for c in result['checks'] if 'independence' in c['name'].lower()]
if handler_check:
    if handler_check[0]['passed']:
        print("❌ BUG CONFIRMED: Handler independence check failed to detect violation")
    else:
        print("✓ Handler independence correctly detected violation")
else:
    print("❌ BUG CONFIRMED: Handler independence check not run")

# BUG 2: Import section detection with docstrings
print("\n[BUG 2] Import section boundary - docstring imports")
print("-" * 80)

test_lines = [
    '#!/home/aipass/.venv/bin/python3',
    '',
    '"""',
    'Docstring with import example:',
    'from seed.apps.modules.bad_import import should_not_trigger',
    '"""',
    '',
    'import sys',
    'from pathlib import Path',
    '',
    'AIPASS_ROOT = Path.home() / "aipass_core"',
    'sys.path.insert(0, str(AIPASS_ROOT))',
    '',
    'from prax.apps.modules.logger import system_logger as logger',
    '',
    'def some_function():',
    '    """Function with import in docstring',
    '    from seed.apps.modules.another_bad import also_should_not_trigger',
    '    """',
    '    pass'
]

import_end = find_import_section_end(test_lines)
print(f"Import section ends at line: {import_end}")
print(f"Line content: '{test_lines[import_end] if import_end < len(test_lines) else 'EOF'}'")

if import_end == 16:  # Should stop at 'def some_function():'
    print("✓ Correctly identifies import section end")
else:
    print(f"❌ BUG: Expected line 16 (def some_function), got line {import_end}")

# BUG 3: Triple-quoted string with imports
print("\n[BUG 3] Triple-quoted strings with import patterns")
print("-" * 80)

string_test_file = '/home/aipass/seed/apps/handlers/test/string_test.py'
with open(string_test_file, 'w') as f:
    f.write('''#!/home/aipass/.venv/bin/python3

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

def example():
    code = """
    from seed.apps.modules.bad_import import something
    """
    return code
''')

result = check_module(string_test_file)
print(f"File: {string_test_file}")
print(f"Result: {'PASS' if result['passed'] else 'FAIL'} - Score: {result['score']}")

handler_check = [c for c in result['checks'] if 'independence' in c['name'].lower()]
if handler_check and handler_check[0]['passed']:
    print("✓ Correctly ignored import in string literal")
elif handler_check and not handler_check[0]['passed']:
    print("❌ BUG: False positive - detected import inside string literal")
else:
    print("⚠️  Handler independence check not run")

# BUG 4: Import order detection edge case
print("\n[BUG 4] Import order - checking actual import section only")
print("-" * 80)

order_test_file = '/home/aipass/seed/apps/handlers/test/order_test.py'
with open(order_test_file, 'w') as f:
    f.write('''#!/home/aipass/.venv/bin/python3

"""
Example showing import order:
from seed.apps.handlers.json import json_handler
from prax.apps.modules.logger import system_logger as logger
"""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from seed.apps.handlers.json import json_handler

def example():
    pass
''')

result = check_module(order_test_file)
print(f"File: {order_test_file}")
print(f"Result: {'PASS' if result['passed'] else 'FAIL'} - Score: {result['score']}")

order_check = [c for c in result['checks'] if 'order' in c['name'].lower()]
if order_check and order_check[0]['passed']:
    print("✓ Correctly validated import order (ignored docstring)")
elif order_check and not order_check[0]['passed']:
    print("❌ BUG: False positive from import pattern in docstring")
else:
    print("⚠️  Import order check not run")

# BUG 5: Check handler independence logic directly
print("\n[BUG 5] Handler independence - direct function test")
print("-" * 80)

test_import_lines = [
    'import sys',
    'from pathlib import Path',
    'AIPASS_ROOT = Path.home() / "aipass_core"',
    'sys.path.insert(0, str(AIPASS_ROOT))',
    'from prax.apps.modules.logger import system_logger as logger',
    'from seed.apps.modules.bad_import import something',
    'def example():',
    '    pass'
]

result = check_handler_independence(
    test_import_lines,
    '/home/aipass/seed/apps/handlers/standards/test.py'
)

print(f"Module path: /home/aipass/seed/apps/handlers/standards/test.py")
print(f"Parent branch detected: seed")
print(f"Import line: 'from seed.apps.modules.bad_import import something'")
print(f"Result: {result}")

if result['passed']:
    print("❌ BUG CONFIRMED: Should have detected violation but passed")
else:
    print("✓ Correctly detected handler importing from parent module")

# BUG 6: Comments with inline code
print("\n[BUG 6] Inline comments with import patterns")
print("-" * 80)

comment_test_file = '/home/aipass/seed/apps/handlers/test/comment_test.py'
with open(comment_test_file, 'w') as f:
    f.write('''#!/home/aipass/.venv/bin/python3

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
# from seed.apps.modules.bad_import import something  # Should be ignored

def example():
    pass
''')

result = check_module(comment_test_file)
print(f"File: {comment_test_file}")
print(f"Result: {'PASS' if result['passed'] else 'FAIL'} - Score: {result['score']}")

handler_check = [c for c in result['checks'] if 'independence' in c['name'].lower()]
if handler_check and handler_check[0]['passed']:
    print("✓ Correctly ignored import in comment")
elif handler_check and not handler_check[0]['passed']:
    print("❌ BUG: False positive - detected commented import")
else:
    print("⚠️  Handler independence check not run")

# SUMMARY
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("[BUG 1] Handler independence detection: TESTING")
print("[BUG 2] Import section boundary detection: TESTED")
print("[BUG 3] Triple-quoted string false positives: TESTED")
print("[BUG 4] Import order with docstrings: TESTED")
print("[BUG 5] Direct handler independence function: TESTED")
print("[BUG 6] Inline comment detection: TESTED")
print("=" * 80)
