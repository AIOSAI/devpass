#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: drone.py - AIPass Command Orchestrator
# Date: 2025-09-22
# Version: 0.3.0
# Category: drone
#
# CHANGELOG:
#   - v0.3.0 (2025-09-22): Complete dynamic refactoring
#     * Removed all hardcoded COMMANDS dictionary (400+ lines)
#     * Dynamic command loading from JSON files
#     * Registry-based auto-discovery
#     * Prax logger integration
#     * Standards-compliant module structure
#   - v0.2.0 (2025-09-20): Linux migration and architecture planning
#     * Fixed Python command execution (python → python3 for Linux compatibility)
#     * Modular command architecture designed with JSON-based command files
#     * Global symlink deployment working (/usr/local/bin/drone)
#     * Backup system integration fully operational on Linux
#   - v0.1.1 (2025-01-11): Added help command
#     * Feature: 'drone help' displays available commands
#   - v0.1.0 (2025-01-11): Initial implementation
#     * Feature: Core command executor for AIPass ecosystem
#     * Feature: 'run seed' command support
#     * Feature: Path resolution from any directory
# =============================================

"""
AIPass Drone Command Executor

Dynamic command orchestrator for the AIPass ecosystem.
Auto-discovers and executes commands from JSON-based registry.

Features:
- Dynamic command discovery from JSON files
- Registry-based module coordination
- Auto-healing command registration
- Standards-compliant module structure

Status: Production-ready dynamic system
"""

# =============================================
# IMPORTS
# =============================================

from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.append(str(AIPASS_ROOT))

from prax.apps.modubles.logger import system_logger as logger

import subprocess
import shlex
import json
from typing import Dict, List, Optional, Any

# Import all drone modules at top (consolidated from scattered inline imports)
# Use relative imports since all modules are in apps/ directory
from drone_loader import get_command_tree, resolve_command
from drone_registry import load_registry, update_registry_on_change
from drone_discovery import (
    scan_module, format_scan_output,
    register_module, format_registration_output,
    activate_commands_interactive, format_activation_summary,
    list_activated_commands, format_list_output,
    edit_activated_command_interactive,
    list_all_systems, format_systems_output,
    remove_activated_command, format_remove_output,
    refresh_system, format_refresh_output,
    resolve_system_name,
    lookup_activated_command,
    show_help_for_target
)
from drone_compliance import upgrade_module

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "drone"
ECOSYSTEM_ROOT = Path.home()  # Scan from /home/aipass/ (not just aipass_core)
DRONE_ROOT = AIPASS_ROOT / "drone"

# =============================================
# HELPER FUNCTIONS
# =============================================


def _format_command(command_parts):
    """Return a shell-friendly representation of the command."""
    return " ".join(shlex.quote(str(part)) for part in command_parts)


def _log_command(command, cwd, internal=False):
    """Print a standardized log line showing the command being executed."""
    if isinstance(command, (list, tuple)):
        command_str = _format_command(command)
    else:
        command_str = str(command)

    prefix = "[DRONE] Internal" if internal else "[DRONE] Command"
    print(f"{prefix}: {command_str} (cwd={cwd})", flush=True)

def get_commands():
    """Get commands dynamically from loader"""
    return get_command_tree()

# =============================================
# MAIN FUNCTIONS
# =============================================

def get_command_info(command_name: str):
    """Get command info from dynamic loader"""
    return resolve_command(command_name)

