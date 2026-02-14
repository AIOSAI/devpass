#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: error_handler/formatters.py
# Date: 2025-11-07
# Version: 1.0.0
# Category: cli/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-07): Initial implementation - Console formatters
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Error Handler Console Output Formatters

Functions for formatting operation results for console output.
"""

from typing import Optional
from rich.console import Console
from .result_types import OperationResult, OperationStatus, CollectedResults

console = Console()


def format_success(operation: str, reason: Optional[str] = None, verbose: bool = False) -> str:
    """
    Format success message

    Args:
        operation: Operation name
        reason: Optional reason/details
        verbose: Include detailed information

    Returns:
        Formatted string
    """
    if verbose and reason:
        return f"✅ {operation}: {reason}"
    else:
        return f"✅ {operation} completed"


def format_skip(operation: str, reason: str, verbose: bool = False) -> str:
    """
    Format skip message

    Args:
        operation: Operation name
        reason: Why it was skipped
        verbose: Include detailed information

    Returns:
        Formatted string
    """
    if verbose:
        return f"⏭️  {operation}: {reason}"
    else:
        return f"⏭️  {operation}: {reason}"  # Always show reason for skips


def format_error(operation: str, error: str, verbose: bool = False) -> str:
    """
    Format error message

    Args:
        operation: Operation name
        error: Error message
        verbose: Include detailed information

    Returns:
        Formatted string
    """
    if verbose:
        return f"❌ {operation} failed: {error}"
    else:
        # Show first line of error only
        error_first_line = error.split('\n')[0]
        return f"❌ {operation} failed: {error_first_line}"


def format_result(result: OperationResult, verbose: bool = False) -> str:
    """
    Format OperationResult for console output

    Args:
        result: OperationResult to format
        verbose: Include detailed information

    Returns:
        Formatted string
    """
    if result.status == OperationStatus.SUCCESS:
        return format_success(result.operation, result.reason, verbose)
    elif result.status == OperationStatus.SKIPPED:
        return format_skip(result.operation, result.reason, verbose)
    else:  # FAILED
        return format_error(result.operation, result.reason, verbose)


def format_summary(collected: CollectedResults, verbose: bool = False) -> str:
    """
    Format CollectedResults summary

    Args:
        collected: CollectedResults to format
        verbose: Include detailed breakdown

    Returns:
        Formatted summary string
    """
    summary = collected.summary()

    if not verbose:
        return summary

    # Verbose format with breakdown
    lines = [
        "="*70,
        "SUMMARY",
        "="*70,
        summary,
    ]

    # Add failure details if any
    if collected.failed > 0:
        lines.append("\nFailed Operations:")
        for result in collected.get_failures():
            lines.append(f"  ❌ {result.operation}: {result.reason}")

    # Add skip details if any
    if collected.skipped > 0:
        lines.append("\nSkipped Operations:")
        for result in collected.get_skipped():
            lines.append(f"  ⏭️  {result.operation}: {result.reason}")

    lines.append("="*70)

    return "\n".join(lines)


def format_progress(current: int, total: int, operation: str) -> str:
    """
    Format progress indicator

    Args:
        current: Current operation number
        total: Total operations
        operation: Current operation name

    Returns:
        Formatted progress string
    """
    percentage = int((current / total) * 100) if total > 0 else 0
    return f"[{current}/{total} - {percentage}%] {operation}"


def format_batch_header(operation: str, total: int) -> str:
    """
    Format header for batch operations with Rich styling

    Args:
        operation: Batch operation name
        total: Total number of operations

    Returns:
        Formatted header with Rich markup
    """
    title = operation.replace('_', ' ').title()
    lines = [
        "",
        "─" * 70,
        f"[bold]{title}[/bold] [dim]({total} operations)[/dim]",
        "─" * 70,
    ]
    return "\n".join(lines)


def display_validation_summary(validation_errors: list) -> None:
    """
    Display concise summary of placeholder validation errors

    Args:
        validation_errors: List of validation error dicts from file_ops
        Each dict contains: file, placeholder_details, available_keys

    Note:
        Prints directly to console. Use this from modules instead of
        implementing display logic in the module itself.
    """
    if not validation_errors:
        return

    console.print(f"\n[yellow]⚠️ Placeholder validation warnings ({len(validation_errors)} files):[/yellow]")
    for i, error in enumerate(validation_errors, 1):
        error_msg = format_placeholder_validation_error(
            error['file'],
            error['placeholder_details'],
            error['available_keys'],
            verbose=False
        )
        console.print(f"{i}. {error_msg.lstrip()}")


def display_placeholder_issues(placeholder_issues: list, target_dir, replacements: dict) -> None:
    """
    Display placeholder issues found during final validation

    Args:
        placeholder_issues: List of (file_path, placeholder_details) tuples
        target_dir: Base directory for relative path calculation
        replacements: Dict of available replacement keys

    Note:
        Prints directly to console with clear summary.
    """
    if not placeholder_issues:
        return

    console.print(f"\n[red]❌ ERROR: Unreplaced template placeholders detected ({len(placeholder_issues)} files)[/red]")
    for i, (file_path, placeholder_details) in enumerate(placeholder_issues, 1):
        from pathlib import Path
        relative_path = Path(file_path).relative_to(target_dir)
        error_msg = format_placeholder_validation_error(
            str(relative_path),
            placeholder_details,
            list(replacements.keys()),
            verbose=False
        )
        console.print(f"{i}. {error_msg.lstrip()}")
    console.print(f"\n[yellow]⚠️ Branch created but has placeholder issues - check files above[/yellow]")


def format_batch_footer(collected: CollectedResults) -> str:
    """
    Format footer for batch operations with Rich styling

    Args:
        collected: CollectedResults from batch

    Returns:
        Formatted footer with Rich markup
    """
    lines = [
        "",
        "─" * 70,
        f"[bold]SUMMARY:[/bold] {collected.summary()}",
        "─" * 70,
        ""
    ]
    return "\n".join(lines)


def format_placeholder_validation_error(
    file_path: str,
    placeholder_details: list,
    available_keys: list,
    verbose: bool = False
) -> str:
    """
    Format placeholder validation error - concise by default, verbose on request

    Args:
        file_path: Path to file with unreplaced placeholders
        placeholder_details: List of dicts with placeholder info
        available_keys: List of available replacement keys
        verbose: If True, show full context. If False, show summary only.

    Returns:
        Formatted error message (concise summary or verbose details)

    Note:
        Full details are always logged to error handler JSON logs.
        Terminal output is kept concise by default to avoid overwhelming the user.
    """
    if not verbose:
        # Concise mode - just show file and placeholder names
        placeholder_names = [detail['placeholder'] for detail in placeholder_details]
        return f"  ❌ {file_path}: {len(placeholder_details)} placeholders ({', '.join(placeholder_names[:3])}{'...' if len(placeholder_names) > 3 else ''})"

    # Verbose mode - full details
    lines = [
        "",
        "="*70,
        "❌ ERROR: UNREPLACED PLACEHOLDERS DETECTED",
        "="*70,
        f"File: {file_path}",
        f"\n⚠️ Found {len(placeholder_details)} unreplaced placeholder(s):\n"
    ]

    for detail in placeholder_details:
        # Build placeholder display without triggering validator
        lines.append(f"  Placeholder: {'{{'}{detail['placeholder']}{'}}'}")
        lines.append(f"  Line: {detail['line_number']}")
        lines.append(f"  Content: {detail['line_content']}")
        lines.append(f"\n  Context:")
        lines.append(detail['context'])
        lines.append("")

    lines.append("⚠️ Available replacement keys:")
    for key in sorted(available_keys):
        lines.append(f"  - {key}")
    lines.append("="*70)
    lines.append("")

    return "\n".join(lines)


def display_change_detection(renames: list, additions: list, updates: list, pruned: list) -> None:
    """
    Display detected changes between template and branch

    Args:
        renames: List of (old_name, new_name, file_id) tuples
        additions: List of (file_name, file_id) tuples
        updates: List of (name, file_id, old_hash, new_hash) tuples
        pruned: List of (file_name, file_id) tuples

    Note:
        Prints directly to console with detailed file listings.
    """
    console.print(f"\n{'='*70}")
    console.print("[bold]CHANGES DETECTED[/bold]")
    console.print(f"{'='*70}")

    # Show renames with details
    if renames:
        console.print(f"\n[yellow]Renames: {len(renames)}[/yellow]")
        for idx, (old_name, new_name, file_id) in enumerate(renames, 1):
            console.print(f"  {idx}. {old_name} → {new_name} [dim](ID: {file_id})[/dim]")

    # Show additions with details
    if additions:
        console.print(f"\n[green]Additions: {len(additions)}[/green]")
        for idx, (file_name, file_id) in enumerate(additions, 1):
            console.print(f"  {idx}. {file_name} [dim](ID: {file_id})[/dim]")

    # Show updates with details
    if updates:
        console.print(f"\n[blue]Updates: {len(updates)}[/blue]")
        for idx, (file_name, file_id, old_hash, new_hash) in enumerate(updates, 1):
            console.print(f"  {idx}. {file_name} [dim](ID: {file_id})[/dim]")

    # Show pruned with details
    if pruned:
        console.print(f"\n[red]Pruned: {len(pruned)}[/red]")
        for idx, (file_name, file_id) in enumerate(pruned, 1):
            console.print(f"  {idx}. {file_name} [dim](ID: {file_id})[/dim]")

    if not renames and not additions and not updates and not pruned:
        console.print("\n[dim]No changes detected - branch matches template[/dim]")

    console.print(f"{'='*70}")


def display_update_summary(
    success_count: int,
    skip_count: int,
    error_count: int,
    backup_dir: str,
    renames_count: int = 0,
    additions_count: int = 0,
    updates_count: int = 0,
    pruned_count: int = 0
) -> None:
    """
    Display update operation summary

    Args:
        success_count: Number of successful operations
        skip_count: Number of skipped operations
        error_count: Number of failed operations
        backup_dir: Path to backup directory
        renames_count: Number of renames detected
        additions_count: Number of additions detected
        updates_count: Number of content updates detected
        pruned_count: Number of pruned files detected

    Note:
        Prints directly to console. Use this from update_branch module.
    """
    console.print(f"\n{'='*70}")
    console.print("[bold]UPDATE SUMMARY[/bold]")
    console.print(f"{'='*70}")

    # Change counts
    if renames_count > 0 or additions_count > 0 or updates_count > 0 or pruned_count > 0:
        console.print(f"Changes: {renames_count} renames, {additions_count} additions, {updates_count} updates, {pruned_count} pruned")

    # Operation results
    console.print(f"[green]Added/Updated: {success_count}[/green]")
    if skip_count > 0:
        console.print(f"[yellow]Skipped: {skip_count}[/yellow] [dim](already exist)[/dim]")
    if error_count > 0:
        console.print(f"[red]Errors: {error_count}[/red]")

    console.print(f"Backup: [dim]{backup_dir}[/dim]")
    console.print(f"{'='*70}")


def display_update_result(success: bool) -> None:
    """
    Display final update result

    Args:
        success: True if update completed without errors

    Note:
        Prints directly to console. Use this from update_branch module.
    """
    if success:
        console.print("\n[green]✅ Update complete![/green]")
    else:
        console.print("\n[red]❌ Update completed with errors - check backup if needed[/red]")


def display_operation_errors(results: 'CollectedResults') -> None:
    """
    Display failed operations with detailed context

    Args:
        results: CollectedResults from update operations

    Note:
        Shows numbered list of all failures with detailed context
    """
    failures = results.get_failures()

    if not failures:
        return

    console.print(f"\n{'='*70}")
    console.print(f"[bold red]OPERATION FAILURES ({len(failures)})[/bold red]")
    console.print(f"{'='*70}")

    for i, result in enumerate(failures, 1):
        console.print(f"\n[bold]{i}. {result.operation.upper()}[/bold]")
        console.print(f"   [red]Reason: {result.reason}[/red]")
        if result.details:
            for key, value in result.details.items():
                console.print(f"   [dim]{key}: {value}[/dim]")

    console.print(f"{'='*70}")


def display_pruned_files_report(pruned_list: list, template_registry: dict, branch_name: str) -> None:
    """
    Display pruned files with ID mismatch warnings

    Args:
        pruned_list: List of (filename, file_id) tuples that were pruned
        template_registry: Template registry to check for ID mismatches
        branch_name: Name of the branch being updated

    Note:
        Shows which files were pruned and warns if template has same file with different ID
        (indicates registry ID instability issue)
    """
    if not pruned_list:
        return

    console.print(f"\n{'='*70}")
    console.print(f"[bold]PRUNED FILES ({len(pruned_list)})[/bold]")
    console.print(f"{'='*70}")

    has_id_mismatches = False

    for i, (filename, file_id) in enumerate(pruned_list, 1):
        console.print(f"\n{i}. {filename} [dim](ID: {file_id})[/dim]")

        # Check if template has same filename with different ID
        # Template registry has 'files' and 'directories' sections, NOT 'file_tracking'
        template_has_file = False
        template_file_id = None

        # Check files section
        for tid, entry in template_registry.get('files', {}).items():
            if entry.get('current_name') == filename or entry.get('path') == filename:
                template_has_file = True
                template_file_id = tid
                break

        # Check directories section if not found
        if not template_has_file:
            for tid, entry in template_registry.get('directories', {}).items():
                if entry.get('current_name') == filename or entry.get('path') == filename:
                    template_has_file = True
                    template_file_id = tid
                    break

        if template_has_file and template_file_id != file_id:
            console.print(f"   [red]❌ ERROR: ID MISMATCH - FILE DELETED BUT NOT REPLACED[/red]")
            console.print(f"   [red]Branch had: {file_id}[/red]")
            console.print(f"   [red]Template has: {template_file_id}[/red]")
            console.print(f"   [red]This file should have been UPDATED, not deleted[/red]")
            has_id_mismatches = True
        elif template_has_file and template_file_id == file_id:
            console.print(f"   [dim]Status: Removed from template (expected prune)[/dim]")
        else:
            console.print(f"   [dim]Status: Not in template (expected prune)[/dim]")

    console.print(f"{'='*70}")

    if has_id_mismatches:
        console.print(f"\n[bold red]⚠️  CRITICAL: ID mismatch errors detected![/bold red]")
        console.print(f"[red]Files were deleted but NOT re-added due to registry ID changes.[/red]")
        console.print(f"[red]This is a registry stability issue that needs to be fixed.[/red]")
        console.print(f"{'='*70}")


def display_registry_validation_errors(mismatches: list) -> None:
    """
    Display template registry validation errors

    Args:
        mismatches: List of mismatch dicts from validate_template_registry()

    Note:
        Prints directly to console. Shows numbered list matching create_branch style.
    """
    if not mismatches:
        return

    console.print(f"\n[yellow]⚠️  WARNING: Template registry out of sync ({len(mismatches)} issue(s))[/yellow]")
    console.print(f"[yellow]Registry paths don't match actual filesystem:[/yellow]\n")

    for i, mismatch in enumerate(mismatches, 1):
        file_id = mismatch["id"]
        file_type = mismatch["type"]
        registry_path = mismatch["registry_path"]
        actual_path = mismatch.get("actual_path")

        console.print(f"{i}. [dim][{file_id}][/dim] {file_type}: {registry_path}")
        if actual_path:
            console.print(f"   [red]❌ Registry says: {registry_path}[/red]")
            console.print(f"   [green]✅ Actually exists as: {actual_path}[/green]")
        else:
            console.print(f"   [red]❌ Not found in template at all[/red]")
        console.print()
