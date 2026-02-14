#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: update_branch.py - Update AIPass Branch
# Date: 2025-11-15
# Version: 1.1.0
# Category: cortex
# Commands: update, update-branch, --help
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2025-11-15): Added drone compliance (Commands line in help)
#   - v1.0.0 (2025-11-04): Refactored implementation - ID-based tracking with handlers
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Update Branch Module

Updates existing AIPass branches from template while preserving all data:
- ID-based file tracking (detects renames vs new files)
- Deep merge template structure + existing values
- Safe rename operations
- Automatic archival of pruned files
- Full backup before modifications
- Batch update all branches
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Prax logger
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console
from rich.prompt import Confirm

# Handler imports - graceful degradation if handlers unavailable
HANDLERS_AVAILABLE = True
HANDLER_ERROR = None

try:
    from cortex.apps.handlers.branch.metadata import (
        get_branch_name
    )

    from cortex.apps.handlers.branch.registry import (
        load_registry,
        find_branch_in_registry,
        register_branch,
        sync_branch_registry
    )

    from cortex.apps.handlers.branch.file_ops import (
        create_backup,
        execute_rename,
        copy_template_file,
        archive_pruned_file
    )

    from cortex.apps.handlers.branch.reconcile import (
        reconcile_branch_state,
        update_branch_meta_from_reconciliation
    )

    from cortex.apps.handlers.registry.meta_ops import (
        load_template_registry,
        load_branch_meta,
        heal_branch_meta,
        save_branch_meta,
        generate_branch_meta_for_existing_branch,
        validate_template_registry,
        FILE_RENAMES
    )

    from cortex.apps.handlers.registry.decorators import (
        ensure_valid_registry
    )

    from cortex.apps.handlers.json.ops import (
        update_branch_file,
        load_migrations,
        prepare_json_backup_dir
    )

    from cortex.apps.handlers.branch.placeholders import (
        build_replacements_dict,
        apply_placeholder_replacements_to_dict
    )

    from cortex.apps.handlers.registry.ignore import (
        load_ignore_patterns,
        should_ignore
    )

    from cortex.apps.handlers.branch.change_detection import (
        detect_changes,
        detect_unregistered_items
    )

    from cortex.apps.handlers.registry.sync_ops import (
        needs_synchronization,
        synchronize_registry,
        preserve_tracking_snapshot
    )

    # NOTE: error.formatters and result_types removed - using direct console output
    # from cortex.apps.handlers.error.formatters import (
    #     display_validation_summary,
    #     display_placeholder_issues,
    #     display_change_detection,
    #     display_update_summary,
    #     display_update_result,
    #     display_registry_validation_errors,
    #     display_operation_errors,
    #     display_pruned_files_report
    # )

    # from cortex.apps.handlers.error.result_types import (
    #     OperationResult,
    #     CollectedResults,
    #     OperationStatus
    # )

    from cortex.apps.handlers.json import json_handler

except ImportError as e:
    # Define placeholder types for type checker
    get_branch_name = None  # type: ignore
    load_registry = None  # type: ignore
    find_branch_in_registry = None  # type: ignore
    register_branch = None  # type: ignore
    sync_branch_registry = None  # type: ignore
    create_backup = None  # type: ignore
    execute_rename = None  # type: ignore
    copy_template_file = None  # type: ignore
    archive_pruned_file = None  # type: ignore
    reconcile_branch_state = None  # type: ignore
    update_branch_meta_from_reconciliation = None  # type: ignore
    load_template_registry = None  # type: ignore
    load_branch_meta = None  # type: ignore
    heal_branch_meta = None  # type: ignore
    save_branch_meta = None  # type: ignore
    generate_branch_meta_for_existing_branch = None  # type: ignore
    validate_template_registry = None  # type: ignore
    FILE_RENAMES = None  # type: ignore
    update_branch_file = None  # type: ignore
    load_migrations = None  # type: ignore
    prepare_json_backup_dir = None  # type: ignore
    build_replacements_dict = None  # type: ignore
    apply_placeholder_replacements_to_dict = None  # type: ignore
    load_ignore_patterns = None  # type: ignore
    should_ignore = None  # type: ignore
    detect_changes = None  # type: ignore
    detect_unregistered_items = None  # type: ignore
    needs_synchronization = None  # type: ignore
    synchronize_registry = None  # type: ignore
    preserve_tracking_snapshot = None  # type: ignore
    json_handler = None  # type: ignore
    logger.error(f"Handler import failed: {e}")
    HANDLERS_AVAILABLE = False
    HANDLER_ERROR = str(e)

    # Define dummy decorator when handlers unavailable
    def ensure_valid_registry(func):  # type: ignore
        """Dummy decorator when handlers not available"""
        return func


