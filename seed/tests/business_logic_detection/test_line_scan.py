#!/home/aipass/.venv/bin/python3
"""
Line-scanning approach to detect business logic (hardcoded data structures)
in Python modules.

Strategy:
- Read file line by line
- Track docstring state to avoid false positives
- Detect module-level (no indentation) variable assignments to [ or {
- Check if next line contains data (not just closing bracket) = multi-line structure
- Skip ALL_CAPS constants (debatable, but common Python convention)
- Skip empty structures
"""

from pathlib import Path
import re


def detect_business_logic_line_scan(file_path: Path) -> list:
    """
    Detect hardcoded data structures at module level using line scanning.

    Args:
        file_path: Path to Python file to analyze

    Returns:
        List of violations, each dict with: line_num, variable_name, type
    """
    violations = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_docstring = False
    docstring_delimiter = None

    for i, line in enumerate(lines, start=1):
        # Track docstring state
        if '"""' in line or "'''" in line:
            delimiter = '"""' if '"""' in line else "'''"
            count = line.count(delimiter)

            if not in_docstring:
                # Starting a docstring
                if count == 1:
                    in_docstring = True
                    docstring_delimiter = delimiter
                # elif count == 2: it's a one-line docstring, stays False
            else:
                # Ending a docstring (if same delimiter)
                if delimiter == docstring_delimiter:
                    if count >= 1:
                        in_docstring = False
                        docstring_delimiter = None

        # Skip if we're inside a docstring
        if in_docstring:
            continue

        # Skip comments and empty lines
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Check if line is indented (function/class scope)
        if line[0] in (' ', '\t'):
            continue

        # Check for module-level variable assignment to list or dict
        # Pattern: variable_name = [ or variable_name = {
        match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[\[\{]', line)

        if not match:
            continue

        variable_name = match.group(1)
        structure_type = 'list' if '[' in line else 'dict'

        # Skip ALL_CAPS constants (Python convention for constants)
        if variable_name.isupper():
            continue

        # Check if it's empty structure on same line: var = [] or var = {}
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[\[\{]\s*[\]\}]', line):
            # Empty structure - skip
            continue

        # Check if structure closes on same line (single-line)
        if (structure_type == 'list' and ']' in line) or \
           (structure_type == 'dict' and '}' in line):
            # Single-line structure - might be OK or might be compact data
            # Check if it contains actual data
            if structure_type == 'list':
                # Extract content between [ and ]
                content = line[line.find('['):line.find(']')+1]
                # If contains comma or quotes, it has data
                if ',' in content or '"' in content or "'" in content:
                    violations.append({
                        'line_num': i,
                        'variable_name': variable_name,
                        'type': structure_type,
                        'severity': 'single-line'
                    })
            elif structure_type == 'dict':
                content = line[line.find('{'):line.find('}')+1]
                if ':' in content:
                    violations.append({
                        'line_num': i,
                        'variable_name': variable_name,
                        'type': structure_type,
                        'severity': 'single-line'
                    })
            continue

        # Multi-line structure - check next line
        if i < len(lines):
            next_line = lines[i].strip()  # lines[i] because enumerate starts at 1

            # If next line is closing bracket, it's empty
            if next_line in [']', '}', '],', '},']:
                continue

            # If next line has content, it's a multi-line data structure
            if next_line and not next_line.startswith('#'):
                violations.append({
                    'line_num': i,
                    'variable_name': variable_name,
                    'type': structure_type,
                    'severity': 'multi-line'
                })

    return violations


def run_tests():
    """Run line scanning detection on all test files."""

    test_dir = Path('/home/aipass/seed/tests/business_logic_detection')

    test_files = {
        'sample_violation_list.py': {
            'expected': 'FAIL',
            'reason': 'Has hardcoded list at module level'
        },
        'sample_violation_dict.py': {
            'expected': 'FAIL',
            'reason': 'Has hardcoded dicts at module level'
        },
        'sample_clean.py': {
            'expected': 'PASS',
            'reason': 'Clean orchestration, only simple constants'
        },
        'sample_edge_function_scope.py': {
            'expected': 'PASS',
            'reason': 'Data is inside function (local scope)'
        },
        'sample_edge_constants.py': {
            'expected': 'PASS',
            'reason': 'ALL_CAPS constants (Python convention)'
        },
        'sample_edge_empty.py': {
            'expected': 'PASS',
            'reason': 'Empty structures only'
        }
    }

    results = []

    print("=" * 80)
    print("BUSINESS LOGIC DETECTION - LINE SCANNING APPROACH")
    print("=" * 80)
    print()

    for filename, expected_info in test_files.items():
        file_path = test_dir / filename

        if not file_path.exists():
            print(f"❌ MISSING: {filename}")
            continue

        violations = detect_business_logic_line_scan(file_path)

        expected = expected_info['expected']
        actual = 'FAIL' if violations else 'PASS'
        match = '✓' if expected == actual else '✗'

        results.append({
            'file': filename,
            'expected': expected,
            'actual': actual,
            'match': match,
            'violations': len(violations),
            'details': violations
        })

        print(f"{match} {filename}")
        print(f"   Expected: {expected} | Actual: {actual} | Violations: {len(violations)}")

        if violations:
            for v in violations:
                print(f"   → Line {v['line_num']}: {v['variable_name']} ({v['type']}, {v['severity']})")

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    correct = sum(1 for r in results if r['match'] == '✓')

    print(f"Total tests: {total}")
    print(f"Correct: {correct}")
    print(f"Incorrect: {total - correct}")
    print(f"Accuracy: {correct/total*100:.1f}%")
    print()

    return results


if __name__ == '__main__':
    results = run_tests()
