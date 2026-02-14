#!/usr/bin/env python3
"""
Test scan_module() with our known-working test modules
"""

import sys
from pathlib import Path

# Add drone directory to path
drone_dir = Path(__file__).parent.parent
sys.path.insert(0, str(drone_dir.parent))  # ecosystem root for prax import
sys.path.insert(0, str(drone_dir))          # drone directory

from drone_discovery import scan_module

def test_known_module(name: str, path: str):
    """Test a module we know should work"""
    print(f"\nTesting: {name}")
    print(f"Path: {path}")

    result = scan_module(path)

    print(f"Success: {result['success']}")
    print(f"Commands found: {len(result['commands'])}")

    if result['commands']:
        for cmd in result['commands']:
            help_text = cmd['help'][:50] if cmd['help'] else '(no help)'
            print(f"  - {cmd['name']}: {help_text}")

    if result['error']:
        print(f"Error: {result['error']}")

    return result['success'] and len(result['commands']) > 0

if __name__ == '__main__':
    print("="*70)
    print("Testing scan_module() with known-working test modules")
    print("="*70)

    test_dir = Path(__file__).parent / 'test_modules'

    tests = [
        ('subparsers.py', test_dir / 'subparsers.py'),
        ('choices.py', test_dir / 'choices.py'),
        ('simple_positional.py', test_dir / 'simple_positional.py'),
        ('adversarial_nested.py', test_dir / 'adversarial_nested.py'),
        ('adversarial_edge_cases.py', test_dir / 'adversarial_edge_cases.py'),
    ]

    results = []
    for name, path in tests:
        success = test_known_module(name, str(path))
        results.append((name, success))

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    pass_count = sum(1 for _, s in results if s)
    print(f"\nTotal: {pass_count}/{len(results)} passed")