# =============================================================================
# CONSTANTS
# =============================================================================

TEMPLATE_DIR = AIPASS_ROOT / "cortex" / "templates" / "branch_template"

# FILE_RENAMES is imported from meta_ops (no local definition needed)


# =============================================================================
# MAIN UPDATE LOGIC
# =============================================================================

@ensure_valid_registry
def update_branch(target_dir: Path, dry_run: bool = False, no_backup: bool = False, trace: bool = False) -> bool:
    """
    Update branch from template using ID-based file tracking

    Args:
        target_dir: Path to branch directory
        dry_run: If True, preview only (no changes)
        no_backup: If True, skip backup creation (faster updates)

    Strategy:
        1. Load .template_registry.json and .branch_meta.json
        2. Detect changes (renames, additions, pruned files)
        3. Create backup before any modifications
        4. Show preview of changes
        5. Ask for confirmation (unless dry_run)
        6. Execute changes (renames, additions, archival)
        7. Update JSON files with deep merge
        8. Update .branch_meta.json

    Args:
        target_dir: Path to branch directory
        dry_run: If True, show preview without executing

    Returns:
        True if successful, False otherwise
    """
    if not HANDLERS_AVAILABLE:
        console.print(f"[update_branch] Handlers unavailable: {HANDLER_ERROR}")
        return False

    # Validate path
    target_dir = target_dir.resolve()

    if not target_dir.exists():
        console.print(f"ERROR: Branch directory does not exist: {target_dir}")
        return False

    if not target_dir.is_dir():
        console.print(f"ERROR: Path is not a directory: {target_dir}")
        return False

    # Sync BRANCH_REGISTRY.json with filesystem reality (scan for .id.json files)
    if not dry_run:
        sync_results = sync_branch_registry()
        if sync_results["removed"] or sync_results["added"]:
            console.print(f"🔄 Registry sync complete:")
            if sync_results["removed"]:
                console.print(f"   Removed {len(sync_results['removed'])} stale entries: {', '.join(sync_results['removed'])}")
            if sync_results["added"]:
                console.print(f"   Added {len(sync_results['added'])} new branches: {', '.join(sync_results['added'])}")

    # Get branch info
    branch_name = get_branch_name(target_dir)
    branchname_upper = branch_name.upper().replace("-", "_")

    console.print(f"\n{'='*70}")
    console.print(f"UPDATE BRANCH - {branchname_upper}")
    console.print(f"{'='*70}")
    console.print(f"Path: {target_dir}")
    if dry_run:
        console.print("Mode: DRY RUN (preview only)")
    if trace:
        console.print("Mode: TRACE (detailed decision logging)")
    console.print()

    # Log operation start
    if not dry_run:
        json_handler.log_operation(
            'branch_update_started',
            {'branch': branchname_upper, 'path': str(target_dir)},
            'update_branch'
        )

    # Load template registry
    template_registry, error = load_template_registry()
    if not template_registry:
        console.print(f"ERROR: Could not load .template_registry.json")
        if error:
            console.print(f"  {error}")
        return False

    # Validate registry against filesystem
    registry_mismatches = validate_template_registry(template_registry, TEMPLATE_DIR)
    if registry_mismatches:
        console.print("\n⚠️  WARNING: Template registry validation errors detected")
        for error in registry_mismatches:
            console.print(f"  - {error}")

    # Detect unregistered items in template
    unregistered_items = detect_unregistered_items(TEMPLATE_DIR, template_registry)
    if unregistered_items["unregistered_files"] or unregistered_items["unregistered_dirs"]:
        console.print("\n" + "="*70)
        console.print("⚠️  WARNING: UNREGISTERED TEMPLATE ITEMS DETECTED")
        console.print("="*70)
        console.print("The following items exist in the template but are NOT registered")
        console.print("in .template_registry.json. They will be IGNORED during updates.")
        console.print()

        if unregistered_items["unregistered_dirs"]:
            console.print("Unregistered Directories:")
            for dir_path in sorted(unregistered_items["unregistered_dirs"]):
                console.print(f"  📁 {dir_path}")
            console.print()

        if unregistered_items["unregistered_files"]:
            console.print("Unregistered Files:")
            for file_path in sorted(unregistered_items["unregistered_files"]):
                console.print(f"  📄 {file_path}")
            console.print()

        console.print("ACTION REQUIRED:")
        console.print("  Run the template registry generator to register these items:")
        console.print(f"  python3 {AIPASS_ROOT}/cortex/apps/modules/regenerate_template_registry.py")
        console.print("="*70)
        console.print()

    # Load migrations (optional - may not exist)
    migrations = load_migrations(TEMPLATE_DIR)

    # Load branch metadata (may not exist for old branches)
    branch_meta_result: Tuple[Optional[Dict], Optional[str]] = load_branch_meta(target_dir)
    branch_meta: Optional[Dict] = branch_meta_result[0]
    error: Optional[str] = branch_meta_result[1]
    # Note: branch_meta can be None for old branches - this is OK

    # =========================================================================
    # PHASE 0: REGISTRY SYNC - Replace outdated branch registry with template
    # =========================================================================
    # This MUST happen first - can't trust outdated registry for any operations
    # Self-healing: Replace old structure/IDs with current template structure

    if trace:
        console.print(f"\n{'='*70}")
        console.print("PHASE 0: REGISTRY STRUCTURE SYNC")
        console.print(f"{'='*70}")

    # Save old registry BEFORE syncing for rename detection
    old_branch_tracking = preserve_tracking_snapshot(branch_meta)

    # Check if sync needed
    needs_sync, sync_reason = needs_synchronization(branch_meta, template_registry)

    if needs_sync:
        console.print(f"\n🔧 REGISTRY SYNC REQUIRED: {sync_reason}")
        console.print(f"   Replacing branch registry with current template structure...")

        # Synchronize registry (returns updated branch_meta dict)
        branch_meta = synchronize_registry(branch_meta, template_registry, target_dir, trace=trace)

        # Save synchronized registry
        save_branch_meta(target_dir, branch_meta)

        console.print(f"   ✅ Registry synchronized: {len(branch_meta['file_tracking'])} entries from template")
        console.print(f"   Registry now matches template structure (IDs, paths, names)")
    elif trace:
        console.print(f"   ✅ Registry structure current - no sync needed")

    # PHASE: Pre-flight reconciliation - sync branch_meta with filesystem reality
    if trace:
        console.print(f"\n{'='*70}")
        console.print("PHASE: PRE-FLIGHT RECONCILIATION")
        console.print(f"{'='*70}")

    # Ensure branch_meta is not None before reconciliation
    if branch_meta is None:
        # Generate metadata for branches that predate ID tracking
        if trace:
            console.print("   Branch has no metadata - generating from template...")
        branch_meta = generate_branch_meta_for_existing_branch(
            target_dir,
            branch_name,
            template_registry
        )
        if branch_meta is None:
            console.print("ERROR: Could not generate branch metadata")
            return False
        save_branch_meta(target_dir, branch_meta)
        if trace:
            console.print(f"   ✅ Metadata generated and saved")

    reconciliation = reconcile_branch_state(target_dir, branch_meta, trace=trace, fast_mode=True)

    if reconciliation['needs_update']:
        if trace or reconciliation['missing_files']:
            console.print(f"\n📋 Reconciliation found discrepancies:")
            console.print(f"   Missing files (tracked but deleted): {len(reconciliation['missing_files'])}")
            console.print(f"   Untracked files (added manually): {len(reconciliation['untracked_files'])}")
            console.print(f"   Hash mismatches (modified): {len(reconciliation['hash_mismatches'])}")

        # Update branch_meta to reflect current reality
        update_result: Tuple[Dict, List] = update_branch_meta_from_reconciliation(branch_meta, reconciliation, trace=trace)
        branch_meta = update_result[0]

        # Save corrected branch_meta
        save_branch_meta(target_dir, branch_meta)

        if trace:
            console.print(f"✅ branch_meta synchronized with filesystem")

    # Detect changes (use old_branch_tracking for rename detection)
    changes = detect_changes(
        template_registry,
        branch_meta,
        target_dir,
        branch_name,
        old_branch_tracking=old_branch_tracking,  # Pass old registry for rename detection
        trace=trace
    )

    renames = changes["renames"]
    additions = changes["additions"]
    updates = changes["updates"]
    pruned = changes["pruned"]

    total_changes = len(renames) + len(additions) + len(updates) + len(pruned)

    if total_changes == 0:
        console.print("\nNo changes detected - branch is up to date!")
        return True

    # Show preview
    console.print(f"\n{'='*70}")
    console.print("DETECTED CHANGES")
    console.print(f"{'='*70}")
    if renames:
        console.print(f"\nRenames ({len(renames)}):")
        for old, new, fid in renames:
            console.print(f"  {old} → {new}")
    if additions:
        console.print(f"\nAdditions ({len(additions)}):")
        for fname, fid in additions:
            console.print(f"  + {fname}")
    if updates:
        console.print(f"\nUpdates ({len(updates)}):")
        for fname, fid, oh, nh in updates:
            console.print(f"  ↻ {fname}")
    if pruned:
        console.print(f"\nPruned ({len(pruned)}):")
        for fname, fid in pruned:
            console.print(f"  - {fname}")

    # Dry run mode - stop here
    if dry_run:
        console.print("\nDRY RUN MODE - No changes executed")
        return True

    # Ask for confirmation
    console.print(f"\n{'='*70}")
    if not Confirm.ask("Execute these changes?", default=False):
        console.print("Update cancelled by user")
        return False

    # Create backup (unless --no-backup flag)
    backup_dir = None
    if not no_backup:
        console.print("\nCreating backup...")
        backup_dir = create_backup(target_dir)
        if not backup_dir:
            console.print("ERROR: Backup creation failed - aborting update")
            return False
        console.print(f"Backup created: {backup_dir}")
    else:
        console.print("\n⚠️  Skipping backup (--no-backup flag)")

    # Execute changes
    console.print(f"\n{'='*70}")
    console.print("EXECUTING CHANGES")
    console.print(f"{'='*70}")

    success_count = 0
    skip_count = 0
    error_count = 0

    # Execute renames first
    if renames:
        console.print(f"\nExecuting {len(renames)} rename(s)...")
        for old_name, new_name, file_id in renames:
            if execute_rename(target_dir, old_name, new_name, file_id):
                success_count += 1
            else:
                error_count += 1
                console.print(f"  ❌ Failed: {old_name} -> {new_name}")

    # Execute additions
    if additions:
        console.print(f"\nAdding {len(additions)} new file(s)...")
        for filename, file_id in additions:
            result, msg = copy_template_file(
                TEMPLATE_DIR,
                target_dir,
                filename,
                file_id,
                template_registry,
                branch_name,
                FILE_RENAMES
            )
            if result == "added":
                success_count += 1
            elif result == "skipped":
                skip_count += 1
            else:  # error
                error_count += 1
                error_reason = msg if msg else "Addition failed"
                console.print(f"  ❌ Failed to add {filename}: {error_reason}")

    # Execute updates (content changed)
    if updates:
        console.print(f"\nUpdating {len(updates)} file(s) with content changes...")
        for filename, file_id, old_hash, new_hash in updates:
            result, msg = copy_template_file(
                TEMPLATE_DIR,
                target_dir,
                filename,
                file_id,
                template_registry,
                branch_name,
                FILE_RENAMES,
                force_overwrite=True  # Force overwrite for content changes
            )
            if result == "updated":
                success_count += 1
            elif result == "added":
                # File was added (shouldn't happen in updates, but handle it)
                success_count += 1
            elif result == "protected":
                skip_count += 1
                # Python files are protected - this is expected behavior
            elif result == "skipped":
                skip_count += 1
            else:  # error
                error_count += 1
                error_reason = msg if msg else "Update failed"
                console.print(f"  ❌ Failed to update {filename}: {error_reason}")

    # Archive pruned files
    if pruned:
        console.print(f"\nArchiving {len(pruned)} pruned file(s)...")
        for filename, file_id in pruned:
            result = archive_pruned_file(target_dir, filename, file_id, AIPASS_ROOT)
            if result:
                success_count += 1
            # Note: Skip count for files not found (already deleted or never existed)

    # Update JSON files with deep merge (only if changes were made)
    if not renames and not additions and not updates and not pruned:
        # No changes - skip JSON updates
        pass
    else:
        # Changes detected - update JSON files to merge template updates

        # Build replacements dict
        replacements = build_replacements_dict(
            branch_name=branch_name,
            target_dir=target_dir,
            repo="unknown",
            profile="unknown"
        )

        # Prepare JSON backup directory using handler
        timestamp = datetime.now().strftime("%Y%m%d")
        json_backup_dir = prepare_json_backup_dir(target_dir)

        # List of JSON files to update (from template)
        json_files_to_update = [
            (f"{branchname_upper}.json", "PROJECT.json"),
            (f"{branchname_upper}.local.json", "LOCAL.json"),
            (f"{branchname_upper}.observations.json", "OBSERVATIONS.json"),
            (f"{branchname_upper}.ai_mail.json", "AI_MAIL.json"),
            (f"{branchname_upper}.id.json", "BRANCH.ID.json"),
            ("README.json", "README.json"),
        ]

        for branch_file, template_file in json_files_to_update:
            branch_file_path = target_dir / branch_file
            template_file_path = TEMPLATE_DIR / template_file

            # Skip if template doesn't exist
            if not template_file_path.exists():
                continue

            success, error_msg = update_branch_file(
                branch_file=branch_file_path,
                template_file=template_file_path,
                backup_dir=json_backup_dir,
                timestamp=timestamp,
                file_label=branch_file,
                replacements=replacements,
                apply_placeholders_func=apply_placeholder_replacements_to_dict,
                migrations=migrations
            )

            if success:
                success_count += 1
            else:
                error_count += 1
                reason = error_msg if error_msg else "JSON merge/update failed"
                console.print(f"  ❌ Failed to update {branch_file}: {reason}")

    # Update/Create .branch_meta.json (silent)

    if branch_meta:
        # Existing metadata - regenerate file tracking and update timestamp
        updated_meta = generate_branch_meta_for_existing_branch(
            target_dir,
            branch_name,
            template_registry
        )
        if updated_meta:
            # Preserve branch_created if it exists
            if "branch_created" in branch_meta and branch_meta["branch_created"] != "unknown":
                updated_meta["branch_created"] = branch_meta["branch_created"]
            branch_meta = updated_meta
        else:
            # Fallback: just update timestamp
            branch_meta["last_updated"] = datetime.now().date().isoformat()
    else:
        # No metadata exists - create it for old branch
        console.print("  Branch predates ID tracking - generating metadata...")
        branch_meta = generate_branch_meta_for_existing_branch(
            target_dir,
            branch_name,
            template_registry
        )
        if not branch_meta:
            console.print("  WARNING: Metadata generation failed")

    # Save metadata
    if branch_meta:
        if save_branch_meta(target_dir, branch_meta):
            console.print(f"  Metadata updated ({len(branch_meta.get('file_tracking', {}))} files tracked)")
        else:
            console.print(f"  WARNING: Metadata save failed")

    # PHASE: Post-flight verification - check all expected files actually exist
    if trace:
        console.print(f"\n{'='*70}")
        console.print("PHASE: POST-FLIGHT VERIFICATION")
        console.print(f"{'='*70}")

    # At this point, branch_meta must exist (either loaded, generated, or synchronized)
    if branch_meta is None:
        console.print("ERROR: Branch metadata is None - cannot verify")
        return False

    verification = reconcile_branch_state(target_dir, branch_meta, trace=trace, fast_mode=True)

    if verification['missing_files']:
        console.print(f"\n{'='*70}")
        console.print(f"❌ POST-FLIGHT VERIFICATION FAILED")
        console.print(f"{'='*70}")
        console.print(f"Missing files after update (should exist but don't):\n")

        for idx, (file_id, path, name) in enumerate(verification['missing_files'], 1):
            console.print(f"{idx}. ❌ Missing: {name}")
            console.print(f"   Path: {path}")
            console.print(f"   ID: {file_id}")

        console.print(f"\n{'='*70}")
        error_count += len(verification['missing_files'])

    elif trace:
        console.print(f"✅ All expected files verified present")

    # Summary
    console.print(f"\n{'='*70}")
    console.print("UPDATE SUMMARY")
    console.print(f"{'='*70}")
    console.print(f"Successful: {success_count}")
    console.print(f"Skipped: {skip_count}")
    console.print(f"Errors: {error_count}")
    if backup_dir:
        console.print(f"Backup: {backup_dir}")
    console.print()
    console.print(f"Changes: {len(renames)} renames, {len(additions)} additions, {len(updates)} updates, {len(pruned)} pruned")

    success = error_count == 0
    if success:
        console.print("\n✅ Update completed successfully!")
    else:
        console.print("\n❌ Update completed with errors")

    # Log operation completion and update stats
    if not dry_run:
        json_handler.log_operation(
            'branch_update_completed',
            {
                'branch': branchname_upper,
                'success': success,
                'changes': {
                    'renames': len(renames),
                    'additions': len(additions),
                    'pruned': len(pruned)
                },
                'results': {
                    'success_count': success_count,
                    'skip_count': skip_count,
                    'error_count': error_count
                }
            },
            'update_branch'
        )

        # Update data metrics
        if success:
            json_handler.increment_counter('update_branch', 'branches_updated')
            json_handler.increment_counter('update_branch', 'operations_successful')
        else:
            json_handler.increment_counter('update_branch', 'operations_failed')

    return success


