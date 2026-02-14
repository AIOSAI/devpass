#!/home/aipass/.venv/bin/python3

"""
================================================================================
META
================================================================================
File: reconcile.py
Purpose: Reconcile branch filesystem state with branch_meta.json
Location: cortex/apps/handlers/branch/reconcile.py
Created: 2025-11-09

CHANGELOG:
[2025-11-09] Initial creation - branch state reconciliation handler

================================================================================
DESCRIPTION
================================================================================
Handler to reconcile branch_meta.json with actual filesystem state.

Identifies:
- Files tracked in branch_meta but missing from disk (deleted manually)
- Files present on disk but not tracked in branch_meta (added manually)
- Files with content hash mismatches (modified outside system)

Usage:
    from cortex.apps.handlers.branch.reconcile import reconcile_branch_state

    results = reconcile_branch_state(
        branch_dir=Path("/home/aipass/aipass_core/api"),
        branch_meta=branch_meta_dict,
        trace=False
    )

    if results['missing_files']:
        print(f"Missing: {results['missing_files']}")
    if results['untracked_files']:
        print(f"Untracked: {results['untracked_files']}")

Returns:
    dict: {
        'missing_files': [(file_id, path, name), ...],      # Tracked but not on disk
        'untracked_files': [(path, name), ...],              # On disk but not tracked
        'hash_mismatches': [(file_id, path, name), ...],    # Content changed
        'needs_update': bool                                 # True if discrepancies found
    }
"""

import hashlib
from pathlib import Path
import sys

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from typing import Dict, List, Tuple, Any

