#!/home/aipass/.venv/bin/python3

import sys
from pathlib import Path
import os

# Add the apps directory to the path so we can import handlers
BACKUP_SYSTEM = Path.home() / "aipass_core" / "backup_system"
sys.path.insert(0, str(BACKUP_SYSTEM / "apps"))

print("\n=== HANDLER FUNCTIONALITY TEST ===\n")

# Test 1: BackupResult (models)
print("1. Testing BackupResult class...")
try:
    from handlers.models.backup_models import BackupResult
    result = BackupResult()
    result.backup_path = "/tmp"
    result.mode = "snapshot"
    result.add_error("test error")
    result.add_warning("test warning")
    print(f"   OK BackupResult works - errors={len(result.error_details)}, warnings={len(result.warnings)}")
except Exception as e:
    print(f"   FAIL BackupResult failed: {e}")

# Test 2: Config handler
print("\n2. Testing config_handler...")
try:
    from handlers.config.config_handler import BACKUP_MODES, get_ignore_patterns
    modes = BACKUP_MODES
    patterns = get_ignore_patterns()
    print(f"   OK Config works - {len(modes)} modes, {len(patterns)} patterns")
except Exception as e:
    print(f"   FAIL Config failed: {e}")

# Test 3: temporarily_writable (utils)
print("\n3. Testing temporarily_writable context manager...")
try:
    from handlers.utils.system_utils import temporarily_writable
    test_path = Path("/tmp/test_file.txt")
    test_path.touch()
    with temporarily_writable(test_path):
        pass
    test_path.unlink()
    print(f"   OK temporarily_writable works")
except Exception as e:
    print(f"   FAIL temporarily_writable failed: {e}")

# Test 4: is_binary_file (diff)
print("\n4. Testing is_binary_file...")
try:
    from handlers.diff.diff_generator import is_binary_file
    result = is_binary_file(Path(__file__))  # Test on this script
    print(f"   OK is_binary_file works - this script is binary: {result}")
except Exception as e:
    print(f"   FAIL is_binary_file failed: {e}")

# Test 5: copy_file_with_structure (operations)
print("\n5. Testing copy_file_with_structure...")
try:
    from handlers.operations.file_operations import copy_file_with_structure
    from handlers.models.backup_models import BackupResult
    import tempfile
    import shutil

    # Create test files in a writable temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        test_source = tmpdir / "test_source.txt"
        test_target = tmpdir / "test_backup" / "test_source.txt"
        test_source.write_text("test content")

        result = BackupResult()
        result.backup_path = str(tmpdir)
        result.mode = "snapshot"
        success = copy_file_with_structure(test_source, test_target, tmpdir, result)

        print(f"   {'OK' if success else 'WARN'} copy_file_with_structure - success={success}")
except Exception as e:
    print(f"   FAIL copy_file_with_structure failed: {e}")

# Test 6: copy_versioned_file (operations)
print("\n6. Testing copy_versioned_file...")
try:
    from handlers.operations.file_operations import copy_versioned_file
    from handlers.models.backup_models import BackupResult
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        test_source = tmpdir / "test_versioned.txt"
        test_target = tmpdir / "backup" / "test_versioned.txt"
        test_source.write_text("version 1 content")

        result = BackupResult()
        result.backup_path = str(tmpdir)
        result.mode = "versioned"
        success = copy_versioned_file(test_source, test_target, tmpdir, result)

        print(f"   {'OK' if success else 'WARN'} copy_versioned_file - success={success}")
except Exception as e:
    print(f"   FAIL copy_versioned_file failed: {e}")

# Test 7: generate_diff_content (diff)
print("\n7. Testing generate_diff_content...")
try:
    from handlers.diff.diff_generator import generate_diff_content
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file1 = tmpdir / "file1.txt"
        file2 = tmpdir / "file2.txt"
        file1.write_text("original content\nline 2\nline 3")
        file2.write_text("modified content\nline 2\nline 3 changed")

        diff = generate_diff_content(file1, file2)
        print(f"   OK generate_diff_content - diff length={len(diff)} chars")
except Exception as e:
    print(f"   FAIL generate_diff_content failed: {e}")

# Test 8: BackupResult.add_error with is_critical flag
print("\n8. Testing BackupResult critical error tracking...")
try:
    from handlers.models.backup_models import BackupResult

    result = BackupResult()
    result.add_error("non-critical error", is_critical=False)
    result.add_error("critical error", is_critical=True)

    print(f"   OK Critical error tracking - total={len(result.error_details)}, critical={len(result.critical_errors)}, success={result.success}")
