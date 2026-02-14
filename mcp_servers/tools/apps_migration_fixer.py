#!/usr/bin/env python3
"""
AIPass Apps Migration Import Fixer
Automatically fixes imports after apps/ structure upgrade

Based on real-world patterns from backup_system, flow, and API branch upgrades.

This script handles:
✅ Pattern 1: parent.parent sys.path → AIPASS_ROOT
✅ Pattern 2: ECOSYSTEM_ROOT calculations → AIPASS_ROOT
✅ Pattern 3: Path calculations (DRONE_DIR, etc.) → BRANCH_ROOT
✅ Pattern 4: Runtime Path(__file__).parent → BRANCH_ROOT
✅ Pattern 5: Cross-module imports (absolute → relative within apps/)
✅ Pattern 6: Delete get_project_root() functions
✅ Pattern 7: Prax imports (prax.module → prax.apps.module)
✅ Pattern 8: Intra-branch imports (api.module → api.apps.module)
⚠️ Pattern 9-10: JavaScript files, import consolidation (flagged for manual)

Usage:
  python3 apps_migration_fixer.py <branch_path> --dry-run  # Preview changes
  python3 apps_migration_fixer.py <branch_path>            # Apply changes

Author: AIPass Admin
Version: 2.2 (Added intra-branch import pattern from API findings)
Date: 2025-10-22
"""

import re
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Any

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# CLI services
from cli.apps.modules import console

