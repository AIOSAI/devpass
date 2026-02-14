#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_error_monitor_e2e.py - Error Monitor End-to-End Test
# Date: 2026-02-02
# Version: 1.0.0
# Category: dev_central/tools
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-02): Created - FPLAN-0284 Phase 3
#
# CODE STANDARDS:
#   - Test script for verifying error monitor chain
#   - Injects ERROR into log, verifies event fired, verifies notification delivered
# =============================================

"""
Error Monitor End-to-End Test

Tests the full chain:
1. Inject ERROR into a branch log
2. Verify Trigger's log_watcher fires error_detected event
3. Verify AI_Mail's error_handler delivers notification to branch inbox

Usage:
    python3 tools/test_error_monitor_e2e.py
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

AIPASS_ROOT = Path.home() / "aipass_core"
AIPASS_HOME = Path.home()
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(AIPASS_HOME))


def inject_test_error(branch_name: str = "flow") -> dict:
    """
    Inject a test ERROR entry into a branch log.

    Returns:
        dict with error details for verification
    """
    branch_path = AIPASS_ROOT / branch_name
    log_dir = branch_path / "logs"
    log_file = log_dir / f"{branch_name}.log"

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create test error in prax format
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_module = "test_error_monitor"
    test_message = f"TEST ERROR for e2e verification - {timestamp}"

    log_entry = f"{timestamp} | {test_module} | ERROR | {test_message}\n"

    print(f"[TEST] Injecting error into {log_file}")
    print(f"[TEST] Entry: {log_entry.strip()}")

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)

    return {
        'branch': branch_name,
        'module': test_module,
        'message': test_message,
        'timestamp': timestamp,
        'log_file': str(log_file)
    }


def check_trigger_event_log(test_info: dict, timeout_seconds: int = 10) -> bool:
    """
    Check if Trigger fired an error_detected event.

    Returns:
        True if event found in trigger/logs/core.log
    """
    event_log = AIPASS_ROOT / "trigger" / "logs" / "core.log"

    if not event_log.exists():
        print(f"[TEST] Event log not found: {event_log}")
        return False

    print(f"[TEST] Checking event log: {event_log}")

    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        with open(event_log, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'error_detected' in content and test_info['module'] in content:
            print("[TEST] ✓ error_detected event found in trigger log")
            return True

        time.sleep(1)

    print("[TEST] ✗ error_detected event NOT found in trigger log")
    return False


def check_branch_inbox(branch_name: str, test_info: dict) -> bool:
    """
    Check if notification was delivered to branch inbox.

    Returns:
        True if notification found
    """
    branch_path = AIPASS_ROOT / branch_name
    inbox_path = branch_path / f"{branch_name}.local" / "inbox.json"

    # Also check alternate location
    alt_inbox = branch_path / "ai_mail.local" / "inbox.json"

    for inbox in [inbox_path, alt_inbox]:
        if inbox.exists():
            print(f"[TEST] Checking inbox: {inbox}")
            try:
                with open(inbox, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for msg in data.get('messages', []):
                    if test_info['module'] in msg.get('message', ''):
                        print(f"[TEST] ✓ Notification found in inbox: {msg.get('subject', 'No subject')}")
                        return True
            except Exception as e:
                print(f"[TEST] Error reading inbox: {e}")

    print(f"[TEST] ✗ Notification NOT found in {branch_name} inbox")
    return False


def run_test():
    """Run the full end-to-end test."""
    print("=" * 60)
    print("ERROR MONITOR E2E TEST")
    print("=" * 60)
    print()

    # Step 1: Inject test error
    print("[STEP 1] Injecting test error...")
    test_info = inject_test_error("flow")
    print()

    # Step 2: Check if log watcher is running
    print("[STEP 2] NOTE: Log watcher must be running for this test.")
    print("         Start with: python3 /home/aipass/aipass_core/trigger/apps/trigger.py watch")
    print()

    # Step 3: Check trigger event log
    print("[STEP 3] Checking for error_detected event...")
    event_fired = check_trigger_event_log(test_info, timeout_seconds=5)
    print()

    # Step 4: Check branch inbox
    print("[STEP 4] Checking for notification in inbox...")
    notification_delivered = check_branch_inbox("flow", test_info)
    print()

    # Summary
    print("=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"  Error injected:           ✓")
    print(f"  Event fired (trigger):    {'✓' if event_fired else '✗ (is log_watcher running?)'}")
    print(f"  Notification delivered:   {'✓' if notification_delivered else '✗ (is error_handler registered?)'}")
    print()

    if event_fired and notification_delivered:
        print("OVERALL: ✓ PASS - Full chain working!")
        return True
    elif not event_fired:
        print("OVERALL: ✗ FAIL - Log watcher not detecting errors")
        print("         Run: python3 /home/aipass/aipass_core/trigger/apps/trigger.py watch")
        return False
    else:
        print("OVERALL: ✗ FAIL - Notification not delivered")
        print("         Check error_handler registration in AI_Mail")
        return False


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
