#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: backup_cli.py
# Date: 2025-10-14
# Version: 1.0.0
# Category: backup_system
#
# CHANGELOG:
#   - v1.0.0 (2025-10-14): Initial extraction from backup.py
#     * Extracted CLI interface (lines 1795-1949)
#     * Command-line argument parsing
#     * Mode selection and execution
#     * Help text and usage examples
#     * Entry point (__main__ handler)
# =============================================

"""
Backup System Command Line Interface

Provides the command-line interface for the backup system.
Handles argument parsing, mode selection, user interaction, and execution.

Usage:
    python backup_cli.py snapshot
    python backup_cli.py versioned --note "Before changes"
    python backup_cli.py all --note "Full backup"
    python backup_cli.py --list-modes
    python backup_cli.py --list-versions
    python backup_cli.py --diff "file.py"
"""

# =============================================
# IMPORTS
# =============================================

import sys
import argparse
import datetime
from pathlib import Path

# Infrastructure import pattern
AIPASS_ROOT = Path.home() / "aipass_core"
BACKUP_SYSTEM_ROOT = AIPASS_ROOT / "backup_system"
sys.path.append(str(AIPASS_ROOT))
from prax.apps.prax_logger import system_logger as logger

# Module dependencies
from backup_config import BACKUP_MODES
from backup_engine import BackupEngine
from backup_diff import list_versioned_files, show_file_diff
from backup_json_handler import initialize_json_files

# =============================================
# CLI HELPER FUNCTIONS
# =============================================

def list_backup_modes():
    """Display available backup modes with descriptions."""
    print(f"\n{'='*70}")
    print("AVAILABLE BACKUP MODES")
    print('='*70)

    for mode, config in BACKUP_MODES.items():
        behavior = "DYNAMIC (overwrites)" if config['behavior'] == 'dynamic' else "VERSIONED (keeps all)"
        print(f"{mode:10s} - {config['name']}")
        print(f"           {config['description']}")
        print(f"           Behavior: {behavior}")
        print(f"           Usage: {config['usage']}")
        print()

# =============================================
# MAIN CLI FUNCTION
# =============================================