class AppsMigrationFixer:
    def __init__(self, branch_path: str):
        self.branch_path = Path(branch_path)
        self.branch_name = self.branch_path.name  # e.g., "drone", "flow", "backup_system"
        self.branch_name_upper = self.branch_name.upper().replace("-", "_")  # e.g., "DRONE", "BACKUP_SYSTEM"

        self.changes_report = {
            "timestamp": datetime.now().isoformat(),
            "branch": str(self.branch_path),
            "branch_name": self.branch_name,
            "pattern_1_sys_path": [],
            "pattern_2_ecosystem_root": [],
            "pattern_3_path_calcs": [],
            "pattern_4_runtime_paths": [],
            "pattern_5_cross_imports": [],
            "pattern_6_func_deletion": [],
            "prax_imports": [],
            "intra_branch_imports": [],
            "manual_review": [],
            "errors": [],
            "summary": {}
        }
        self.dry_run = False

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

    def fix_pattern_1_sys_path(self, file_path: Path, content: str) -> Tuple[str, bool]:
        """Pattern 1: Replace parent.parent sys.path with AIPASS_ROOT."""
        modified = False

        # Pattern 1a: AIPASS_ROOT = Path.home()
        pattern_a = r'sys\.path\.append\(str\(Path\(__file__\)\.parent\.parent\)\)'

        if re.search(pattern_a, content):
            # Check if AIPASS_ROOT already defined
            if 'AIPASS_ROOT = Path.home()' not in content:
                # Add imports at top if not present
                if 'from pathlib import Path' not in content:
                    content = 'from pathlib import Path\n' + content
                if 'import sys' not in content:
                    content = 'import sys\n' + content

                # Replace pattern
                replacement = 'AIPASS_ROOT = Path.home()\nsys.path.append(str(AIPASS_ROOT))'
                content = re.sub(pattern_a, replacement, content)
                modified = True

                self.log_change("pattern_1_sys_path", {
                    "file": str(file_path),
                    "pattern": "sys.path parent.parent → AIPASS_ROOT (Path variant)"
                })

        # Pattern 1b: sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        pattern_b = r'sys\.path\.append\(os\.path\.join\(os\.path\.dirname\(__file__\),\s*[\'"]\.\.[\'"]\)\)'

        if re.search(pattern_b, content):
            # Check if AIPASS_ROOT already defined
            if 'AIPASS_ROOT = Path.home()' not in content:
                # Add imports at top if not present
                if 'from pathlib import Path' not in content:
                    content = 'from pathlib import Path\n' + content
                if 'import sys' not in content:
                    content = 'import sys\n' + content

                # Replace pattern
                replacement = 'AIPASS_ROOT = Path.home()\nsys.path.append(str(AIPASS_ROOT))'
                content = re.sub(pattern_b, replacement, content)
                modified = True

                self.log_change("pattern_1_sys_path", {
                    "file": str(file_path),
                    "pattern": "sys.path parent.parent → AIPASS_ROOT (os.path variant)"
                })

        return content, modified

    def find_module_level_insertion_point(self, lines: list) -> int:
        """Find safe module-level insertion point (indentation = 0).

        Returns line index after last module-level import, or after docstring if no imports.
        Avoids inserting inside try/except/def/class blocks.
        """
        last_module_import_idx = -1
        in_docstring = False
        docstring_end_idx = -1

        for i, line in enumerate(lines):
            # Track docstrings
            if '"""' in line or "'''" in line:
                if not in_docstring:
                    in_docstring = True
                else:
                    in_docstring = False
                    docstring_end_idx = i
                continue

            if in_docstring:
                continue

            # Check indentation level
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()

            # Only consider module-level imports (indent = 0)
            if indent == 0 and (stripped.startswith('import ') or stripped.startswith('from ')):
                last_module_import_idx = i

        # Return insertion point
        if last_module_import_idx >= 0:
            return last_module_import_idx
        elif docstring_end_idx >= 0:
            return docstring_end_idx
        else:
            # Find first non-comment line at module level
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#'):
                    return max(0, i - 1)

        return 0

    def fix_pattern_2_ecosystem_root(self, file_path: Path, content: str) -> Tuple[str, bool]:
        """Pattern 2: Replace ECOSYSTEM_ROOT calculations with AIPASS_ROOT."""
        modified = False

        # Add AIPASS_ROOT if any ECOSYSTEM_ROOT found
        if 'ECOSYSTEM_ROOT' in content and 'AIPASS_ROOT = Path.home()' not in content:
            try:
                lines = content.split('\n')

                # Find safe module-level insertion point
                insert_idx = self.find_module_level_insertion_point(lines)

                if insert_idx == -1:
                    self.log_error(
                        f"Could not find safe insertion point for AIPASS_ROOT. File may need manual review.",
                        str(file_path)
                    )
                else:
                    # Insert after the found line at module level
                    lines.insert(insert_idx + 1, '')
                    lines.insert(insert_idx + 2, '# ===== PATHS =====')
                    lines.insert(insert_idx + 3, 'AIPASS_ROOT = Path.home()')
                    content = '\n'.join(lines)

            except Exception as e:
                self.log_error(
                    f"Error inserting AIPASS_ROOT constant: {str(e)}. Manual insertion may be needed.",
                    str(file_path)
                )

        # Pattern 2a: ECOSYSTEM_ROOT = Path.home()
        pattern_a = r'ECOSYSTEM_ROOT\s*=\s*Path\(__file__\)\.parent\.parent'
        if re.search(pattern_a, content):
            content = re.sub(pattern_a, 'ECOSYSTEM_ROOT = AIPASS_ROOT', content)
            modified = True
            self.log_change("pattern_2_ecosystem_root", {
                "file": str(file_path),
                "pattern": "ECOSYSTEM_ROOT = parent.parent → AIPASS_ROOT"
            })

        # Pattern 2b: ECOSYSTEM_ROOT = get_project_root()
        pattern_b = r'ECOSYSTEM_ROOT\s*=\s*get_project_root\(\)'
        if re.search(pattern_b, content):
            content = re.sub(pattern_b, 'ECOSYSTEM_ROOT = AIPASS_ROOT', content)
            modified = True
            self.log_change("pattern_2_ecosystem_root", {
                "file": str(file_path),
                "pattern": "ECOSYSTEM_ROOT = get_project_root() → AIPASS_ROOT"
            })

        return content, modified

    def fix_pattern_3_path_calculations(self, file_path: Path, content: str) -> Tuple[str, bool]:
        """Pattern 3: Replace Path(__file__).parent with BRANCH_ROOT."""
        modified = False

        # Add BRANCH_ROOT constant if needed
        branch_root_name = f"{self.branch_name_upper}_ROOT"
        branch_root_def = f'{branch_root_name} = AIPASS_ROOT / "{self.branch_name}"'

        # Check if we need BRANCH_ROOT
        needs_branch_root = False
        if f'Path(__file__).parent' in content and branch_root_def not in content:
            needs_branch_root = True

        if needs_branch_root and 'AIPASS_ROOT' in content:
            # Insert BRANCH_ROOT after AIPASS_ROOT or ECOSYSTEM_ROOT
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'AIPASS_ROOT' in line or 'ECOSYSTEM_ROOT' in line:
                    lines.insert(i + 1, branch_root_def)
                    content = '\n'.join(lines)
                    break

        # Pattern 3a: BRANCH_DIR = Path(__file__).parent
        pattern_dir = rf'{self.branch_name_upper}_DIR\s*=\s*Path\(__file__\)\.parent'
        if re.search(pattern_dir, content):
            content = re.sub(pattern_dir, f'{self.branch_name_upper}_DIR = {branch_root_name}', content)
            modified = True
            self.log_change("pattern_3_path_calcs", {
                "file": str(file_path),
                "pattern": f"{self.branch_name_upper}_DIR = parent → {branch_root_name}"
            })

        # Pattern 3b: BRANCH_JSON_DIR = Path(__file__).parent / "branch_json"
        pattern_json = rf'{self.branch_name_upper}_JSON_DIR\s*=\s*Path\(__file__\)\.parent\s*/\s*"{self.branch_name}_json"'
        if re.search(pattern_json, content):
            content = re.sub(pattern_json, f'{self.branch_name_upper}_JSON_DIR = {branch_root_name} / "{self.branch_name}_json"', content)
            modified = True
            self.log_change("pattern_3_path_calcs", {
                "file": str(file_path),
                "pattern": f"{self.branch_name_upper}_JSON_DIR calculation fixed"
            })

        return content, modified

    def fix_pattern_4_runtime_paths(self, file_path: Path, content: str) -> Tuple[str, bool]:
        """Pattern 4: Replace runtime Path(__file__).parent references."""
        modified = False
        branch_root_name = f"{self.branch_name_upper}_ROOT"

        # Pattern 4a: Path(__file__).parent / "commands"
        pattern_commands = r'Path\(__file__\)\.parent\s*/\s*"commands"'
        count_commands = len(re.findall(pattern_commands, content))
        if count_commands > 0:
            content = re.sub(pattern_commands, f'{branch_root_name} / "commands"', content)
            modified = True
            self.log_change("pattern_4_runtime_paths", {
                "file": str(file_path),
                "pattern": f'Path(__file__).parent / "commands" → {branch_root_name} (x{count_commands})'
            })

        # Pattern 4b: Path(__file__).parent / "branch_json"
        pattern_json = rf'Path\(__file__\)\.parent\s*/\s*"{self.branch_name}_json"'
        count_json = len(re.findall(pattern_json, content))
        if count_json > 0:
            content = re.sub(pattern_json, f'{branch_root_name} / "{self.branch_name}_json"', content)
            modified = True
            self.log_change("pattern_4_runtime_paths", {
                "file": str(file_path),
                "pattern": f'Path(__file__).parent / "{self.branch_name}_json" → {branch_root_name} (x{count_json})'
            })

        return content, modified

    def fix_pattern_5_cross_imports(self, file_path: Path, content: str) -> Tuple[str, bool]:
        """Pattern 5: Convert absolute imports to relative within apps/."""
        modified = False

        # Pattern: from branch.apps.module_name import → from module_name import
        # Only if file is in apps/ directory
        if '/apps/' in str(file_path):
            pattern = rf'from {self.branch_name}\.apps\.([a-zA-Z_]+) import'
            matches = re.findall(pattern, content)

            if matches:
                content = re.sub(pattern, r'from \1 import', content)
                modified = True
                self.log_change("pattern_5_cross_imports", {
                    "file": str(file_path),
                    "pattern": f"Absolute → relative imports within apps/ (x{len(matches)})",
                    "modules": matches
                })

        return content, modified

    def fix_pattern_6_delete_functions(self, file_path: Path, content: str) -> Tuple[str, bool]:
        """Pattern 6: Delete get_project_root() function."""
        modified = False

        # Pattern: Delete entire get_project_root() function
        # Look for function definition and its body
        pattern = r'def get_project_root\(\):[^\n]*\n(?:    [^\n]*\n)+'

        if re.search(pattern, content):
            content = re.sub(pattern, '', content)
            modified = True
            self.log_change("pattern_6_func_deletion", {
                "file": str(file_path),
                "pattern": "Deleted get_project_root() function"
            })

        return content, modified

    def fix_pattern_7_prax_imports(self, file_path: Path, content: str) -> Tuple[str, bool]:
        """Pattern 7: Update Prax imports to apps/ structure."""
        modified = False

        # Pattern 7a: from prax.prax_logger import → from prax.apps.prax_logger import
        pattern_logger = r'from prax\.prax_logger import'
        if re.search(pattern_logger, content):
            content = re.sub(pattern_logger, 'from prax.apps.prax_logger import', content)
            modified = True
            self.log_change("prax_imports", {
                "file": str(file_path),
                "pattern": "prax.prax_logger → prax.apps.prax_logger"
            })

        # Pattern 7b: from prax.openrouter import → from prax.apps.openrouter import
        pattern_openrouter = r'from prax\.openrouter import'
        if re.search(pattern_openrouter, content):
            content = re.sub(pattern_openrouter, 'from prax.apps.openrouter import', content)
            modified = True
            self.log_change("prax_imports", {
                "file": str(file_path),
                "pattern": "prax.openrouter → prax.apps.openrouter"
            })

        # Pattern 7c: Generic prax module imports - from prax.<module> import
        # Matches any prax module that isn't already using apps
        pattern_generic = r'from prax\.(?!apps\.)([a-zA-Z_]+) import'
        matches = re.findall(pattern_generic, content)
        if matches:
            content = re.sub(pattern_generic, r'from prax.apps.\1 import', content)
            modified = True
            for module in set(matches):
                self.log_change("prax_imports", {
                    "file": str(file_path),
                    "pattern": f"prax.{module} → prax.apps.{module}"
                })

        return content, modified

    def fix_pattern_8_intra_branch_imports(self, file_path: Path, content: str) -> Tuple[str, bool]:
        """Pattern 8: Update intra-branch imports to apps/ structure."""
        modified = False

        # Pattern 8: from {branch_name}.{module} import → from {branch_name}.apps.{module} import
        # Only apply if NOT already using apps (negative lookahead)
        pattern = rf'from {self.branch_name}\.(?!apps\.)([a-zA-Z_]+) import'
        matches = re.findall(pattern, content)

        if matches:
            # Replace with apps path
            replacement = rf'from {self.branch_name}.apps.\1 import'
            content = re.sub(pattern, replacement, content)
            modified = True

            for module in set(matches):
                self.log_change("intra_branch_imports", {
                    "file": str(file_path),
                    "pattern": f"{self.branch_name}.{module} → {self.branch_name}.apps.{module}"
                })

        return content, modified

    def find_hardcoded_paths(self, file_path: Path):
        """Find hard-coded file paths that may need manual review."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Look for hard-coded paths (common patterns)
            patterns = [
                r'/home/aipass/[a-zA-Z_]+/[a-zA-Z_]+\.py',  # Direct file paths
                r'"[^"]+\.py"',  # Quoted .py paths
                r"'[^']+\.py'",  # Single-quoted .py paths
            ]

            found_paths = []
            for i, line in enumerate(content.split('\n'), 1):
                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    if matches:
                        # Exclude comments
                        if not line.strip().startswith('#'):
                            found_paths.append({
                                "line": i,
                                "content": line.strip(),
                                "matches": matches
                            })

            if found_paths:
                self.log_change("hardcoded_paths", {
                    "file": str(file_path),
                    "paths": found_paths
                })

        except Exception as e:
            self.log_error(f"Failed to scan for hard-coded paths: {e}", str(file_path))

    def process_python_file(self, py_file: Path):
        """Process a single Python file through all pattern fixes."""
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            any_modified = False

            # Apply all pattern fixes in sequence
            content, mod = self.fix_pattern_1_sys_path(py_file, content)
            any_modified = any_modified or mod

            content, mod = self.fix_pattern_2_ecosystem_root(py_file, content)
            any_modified = any_modified or mod

            content, mod = self.fix_pattern_3_path_calculations(py_file, content)
            any_modified = any_modified or mod

            content, mod = self.fix_pattern_4_runtime_paths(py_file, content)
            any_modified = any_modified or mod

            content, mod = self.fix_pattern_5_cross_imports(py_file, content)
            any_modified = any_modified or mod

            content, mod = self.fix_pattern_6_delete_functions(py_file, content)
            any_modified = any_modified or mod

            # Pattern 7: Fix Prax imports (new pattern)
            content, mod = self.fix_pattern_7_prax_imports(py_file, content)
            any_modified = any_modified or mod

            # Pattern 8: Fix intra-branch imports (new pattern)
            content, mod = self.fix_pattern_8_intra_branch_imports(py_file, content)
            any_modified = any_modified or mod

            # Write changes if any modifications made
            if any_modified and content != original_content:
                if not self.dry_run:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)

        except Exception as e:
            self.log_error(f"Failed to process file: {e}", str(py_file))

    def detect_manual_review_items(self, branch_path: Path):
        """Detect items that need manual review with severity classification."""
        # Check for JavaScript files (HIGH priority - requires action)
        js_files = list(branch_path.glob("*.js"))
        if js_files:
            self.log_change("manual_review", {
                "severity": "HIGH",
                "priority": "ISSUE",
                "type": "JavaScript files found",
                "files": [str(f) for f in js_files],
                "action": "Update paths in .js files manually (e.g., 'apps/drone.py')",
                "reason": "JavaScript cannot be auto-fixed, requires manual update"
            })

        # Check for scattered inline imports (INFO level - optional optimization)
        apps_dir = branch_path / "apps"
        if apps_dir.exists():
            for py_file in apps_dir.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    # Find inline imports with line numbers
                    inline_imports = []
                    for i, line in enumerate(lines, 1):
                        # Check for indented imports (4+ spaces)
                        if re.match(r'^\s{4,}(from .+ import|import .+)', line.strip()):
                            # Check if it's stdlib or local module
                            is_stdlib = any(lib in line for lib in ['json', 'inspect', 'os', 'sys', 're', 'typing', 'pathlib'])

                            inline_imports.append({
                                "line": i,
                                "content": line.strip(),
                                "is_stdlib": is_stdlib
                            })

                    if inline_imports:
                        # Separate stdlib from local imports
                        stdlib_count = sum(1 for imp in inline_imports if imp["is_stdlib"])
                        local_count = len(inline_imports) - stdlib_count

                        severity = "INFO" if stdlib_count == len(inline_imports) else "MEDIUM"

                        self.log_change("manual_review", {
                            "severity": severity,
                            "priority": "INFO" if severity == "INFO" else "WARNING",
                            "type": "Inline imports detected",
                            "file": str(py_file),
                            "lines": [imp["line"] for imp in inline_imports[:3]],  # Show first 3
                            "count": len(inline_imports),
                            "stdlib_count": stdlib_count,
                            "local_count": local_count,
                            "action": "Consider consolidating to top if local imports (stdlib inline is often intentional)",
                            "reason": "Inline imports can cause issues with circular dependencies"
                        })
                except:
                    pass

    def process_branch(self):
        """Process all Python files in the branch."""
        apps_dir = self.branch_path / "apps"

        if not apps_dir.exists():
            console.console.print(f"⚠️  Warning: apps/ directory not found in {self.branch_path}")
            console.console.print("This branch may not have been upgraded yet.")
            return

        console.print(f"\n🔍 Scanning Python files in {apps_dir}...")

        # Process all Python files
        py_files = list(apps_dir.rglob("*.py"))
        for py_file in py_files:
            if "__pycache__" in str(py_file):
                continue

            console.print(f"  📝 Processing: {py_file.name}")
            self.process_python_file(py_file)

        # Detect manual review items
        console.print(f"\n🔍 Checking for manual review items...")
        self.detect_manual_review_items(self.branch_path)

    def generate_summary(self):
        """Generate summary statistics."""
        self.changes_report["summary"] = {
            "pattern_1_sys_path": len(self.changes_report["pattern_1_sys_path"]),
            "pattern_2_ecosystem_root": len(self.changes_report["pattern_2_ecosystem_root"]),
            "pattern_3_path_calcs": len(self.changes_report["pattern_3_path_calcs"]),
            "pattern_4_runtime_paths": len(self.changes_report["pattern_4_runtime_paths"]),
            "pattern_5_cross_imports": len(self.changes_report["pattern_5_cross_imports"]),
            "pattern_6_func_deletion": len(self.changes_report["pattern_6_func_deletion"]),
            "prax_import_fixes": len(self.changes_report["prax_imports"]),
            "intra_branch_import_fixes": len(self.changes_report["intra_branch_imports"]),
            "manual_review_items": len(self.changes_report["manual_review"]),
            "total_errors": len(self.changes_report["errors"]),
            "dry_run": self.dry_run
        }

    def save_report(self):
        """Save the changes report to DOCUMENTS/ folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.branch_path / "DOCUMENTS" / f"apps_migration_report_{timestamp}.json"

        # Create DOCUMENTS if doesn't exist
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.changes_report, f, indent=2)

        console.print(f"\n✅ Report saved to: {report_path}")

    def print_summary(self):
        """Print a summary of changes."""
        summary = self.changes_report["summary"]

        console.print("\n" + "="*70)
        console.print("Apps Migration Import Fixer Report (v2.2)")
        console.print("="*70)
        console.print(f"Mode: {'🔍 DRY RUN' if self.dry_run else '✅ LIVE EXECUTION'}")
        console.print(f"Branch: {self.branch_name} ({self.branch_path})")
        console.print(f"Timestamp: {self.changes_report['timestamp']}")

        console.print("\n📊 Pattern Fixes Summary:")
        console.print(f"  Pattern 1 (sys.path parent.parent → AIPASS_ROOT): {summary['pattern_1_sys_path']}")
        console.print(f"  Pattern 2 (ECOSYSTEM_ROOT calculations): {summary['pattern_2_ecosystem_root']}")
        console.print(f"  Pattern 3 (Path calculations): {summary['pattern_3_path_calcs']}")
        console.print(f"  Pattern 4 (Runtime path references): {summary['pattern_4_runtime_paths']}")
        console.print(f"  Pattern 5 (Cross-module imports): {summary['pattern_5_cross_imports']}")
        console.print(f"  Pattern 6 (Function deletions): {summary['pattern_6_func_deletion']}")
        console.print(f"  Pattern 7 (Prax imports): {summary['prax_import_fixes']}")
        console.print(f"  Pattern 8 (Intra-branch imports): {summary['intra_branch_import_fixes']}")

        total_fixes = (summary['pattern_1_sys_path'] + summary['pattern_2_ecosystem_root'] +
                      summary['pattern_3_path_calcs'] + summary['pattern_4_runtime_paths'] +
                      summary['pattern_5_cross_imports'] + summary['pattern_6_func_deletion'] +
                      summary['prax_import_fixes'] + summary['intra_branch_import_fixes'])

        console.print(f"\n✅ Total automated fixes: {total_fixes}")
        console.print(f"⚠️  Manual review items: {summary['manual_review_items']}")
        console.print(f"❌ Errors: {summary['total_errors']}")

        # Show details if not too many
        if total_fixes > 0 and total_fixes <= 20:
            console.print("\n📝 Detailed Changes:")
            for category in ["pattern_1_sys_path", "pattern_2_ecosystem_root", "pattern_3_path_calcs",
                           "pattern_4_runtime_paths", "pattern_5_cross_imports", "pattern_6_func_deletion"]:
                if self.changes_report[category]:
                    console.print(f"\n  {category.replace('_', ' ').title()}:")
                    for change in self.changes_report[category]:
                        console.print(f"    • {Path(change['file']).name}: {change['pattern']}")

        if self.changes_report["manual_review"]:
            console.print("\n⚠️  MANUAL REVIEW REQUIRED:")
            for item in self.changes_report["manual_review"]:
                console.print(f"  • {item['type']}: {item['action']}")
                if 'file' in item:
                    console.print(f"    File: {Path(item['file']).name}")
                if 'files' in item:
                    console.print(f"    Files: {', '.join([Path(f).name for f in item['files']])}")

        if self.changes_report["errors"]:
            console.print("\n❌ ERRORS ENCOUNTERED:")
            for error in self.changes_report["errors"]:
                console.print(f"  • {error['error']}")
                if error['file']:
                    console.print(f"    File: {error['file']}")

        console.print("\n" + "="*70)
        console.print(f"📄 Full report saved to: DOCUMENTS/apps_migration_report_<timestamp>.json")
        console.print("="*70)

    def execute(self, dry_run: bool = False):
        """Execute the migration fixes."""
        self.dry_run = dry_run

        console.print(f"\n🔧 Starting apps/ migration import fixes {'(DRY RUN)' if dry_run else '(LIVE)'}...")
        console.print(f"Branch path: {self.branch_path}\n")

        # Process all files
        self.process_branch()

        # Generate summary
        self.generate_summary()

        # Print and save report
        self.print_summary()
        self.save_report()

        return self.changes_report


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Fix imports after apps/ structure upgrade',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  python3 apps_migration_fixer.py /home/aipass/drone --dry-run
  python3 apps_migration_fixer.py /home/aipass/drone
  python3 apps_migration_fixer.py /home/aipass/flow
        """
    )

    parser.add_argument('branch_path',
                       type=str,
                       help='Path to branch directory (e.g., /home/aipass/drone)')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be changed without making changes')

    args = parser.parse_args()

    # Validate path
    branch_path = Path(args.branch_path)
    if not branch_path.exists():
        console.print(f"❌ Error: Branch path does not exist: {branch_path}")
        return 1

    if not branch_path.is_dir():
        console.print(f"❌ Error: Path is not a directory: {branch_path}")
        return 1

    # Execute
    fixer = AppsMigrationFixer(args.branch_path)
    fixer.execute(dry_run=args.dry_run)

    if args.dry_run:
        console.print("\n💡 This was a DRY RUN. To execute changes, run without --dry-run flag.")
    else:
        console.print("\n✅ Import fixes completed! Check the report in DOCUMENTS/ for details.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
