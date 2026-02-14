#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: regenerate_template_registry.py - Regenerate Template Registry
# Date: 2025-11-15
# Version: 1.1.0
# Category: cortex
# Commands: regenerate, --help
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2025-11-15): Added drone compliance (Commands line in help)
#   - v1.0.0 (2025-11-04): Initial implementation
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Regenerate Template Registry

Quick script to regenerate .template_registry.json after template changes.
PRESERVES IDs for existing files - only assigns new IDs to new files
"""

import sys
from pathlib import Path
import json
import hashlib
from datetime import datetime

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Prax logger
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

from cortex.apps.handlers.registry.ignore import load_ignore_patterns, should_ignore

TEMPLATE_DIR = AIPASS_ROOT / "cortex" / "templates" / "branch_template"
REGISTRY_FILE = TEMPLATE_DIR / ".template_registry.json"


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of file content

    Args:
        file_path: Path to file

    Returns:
        Hex string of file hash (first 12 characters for readability)
    """
    if not file_path.is_file():
        return ""

    try:
        sha256 = hashlib.sha256()
        # DIRECT OPERATION JUSTIFIED: Binary read required for hash calculation
        # Handlers (reconcile.py, meta_ops.py) also use direct binary reads for hashing
        # No abstracted handler exists for this low-level infrastructure operation
        with open(file_path, 'rb') as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        # Return first 12 chars of hash (enough for uniqueness)
        return sha256.hexdigest()[:12]
    except Exception as e:
        logger.error(f"File hash calculation failed for {file_path.name}: {e}")
        console.print(f"WARNING: Could not hash {file_path.name}: {e}")
        return ""


def load_existing_registry():
    """Load existing registry to preserve IDs"""
    if not REGISTRY_FILE.exists():
        return None

    try:
        # DIRECT OPERATION JUSTIFIED: Infrastructure file read (template registry management)
        # Not branch content - this is system-level registry maintenance
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load existing registry: {e}")
        console.print(f"WARNING: Could not load existing registry: {e}")
        return None


def scan_template_directory():
    """
    Scan template directory and build registry from filesystem

    PRESERVES IDs for existing files by matching on path
    Only assigns new IDs to genuinely new files
    """
    # Load ignore patterns
    ignore_patterns = load_ignore_patterns(TEMPLATE_DIR)
    ignore_files = ignore_patterns.get("ignore_files", [])
    ignore_globs = ignore_patterns.get("ignore_patterns", [])

    # Load existing registry to preserve IDs
    existing_registry = load_existing_registry()
    existing_files_by_hash = {}  # hash → ID (Priority 1: content unchanged)
    existing_files_by_path = {}  # path → ID (Priority 2: content changed, location same)
    existing_dirs_by_path = {}   # path → ID (dirs don't change content)

    if existing_registry:
        # Build hash → ID and path → ID mappings for files
        for file_id, file_info in existing_registry.get("files", {}).items():
            content_hash = file_info.get("content_hash", "")
            path = file_info.get("path", "")

            # Priority 1: Match by content hash
            if content_hash:
                existing_files_by_hash[content_hash] = file_id

            # Priority 2: Match by path (for when content changes)
            if path:
                existing_files_by_path[path] = file_id

        # Build path → ID mappings for directories
        for dir_id, dir_info in existing_registry.get("directories", {}).items():
            path = dir_info.get("path", "")
            existing_dirs_by_path[path] = dir_id

    files = {}
    directories = {}

    # Track which IDs are already used
    used_file_ids = set(existing_files_by_hash.values())
    used_dir_ids = set(existing_dirs_by_path.values())

    # Counters for new IDs
    file_counter = 1
    dir_counter = 1

    # Walk template directory
    for item in TEMPLATE_DIR.rglob("*"):
        # Apply ignore patterns
        if should_ignore(item, TEMPLATE_DIR, ignore_files, ignore_globs):
            continue

        relative_path = str(item.relative_to(TEMPLATE_DIR))

        if item.is_file():
            # Calculate content hash
            content_hash = calculate_file_hash(item)

            # HYBRID ID MATCHING (Hash+Path priority system)
            # Priority 1: Match by content hash (file unchanged)
            if content_hash and content_hash in existing_files_by_hash:
                file_id = existing_files_by_hash[content_hash]
                # print(f"  [P1-HASH] {relative_path} → {file_id}")

            # Priority 2: Match by path (content changed at same location)
            elif relative_path in existing_files_by_path:
                file_id = existing_files_by_path[relative_path]
                # print(f"  [P2-PATH] {relative_path} → {file_id} (content updated)")

            # Priority 3: New file - assign new ID
            else:
                while f"f{file_counter:03d}" in used_file_ids:
                    file_counter += 1
                file_id = f"f{file_counter:03d}"
                used_file_ids.add(file_id)
                file_counter += 1
                # print(f"  [P3-NEW] {relative_path} → {file_id}")

            files[file_id] = {
                "current_name": item.name,
                "path": relative_path,
                "content_hash": content_hash,
                "has_branch_placeholder": "{{BRANCH}}" in item.name or "{{BRANCHNAME}}" in item.name
            }

        elif item.is_dir():
            # DIRECTORY ID MATCHING (Path+Name priority system)
            # Priority 1: Match by exact path (directory at same location)
            if relative_path in existing_dirs_by_path:
                dir_id = existing_dirs_by_path[relative_path]
                # print(f"  [D1-PATH] {relative_path} → {dir_id}")

            # Priority 2: Match by name (directory renamed, try to preserve ID)
            # Check if there's an old directory with same name in existing registry
            else:
                dir_id = None
                dir_name = item.name

                # Look for directories in old registry that don't exist on filesystem anymore
                # but have the same or similar name
                for old_path, old_id in existing_dirs_by_path.items():
                    old_dir_path = TEMPLATE_DIR / old_path
                    if not old_dir_path.exists():
                        # This directory was renamed or deleted
                        old_name = Path(old_path).name

                        # Check if names match (exact or similar)
                        if old_name == dir_name:
                            # Exact name match - likely just moved
                            dir_id = old_id
                            # print(f"  [D2-NAME-EXACT] {relative_path} → {dir_id} (was: {old_path})")
                            break
                        elif old_name in dir_name or dir_name in old_name:
                            # Fuzzy match - names are similar (e.g., DOCUMENTS vs DOCUMENTSxxx)
                            dir_id = old_id
                            # print(f"  [D2-NAME-FUZZY] {relative_path} → {dir_id} (was: {old_path})")
                            break

                # Priority 3: New directory - assign new ID
                if dir_id is None:
                    while f"d{dir_counter:03d}" in used_dir_ids:
                        dir_counter += 1
                    dir_id = f"d{dir_counter:03d}"
                    used_dir_ids.add(dir_id)
                    dir_counter += 1
                    # print(f"  [D3-NEW] {relative_path} → {dir_id}")
                else:
                    used_dir_ids.add(dir_id)

            directories[dir_id] = {
                "current_name": item.name,
                "path": relative_path,
                "has_branch_placeholder": "{{BRANCH}}" in item.name or "{{BRANCHNAME}}" in item.name
            }

    return {"files": files, "directories": directories}


