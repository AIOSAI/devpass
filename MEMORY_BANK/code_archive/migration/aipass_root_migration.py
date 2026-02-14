#!/usr/bin/env python3
"""
AIPass Ecosystem: AIPASS_ROOT Import Pattern Migration Script
Migrates from hardcoded/legacy import patterns to Path.home() pattern.

This script:
1. Updates all file contents containing legacy import patterns
2. Handles both parent.parent pattern AND hardcoded Path.home() pattern
3. Provides comprehensive dry-run and change reporting
4. Validates changes before applying

Patterns migrated:
- Legacy: sys.path.append(str(Path(__file__).parent.parent))
- Current: AIPASS_ROOT = Path("/home/aipass")
- Target: AIPASS_ROOT = Path.home()

Author: PRAX Branch
Version: 2.0 (adapted from ai_mail_rename.py v1.0)
Date: 2025-10-26
"""

import os
import shutil
import json
import re
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Any, Optional, Union

class AipassRootMigrator:
    def __init__(self, root_path: str | None = None):
        self.root_path = Path(root_path) if root_path else Path("/")  # Default to system root
        self.changes_report = {
            "timestamp": datetime.now().isoformat(),
            "root_path": str(self.root_path),
            "directory_renames": [],
            "file_renames": [],
            "file_content_changes": [],
            "json_updates": [],
            "errors": [],
            "summary": {}
        }
        self.dry_run = False
        self.exclude_dirs = {
            # Python/Development
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            '.vscode', 'venv', 'env', '.env', '.local', '.cache',
            '.Trash', '.serena',

            # Linux System Directories (NEVER MODIFY)
            'proc', 'sys', 'dev', 'boot', 'run', 'mnt', 'media',
            'var', 'opt', 'srv', 'root', 'lib', 'lib64', 'bin', 'sbin',
            'usr', 'lost+found', 'cdrom', 'snap', 'swap.img',

            # Note: /etc is NOT excluded - we need to check /etc/claude-code/
            # Only /etc/claude-code/ will be scanned (other /etc subdirs skipped by other rules)

            # User data and backups
            'backups', 'backup', 'downloads', 'Downloads',
            'archive', 'Archive', 'archives', 'Archives',
            'temp', 'tmp', '.tmp',

            # AIPass specific backups
            'processed_plans', 'memory_bank',

            # System config and history (don't modify)
            '.config', 'admin_dev',

            # Editor history
            'History', 'history', '.bash_history', '.python_history'
        }

    def log_change(self, category: str, item: Dict[str, Any]):
        """Log a change to the report."""
        self.changes_report[category].append(item)

    def log_error(self, error: str, file_path: str = ""):
        """Log an error to the report."""
        self.changes_report["errors"].append({
            "error": error,
            "file": file_path,
            "timestamp": datetime.now().isoformat()
        })

    def update_file_content(self, file_path: Path) -> bool:
        """Update file content replacing legacy import patterns with Path.home()."""
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()

            # Pattern replacements - Legacy/hardcoded imports to Path.home()
            patterns = [
                # PRIMARY PATTERNS - Import statements

                # Pattern 1: Hardcoded AIPASS_ROOT = Path.home()
                (r'AIPASS_ROOT = Path\("/home/aipass"\)', 'AIPASS_ROOT = Path.home()'),
                (r"AIPASS_ROOT = Path\('/home/aipass'\)", 'AIPASS_ROOT = Path.home()'),

                # Pattern 2: Legacy parent.parent pattern (with variations)
                (r'sys\.path\.append\(str\(Path\(__file__\)\.parent\.parent\)\)',
                 'AIPASS_ROOT = Path.home()\nimport sys\nsys.path.append(str(AIPASS_ROOT))'),

                # Pattern 3: Other hardcoded path variations
                (r'ECOSYSTEM_ROOT = Path\("/home/aipass"\)', 'ECOSYSTEM_ROOT = Path.home()'),
                (r"ECOSYSTEM_ROOT = Path\('/home/aipass'\)", 'ECOSYSTEM_ROOT = Path.home()'),

                # Pattern 4: In documentation/comments - show new pattern
                (r'AIPASS_ROOT = Path\("/home/aipass"\)  # Hardcoded',
                 'AIPASS_ROOT = Path.home()  # Dynamic - works across all profiles'),
                (r'AIPASS_ROOT = Path\("/home/aipass"\) # Hardcoded',
                 'AIPASS_ROOT = Path.home() # Dynamic - works across all profiles'),

                # Pattern 5: String references in docs/markdown
                (r'Path\("/home/aipass"\)', 'Path.home()'),
                (r"Path\('/home/aipass'\)", 'Path.home()'),

                # Pattern 6: Comments explaining the pattern
                (r'# Dynamic path using Path.home()', '# Dynamic path using Path.home()'),
                (r'# dynamic user-aware', '# dynamic user-aware'),

                # Pattern 7: Code examples in documentation
                (r'`AIPASS_ROOT = Path\("/home/aipass"\)`', '`AIPASS_ROOT = Path.home()`'),
                (r'```python\s*AIPASS_ROOT = Path\("/home/aipass"\)',
                 '```python\nAIPASS_ROOT = Path.home()'),

            ]

            modified_content = original_content
            changes_made = []

            for pattern, replacement in patterns:
                if re.search(pattern, modified_content):
                    count = len(re.findall(pattern, modified_content))
                    modified_content = re.sub(pattern, replacement, modified_content)
                    changes_made.append({
                        "pattern": pattern,
                        "replacement": replacement,
                        "count": count
                    })

            # Only write if changes were made
            if changes_made and original_content != modified_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)

                self.log_change("file_content_changes", {
                    "file": str(file_path),
                    "changes": changes_made,
                    "status": "completed" if not self.dry_run else "planned"
                })
                return True

            return False

        except Exception as e:
            self.log_error(f"Failed to update file content: {e}", str(file_path))
            return False

    def process_json_file(self, file_path: Path) -> bool:
        """Specifically handle JSON files with careful parsing."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Try to parse as JSON first
            try:
                data = json.loads(content)
                original_str = json.dumps(data, indent=2)
            except json.JSONDecodeError:
                # If not valid JSON, treat as text file
                return self.update_file_content(file_path)

            # Convert to string and apply replacements
            modified_str = original_str
            patterns = [
                # Import pattern references in JSON
                (r'Path\\("/home/aipass"\\)', 'Path.home()'),
                (r"Path\\('/home/aipass'\\)", 'Path.home()'),
                (r'"/home/aipass"', 'Path.home()'),  # In config values
            ]

            changes_made = []
            for pattern, replacement in patterns:
                if re.search(pattern, modified_str):
                    count = len(re.findall(pattern, modified_str))
                    modified_str = re.sub(pattern, replacement, modified_str)
                    changes_made.append({
                        "pattern": pattern,
                        "replacement": replacement,
                        "count": count
                    })

            if changes_made and original_str != modified_str:
                if not self.dry_run:
                    # Validate JSON is still valid
                    try:
                        json.loads(modified_str)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(modified_str)
                    except json.JSONDecodeError as e:
                        self.log_error(f"JSON validation failed after changes: {e}", str(file_path))
                        return False

                self.log_change("json_updates", {
                    "file": str(file_path),
                    "changes": changes_made,
                    "status": "completed" if not self.dry_run else "planned"
                })
                return True

            return False

        except Exception as e:
            self.log_error(f"Failed to process JSON file: {e}", str(file_path))
            return False

    def rename_directories(self):
        """Rename directories containing ai-mail to ai_mail."""
        print(f"\n📁 Scanning for directories with 'ai-mail' in name...")

        dirs_to_rename = []

        # Collect all directories that need renaming (depth-first, deepest first)
        try:
            all_paths = sorted(self.root_path.rglob('*'), key=lambda p: len(p.parts), reverse=True)
        except PermissionError as e:
            print(f"  ⚠️  Permission denied scanning some directories (skipped): {e}")
            all_paths = []

        for dir_path in all_paths:
            try:
                if not dir_path.is_dir():
                    continue

                # Skip if in excluded directories
                if any(exclude in dir_path.parts for exclude in self.exclude_dirs):
                    continue

                # Check if directory name contains ai-mail or ai_mail with hyphens
                if 'ai-mail' in dir_path.name or 'ai_mail-' in dir_path.name:
                    # First replace ai-mail with ai_mail, then replace any remaining hyphens in ai_mail patterns
                    new_name = dir_path.name.replace('ai-mail', 'ai_mail').replace('ai_mail-', 'ai_mail_')
                    new_path = dir_path.parent / new_name

                    dirs_to_rename.append({
                        'old': str(dir_path),
                        'new': str(new_path),
                        'old_name': dir_path.name,
                        'new_name': new_name,
                        'status': 'pending'
                    })

                    print(f"  🔄 Found: {dir_path.relative_to(self.root_path)} → {new_name}")

            except (PermissionError, OSError) as e:
                # Skip directories we can't access
                continue

        # Execute renames
        for rename_op in dirs_to_rename:
            old_path = Path(rename_op['old'])
            new_path = Path(rename_op['new'])

            if new_path.exists():
                error_msg = f"Target directory already exists: {new_path}"
                self.log_error(error_msg, str(old_path))
                rename_op['status'] = 'failed'
                rename_op['error'] = error_msg
                continue

            if not self.dry_run:
                try:
                    shutil.move(str(old_path), str(new_path))
                    rename_op['status'] = 'completed'
                except Exception as e:
                    error_msg = f"Failed to rename directory: {e}"
                    self.log_error(error_msg, str(old_path))
                    rename_op['status'] = 'failed'
                    rename_op['error'] = str(e)
            else:
                rename_op['status'] = 'planned'

            self.log_change("directory_renames", rename_op)

        return len(dirs_to_rename)

    def rename_files(self):
        """Rename files containing ai-mail to ai_mail."""
        print(f"\n📄 Scanning for files with 'ai-mail' in name...")

        files_to_rename = []

        # Use os.walk for better permission handling
        for root, dirs, files in os.walk(str(self.root_path), onerror=lambda e: None):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for filename in files:
                try:
                    file_path = Path(root) / filename

                    # Skip ALL rename scripts (protect rename tooling)
                    if filename.endswith('_rename.py'):
                        continue

                    # Check if filename contains ai-mail or ai_mail with hyphens (case-insensitive)
                    filename_lower = filename.lower()
                    if 'ai-mail' in filename_lower or 'ai_mail-' in filename_lower:
                        # Case-preserving replacements (handle both uppercase and lowercase)
                        new_name = filename.replace('ai-mail', 'ai_mail').replace('AI-MAIL', 'AI_MAIL')
                        new_name = new_name.replace('ai_mail-', 'ai_mail_').replace('AI_MAIL-', 'AI_MAIL_')
                        new_path = file_path.parent / new_name

                        files_to_rename.append({
                            'old': str(file_path),
                            'new': str(new_path),
                            'old_name': filename,
                            'new_name': new_name,
                            'status': 'pending'
                        })

                        try:
                            rel_path = file_path.relative_to(self.root_path)
                        except ValueError:
                            rel_path = file_path
                        print(f"  🔄 Found: {rel_path} → {new_name}")

                except (PermissionError, OSError):
                    # Skip files we can't access
                    continue

        # Execute renames
        for rename_op in files_to_rename:
            old_path = Path(rename_op['old'])
            new_path = Path(rename_op['new'])

            if new_path.exists():
                error_msg = f"Target file already exists: {new_path}"
                self.log_error(error_msg, str(old_path))
                rename_op['status'] = 'failed'
                rename_op['error'] = error_msg
                continue

            if not self.dry_run:
                try:
                    shutil.move(str(old_path), str(new_path))
                    rename_op['status'] = 'completed'
                except Exception as e:
                    error_msg = f"Failed to rename file: {e}"
                    self.log_error(error_msg, str(old_path))
                    rename_op['status'] = 'failed'
                    rename_op['error'] = str(e)
            else:
                rename_op['status'] = 'planned'

            self.log_change("file_renames", rename_op)

        return len(files_to_rename)

    def scan_and_update_files(self):
        """Scan all files and update those containing ai-mail references."""
        file_extensions = {
            '.py', '.md', '.json', '.txt', '.rst', '.yml', '.yaml',
            '.toml', '.cfg', '.ini', '.sh', '.bat', '.js', '.ts'
        }

        print(f"🔍 Scanning {self.root_path} for legacy import patterns...")

        # Use os.walk for better permission handling
        for root, dirs, files in os.walk(str(self.root_path), onerror=lambda e: None):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for filename in files:
                try:
                    file_path = Path(root) / filename

                    # Skip rename scripts and rename reports (protect rename tooling)
                    if filename.endswith('_rename.py'):
                        continue
                    if filename.endswith('_rename_report_') or 'rename_report' in filename:
                        continue
                    if file_path.suffix not in file_extensions:
                        continue

                    # Check if file contains ai-mail patterns
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        # Search for import patterns (legacy parent.parent OR hardcoded AIPASS_ROOT)
                        if re.search(r'Path\(__file__\)\.parent\.parent|AIPASS_ROOT = Path\("/home/aipass"\)|ECOSYSTEM_ROOT = Path\("/home/aipass"\)', content):
                            try:
                                rel_path = file_path.relative_to(self.root_path)
                            except ValueError:
                                rel_path = file_path
                            print(f"  📝 Found legacy import pattern in: {rel_path}")

                            if file_path.suffix == '.json':
                                self.process_json_file(file_path)
                            else:
                                self.update_file_content(file_path)

                    except Exception as e:
                        self.log_error(f"Failed to read file: {e}", str(file_path))

                except (PermissionError, OSError):
                    # Skip files we can't access
                    continue

    def generate_summary(self):
        """Generate summary statistics."""
        self.changes_report["summary"] = {
            "directories_renamed": len(self.changes_report["directory_renames"]),
            "files_renamed": len(self.changes_report["file_renames"]),
            "files_modified": len(self.changes_report["file_content_changes"]),
            "json_files_updated": len(self.changes_report["json_updates"]),
            "total_errors": len(self.changes_report["errors"]),
            "dry_run": self.dry_run
        }

    def save_report(self, report_path: str | None = None):
        """Save the changes report to a JSON file."""
        if not report_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = str(self.root_path / f"aipass_root_migration_report_{timestamp}.json")

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.changes_report, f, indent=2)

        print(f"\n📄 Report saved to: {report_path}")

    def print_summary(self):
        """Print a summary of changes."""
        summary = self.changes_report["summary"]

        print("\n" + "="*70)
        print("AIPASS_ROOT Import Pattern Migration Report")
        print("="*70)
        print(f"Mode: {'🔍 DRY RUN' if self.dry_run else '✅ LIVE EXECUTION'}")
        print(f"Root path: {self.root_path}")
        print(f"Timestamp: {self.changes_report['timestamp']}")
        print(f"Directories renamed: {summary['directories_renamed']}")
        print(f"Files renamed: {summary['files_renamed']}")
        print(f"File contents modified: {summary['files_modified']}")
        print(f"JSON files updated: {summary['json_files_updated']}")
        print(f"Errors encountered: {summary['total_errors']}")

        if self.changes_report["errors"]:
            print("\n❌ ERRORS:")
            for error in self.changes_report["errors"]:
                print(f"  - {error['error']} ({error['file']})")

        if self.changes_report["directory_renames"]:
            print(f"\n📁 DIRECTORY RENAMES: {len(self.changes_report['directory_renames'])}")
            for rename in self.changes_report["directory_renames"]:
                old_rel = Path(rename['old']).relative_to(self.root_path)
                print(f"  • {old_rel} → {rename['new_name']} ({rename['status']})")

        if self.changes_report["file_renames"]:
            print(f"\n📄 FILE RENAMES: {len(self.changes_report['file_renames'])}")
            for rename in self.changes_report["file_renames"]:  # Show ALL files (no limit)
                old_rel = Path(rename['old']).relative_to(self.root_path)
                print(f"  • {old_rel} → {rename['new_name']} ({rename['status']})")

        if self.changes_report["file_content_changes"]:
            print(f"\n📝 FILE CONTENT CHANGES: {len(self.changes_report['file_content_changes'])} files")
            for change in self.changes_report["file_content_changes"]:  # Show ALL files (no limit)
                rel_path = Path(change['file']).relative_to(self.root_path) if self.root_path in Path(change['file']).parents else Path(change['file'])
                total_changes = sum(c['count'] for c in change['changes'])
                print(f"  • {rel_path} ({total_changes} replacements)")

        print("\n" + "="*70)

    def execute(self, dry_run: bool = False):
        """Execute the rename operation."""
        self.dry_run = dry_run

        print(f"\n🚀 Starting AIPASS_ROOT import pattern migration {'(DRY RUN)' if dry_run else '(LIVE)'}...")
        print(f"Root path: {self.root_path}\n")
        print("Migrating from:")
        print("  - Legacy: sys.path.append(str(Path(__file__).parent.parent))")
        print('  - Current: AIPASS_ROOT = Path("/home/aipass")')
        print("To:")
        print("  - Target: AIPASS_ROOT = Path.home()")
        print()

        # Step 1: Rename directories (deepest first to avoid path issues)
        self.rename_directories()

        # Step 2: Rename files
        self.rename_files()

        # Step 3: Update file contents
        print(f"\n📝 Scanning file contents for import patterns...")
        self.scan_and_update_files()

        # Generate summary
        self.generate_summary()

        # Print and save report
        self.print_summary()
        self.save_report()

        return self.changes_report


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Migrate AIPASS_ROOT import patterns to Path.home() throughout AIPass ecosystem',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: migrate, --dry-run, --root

USAGE:
  migrate  - Execute the migration operation (default if no command specified)

OPTIONS:
  --dry-run  - Show what would be changed without making changes (RECOMMENDED FIRST)
  --root     - Root directory path (default: / - system root)

PATTERNS MIGRATED:
  Legacy:   sys.path.append(str(Path(__file__).parent.parent))
  Current:  AIPASS_ROOT = Path("/home/aipass")
  Target:   AIPASS_ROOT = Path.home()

SAFETY:
  System directories automatically excluded (proc, sys, dev, boot, usr, etc)
  Backup dirs excluded (backups/, backup/, processed_plans/, memory_bank/)
  Safe for root-level execution - only touches AIPass code files
  Always run --dry-run first to preview changes

EXAMPLES:
  python3 aipass_root_migration.py --dry-run --root /home/aipass    # Preview changes (DO THIS FIRST)
  python3 aipass_root_migration.py --root /home/aipass               # Execute migration
  python3 aipass_root_migration.py --dry-run --root /home/aipass/backup_system  # Specific directory
        """
    )

    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be changed without making changes')
    parser.add_argument('--root',
                       type=str,
                       default='/',
                       help='Root directory path (default: / - system root, safe with exclusions)')

    args = parser.parse_args()

    migrator = AipassRootMigrator(args.root)
    migrator.execute(dry_run=args.dry_run)

    if args.dry_run:
        print("\n💡 This was a DRY RUN. To execute changes, run without --dry-run flag.")
    else:
        print("\n✅ Migration operation completed! Check the report for details.")

    return 0


if __name__ == "__main__":
    sys.exit(main())