# Import ignore handler for consistent ignore logic across system
from cortex.apps.handlers.registry.ignore import load_ignore_patterns, should_ignore


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of file contents (first 12 chars)

    Args:
        file_path: Path to file

    Returns:
        First 12 characters of SHA-256 hash, or empty string on error
    """
    try:
        content = file_path.read_bytes()
        full_hash = hashlib.sha256(content).hexdigest()
        return full_hash[:12]
    except Exception:
        return ""


# Removed hardcoded should_ignore_path() - now using registry ignore handler


def scan_branch_filesystem(
    branch_dir: Path,
    template_dir: Path,
    ignore_files: List[str],
    ignore_patterns: List[str],
    trace: bool = False
) -> Dict[str, Any]:
    """
    Scan branch filesystem and build current state map

    Args:
        branch_dir: Branch directory path
        template_dir: Template directory (for ignore handler)
        ignore_files: Exact filenames to ignore
        ignore_patterns: Glob patterns to ignore
        trace: Enable trace logging

    Returns:
        dict: {
            'files': {path: {name, hash, is_dir}, ...},
            'directories': {path: {name}, ...},
            'trace_logs': [(type, message, details), ...]  # if trace=True
        }
    """
    current_state = {
        'files': {},
        'directories': {},
        'trace_logs': []
    }

    if trace:
        current_state['trace_logs'].append(('scan_start', f"Scanning branch filesystem at {branch_dir}", {}))

    # Use iterative directory walking to avoid descending into ignored directories
    # This prevents scanning massive trees like .cache, .archive, aipass_core subdirs, etc.
    def walk_directory(directory: Path):
        """Recursively walk directory, skipping ignored paths at directory level"""
        try:
            for item in directory.iterdir():
                # Check if this item should be ignored
                if should_ignore(item, template_dir, ignore_files, ignore_patterns):
                    if trace:
                        try:
                            relative = item.relative_to(branch_dir)
                            current_state['trace_logs'].append(('ignored', str(relative), {}))
                        except ValueError:
                            pass
                    continue

                relative_path = str(item.relative_to(branch_dir))

                if item.is_file():
                    content_hash = calculate_file_hash(item)
                    current_state['files'][relative_path] = {
                        'name': item.name,
                        'hash': content_hash,
                        'is_dir': False
                    }
                    if trace:
                        current_state['trace_logs'].append(('file_found', relative_path, {'hash': content_hash}))

                elif item.is_dir():
                    current_state['directories'][relative_path] = {
                        'name': item.name
                    }
                    if trace:
                        current_state['trace_logs'].append(('dir_found', relative_path, {}))

                    # Recursively walk subdirectory (only if not ignored)
                    walk_directory(item)

        except PermissionError:
            if trace:
                current_state['trace_logs'].append(('permission_denied', str(directory), {}))
        except Exception as e:
            if trace:
                current_state['trace_logs'].append(('scan_error', str(directory), {'error': str(e)}))

    try:
        walk_directory(branch_dir)
    except Exception as e:
        if trace:
            current_state['trace_logs'].append(('filesystem_scan_error', 'root', {'error': str(e)}))

    return current_state


def reconcile_branch_state(
    branch_dir: Path,
    branch_meta: Dict,
    trace: bool = False,
    fast_mode: bool = False
) -> Dict[str, Any]:
    """
    Reconcile branch_meta with actual filesystem state

    Identifies discrepancies:
    - Files tracked but missing (manual deletion)
    - Files present but untracked (manual addition) [only in full mode]
    - Content hash mismatches (manual modification) [only in full mode]

    Args:
        branch_dir: Branch directory path
        branch_meta: Branch metadata dict
        trace: Enable trace logging
        fast_mode: If True, only check if tracked files exist (skip filesystem scan)

    Returns:
        dict: Reconciliation results with missing/untracked/mismatched files
              and trace_logs if trace=True
    """
    trace_logs = []

    if trace:
        trace_logs.append(('reconcile_start', 'BRANCH STATE RECONCILIATION', {}))
        if fast_mode:
            trace_logs.append(('mode', 'FAST (only check tracked files exist)', {}))

    # Get tracked state from branch_meta
    file_tracking = branch_meta.get("file_tracking", {})

    # FAST MODE: Only check if tracked files exist (no filesystem scan)
    # Used during update_branch for speed - we don't care about untracked files
    if fast_mode:
        missing_files = []

        if trace:
            trace_logs.append(('fast_mode_check', f"Checking {len(file_tracking)} tracked files", {}))

        for file_id, file_info in file_tracking.items():
            tracked_path = file_info.get('path', '')
            tracked_name = file_info.get('current_name', '')

            # Check if file/dir exists
            full_path = branch_dir / tracked_path
            if not full_path.exists():
                missing_files.append((file_id, tracked_path, tracked_name))
                if trace:
                    trace_logs.append(('missing_file', file_id, {'name': tracked_name, 'path': tracked_path}))

        return {
            'missing_files': missing_files,
            'untracked_files': [],
            'hash_mismatches': [],
            'needs_update': bool(missing_files),
            'trace_logs': trace_logs
        }

    # FULL MODE: Scan filesystem and perform complete reconciliation
    # Load ignore patterns from template using registry ignore handler
    # This gives us consistent ignore logic across entire system
    AIPASS_ROOT = Path.home() / "aipass_core"
    template_dir = AIPASS_ROOT / "cortex" / "templates" / "branch_template"

    ignore_config = load_ignore_patterns(template_dir)
    ignore_files = ignore_config.get('ignore_files', [])
    ignore_patterns = ignore_config.get('ignore_patterns', [])

    # Add reconciliation-specific ignores (branch metadata files)
    ignore_files.extend(['.branch_meta.json', '.template_registry.json'])

    # Scan current filesystem
    current_state = scan_branch_filesystem(
        branch_dir, template_dir, ignore_files, ignore_patterns, trace
    )

    # Merge scan trace logs into reconcile trace logs
    if trace and 'trace_logs' in current_state:
        trace_logs.extend(current_state['trace_logs'])

    if trace:
        trace_logs.append(('state_comparison', 'Comparing states', {
            'tracked_in_meta': len(file_tracking),
            'files_on_disk': len(current_state['files']),
            'dirs_on_disk': len(current_state['directories'])
        }))

    # Results
    missing_files = []      # Tracked but not on disk
    untracked_files = []    # On disk but not tracked
    hash_mismatches = []    # Content changed

    # Check 1: Files tracked but missing from disk
    if trace:
        trace_logs.append(('check_missing', 'Checking for missing files (tracked but not on disk)', {}))

    for file_id, file_info in file_tracking.items():
        tracked_path = file_info.get('path', '')
        tracked_name = file_info.get('current_name', '')

        # Check if file/dir exists on filesystem
        is_file = tracked_path in current_state['files']
        is_dir = tracked_path in current_state['directories']

        if not is_file and not is_dir:
            missing_files.append((file_id, tracked_path, tracked_name))
            if trace:
                trace_logs.append(('missing_file', file_id, {'name': tracked_name, 'path': tracked_path}))

    # Check 2: Files on disk but not tracked
    if trace:
        trace_logs.append(('check_untracked', 'Checking for untracked files (on disk but not tracked)', {}))

    # Build set of tracked paths for fast lookup
    tracked_paths = {info.get('path', '') for info in file_tracking.values()}

    for path, file_info in current_state['files'].items():
        if path not in tracked_paths:
            untracked_files.append((path, file_info['name']))
            if trace:
                trace_logs.append(('untracked_file', path, {'name': file_info['name']}))

    for path, dir_info in current_state['directories'].items():
        if path not in tracked_paths:
            untracked_files.append((path, dir_info['name']))
            if trace:
                trace_logs.append(('untracked_dir', path, {'name': dir_info['name']}))

    # Check 3: Hash mismatches (content changed)
    if trace:
        trace_logs.append(('check_hashes', 'Checking for content hash mismatches', {}))

    for file_id, file_info in file_tracking.items():
        tracked_path = file_info.get('path', '')
        tracked_hash = file_info.get('content_hash', '')

        # Only check files (directories have empty hash)
        if tracked_path in current_state['files'] and tracked_hash:
            current_hash = current_state['files'][tracked_path]['hash']

            if current_hash and current_hash != tracked_hash:
                hash_mismatches.append((file_id, tracked_path, file_info.get('current_name', '')))
                if trace:
                    trace_logs.append(('hash_mismatch', file_id, {
                        'expected': tracked_hash,
                        'got': current_hash
                    }))

    # Summary
    needs_update = bool(missing_files or untracked_files or hash_mismatches)

    if trace:
        trace_logs.append(('reconcile_complete', 'RECONCILIATION COMPLETE', {
            'missing_files': len(missing_files),
            'untracked_files': len(untracked_files),
            'hash_mismatches': len(hash_mismatches),
            'needs_update': needs_update
        }))

    return {
        'missing_files': missing_files,
        'untracked_files': untracked_files,
        'hash_mismatches': hash_mismatches,
        'needs_update': needs_update,
        'trace_logs': trace_logs
    }


def update_branch_meta_from_reconciliation(
    branch_meta: Dict,
    reconciliation: Dict,
    trace: bool = False
) -> Tuple[Dict, List]:
    """
    Update branch_meta to reflect current filesystem reality

    Args:
        branch_meta: Current branch metadata
        reconciliation: Results from reconcile_branch_state()
        trace: Enable trace logging

    Returns:
        Tuple of (updated branch_meta dict, trace_logs list)
    """
    trace_logs = []

    if trace:
        trace_logs.append(('update_start', 'Updating branch_meta from reconciliation results', {}))

    file_tracking = branch_meta.get("file_tracking", {})

    # Remove entries for missing files
    for file_id, path, name in reconciliation['missing_files']:
        if file_id in file_tracking:
            if trace:
                trace_logs.append(('remove_tracking', file_id, {'name': name, 'reason': 'File deleted'}))
            del file_tracking[file_id]

    # Update hashes for mismatched files
    # (We don't have current hash here, will be updated during normal operations)
    for file_id, path, name in reconciliation['hash_mismatches']:
        if file_id in file_tracking and trace:
            trace_logs.append(('hash_mismatch_noted', file_id, {'name': name, 'note': 'Will update on next operation'}))

    # Note: Untracked files will be added during next registry update

    if trace:
        trace_logs.append(('update_complete', f'Updated file_tracking: {len(file_tracking)} entries', {}))

    return (branch_meta, trace_logs)
