#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: test_log_rotation.py - Test Log Rotation Behavior
# Date: 2025-10-27
# Version: 1.0.0
# Category: prax
#
# CHANGELOG:
#   - v1.0.0 (2025-10-27): Test rotation with config-driven limits
# =============================================

"""
Test Log Rotation Module

Tests that log rotation is working correctly with config-driven limits.
Generates enough log entries to trigger rotation and validates results.
"""

# INFRASTRUCTURE IMPORT PATTERN - Universal AIPass pattern
from pathlib import Path
AIPASS_ROOT = Path.home()
import sys
sys.path.append(str(AIPASS_ROOT))

from prax.apps.prax_handlers import system_logger

def test_rotation():
    """Generate enough log entries to trigger rotation"""
    print("=" * 60)
    print("TEST: Log Rotation Validation")
    print("=" * 60)

    # System logs should rotate at 1000 lines (150KB)
    # Local logs should rotate at 250 lines (37.5KB)
    # We'll generate 2000 entries to trigger rotation twice

    print("\nGenerating 2000 log entries...")
    print("Expected behavior:")
    print("  - At 1000 lines: test_log_rotation.log rotates to .log.1")
    print("  - At 2000 lines: old .log.1 deleted, current → .log.1, new .log created")

    for i in range(2000):
        system_logger.info(f"Test log entry {i:04d} - Testing rotation behavior with config-driven limits")
        if (i + 1) % 250 == 0:
            print(f"  Generated {i + 1} entries...")

    print("\n✓ Log generation complete")

    # Check results
    system_logs_dir = AIPASS_ROOT / "system_logs"
    log_file = system_logs_dir / "test_log_rotation.log"
    log_file_backup = system_logs_dir / "test_log_rotation.log.1"

    print("\nChecking results:")

    if log_file.exists():
        size_kb = log_file.stat().st_size / 1024
        lines = len(log_file.read_text().splitlines())
        print(f"  ✓ test_log_rotation.log exists")
        print(f"    Size: {size_kb:.1f} KB")
        print(f"    Lines: {lines}")

        if size_kb <= 150:
            print(f"    ✓ Size within limit (< 150KB)")
        else:
            print(f"    ⚠️ Size exceeds limit!")
    else:
        print(f"  ❌ test_log_rotation.log NOT FOUND")

    if log_file_backup.exists():
        size_kb = log_file_backup.stat().st_size / 1024
        lines = len(log_file_backup.read_text().splitlines())
        print(f"  ✓ test_log_rotation.log.1 exists (ROTATION WORKING!)")
        print(f"    Size: {size_kb:.1f} KB")
        print(f"    Lines: {lines}")
    else:
        print(f"  ❌ test_log_rotation.log.1 NOT FOUND (rotation may not have triggered)")

    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)

if __name__ == "__main__":
    test_rotation()
