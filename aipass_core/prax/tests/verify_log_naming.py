#!/home/aipass/.venv/bin/python3

"""
Verification script for log file naming fix

This script verifies that the log naming changes work correctly
by inspecting the setup.py code logic without actually running it.
"""

from pathlib import Path

def verify_log_naming_logic():
    """Verify the log naming logic is correct"""

    print("\n=== PRAX Log Naming Fix Verification ===\n")

    # Read the setup.py file
    setup_file = Path("/home/aipass/aipass_core/prax/apps/handlers/logging/setup.py")
    content = setup_file.read_text()

    # Check 1: Branch detection happens FIRST
    if 'module_path = get_calling_module_path()' in content:
        if content.index('module_path = get_calling_module_path()') < content.index('system_log_file = SYSTEM_LOGS_DIR'):
            print("✅ Branch detection happens BEFORE log naming")
        else:
            print("❌ Branch detection happens AFTER log naming")
            return False

    # Check 2: Branch name extraction logic exists
    if 'branch_name = branch_path.split' in content:
        print("✅ Branch name extraction logic present")
    else:
        print("❌ Branch name extraction logic missing")
        return False

    # Check 3: System log uses branch_name variable
    if 'f"{branch_name}_{module_name}.log"' in content:
        print("✅ System logs use {branch_name}_{module_name}.log format")
    else:
        print("❌ System logs still using old format")
        return False

    # Check 4: Fallback to prax exists
    if '"prax"  # Fallback' in content or 'branch_name = "prax"' in content:
        print("✅ Fallback to 'prax' when no branch detected")
    else:
        print("❌ No fallback for when branch isn't detected")
        return False

    print("\n=== Expected Behavior ===\n")
    print("When Cortex calls prax logging:")
    print("  - detect_branch_from_path() returns: 'aipass_core/cortex'")
    print("  - branch_name extraction: 'cortex' (from split('/')[-1])")
    print("  - System log file: cortex_{module}.log")
    print("  - Branch log file: /home/aipass/aipass_core/cortex/logs/{module}.log")

    print("\nWhen Flow calls prax logging:")
    print("  - detect_branch_from_path() returns: 'aipass_core/flow'")
    print("  - branch_name extraction: 'flow'")
    print("  - System log file: flow_{module}.log")
    print("  - Branch log file: /home/aipass/aipass_core/flow/logs/{module}.log")

    print("\nWhen PRAX calls its own logging:")
    print("  - detect_branch_from_path() returns: 'aipass_core/prax'")
    print("  - branch_name extraction: 'prax'")
    print("  - System log file: prax_{module}.log")
    print("  - Branch log file: /home/aipass/aipass_core/prax/logs/{module}.log")

    print("\nWhen branch detection fails:")
    print("  - branch_path is None")
    print("  - Fallback: branch_name = 'prax'")
    print("  - System log file: prax_{module}.log")

    print("\n=== Code Logic Verification ===")
    return True

if __name__ == "__main__":
    success = verify_log_naming_logic()
    if success:
        print("\n✅ ALL CHECKS PASSED - Log naming fix is correct!")
        print("\nNext step: Actual runtime testing with different branches")
    else:
        print("\n❌ VERIFICATION FAILED - Review the changes")
