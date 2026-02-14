#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: rollover.py - Rollover Orchestration Module
# Date: 2025-11-16
# Version: 0.1.0
# Category: memory_bank/modules
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-16): Initial version - orchestrate rollover workflow
#
# CODE STANDARDS:
#   - Thin orchestration: Delegate all logic to handlers
#   - No business logic: Only coordinate workflow
#   - handle_command() pattern
# =============================================

"""
Rollover Orchestration Module

Coordinates the memory rollover workflow by calling handlers in sequence:
1. Detect rollover triggers (monitor/detector)
2. Extract oldest memories (rollover/extractor)
3. Generate embeddings (vector/embedder)
4. Store in Chroma (storage/chroma)

Purpose:
    Thin orchestration layer - no business logic implementation.
    All domain logic lives in handlers.
"""

import sys
from pathlib import Path
from typing import List, Dict

# Infrastructure setup
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))  # For MEMORY_BANK package imports

# Service imports
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header

# Handler imports (domain-organized)
from MEMORY_BANK.apps.handlers.monitor import detector
from MEMORY_BANK.apps.handlers.rollover import extractor
from MEMORY_BANK.apps.handlers.vector import embedder
from MEMORY_BANK.apps.handlers.tracking import line_counter
from MEMORY_BANK.apps.handlers.central_writer import update_central

# ChromaDB storage via subprocess (uses Memory Bank's Python 3.12)
import subprocess
import json

CHROMA_SUBPROCESS_SCRIPT = Path.home() / "MEMORY_BANK" / "apps" / "handlers" / "storage" / "chroma_subprocess.py"
MEMORY_BANK_PYTHON = Path.home() / "MEMORY_BANK" / ".venv" / "bin" / "python3"


