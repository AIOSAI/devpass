#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: memory_watcher.py - Memory File System Watcher
# Date: 2025-11-26
# Version: 1.0.0
# Category: memory_bank/handlers/monitor
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-26): Initial version
#     * Watches memory files for modifications
#     * Auto-updates line counts on file changes
#     * Triggers rollover when files exceed 600 lines
#
# CODE STANDARDS:
#   - Handler independence: Uses watchdog library
#   - Error handling: Returns status dicts (3-tier architecture)
#   - Pure handler - no CLI display imports
# =============================================

"""
Memory File System Watcher

Watches memory files (*.local.json, *.observations.json) for modifications.
On change, updates line counts and triggers rollover if needed.

Purpose:
    Automatic memory file monitoring without polling. Responds to filesystem
    events in real-time, keeping metadata accurate and triggering rollover
    when thresholds are exceeded.

Independence:
    Uses watchdog library for events. Delegates to line_counter and rollover
    handlers for processing. No direct service dependencies.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Infrastructure setup
AIPASS_ROOT = Path.home() / "aipass_core"
MEMORY_BANK_ROOT = Path.home() / "MEMORY_BANK"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))  # For MEMORY_BANK package imports

# Handler imports (domain-organized)
from MEMORY_BANK.apps.handlers.tracking.line_counter import update_line_count
from MEMORY_BANK.apps.handlers.monitor.detector import check_single_file

# Lazy logger import to avoid circular dependency with prax
_logger = None

def _get_logger():
    """Get prax logger lazily to avoid circular import"""
    global _logger
    if _logger is None:
        from prax.apps.modules.logger import system_logger
        _logger = system_logger
    return _logger

# Global observer instance
_observer: Optional[Observer] = None


# =============================================================================
# STARTUP CHECK (runs once per command, no daemon needed)
# =============================================================================

_startup_check_done = False


def _get_rollover_threshold(branch_name: str) -> int:
    """
    Get rollover threshold for a branch from config.

    Priority: per_branch config > defaults > hardcoded 600

    Args:
        branch_name: Branch name (uppercase, e.g., 'DEV_CENTRAL')

    Returns:
        Max lines threshold for rollover
    """
    import json

    config_path = MEMORY_BANK_ROOT / "memory_bank_json" / "memory_bank.config.json"

    try:
        with open(config_path) as f:
            config = json.load(f)

        # Check per-branch override first
        branch_limits = config.get('rollover', {}).get('per_branch', {}).get(branch_name, {})
        if 'max_lines' in branch_limits:
            return branch_limits['max_lines']

        # Fall back to defaults
        default_limit = config.get('rollover', {}).get('defaults', {}).get('max_lines')
        if default_limit is not None:
            return default_limit

    except Exception:
        pass

    # Final fallback
    return 600


def check_and_rollover() -> Dict[str, Any]:
    """
    Check all memory files and trigger rollover if any exceed their threshold.
    Also processes any new files in memory_pool.

    Threshold is determined per-branch from config (defaults to 600).

    This is a startup check - runs once per command, synchronous.
    No daemon or file watcher needed.

    Returns:
        Dict with check results and any rollover actions taken
    """
    global _startup_check_done

    # Only run once per process
    if _startup_check_done:
        return {'success': True, 'skipped': True, 'reason': 'Already checked this session'}

    _startup_check_done = True

    results = {
        'success': True,
        'files_checked': 0,
        'files_over_limit': [],
        'rollover_triggered': False,
        'memory_pool': None
    }

    # Get all branch paths
    branch_paths = _get_branch_paths()

    if not branch_paths:
        results['error'] = 'No branch paths found'
        return results

    # Check each branch for memory files over limit
    # Also sync current_lines metadata to keep it accurate
    lines_synced = 0
    for branch_path in branch_paths:
        branch = Path(branch_path)
        # Extract branch name from path (last component, uppercase)
        branch_name = branch.name.upper()

        # Get threshold for this branch (may differ per-branch)
        threshold = _get_rollover_threshold(branch_name)

        # Find memory files in this branch (skip DASHBOARD files - no rollover metadata)
        for pattern in ['*.local.json', '*.observations.json']:
            for memory_file in branch.glob(pattern):
                if memory_file.name.startswith('DASHBOARD'):
                    continue

                results['files_checked'] += 1

                try:
                    line_count = len(memory_file.read_text(encoding='utf-8').splitlines())

                    # Sync current_lines metadata if stale
                    try:
                        import json as _json
                        _data = _json.loads(memory_file.read_text(encoding='utf-8'))
                        meta_lines = _data.get('document_metadata', {}).get('status', {}).get('current_lines')
                        if meta_lines != line_count:
                            sync_result = update_line_count(memory_file)
                            if sync_result.get('success'):
                                lines_synced += 1
                                # Re-read actual line count after metadata update
                                line_count = len(memory_file.read_text(encoding='utf-8').splitlines())
                    except Exception:
                        pass  # Non-critical - sync is best-effort

                    if line_count > threshold:
                        results['files_over_limit'].append({
                            'file': str(memory_file),
                            'lines': line_count,
                            'threshold': threshold
                        })
                except Exception:
                    pass  # Skip files we can't read

    results['lines_synced'] = lines_synced

    # Trigger rollover if any files are over limit
    if results['files_over_limit']:
        results['rollover_triggered'] = True

        try:
            from MEMORY_BANK.apps.modules.rollover import execute_rollover
            execute_rollover()
        except Exception as e:
            results['rollover_error'] = str(e)
            results['success'] = False

    # Check memory_pool for new files to process
    results['memory_pool'] = _check_memory_pool()

    # Check plans for new files to vectorize
    results['plans'] = _check_plans()

    # Check code_archive for new files to index
    results['code_archive'] = _check_code_archive()

    return results


def _check_memory_pool() -> Dict[str, Any]:
    """
    Check memory_pool for new files and process if needed.

    Compares files in pool against configured keep_recent limit.
    If more files exist, runs processor to vectorize and archive.

    Returns:
        Dict with processing status
    """
    import json

    config_path = MEMORY_BANK_ROOT / "memory_bank_json" / "memory_bank.config.json"
    pool_path = MEMORY_BANK_ROOT / "memory_pool"

    # Load config
    try:
        with open(config_path) as f:
            config = json.load(f)
        pool_config = config.get('memory_pool', {})
    except Exception:
        return {'success': False, 'error': 'Could not load config'}

    # Check if enabled
    if not pool_config.get('enabled', False):
        return {'success': True, 'skipped': True, 'reason': 'memory_pool disabled'}

    # Count files in pool (excluding .archive)
    extensions = pool_config.get('supported_extensions', ['.md', '.txt'])
    keep_recent = pool_config.get('keep_recent', 10)

    files = []
    for ext in extensions:
        files.extend(pool_path.glob(f'*{ext}'))

    file_count = len(files)

    # If under limit, nothing to do
    if file_count <= keep_recent:
        return {
            'success': True,
            'files_in_pool': file_count,
            'keep_recent': keep_recent,
            'action': 'none'
        }

    # Files exceed limit - run processor
    try:
        from MEMORY_BANK.apps.handlers.intake.pool_processor import process_memory_pool
        result = process_memory_pool()
        return {
            'success': result.get('success', False),
            'files_processed': result.get('files_processed', 0),
            'files_archived': result.get('archive', {}).get('archived_count', 0),
            'action': 'processed'
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'action': 'failed'}


def _check_plans() -> Dict[str, Any]:
    """
    Check plans directory for files to vectorize.

    Processes any plan files that haven't been vectorized yet.

    Returns:
        Dict with processing status
    """
    import json

    config_path = MEMORY_BANK_ROOT / "memory_bank_json" / "memory_bank.config.json"

    # Load config
    try:
        with open(config_path) as f:
            config = json.load(f)
        plans_config = config.get('plans', {})
    except Exception:
        return {'success': False, 'error': 'Could not load config'}

    # Check if enabled
    if not plans_config.get('enabled', False):
        return {'success': True, 'skipped': True, 'reason': 'plans disabled'}

    # Get plans path and count files
    plans_path = MEMORY_BANK_ROOT / plans_config.get('path', 'plans')
    extensions = plans_config.get('supported_extensions', ['.md'])

    if not plans_path.exists():
        return {'success': True, 'skipped': True, 'reason': 'plans directory does not exist'}

    files = []
    for ext in extensions:
        files.extend(plans_path.glob(f'*{ext}'))

    file_count = len(files)

    if file_count == 0:
        return {'success': True, 'files_in_plans': 0, 'action': 'none'}

    # Process plans to vectors
    try:
        from MEMORY_BANK.apps.handlers.intake.plans_processor import process_plans
        result = process_plans()
        return {
            'success': result.get('success', False),
            'files_processed': result.get('files_processed', 0),
            'total_chunks': result.get('total_chunks', 0),
            'action': 'processed'
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'action': 'failed'}


def _check_code_archive() -> Dict[str, Any]:
    """
    Check code_archive for new files and index them.

    Returns:
        Dict with indexing status
    """
    try:
        from MEMORY_BANK.apps.handlers.archive.indexer import check_for_new_files
        return check_for_new_files()
    except Exception as e:
        return {'success': False, 'error': str(e)}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _get_branch_paths() -> list[Path]:
    """
    Get all branch paths from BRANCH_REGISTRY.json (silent - no logging)

    Returns:
        List of Path objects for each branch
    """
    import json

    registry_path = Path.home() / "BRANCH_REGISTRY.json"

    if not registry_path.exists():
        return []

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            branches = data.get('branches', [])

            paths = []
            for branch in branches:
                branch_path = Path(branch.get('path', ''))
                if branch_path.exists():
                    paths.append(branch_path)

            return paths
    except Exception:
        return []


def _is_memory_file(file_path: Path) -> bool:
    """
    Check if file is a memory file (*.local.json or *.observations.json)

    Args:
        file_path: Path to check

    Returns:
        True if memory file, False otherwise
    """
    name = file_path.name
    return (name.endswith('.local.json') or name.endswith('.observations.json'))


# =============================================================================
# FILE SYSTEM EVENT HANDLER
# =============================================================================

class MemoryFileWatcher(FileSystemEventHandler):
    """Watch for memory file modifications"""

    def __init__(self):
        super().__init__()
        # Track recent modifications to avoid duplicate processing
        self._recent_modifications = set()

    def on_modified(self, event):
        """Handle file modification events"""
        # Ignore directory events
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process memory files
        if not _is_memory_file(file_path):
            return

        # Skip if we just processed this file
        file_key = str(file_path)
        if file_key in self._recent_modifications:
            self._recent_modifications.discard(file_key)
            return

        _get_logger().info(f"[memory_watcher] Detected modification: {file_path.name}")

        # Step 1: Update line count metadata
        update_result = update_line_count(file_path)

        if not update_result['success']:
            _get_logger().error(f"[memory_watcher] Failed to update line count for {file_path.name}: {update_result.get('error')}")
            return

        current_lines = update_result.get('lines', 0)
        _get_logger().info(f"[memory_watcher] Updated {file_path.name}: {current_lines} lines")

        # Step 2: Check if rollover needed
        check_result = check_single_file(file_path)

        if not check_result['success']:
            _get_logger().error(f"[memory_watcher] Failed to check rollover for {file_path.name}: {check_result.get('error')}")
            return

        if check_result.get('should_rollover', False):
            trigger = check_result.get('trigger')
            _get_logger().warning(f"[memory_watcher] ROLLOVER TRIGGERED: {trigger}")

            # Import rollover module here to avoid circular imports
            from MEMORY_BANK.apps.modules.rollover import execute_rollover

            # Trigger rollover
            _get_logger().info(f"[memory_watcher] Triggering rollover for {file_path.name}")

            # Mark file as recently modified to avoid re-processing after rollover
            self._recent_modifications.add(file_key)

            # Execute rollover
            try:
                execute_rollover()
            except Exception as e:
                _get_logger().error(f"[memory_watcher] Rollover failed: {e}")


# =============================================================================
# WATCHER CONTROL FUNCTIONS
# =============================================================================

def start_memory_watcher() -> Dict[str, Any]:
    """
    Start watching memory files for modifications

    Starts watchdog observer to monitor all branch directories for memory
    file changes. Updates line counts and triggers rollover automatically.

    Returns:
        Dict with success status and watched paths
    """
    global _observer

    if _observer and _observer.is_alive():
        return {
            'success': False,
            'error': 'Watcher already running'
        }

    # Get all branch paths
    branch_paths = _get_branch_paths()

    if not branch_paths:
        return {
            'success': False,
            'error': 'No branch paths found in BRANCH_REGISTRY.json'
        }

    # Create watcher instance
    watcher = MemoryFileWatcher()

    # Create observer
    new_observer = Observer()

    # Schedule watcher for each branch path (silent - no logging during startup)
    watched_paths = []
    for branch_path in branch_paths:
        try:
            new_observer.schedule(watcher, str(branch_path), recursive=False)
            watched_paths.append(str(branch_path))
        except Exception:
            pass  # Skip invalid paths silently

    # Start observer
    new_observer.start()
    _observer = new_observer

    return {
        'success': True,
        'watched_paths': watched_paths,
        'count': len(watched_paths)
    }


def stop_memory_watcher() -> Dict[str, Any]:
    """
    Stop the memory file watcher

    Returns:
        Dict with success status
    """
    global _observer

    if not _observer or not _observer.is_alive():
        return {
            'success': False,
            'error': 'Watcher not running'
        }

    _observer.stop()
    _observer.join()
    _observer = None

    _get_logger().info("[memory_watcher] Stopped")

    return {
        'success': True,
        'message': 'Memory watcher stopped'
    }


def is_memory_watcher_active() -> bool:
    """
    Check if memory watcher is currently active

    Returns:
        True if watcher is running, False otherwise
    """
    return _observer is not None and _observer.is_alive()


def get_watcher_status() -> Dict[str, Any]:
    """
    Get current watcher status

    Returns:
        Dict with watcher status and details
    """
    active = is_memory_watcher_active()

    if not active:
        return {
            'active': False,
            'message': 'Watcher not running'
        }

    # Get watched paths
    branch_paths = _get_branch_paths()

    return {
        'active': True,
        'watched_directories': len(branch_paths),
        'paths': [str(p) for p in branch_paths]
    }


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    import argparse
    import time

    parser = argparse.ArgumentParser(
        description='Memory File Watcher - Monitor memory files for rollover'
    )
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'status'],
        help='Command to execute'
    )

    args = parser.parse_args()

    if args.command == 'start':
        result = start_memory_watcher()

        if result['success']:
            print(f"Started watching {result['count']} directories")
            print("Press Ctrl+C to stop...")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping...")
                stop_memory_watcher()
        else:
            print(f"Failed to start: {result.get('error')}")

    elif args.command == 'stop':
        result = stop_memory_watcher()

        if result['success']:
            print(result['message'])
        else:
            print(f"Failed to stop: {result.get('error')}")

    elif args.command == 'status':
        status = get_watcher_status()

        if status['active']:
            print(f"Watcher is ACTIVE")
            print(f"Watching {status['watched_directories']} directories:")
            for path in status['paths']:
                print(f"  - {path}")
        else:
            print("Watcher is INACTIVE")
