#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: cleanup_outputs.py
# Date: 2025-07-19
# Version: 1.0.0
# 
# CHANGELOG:
#   - v1.0.0 (2025-07-19): Initial cleanup script creation
# =============================================

"""
Output Cleanup Script for AIPass-Code-Sniffer

Completely clears all output directories and files to provide a fresh slate
for testing and development.
"""

import os
import shutil
import sys
from pathlib import Path

# =============================================
# CONFIGURATION SECTION
# =============================================

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# Directories to clean
CLEAN_DIRECTORIES = [
    PROJECT_ROOT / "output",
    PROJECT_ROOT / "test_output",
]

# Files to clean (if they exist)
CLEAN_FILES = [
    PROJECT_ROOT / "skill_analysis_report.json",
    PROJECT_ROOT / "SKILL_DISCOVERY_REPORT.md",
]

# =============================================
# END CONFIGURATION
# =============================================

def clean_directory(dir_path: Path) -> bool:
    """Clean a directory completely."""
    try:
        if dir_path.exists():
            print(f"[CLEAN] Cleaning directory: {dir_path}")
            
            # Remove all contents
            for item in dir_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"   [DIR] Removed directory: {item.name}")
                else:
                    item.unlink()
                    print(f"   [FILE] Removed file: {item.name}")
            
            print(f"[SUCCESS] Directory cleaned: {dir_path}")
            return True
        else:
            print(f"[INFO] Directory doesn't exist: {dir_path}")
            return True
    except Exception as e:
        print(f"[ERROR] Error cleaning directory {dir_path}: {e}")
        return False

def clean_file(file_path: Path) -> bool:
    """Clean a specific file."""
    try:
        if file_path.exists():
            file_path.unlink()
            print(f"[SUCCESS] Removed file: {file_path}")
            return True
        else:
            print(f"[INFO] File doesn't exist: {file_path}")
            return True
    except Exception as e:
        print(f"[ERROR] Error removing file {file_path}: {e}")
        return False

def ensure_directories_exist():
    """Ensure clean directories exist for future use."""
    for dir_path in CLEAN_DIRECTORIES:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"[CREATE] Created directory: {dir_path}")

def main():
    """Main cleanup execution."""
    print("AIPass-Code-Sniffer Output Cleanup Starting...")
    print("=" * 50)
    
    success_count = 0
    total_count = 0
    
    # Clean directories
    print("\nCleaning directories...")
    for dir_path in CLEAN_DIRECTORIES:
        total_count += 1
        if clean_directory(dir_path):
            success_count += 1
    
    # Clean files
    print("\nCleaning files...")
    for file_path in CLEAN_FILES:
        total_count += 1
        if clean_file(file_path):
            success_count += 1
    
    # Recreate directories
    print("\nEnsuring directories exist...")
    ensure_directories_exist()
    
    # Summary
    print("\n" + "=" * 50)
    print("Cleanup Summary")
    print("=" * 50)
    print(f"Successful operations: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("SUCCESS: All outputs cleaned successfully!")
        print("Fresh slate ready for testing")
        return 0
    else:
        print("WARNING: Some cleanup operations failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
