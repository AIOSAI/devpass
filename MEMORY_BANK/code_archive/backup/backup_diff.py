#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: backup_diff.py
# Date: 2025-10-14
# Version: 1.0.0
# Category: backup_system
#
# CHANGELOG:
#   - v1.0.0 (2025-10-14): Initial extraction from backup.py
#     * Extracted diff functionality (lines 840-854, 856-1198)
#     * Diff generation with binary file detection
#     * Version file discovery and management
#     * VS Code integration for visual diffs
#     * List versioned files with history
# =============================================

"""
Backup System Diff Functionality

Handles diff generation, version management, and VS Code integration.
Supports the file-organized structure (file.py/file.py_diffs/file.py_v*.diff).
"""

# =============================================
# IMPORTS
# =============================================

import sys
import os
import datetime
import difflib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Infrastructure import pattern
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))
from prax.apps.prax_logger import system_logger as logger

# Import from our modules
from backup_utils import safe_print
from backup_config import DIFF_IGNORE_PATTERNS, DIFF_INCLUDE_PATTERNS

# =============================================
# DIFF GENERATION
# =============================================

def should_create_diff(file_path: Path) -> bool:
    """Check if file should have diffs created based on ignore patterns.

    Args:
        file_path: Path to file to check

    Returns:
        True if diff should be created, False otherwise
    """
    # Check include patterns first (exceptions that should always have diffs)
    for pattern in DIFF_INCLUDE_PATTERNS:
        if file_path.match(pattern):
            return True

    # Then check ignore patterns
    for pattern in DIFF_IGNORE_PATTERNS:
        if file_path.match(pattern):
            return False

    # Default: create diff for all other files
    return True


