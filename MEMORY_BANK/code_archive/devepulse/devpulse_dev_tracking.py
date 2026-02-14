#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: devpulse_dev_tracking.py
# Date: 2025-10-31
# Version: 2.0.0
# Description: Dev.local workflow automation - quick entry for issues, ideas, todos, notes
#
# CHANGELOG:
#   - v1.0.0 (2025-10-23): Initial implementation with section-based markdown updates
# =============================================

"""
Dev.local tracking system for AIPass branches.

Enables quick CLI entry to dev.local.md sections:
  • issue - Add to ## Issues section
  • enhancement - Add to ## Enhancements section
  • todo - Add to ## Quick Notes/Todos section
  • note - Add to ## Quick Notes section

Automatically syncs to PROJECT.dev.local.md after each update.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# =============================================
# PATH SETUP
# =============================================

AIPASS_ROOT = Path.home() / "aipass_core"
DEVEPULSE_ROOT = AIPASS_ROOT / "devepulse"
sys.path.append(str(AIPASS_ROOT))
APPS_ROOT = Path(__file__).resolve().parent
if str(APPS_ROOT) not in sys.path:
    sys.path.append(str(APPS_ROOT))

# Install Prax fallback before importing the logger
try:
    from prax_fallback_bootstrap import install_prax_fallback  # type: ignore
except ImportError:  # pragma: no cover - package mode
    from .prax_fallback_bootstrap import install_prax_fallback  # type: ignore

install_prax_fallback()

# Logger import
from prax.apps.modules.logger import system_logger as logger

# =============================================
# CONFIGURATION
# =============================================

# Module identity
MODULE_NAME = "devepulse_dev_tracking"

# System paths
ECOSYSTEM_ROOT = AIPASS_ROOT
DEVEPULSE_JSON_DIR = DEVEPULSE_ROOT / "devepulse_json"
TEMPLATE_FILE = Path("/home/aipass/aipass_core/templates/ai_branch_setup_template/dev.local.md")

# Auto-create JSON directory
DEVEPULSE_JSON_DIR.mkdir(exist_ok=True)

# 3-file JSON structure
CONFIG_FILE = DEVEPULSE_JSON_DIR / "dev_tracking_config.json"
DATA_FILE = DEVEPULSE_JSON_DIR / "dev_tracking_data.json"
LOG_FILE = DEVEPULSE_JSON_DIR / "dev_tracking_log.json"

# Default configuration
DEFAULT_CONFIG = {
    "sync_script": "/home/aipass/aipass_core/devepulse/sync-devepulse.sh",
    "template_file": "/home/AIPass_branch_setup_template/dev.local.md",
    "auto_sync": True,
    "auto_heal": True,
    "timestamp_format": "%Y-%m-%d %H:%M"
}

# =============================================
# JSON FILE MANAGEMENT
# =============================================

def load_config():
    """Load configuration from JSON file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Merge with defaults (in case new keys added)
            return {**DEFAULT_CONFIG, **config}
    else:
        # Create default config
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG

def load_data():
    """Load data from JSON file."""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Create default data structure
        default_data = {
            "recent_branches": [],
            "total_entries": 0,
            "entries_by_type": {
                "issue": 0,
                "enhancement": 0,
                "todo": 0,
                "note": 0
            }
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2)
        return default_data

