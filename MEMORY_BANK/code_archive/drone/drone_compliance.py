   #!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: drone_compliance.py - AI-Powered CLI Compliance Upgrades
# Date: 2025-10-17
# Version: 1.0.0
# Category: drone
#
# CHANGELOG:
#   - v1.0.0 (2025-10-17): Initial implementation with OpenRouter AI
# =============================================

"""
Drone CLI Compliance Upgrader

Automatically upgrades Python CLI modules to be drone-compatible using AI.
Uses OpenRouter API to generate compliant --help code based on existing module.

Features:
- AI-powered code generation (reads CLI_COMPLIANCE_INSTRUCTIONS.md)
- Automatic backup before changes
- Diff preview before applying
- Post-upgrade verification with drone scan
- 3-file JSON tracking (config/data/log)

Workflow:
1. Read non-compliant module
2. Send to AI with compliance instructions
3. Show diff preview
4. Apply with backup (optional)
5. Test with drone scan
"""

# =============================================
# IMPORTS
# =============================================

# INFRASTRUCTURE IMPORT PATTERN - Universal AIPass pattern
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.append(str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger

# Standard imports
import json
import difflib
import shutil
from datetime import datetime, timezone
from typing import Optional, Dict, List
import argparse

# Drone modules - relative import (same directory)
from drone_discovery import scan_module

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "drone_compliance"
MODULE_VERSION = "1.0.0"

# API import - following flow_plan_summarizer pattern (post-migration path)
try:
    ##from api.apps.modules.openrouter import get_response
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    logger.error(f"[{MODULE_NAME}] CRITICAL: API provider not available - cannot upgrade modules")

# Paths - Fixed for apps/ location
DRONE_DIR = AIPASS_ROOT / "drone"
ECOSYSTEM_ROOT = Path.home()  # Scan from /home/aipass/ (not just aipass_core)
DRONE_JSON_DIR = DRONE_DIR / "drone_json"
COMPLIANCE_INSTRUCTIONS = DRONE_DIR / "DOCUMENTS" / "CLI_COMPLIANCE_INSTRUCTIONS.md"

# 3-File JSON Pattern
CONFIG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_config.json"
DATA_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_data.json"
LOG_FILE = DRONE_JSON_DIR / f"{MODULE_NAME}_log.json"

# =============================================
# CONFIG MANAGEMENT
# =============================================

def load_config() -> Dict:
    """Load configuration with auto-healing (3-file JSON pattern)"""
    default_config = {
        "ai_model": "anthropic/claude-haiku-4.5",
        "created_date": datetime.now(timezone.utc).isoformat(),
        "version": MODULE_VERSION
    }

    if not CONFIG_FILE.exists():
        logger.info(f"[{MODULE_NAME}] Config file not found - creating default: {CONFIG_FILE}")
        DRONE_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # Ensure ai_model exists (auto-heal if missing)
        if "ai_model" not in config:
            logger.warning(f"[{MODULE_NAME}] Config missing 'ai_model' - adding default")
            config["ai_model"] = default_config["ai_model"]
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        return config
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error loading config: {e} - using default")
        return default_config

# =============================================
# LOGGING
# =============================================

def log_operation(operation: str, success: bool, details: str = "", error: str = ""):
    """Log compliance operations"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "success": success,
        "details": details,
        "error": error
    }

    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []

    logs.append(log_entry)

    # Keep last 1000 entries
    if len(logs) > 1000:
        logs = logs[-1000:]

    try:
        DRONE_JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error saving log: {e}")

# =============================================
# CORE FUNCTIONS
# =============================================

def read_module(module_path: Path) -> Optional[str]:
    """Read module code from file"""
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error reading module: {e}")
        return None

def get_compliance_instructions() -> Optional[str]:
    """Read CLI compliance instructions"""
    try:
        if not COMPLIANCE_INSTRUCTIONS.exists():
            logger.error(f"[{MODULE_NAME}] Compliance instructions not found: {COMPLIANCE_INSTRUCTIONS}")
            return None

        with open(COMPLIANCE_INSTRUCTIONS, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error reading instructions: {e}")
        return None

def ai_upgrade_module(module_code: str, instructions: str, module_name: str) -> Optional[str]:
    """
    Use AI to upgrade module to CLI compliance

    Args:
        module_code: Original module code
        instructions: CLI compliance instructions
        module_name: Name of module for logging

    Returns:
        Upgraded code or None if failed
    """
    if not API_AVAILABLE:
        print("❌ OpenRouter API not available")
        logger.error(f"[{MODULE_NAME}] OpenRouter API not imported")
        log_operation("ai_upgrade", False, "", "API not available")
        return None

    try:
        # Build AI prompt - following flow_plan_summarizer pattern
        system_prompt = f"""You are a Python code expert specializing in CLI module compliance.

Your task: Upgrade Python CLI modules to follow the AIPass CLI standard.

INSTRUCTIONS:
{instructions}

CRITICAL RULES:
1. Preserve ALL existing functionality - only add compliance code
2. Keep all imports, functions, and logic intact
3. Add argparse if not present
4. Add --help support with "Commands: cmd1, cmd2, cmd3, --flag1, --flag2" line
5. Return ONLY the complete updated Python code
6. Do NOT add explanations or markdown - just code
7. **COMPREHENSIVE COMMAND DETECTION** - You MUST find ALL user-facing commands AND flags:
   - Positional arguments (choices=['cmd1', 'cmd2'])
   - ALL optional flags (--note, --verbose, --output, etc.)
   - Boolean flags (action='store_true')
   - Value flags (type=str, type=int)
   - Utility flags (--list-*, --show-*, --diff, etc.)
   - Comparison flags (--v1, --v2, etc.)
   - **IN-CHAT COMMANDS** (quit, exit, help, status in main loop)
   - **FILE OPERATIONS** (load file, read file, open file, save)
   - **SPECIAL PREFIXES** (add knowledge:, store:, note:)
8. **CRITICAL: READ ACTUAL FUNCTION BODIES, NOT JUST ARGPARSE**:
   - Argparse only shows CLI interface - actual commands live in handle_command() functions!
   - Find functions: `_handle_*` or `handle_*` or `handle_command()`
   - **READ THE ENTIRE FUNCTION BODY** line by line

9. **SCAN handle_command() USING THESE EXACT PATTERNS**:

   **Pattern 1: List Membership (MOST IMPORTANT)**:
     - Search: `if user_input in [...]` or `if msg in [...]` or `elif input in [...]`
     - Extract EVERY string literal inside brackets
     - Example: `if user_input in ["update system", "reload system", "999"]`
       → Commands: "update system", "reload system", "999" (ALL THREE)
     - Multi-word strings are intentional commands, don't skip them!

   **Pattern 2: Exact String Equality**:
     - Search: `if user_input == "command"` or `if msg == "quit"`
     - Include string literal as command

   **Pattern 3: All List Items**:
     - `if x in ["cmd1", "cmd2", "cmd3"]` → include cmd1, cmd2, cmd3
     - Even in elif branches

   **Pattern 4: Multi-Word Commands Are Distinct**:
     - "update system" ≠ "update" (different commands)
     - "reload openai" is a real command, not a variant
     - Numeric triggers: "999", "000" (include as-is)

10. **OTHER COMMAND SOURCES**:
   - Look for `if msg == "quit"` or `startswith("exit")` patterns
   - Find pattern matching (regex, startswith, contains)
   - **CHECK EVERY regex pattern** - if code has `re.match(r"(store fact:|save info:|add fact:)")`, include ALL variants
   - Special prefixes (add knowledge:, store:, note:)
   - Multi-word variants with different word orders: `"reload openai"` AND `"openai reload"` are BOTH commands
9. **KEEP `--` PREFIX on all flags** (write `--note`, NOT `note`)
10. If module already has argparse, READ ALL parser.add_argument() calls to find every flag
11. The Commands: line must include EVERYTHING a user can invoke
"""

        user_prompt = f"""Upgrade this Python module to be CLI compliant:

```python
{module_code}
```

Requirements:
1. Add argparse with RawDescriptionHelpFormatter
2. Include "Commands: cmd1, cmd2, cmd3, --flag1, --flag2" line in epilog
3. **CRITICAL: READ handle_command() FUNCTION BODY, NOT JUST ARGPARSE**:
   - Argparse shows CLI interface, real commands are in handle_command()
   - Search for: `if user_input in [...]` patterns
   - Extract EVERY string literal inside brackets
   - Example: `if user_input in ["update system", "reload openai", "999"]`
     → Commands: "update system", "reload openai", "999" (ALL THREE)
   - Multi-word commands are intentional, don't skip them!
4. **ALSO SCAN FOR**:
   - Main loop command handlers (quit, exit, help)
   - File operations (load file, read file, save)
   - Special command prefixes (add knowledge:, store:)
   - Pattern matching handlers (startswith, regex, contains)
4. **KEEP `--` prefix on flags** (--note, --diff, NOT note, diff)
5. Preserve all existing functionality
6. Return only the complete updated code (no explanations)
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        config = load_config()
        model_name = config.get("ai_model", "anthropic/claude-haiku-4.5")

        print("🤖 Sending module to AI for compliance upgrade...")
        print(f"   Model: {model_name}")
        logger.info(f"[{MODULE_NAME}] Requesting AI upgrade for {module_name}")

        # Call OpenRouter - using configured model (default: Claude Haiku 4.5)
        # Haiku 4.5: 73% SWE-bench Verified, $1/$5 per M tokens, released Oct 2025
        response = get_response(
            messages=messages,
            model=model_name,
            caller="drone_compliance"
        )

        if not response:
            print("❌ AI upgrade failed - no response from API")
            logger.error(f"[{MODULE_NAME}] No response from AI for {module_name}")
            log_operation("ai_upgrade", False, "", "No API response")
            return None

        # Clean response (remove markdown code blocks if present)
        cleaned = response.strip()
        if cleaned.startswith("```python"):
            cleaned = cleaned.split("```python", 1)[1]
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 1)[1]
        if "```" in cleaned:
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        print("✅ AI upgrade complete")
        logger.info(f"[{MODULE_NAME}] AI upgrade successful for {module_name}")
        log_operation("ai_upgrade", True, f"Module: {module_name}")

        return cleaned

    except Exception as e:
        print(f"❌ AI upgrade error: {e}")
        logger.error(f"[{MODULE_NAME}] AI upgrade error: {e}")
        log_operation("ai_upgrade", False, "", str(e))
        return None