# =============================================================================
# BATCH OPERATIONS
# =============================================================================

def update_all_branches(dry_run: bool = False, no_backup: bool = False) -> Tuple[int, int]:
    """
    Update all branches from BRANCH_REGISTRY.json

    Args:
        dry_run: If True, preview only
        no_backup: If True, skip backup creation (faster updates)

    Returns:
        Tuple of (success_count, total_count)
    """
    if not HANDLERS_AVAILABLE:
        console.print(f"[update_all_branches] Handlers unavailable: {HANDLER_ERROR}")
        return (0, 0)

    # Load branch registry
    registry = load_registry()
    if not registry:
        console.print("ERROR: Could not load BRANCH_REGISTRY.json")
        return (0, 0)

    branches = registry.get("branches", [])
    total_branches = len(branches)

    console.print(f"\n{'='*70}")
    console.print(f"BATCH UPDATE - {total_branches} branches")
    console.print(f"{'='*70}")
    if dry_run:
        console.print("Mode: DRY RUN (preview only)\n")

    # Log batch operation start
    if not dry_run:
        json_handler.log_operation(
            'batch_update_started',
            {'total_branches': total_branches},
            'update_branch'
        )

    success_count = 0
    failed_branches = []

    for i, branch_info in enumerate(branches, 1):
        branch_path = Path(branch_info["path"])
        branch_name = branch_info["name"]

        console.print(f"\n[{i}/{total_branches}] {branch_name}")
        console.print(f"Path: {branch_path}")
        console.print("-" * 70)

        # Skip backup directories
        if "/backups/" in str(branch_path) or str(branch_path).endswith("/backups"):
            console.print(f"INFO: Skipping backup directory")
            continue

        if not branch_path.exists():
            console.print(f"WARNING: Branch directory not found - skipping")
            failed_branches.append((branch_name, "Directory not found"))
            continue

        try:
            success = update_branch(branch_path, dry_run=dry_run, no_backup=no_backup)
            if success:
                success_count += 1
            else:
                failed_branches.append((branch_name, "Update failed"))
        except Exception as e:
            logger.error(f"Batch update failed for {branch_name}: {e}")
            console.print(f"ERROR: {e}")
            failed_branches.append((branch_name, str(e)))

    # Summary
    console.print(f"\n{'='*70}")
    console.print("BATCH UPDATE SUMMARY")
    console.print(f"{'='*70}")
    console.print(f"Total branches: {total_branches}")
    console.print(f"Successful: {success_count}")
    if failed_branches:
        console.print(f"Failed: {len(failed_branches)}")
        console.print("\nFailed branches:")
        for branch_name, reason in failed_branches:
            console.print(f"  - {branch_name}: {reason}")

    # Log batch operation completion
    if not dry_run:
        json_handler.log_operation(
            'batch_update_completed',
            {
                'total': total_branches,
                'successful': success_count,
                'failed': len(failed_branches),
                'failed_branches': [name for name, _ in failed_branches]
            },
            'update_branch'
        )

        # Update data metrics
        data = json_handler.load_json('update_branch', 'data')
        current_batch_runs = data.get('total_batch_runs', 0) if data else 0
        json_handler.update_data_metrics(
            'update_branch',
            total_batch_runs=current_batch_runs + 1,
            last_batch_total=total_branches,
            last_batch_successful=success_count
        )

    return (success_count, total_branches)