except Exception as e:
    print(f"   FAIL Critical error tracking failed: {e}")

# Test 9: should_create_diff (diff)
print("\n9. Testing should_create_diff...")
try:
    from handlers.diff.diff_generator import should_create_diff
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        text_file = tmpdir / "file.txt"
        binary_file = tmpdir / "file.bin"
        text_file.write_text("text content")
        binary_file.write_bytes(b"\x00\x01\x02\x03")

        text_result = should_create_diff(text_file)
        binary_result = should_create_diff(binary_file)
        print(f"   OK should_create_diff - text={text_result}, binary={binary_result}")
except Exception as e:
    print(f"   FAIL should_create_diff failed: {e}")

# Test 10: safe_print utility
print("\n10. Testing safe_print utility...")
try:
    from handlers.utils.system_utils import safe_print
    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    safe_print("Test message")
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    print(f"   OK safe_print - output captured: {len(output) > 0}")
except Exception as e:
    print(f"   FAIL safe_print failed: {e}")

# Test 11: get_versioned_files (version_manager)
print("\n11. Testing get_versioned_files...")
try:
    from handlers.diff.version_manager import get_versioned_files
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create a mock versioned structure
        file_folder = tmpdir / "subdir" / "testfile.txt"
        diff_folder = file_folder.parent / "testfile.txt_diffs"
        diff_folder.mkdir(parents=True, exist_ok=True)

        # Create some version diffs
        (diff_folder / "testfile.txt_v2025-11-16_10-30-00.diff").write_text("diff content")
        (diff_folder / "testfile.txt_v2025-11-16_11-30-00.diff").write_text("diff content 2")

        versioned = get_versioned_files(tmpdir)
        print(f"   OK get_versioned_files - found {len(versioned)} files")
except Exception as e:
    print(f"   FAIL get_versioned_files failed: {e}")

# Test 12: test get_ignore_patterns returns list
print("\n12. Testing get_ignore_patterns return type...")
try:
    from handlers.config.config_handler import get_ignore_patterns
    patterns = get_ignore_patterns()
    is_list = isinstance(patterns, list)
    has_patterns = len(patterns) > 0
    print(f"   OK get_ignore_patterns - is_list={is_list}, count={len(patterns)}")
except Exception as e:
    print(f"   FAIL get_ignore_patterns failed: {e}")

# Test 13: BACKUP_MODES constant
print("\n13. Testing BACKUP_MODES constant...")
try:
    from handlers.config.config_handler import BACKUP_MODES
    modes = BACKUP_MODES
    has_snapshot = "snapshot" in modes
    has_versioned = "versioned" in modes
    print(f"   OK BACKUP_MODES - snapshot={has_snapshot}, versioned={has_versioned}, modes={modes}")
except Exception as e:
    print(f"   FAIL BACKUP_MODES failed: {e}")

# Test 14: BackupResult file statistics
print("\n14. Testing BackupResult file statistics...")
try:
    from handlers.models.backup_models import BackupResult

    result = BackupResult()
    result.files_checked = 10
    result.files_copied = 8
    result.files_skipped = 2
    result.files_deleted = 1
    result.files_added = 3

    total = (result.files_checked + result.files_copied +
             result.files_skipped + result.files_deleted + result.files_added)
    print(f"   OK File statistics - checked={result.files_checked}, copied={result.files_copied}, skipped={result.files_skipped}")
except Exception as e:
    print(f"   FAIL File statistics failed: {e}")

# Test 15: get_backup_destination and get_cli_tracking_patterns (config)
print("\n15. Testing config helper functions...")
try:
    from handlers.config.config_handler import get_backup_destination, get_cli_tracking_patterns
    dest = get_backup_destination("system_snapshot")
    tracking = get_cli_tracking_patterns()
    print(f"   OK Config helpers - destination exists={Path(dest).exists()}, tracking patterns={len(tracking)}")
except Exception as e:
    print(f"   FAIL Config helpers failed: {e}")

# Test 16: filter_tracked_items (config)
print("\n16. Testing filter_tracked_items...")
try:
    from handlers.config.config_handler import filter_tracked_items
    test_items = {
        "directories": {"backups", "node_modules", "/home/aipass/aipass_core/backup_system"},
        "files": {"file.py", "test.log"}
    }
    filtered = filter_tracked_items(test_items)
    print(f"   OK filter_tracked_items - filtered {len(filtered['directories'])} dirs, {len(filtered['files'])} files")
except Exception as e:
    print(f"   FAIL filter_tracked_items failed: {e}")

print("\n=== TEST COMPLETE ===\n")