def show_help():
    """Display help information for drone commands."""
    print("=" * 70)
    print("AIPass Drone - Command Executor")
    print("=" * 70)
    print("\nUsage: drone [command] [arguments]")

    print("\n" + "=" * 70)
    print("COMMANDS")
    print("=" * 70)

    print("\nDiscovery:")
    print("  drone scan @path            Scan module/directory for commands")
    print("  drone scan full @path       Scan with full command paths")
    print("  drone systems               List all registered systems")

    print("\nRegistration:")
    print("  drone reg @path             Register module and assign command IDs")
    print("  drone comply @path          Upgrade module to compliance (auto-refreshes)")
    print("  drone refresh <system>      Manual re-scan (rarely needed - upgrades auto-refresh)")

    print("\nActivation:")
    print("  drone activate <system>     Activate commands (interactive)")
    print("  drone list                  Show all activated commands")
    print("  drone remove <command>      Deactivate a specific command")

    print("\nQuick Help:")
    print("  drone <system_name>         Show help for system")
    print("  drone <module.py>           Show help for module")

    print("\nPlan Management:")
    print("  drone plan create [@location] [subject]")
    print("                              Create standard PLAN (single-phase work)")
    print("  drone plan create [@location] [subject] \"master\"")
    print("                              Create MASTER PLAN (3+ phases, complex)")
    print("  drone plan status           Show all active plans")
    print("  drone plan close <number>   Close plan (auto-processes to memory)")
    print("  drone plan summarize        Update CLAUDE.md with plan summaries")
    print("")
    print("  Standard Plan Examples:")
    print("    drone plan create @drone \"Fix email bug\"")
    print("    drone plan create \"Update documentation\"")
    print("")
    print("  Master Plan Examples (note the \"master\" parameter):")
    print("    drone plan create @standards \"Code Standards Update\" \"master\"")
    print("    drone plan create @flow \"System Migration\" \"master\"")
    print("")
    print("  When to use Master Plans:")
    print("    - 3+ distinct phases")
    print("    - Multi-day/session work")
    print("    - Agent deployment per phase")
    print("    - Complex refactoring")
    print("")
    print("  Close examples:")
    print("    drone plan close 0022")

    print("\n" + "=" * 70)
    print("PATH STANDARD")
    print("=" * 70)
    print("\n  @ symbol REQUIRED for all path operations")
    print("  Registered system names work without @")
    print("\nSupported @ formats:")
    print("  @flow              →  /home/aipass/flow")
    print("  @/flow/            →  /home/aipass/flow")
    print("  @/home/aipass/flow →  /home/aipass/flow")
    print("  @flow/flow_plan.py →  /home/aipass/flow/flow_plan.py")

    print("\nExamples:")
    print("  drone scan @backup_system")
    print("  drone reg @flow/apps/flow_plan.py")
    print("  drone activate flow           (name, not path)")
    print("  drone create plan @drone \"My task\"")

    print("\n" + "=" * 70)
    print("💡 TIP: Run 'drone systems' to see what's registered")
    print("=" * 70)

    # Show activated commands
    try:
        result = list_activated_commands()

        if result['success'] and result['commands']:
            print("\n" + "=" * 70)
            print(f"ACTIVATED COMMANDS ({len(result['commands'])} total)")
            print("=" * 70)

            # Group by system
            by_system = {}
            for cmd in result['commands']:
                system = cmd['system']
                if system not in by_system:
                    by_system[system] = []
                by_system[system].append(cmd)

            for system, cmds in sorted(by_system.items()):
                print(f"\n{system}:")
                for cmd in sorted(cmds, key=lambda x: x['drone_command']):
                    drone_cmd = cmd['drone_command']
                    desc = cmd['description'][:40] if cmd['description'] else '(no description)'
                    print(f"  drone {drone_cmd:<20} - {desc}")
        else:
            print("\n" + "=" * 70)
            print("ACTIVATED COMMANDS")
            print("=" * 70)
            print("\n💡 No commands activated yet")
            print("   Use 'drone activate <system>' to activate commands")

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error loading activated commands in help: {e}")
        print("\n⚠️ Note: Could not load activated commands")

    print("\n" + "=" * 70)
    print("For more info: /home/aipass/aipass_core/drone/README.md")
    print("=" * 70)

    return 0

# =============================================
# CLI/EXECUTION
# =============================================