# =============================================================================
# MODULE INTERFACE
# =============================================================================

def handle_command(args) -> bool:
    """
    Orchestrator interface for update_branch

    Args:
        args: Command arguments

    Returns:
        True if command handled, False otherwise
    """
    # Check if this module should handle the command FIRST
    if not hasattr(args, 'command') or args.command != 'update-branch':
        return False

    # Then check if handlers are available
    if not HANDLERS_AVAILABLE:
        console.print(f"[update_branch] Handlers unavailable: {HANDLER_ERROR}")
        return True

    # Check for batch update flag
    if hasattr(args, 'all_branches') and args.all_branches:
        dry_run = getattr(args, 'dry_run', False)
        success_count, total_count = update_all_branches(dry_run=dry_run)
        return success_count == total_count

    # Single branch update
    if not hasattr(args, 'target_directory') or not args.target_directory:
        console.print("Error: target_directory required")
        console.print("Usage: cortex update-branch <target_directory> [--dry-run]")
        console.print("   or: cortex update-branch --all [--dry-run]")
        return True

    target_dir = Path(args.target_directory).resolve()
    dry_run = getattr(args, 'dry_run', False)

    return update_branch(target_dir, dry_run=dry_run)


# =============================================================================
# DRONE COMPLIANCE - HELP SYSTEM
# =============================================================================

