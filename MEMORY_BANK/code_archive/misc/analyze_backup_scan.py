#!/usr/bin/env python3
"""Analyze what directories the backup system is actually scanning"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path.home() / 'aipass_core'))

from backup_system.apps.handlers.config.config_handler import (
    GLOBAL_IGNORE_PATTERNS,
    IGNORE_EXCEPTIONS,
    should_ignore
)

source_dir = Path.home()
backup_dest = Path.home() / "aipass_core" / "backup_system" / "backups"

# Count files per top-level directory
dir_file_counts = defaultdict(int)
dir_sizes = defaultdict(int)

print("Scanning directories to find what's being backed up...\n")

for item in source_dir.rglob("*"):
    if item.is_file():
        # Check if this file would be ignored
        if not should_ignore(item, GLOBAL_IGNORE_PATTERNS, IGNORE_EXCEPTIONS, backup_dest):
            # Find the top-level directory
            try:
                rel_path = item.relative_to(source_dir)
                if len(rel_path.parts) > 0:
                    top_dir = rel_path.parts[0]
                    dir_file_counts[top_dir] += 1
                    try:
                        dir_sizes[top_dir] += item.stat().st_size
                    except:
                        pass
            except:
                pass

# Sort by file count
sorted_dirs = sorted(dir_file_counts.items(), key=lambda x: x[1], reverse=True)

print("="*80)
print("DIRECTORIES BEING BACKED UP (sorted by file count)")
print("="*80)
print(f"{'Directory':<30} {'Files':>10} {'Size':>15}")
print("-"*80)

total_files = 0
for dir_name, count in sorted_dirs[:20]:  # Top 20
    size = dir_sizes[dir_name]
    size_mb = size / (1024 * 1024)
    total_files += count
    print(f"{dir_name:<30} {count:>10} {size_mb:>12.1f} MB")

print("-"*80)
print(f"{'TOTAL':<30} {total_files:>10}")
print("="*80)

# Show directories that ARE being ignored
print("\n" + "="*80)
print("SAMPLE IGNORED DIRECTORIES (first 10)")
print("="*80)
ignored_samples = []
for item in source_dir.iterdir():
    if item.is_dir() and should_ignore(item, GLOBAL_IGNORE_PATTERNS, IGNORE_EXCEPTIONS, backup_dest):
        ignored_samples.append(item.name)
        if len(ignored_samples) >= 10:
            break

for d in ignored_samples:
    print(f"  ✓ {d}")