def save_data(data):
    """Save data to JSON file."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# =============================================
# LOGGING
# =============================================

def log_operation(command, branch, section, entry, success, message=""):
    """Log operation to JSON log file."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "branch": str(branch),
        "section": section,
        "entry": entry,
        "success": success,
        "message": message
    }

    # Load existing log
    if LOG_FILE.exists():
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                log_data = {"operations": []}
    else:
        log_data = {"operations": []}

    # Append new entry
    log_data["operations"].append(log_entry)

    # Keep only last 100 entries
    log_data["operations"] = log_data["operations"][-100:]

    # Save log
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def resolve_branch(branch_arg):
    """
    Resolve @branch notation to absolute path.

    Examples:
        @flow → /home/aipass/flow
        @drone → /home/aipass/drone
        . → current working directory
    """
    if branch_arg == ".":
        return Path.cwd()

    if branch_arg.startswith("@"):
        branch_name = branch_arg[1:]  # Remove @
        branch_path = AIPASS_ROOT / branch_name
        if not branch_path.exists():
            raise ValueError(f"Branch not found: {branch_path}")
        return branch_path

    # Treat as absolute/relative path
    branch_path = Path(branch_arg)
    if not branch_path.exists():
        raise ValueError(f"Path not found: {branch_path}")
    return branch_path.resolve()

def find_dev_local_file(branch_path):
    """Find dev.local.md in branch directory."""
    dev_file = branch_path / "dev.local.md"
    if not dev_file.exists():
        raise FileNotFoundError(f"dev.local.md not found in {branch_path}")
    return dev_file

def format_entry(text, config):
    """Format entry with timestamp."""
    timestamp = datetime.now().strftime(config["timestamp_format"])
    return f"- [{timestamp}] {text}"

def find_section(content, section_name):
    """
    Find section in markdown content.

    Returns: (start_line, end_line) or None if not found

    Looks for:
    - ## Section
    - ## **Section**
    """
    lines = content.split('\n')
    start_line = None
    end_line = None

    # Find section header
    for i, line in enumerate(lines):
        # Match ## Section or ## **Section**
        if line.strip().startswith('##'):
            # Remove ##, **, and whitespace to get section name
            header_text = line.replace('#', '').replace('*', '').strip()
            if header_text.lower() == section_name.lower():
                start_line = i
                break

    if start_line is None:
        return None

    # Find end of section (next --- or end of file)
    for i in range(start_line + 1, len(lines)):
        if lines[i].strip() == '---':
            end_line = i
            break

    if end_line is None:
        end_line = len(lines)

    return (start_line, end_line)

def append_to_section(content, section_name, entry):
    """
    Append entry to section before the --- separator.

    Returns: updated content
    """
    section_bounds = find_section(content, section_name)
    if section_bounds is None:
        raise ValueError(f"Section '## {section_name}' not found in dev.local.md")

    start_line, end_line = section_bounds
    lines = content.split('\n')

    # Find insertion point (before ---, after last content)
    insert_line = end_line

    # If section only has placeholder "-", replace it
    has_only_placeholder = True
    for i in range(start_line + 1, end_line):
        line = lines[i].strip()
        if line and line != '-':
            has_only_placeholder = False
            break

    if has_only_placeholder:
        # Remove placeholder lines, insert new entry
        # Find first line after header
        insert_line = start_line + 1
        # Remove existing placeholder content
        while insert_line < end_line and lines[insert_line].strip() in ('', '-'):
            lines.pop(insert_line)
            end_line -= 1
        # Insert entry
        lines.insert(insert_line, entry)
    else:
        # Append to existing content (before ---)
        lines.insert(end_line, entry)

    return '\n'.join(lines)