def print_help():
    """Display drone-compliant help output"""
    console.print()
    console.print("="*70)
    console.print("UPDATE BRANCH - AIPass Branch Update")
    console.print("="*70)
    console.print()
    console.print("Updates existing AIPass branches from template with ID tracking.")
    console.print()
    console.print("USAGE:")
    console.print("  python3 update_branch.py <target_directory> [--dry-run] [--no-backup] [--trace]")
    console.print("  python3 update_branch.py --all [--dry-run] [--no-backup]")
    console.print("  cortex update <target_directory>")
    console.print("  cortex update-branch <target_directory>")
    console.print()
    console.print("EXAMPLES:")
    console.print("  python3 update_branch.py /home/aipass/aipass_core/my_branch")
    console.print("  python3 update_branch.py /home/aipass/aipass_core/my_branch --dry-run")
    console.print("  python3 update_branch.py --all")
    console.print()
    console.print("WHAT IT DOES:")
    console.print("  - Detects changes between template and branch (renames, additions, updates)")
    console.print("  - Creates backup before modifications (unless --no-backup)")
    console.print("  - Executes file renames, additions, and updates")
    console.print("  - Updates JSON files with deep merge")
    console.print("  - Archives pruned files")
    console.print()
    console.print("FLAGS:")
    console.print("  --dry-run     Preview changes without executing")
    console.print("  --no-backup   Skip backup creation (faster)")
    console.print("  --trace       Enable detailed decision logging")
    console.print("  --all         Update all branches in registry")
    console.print()
    console.print("REQUIREMENTS:")
    console.print("  - Target directory must exist")
    console.print("  - User confirmation required (unless --dry-run)")
    console.print()
    console.print("="*70)
    console.print()
    console.print("Commands: update, update-branch, --help")
    console.print()


