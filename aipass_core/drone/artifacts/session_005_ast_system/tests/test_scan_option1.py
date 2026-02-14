#!/usr/bin/env python3
"""
Option 1: Import & Introspect Detection
Actually imports the module and examines ArgumentParser in memory
"""

import sys
import importlib.util
import argparse
from pathlib import Path

def detect_commands_introspect(module_path: str) -> dict:
    """
    Import module and introspect ArgumentParser instance

    Returns:
        {
            'method': 'Import & Introspect',
            'commands': [{'name': str, 'help': str}, ...],
            'success': bool,
            'error': str | None
        }
    """
    result = {
        'method': 'Import & Introspect',
        'commands': [],
        'success': False,
        'error': None
    }

    try:
        # Load module dynamically
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        if not spec or not spec.loader:
            result['error'] = "Could not load module spec"
            return result

        module = importlib.util.module_from_spec(spec)

        # Temporarily capture the parser creation
        original_parser = argparse.ArgumentParser
        captured_parser = None

        def capture_parser(*args, **kwargs):
            nonlocal captured_parser
            captured_parser = original_parser(*args, **kwargs)
            return captured_parser

        # Monkey-patch ArgumentParser to capture instance
        argparse.ArgumentParser = capture_parser

        try:
            # Execute module to create parser
            spec.loader.exec_module(module)

            # Call main() if it exists to ensure parser is created
            if hasattr(module, 'main'):
                # Backup original sys.argv to avoid side effects
                original_argv = sys.argv
                sys.argv = [module_path]

                try:
                    # Try to get parser without full execution
                    # We just want the parser definition, not to run the program
                    pass
                except SystemExit:
                    # Expected - argparse calls sys.exit()
                    pass
                finally:
                    sys.argv = original_argv
        finally:
            # Restore original ArgumentParser
            argparse.ArgumentParser = original_parser

        if not captured_parser:
            result['error'] = "No ArgumentParser found in module"
            return result

        # Extract commands from parser
        commands = extract_commands_from_parser(captured_parser)

        result['commands'] = commands
        result['success'] = True

    except Exception as e:
        result['error'] = f"Exception: {str(e)}"

    return result

def extract_commands_from_parser(parser: argparse.ArgumentParser) -> list:
    """Extract command information from ArgumentParser instance"""
    commands = []

    # Check for subparsers
    if hasattr(parser, '_subparsers') and parser._subparsers:
        for action in parser._subparsers._actions:
            if isinstance(action, argparse._SubParsersAction):
                for choice, subparser in action.choices.items():
                    commands.append({
                        'name': choice,
                        'help': subparser.description or action.help or ''
                    })

    # Check for positional arguments with choices
    for action in parser._actions:
        if isinstance(action, argparse._StoreAction):
            if action.choices and action.dest != 'help':
                # This is a positional argument with choices
                for choice in action.choices:
                    commands.append({
                        'name': choice,
                        'help': action.help or ''
                    })

    return commands

def test_module(module_name: str, module_path: str):
    """Test a single module with introspection"""
    print(f"\n{'='*60}")
    print(f"Testing: {module_name}")
    print(f"Path: {module_path}")
    print(f"{'='*60}")

    result = detect_commands_introspect(module_path)

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
    print("OPTION 1: Import & Introspect Detection")
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
