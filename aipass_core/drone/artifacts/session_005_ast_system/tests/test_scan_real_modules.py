#!/usr/bin/env python3
"""
Test scan_module() with real AIPass modules
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from drone_discovery import scan_module

def test_module(module_name: str, module_path: str):
    """Test scanning a real module"""
    print(f"\n{'='*70}")
    print(f"Testing: {module_name}")
    print(f"Path: {module_path}")
    print(f"{'='*70}")

    result = scan_module(module_path)

    print(f"Success: {result['success']}")

    if result['error']:
        print(f"❌ Error: {result['error']}")
        return False

    if result['notes']:
        print("\nNotes:")
        for note in result['notes']:
            print(f"  ℹ️  {note}")

    if result['commands']:
        print(f"\n✅ Commands found: {len(result['commands'])}")
        for i, cmd in enumerate(result['commands'], 1):
            help_preview = cmd['help'][:60] + '...' if len(cmd['help']) > 60 else cmd['help']
            print(f"  {chr(96+i)}. {cmd['name']}")
            if cmd['help']:
                print(f"     {help_preview}")
    else:
        print("⚠️  No commands found")

    return result['success']

if __name__ == '__main__':
    print("="*70)
    print("REAL MODULE TESTING: scan_module() with AIPass modules")
    print("="*70)

    # Get ecosystem root
    drone_dir = Path(__file__).parent.parent
    ecosystem_root = drone_dir.parent

    # Test modules
    tests = [
        ('backup_cli.py', ecosystem_root / 'backup_system' / 'backup_cli.py'),
        ('flow_plan.py', ecosystem_root / 'flow' / 'flow_plan.py'),
    ]

    results = []
    for name, path in tests:
        if path.exists():
            success = test_module(name, str(path))
            results.append((name, success))
        else:
            print(f"\n⚠️  Skipping {name} - file not found: {path}")
            results.append((name, False))

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    pass_count = sum(1 for _, s in results if s)
    print(f"\nTotal: {pass_count}/{len(results)} passed")