# =============================================================================
# STANDALONE EXECUTION (for testing/debugging)
# =============================================================================

if __name__ == "__main__":
    import sys

    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    # Parse arguments
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    batch_mode = '--all' in args
    no_backup = '--no-backup' in args
    trace = '--trace' in args

    # Remove flags from args
    args = [a for a in args if a not in ['--dry-run', '--all', '--no-backup', '--trace']]

    # Check if we have command to execute
    if batch_mode:
        # Batch update all branches
        success_count, total_count = update_all_branches(dry_run=dry_run, no_backup=no_backup)
        sys.exit(0 if success_count == total_count else 1)
    elif args:
        # Single branch update
        target_path = Path(args[0]).resolve()
        success = update_branch(target_path, dry_run=dry_run, no_backup=no_backup, trace=trace)
        sys.exit(0 if success else 1)

    # No arguments - show status
    console.print("\n" + "="*60)
    console.print("update_branch - Module Status Report")
    console.print("="*60)

    console.print(f"\nModule: update_branch.py")
    console.print(f"Purpose: Update AIPass branches from template with ID tracking")
    console.print(f"Status: {'Ready' if HANDLERS_AVAILABLE else 'Handlers Missing'}")

    if HANDLERS_AVAILABLE:
        console.print(f"\nHandlers:")
        console.print(f"  metadata (get_branch_name)")
        console.print(f"  registry (load_registry)")
        console.print(f"  file_ops (create_backup, execute_rename, copy_template_file, archive_pruned_file)")
        console.print(f"  meta_ops (load_template_registry, load_branch_meta, save_branch_meta, generate_branch_meta_for_existing_branch)")
        console.print(f"  json_ops (update_branch_file)")
        console.print(f"  placeholders (build_replacements_dict, apply_placeholder_replacements_to_dict)")
        console.print(f"\nReady to update branches!")
    else:
        console.print(f"\nHandler Error:")
        console.print(f"  {HANDLER_ERROR}")

    console.print(f"\nUsage:")
    console.print(f"  Direct: python3 update_branch.py <target_directory> [--dry-run]")
    console.print(f"  Direct: python3 update_branch.py --all [--dry-run]")
    console.print(f"  Orchestrator: cortex update-branch <target_directory>")
    console.print(f"  Orchestrator: cortex update-branch --all")
    console.print("="*60 + "\n")
