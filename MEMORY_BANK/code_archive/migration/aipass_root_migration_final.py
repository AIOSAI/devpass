#!/usr/bin/env python3
"""
AIPass Ecosystem: ai-mail to ai_mail Rename Script
Performs system-wide renaming of 'ai-mail' to 'ai_mail' with detailed reporting.

This script:
1. Updates all file contents containing ai-mail references (hyphen → underscore)
2. Handles paths, imports, strings, JSON configs
3. Provides comprehensive dry-run and change reporting
4. Validates changes before applying

Author: AIPass Admin
Version: 1.0
Date: 2025-10-25
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

class AiMailRenamer:
    def __init__(self, root_path: Optional[str] = None):
        self.root_path = Path(root_path) if root_path else Path("/home/aipass")
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
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            '.vscode', 'venv', 'env', '.env', '.local', '.cache',
            '.Trash', '.serena',
            # User data and system directories to skip
            'backups', 'backup', 'downloads', 'Downloads',
            'archive', 'Archive', 'archives', 'Archives',
            'temp', 'tmp', '.tmp',
            # Specific AIPass backup locations
            'processed_plans', 'memory_bank',
            # System config (removed .claude to scan hooks)
            '.config', 'admin_dev',
            # VS Code and editor history
            'History', 'history'
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
        """Update file content replacing ai-mail with ai_mail."""
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()

            # Pattern replacements - Legacy/hardcoded imports to Path.home()
            patterns = [
                # Pattern 1: Hardcoded AIPASS_ROOT = Path.home()
                (r'AIPASS_ROOT = Path\("/home/aipass"\)', 'AIPASS_ROOT = Path.home()'),
                (r"AIPASS_ROOT = Path\('/home/aipass'\)", 'AIPASS_ROOT = Path.home()'),

                # Pattern 2: ECOSYSTEM_ROOT parent.parent patterns
                (r'ECOSYSTEM_ROOT = Path\(__file__\)\.parent\.parent\.parent', 'ECOSYSTEM_ROOT = Path.home()'),
                (r'ECOSYSTEM_ROOT = Path\(__file__\)\.parent\.parent', 'ECOSYSTEM_ROOT = Path.home()'),

                # Pattern 3: AIPASS_ROOT parent.parent
                (r'AIPASS_ROOT = Path\(__file__\)\.parent\.parent', 'AIPASS_ROOT = Path.home()'),
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
                (r'/home/aipass/ai-mail/', '/home/aipass/ai_mail/'),
                (r'"ai-mail"', '"ai_mail"'),
                (r'AI-MAIL', 'AI_MAIL'),
                (r'/ai-mail/', '/ai_mail/'),
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

    def scan_and_update_files(self):
        """Scan all files and update those containing ai-mail references."""
        file_extensions = {
            '.py', '.md', '.json', '.txt', '.rst', '.yml', '.yaml',
            '.toml', '.cfg', '.ini', '.sh', '.bat', '.js', '.ts'
        }

        exclude_dirs = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            '.vscode', 'venv', 'env', '.env', '.local', '.cache',
            '.Trash', '.serena',
            # User data and system directories to skip
            'backups', 'backup', 'downloads', 'Downloads',
            'archive', 'Archive', 'archives', 'Archives',
            'temp', 'tmp', '.tmp',
            # Specific AIPass backup locations
            'processed_plans', 'memory_bank',
            # System config (removed .claude to scan hooks)
            '.config',
            # VS Code and editor history
            'History', 'history'
        }

        exclude_files = {
            'ai_mail_rename.py'  # Don't modify this script itself
        }

        print(f"🔍 Scanning {self.root_path} for ai-mail references...")

        for file_path in self.root_path.rglob('*'):
            # Skip directories and excluded paths
            if file_path.is_dir():
                continue
            if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                continue
            if file_path.name in exclude_files:
                continue
            if file_path.suffix not in file_extensions:
                continue

            # Check if file contains ai-mail patterns
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                if re.search(r'AIPASS_ROOT = Path\(["\']|ECOSYSTEM_ROOT = Path\(__file__\)|sys\.path\.append\(str\(Path\(__file__\)\.parent\.parent', content):
                    print(f"  📝 Found legacy import pattern in: {file_path.relative_to(self.root_path)}")
                    if file_path.suffix == '.json':
                        self.process_json_file(file_path)
                    else:
                        self.update_file_content(file_path)

            except Exception as e:
                self.log_error(f"Failed to read file: {e}", str(file_path))

    def generate_summary(self):
        """Generate summary statistics."""
        self.changes_report["summary"] = {
            "files_modified": len(self.changes_report["file_content_changes"]),
            "json_files_updated": len(self.changes_report["json_updates"]),
            "total_errors": len(self.changes_report["errors"]),
            "dry_run": self.dry_run
        }

    def save_report(self, report_path: Optional[str] = None):
        """Save the changes report to a JSON file."""
        if not report_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = str(self.root_path / f"ai_mail_rename_report_{timestamp}.json")

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.changes_report, f, indent=2)

        print(f"\n📄 Report saved to: {report_path}")

    def print_summary(self):
        """Print a summary of changes."""
        summary = self.changes_report["summary"]

        print("\n" + "="*70)
        print("AI-Mail Rename Script Report (ai-mail → ai_mail)")
        print("="*70)
        print(f"Mode: {'🔍 DRY RUN' if self.dry_run else '✅ LIVE EXECUTION'}")
        print(f"Root path: {self.root_path}")
        print(f"Timestamp: {self.changes_report['timestamp']}")
        print(f"Files modified: {summary['files_modified']}")
        print(f"JSON files updated: {summary['json_files_updated']}")
        print(f"Errors encountered: {summary['total_errors']}")

        if self.changes_report["errors"]:
            print("\n❌ ERRORS:")
            for error in self.changes_report["errors"]:
                print(f"  - {error['error']} ({error['file']})")

        print(f"\n📝 FILE CHANGES: {len(self.changes_report['file_content_changes'])} files")
        for change in self.changes_report["file_content_changes"][:10]:  # Show first 10
            rel_path = Path(change['file']).relative_to(self.root_path) if self.root_path in Path(change['file']).parents else Path(change['file'])
            total_changes = sum(c['count'] for c in change['changes'])
            print(f"  • {rel_path} ({total_changes} replacements)")

        if len(self.changes_report["file_content_changes"]) > 10:
            print(f"  ... and {len(self.changes_report['file_content_changes']) - 10} more files")

        print("\n" + "="*70)

    def execute(self, dry_run: bool = False):
        """Execute the rename operation."""
        self.dry_run = dry_run

        print(f"\n🚀 Starting ai-mail → ai_mail rename {'(DRY RUN)' if dry_run else '(LIVE)'}...")
        print(f"Root path: {self.root_path}\n")

        # Scan and update files
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
        description='Rename ai-mail to ai_mail throughout AIPass ecosystem',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  python3 ai_mail_rename.py --dry-run                    # Preview all changes
  python3 ai_mail_rename.py                              # Execute changes
  python3 ai_mail_rename.py --root /home/aipass/flow     # Specific directory
        """
    )

    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be changed without making changes')
    parser.add_argument('--root',
                       type=str,
                       default='/home/aipass',
                       help='Root directory path (default: /home/aipass)')

    args = parser.parse_args()

    renamer = AiMailRenamer(args.root)
    renamer.execute(dry_run=args.dry_run)

    if args.dry_run:
        print("\n💡 This was a DRY RUN. To execute changes, run without --dry-run flag.")
    else:
        print("\n✅ Rename operation completed! Check the report for details.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
