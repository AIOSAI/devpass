#!/home/aipass/.venv/bin/python3
"""
Hybrid Business Logic Detector
Combines line scanning (fast pattern detection) with AST (accurate verification)
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple


class BusinessLogicViolation:
    """Represents a detected violation"""
    def __init__(self, file_path: str, line_number: int, var_name: str,
                 var_type: str, element_count: int):
        self.file_path = file_path
        self.line_number = line_number
        self.var_name = var_name
        self.var_type = var_type  # 'list' or 'dict'
        self.element_count = element_count

    def __repr__(self):
        return (f"Violation(line={self.line_number}, var='{self.var_name}', "
                f"type={self.var_type}, count={self.element_count})")


class HybridDetector:
    """Two-phase detection: line scan + AST verification"""

    def __init__(self):
        # Phase 1: Line scan patterns
        # Match: lowercase_var = [ or lowercase_var = {
        # Skip: ALL_CAPS_VAR = [ (constants)
        self.list_pattern = re.compile(r'^\s*([a-z][a-z0-9_]*)\s*=\s*\[')
        self.dict_pattern = re.compile(r'^\s*([a-z][a-z0-9_]*)\s*=\s*\{')

    def detect(self, file_path: Path) -> List[BusinessLogicViolation]:
        """Run hybrid detection on a file"""
        violations = []

        # Phase 1: Quick line scan to find candidates
        candidates = self._line_scan_phase(file_path)

        if not candidates:
            return violations  # No candidates found

        # Phase 2: AST verification
        violations = self._ast_verification_phase(file_path, candidates)

        return violations

    def _line_scan_phase(self, file_path: Path) -> Dict[str, int]:
        """
        Phase 1: Quick line scan
        Returns: {var_name: line_number} dict of candidates
        """
        candidates = {}

        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, start=1):
                    # Check for list assignment
                    match = self.list_pattern.match(line)
                    if match:
                        var_name = match.group(1)
                        candidates[var_name] = line_num
                        continue

                    # Check for dict assignment
                    match = self.dict_pattern.match(line)
                    if match:
                        var_name = match.group(1)
                        candidates[var_name] = line_num

        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return {}

        return candidates

    def _ast_verification_phase(self, file_path: Path,
                                 candidates: Dict[str, int]) -> List[BusinessLogicViolation]:
        """
        Phase 2: AST verification
        Verify candidates are:
        1. At module level (not in function)
        2. Not empty structures
        3. Not ALL_CAPS (constants)
        4. Actually contain data
        """
        violations = []

        try:
            with open(file_path, 'r') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))

            # Walk only module-level assignments
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    # Check if this is module-level
                    if not self._is_module_level(node, tree):
                        continue

                    # Get variable name
                    if not isinstance(node.targets[0], ast.Name):
                        continue

                    var_name = node.targets[0].id

                    # Only check candidates found in phase 1
                    if var_name not in candidates:
                        continue

                    # Filter: Skip ALL_CAPS (constants)
                    if var_name.isupper():
                        continue

                    # Check if it's a list or dict
                    value = node.value
                    var_type = None
                    element_count = 0

                    if isinstance(value, ast.List):
                        var_type = 'list'
                        element_count = len(value.elts)
                    elif isinstance(value, ast.Dict):
                        var_type = 'dict'
                        element_count = len(value.keys)
                    else:
                        continue  # Not a list or dict

                    # Filter: Skip empty structures
                    if element_count == 0:
                        continue

                    # Filter: Skip single-element structures (might be placeholders)
                    # Actually, let's flag them - user can decide

                    # This is a confirmed violation
                    violation = BusinessLogicViolation(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        var_name=var_name,
                        var_type=var_type,
                        element_count=element_count
                    )
                    violations.append(violation)

        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

        return violations

    def _is_module_level(self, node: ast.AST, tree: ast.Module) -> bool:
        """Check if a node is at module level (not inside a function/class)"""
        # Simple check: if node is directly in tree.body, it's module-level
        for item in tree.body:
            if item is node:
                return True
            # Also check if it's the same line number (for assignments)
            if hasattr(item, 'lineno') and hasattr(node, 'lineno'):
                if item.lineno == node.lineno:
                    return True
        return False


def run_tests():
    """Test the hybrid detector on all sample files"""

    test_dir = Path("/home/aipass/seed/tests/business_logic_detection")

    # Test files and expected results
    test_cases = [
        ("sample_violation_list.py", True, "Has hardcoded list"),
        ("sample_violation_dict.py", True, "Has hardcoded dicts"),
        ("sample_clean.py", False, "Clean orchestration module"),
        ("sample_edge_function_scope.py", False, "Data inside function - EDGE CASE"),
        ("sample_edge_constants.py", False, "ALL_CAPS constants - EDGE CASE"),
        ("sample_edge_empty.py", False, "Empty structures - EDGE CASE"),
    ]

    detector = HybridDetector()
    results = []

    print("=" * 80)
    print("HYBRID BUSINESS LOGIC DETECTION TEST")
    print("=" * 80)
    print()

    for filename, should_fail, description in test_cases:
        file_path = test_dir / filename

        if not file_path.exists():
            print(f"⚠️  SKIP: {filename} - File not found")
            results.append({
                'file': filename,
                'expected': 'FAIL' if should_fail else 'PASS',
                'actual': 'SKIP',
                'status': '⚠️  SKIP',
                'violations': [],
                'description': description
            })
            continue

        violations = detector.detect(file_path)

        # Determine pass/fail
        has_violations = len(violations) > 0
        expected_result = 'FAIL' if should_fail else 'PASS'
        actual_result = 'FAIL' if has_violations else 'PASS'

        # Check if test passed
        test_passed = (expected_result == actual_result)
        status = '✓ PASS' if test_passed else '✗ FAIL'

        results.append({
            'file': filename,
            'expected': expected_result,
            'actual': actual_result,
            'status': status,
            'violations': violations,
            'description': description
        })

        # Print results
        print(f"File: {filename}")
        print(f"  Description: {description}")
        print(f"  Expected: {expected_result} | Actual: {actual_result} | {status}")

        if violations:
            print(f"  Violations found: {len(violations)}")
            for v in violations:
                print(f"    - Line {v.line_number}: {v.var_name} ({v.var_type}, {v.element_count} elements)")
        else:
            print(f"  No violations found")

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for r in results if '✓' in r['status'])
    failed = sum(1 for r in results if '✗' in r['status'])
    skipped = sum(1 for r in results if '⚠️' in r['status'])

    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print()

    # Results table
    print("=" * 80)
    print("RESULTS TABLE")
    print("=" * 80)
    print(f"{'File':<40} {'Expected':<10} {'Actual':<10} {'Status':<10}")
    print("-" * 80)

    for r in results:
        print(f"{r['file']:<40} {r['expected']:<10} {r['actual']:<10} {r['status']:<10}")

    print("=" * 80)

    return results


def analyze_hybrid_approach():
    """Analyze the hybrid approach - pros, cons, trade-offs"""

    analysis = """

