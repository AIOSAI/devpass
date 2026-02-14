#!/usr/bin/env python3
"""
Simple scanner to find legacy AIPASS_ROOT import patterns.
NO modifications - just reports what's found.

Searches for:
1. Legacy: sys.path.append(str(Path(__file__).parent.parent))
2. Current: AIPASS_ROOT = Path("/home/aipass")
"""

import os
import re
from pathlib import Path

# Directories to skip
EXCLUDE_DIRS = {
    '.git', '__pycache__', '.pytest_cache', 'node_modules',
    '.vscode', 'venv', 'env', '.env', '.local', '.cache',
    '.Trash', '.serena',
    'proc', 'sys', 'dev', 'boot', 'run', 'mnt', 'media',
    'var', 'opt', 'srv', 'root', 'lib', 'lib64', 'bin', 'sbin',
    'usr', 'lost+found', 'cdrom', 'snap', 'swap.img',
    'backups', 'backup', 'downloads', 'Downloads',
    'archive', 'Archive', 'archives', 'Archives',
     'tmp', '.tmp',
    'processed_plans', 'memory_bank',
    '.config', 'admin_dev',
    'History', 'history', '.bash_history', '.python_history'
}

# File extensions to scan
FILE_EXTENSIONS = {
    '.py', '.md', '.txt', '.rst', '.sh'
}

# Patterns to search for
PATTERNS = [
    r'sys\.path\.append\(str\(Path\(__file__\)\.parent\.parent\)\)',
    r'AIPASS_ROOT = Path\("/home/aipass"\)',
    r"AIPASS_ROOT = Path\('/home/aipass'\)",
    r'ECOSYSTEM_ROOT = Path\("/home/aipass"\)',
    r"ECOSYSTEM_ROOT = Path\('/home/aipass'\)",
]

def scan_directory(root_path):
    """Scan directory for legacy patterns."""
    found_files = []
    scanned_dirs = []

    print(f"Scanning {root_path} for legacy patterns...\n")

    for root, dirs, files in os.walk(root_path):
        # Track this directory
        scanned_dirs.append(root)

        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for filename in files:
            file_path = Path(root) / filename

            # Only scan relevant file types
            if file_path.suffix not in FILE_EXTENSIONS:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Check if any pattern matches
                matches = []
                for pattern in PATTERNS:
                    if re.search(pattern, content):
                        count = len(re.findall(pattern, content))
                        matches.append((pattern, count))

                if matches:
                    rel_path = file_path.relative_to(root_path)
                    found_files.append({
                        'path': str(rel_path),
                        'full_path': str(file_path),
                        'matches': matches
                    })

            except Exception:
                continue

    return found_files, scanned_dirs

def print_results(found_files, scanned_dirs, root_path):
    """Print scan results."""
    print("="*70)
    print("DIRECTORIES SCANNED")
    print("="*70)

    # Get unique top-level directories
    top_dirs = set()
    for d in scanned_dirs:
        rel = Path(d).relative_to(root_path)
        parts = rel.parts
        if parts:
            top_dirs.add(parts[0])

    for dirname in sorted(top_dirs):
        print(f"  📁 {dirname}/")

    print(f"\nTotal directories scanned: {len(scanned_dirs)}")

    print("\n" + "="*70)
    print("LEGACY PATTERN SCAN RESULTS")
    print("="*70)
    print(f"Total files found: {len(found_files)}\n")

    if not found_files:
        print("No files with legacy patterns found.")
        return

    for item in found_files:
        print(f"📝 {item['path']}")
        for pattern, count in item['matches']:
            pattern_name = "parent.parent" if "parent.parent" in pattern else "hardcoded Path"
            print(f"   - {pattern_name}: {count} occurrence(s)")
        print()

    print("="*70)

if __name__ == "__main__":
    import sys

    root_path = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/aipass")
    found, scanned_dirs = scan_directory(root_path)
    print_results(found, scanned_dirs, root_path)
