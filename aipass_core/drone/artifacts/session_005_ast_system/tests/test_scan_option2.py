#!/usr/bin/env python3
"""
Option 2: AST Parsing Detection
Parses Python code as Abstract Syntax Tree without execution
"""

import ast
from pathlib import Path

def detect_commands_ast(module_path: str) -> dict:
    """
    Parse module as AST and extract argparse patterns

    Returns:
        {
            'method': 'AST Parsing',
            'commands': [{'name': str, 'help': str}, ...],
            'success': bool,
            'error': str | None
        }
    """
    result = {
        'method': 'AST Parsing',
        'commands': [],
        'success': False,
        'error': None
    }

    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source)

        # Walk the AST looking for argparse patterns
        commands = []

        for node in ast.walk(tree):
            # Look for add_parser() calls (subparsers pattern)
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'add_parser'):
                    # Found subparser.add_parser('command', help='...')
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

    # First positional arg is the command name
    cmd_name = None
    if isinstance(node.args[0], ast.Constant):
        cmd_name = node.args[0].value

    if not cmd_name:
        return None

    # Look for help keyword argument
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

    # Look for choices keyword argument
    choices = None
    for keyword in node.keywords:
        if keyword.arg == 'choices':
            if isinstance(keyword.value, ast.List):
                # choices=['a', 'b', 'c']
                choices = []
                for elt in keyword.value.elts:
                    if isinstance(elt, ast.Constant):
                        choices.append(elt.value)

    if not choices:
        return []

    # Look for help text
    help_text = ''
    for keyword in node.keywords:
        if keyword.arg == 'help' and isinstance(keyword.value, ast.Constant):
            help_text = keyword.value.value

    # Create command entry for each choice
    for choice in choices:
        commands.append({
            'name': choice,
            'help': help_text
        })

    return commands

def test_module(module_name: str, module_path: str):
    """Test a single module with AST parsing"""
    print(f"\n{'='*60}")
    print(f"Testing: {module_name}")
    print(f"Path: {module_path}")
    print(f"{'='*60}")

    result = detect_commands_ast(module_path)

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
    print("OPTION 2: AST Parsing Detection")
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
