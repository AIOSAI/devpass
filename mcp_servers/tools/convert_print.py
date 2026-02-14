#!/usr/bin/env python3
"""
Convert all print() statements to console.print() in AIPass apps/
"""

import re
from pathlib import Path

def add_rich_import(content):
    """Add Rich console import if not present."""
    if 'from rich.console import Console' not in content:
        # Find the right place to add the import
        lines = content.split('\n')
        import_index = -1

        # Look for the last standard library or typing import before internal imports
        for i, line in enumerate(lines):
            if line.startswith('from typing') or (line.startswith('import ') and not 'from .' in lines[i:i+5]):
                import_index = i
            # Stop if we hit internal imports
            if line.startswith('# Internal') or line.startswith('from .'):
                break

        # Add Rich import after the last import
        if import_index >= 0:
            # Find the next line after this import group
            insert_at = import_index + 1
            while insert_at < len(lines) and lines[insert_at].strip() and not lines[insert_at].startswith('#'):
                insert_at += 1

            lines.insert(insert_at, '')
            lines.insert(insert_at + 1, '# Rich console for output')
            lines.insert(insert_at + 2, 'from rich.console import Console')
            lines.insert(insert_at + 3, 'console = Console()')

        content = '\n'.join(lines)
    return content

def convert_prints(content):
    """Convert print() to console.print()."""
    # Simple replacement for print( to console.print(
    content = re.sub(r'\bprint\(', 'console.print(', content)
    return content

def process_file(filepath):
    """Process a single file."""
    print(f"Processing: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if file has print statements
    if 'print(' in content:
        # Add Rich import
        content = add_rich_import(content)

        # Convert prints
        content = convert_prints(content)

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  ✓ Converted print() to console.print()")
    else:
        print(f"  - No print() statements found")

def main():
    """Main conversion function."""
    files_to_convert = [
        '/home/aipass/apps/handlers/branch/file_ops.py',
        '/home/aipass/apps/handlers/error/logger.py',
        '/home/aipass/apps/handlers/error/decorators.py',
        '/home/aipass/apps/handlers/cli/prompts.py',
        '/home/aipass/apps/handlers/json/json_ops.py'
    ]

    print("Converting print() statements to console.print()...\n")

    for filepath in files_to_convert:
        if Path(filepath).exists():
            process_file(filepath)
        else:
            print(f"File not found: {filepath}")

    print("\n✓ Conversion complete!")

if __name__ == "__main__":
    main()