def execute_command(cmd_path, args=None):
    """Execute a Python script with optional arguments."""
    try:
        command = ["python3", cmd_path]
        if args:
            command.extend(args)

        _log_command(command, ECOSYSTEM_ROOT)

        result = subprocess.run(
            command,
            cwd=ECOSYSTEM_ROOT,
            capture_output=False,
            text=True,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\nDrone: Command interrupted by user")
        return 130  # Standard exit code for Ctrl+C
    except FileNotFoundError:
        print(f"Error: Could not find file: {cmd_path}")
        return 1
    except Exception as e:
        print(f"Error executing command: {e}")
        return 1

def execute_command_in_dir(cmd_path, args=None, working_dir=None):
    """Execute a command with optional arguments in a specific directory."""
    try:
        # Handle direct commands like 'python3'
        if cmd_path in ['python3', 'python', 'node', 'npm']:
            command = [cmd_path]
        else:
            command = ["python3", cmd_path]

        if args:
            command.extend(args)

        cwd_to_use = working_dir or ECOSYSTEM_ROOT
        _log_command(command, cwd_to_use)

        result = subprocess.run(
            command,
            cwd=cwd_to_use,
            capture_output=False,
            text=True,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\nDrone: Command interrupted by user")
        return 130  # Standard exit code for Ctrl+C
    except FileNotFoundError:
        print(f"Error: Could not find file: {cmd_path}")
        return 1
    except Exception as e:
        print(f"Error executing command: {e}")
        return 1

def auto_heal_active_commands():
    """Auto-heal active.json files to ensure command_name is correct (not module:command)"""
    try:
        commands_dir = DRONE_ROOT / "commands"
        if not commands_dir.exists():
            return

        healed_count = 0
        for system_dir in commands_dir.iterdir():
            if not system_dir.is_dir():
                continue

            active_file = system_dir / "active.json"
            if not active_file.exists():
                continue

            # Load active commands
            try:
                with open(active_file, 'r', encoding='utf-8') as f:
                    active_data = json.load(f)
            except:
                continue

            # Check and fix command_name format
            needs_update = False
            for drone_cmd, cmd_data in active_data.items():
                command_name = cmd_data.get('command_name', '')
                # If command_name contains ':', extract the actual command
                if ':' in command_name:
                    actual_command = command_name.split(':', 1)[1]
                    cmd_data['command_name'] = actual_command
                    needs_update = True
                    healed_count += 1

            # Save if updated
            if needs_update:
                with open(active_file, 'w', encoding='utf-8') as f:
                    json.dump(active_data, f, indent=2, ensure_ascii=False)

        if healed_count > 0:
            logger.info(f"[{MODULE_NAME}] Auto-healed {healed_count} active command(s)")

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Auto-heal error: {e}")

def main():
    """Main entry point for drone command - now dynamic with reactive system."""
    try:
        logger.info(f"[{MODULE_NAME}] Drone started with args: {sys.argv[1:] if len(sys.argv) > 1 else 'help'}")

        # Auto-heal active commands on startup
        auto_heal_active_commands()

        # Check registry state first (reactive system)
        from pathlib import Path
        import os

        registry = load_registry()

        # Auto-detect file changes by checking modification times
        scan_locations = registry.get("scan_locations", [])
        source_files = registry.get("source_files", {})

        for location in scan_locations:
            location_path = Path(location)
            if location_path.exists():
                for json_file in location_path.glob("*.json"):
                    file_name = json_file.name
                    current_mtime = os.path.getmtime(json_file)

                    if file_name in source_files:
                        # Check if file was modified since last scan
                        from datetime import datetime, timezone
                        last_modified = source_files[file_name].get("last_modified")
                        if last_modified:
                            last_mtime = datetime.fromisoformat(last_modified.replace('Z', '+00:00')).timestamp()
                            # Use a small tolerance to avoid floating point comparison issues
                            if current_mtime > last_mtime + 0.001:  # 1ms tolerance
                                # File was modified - mark registry dirty
                                update_registry_on_change(str(json_file))
                    else:
                        # New file discovered
                        update_registry_on_change(str(json_file))

        # Reload registry after potential updates
        registry = load_registry()

        if registry.get("dirty", False):
            print("[DRONE] Configuration changes detected - updating commands...")
            # This will trigger a rebuild via get_command_tree
            get_command_tree()
            print("[DRONE] Commands updated. Please run your command again.")
            return 0

        if len(sys.argv) < 2:
            return show_help()

        command = sys.argv[1]

        # Handle help command
        if command == "help":
            return show_help()

        # Handle scan command (Phase 1: Auto-discovery)
        if command == "scan":
            # Check for "scan full" vs just "scan"
            show_full = False
            if len(sys.argv) >= 3 and sys.argv[2] == "full":
                show_full = True
                # Path is in sys.argv[3] for "drone scan full <path>"
                if len(sys.argv) < 4:
                    print("Error: 'drone scan full' requires a module path")
                    print("Usage: drone scan full <module_path>")
                    print("Example: drone scan full @backup_system")
                    print("Example: drone scan full /home/aipass/backup_system/backup_cli.py")
                    return 1
                module_path = sys.argv[3]
            else:
                # Regular scan - path is in sys.argv[2]
                if len(sys.argv) < 3:
                    print("Error: 'drone scan' requires a module path")
                    print("Usage: drone scan <module_path>")
                    print("       drone scan full <module_path>  (show full commands)")
                    print("Example: drone scan @backup_system")
                    print("Example: drone scan full @backup_system")
                    return 1
                module_path = sys.argv[2]


            logger.info(f"[{MODULE_NAME}] Scanning module: {module_path}")
            result = scan_module(module_path)
            output = format_scan_output(result, show_full_command=show_full)
            print(output)

            # Interactive upgrade prompt (only for directory scans with non-compliant modules)
            if result.get('is_directory'):
                modules_scanned = result.get('modules_scanned', [])
                cli_modules = [m for m in modules_scanned if not m['commands'] and m.get('module_type') == 'cli']

                if cli_modules:
                    print("\n" + "=" * 70)
                    print("💡 Interactive Upgrade Available")
                    print("=" * 70)
                    print("\nWould you like to upgrade non-compliant modules?")
                    print("")

                    # Number each module (supports 1-99)
                    for i, mod in enumerate(cli_modules, start=1):
                        print(f"  {i}. {mod['file']}")

                    print("")
                    print("Options:")
                    print("  - Enter numbers (comma-separated): 1,2,3")
                    print("  - Enter 'all' to upgrade all modules")
                    print("  - Enter 'n' to skip")
                    print("")

                    try:
                        selection = input("Select modules to upgrade: ").strip().lower()
                    except (KeyboardInterrupt, EOFError):
                        print("\n\nUpgrade cancelled.")
                        return 0 if result['success'] else 1

                    if selection == 'n' or selection == '':
                        print("Upgrade skipped.")
                        return 0 if result['success'] else 1

                    # Determine which modules to upgrade
                    modules_to_upgrade = []

                    if selection == 'all':
                        modules_to_upgrade = cli_modules
                    else:
                        # Parse number selection
                        selected_numbers = [s.strip() for s in selection.split(',')]
                        for num_str in selected_numbers:
                            try:
                                num = int(num_str)
                                if 1 <= num <= len(cli_modules):
                                    modules_to_upgrade.append(cli_modules[num - 1])  # Convert to 0-based index
                                else:
                                    print(f"Warning: Invalid selection '{num_str}' - must be 1-{len(cli_modules)}")
                            except ValueError:
                                print(f"Warning: Invalid selection '{num_str}' - must be a number")

                    if not modules_to_upgrade:
                        print("No valid modules selected.")
                        return 0 if result['success'] else 1

                    # Upgrade selected modules

                    print(f"\n🚀 Upgrading {len(modules_to_upgrade)} module(s)...\n")

                    success_count = 0
                    failed_count = 0

                    for mod in modules_to_upgrade:
                        print("=" * 70)
                        print(f"Upgrading: {mod['file']}")
                        print("=" * 70)

                        # Convert absolute path to @ format for upgrade_module
                        # /home/aipass/aipass_core/flow/apps/file.py → @flow/apps/file.py
                        abs_path = Path(mod['path'])
                        if str(abs_path).startswith('/home/aipass/aipass_core/'):
                            # Inside aipass_core - make relative to aipass_core
                            relative_path = abs_path.relative_to('/home/aipass/aipass_core')
                            at_path = f"@{relative_path}"
                        elif str(abs_path).startswith('/home/aipass/'):
                            # Outside aipass_core but in /home/aipass - full path needed
                            at_path = str(abs_path)
                        else:
                            # Fallback to absolute path
                            at_path = str(abs_path)

                        success = upgrade_module(at_path, auto_apply=False)

                        if success:
                            success_count += 1
                        else:
                            failed_count += 1

                        print("")

                    # Summary
                    print("=" * 70)
                    print("Upgrade Summary")
                    print("=" * 70)
                    print(f"✅ Successful: {success_count}")
                    print(f"❌ Failed: {failed_count}")
                    print(f"📊 Total: {len(modules_to_upgrade)}")
                    print("")

            # Interactive upgrade prompt for single file scans
            elif not result.get('is_directory'):
                # Check if this is a non-compliant CLI module
                is_cli = result.get('module_type') == 'cli'
                has_no_commands = not result.get('commands') or len(result.get('commands', [])) == 0

                if is_cli and has_no_commands:
                    print("\n" + "=" * 70)
                    print("💡 Upgrade Available")
                    print("=" * 70)
                    print("\nThis CLI module is missing compliance.")
                    print(f"Module: {Path(result['module_path']).name}")
                    print("")
                    print("Would you like to upgrade it now?")
                    print("")

                    try:
                        choice = input("Upgrade this module? (y/n): ").strip().lower()
                    except (KeyboardInterrupt, EOFError):
                        print("\n\nUpgrade cancelled.")
                        return 0 if result['success'] else 1

                    if choice == 'y':

                        print("\n🚀 Starting upgrade...\n")
                        print("=" * 70)
                        print(f"Upgrading: {Path(result['module_path']).name}")
                        print("=" * 70)

                        # Convert absolute path to @ format for upgrade_module
                        abs_path = Path(result['module_path'])
                        if str(abs_path).startswith('/home/aipass/'):
                            relative_path = abs_path.relative_to('/home/aipass')
                            at_path = f"@{relative_path}"
                        else:
                            at_path = f"@{abs_path}"

                        success = upgrade_module(at_path, auto_apply=False)

                        if success:
                            print("\n✅ Upgrade successful!")
                        else:
                            print("\n❌ Upgrade failed")
                    else:
                        print("Upgrade skipped.")

            return 0 if result['success'] else 1

        # Handle reg command (Phase 2: Registration)
        if command == "reg":
            if len(sys.argv) < 3:
                print("Error: 'drone reg' requires a module path")
                print("Usage: drone reg <module_path> [system_name]")
                print("Example: drone reg tests/test_modules/subparsers.py")
                print("Example: drone reg tests/test_modules/subparsers.py test_system")
                return 1

            module_path = sys.argv[2]
            system_name = sys.argv[3] if len(sys.argv) > 3 else None


            logger.info(f"[{MODULE_NAME}] Registering module: {module_path}")
            result = register_module(module_path, system_name)
            output = format_registration_output(result)
            print(output)

            return 0 if result['success'] else 1

        # Handle activate command (Phase 3: Interactive Activation)
        if command == "activate":
            if len(sys.argv) < 3:
                print("Error: 'drone activate' requires a system identifier")
                print("Usage: drone activate <system_name|path>")
                print("Example: drone activate flow_plan")
                print("Example: drone activate @flow")
                print("Example: drone activate /home/aipass/flow")
                return 1

            system_input = sys.argv[2]


            # Resolve system name from any input format
            system_name = resolve_system_name(system_input)

            logger.info(f"[{MODULE_NAME}] Activating commands for: {system_name}")
            result = activate_commands_interactive(system_name)

            # If no registry found, offer to register
            if not result['success'] and result.get('error') and "No registry found" in result['error']:
                print(format_activation_summary(system_name, result))
                print()
                print("💡 This system hasn't been registered yet")

                try:
                    choice = input("\nWould you like to register this system now? (y/n): ").strip().lower()
                except (KeyboardInterrupt, EOFError):
                    print("\n\nCancelled.")
                    return 1

                if choice == 'y':
                    print(f"\n🔧 Registering {system_name}...")

                    # === AIPASS FIX START ===
                    # Ensure path has @ symbol for register_module (it requires @ format)
                    registration_path = system_input if system_input.startswith('@') else f"@{system_input}"
                    # === AIPASS FIX END ===

                    # Register using the path with @ symbol
                    reg_result = register_module(registration_path, system_name)

                    if reg_result['success']:
                        print(f"✅ System registered - {reg_result.get('commands_count', 0)} commands found")
                        print()

                        # Ask if they want to activate now
                        try:
                            activate_choice = input("Would you like to activate commands now? (y/n): ").strip().lower()
                        except (KeyboardInterrupt, EOFError):
                            print("\n\nCancelled.")
                            return 0  # Registration succeeded, activation skipped

                        if activate_choice == 'y':
                            print()
                            # Go into interactive activation CLI (choose which commands)
                            result = activate_commands_interactive(system_name)
                            summary = format_activation_summary(system_name, result)
                            print(summary)
                            return 0 if result['success'] else 1
                        else:
                            print("\n💡 Activate later with: drone activate <system>")
                            return 0  # Registration succeeded
                    else:
                        print(f"❌ Registration failed: {reg_result.get('error', 'Unknown error')}")
                        return 1
                else:
                    print("\n💡 Register manually with: drone reg <path>")
                    return 1
            else:
                # Normal flow - show summary
                summary = format_activation_summary(system_name, result)
                print(summary)
                return 0 if result['success'] else 1

        # Handle list command (Phase 4: List activated commands)
        if command == "list":

            _log_command([sys.argv[0]] + sys.argv[1:], ECOSYSTEM_ROOT)
            logger.info(f"[{MODULE_NAME}] Listing activated commands")
            result = list_activated_commands()
            output = format_list_output(result)
            print(output)

            return 0 if result['success'] else 1

        # Handle edit command (Phase 8: Edit activated commands)
        if command == "edit":

            logger.info(f"[{MODULE_NAME}] Editing activated command")
            result = edit_activated_command_interactive()

            return 0 if result['success'] else 1

        # Handle systems command (Phase 4: List registered systems)
        if command == "systems":

            _log_command([sys.argv[0]] + sys.argv[1:], ECOSYSTEM_ROOT)
            logger.info(f"[{MODULE_NAME}] Listing registered systems")
            result = list_all_systems()
            output = format_systems_output(result)
            print(output)

            return 0 if result['success'] else 1

        # Handle remove command (Phase 6: Deactivate commands)
        if command == "remove":
            if len(sys.argv) < 3:
                print("Error: 'drone remove' requires a command name")
                print("Usage: drone remove <drone_command>")
                print("Example: drone remove snapshot")
                print("Example: drone remove backup-snap")
                print("Example: drone remove \"close plan\"")
                print("Note: This removes activated commands, not systems")
                return 1

            # Join all arguments to support multi-word commands (e.g., "close plan")
            drone_command = " ".join(sys.argv[2:])


            _log_command([sys.argv[0]] + sys.argv[1:], ECOSYSTEM_ROOT)
            logger.info(f"[{MODULE_NAME}] Removing command: {drone_command}")
            result = remove_activated_command(drone_command)
            output = format_remove_output(result)
            print(output)

            return 0 if result['success'] else 1

        # Handle refresh command (Phase 7: Re-scan for new commands)
        if command == "refresh":
            if len(sys.argv) < 3:
                print("Error: 'drone refresh' requires a system identifier")
                print("Usage: drone refresh <system_name|path>")
                print("Example: drone refresh backup_cli")
                print("Example: drone refresh @flow")
                print("Example: drone refresh /home/aipass/backup_system")
                return 1

            system_input = sys.argv[2]


            # Resolve system name from any input format
            system_name = resolve_system_name(system_input)

            _log_command([sys.argv[0]] + sys.argv[1:], ECOSYSTEM_ROOT)
            logger.info(f"[{MODULE_NAME}] Refreshing system: {system_name}")
            result = refresh_system(system_name)
            output = format_refresh_output(result)
            print(output)

            return 0 if result['success'] else 1

        # Handle comply command (AI-powered compliance upgrades)
        if command == "comply" or command == "upgrade":
            if len(sys.argv) < 3:
                print("Error: 'drone comply' requires a module path")
                print("Usage: drone comply <module_path>         (single module)")
                print("       drone comply <directory>           (batch mode - all non-compliant modules)")
                print("       drone comply <path> --auto         (auto-apply without prompts)")
                print("Example: drone comply @tools/aipass_rename_script.py")
                print("Example: drone comply @tools --auto")
                print("Example: drone comply /home/aipass/prax/prax_logger.py --auto")
                return 1

            module_path = sys.argv[2]
            auto_apply = '--auto' in sys.argv


            # Check if this is a directory (batch mode)
            logger.info(f"[{MODULE_NAME}] Checking path: {module_path}")
            scan_result = scan_module(module_path)

            if scan_result.get('is_directory'):
                # Batch mode - upgrade all non-compliant CLI modules
                modules_scanned = scan_result.get('modules_scanned', [])
                cli_modules = [m for m in modules_scanned if not m['commands'] and m.get('module_type') == 'cli']

                if not cli_modules:
                    print(f"✅ No non-compliant CLI modules found in {module_path}")
                    return 0

                print("=" * 70)
                print("🚀 Batch Mode: Upgrading Non-Compliant Modules")
                print("=" * 70)
                print(f"\nFound {len(cli_modules)} non-compliant module(s):\n")

                for i, mod in enumerate(cli_modules, 1):
                    print(f"  {i}. {mod['file']}")

                print(f"\nMode: {'Auto-apply (--auto)' if auto_apply else 'Interactive (confirmation required)'}")
                print("")

                if not auto_apply:
                    try:
                        confirm = input(f"Proceed with upgrading {len(cli_modules)} module(s)? (y/n): ").strip().lower()
                    except (KeyboardInterrupt, EOFError):
                        print("\n\nBatch upgrade cancelled.")
                        return 1

                    if confirm != 'y':
                        print("Batch upgrade cancelled.")
                        return 1

                # Upgrade each module
                success_count = 0
                failed_count = 0

                for mod in cli_modules:
                    print("\n" + "=" * 70)
                    print(f"Upgrading: {mod['file']}")
                    print("=" * 70)

                    logger.info(f"[{MODULE_NAME}] Batch upgrading: {mod['path']}")
                    success = upgrade_module(mod['path'], auto_apply=auto_apply)

                    if success:
                        success_count += 1
                    else:
                        failed_count += 1

                # Summary
                print("\n" + "=" * 70)
                print("Batch Upgrade Summary")
                print("=" * 70)
                print(f"✅ Successful: {success_count}")
                print(f"❌ Failed: {failed_count}")
                print(f"📊 Total: {len(cli_modules)}")
                print("")

                return 0 if failed_count == 0 else 1

            else:
                # Single module mode
                logger.info(f"[{MODULE_NAME}] Upgrading module to compliance: {module_path}")
                success = upgrade_module(module_path, auto_apply)

                return 0 if success else 1

        # Phase 5: Check for activated commands (auto-discovery execution)
        # Try multi-word drone commands first (e.g., "drone test create" = "test create")

        activated_cmd = None
        drone_command_str = None
        remaining_args = []

        # Try progressively longer combinations (up to 3 words)
        for word_count in range(min(4, len(sys.argv)), 1, -1):
            potential_drone_cmd = " ".join(sys.argv[1:word_count])
            activated_cmd = lookup_activated_command(potential_drone_cmd)
            if activated_cmd:
                drone_command_str = potential_drone_cmd
                remaining_args = sys.argv[word_count:]  # Everything after the drone command
                break

        if activated_cmd:
            # Found an activated command - execute it
            module_path = activated_cmd['module_path']
            command_name = activated_cmd['command_name']

            logger.info(f"[{MODULE_NAME}] Executing activated command: {drone_command_str} -> {command_name}")
            print(f"Drone: Executing '{drone_command_str}' ({command_name})...")

            # Resolve module path (handle relative paths from drone directory)
            module_path_obj = Path(module_path)
            if not module_path_obj.is_absolute():
                # Try relative to drone directory first
                drone_dir = Path(__file__).parent
                resolved = drone_dir / module_path
                if resolved.exists():
                    module_path = str(resolved)
                else:
                    # Try relative to ecosystem root
                    resolved = ECOSYSTEM_ROOT / module_path
                    if resolved.exists():
                        module_path = str(resolved)

            # Special handling for email commands - convert paths to @ format
            is_email_command = command_name == "send"

            if is_email_command and remaining_args:
                # First arg is recipient - convert to @format if it's a path
                recipient = remaining_args[0]

                if not recipient.startswith('@'):
                    # Convert path to @format
                    recipient_path = Path(recipient)

                    # Handle absolute paths
                    if recipient_path.is_absolute():
                        # /home/aipass/flow → @flow
                        # / → @admin
                        if str(recipient_path) == "/":
                            recipient = "@admin"
                        elif str(recipient_path).startswith('/home/aipass/'):
                            branch_name = recipient_path.relative_to('/home/aipass').parts[0]
                            recipient = f"@{branch_name}"
                        else:
                            # Unknown path format - keep as-is and let module handle error
                            pass
                    else:
                        # Relative path or bare name - convert to @
                        # admin → @admin
                        # flow → @flow
                        recipient = f"@{recipient}"

                    # Replace first arg with converted recipient
                    remaining_args = [recipient] + remaining_args[1:]

            # Resolve @ symbols in remaining_args to absolute paths (only if path exists)
            # Skip for email commands - they need @ format preserved
            resolved_args = []
            for i, arg in enumerate(remaining_args):
                if arg.startswith('@'):
                    # For email commands, first arg is recipient - preserve @ format
                    if is_email_command and i == 0:
                        resolved_args.append(arg)
                    else:
                        # Strip @ and check if it resolves to an actual path
                        location = arg[1:]
                        resolved_path = ECOSYSTEM_ROOT / location

                        # Only resolve if the path actually exists as a directory
                        # This preserves @ format for non-path uses (e.g., email addresses)
                        if resolved_path.exists() and resolved_path.is_dir():
                            resolved_args.append(str(resolved_path))
                        else:
                            # Path doesn't exist - preserve @ format for other uses
                            resolved_args.append(arg)
                else:
                    resolved_args.append(arg)

            # Build command: python3 module_path command_name [resolved_args]
            cmd_args = [command_name] + resolved_args
            return execute_command(module_path, cmd_args)

        # Try progressively longer command combinations (legacy dynamic loader)
        # This allows "drone create plan", "drone create plan test", etc.
        cmd_info = None
        actual_command = None
        args_start_index = 2

        # Try multi-word commands first (up to 3 words total)
        for word_count in range(min(4, len(sys.argv)), 0, -1):
            if word_count > 1:
                # Try multi-word combination with underscores
                potential_command = "_".join(sys.argv[1:word_count])
                cmd_info = get_command_info(potential_command)
                if cmd_info:
                    actual_command = potential_command
                    args_start_index = word_count
                    break

        # If no multi-word match found, try single word
        if not cmd_info:
            cmd_info = get_command_info(command)
            actual_command = command
            args_start_index = 2

        # Update sys.argv to properly separate command from args
        if cmd_info and args_start_index > 2:
            command = actual_command
            # Reconstruct sys.argv with the combined command
            sys.argv = [sys.argv[0], actual_command] + sys.argv[args_start_index:]

        if cmd_info:
            # Direct command found (e.g., 'backup', 'snapshot', 'cleanup')
            logger.info(f"[{MODULE_NAME}] Executing command: {command}")
            print(f"Drone: Executing {command}...")

            path = cmd_info.get("path", "")
            args = cmd_info.get("args", [])  # Use exact args from command definition
            cwd = cmd_info.get("cwd")

            if cwd:
                return execute_command_in_dir(path, args, cwd)
            else:
                return execute_command(path, args)
        else:
            # Before showing error, check if it's a system/module name requesting help

            # Strip @ symbol if present (command guaranteed non-None here)
            if command:
                help_target = command[1:] if command.startswith('@') else command

                if show_help_for_target(help_target):
                    # Successfully showed help for system/module
                    logger.info(f"[{MODULE_NAME}] Displayed help for: {command}")
                    return 0

            # Command not found
            logger.warning(f"[{MODULE_NAME}] Unknown command: {command}")
            print(f"Error: Unknown command '{command}'")
            print("Run 'drone help' to see available commands")
            return 1

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error resolving command '{command}': {e}")
        print(f"Error resolving command '{command}': {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
