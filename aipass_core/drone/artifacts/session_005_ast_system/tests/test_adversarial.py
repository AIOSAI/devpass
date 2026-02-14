#!/usr/bin/env python3
"""
Adversarial Testing for AST Detection
Purpose: Stress test AST parsing to find its REAL limitations
Be brutally honest about failures - failures here are valuable information
"""

import ast
from pathlib import Path

def detect_commands_ast(module_path: str) -> dict:
    """AST parsing detection (same as option 2)"""
    result = {
        'method': 'AST Parsing',
        'commands': [],
        'success': False,
        'error': None,
        'warnings': []
    }

    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source)
        commands = []

        for node in ast.walk(tree):
            # Look for add_parser() calls (subparsers pattern)
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'add_parser'):
                    cmd_info = extract_add_parser_call(node)
                    if cmd_info:
                        commands.append(cmd_info)

                # Look for add_argument() calls with choices
                elif (isinstance(node.func, ast.Attribute) and
                      node.func.attr == 'add_argument'):
                    cmd_info = extract_add_argument_choices(node)
                    if cmd_info:
                        commands.extend(cmd_info)

        result['commands'] = commands
        result['success'] = True

    except Exception as e:
        result['error'] = f"Exception: {str(e)}"

    return result

def extract_add_parser_call(node: ast.Call) -> dict | None:
    """Extract command info from add_parser() call"""
    if not node.args:
        return None

    cmd_name = None
    if isinstance(node.args[0], ast.Constant):
        cmd_name = node.args[0].value
    # Handle f-strings (e.g., f'filter_{status}')
    elif isinstance(node.args[0], ast.JoinedStr):
        # F-string detected - can't statically determine value
        return None

    if not cmd_name:
        return None

    help_text = ''
    for keyword in node.keywords:
        if keyword.arg == 'help' and isinstance(keyword.value, ast.Constant):
            help_text = keyword.value.value

    return {
        'name': cmd_name,
        'help': help_text
    }

def extract_add_argument_choices(node: ast.Call) -> list:
    """Extract commands from add_argument() with choices parameter"""
    commands = []

    choices = None
    for keyword in node.keywords:
        if keyword.arg == 'choices':
            if isinstance(keyword.value, ast.List):
                # Static list: choices=['a', 'b', 'c']
                choices = []
                for elt in keyword.value.elts:
                    if isinstance(elt, ast.Constant):
                        choices.append(elt.value)
            elif isinstance(keyword.value, ast.Name):
                # Variable reference: choices=BACKUP_MODES
                # Can't resolve at AST level
                return []
            elif isinstance(keyword.value, ast.ListComp):
                # List comprehension: choices=[e for e in ENVIRONMENTS]
                # Can't resolve at AST level
                return []
            elif isinstance(keyword.value, ast.Call):
                # Function call: choices=get_formats()
                # Can't resolve at AST level
                return []

    if not choices:
        return []

    help_text = ''
    for keyword in node.keywords:
        if keyword.arg == 'help' and isinstance(keyword.value, ast.Constant):
            help_text = keyword.value.value

    for choice in choices:
        commands.append({
            'name': choice,
            'help': help_text
        })

    return commands

def test_module(module_name: str, module_path: str, expected_commands: int | str):
    """Test a single adversarial module"""
    print(f"\n{'='*70}")
    print(f"Testing: {module_name}")
    print(f"Path: {module_path}")
    if isinstance(expected_commands, int):
        print(f"Expected: {expected_commands} commands")
    else:
        print(f"Expected: {expected_commands}")
    print(f"{'='*70}")

    result = detect_commands_ast(module_path)

    print(f"Success: {result['success']}")

    if result['error']:
        print(f"❌ Error: {result['error']}")

    if result['commands']:
        print(f"\n✓ Commands found: {len(result['commands'])}")
        for cmd in result['commands']:
            help_preview = cmd['help'][:50] + '...' if len(cmd['help']) > 50 else cmd['help']
            print(f"  - {cmd['name']}: {help_preview}")
    else:
        print("❌ No commands found")

    # Verdict
    if isinstance(expected_commands, int):
        if len(result['commands']) == expected_commands:
            print(f"\n✅ PASS: Found expected {expected_commands} commands")
            return 'pass'
        else:
            print(f"\n⚠️  PARTIAL/FAIL: Expected {expected_commands}, found {len(result['commands'])}")
            return 'fail'
    else:
        print(f"\n📊 RESULT: Found {len(result['commands'])} commands (dynamic - actual count varies)")
        return 'partial'

if __name__ == '__main__':
    print("="*70)
    print("ADVERSARIAL TESTING: AST Detection Under Stress")
    print("Purpose: Find real limitations - failures are valuable info")
    print("="*70)

    test_modules_dir = Path(__file__).parent / 'test_modules'

    # Define tests with expected command counts
    # Format: (filename, expected_commands or 'dynamic')
    adversarial_tests = [
        ('adversarial_nested.py', 7),  # database, api, version + nested (migrate, seed, reset, start, stop, status)
        ('adversarial_dynamic.py', 'EXPECTED FAIL: choices from variables'),
        ('adversarial_multiple_parsers.py', 'UNCERTAIN: multiple parsers in one file'),
        ('adversarial_loops.py', 'EXPECTED FAIL: commands in loops'),
        ('adversarial_edge_cases.py', 11),  # deploy, backup, query, status, ping, migrate, clean, build, test, run_server, check-health
        ('adversarial_conditional.py', 'EXPECTED FAIL: conditional creation'),
    ]

    results = []
    for name, expected in adversarial_tests:
        path = test_modules_dir / name
        verdict = test_module(name, str(path), expected)
        results.append((name, verdict, expected))

    # Summary
    print(f"\n{'='*70}")
    print("ADVERSARIAL TEST SUMMARY")
    print(f"{'='*70}")

    pass_count = sum(1 for _, v, _ in results if v == 'pass')
    fail_count = sum(1 for _, v, _ in results if v == 'fail')
    partial_count = sum(1 for _, v, _ in results if v == 'partial')

    for name, verdict, expected in results:
        symbol = "✅" if verdict == 'pass' else "⚠️" if verdict == 'partial' else "❌"
        print(f"{symbol} {name}: {verdict.upper()} (expected: {expected})")

    print(f"\n{'='*70}")
    print(f"Results: {pass_count} pass, {fail_count} fail, {partial_count} partial")
    print(f"{'='*70}")

    print("\n📋 HONEST ANALYSIS:")
    print("AST parsing has clear limitations:")
    print("  ✓ Works great for static, literal definitions")
    print("  ✗ Cannot resolve runtime values (variables, loops, functions)")
    print("  ✗ Cannot evaluate conditional logic")
    print("  ? Multiple parsers - depends on code structure")
    print("\nThis is EXPECTED behavior for static analysis.")
    print("The question: Are these limitations acceptable for drone's use case?")