def _store_vectors_subprocess(branch: str, memory_type: str, embeddings: list,
                               documents: list, metadatas: list, db_path: str | Path | None = None) -> dict:
    """
    Store vectors via subprocess using Memory Bank's Python 3.12.

    This ensures ChromaDB compatibility regardless of calling Python version.
    """
    # Convert numpy arrays to lists for JSON serialization
    embeddings_serializable = [
        emb.tolist() if hasattr(emb, 'tolist') else emb
        for emb in embeddings
    ]

    input_data = {
        'operation': 'store_vectors',
        'branch': branch,
        'memory_type': memory_type,
        'embeddings': embeddings_serializable,
        'documents': documents,
        'metadatas': metadatas,
        'db_path': str(db_path) if db_path else None
    }

    try:
        result = subprocess.run(
            [str(MEMORY_BANK_PYTHON), str(CHROMA_SUBPROCESS_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return {'success': False, 'error': result.stderr or 'Subprocess failed'}

        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Storage operation timed out'}
    except json.JSONDecodeError as e:
        return {'success': False, 'error': f'Invalid JSON response: {e}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# No other module imports (modules don't import modules)


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:  # noqa: ARG001
    """
    Handle rollover commands

    Commands supported:
    - rollover: Execute rollover for triggered branches
    - status: Show rollover statistics
    - check: Check which branches need rollover
    - sync-lines: Update line count metadata for all branches

    Args:
        command: Command name
        args: Additional arguments

    Returns:
        True if command handled, False otherwise
    """
    if command in ('--help', '-h', 'help'):
        print_help()
        return True

    if command == 'rollover':
        execute_rollover()
        return True

    elif command == 'status':
        show_status()
        return True

    elif command == 'check':
        check_triggers()
        return True

    elif command == 'sync-lines':
        sync_line_counts()
        return True

    return False


def print_help() -> None:
    """Display rollover module help"""
    console.print()
    header("Rollover Module - Memory Rollover Orchestration")
    console.print()
    console.print("[bold]USAGE:[/bold]")
    console.print("  python3 rollover.py <command>")
    console.print()
    console.print("[bold]COMMANDS:[/bold]")
    console.print("  [cyan]rollover[/cyan]    Execute rollover for files over 600 lines")
    console.print("  [cyan]status[/cyan]      Show rollover statistics for all branches")
    console.print("  [cyan]check[/cyan]       Check which files need rollover (dry run)")
    console.print("  [cyan]sync-lines[/cyan]  Update line count metadata for all branches")
    console.print("  [cyan]help[/cyan]        Show this help message")
    console.print()
    console.print("[bold]WORKFLOW:[/bold]")
    console.print("  1. Detect files over 600 lines")
    console.print("  2. Extract oldest entries (target ~500 lines)")
    console.print("  3. Generate embeddings via sentence-transformers")
    console.print("  4. Store vectors in local + global ChromaDB")
    console.print()


# =============================================================================
# ROLLOVER ORCHESTRATION
# =============================================================================

def execute_rollover() -> bool:
    """
    Execute rollover workflow for all triggered branches

    Workflow:
    1. Check all branches for triggers
    2. For each trigger:
       - Extract oldest 100 entries
       - Generate embeddings
       - Store in Chroma
    3. Report results
    """
    console.print()
    header("Memory Bank - Rollover Execution")
    console.print()

    # Step 1: Detect triggers
    console.print("[cyan]Checking for rollover triggers...[/cyan]")
    triggers_result = detector.check_all_branches()

    if not triggers_result['success']:
        logger.error(f"[rollover] Failed to check branches: {triggers_result.get('error', 'Unknown error')}")
        console.print("[red]✗[/red] Failed to check for rollover triggers")
        return False

    triggers = triggers_result.get('triggers', [])
    if not triggers:
        console.print("[green]✓[/green] No files need rollover")
        logger.info("[rollover] No rollover triggers detected")
        return True

    console.print(f"[green]✓[/green] Found {len(triggers)} files ready for rollover")
    logger.info(f"[rollover] Found {len(triggers)} files ready for rollover")
    console.print()

    # Process each trigger
    success_count = 0
    failed = []

    for trigger in triggers:
        console.print(f"[yellow]Processing:[/yellow] {trigger}")

        # Step 1: CREATE BACKUP (safety net)
        backup_result = extractor.create_rollover_backup(trigger.file_path)

        if not backup_result['success']:
            error_msg = backup_result.get('error', 'Backup failed')
            logger.error(f"[rollover] Backup failed for {trigger}: {error_msg}")
            failed.append((trigger, "backup", error_msg))
            continue  # Don't proceed without backup

        logger.info(f"[rollover] {backup_result.get('message')}")

        # Step 2: Extract memories (auto-calculates percentage)
        extract_result = extractor.extract_with_metadata(trigger.file_path)

        if not extract_result['success']:
            error_msg = extract_result.get('error', 'Unknown error')
            logger.error(f"[rollover] Extraction failed for {trigger}: {error_msg}")

            # RESTORE from backup
            restore_result = extractor.restore_from_backup(trigger.file_path)
            if restore_result['success']:
                logger.info(f"[rollover] Restored from backup after extraction failure")

            failed.append((trigger, "extraction", error_msg))
            continue

        memories = extract_result.get('entries', [])
        branch = extract_result.get('branch', '')
        memory_type = extract_result.get('type', 'unknown')
        old_lines = extract_result.get('old_lines', 0)
        new_lines = extract_result.get('new_lines', 0)

        if not branch:
            logger.error(f"[rollover] No branch found in extraction result for {trigger}")
            failed.append((trigger, "extraction", "No branch in result"))
            continue

        logger.info(f"[rollover] Extracted {len(memories)} items from {trigger} ({old_lines} → {new_lines} lines)")

        # Convert memory items to text for vectorization
        texts = _extract_text_from_memories(memories)

        # Step 3: Generate embeddings
        embed_result = embedder.encode_batch(texts)

        if not embed_result['success']:
            error_msg = embed_result.get('error', 'Unknown error')
            logger.error(f"[rollover] Embedding failed for {trigger}: {error_msg}")

            # RESTORE from backup
            restore_result = extractor.restore_from_backup(trigger.file_path)
            if restore_result['success']:
                logger.info(f"[rollover] Restored from backup after embedding failure")

            failed.append((trigger, "embedding", error_msg))
            continue

        embeddings = embed_result.get('embeddings', [])
        if not embeddings:
            logger.error(f"[rollover] No embeddings generated for {trigger}")
            failed.append((trigger, "embedding", "No embeddings in result"))
            continue

        logger.info(f"[rollover] Generated {len(embeddings)} embeddings for {trigger}")

        # Step 4: Prepare metadata for vectorization
        metadatas = []
        for memory in memories:
            metadata = memory.get('_metadata', {})
            metadata['timestamp'] = memory.get('timestamp', '')
            metadatas.append(metadata)

        # Step 5: Store in LOCAL branch Chroma (via subprocess for Python 3.12 compatibility)
        # Type assertions for Pylance (validated above with early returns)
        branch_str: str = branch
        memory_type_str: str = memory_type
        embeddings_list: list = embeddings

        local_chroma_path = _get_branch_local_chroma_path(branch_str)
        local_store_result = None

        if local_chroma_path:
            local_store_result = _store_vectors_subprocess(
                branch=branch_str,
                memory_type=memory_type_str,
                embeddings=embeddings_list,
                documents=texts,
                metadatas=metadatas,
                db_path=str(local_chroma_path)
            )

            if not local_store_result['success']:
                logger.warning(f"[rollover] Local storage failed for {branch}: {local_store_result.get('error')}")
                # Continue anyway - global storage is primary
            else:
                logger.info(f"[rollover] Stored {len(embeddings)} vectors in local Chroma for {branch}")

        # Step 6: Store in GLOBAL Memory Bank Chroma (via subprocess for Python 3.12 compatibility)
        global_store_result = _store_vectors_subprocess(
            branch=branch_str,
            memory_type=memory_type_str,
            embeddings=embeddings_list,
            documents=texts,
            metadatas=metadatas
            # db_path=None means global
        )

        if not global_store_result['success']:
            error_msg = global_store_result.get('error', 'Unknown error')
            logger.error(f"[rollover] Global storage failed for {trigger}: {error_msg}")

            # RESTORE from backup (CRITICAL - file was modified but storage failed)
            restore_result = extractor.restore_from_backup(trigger.file_path)
            if restore_result['success']:
                logger.info(f"[rollover] Restored from backup after storage failure")
            else:
                logger.error(f"[rollover] CRITICAL: Failed to restore from backup: {restore_result.get('error')}")

            failed.append((trigger, "global_storage", error_msg))
            continue

        logger.info(f"[rollover] Stored {len(embeddings)} vectors in global Chroma for {branch}")

        # Step 7: Update line count metadata
        update_result = line_counter.update_line_count(trigger.file_path)
        if update_result['success']:
            logger.info(f"[rollover] Updated line count metadata for {trigger.file_path.name}")
        else:
            logger.warning(f"[rollover] Failed to update line count for {trigger.file_path.name}: {update_result.get('error')}")

        # Success!
        success_count += 1
        global_collection = global_store_result.get('collection')
        global_total = global_store_result.get('total_vectors')

        # Report both local and global storage
        local_status = "✓ local" if local_store_result and local_store_result['success'] else "✗ local"
        console.print(
            f"  [green]✓[/green] Rolled over {len(memories)} items → {global_collection} "
            f"({old_lines} → {new_lines} lines, global: {global_total} vectors, {local_status})"
        )
        logger.info(f"[rollover] Successfully rolled over {trigger}: {len(memories)} items, {old_lines} → {new_lines} lines")

        # Update MEMORY_BANK.central.json after successful rollover
        try:
            update_central()
            logger.info("[rollover] Updated MEMORY_BANK.central.json")
        except Exception as e:
            logger.warning(f"[rollover] Failed to update central.json (non-critical): {e}")
            # Don't break rollover if central update fails

    # Report results
    console.print()
    if success_count > 0:
        console.print(f"[green]✓[/green] Rollover complete: {success_count}/{len(triggers)} successful")
        logger.info(f"[rollover] Rollover complete: {success_count}/{len(triggers)} successful")

    if failed:
        console.print()
        console.print("[red]Failed operations:[/red]")
        for trigger, stage, err in failed:
            console.print(f"  [red]✗[/red] {trigger} - {stage}: {err}")
        logger.error(f"[rollover] {len(failed)} operations failed")

    return success_count > 0


# =============================================================================
# PATH HELPERS
# =============================================================================

def _get_branch_local_chroma_path(branch_name: str) -> Path | None:
    """
    Get local .chroma path for branch

    Args:
        branch_name: Branch name (e.g., "SEED", "AIPASS")

    Returns:
        Path to branch's local .chroma directory, or None if branch not found

    Example:
        SEED → /home/aipass/aipass_core/seed/.chroma
        AIPASS → /home/aipass/.chroma
    """
    # Read registry to get branch path
    if not branch_name:
        return None

    registry = detector._read_registry()

    for branch in registry:
        if branch.get('name', '').upper() == branch_name.upper():
            branch_path = Path(branch.get('path', ''))
            if branch_path.exists():
                chroma_path = branch_path / '.chroma'
                # Auto-create .chroma directory if missing
                if not chroma_path.exists():
                    chroma_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"[rollover] Created local .chroma directory for {branch_name}")
                return chroma_path

    logger.warning(f"[rollover] Branch {branch_name} not found in registry")
    return None


# =============================================================================
# TEXT EXTRACTION HELPERS
# =============================================================================

def _extract_text_from_memories(memories: List[Dict]) -> List[str]:
    """
    Extract text content from memory items for vectorization

    Memory items have different structures:
    - sessions: 'activities' array (join into text)
    - observations: might have 'content' or 'text' field
    - generic: convert to JSON string

    Args:
        memories: List of memory items

    Returns:
        List of text strings for embedding
    """
    texts = []

    for memory in memories:
        # Try common text fields
        if 'activities' in memory and isinstance(memory['activities'], list):
            # Sessions type - join activities
            text = '\n'.join(str(a) for a in memory['activities'])
        elif 'content' in memory:
            text = str(memory['content'])
        elif 'text' in memory:
            text = str(memory['text'])
        elif 'message' in memory:
            text = str(memory['message'])
        else:
            # Fallback - convert to string representation
            text = str(memory)

        texts.append(text)

    return texts


# =============================================================================
# LINE COUNT SYNC
# =============================================================================

def sync_line_counts() -> None:
    """
    Update line count metadata for all branch memory files.

    Reads actual line counts and updates document_metadata.status.current_lines
    for all *.local.json and *.observations.json files in BRANCH_REGISTRY.
    """
    console.print()
    header("Memory Bank - Sync Line Counts")
    console.print()

    console.print("[cyan]Updating line counts for all memory files...[/cyan]")
    console.print()

    result = line_counter.update_all_memory_files()

    if result['success']:
        console.print(f"[green]✓[/green] Updated {result['updated']} files")
        if result['failed'] > 0:
            console.print(f"[yellow]![/yellow] {result['failed']} files failed:")
            for branch, mem_type, error in result.get('failures', []):
                console.print(f"    [red]✗[/red] {branch}.{mem_type}: {error}")
        logger.info(f"[rollover] Synced line counts: {result['updated']} updated, {result['failed']} failed")
    else:
        console.print(f"[red]✗[/red] Failed to sync line counts")
        logger.error("[rollover] Failed to sync line counts")

    console.print()


# =============================================================================
# STATUS & CHECKING
# =============================================================================

def show_status() -> None:
    """
    Show rollover statistics for all branches

    Displays:
    - Files checked
    - Files ready for rollover
    - Per-branch status (current/max lines)
    """
    console.print()
    header("Memory Bank - Rollover Status")
    console.print()

    # Get stats from detector
    stats_result = detector.get_rollover_stats()

    if not stats_result['success']:
        console.print(f"[red]✗[/red] Failed to get status: {stats_result.get('error', 'Unknown error')}")
        logger.error(f"[rollover] Failed to get status: {stats_result.get('error')}")
        return

    stats = stats_result

    # Summary
    console.print(f"[cyan]Branches:[/cyan] {stats['total_branches']}")
    console.print(f"[cyan]Files checked:[/cyan] {stats['files_checked']}")
    console.print(f"[cyan]Ready for rollover:[/cyan] {stats['files_ready']}")
    console.print()

    # Per-branch details
    if stats['branches']:
        console.print("[yellow]Branch Details:[/yellow]")
        console.print()

        for branch_name, branch_stats in stats['branches'].items():
            console.print(f"  [bold]{branch_name}[/bold]")

            for memory_type, file_stats in branch_stats.items():
                current = file_stats['current']
                max_lines = file_stats['max']
                ready = file_stats['ready']
                remaining = file_stats['remaining']

                status_icon = "🔴" if ready else "🟢"
                status_text = "READY" if ready else f"{remaining} remaining"

                console.print(
                    f"    {status_icon} {memory_type}: {current}/{max_lines} lines ({status_text})"
                )

            console.print()


def check_triggers() -> None:
    """
    Check which branches need rollover (without executing)

    Displays list of files that hit rollover threshold
    """
    console.print()
    header("Memory Bank - Rollover Check")
    console.print()

    triggers_result = detector.check_all_branches()

    if not triggers_result['success']:
        console.print(f"[red]✗[/red] Failed to check triggers: {triggers_result.get('error', 'Unknown error')}")
        logger.error(f"[rollover] Failed to check triggers: {triggers_result.get('error')}")
        return

    triggers = triggers_result.get('triggers', [])

    if not triggers:
        console.print("[green]✓[/green] No files need rollover")
        return

    console.print(f"[yellow]Found {len(triggers)} files ready for rollover:[/yellow]")
    console.print()

    for trigger in triggers:
        console.print(f"  • {trigger}")

    console.print()
    console.print(f"[dim]Run 'python3 memory_bank.py rollover' to process these files[/dim]")
    console.print()


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    import sys

    # Handle --help before argparse (module standard)
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h', 'help'):
        handle_command('help', [])
        sys.exit(0)

    # Execute command via handle_command
    command = sys.argv[1]
    if not handle_command(command, sys.argv[2:]):
        console.print(f"[red]Unknown command:[/red] {command}")
        console.print("Run with [cyan]help[/cyan] for available commands")
        sys.exit(1)
