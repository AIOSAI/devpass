#!/usr/bin/env python3

# ===================AIPASS====================
# META DATA HEADER
# Name: branch_clean.py - AIPass Branch Clean Script
# Date: 2025-10-29
# Version: 1.0.0
# Category: branch_operations
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-10-29): Initial standardized version - Added META header
# =============================================

"""
AIPass Branch Clean Script
Wipes all memory data from branch while preserving directory structure

Usage:
    python3 branch_clean.py /path/to/branch
    python3 branch_clean.py /path/to/branch --force

Safety Features:
    - User confirmation required (type exact branch name)
    - Timestamped backups in .backup/ directory
    - Preserves PROJECT.json and ID.json
    - Preserves all directory structure
    - Reports what will be cleaned before execution
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))

# Standard library imports
import argparse
import json
from datetime import datetime
from typing import Dict, Optional

# AIPass infrastructure imports
from prax.apps.prax_logger import system_logger as logger

# Import from branch_lib
from branch_lib import get_branch_name


# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

# Module root and JSON directory
MODULE_ROOT = Path(__file__).parent.parent
JSON_DIR = MODULE_ROOT / "branch_operations_json"

# Auto-create JSON directory
JSON_DIR.mkdir(exist_ok=True)

# 3-file JSON structure for branch_clean module
CONFIG_FILE = JSON_DIR / "branch_clean_config.json"
DATA_FILE = JSON_DIR / "branch_clean_data.json"
LOG_FILE = JSON_DIR / "branch_clean_log.json"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log_operation(operation: str, success: bool, details: str = "", error: str = ""):
    """
    Log branch_clean operations to module-specific log file

    Args:
        operation: Operation name (e.g., "branch_clean_start")
        success: Whether operation succeeded
        details: Additional details about the operation
        error: Error message if operation failed
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
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
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_clean] Error saving log: {e}")


def load_config() -> Dict:
    """
    Load branch_clean configuration

    Returns:
        Config dict with module settings
    """
    default_config = {
        "enabled": True,
        "version": "1.0.0",
        "auto_backup": True,
        "require_confirmation": True,
        "max_log_entries": 1000
    }

    if not CONFIG_FILE.exists():
        save_config(default_config)
        return default_config

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[branch_clean] Error loading config: {e}")
        return default_config


