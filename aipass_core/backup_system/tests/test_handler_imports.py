#!/home/aipass/.venv/bin/python3

"""
Handler Import Integrity Test

Verifies that each handler module can be imported independently.
Tests the structure integrity of the backup system handlers.
"""

import sys
from pathlib import Path

# Setup paths
AIPASS_ROOT = Path.home() / "aipass_core"
BACKUP_SYSTEM = AIPASS_ROOT / "backup_system"
APPS_DIR = BACKUP_SYSTEM / "apps"

sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(BACKUP_SYSTEM))
sys.path.insert(0, str(APPS_DIR))

# Change working directory to apps for relative imports
import os
os.chdir(str(APPS_DIR))

# Test specifications: (module_path, item_to_import)
HANDLERS_TO_TEST = [
    ("handlers.config.config_handler", "BACKUP_MODES"),
    ("handlers.config.config_handler", "get_ignore_patterns"),
    ("handlers.models.backup_models", "BackupResult"),
    ("handlers.utils.system_utils", "temporarily_writable"),
    ("handlers.utils.system_utils", "safe_print"),
    ("handlers.operations.file_operations", "copy_file_with_structure"),
    ("handlers.operations.file_operations", "copy_versioned_file"),
    ("handlers.diff.diff_generator", "generate_diff_content"),
    ("handlers.diff.diff_generator", "is_binary_file"),
    ("handlers.diff.version_manager", "get_versioned_files"),
    ("handlers.diff.version_manager", "list_versioned_files"),
    ("handlers.diff.vscode_integration", "show_file_diff"),
    ("handlers.json.json_handler", "log_operation"),
    ("handlers.json.json_handler", "load_json"),
    ("handlers.json.json_handler", "save_json"),
]

def run_import_tests():
    """Run all import tests and return results."""
    results = []
    failed_count = 0
    success_count = 0
    warning_count = 0

    print("\n" + "=" * 60)
    print("HANDLER IMPORT INTEGRITY TEST")
    print("=" * 60 + "\n")

    for module_path, item_name in HANDLERS_TO_TEST:
        test_label = f"{module_path}::{item_name}"
        try:
            # Attempt import
            module = __import__(module_path, fromlist=[item_name])
            item = getattr(module, item_name, None)

            if item is not None:
                success_count += 1
                status = "[PASS]"
                print(f"{status} {test_label}")
                results.append((test_label, "PASS", None))
            else:
                warning_count += 1
                status = "[WARN]"
                msg = f"Module loaded but '{item_name}' not found"
                print(f"{status} {test_label}")
                print(f"        {msg}")
                results.append((test_label, "WARN", msg))

        except ImportError as e:
            failed_count += 1
            status = "[FAIL]"
            error_msg = str(e)[:100]
            print(f"{status} {test_label}")
            print(f"        ImportError: {error_msg}")
            results.append((test_label, "FAIL", error_msg))

        except Exception as e:
            failed_count += 1
            status = "[FAIL]"
            error_msg = str(e)[:100]
            print(f"{status} {test_label}")
            print(f"        {type(e).__name__}: {error_msg}")
            results.append((test_label, "FAIL", error_msg))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests:    {len(HANDLERS_TO_TEST)}")
    print(f"Passed:         {success_count}")
    print(f"Warnings:       {warning_count}")
    print(f"Failed:         {failed_count}")
    print("=" * 60 + "\n")

    # Return exit code
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    exit_code = run_import_tests()
    sys.exit(exit_code)