def main():
    """Main function with command line interface.

    Handles all CLI interactions including:
    - Argument parsing
    - Mode selection
    - Diff operations
    - Backup execution
    - Error handling

    Returns:
        0 on success, 1 on failure
    """
    # Initialize AIPass 3-JSON system
    if not initialize_json_files():
        logger.error("[backup_cli] Failed to initialize 3-JSON system")
        return 1

    logger.info("[backup_cli] Module started via command line interface")

    parser = argparse.ArgumentParser(
        description='AIPass Unified Backup System - Modular Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: snapshot, versioned, all, test, --note, --list-modes, --list-versions, --diff, --v1, --v2

BACKUP MODES:
  snapshot  - Dynamic instant backup (overwrites previous)
  versioned - Cumulative file history (keeps all versions forever)
  all       - Run all backup modes sequentially
  test      - Test mode for validation

DIFF COMMANDS:
  python backup_cli.py --list-versions                   # List all versioned files
  python backup_cli.py --diff <file_path>                # Show diff for file (latest vs current)
  python backup_cli.py --diff <file_path> --v1 <ver1> --v2 <ver2>  # Compare specific versions

EXAMPLES:
  python backup_cli.py snapshot                           # Quick snapshot
  python backup_cli.py versioned --note "Before changes" # Versioned with note
  python backup_cli.py all --note "Full backup"          # All modes
  python backup_cli.py --list-modes                      # Show all modes
  python backup_cli.py --list-versions                   # Show versioned files
  python backup_cli.py --diff "backup.py"                # Show latest changes
        """
    )

    parser.add_argument('mode', nargs='?', choices=list(BACKUP_MODES.keys()) + ['all', 'test'],
                       help='Backup mode to use (required unless using --list-* or --diff)')
    parser.add_argument('--note', type=str, help='Note for backup operation')
    parser.add_argument('--list-modes', action='store_true', help='List available backup modes')
    parser.add_argument('--dry-run', action='store_true', help='Dry-run: show what would be backed up without copying files')

    # Diff functionality arguments
    parser.add_argument('--list-versions', action='store_true', help='List all versioned files')
    parser.add_argument('--diff', type=str, help='Show diff for specified file')
    parser.add_argument('--v1', type=str, help='First version for comparison (use with --diff)')
    parser.add_argument('--v2', type=str, help='Second version for comparison (use with --diff)')

    args = parser.parse_args()

    try:
        # Handle diff-related commands first
        if args.list_versions:
            # Get versioned backup path from config
            versioned_config = BACKUP_MODES['versioned']
            backup_path = Path(versioned_config['destination']) / versioned_config['folder_name']
            success = list_versioned_files(backup_path)
            return 0 if success else 1

        if args.diff:
            # Get paths from config for diff operation
            versioned_config = BACKUP_MODES['versioned']
            backup_path = Path(versioned_config['destination']) / versioned_config['folder_name']
            source_dir = Path(__file__).parent.parent.parent  # /home/aipass/ (entire Workshop)
            success = show_file_diff(backup_path, source_dir, args.diff, args.v1, args.v2)
            return 0 if success else 1

        if args.list_modes:
            list_backup_modes()
            return 0

        if not args.mode:
            # No mode specified - show help
            parser.print_help()
            return 1

        if args.mode == 'all':
            # Run all backup modes
            print("Running ALL backup modes...")
            success_count = 0

            for mode in ['snapshot', 'versioned']:
                print(f"\n{'='*70}")
                print(f"RUNNING {mode.upper()} MODE")
                print('='*70)

                try:
                    backup_engine = BackupEngine(mode)

                    # Get backup note
                    if args.note:
                        backup_note = f"{args.note} (all modes run)"
                    else:
                        backup_note = f"All modes backup - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

                    backup_engine.save_changelog_entry(backup_note)
                    result = backup_engine.run_backup(backup_note)

                    if result.errors == 0:
                        success_count += 1
                        print(f"✅ {mode.upper()} mode completed successfully")
                    else:
                        print(f"⚠️ {mode.upper()} mode completed with {result.errors} errors")

                except Exception as e:
                    print(f"❌ {mode.upper()} mode failed: {e}")
                    logger.error(f"[backup_cli] {mode} mode failed: {e}")

            print(f"\n{'='*70}")
            print(f"ALL MODES SUMMARY: {success_count}/2 completed successfully")
            print('='*70)
            return 0 if success_count == 2 else 1

        # Single mode operation
        backup_engine = BackupEngine(args.mode, dry_run=args.dry_run)

        # DRY-RUN notification
        if args.dry_run:
            print("\n" + "="*70)
            print("🔍 DRY-RUN MODE - Files will be scanned but NOT copied")
            print("="*70 + "\n")

        # Regular backup operation
        backup_engine.display_previous_comments()

        # Get backup note
        if args.note:
            backup_note = args.note
        else:
            print('='*60)
            print(f"{backup_engine.mode_config['name']} - Add Note")
            print('='*60)
            backup_note = input("Enter a note for this backup (or press Enter to skip): ").strip()
            if not backup_note:
                backup_note = "No note provided"

        # Add DRY-RUN to note if applicable
        if args.dry_run:
            backup_note = f"[DRY-RUN] {backup_note}"

        # Save changelog entry and run backup
        if not args.dry_run:
            backup_engine.save_changelog_entry(backup_note)
        result = backup_engine.run_backup(backup_note)

        if result.errors == 0:
            print(f"\n{backup_engine.mode_config['name']} completed successfully!")
            logger.info(f"[backup_cli] {args.mode} mode completed successfully")
            return 0
        else:
            print(f"\n{backup_engine.mode_config['name']} completed with errors!")
            logger.warning(f"[backup_cli] {args.mode} mode completed with {result.errors} errors")
            return 1

    except KeyboardInterrupt:
        print("\nBackup interrupted by user.")
        logger.info("[backup_cli] Backup interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        logger.error(f"[backup_cli] Unexpected error: {e}")
        return 1

# =============================================
# ENTRY POINT
# =============================================

if __name__ == "__main__":
    sys.exit(main())