def save_config(config: Dict):
    """Save branch_clean configuration"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_clean] Error saving config: {e}")


def load_data() -> Dict:
    """
    Load branch_clean runtime data

    Returns:
        Data dict with operation statistics
    """
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[branch_clean] Error loading data: {e}")

    default_data = {
        "created": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "operations_total": 0,
        "operations_successful": 0,
        "operations_failed": 0,
        "files_cleaned": 0
    }
    return default_data


def save_data(data: Dict):
    """Save branch_clean runtime data with auto timestamp"""
    try:
        data["last_updated"] = datetime.now().isoformat()
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_clean] Error saving data: {e}")


# =============================================================================
# TEMPLATE LOADING
# =============================================================================

def get_template_path() -> Path:
    """
    Get path to template directory - single point of change for path migration

    Returns:
        Path to ai_branch_setup_template directory

    Note:
        Uses AIPASS_ROOT for dynamic path resolution.
        Template location: AIPASS_ROOT / "templates" / "ai_branch_setup_template"
    """
    return AIPASS_ROOT / "templates" / "ai_branch_setup_template"


def load_template(filename: str) -> Optional[Dict]:
    """
    Load template JSON file

    Args:
        filename: Template filename (e.g., "LOCAL..json")

    Returns:
        Template dict or None if failed
    """
    template_path = get_template_path() / filename

    if not template_path.exists():
        print(f"ERROR: Template not found: {template_path}")
        return None

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load template {filename}: {e}")
        return None


# =============================================================================
# MEMORY FILE ANALYSIS
# =============================================================================

def analyze_memory_file(file_path: Path, file_type: str) -> Dict[str, int | bool]:
    """
    Analyze memory file to report what will be deleted

    Args:
        file_path: Path to memory file
        file_type: Type of file (local, observations, ai_mail)

    Returns:
        Dict with counts of items to be deleted (int) and status flags (bool)
    """
    if not file_path.exists():
        return {"exists": False}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return {"exists": True, "error": True}

    counts: Dict[str, int | bool] = {"exists": True, "error": False}

    if file_type == "local":
        sessions = data.get("sessions", [])
        counts["sessions"] = len(sessions)
        counts["active_tasks"] = len(data.get("active_tasks", {}).get("today_focus", []))

    elif file_type == "observations":
        observations = data.get("observations", [])
        # Count total entries across all date groups
        total_entries = 0
        for obs_group in observations:
            if isinstance(obs_group, dict):
                entries = obs_group.get("entries", [])
                total_entries += len(entries)
        counts["observations"] = total_entries

    elif file_type == "ai_mail":
        summary = data.get("summary", {})
        counts["inbox_messages"] = summary.get("inbox", {}).get("total", 0)
        counts["sent_messages"] = summary.get("sent", {}).get("total", 0)

    return counts


# =============================================================================
# BACKUP OPERATIONS
# =============================================================================

def create_backup(file_path: Path, backup_dir: Path, timestamp: str) -> Optional[Path]:
    """
    Create timestamped backup of file

    Args:
        file_path: Path to file to backup
        backup_dir: Directory for backups
        timestamp: Timestamp string for backup filename

    Returns:
        Path to backup file or None if failed
    """
    if not file_path.exists():
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{file_path.name}.{timestamp}.backup"

    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"ERROR: Failed to backup {file_path.name}: {e}")
        return None


# =============================================================================
# CLEAN OPERATIONS
# =============================================================================

def clean_local_file(local_file: Path, template_file: Path, backup_dir: Path, timestamp: str) -> bool:
    """
    Clean local.json file - reset sessions and active tasks

    Args:
        local_file: Path to BRANCHNAME.local.json
        template_file: Path to template LOCAL..json
        backup_dir: Directory for backups
        timestamp: Timestamp string

    Returns:
        True if successful, False otherwise
    """
    # Create backup first
    if local_file.exists():
        backup_path = create_backup(local_file, backup_dir, timestamp)
        if not backup_path:
            print("  ERROR: Backup failed - aborting clean")
            return False

    # Load template
    template = load_template(template_file.name)
    if not template:
        return False

    # If file doesn't exist, create from template
    if not local_file.exists():
        try:
            with open(local_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"  ERROR: Failed to create {local_file.name}: {e}")
            return False

    # Load existing file
    try:
        with open(local_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ERROR: Failed to load {local_file.name}: {e}")
        return False

    # Reset sessions array to empty
    data["sessions"] = []

    # Reset active_tasks
    if "active_tasks" in data:
        data["active_tasks"]["today_focus"] = []
        data["active_tasks"]["recently_completed"] = []

    # Update metadata if it exists
    if "metadata" in data:
        if "memory_health" in data["metadata"]:
            data["metadata"]["memory_health"]["current_lines"] = 0
            data["metadata"]["memory_health"]["status"] = "healthy"

    # Save cleaned file
    try:
        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"  ERROR: Failed to save {local_file.name}: {e}")
        return False


def clean_observations_file(obs_file: Path, template_file: Path, backup_dir: Path, timestamp: str) -> bool:
    """
    Clean observations.json file - reset observations array

    Args:
        obs_file: Path to BRANCHNAME.observations.json
        template_file: Path to template OBSERVATIONS.json
        backup_dir: Directory for backups
        timestamp: Timestamp string

    Returns:
        True if successful, False otherwise
    """
    # Create backup first
    if obs_file.exists():
        backup_path = create_backup(obs_file, backup_dir, timestamp)
        if not backup_path:
            print("  ERROR: Backup failed - aborting clean")
            return False

    # Load template
    template = load_template(template_file.name)
    if not template:
        return False

    # If file doesn't exist, create from template
    if not obs_file.exists():
        try:
            with open(obs_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"  ERROR: Failed to create {obs_file.name}: {e}")
            return False

    # Load existing file
    try:
        with open(obs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ERROR: Failed to load {obs_file.name}: {e}")
        return False

    # Reset observations array to empty
    data["observations"] = []

    # Update metadata if it exists
    if "metadata" in data:
        if "memory_health" in data["metadata"]:
            data["metadata"]["memory_health"]["current_lines"] = 0
            data["metadata"]["memory_health"]["status"] = "healthy"

    # Save cleaned file
    try:
        with open(obs_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"  ERROR: Failed to save {obs_file.name}: {e}")
        return False


def clean_ai_mail_file(mail_file: Path, template_file: Path, backup_dir: Path, timestamp: str) -> bool:
    """
    Clean ai_mail.json file - reset inbox/sent counts and previews

    Args:
        mail_file: Path to BRANCHNAME.ai_mail.json
        template_file: Path to template AI_MAIL.json
        backup_dir: Directory for backups
        timestamp: Timestamp string

    Returns:
        True if successful, False otherwise
    """
    # Create backup first
    if mail_file.exists():
        backup_path = create_backup(mail_file, backup_dir, timestamp)
        if not backup_path:
            print("  ERROR: Backup failed - aborting clean")
            return False

    # Load template
    template = load_template(template_file.name)
    if not template:
        return False

    # If file doesn't exist, create from template
    if not mail_file.exists():
        try:
            with open(mail_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"  ERROR: Failed to create {mail_file.name}: {e}")
            return False

    # Load existing file
    try:
        with open(mail_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ERROR: Failed to load {mail_file.name}: {e}")
        return False

    # Reset summary counts
    if "summary" in data:
        if "inbox" in data["summary"]:
            data["summary"]["inbox"]["total"] = 0
            data["summary"]["inbox"]["unread"] = 0
            data["summary"]["inbox"]["recent_preview"] = []

        if "sent" in data["summary"]:
            data["summary"]["sent"]["total"] = 0
            data["summary"]["sent"]["recent_preview"] = []

        if "deleted" in data["summary"]:
            data["summary"]["deleted"]["total"] = 0

    # Save cleaned file
    try:
        with open(mail_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"  ERROR: Failed to save {mail_file.name}: {e}")
        return False


# =============================================================================
# USER CONFIRMATION
# =============================================================================

def get_user_confirmation(branch_name: str, analysis: Dict[str, Dict]) -> bool:
    """
    Get user confirmation before cleaning

    Args:
        branch_name: Branch name to confirm
        analysis: Dict with analysis of what will be deleted

    Returns:
        True if user confirms, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"WARNING: This will wipe all memory data from branch: {branch_name}")
    print(f"{'='*70}")
    print()
    print("The following will be reset to defaults:")
    print()

    # Report local file
    local_info = analysis.get("local", {})
    if local_info.get("exists"):
        if local_info.get("error"):
            print(f"  - Sessions history (file corrupted - will be reset)")
        else:
            sessions = local_info.get("sessions", 0)
            tasks = local_info.get("active_tasks", 0)
            print(f"  - Sessions history ({sessions} sessions will be deleted)")
            if tasks > 0:
                print(f"  - Active tasks ({tasks} tasks will be cleared)")

    # Report observations file
    obs_info = analysis.get("observations", {})
    if obs_info.get("exists"):
        if obs_info.get("error"):
            print(f"  - Observations (file corrupted - will be reset)")
        else:
            obs_count = obs_info.get("observations", 0)
            print(f"  - Observations ({obs_count} entries will be deleted)")

    # Report ai_mail file
    mail_info = analysis.get("ai_mail", {})
    if mail_info.get("exists"):
        if mail_info.get("error"):
            print(f"  - AI_Mail inbox (file corrupted - will be reset)")
        else:
            inbox = mail_info.get("inbox_messages", 0)
            sent = mail_info.get("sent_messages", 0)
            if inbox > 0 or sent > 0:
                print(f"  - AI_Mail inbox ({inbox} messages will be cleared)")
                print(f"  - AI_Mail sent ({sent} messages will be cleared)")

    print()
    print("What will be preserved:")
    print(f"  - All metadata and identity information")
    print(f"  - All directory structure (apps/, tests/, etc)")
    print(f"  - All configuration files (PROJECT.json, ID.json)")
    print()

    # Show backup location
    backup_dir = Path(f".backup")
    print(f"Backups will be created in: {backup_dir.absolute()}")
    print()

    # Require exact branch name match
    print(f"Type the exact branch name to confirm: ", end='', flush=True)
    user_input = input().strip()

    if user_input == branch_name:
        return True
    else:
        print()
        print(f"Confirmation failed. Expected '{branch_name}', got '{user_input}'")
        return False