def ai_fix_imports(module_code: str, error_output: str, module_name: str) -> Optional[str]:
    """
    Use AI to fix import errors in module

    Args:
        module_code: Original module code
        error_output: Error output from running the module
        module_name: Name of module for logging

    Returns:
        Fixed code or None if failed
    """
    if not API_AVAILABLE:
        print("❌ OpenRouter API not available")
        logger.error(f"[{MODULE_NAME}] OpenRouter API not imported for import fix")
        log_operation("ai_fix_imports", False, "", "API not available")
        return None

    try:
        system_prompt = """You are a Python import error fixer.

Your task: Fix import errors in Python modules, especially after apps/ migration.

COMMON FIXES:
1. from prax.prax_logger → from prax.apps.prax_logger
2. from api.openrouter → from api.apps.openrouter
3. from module_name → from apps.module_name (for local imports)

RULES:
1. ONLY fix imports - do NOT change any other code
2. Preserve ALL existing functionality
3. Keep all imports, functions, and logic intact
4. Return ONLY the complete updated Python code
5. Do NOT add explanations or markdown - just code
"""

        user_prompt = f"""Fix the import errors in this Python module:

ERROR OUTPUT:
```
{error_output}
```

MODULE CODE:
```python
{module_code}
```

Fix ONLY the import statements that are causing the errors. Return the complete fixed code."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        config = load_config()
        model_name = config.get("ai_model", "anthropic/claude-haiku-4.5")

        print(f"🤖 Sending module to AI for import fix...")
        print(f"   Model: {model_name}")

        response = get_response(
            messages=messages,
            model=model_name,
            caller="drone_compliance"
        )

        if not response:
            print("❌ No response from AI")
            logger.error(f"[{MODULE_NAME}] No AI response for import fix")
            log_operation("ai_fix_imports", False, f"Module: {module_name}", "No response")
            return None

        # Clean response (remove markdown code blocks if present)
        # get_response() returns string directly, not dict with 'choices'
        cleaned = response.strip()
        if cleaned.startswith("```python"):
            cleaned = cleaned.split("```python", 1)[1]
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 1)[1]
        if "```" in cleaned:
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        print("✅ AI import fix complete")
        logger.info(f"[{MODULE_NAME}] AI import fix successful for {module_name}")
        log_operation("ai_fix_imports", True, f"Module: {module_name}")

        return cleaned

    except Exception as e:
        print(f"❌ AI import fix error: {e}")
        logger.error(f"[{MODULE_NAME}] AI import fix error: {e}")
        log_operation("ai_fix_imports", False, "", str(e))
        return None

def show_diff(original: str, updated: str, module_path: Path):
    """Show diff between original and updated code"""
    print("\n" + "=" * 70)
    print("DIFF PREVIEW")
    print("=" * 70)

    original_lines = original.splitlines(keepends=True)
    updated_lines = updated.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        updated_lines,
        fromfile=f"{module_path.name} (original)",
        tofile=f"{module_path.name} (upgraded)",
        lineterm=''
    )

    diff_output = list(diff)
    if not diff_output:
        print("\n⚠️  No changes detected")
        return False

    for line in diff_output[:100]:  # Limit to first 100 lines
        if line.startswith('+'):
            print(f"\033[32m{line}\033[0m")  # Green
        elif line.startswith('-'):
            print(f"\033[31m{line}\033[0m")  # Red
        else:
            print(line)

    if len(diff_output) > 100:
        print(f"\n... ({len(diff_output) - 100} more lines)")

    print("\n" + "=" * 70)
    return True

def backup_module(module_path: Path) -> Optional[Path]:
    """Create backup of module before modifying"""
    try:
        backup_path = module_path.with_suffix(module_path.suffix + '.backup')
        shutil.copy2(module_path, backup_path)
        print(f"💾 Backup created: {backup_path}")
        logger.info(f"[{MODULE_NAME}] Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        logger.error(f"[{MODULE_NAME}] Backup failed: {e}")
        return None

def apply_upgrade(module_path: Path, upgraded_code: str) -> bool:
    """Apply upgraded code to module"""
    try:
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(upgraded_code)
        print(f"✅ Module updated: {module_path}")
        logger.info(f"[{MODULE_NAME}] Module updated: {module_path}")
        log_operation("apply_upgrade", True, f"Module: {module_path.name}")
        return True
    except Exception as e:
        print(f"❌ Failed to write updated code: {e}")
        logger.error(f"[{MODULE_NAME}] Write failed: {e}")
        log_operation("apply_upgrade", False, f"Module: {module_path.name}", str(e))
        return False

def verify_upgrade(module_path: Path) -> bool:
    """Test upgraded module with drone scan"""
    print("\n" + "=" * 70)
    print("VERIFICATION - Running drone scan")
    print("=" * 70)

    # Convert absolute path to @ format for scan_module (required by new @ standard)
    if module_path.is_relative_to(ECOSYSTEM_ROOT):
        scan_path = f"@{module_path.relative_to(ECOSYSTEM_ROOT)}"
    else:
        scan_path = f"@{module_path}"

    result = scan_module(scan_path)

    if result['success'] and result['commands']:
        print(f"\n✅ Verification passed - {len(result['commands'])} commands detected:")
        for cmd in result['commands']:
            print(f"   - {cmd}")
        log_operation("verify_upgrade", True, f"Module: {module_path.name}, Commands: {len(result['commands'])}")
        return True
    else:
        print(f"\n❌ Verification failed - no commands detected")
        if result.get('error'):
            print(f"Error: {result['error']}")
        log_operation("verify_upgrade", False, f"Module: {module_path.name}", result.get('error', 'No commands'))
        return False

# =============================================
# AUTO-REFRESH
# =============================================

def auto_refresh_after_upgrade(module_path: Path) -> None:
    """
    Automatically refresh system(s) after module upgrade

    Finds which registered system(s) contain this module and refreshes them.
    This eliminates the manual refresh step after compliance upgrades.

    Args:
        module_path: Path to the upgraded module
    """
    from drone_discovery import refresh_system

    # Registries are stored per-system in /drone/commands/{system}/registry.json
    commands_dir = DRONE_DIR / "commands"
    if not commands_dir.exists():
        return  # No registrations exist yet

    module_path_str = str(module_path)
    systems_to_refresh = set()

    # Check each system's registry
    try:
        for system_dir in commands_dir.iterdir():
            if not system_dir.is_dir():
                continue

            registry_file = system_dir / "registry.json"
            if not registry_file.exists():
                continue

            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)

                # Check if any command in this system uses this module
                for cmd_data in registry.values():
                    if isinstance(cmd_data, dict) and cmd_data.get('module_path') == module_path_str:
                        systems_to_refresh.add(system_dir.name)
                        break  # Found this system, no need to check more commands

            except Exception as e:
                logger.error(f"[{MODULE_NAME}] Failed to load registry for {system_dir.name}: {e}")
                continue

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to scan commands directory: {e}")
        return

    # Refresh each system that contains this module
    if systems_to_refresh:
        for system_name in systems_to_refresh:
            print(f"\n🔄 Auto-refreshing system '{system_name}'...")
            result = refresh_system(system_name)
            if result['success']:
                if result['new_commands'] > 0:
                    print(f"✅ Refresh complete - {result['new_commands']} new commands detected")
                else:
                    print(f"✅ Refresh complete - no new commands")
            else:
                print(f"⚠️  Refresh failed: {result.get('error', 'Unknown error')}")

# =============================================
# MAIN FUNCTION
# =============================================

def upgrade_module(module_path: str | Path, auto_apply: bool = False) -> bool:
    """
    Main entry point - upgrade a module to CLI compliance

    Args:
        module_path: Path to module to upgrade
        auto_apply: If True, apply without confirmation

    Returns:
        True if successful, False otherwise
    """
    # Resolve path (handles @ symbol, system names, etc.)
    from drone_discovery import resolve_scan_path

    try:
        module_path = resolve_scan_path(str(module_path))
    except FileNotFoundError as e:
        print(f"❌ Path resolution failed: {e}")
        return False

    print("=" * 70)
    print("DRONE COMPLIANCE UPGRADER")
    print("=" * 70)
    print(f"Module: {module_path}")
    print()

    # 1. Read module
    print("📖 Reading module...")
    original_code = read_module(module_path)
    if not original_code:
        print("❌ Failed to read module")
        return False

    # 2. Read instructions
    print("📋 Loading compliance instructions...")
    instructions = get_compliance_instructions()
    if not instructions:
        print("❌ Failed to load compliance instructions")
        return False

    # 3. AI upgrade
    upgraded_code = ai_upgrade_module(original_code, instructions, module_path.name)
    if not upgraded_code:
        print("❌ AI upgrade failed")
        return False

    # 4. Show diff
    has_changes = show_diff(original_code, upgraded_code, module_path)
    if not has_changes:
        print("\n⚠️  No changes detected")
        print("\n🔍 Verifying current compliance status...")

        # === AIPASS FIX START ===
        # Check compliance by analyzing source code instead of executing
        # (executing with --help can cause side effects on non-compliant modules)
        print("   Analyzing source code for compliance indicators...")

        # Check for argparse import
        has_argparse = 'import argparse' in original_code or 'from argparse import' in original_code

        # Check for "Commands:" comment in help text (compliance indicator)
        has_commands_line = 'Commands:' in original_code

        if has_argparse and has_commands_line:
            print("✅ Module appears compliant (has argparse + Commands: line)")
            print("💡 No upgrade needed - module already follows compliance pattern")
            return False
        else:
            print("❌ Module is non-compliant but AI couldn't generate upgrade")
            print(f"   - Has argparse: {has_argparse}")
            print(f"   - Has Commands: line: {has_commands_line}")
            print("\n💡 This module may need manual compliance upgrade")
            print("   The AI couldn't determine how to add --help support automatically")
            return False
        # === AIPASS FIX END ===

        # OLD CODE: Run module with --help (DANGEROUS - causes side effects!)
        # Keeping this commented for reference
        """
        import subprocess
        try:
            result = subprocess.run(
                ['python3', str(module_path), '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Check if help output contains "Commands:" line (compliance indicator)
            help_output = result.stdout + result.stderr
            commands_found = False

            for line in help_output.splitlines():
                if line.strip().startswith('Commands:'):
                    commands_found = True
                    break

            if commands_found and result.returncode == 0:
                # Module IS compliant
                print("✅ Module is already compliant")
                print("💡 No upgrade needed - this was likely a false positive")
                return False
            else:
                # Module is NOT compliant - AI couldn't fix it
                print("❌ Module is still non-compliant but AI couldn't generate a fix")

                # Show the actual error
                if result.returncode != 0:
                    error_output = result.stderr.strip() if result.stderr.strip() else result.stdout.strip()
                    if error_output:
                        print(f"\n📋 Actual error when running module:")
                        # Show first few lines of error
                        error_lines = error_output.splitlines()[:5]
                        for line in error_lines:
                            print(f"   {line}")

                        # Check for common issues and offer to fix
                        if 'ModuleNotFoundError' in error_output or 'ImportError' in error_output:
                            print("\n💡 This looks like an import error")

                            # Offer to fix the import error
                            try:
                                fix_choice = input("\nWould you like to fix this import error now? (y/n): ").strip().lower()
                            except (KeyboardInterrupt, EOFError):
                                print("\n\nCancelled.")
                                return False

                            if fix_choice == 'y':
                                print("\n🔧 Attempting to fix import error...")
                                fixed_code = ai_fix_imports(original_code, error_output, module_path.name)

                                if fixed_code and fixed_code != original_code:
                                    # Show diff of import fix
                                    print("\n" + "=" * 70)
                                    print("IMPORT FIX PREVIEW")
                                    print("=" * 70)
                                    show_diff(original_code, fixed_code, module_path)

                                    # Apply import fix
                                    backup_path = backup_module(module_path)
                                    if backup_path and apply_upgrade(module_path, fixed_code):
                                        print("\n✅ Import fix applied")
                                        print(f"💾 Backup: {backup_path}")

                                        # Retry compliance upgrade with fixed imports
                                        # Convert absolute path back to @ format for retry
                                        abs_path = Path(module_path)
                                        if str(abs_path).startswith('/home/aipass/'):
                                            relative_path = abs_path.relative_to('/home/aipass')
                                            at_path = f"@{relative_path}"
                                        else:
                                            at_path = f"@{abs_path}"

                                        print("\n🔄 Retrying compliance upgrade...")
                                        return upgrade_module(at_path, auto_apply=auto_apply)
                                    else:
                                        print("\n❌ Failed to apply import fix")
                                        return False
                                else:
                                    print("\n❌ Could not generate import fix")
                                    return False
                            else:
                                print("\n💡 Fix imports manually before retrying compliance upgrade")
                                return False

                        elif 'SyntaxError' in error_output:
                            print("\n💡 This looks like a syntax error - fix syntax before compliance upgrade")

                return False

        except subprocess.TimeoutExpired:
            print("❌ Module timed out during verification - may have infinite loop or blocking input")
            return False
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
        """
        # END OLD CODE

    # 5. Confirm (unless auto_apply)
    if not auto_apply:
        print("\n" + "=" * 70)
        response = input("Apply these changes? (y/n): ").strip().lower()
        if response != 'y':
            print("❌ Upgrade cancelled by user")
            log_operation("upgrade_module", False, f"Module: {module_path.name}", "Cancelled by user")
            return False

    # 6. Backup
    backup_path = backup_module(module_path)
    if not backup_path:
        print("❌ Cannot proceed without backup")
        return False

    # 7. Apply
    if not apply_upgrade(module_path, upgraded_code):
        print(f"❌ Failed to apply upgrade")
        print(f"💡 Original preserved at: {backup_path}")
        return False

    # 8. Verify
    success = verify_upgrade(module_path)

    if success:
        print("\n" + "=" * 70)
        print("✅ UPGRADE SUCCESSFUL")
        print("=" * 70)
        print(f"Module: {module_path}")
        print(f"Backup: {backup_path}")

        # Auto-refresh any registered systems containing this module
        auto_refresh_after_upgrade(module_path)

        print(f"\n💡 You can now:")
        print(f"   - drone scan @{module_path.relative_to(ECOSYSTEM_ROOT) if module_path.is_relative_to(ECOSYSTEM_ROOT) else module_path}")
        print(f"   - drone reg @{module_path.relative_to(ECOSYSTEM_ROOT) if module_path.is_relative_to(ECOSYSTEM_ROOT) else module_path}")
        log_operation("upgrade_module", True, f"Module: {module_path.name}")
    else:
        print("\n" + "=" * 70)
        print("⚠️  UPGRADE APPLIED BUT VERIFICATION FAILED")
        print("=" * 70)
        print(f"Module: {module_path}")
        print(f"Backup: {backup_path}")
        print(f"\n💡 To restore original:")
        print(f"   mv {backup_path} {module_path}")
        log_operation("upgrade_module", False, f"Module: {module_path.name}", "Verification failed")

    return success

# =============================================
# CLI INTERFACE
# =============================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Drone CLI Compliance Upgrader - AI-powered automatic upgrades',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: upgrade, --auto

  upgrade - Upgrade Python module to drone CLI compliance standard
            Reads module, sends to AI, shows diff, applies with backup

OPTIONS:
  --auto  - Apply changes without confirmation prompt

EXAMPLES:
  python3 drone_compliance.py upgrade @tools/test_cleanup.py
  python3 drone_compliance.py upgrade /home/aipass/prax/prax_logger.py --auto
  python3 drone_compliance.py upgrade backup_cli.py

WORKFLOW:
  1. Reads non-compliant module code
  2. Sends to AI with CLI compliance instructions
  3. Shows diff preview (green=added, red=removed)
  4. Prompts for confirmation (unless --auto)
  5. Creates backup (.backup file)
  6. Applies upgraded code
  7. Verifies with 'drone scan'

INTEGRATION:
  Via drone:  drone comply <module_path>
  Direct:     python3 drone_compliance.py upgrade <module_path>
        """
    )

    parser.add_argument('command',
                       choices=['upgrade'],
                       help='Command to execute')

    parser.add_argument('module_path',
                       type=str,
                       help='Path to module to upgrade (supports @symbol and system names)')

    parser.add_argument('--auto',
                       action='store_true',
                       help='Apply changes without confirmation prompt')

    args = parser.parse_args()

    # Route to command handler
    if args.command == 'upgrade':
        success = upgrade_module(args.module_path, args.auto)
        sys.exit(0 if success else 1)