HYBRID APPROACH ANALYSIS
========================

## Approach Overview

The hybrid detector uses a two-phase process:

1. **Phase 1: Line Scanning (Fast Pattern Detection)**
   - Uses regex to quickly scan file line-by-line
   - Looks for patterns: `lowercase_var = [` or `lowercase_var = {`
   - Fast but imprecise - just finds candidates
   - No parsing overhead for clean files

2. **Phase 2: AST Verification (Accurate Analysis)**
   - Only runs if Phase 1 found candidates
   - Parses file with AST to verify violations
   - Checks: module-level, not ALL_CAPS, not empty, element count
   - Provides accurate line numbers and metadata

## Advantages

1. **Performance**: Line scan is fast, only parse if needed
2. **Accuracy**: AST confirms violations, eliminates false positives
3. **Context-aware**: AST knows module vs function scope
4. **Detailed info**: Can count elements, get exact line numbers
5. **Extensible**: Easy to add filters (ALL_CAPS, empty, etc.)

## Disadvantages

1. **Complexity**: Two phases means more code
2. **Edge cases**: Some patterns might slip through line scan
3. **Maintenance**: Changes need updates in both phases
4. **False negatives**: If line scan misses pattern, AST never runs

## Trade-offs

**vs. Pure Line Scanning:**
- Hybrid: More accurate, fewer false positives
- Line-only: Faster, simpler, but less reliable

**vs. Pure AST:**
- Hybrid: Faster on clean files (no parsing needed)
- AST-only: Simpler code, but slower on large codebases

## Recommended Use Cases

**Use Hybrid When:**
- Need high accuracy with good performance
- Working with large codebases
- Want detailed violation metadata
- Edge cases matter (constants, function scope)

**Use Pure Line Scan When:**
- Speed is critical
- False positives are acceptable
- Simple patterns are sufficient

**Use Pure AST When:**
- Codebase is small
- Need 100% pattern coverage
- Complex code structures to analyze

## Verdict

The hybrid approach offers the **best balance** for AIPass:
- Fast enough for real-time linting
- Accurate enough to avoid false positives
- Flexible enough to handle edge cases
- Detailed enough for useful error messages

**Recommendation**: Use hybrid approach as the standard detector.
"""

    return analysis


if __name__ == "__main__":
    # Run tests
    results = run_tests()

    # Write results to markdown
    output_file = Path("/home/aipass/seed/tests/business_logic_detection/results_hybrid.md")

    with open(output_file, 'w') as f:
        f.write("# Hybrid Business Logic Detection - Test Results\n\n")
        f.write("**Date:** 2025-11-25\n")
        f.write("**Detector:** Hybrid (Line Scan + AST)\n\n")

        # Test results
        f.write("## Test Results\n\n")
        f.write("| File | Expected | Actual | Status | Description |\n")
        f.write("|------|----------|--------|--------|-------------|\n")

        for r in results:
            f.write(f"| {r['file']} | {r['expected']} | {r['actual']} | "
                   f"{r['status']} | {r['description']} |\n")

        f.write("\n## Detailed Violations\n\n")

        for r in results:
            if r['violations']:
                f.write(f"### {r['file']}\n\n")
                for v in r['violations']:
                    f.write(f"- **Line {v.line_number}**: `{v.var_name}` "
                           f"({v.var_type}, {v.element_count} elements)\n")
                f.write("\n")

        # Analysis
        f.write(analyze_hybrid_approach())

        # Detection code
        f.write("\n## Detection Code\n\n")
        f.write("```python\n")
        with open(__file__, 'r') as source:
            f.write(source.read())
        f.write("\n```\n")

    print(f"\nResults written to: {output_file}")