# =============================================================================
# MAIN CLEAN PROCESS
# =============================================================================

def clean_branch(target_path: Path, force: bool = False) -> bool:
    """
    Clean branch memories while preserving structure

    Args:
        target_path: Path to branch directory
        force: If True, skip user confirmation

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Branch clean initiated for: {target_path} (force={force})")

    # Log operation start
    log_operation(
        operation="branch_clean_start",
        success=True,
        details=f"Initiating branch clean for: {target_path} (force={force})"
    )

    # Validate path exists
    if not target_path.exists():
        logger.error(f"Target path does not exist: {target_path}")
        print(f"❌ ERROR: Path does not exist: {target_path}")
        return False

    if not target_path.is_dir():
        logger.error(f"Target path is not a directory: {target_path}")
        print(f"❌ ERROR: Path is not a directory: {target_path}")
        return False

    # Get branch name
    branch_name = get_branch_name(target_path)
    branchname_upper = branch_name.upper().replace("-", "_")

    print(f"Branch Clean Tool")
    print(f"Target: {target_path}")
    print(f"Branch: {branchname_upper}")
    print()

    # Define file paths
    local_file = target_path / f"{branchname_upper}.local.json"
    obs_file = target_path / f"{branchname_upper}.observations.json"
    mail_file = target_path / f"{branchname_upper}.ai_mail.json"

    # Analyze what will be deleted
    print("Analyzing memory files...")
    analysis = {
        "local": analyze_memory_file(local_file, "local"),
        "observations": analyze_memory_file(obs_file, "observations"),
        "ai_mail": analyze_memory_file(mail_file, "ai_mail")
    }

    # Check if any files exist
    if not any(info.get("exists") for info in analysis.values()):
        print()
        print("No memory files found to clean.")
        print("Branch appears to already be clean or newly created.")
        return True

    # Get user confirmation (unless force flag)
    if not force:
        if not get_user_confirmation(branchname_upper, analysis):
            print()
            print("Clean operation cancelled by user.")
            return False
    else:
        print("Force flag enabled - skipping confirmation")

    print()
    print(f"{'='*70}")
    print("Cleaning memory files...")
    print(f"{'='*70}")
    print()

    # Create backup directory and timestamp
    backup_dir = target_path / ".backup"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Clean each file
    results = []

    # Clean local.json
    if local_file.exists():
        print(f"Cleaning {local_file.name}...")
        template_local = get_template_path() / "LOCAL..json"
        success = clean_local_file(local_file, template_local, backup_dir, timestamp)
        if success:
            print(f"  ✅ SUCCESS: Sessions cleared, file reset to template")
            results.append(("local", True))
        else:
            print(f"  ❌ FAILED: Could not clean local file")
            results.append(("local", False))
        print()

    # Clean observations.json
    if obs_file.exists():
        print(f"Cleaning {obs_file.name}...")
        template_obs = get_template_path() / "OBSERVATIONS.json"
        success = clean_observations_file(obs_file, template_obs, backup_dir, timestamp)
        if success:
            print(f"  ✅ SUCCESS: Observations cleared, file reset to template")
            results.append(("observations", True))
        else:
            print(f"  ❌ FAILED: Could not clean observations file")
            results.append(("observations", False))
        print()

    # Clean ai_mail.json
    if mail_file.exists():
        print(f"Cleaning {mail_file.name}...")
        template_mail = get_template_path() / "AI_MAIL.json"
        success = clean_ai_mail_file(mail_file, template_mail, backup_dir, timestamp)
        if success:
            print(f"  ✅ SUCCESS: AI_Mail cleared, file reset to template")
            results.append(("ai_mail", True))
        else:
            print(f"  ❌ FAILED: Could not clean ai_mail file")
            results.append(("ai_mail", False))
        print()

    # Report summary
    print(f"{'='*70}")
    print("Clean Summary:")
    print(f"{'='*70}")

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    print(f"Files processed: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")
    print()

    if success_count == total_count:
        logger.info(f"Branch clean complete: {branch_name} - all {total_count} files cleaned successfully")
        log_operation(
            operation="branch_clean_complete",
            success=True,
            details=f"Branch '{branch_name}' cleaned successfully. {total_count} files processed"
        )
        print(f"✅ Branch cleaned successfully!")
        print(f"Backups saved to: {backup_dir}")
        print()
        print("Branch is now in fresh state with:")
        print("  - No session history")
        print("  - No observations")
        print("  - No AI_Mail messages")
        print("  - All structure and identity preserved")
        return True
    else:
        logger.error(f"Branch clean completed with errors: {branch_name} - {success_count}/{total_count} files cleaned")
        log_operation(
            operation="branch_clean_failed",
            success=False,
            details=f"Branch '{branch_name}' clean completed with errors. {success_count}/{total_count} files cleaned",
            error=f"{total_count - success_count} file(s) failed"
        )
        print(f"❌ Clean completed with errors.")
        print(f"Some files could not be cleaned.")
        return False


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='AIPass Branch Clean - Reset branch to fresh state',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: branch_path, --force

USAGE:
  clean <branch_path> [--force] - Reset branch memory to fresh state

EXAMPLES:
  python3 branch_clean.py /home/aipass/analytics
  python3 branch_clean.py /home/aipass/backup_system --force

WHAT GETS CLEANED:
  - All session entries (reset to empty)
  - All observation entries
  - All email messages

WHAT GETS PRESERVED:
  - All metadata and identity
  - All directory structure
  - All configuration files
  - Backups in .backup/ directory

SAFETY FEATURES:
  - Requires exact branch name confirmation
  - Creates timestamped backups
  - Shows preview before execution
        """
    )
    parser.add_argument('branch_path', help='Path to branch directory to clean')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()
    target_path = Path(args.branch_path).resolve()

    # Initialize JSON infrastructure
    config = load_config()
    data = load_data()

    try:
        success = clean_branch(target_path, args.force)

        # Update statistics
        data["operations_total"] += 1
        if success:
            data["operations_successful"] += 1
            # Count files cleaned from the operation
            data["files_cleaned"] += 3  # local, observations, ai_mail
        else:
            data["operations_failed"] += 1

        save_data(data)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()