def is_binary_file(file_path: Path) -> bool:
    """Check if a file is likely binary.

    Args:
        file_path: Path to file to check

    Returns:
        True if file appears to be binary, False otherwise
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
        return b'\0' in chunk
    except Exception:
        return True  # Assume binary if we can't read it


def generate_diff_content(old_file: Path, new_file: Path) -> str:
    """Generate unified diff content between two files.

    Args:
        old_file: Path to old version of file
        new_file: Path to new version of file

    Returns:
        Unified diff string showing changes
    """
    try:
        # Check if files are likely binary
        if is_binary_file(old_file) or is_binary_file(new_file):
            return f"Binary file {old_file.name} changed\n"

        # Read file contents
        with open(old_file, 'r', encoding='utf-8', errors='replace') as f:
            old_lines = f.readlines()
        with open(new_file, 'r', encoding='utf-8', errors='replace') as f:
            new_lines = f.readlines()

        # Generate unified diff
        diff_lines = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{old_file.name}",
            tofile=f"b/{new_file.name}",
            fromfiledate=datetime.datetime.fromtimestamp(old_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            tofiledate=datetime.datetime.fromtimestamp(new_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            lineterm=''
        )

        return '\n'.join(diff_lines)

    except Exception as e:
        return f"Error generating diff: {e}\n"

# =============================================
# VERSION FILE DISCOVERY
# =============================================

def get_versioned_files(backup_path: Path, file_path: str | None = None) -> Dict[str, List[str]]:
    """Get all versioned files using new file-organized structure.

    Args:
        backup_path: Path to backup root directory
        file_path: Optional filter to search for specific file

    Returns:
        Dictionary mapping file paths to lists of version timestamps
    """
    versioned_files = {}

    if not backup_path.exists():
        return versioned_files

    # Normalize search path for cross-platform compatibility
    normalized_search_path = None
    if file_path:
        normalized_search_path = str(Path(file_path)).replace('\\', '/').lower()

    # NEW STRUCTURE: Look for *_diffs folders
    for diff_folder in backup_path.rglob('*_diffs'):
        if not diff_folder.is_dir():
            continue

        # Extract base filename from diff folder name (remove _diffs suffix)
        if not diff_folder.name.endswith('_diffs'):
            continue

        base_filename = diff_folder.name[:-6]  # Remove '_diffs'

        # Get relative path from backup root to the file
        # diff_folder structure: .../filename/filename_diffs/
        file_folder = diff_folder.parent
        if file_folder.name != base_filename:
            continue  # Skip if structure doesn't match expected pattern

        # Calculate base path for this file
        rel_path_to_file_folder = file_folder.relative_to(backup_path)
        base_path = str(rel_path_to_file_folder / base_filename)

        # Filter by search path if provided
        if file_path:
            normalized_base_path = str(base_path).replace('\\', '/').lower()
            if normalized_search_path is not None and normalized_search_path not in normalized_base_path:
                continue

        # Find all diff files in this folder
        versions = []
        for diff_file in diff_folder.glob('*_v*.diff'):
            filename = diff_file.name
            if '_v' in filename and filename.endswith('.diff'):
                # Extract version from filename: basename_v<timestamp>.diff
                version_part = filename.split('_v')[1].replace('.diff', '')
                versions.append(version_part)

        if versions:
            versioned_files[base_path] = sorted(versions, reverse=True)  # Newest first

    return versioned_files


def list_versioned_files(backup_path: Path) -> bool:
    """List all versioned files with their version counts.

    Args:
        backup_path: Path to backup root directory

    Returns:
        True if files were found and listed, False otherwise
    """
    try:
        versioned_files = get_versioned_files(backup_path)

        if not versioned_files:
            safe_print("📂 No versioned files found")
            return False

        print(f"\n{'='*70}")
        print("📋 VERSIONED FILES HISTORY")
        print('='*70)

        for file_path, versions in versioned_files.items():
            version_count = len(versions)
            latest_version = versions[0] if versions else "unknown"

            safe_print(f"📄 {file_path}")
            print(f"   Versions: {version_count} | Latest: {latest_version}")

            # Show first 3 versions
            for i, version in enumerate(versions[:3]):
                marker = "📍" if i == 0 else "  "
                print(f"   {marker} v{version}")

            if len(versions) > 3:
                print(f"   ... and {len(versions) - 3} more versions")
            print()

        print('='*70)
        print(f"💡 Use: python backup.py diff --file <path> to see changes")
        return True

    except Exception as e:
        safe_print(f"❌ Error listing versioned files: {e}")
        logger.error(f"[backup_diff] Failed to list versioned files: {e}")
        return False

# =============================================
# VS CODE INTEGRATION
# =============================================

def show_file_diff(backup_path: Path, source_dir: Path, file_path: str, version1: str | None = None, version2: str | None = None) -> bool:
    """Show diff between two versions of a file in VS Code.

    Args:
        backup_path: Path to backup root directory
        source_dir: Path to source directory (for current file comparison)
        file_path: File path to show diff for
        version1: First version timestamp (optional)
        version2: Second version timestamp (optional)

    Returns:
        True if diff was opened successfully, False otherwise
    """
    try:
        versioned_files = get_versioned_files(backup_path, file_path)

        if not versioned_files:
            safe_print(f"❌ No versioned files found for: {file_path}")
            return False

        # Find the matching file with normalized path comparison
        matching_file = None
        normalized_search_path = str(Path(file_path)).replace('\\', '/').lower()
        for base_path in versioned_files:
            normalized_base_path = str(base_path).replace('\\', '/').lower()
            if normalized_search_path in normalized_base_path:
                matching_file = base_path
                break

        if not matching_file:
            safe_print(f"❌ File not found: {file_path}")
            return False

        versions = versioned_files[matching_file]

        if len(versions) < 1:
            safe_print(f"⚠️  Only one version found for: {file_path}")
            return False

        # Determine which versions to compare
        if version1 and version2:
            if version1 not in versions or version2 not in versions:
                safe_print(f"❌ Version not found. Available: {', '.join(versions)}")
                return False
        else:
            # Compare latest version with current file, or two most recent versions
            current_file = backup_path / matching_file
            if current_file.exists() and len(versions) >= 1:
                version1 = "current"
                version2 = versions[0]  # Most recent version
            elif len(versions) >= 2:
                version1 = versions[1]  # Second most recent
                version2 = versions[0]  # Most recent
            else:
                safe_print(f"⚠️  Need at least 2 versions to compare")
                return False

        # Determine file paths for comparison using NEW STRUCTURE
        # For VS Code diff, we need actual files, not diff patches
        try:
            # NEW STRUCTURE: matching_file is like "root/CLAUDE.local.md/CLAUDE.local.md"
            # We need to find the file folder and look for baseline + current file

            # Extract the base filename for pattern matching
            base_filename = Path(matching_file).name
            file_folder_path = backup_path / Path(matching_file).parent

            # Look for baseline file in the file folder
            # Handle files with extensions like CLAUDE.local.md -> CLAUDE.local-baseline-*
            name_without_ext = base_filename.rsplit('.', 1)[0] if '.' in base_filename else base_filename
            baseline_pattern = f"{name_without_ext}-baseline-*"
            baseline_files = list(file_folder_path.glob(baseline_pattern))

            # Current backup file path (in the organized structure)
            current_backup_file = file_folder_path / base_filename

            # Source file path (live file in source directory)
            # Convert backup path back to source path
            matching_file_normalized = str(Path(matching_file)).replace('\\', '/')
            if matching_file_normalized.startswith("root/"):
                # Root level file: root/filename/filename -> filename
                source_relative_path = base_filename
            else:
                # Nested file: folder/filename/filename -> folder/filename
                source_relative_path = str(Path(matching_file).parent.parent / base_filename)

            source_file_path = source_dir / source_relative_path

            if baseline_files:
                # ALWAYS prefer baseline comparison when available
                file1_path = baseline_files[0]  # Use first baseline found
                file2_path = source_file_path   # Current source
                label1 = f"{base_filename} (baseline)"
                label2 = f"{base_filename} (current)"
            elif current_backup_file.exists():
                # No baseline, compare backup against current source
                file1_path = current_backup_file  # Backup version
                file2_path = source_file_path     # Live source
                label1 = f"{base_filename} (backup)"
                label2 = f"{base_filename} (current)"

                # Check if they're the same
                if file1_path.exists() and file2_path.exists():
                    if file1_path.stat().st_mtime == file2_path.stat().st_mtime:
                        safe_print(f"⚠️  Note: Backup is identical to current file (no changes)")
                        safe_print(f"   This happens when Google Drive sync updates the backup")
            else:
                safe_print(f"❌ Could not find backup file in new structure: {matching_file}")
                return False

            # Verify files exist
            if not file1_path.exists():
                safe_print(f"❌ File not found: {file1_path}")
                return False
            if not file2_path.exists():
                safe_print(f"❌ File not found: {file2_path}")
                return False

        except Exception as e:
            safe_print(f"❌ Error locating files: {e}")
            logger.error(f"[backup_diff] Error locating files for diff: {e}")
            return False

        # Open diff in VS Code
        print(f"\n{'='*70}")
        print(f"📋 Opening diff in VS Code: {matching_file}")
        print(f"Comparing: {label2} → {label1}")
        print('='*70)

        # Launch VS Code with diff view
        try:
            # Try to find VS Code command
            code_cmd = 'code'
            if sys.platform == 'win32':
                # On Windows, try common VS Code paths if 'code' not in PATH
                import shutil
                if not shutil.which('code'):
                    # Platform-specific VS Code detection
                    if sys.platform == 'win32':
                        # Windows VS Code path
                        vscode_path = Path(r"C:\Users") / os.environ.get('USERNAME', 'input') / r"AppData\Local\Programs\Microsoft VS Code\bin\code.cmd"
                        if vscode_path.exists():
                            code_cmd = str(vscode_path)
                        else:
                            code_cmd = 'code.cmd'
                    else:
                        # Linux - VS Code is usually in PATH or use snap
                        if Path('/snap/bin/code').exists():
                            code_cmd = '/snap/bin/code'
                        elif Path('/usr/bin/code').exists():
                            code_cmd = '/usr/bin/code'
                        else:
                            code_cmd = 'code'

            # Use subprocess for better error handling
            # Swap order so baseline (older) is on left, current (newer) is on right
            result = subprocess.run(
                [code_cmd, '--diff', str(file1_path), str(file2_path)],
                capture_output=True,
                text=True,
                shell=True if sys.platform == 'win32' else False
            )
            if result.returncode == 0:
                safe_print(f"✅ Diff opened in VS Code")
            else:
                safe_print(f"⚠️ VS Code returned code {result.returncode}")
                if result.stderr:
                    safe_print(f"Error: {result.stderr}")
        except FileNotFoundError:
            safe_print(f"❌ VS Code command not found. Make sure 'code' is in your PATH")
            safe_print(f"💡 You can manually compare:")
            safe_print(f"   File 1: {file2_path}")
            safe_print(f"   File 2: {file1_path}")
            return False
        except Exception as e:
            safe_print(f"❌ Error launching VS Code: {e}")
            logger.error(f"[backup_diff] Error launching VS Code: {e}")
            return False

        print('='*70)
        return True

    except Exception as e:
        safe_print(f"❌ Error generating diff: {e}")
        logger.error(f"[backup_diff] Error in show_file_diff: {e}")
        return False

# =============================================
# MODULE INITIALIZATION
# =============================================

logger.info("[backup_diff] Module loaded - diff functionality ready")
