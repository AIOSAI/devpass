#!/usr/bin/env python3
"""
Option 3: Regex Pattern Matching Detection
Searches for common argparse patterns using regex
"""

import re
from pathlib import Path

def detect_commands_regex(module_path: str) -> dict:
    """
    Search for argparse patterns using regex

    Returns:
        {
            'method': 'Regex Matching',
            'commands': [{'name': str, 'help': str}, ...],
            'success': bool,
            'error': str | None
        }
    """
    result = {
        'method': 'Regex Matching',
        'commands': [],
        'success': False,
        'error': None
    }

    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            source = f.read()

        commands = []

        # Pattern 1: subparsers.add_parser('command', help='...')
        # Matches: add_parser('create', help='Create a new item')
        pattern1 = r"add_parser\s*\(\s*['\"](\w+)['\"](?:.*?help\s*=\s*['\"]([^'\"]*)['\"])?"
        for match in re.finditer(pattern1, source, re.DOTALL):
            cmd_name = match.group(1)
            help_text = match.group(2) if match.group(2) else ''
            commands.append({
                'name': cmd_name,
                'help': help_text
            })

        # Pattern 2: add_argument('arg', choices=['a', 'b', 'c'])
        # Matches: add_argument('mode', choices=['snapshot', 'versioned'])
        pattern2 = r"add_argument\s*\(\s*['\"](\w+)['\"].*?choices\s*=\s*\[(.*?)\]"
        for match in re.finditer(pattern2, source, re.DOTALL):
            arg_name = match.group(1)
            choices_str = match.group(2)

            # Extract individual choices
            choices = re.findall(r"['\"](\w+)['\"]", choices_str)

            # Try to find help text for this argument
            help_pattern = rf"add_argument\s*\(\s*['\"]({arg_name})['\"].*?help\s*=\s*['\"]([^'\"]*)['\"]"
            help_match = re.search(help_pattern, source, re.DOTALL)
            help_text = help_match.group(2) if help_match and help_match.group(2) else ''

            for choice in choices:
                commands.append({
                    'name': choice,
                    'help': help_text
                })

        # Pattern 3: Positional with choices (unnamed)
        # Matches: parser.add_argument('command', choices=['start', 'stop'])
        # This might overlap with Pattern 2, but we'll deduplicate

        # Remove duplicates based on command name
        seen = set()
        unique_commands = []
        for cmd in commands:
            if cmd['name'] not in seen:
                seen.add(cmd['name'])
                unique_commands.append(cmd)

        result['commands'] = unique_commands
        result['success'] = True

    except Exception as e:
        result['error'] = f"Exception: {str(e)}"

    return result

def test_module(module_name: str, module_path: str):
    """Test a single module with regex matching"""
    print(f"\n{'='*60}")
    print(f"Testing: {module_name}")
    print(f"Path: {module_path}")
    print(f"{'='*60}")

    result = detect_commands_regex(module_path)

    print(f"Method: {result['method']}")
    print(f"Success: {result['success']}")

    if result['error']:
        print(f"Error: {result['error']}")

    if result['commands']:
        print(f"\nCommands found: {len(result['commands'])}")
        for cmd in result['commands']:
            print(f"  - {cmd['name']}: {cmd['help']}")
    else:
        print("No commands found")

    return result

if __name__ == '__main__':
    print("="*60)
    print("OPTION 3: Regex Pattern Matching Detection")
    print("="*60)

    test_modules_dir = Path(__file__).parent / 'test_modules'

    modules = [
        ('simple_positional.py', test_modules_dir / 'simple_positional.py'),
        ('subparsers.py', test_modules_dir / 'subparsers.py'),
        ('choices.py', test_modules_dir / 'choices.py'),
        ('mixed_pattern.py', test_modules_dir / 'mixed_pattern.py'),
    ]

    results = []
    for name, path in modules:
        result = test_module(name, str(path))
        results.append((name, result))

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    for name, result in results:
        status = "✓" if result['success'] else "✗"
        cmd_count = len(result['commands']) if result['success'] else 0
        print(f"{status} {name}: {cmd_count} commands")
        if result['error']:
            print(f"  Error: {result['error']}")
