#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: delete_protected.py
# Date: 2025-10-20
# Version: 1.0.0
# Category: backup_system
#
# CHANGELOG:
#   - v1.0.0 (2025-10-20): Initial protected file deletion tool
#     * Delete read-only files and directories safely
#     * Uses temporarily_writable() context manager
#     * Works with backup system's read-only protection
# =============================================

"""
Protected File Deletion Tool

Deletes read-only files and directories by temporarily removing protection.
Designed for use with backup system's read-only files.

Usage:
    python3 delete_protected.py delete <filepath>    # Delete with confirmation
    python3 delete_protected.py force <filepath>     # Delete without confirmation
    python3 delete_protected.py preview <filepath>   # Show file/directory info
"""

import sys
import shutil
import stat
from pathlib import Path
from datetime import datetime

# Module dependencies
sys.path.append(str(Path(__file__).parent))
from backup_utils import temporarily_writable

# =============================================
# CORE FUNCTIONS
# =============================================

def get_path_info(file_path):
    """Get information about a file or directory

    Args:
        file_path: Path to file or directory

    Returns:
        tuple: (exists, is_dir, file_count, total_size, is_readonly)
    """
    path = Path(file_path).resolve()

    if not path.exists():
        return False, False, 0, 0, False

    is_dir = path.is_dir()
    is_readonly = not (path.stat().st_mode & stat.S_IWUSR)

    if is_dir:
        file_count = 0
        total_size = 0
        for item in path.rglob("*"):
            if item.is_file():
                file_count += 1
                total_size += item.stat().st_size
        return True, True, file_count, total_size, is_readonly
    else:
        file_size = path.stat().st_size
        return True, False, 1, file_size, is_readonly

def format_size(bytes_size):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def show_preview(file_path):
    """Show information about what will be deleted

    Args:
        file_path: Path to file or directory

    Returns:
        bool: True if path exists, False otherwise
    """
    path = Path(file_path).resolve()
    exists, is_dir, file_count, total_size, is_readonly = get_path_info(path)

    print("\n" + "="*60)
    print("PROTECTED FILE DELETION - PREVIEW")
    print("="*60)

    if not exists:
        print(f"\n✗ Path not found: {path}")
        print("\n" + "="*60)
        return False

    print(f"\nPath: {path}")
    print(f"Type: {'Directory' if is_dir else 'File'}")
    print(f"Protection: {'Read-only' if is_readonly else 'Writable'}")

    if is_dir:
        print(f"Files: {file_count:,}")
        print(f"Total Size: {format_size(total_size)}")
    else:
        print(f"Size: {format_size(total_size)}")

    print("\n" + "="*60)
    return True

def confirm_deletion(file_path, is_dir, file_count):
    """Get user confirmation for deletion

    Args:
        file_path: Path being deleted
        is_dir: Whether it's a directory
        file_count: Number of files

    Returns:
        bool: True if confirmed, False otherwise
    """
    print("\n⚠️  WARNING: This will PERMANENTLY DELETE this " + ("directory" if is_dir else "file") + "!")
    print("   This action cannot be undone.")

    if is_dir:
        print(f"   This will delete {file_count:,} file(s)")

    print(f"\n   Path: {file_path}")

    while True:
        response = input("\nProceed with deletion? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")

def make_writable_recursive(path):
    """Recursively make all files and directories writable

    Args:
        path: Path to make writable (and all children if directory)
    """
    try:
        # Make the path itself writable
        path.chmod(0o755 if path.is_dir() else 0o644)

        # If it's a directory, recurse through all contents
        if path.is_dir():
            for item in path.rglob("*"):
                try:
                    item.chmod(0o755 if item.is_dir() else 0o644)
                except Exception:
                    pass  # Continue even if some files can't be changed
    except Exception:
        pass  # Continue even if top-level can't be changed

def delete_path(file_path, force=False):
    """Delete a file or directory (handling read-only protection)

    Args:
        file_path: Path to delete
        force: Skip confirmation if True

    Returns:
        int: 0 on success, 1 on failure
    """
    path = Path(file_path).resolve()

    # Get path info
    exists, is_dir, file_count, total_size, is_readonly = get_path_info(path)

    if not exists:
        print(f"\n✗ Path not found: {path}")
        return 1

    # Show preview
    show_preview(path)

    # Get confirmation unless forced
    if not force:
        if not confirm_deletion(path, is_dir, file_count):
            print("\n✓ Operation cancelled - nothing was deleted")
            return 0

    # Perform deletion
    print("\n" + "="*60)
    print("DELETING...")
    print("="*60)

    try:
        # Find the first existing ancestor (same pattern as backup_operations.py)
        check_path = path.parent
        while not check_path.exists() and check_path.parent != check_path:
            check_path = check_path.parent

        # Make ancestor writable so we can remove the entry
        with temporarily_writable(check_path):
            # Recursively remove read-only protection from target
            make_writable_recursive(path)

            if is_dir:
                shutil.rmtree(path)
                print(f"✓ Deleted directory: {path}")
                print(f"  Removed {file_count:,} file(s) ({format_size(total_size)})")
            else:
                path.unlink()
                print(f"✓ Deleted file: {path}")
                print(f"  Removed {format_size(total_size)}")

        print("\n" + "="*60)
        print("DELETION COMPLETE!")
        print("="*60)
        return 0

    except Exception as e:
        print(f"\n✗ Deletion failed: {e}")
        return 1

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Protected File Deletion Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: delete, force, preview

  delete <filepath>  - Delete with confirmation
  force <filepath>   - Delete without confirmation
  preview <filepath> - Show file/directory info only

EXAMPLES:
  python3 delete_protected.py delete /path/to/file
  python3 delete_protected.py force /path/to/directory
  python3 delete_protected.py preview /path/to/backup

NOTE:
  This tool safely deletes read-only files and directories
  by temporarily removing protection during deletion.
  Designed for backup system files but works with any protected files.
        """
    )

    parser.add_argument('command',
                       choices=['delete', 'force', 'preview'],
                       help='Command to execute')

    parser.add_argument('filepath',
                       help='Path to file or directory to delete')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("PROTECTED FILE DELETION TOOL v1.0.0")
    print("="*60)
    print(f"Mode: {args.command.upper()}")

    # Preview mode
    if args.command == 'preview':
        exists = show_preview(args.filepath)
        if exists:
            print("\n✓ PREVIEW COMPLETE - No files were deleted")
            return 0
        else:
            return 1

    # Delete modes (with or without confirmation)
    force = (args.command == 'force')
    return delete_path(args.filepath, force=force)

# =============================================
# SCRIPT ENTRY POINT
# =============================================

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n✗ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