def regenerate_registry():
    """Regenerate .template_registry.json from current filesystem state"""
    console.print(f"Scanning template directory: {TEMPLATE_DIR}")

    # Scan filesystem
    scanned = scan_template_directory()

    # Build new registry
    registry = {
        "metadata": {
            "version": "1.0.0",
            "last_updated": datetime.now().date().isoformat(),
            "description": "Template file tracking registry for ID-based updates"
        },
        "files": scanned["files"],
        "directories": scanned["directories"]
    }

    # Save registry
    # DIRECT OPERATION JUSTIFIED: Infrastructure file write (template registry management)
    # Not branch content - this is system-level registry maintenance
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    file_count = len(scanned["files"])
    dir_count = len(scanned["directories"])

    console.print(f"✅ Registry regenerated successfully!")
    console.print(f"   Files: {file_count}")
    console.print(f"   Directories: {dir_count}")
    console.print(f"   Saved to: {REGISTRY_FILE}")

    return True


# =============================================================================
# MODULE INTERFACE
# =============================================================================

def handle_command(args) -> bool:
    """
    Orchestrator interface for regenerate_template_registry

    Args:
        args: Command arguments (argparse Namespace)

    Returns:
        True if command handled, False otherwise
    """
    # Check if this module should handle the command
    if not hasattr(args, 'command') or args.command != 'regenerate-template-registry':
        return False

    # Execute registry regeneration (no arguments needed)
    try:
        return regenerate_registry()
    except Exception as e:
        logger.error(f"Registry regeneration failed: {e}")
        console.print(f"ERROR: {e}")
        return False


# =============================================================================
# DRONE COMPLIANCE - HELP SYSTEM
# =============================================================================

def print_help():
    """Display drone-compliant help output"""
    console.print()
    console.print("="*70)
    console.print("REGENERATE TEMPLATE REGISTRY - Template Registry Generator")
    console.print("="*70)
    console.print()
    console.print("Regenerates .template_registry.json after template changes.")
    console.print()
    console.print("USAGE:")
    console.print("  python3 regenerate_template_registry.py")
    console.print("  cortex regenerate")
    console.print()
    console.print("EXAMPLE:")
    console.print("  python3 regenerate_template_registry.py")
    console.print()
    console.print("WHAT IT DOES:")
    console.print("  - Scans template directory for all files and directories")
    console.print("  - Preserves IDs for existing files (only assigns new IDs to new files)")
    console.print("  - Calculates content hashes for change detection")
    console.print("  - Saves registry to .template_registry.json")
    console.print()
    console.print("WHEN TO USE:")
    console.print("  - After adding new files to template")
    console.print("  - After renaming files in template")
    console.print("  - After modifying template structure")
    console.print()
    console.print("REQUIREMENTS:")
    console.print("  - Template directory must exist at:")
    console.print("    /home/aipass/aipass_core/cortex/templates/branch_template")
    console.print()
    console.print("="*70)
    console.print()
    console.print("Commands: regenerate, --help")
    console.print()


if __name__ == "__main__":
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    try:
        regenerate_registry()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Registry regeneration failed: {e}")
        console.print(f"❌ Error: {e}")
        sys.exit(1)