def run_sync_script(config):
    """Run sync-dev-local.sh to update PROJECT.dev.local.md"""
    sync_script = config["sync_script"]

    if not os.path.exists(sync_script):
        return False, f"Sync script not found: {sync_script}"

    try:
        result = subprocess.run(
            [sync_script],
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        return True, "Sync completed successfully"
    except subprocess.TimeoutExpired:
        return False, "Sync script timeout (>30s)"
    except subprocess.CalledProcessError as e:
        return False, f"Sync script failed: {e.stderr}"
    except Exception as e:
        return False, f"Sync error: {str(e)}"

# =============================================
# DYNAMIC SECTION MANAGEMENT
# =============================================

def parse_template_sections():
    """
    Parse template file and extract section names.

    Returns: list[str] - Section names (e.g., ["Issues", "Upgrades", ...])
    """
    if not TEMPLATE_FILE.exists():
        logger.error(f"[{MODULE_NAME}] Template file not found: {TEMPLATE_FILE}")
        return []

    sections = []
    try:
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                # Look for ## Section headers (but skip metadata like ## Issues that are empty)
                if line.startswith("## ") and len(line.strip()) > 3:
                    # Extract section name
                    section_name = line.replace("##", "").strip()
                    # Skip empty or whitespace-only sections
                    if section_name:
                        sections.append(section_name)

        logger.info(f"[{MODULE_NAME}] Parsed {len(sections)} sections from template: {sections}")
        return sections
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to parse template: {e}")
        return []

# =============================================
# AUTO-HEALING SYSTEM
# =============================================

def check_template_compliance(dev_file_path):
    """
    Check if dev.local.md file complies with template structure.

    Returns: (is_compliant: bool, issues: list[str])
    """
    # Dynamic section extraction from template
    required_sections = parse_template_sections()
    if not required_sections:
        return False, ["Failed to parse template sections"]

    issues = []

    try:
        with open(dev_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, [f"Failed to read file: {e}"]

    lines = content.split('\n')

    # Check for metadata header (first 5 lines should have Branch/Created/etc)
    if len(lines) < 5:
        issues.append("Missing metadata header")
    else:
        if "Branch:" not in content[:200]:
            issues.append("Missing Branch metadata")
        if "Created:" not in content[:200]:
            issues.append("Missing Created metadata")

    # Check for ASCII art banner (should contain "888" or "Y88" or similar ASCII pattern)
    has_ascii = False
    for line in lines[:25]:
        if "888" in line or "Y88" in line:
            has_ascii = True
            break
    if not has_ascii:
        issues.append("Missing ASCII art banner")

    # Check for required sections
    for section in required_sections:
        found = False
        for line in lines:
            if line.strip().startswith('##'):
                header_text = line.replace('#', '').replace('*', '').strip()
                if header_text.lower() == section.lower():
                    found = True
                    break
        if not found:
            issues.append(f"Missing section: {section}")

    # Check for Purpose/Note lines (allow for bold formatting)
    if "Purpose:" not in content and "**Purpose:**" not in content:
        issues.append("Missing Purpose line")
    if ("Note: This file is NOT loaded into AI context" not in content and
        "**Note:** This file is NOT loaded into AI context" not in content):
        issues.append("Missing Note line")

    is_compliant = len(issues) == 0
    return is_compliant, issues

def heal_dev_local_file(dev_file_path, branch_path):
    """
    Heal non-compliant dev.local.md file by rebuilding from template.
    Preserves ALL user content from sections.

    Returns: (success: bool, message: str)
    """
    if not TEMPLATE_FILE.exists():
        return False, f"Template not found: {TEMPLATE_FILE}"

    # Read template
    try:
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            template = f.read()
    except Exception as e:
        return False, f"Failed to read template: {e}"

    # Read current file to extract user content
    try:
        with open(dev_file_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
    except Exception as e:
        return False, f"Failed to read current file: {e}"

    # Extract user content from current file - DYNAMIC SECTIONS
    sections = parse_template_sections()
    if not sections:
        return False, "Failed to parse template sections"

    user_content = {section: [] for section in sections}

    current_lines = current_content.split('\n')
    current_section = None

    for line in current_lines:
        # Detect section headers
        if line.strip().startswith('##'):
            header = line.replace('#', '').replace('*', '').strip()
            # Check if this header matches any template section (case-insensitive)
            for section in sections:
                if header.lower() == section.lower():
                    current_section = section
                    break
            else:
                current_section = None  # Unknown section - not in template
        # Collect content from known sections
        elif current_section and line.strip() and line.strip() != '-' and not line.strip() == '---':
            user_content[current_section].append(line)

    # Replace template placeholders
    branch_name = branch_path.name
    healed = template.replace("{{FOLDERNAME}}", branch_name)
    healed = healed.replace("{{CWD}}", str(branch_path))
    healed = healed.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
    healed = healed.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Insert user content into template sections
    healed_lines = healed.split('\n')
    result_lines = []
    current_section = None
    section_content_inserted = set()

    for i, line in enumerate(healed_lines):
        # Detect section headers in template
        if line.strip().startswith('##'):
            header = line.replace('#', '').replace('*', '').strip()
            if header in user_content:
                current_section = header
                section_content_inserted.add(header)
                result_lines.append(line)
                # Skip the placeholder "-" in next lines and insert user content
                j = i + 1
                while j < len(healed_lines) and healed_lines[j].strip() in ('', '-'):
                    j += 1
                # Insert user content
                if user_content[header]:
                    result_lines.append("")
                    result_lines.extend(user_content[header])
                else:
                    result_lines.append("")
                    result_lines.append("-")
                # Skip to separator
                continue
            else:
                current_section = None
                result_lines.append(line)
        # Skip placeholder content in template if we're in a section we're replacing
        elif current_section and line.strip() in ('', '-'):
            continue
        # Keep separator lines and other content
        else:
            if current_section and line.strip() == '---':
                current_section = None
            result_lines.append(line)

    healed_content = '\n'.join(result_lines)

    # Write healed file
    try:
        with open(dev_file_path, 'w', encoding='utf-8') as f:
            f.write(healed_content)
    except Exception as e:
        return False, f"Failed to write healed file: {e}"

    return True, "File healed successfully"

def auto_heal_if_needed(dev_file_path, branch_path):
    """
    Auto-heal dev.local file if non-compliant.
    Runs before add operations.

    Returns: None (logs and reports as needed)
    """
    is_compliant, issues = check_template_compliance(dev_file_path)

    if is_compliant:
        # Silent - no need to report compliance
        logger.info(f"[{MODULE_NAME}] Template compliance check: {dev_file_path.name} is compliant")
        return

    # Non-compliant - heal it
    logger.warning(f"[{MODULE_NAME}] Template compliance issues found in {dev_file_path.name}: {len(issues)} issue(s)")
    for issue in issues:
        logger.warning(f"[{MODULE_NAME}]   - {issue}")

    print(f"⚠️  Template compliance issues detected: {len(issues)} issue(s)")
    print(f"🔧 Auto-healing {branch_path.name}/dev.local.md...")

    success, message = heal_dev_local_file(dev_file_path, branch_path)

    if success:
        logger.info(f"[{MODULE_NAME}] Auto-heal successful: {dev_file_path.name}")
        print(f"✅ {message}")
    else:
        logger.error(f"[{MODULE_NAME}] Auto-heal failed: {message}")
        print(f"❌ Auto-heal failed: {message}")

# =============================================
# COMMAND HANDLERS
# =============================================

def add_entry(section_name: str, branch_arg: str, entry_text: str | None = None):
    """
    Add entry to dev.local.md section.

    Args:
        section_name: Section name from template (e.g., "Issues", "Upgrades")
        branch_arg: @flow, @drone, or path
        entry_text: text to add (prompts if None)
    """
    logger.info(f"[{MODULE_NAME}] Adding entry to {section_name} section in {branch_arg}")
    config = load_config()
    data = load_data()

    # Resolve branch path
    try:
        branch_path = resolve_branch(branch_arg)
    except ValueError as e:
        logger.error(f"[{MODULE_NAME}] Failed to resolve branch {branch_arg}: {e}")
        print(f"❌ Error: {e}")
        return False

    # Find dev.local.md
    try:
        dev_file = find_dev_local_file(branch_path)
    except FileNotFoundError as e:
        logger.error(f"[{MODULE_NAME}] dev.local.md not found in {branch_path}: {e}")
        print(f"❌ Error: {e}")
        return False

    # AUTO-HEAL: Check template compliance before adding entry
    auto_heal_if_needed(dev_file, branch_path)

    # Validate section exists in template
    valid_sections = parse_template_sections()
    if not valid_sections:
        logger.error(f"[{MODULE_NAME}] Failed to parse template sections")
        print("❌ Error: Failed to parse template sections")
        return False

    # Case-insensitive section matching
    section_match = None
    for section in valid_sections:
        if section.lower() == section_name.lower():
            section_match = section
            break

    if not section_match:
        logger.error(f"[{MODULE_NAME}] Unknown section: {section_name}")
        print(f"❌ Error: Unknown section '{section_name}'")
        print(f"💡 Available sections: {', '.join(valid_sections)}")
        return False

    section_name = section_match  # Use exact case from template

    # Prompt for entry if not provided
    if entry_text is None:
        try:
            entry_text = input(f"Enter text for {section_name}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n↩️  Aborted.")
            return False

    if not entry_text:
        print("❌ Error: Entry text cannot be empty")
        return False

    # Read dev.local.md
    with open(dev_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Format entry with timestamp
    formatted_entry = format_entry(entry_text, config)

    # Append to section
    try:
        updated_content = append_to_section(content, section_name, formatted_entry)
    except ValueError as e:
        logger.error(f"[{MODULE_NAME}] Failed to append to section {section_name}: {e}")
        print(f"❌ Error: {e}")
        log_operation(section_name, branch_path, section_name, entry_text, False, str(e))
        return False

    # Write updated content
    with open(dev_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    logger.info(f"[{MODULE_NAME}] Successfully added entry to {section_name} in {branch_path.name}/dev.local.md")
    print(f"✅ Entry added to {section_name} in {branch_path.name}/dev.local.md")

    # Update data tracking
    data["total_entries"] += 1
    data["entries_by_section"] = data.get("entries_by_section", {})
    data["entries_by_section"][section_name] = data["entries_by_section"].get(section_name, 0) + 1
    if str(branch_path) not in data["recent_branches"]:
        data["recent_branches"].append(str(branch_path))
        data["recent_branches"] = data["recent_branches"][-10:]  # Keep last 10
    save_data(data)

    # Run sync script if enabled
    if config["auto_sync"]:
        print("🔄 Running sync script...")
        sync_success, sync_message = run_sync_script(config)
        if sync_success:
            print(f"✅ {sync_message}")
        else:
            print(f"⚠️  {sync_message}")

    # Log operation
    log_operation(section_name, branch_path, section_name, entry_text, True)

    return True

def show_log(limit: int = 10):
    """Show recent operations from log."""
    if not LOG_FILE.exists():
        print("No operations logged yet.")
        return

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        try:
            log_data = json.load(f)
        except json.JSONDecodeError:
            print("❌ Error: Log file corrupted")
            return

    operations = log_data.get("operations", [])
    if not operations:
        print("No operations logged yet.")
        return

    print(f"\n=== Recent Operations (last {limit}) ===\n")

    for op in operations[-limit:]:
        timestamp = op["timestamp"]
        command = op["command"]
        branch = Path(op["branch"]).name
        entry = op["entry"][:50] + "..." if len(op["entry"]) > 50 else op["entry"]
        status = "✅" if op["success"] else "❌"

        print(f"{status} [{timestamp}] {command} @{branch}")
        print(f"   {entry}")
        if not op["success"]:
            print(f"   Error: {op.get('message', 'Unknown error')}")
        print()

def cmd_heal(branch_arg: str | None = None):
    """Heal dev.local.md template compliance (single branch or all)."""
    if branch_arg is None or branch_arg == "all":
        # Heal all branches
        print("🔍 Scanning for all dev.local.md files...")

        dev_files = list(AIPASS_ROOT.glob("**/dev.local.md"))
        dev_files = [f for f in dev_files if "/.local/" not in str(f) and "/archive/" not in str(f) and "/backups/" not in str(f) and f.name != "PROJECT.dev.local.md"]

        print(f"📋 Found {len(dev_files)} branch(es)")

        healed_count = 0
        already_compliant = 0

        for dev_file in dev_files:
            branch_path = dev_file.parent
            is_compliant, issues = check_template_compliance(dev_file)

            if is_compliant:
                already_compliant += 1
                continue

            print(f"\n🔧 Healing {branch_path.name}/dev.local.md ({len(issues)} issue(s))...")
            success, message = heal_dev_local_file(dev_file, branch_path)

            if success:
                healed_count += 1
                print(f"   ✅ {message}")
            else:
                print(f"   ❌ {message}")

        print(f"\n📊 Summary: {healed_count} healed, {already_compliant} already compliant")
        return True
    else:
        # Heal single branch
        try:
            branch_path = resolve_branch(branch_arg)
            dev_file = find_dev_local_file(branch_path)
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Error: {e}")
            return False

        is_compliant, issues = check_template_compliance(dev_file)

        if is_compliant:
            print(f"✅ {branch_path.name}/dev.local.md is already compliant")
            return True

        print(f"⚠️  Found {len(issues)} compliance issue(s):")
        for issue in issues:
            print(f"   - {issue}")

        print(f"\n🔧 Healing {branch_path.name}/dev.local.md...")
        success, message = heal_dev_local_file(dev_file, branch_path)

        if success:
            print(f"✅ {message}")
            return True
        else:
            print(f"❌ {message}")
            return False

def cmd_status(branch_arg: str | None = None):
    """Show template compliance status (single branch or all)."""
    if branch_arg is None or branch_arg == "all":
        # Status for all branches
        print("🔍 Checking all dev.local.md files...\n")

        dev_files = list(AIPASS_ROOT.glob("**/dev.local.md"))
        dev_files = [f for f in dev_files if "/.local/" not in str(f) and "/archive/" not in str(f) and "/backups/" not in str(f) and f.name != "PROJECT.dev.local.md"]

        compliant_count = 0
        non_compliant = []

        for dev_file in dev_files:
            branch_path = dev_file.parent
            is_compliant, issues = check_template_compliance(dev_file)

            if is_compliant:
                compliant_count += 1
                print(f"✅ {branch_path.name:20} - Compliant")
            else:
                non_compliant.append((branch_path.name, len(issues)))
                print(f"⚠️  {branch_path.name:20} - {len(issues)} issue(s)")

        print(f"\n📊 Summary: {compliant_count} compliant, {len(non_compliant)} need healing")

        if non_compliant:
            print(f"\n💡 Run 'drone dev heal all' to fix all issues")

        return True
    else:
        # Status for single branch
        try:
            branch_path = resolve_branch(branch_arg)
            dev_file = find_dev_local_file(branch_path)
        except (ValueError, FileNotFoundError) as e:
            print(f"❌ Error: {e}")
            return False

        is_compliant, issues = check_template_compliance(dev_file)

        print(f"\n{'='*60}")
        print(f"Branch: {branch_path.name}")
        print(f"File: {dev_file.relative_to(AIPASS_ROOT)}")
        print(f"{'='*60}\n")

        if is_compliant:
            print("✅ Status: COMPLIANT")
            print("\nAll template requirements met.")
        else:
            print(f"⚠️  Status: NON-COMPLIANT ({len(issues)} issue(s))")
            print("\nIssues found:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            print(f"\n💡 Run 'drone dev heal @{branch_path.name}' to fix")

        return True

def cmd_sync():
    """Run sync-dev-local.sh to update PROJECT.dev.local.md."""
    config = load_config()
    print("🔄 Running sync script...")
    success, message = run_sync_script(config)

    if success:
        print(f"✅ {message}")
        return True
    else:
        print(f"❌ {message}")
        return False

def cmd_update():
    """Full update: heal all + sync."""
    print("🔧 Full dev.local update starting...\n")
    print("Step 1: Healing all branches...")
    cmd_heal("all")
    print("\nStep 2: Syncing to PROJECT.dev.local.md...")
    cmd_sync()
    print("\n✅ Full update complete!")
    return True

# =============================================
# CLI SETUP
# =============================================

def main():
    # Get available sections from template for help text
    sections = parse_template_sections()
    sections_list = ', '.join(f'"{s}"' for s in sections) if sections else "Issues, Upgrades, Testing Notes, Quick Notes/Todos"

    parser = argparse.ArgumentParser(
        description='Flow Dev Tracking - Template-driven dev.local.md management + auto-healing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
COMMANDS:
  Commands: add, heal, status, sync, update, log

ADD COMMAND:
  drone dev add @branch "Section" "text"

  Available sections (from template):
    {sections_list}

  Section names are case-insensitive. Add/remove/rename sections in template
  at /home/AIPass_branch_setup_template/dev.local.md and system adapts automatically.

SYSTEM COMMANDS:
  heal [@branch|all]   - Check/heal template compliance (auto-heal before entries)
  status [@branch|all] - Show compliance status
  sync                 - Run sync-dev-local.sh (update PROJECT.dev.local.md)
  update               - Full update: heal all + sync
  log                  - Show recent operations

EXAMPLES:
  # Add entries (auto-heals if needed)
  drone dev add @flow "Issues" "Registry not syncing"
  drone dev add @drone "Upgrades" "Add progress bars"
  drone dev add @speakeasy "Testing Notes" "Voice system validated"
  drone dev add @flow "Quick Notes/Todos" "Update documentation"

  # Auto-healing
  drone dev heal @speakeasy    # Heal one branch
  drone dev heal all           # Heal all branches
  drone dev status all         # Check all statuses

  # Sync and update
  drone dev sync               # Update PROJECT overview
  drone dev update             # Heal all + sync

BRANCH NOTATION:
  @flow   - /home/aipass/flow
  @drone  - /home/aipass/drone
  .       - Current working directory
  /path   - Absolute path to branch
  all     - All branches (for heal/status commands)

TEMPLATE-DRIVEN:
  Single source of truth: /home/AIPass_branch_setup_template/dev.local.md
  Add a new section to template → immediately available via 'add' command
  Remove a section from template → system stops using it
  Rename a section in template → system uses new name
        """
    )

    parser.add_argument('command',
                       choices=['add', 'heal', 'status', 'sync', 'update', 'log'],
                       help='Command to execute')

    parser.add_argument('branch',
                       nargs='?',
                       help='Branch location (@flow, @drone, ., all, or path)')

    parser.add_argument('section',
                       nargs='?',
                       help='Section name (for add command)')

    parser.add_argument('text',
                       nargs='?',
                       help='Entry text (for add command, optional - will prompt if not provided)')

    args = parser.parse_args()

    # Handle system commands (no branch required or optional)
    if args.command == 'log':
        show_log()
        sys.exit(0)

    if args.command == 'sync':
        success = cmd_sync()
        sys.exit(0 if success else 1)

    if args.command == 'update':
        success = cmd_update()
        sys.exit(0 if success else 1)

    if args.command == 'heal':
        success = cmd_heal(args.branch)
        sys.exit(0 if success else 1)

    if args.command == 'status':
        success = cmd_status(args.branch)
        sys.exit(0 if success else 1)

    # Add command requires branch and section
    if args.command == 'add':
        if not args.branch:
            print("❌ Error: branch argument required for add command")
            print(f"Example: drone dev add @flow \"Issues\" \"Issue text\"")
            sys.exit(1)

        if not args.section:
            print("❌ Error: section argument required for add command")
            print(f"Available sections: {sections_list}")
            print(f"Example: drone dev add @flow \"Issues\" \"Issue text\"")
            sys.exit(1)

        # Execute add command
        success = add_entry(args.section, args.branch, args.text)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
