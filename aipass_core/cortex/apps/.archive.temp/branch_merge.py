#!/usr/bin/env python3

# ===================AIPASS====================
# META DATA HEADER
# Name: branch_merge.py - AIPass Branch Merge Script
# Date: 2025-10-29
# Version: 1.0.0
# Category: branch_operations
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-10-29): Initial standardized version - Added META header
# =============================================

"""
AIPass Branch Merge Script
Merges two branches' memories into one

Usage:
    python3 branch_merge.py <source_path> <target_path>
    python3 branch_merge.py <source_path> <target_path> --preview
    python3 branch_merge.py <source_path> <target_path> --force

Strategy:
    - Merge sessions chronologically with renumbering
    - Merge observations by date order
    - Merge emails (inbox + sent consolidation)
    - Update metadata with merge history
    - Update registry to mark source as merged
    - Create backups before merge
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))

# Standard library imports
import argparse
import json
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# AIPass infrastructure imports
from prax.apps.prax_logger import system_logger as logger

# Import from branch_lib
from branch_lib import (
    get_branch_name,
    load_registry,
    save_registry,
    find_branch_in_registry
)


# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

# Module root and JSON directory
MODULE_ROOT = Path(__file__).parent.parent
JSON_DIR = MODULE_ROOT / "branch_operations_json"

# Auto-create JSON directory
JSON_DIR.mkdir(exist_ok=True)

# 3-file JSON structure for branch_merge module
CONFIG_FILE = JSON_DIR / "branch_merge_config.json"
DATA_FILE = JSON_DIR / "branch_merge_data.json"
LOG_FILE = JSON_DIR / "branch_merge_log.json"


# =============================================================================
# PATH GETTERS
# =============================================================================

def get_template_dir() -> Path:
    """
    Get template directory path.

    Returns:
        Path to ai_branch_setup_template directory

    Notes:
        Uses AIPASS_ROOT for dynamic path resolution.
        Template location: AIPASS_ROOT / "templates" / "ai_branch_setup_template"
    """
    return AIPASS_ROOT / "templates" / "ai_branch_setup_template"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log_operation(operation: str, success: bool, details: str = "", error: str = ""):
    """
    Log branch_merge operations to module-specific log file

    Args:
        operation: Operation name (e.g., "branch_merge_start")
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
        logger.error(f"[branch_merge] Error saving log: {e}")


def load_config() -> Dict:
    """Load branch_merge configuration"""
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
        logger.error(f"[branch_merge] Error loading config: {e}")
        return default_config


def save_config(config: Dict):
    """Save branch_merge configuration"""
    try:
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_merge] Error saving config: {e}")


def load_data() -> Dict:
    """Load branch_merge runtime data"""
    default_data = {
        "created": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "operations_total": 0,
        "operations_successful": 0,
        "operations_failed": 0,
        "merges_completed": 0
    }

    if not DATA_FILE.exists():
        return default_data

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[branch_merge] Error loading data: {e}")
        return default_data


def save_data(data: Dict):
    """Save branch_merge runtime data with auto timestamp"""
    data["last_updated"] = datetime.now().isoformat()
    try:
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[branch_merge] Error saving data: {e}")


# =============================================================================
# FILE OPERATIONS
# =============================================================================

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file, return None if doesn't exist"""
    if not path.exists():
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ERROR loading {path.name}: {e}")
        return None


def save_json(path: Path, data: Dict[str, Any]) -> bool:
    """Save JSON file with pretty formatting"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"  ERROR saving {path.name}: {e}")
        return False


def backup_file(source: Path, backup_dir: Path, timestamp: str) -> Optional[Path]:
    """Create timestamped backup of file"""
    if not source.exists():
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{source.name}.{timestamp}.backup"

    try:
        shutil.copy2(source, backup_path)
        return backup_path
    except Exception as e:
        print(f"  ERROR backing up {source.name}: {e}")
        return None


def load_branch_memories(branch_path: Path, branch_name: str) -> Optional[Dict[str, Any]]:
    """
    Load all memory files from a branch

    Args:
        branch_path: Path to branch directory
        branch_name: Branch name (uppercase with underscores)

    Returns:
        Dict containing all memory data or None
    """
    branchname_upper = branch_name.upper().replace("-", "_")

    # File paths
    local_file = branch_path / f"{branchname_upper}.local.json"
    obs_file = branch_path / f"{branchname_upper}.observations.json"
    mail_file = branch_path / f"{branchname_upper}.ai_mail.json"
    project_file = branch_path / f"{branchname_upper}.json"

    # Load each file
    local_data = load_json(local_file)
    obs_data = load_json(obs_file)
    mail_data = load_json(mail_file)
    project_data = load_json(project_file)

    if not local_data or not obs_data or not mail_data:
        return None

    return {
        "local": local_data,
        "observations": obs_data,
        "ai_mail": mail_data,
        "project": project_data or {}
    }


def save_merged_memories(target_path: Path, branch_name: str, merged_data: Dict) -> bool:
    """
    Save merged memories to target branch

    Args:
        target_path: Path to target branch
        branch_name: Branch name
        merged_data: Dict containing merged memory data

    Returns:
        True if successful, False otherwise
    """
    branchname_upper = branch_name.upper().replace("-", "_")

    # File paths
    local_file = target_path / f"{branchname_upper}.local.json"
    obs_file = target_path / f"{branchname_upper}.observations.json"
    mail_file = target_path / f"{branchname_upper}.ai_mail.json"
    project_file = target_path / f"{branchname_upper}.json"

    # Save each file
    success = True

    if not save_json(local_file, merged_data["local"]):
        success = False

    if not save_json(obs_file, merged_data["observations"]):
        success = False

    if not save_json(mail_file, merged_data["ai_mail"]):
        success = False

    if merged_data.get("project") and not save_json(project_file, merged_data["project"]):
        success = False

    return success


# =============================================================================
# SESSION MERGING
# =============================================================================

def merge_sessions(source_sessions: List[Dict], target_sessions: List[Dict], source_name: str) -> List[Dict]:
    """
    Merge sessions from both branches in chronological order

    Args:
        source_sessions: Sessions from source branch
        target_sessions: Sessions from target branch
        source_name: Name of source branch (for tracking)

    Returns:
        Merged session list in chronological order with sequential numbering
    """
    # Combine all sessions
    all_sessions = []

    # Add source sessions with merge tracking
    for session in source_sessions:
        session_copy = session.copy()
        session_copy["merged_from"] = source_name
        all_sessions.append(session_copy)

    # Add target sessions
    all_sessions.extend(target_sessions)

    # Sort by date (chronological order)
    all_sessions.sort(key=lambda s: s.get("date", ""))

    # Renumber sequentially
    for i, session in enumerate(all_sessions, start=1):
        session["session_number"] = i

    return all_sessions


# =============================================================================
# OBSERVATIONS MERGING
# =============================================================================

def merge_observations(source_obs: List[Dict], target_obs: List[Dict], source_name: str) -> List[Dict]:
    """
    Merge observations from both branches

    Args:
        source_obs: Observations from source branch
        target_obs: Observations from target branch
        source_name: Name of source branch (for tracking)

    Returns:
        Merged observation list sorted by date
    """
    # Combine all observations
    all_obs = []

    # Add source observations with merge tracking
    for obs in source_obs:
        obs_copy = obs.copy()
        # Add merged_from to each entry in the observation group
        if "entries" in obs_copy:
            for entry in obs_copy["entries"]:
                entry["merged_from"] = source_name
        all_obs.append(obs_copy)

    # Add target observations
    all_obs.extend(target_obs)

    # Sort by date (chronological order)
    all_obs.sort(key=lambda o: o.get("date", ""))

    return all_obs


# =============================================================================
# EMAIL MERGING
# =============================================================================

def merge_emails(source_mail: Dict, target_mail: Dict) -> Dict:
    """
    Merge email boxes from both branches

    Args:
        source_mail: Email data from source branch
        target_mail: Email data from target branch

    Returns:
        Merged email structure
    """
    # Start with target mail structure
    merged = target_mail.copy()

    # Merge summary counts
    if "summary" in source_mail:
        source_summary = source_mail["summary"]

        if "inbox" in source_summary and "inbox" in merged.get("summary", {}):
            merged["summary"]["inbox"]["total"] += source_summary["inbox"].get("total", 0)
            # Handle optional unread count (may not exist in all structures)
            merged["summary"]["inbox"]["unread"] = (
                merged["summary"]["inbox"].get("unread", 0) +
                source_summary["inbox"].get("unread", 0)
            )

        if "sent" in source_summary and "sent" in merged.get("summary", {}):
            merged["summary"]["sent"]["total"] += source_summary["sent"].get("total", 0)

        if "deleted" in source_summary and "deleted" in merged.get("summary", {}):
            merged["summary"]["deleted"]["total"] += source_summary["deleted"].get("total", 0)

    return merged


# =============================================================================
# METADATA UPDATE
# =============================================================================

def update_merged_metadata(
    target_data: Dict,
    source_name: str,
    source_path: Path,
    merge_timestamp: str,
    source_stats: Dict,
    target_stats: Dict
) -> Dict:
    """
    Update target branch metadata to reflect merge

    Args:
        target_data: Target branch project data
        source_name: Source branch name
        source_path: Path to source branch
        merge_timestamp: Timestamp of merge operation
        source_stats: Statistics from source branch
        target_stats: Statistics from target branch

    Returns:
        Updated project data
    """
    if not target_data:
        target_data = {}

    # Initialize merge_history array if not present
    if "merge_history" not in target_data:
        target_data["merge_history"] = []

    # Add merge record
    merge_record = {
        "source_branch": source_name,
        "source_path": str(source_path),
        "merge_date": merge_timestamp,
        "sessions_merged": source_stats.get("sessions", 0),
        "observations_merged": source_stats.get("observations", 0),
        "emails_merged": source_stats.get("emails", 0)
    }

    target_data["merge_history"].append(merge_record)

    # Update last_modified if metadata exists
    if "metadata" in target_data:
        target_data["metadata"]["last_modified"] = merge_timestamp

    return target_data


# =============================================================================
# REGISTRY OPERATIONS
# =============================================================================

def update_registry_for_merge(source_name: str, target_name: str, merge_date: str) -> bool:
    """
    Update registry to mark source as merged and update target last_active

    Args:
        source_name: Source branch name
        target_name: Target branch name
        merge_date: Merge date string

    Returns:
        True if successful, False otherwise
    """
    registry = load_registry()

    # Find source branch
    source_branch = None
    for branch in registry.get("branches", []):
        if branch.get("name") == source_name:
            source_branch = branch
            break

    # Find target branch
    target_branch = None
    for branch in registry.get("branches", []):
        if branch.get("name") == target_name:
            target_branch = branch
            break

    # Update source status
    if source_branch:
        source_branch["status"] = "merged"
        source_branch["merge_info"] = {
            "target_branch": target_name,
            "merge_date": merge_date
        }

    # Update target last_active
    if target_branch:
        target_branch["last_active"] = merge_date

    # Save registry
    return save_registry(registry)


# =============================================================================
# ANALYSIS AND PREVIEW
# =============================================================================

def analyze_branch(data: Dict) -> Dict[str, int]:
    """
    Analyze branch memory data for statistics

    Args:
        data: Branch memory data

    Returns:
        Dict with counts
    """
    stats = {
        "sessions": len(data.get("local", {}).get("sessions", [])),
        "observations": 0,
        "emails": 0
    }

    # Count observation entries
    for obs_group in data.get("observations", {}).get("observations", []):
        if isinstance(obs_group, dict):
            stats["observations"] += len(obs_group.get("entries", []))

    # Count emails
    mail_summary = data.get("ai_mail", {}).get("summary", {})
    stats["emails"] = (
        mail_summary.get("inbox", {}).get("total", 0) +
        mail_summary.get("sent", {}).get("total", 0)
    )

    return stats


def show_merge_preview(
    source_name: str,
    target_name: str,
    source_path: Path,
    target_path: Path,
    source_data: Dict,
    target_data: Dict
) -> None:
    """
    Display merge preview

    Args:
        source_name: Source branch name
        target_name: Target branch name
        source_path: Path to source branch
        target_path: Path to target branch
        source_data: Source branch data
        target_data: Target branch data
    """
    source_stats = analyze_branch(source_data)
    target_stats = analyze_branch(target_data)

    # Calculate totals
    total_sessions = source_stats["sessions"] + target_stats["sessions"]
    total_obs = source_stats["observations"] + target_stats["observations"]
    total_emails = source_stats["emails"] + target_stats["emails"]

    print()
    print("BRANCH MERGE PREVIEW")
    print("=" * 70)
    print()
    print(f"SOURCE: {source_name:30} TARGET: {target_name}")
    print(f"Path: {str(source_path):32} Path: {target_path}")
    print()
    print(f"Sessions:     {source_stats['sessions']:3}                      Sessions:     {target_stats['sessions']:3}")
    print(f"Observations: {source_stats['observations']:3}                      Observations: {target_stats['observations']:3}")
    print(f"Emails:       {source_stats['emails']:3}                      Emails:       {target_stats['emails']:3}")
    print()
    print("AFTER MERGE:")
    print("-" * 70)
    print(f"Target ({target_name}) will contain:")
    print(f"  Sessions:     {total_sessions:3} (combined, renumbered)")
    print(f"  Observations: {total_obs:3} (chronologically sorted)")
    print(f"  Emails:       {total_emails:3} (counts combined)")
    print()
    print(f"Source ({source_name}) will be:")
    print(f"  Status: MERGED (marked in registry)")
    print()


def get_merge_confirmation(source_name: str, target_name: str) -> bool:
    """
    Get user confirmation for merge

    Args:
        source_name: Source branch name
        target_name: Target branch name

    Returns:
        True if confirmed, False otherwise
    """
    print("Type both branch names to confirm (space separated): ", end='', flush=True)
    user_input = input().strip()

    # Split input
    parts = user_input.split()

    if len(parts) != 2:
        print()
        print(f"ERROR: Expected 2 branch names, got {len(parts)}")
        return False

    # Check if names match (order doesn't matter)
    if set([source_name, target_name]) == set(parts):
        return True
    else:
        print()
        print(f"ERROR: Branch names don't match")
        print(f"Expected: {source_name} and {target_name}")
        print(f"Got: {parts[0]} and {parts[1]}")
        return False


# =============================================================================
# MAIN MERGE PROCESS
# =============================================================================

def merge_branches(
    source_path: Path,
    target_path: Path,
    preview_only: bool = False,
    force: bool = False
) -> bool:
    """
    Merge source branch into target branch

    Args:
        source_path: Path to source branch (data comes FROM here)
        target_path: Path to target branch (data goes TO here)
        preview_only: If True, only show preview without merging
        force: If True, skip confirmation

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Branch merge initiated: {source_path} → {target_path} (preview={preview_only}, force={force})")

    # Log operation start
    log_operation(
        operation="branch_merge_start",
        success=True,
        details=f"Initiating branch merge: {source_path} → {target_path} (preview={preview_only}, force={force})"
    )

    # Validate paths exist
    if not source_path.exists():
        logger.error(f"Source path does not exist: {source_path}")
        print(f"❌ ERROR: Source path does not exist: {source_path}")
        return False

    if not target_path.exists():
        logger.error(f"Target path does not exist: {target_path}")
        print(f"❌ ERROR: Target path does not exist: {target_path}")
        return False

    if not source_path.is_dir():
        logger.error(f"Source path is not a directory: {source_path}")
        print(f"❌ ERROR: Source path is not a directory: {source_path}")
        return False

    if not target_path.is_dir():
        logger.error(f"Target path is not a directory: {target_path}")
        print(f"❌ ERROR: Target path is not a directory: {target_path}")
        return False

    # Check if same path
    if source_path.resolve() == target_path.resolve():
        logger.error("Source and target paths are the same")
        print(f"❌ ERROR: Source and target paths are the same")
        return False

    # Get branch names
    source_name = get_branch_name(source_path)
    target_name = get_branch_name(target_path)

    source_name_upper = source_name.upper().replace("-", "_")
    target_name_upper = target_name.upper().replace("-", "_")

    print(f"=== Branch Merge System ===")
    print(f"Source: {source_name_upper} ({source_path})")
    print(f"Target: {target_name_upper} ({target_path})")
    print()

    # Load memories from both branches
    print("Loading source branch memories...")
    source_data = load_branch_memories(source_path, source_name)
    if not source_data:
        print(f"❌ ERROR: Failed to load source branch memories")
        return False

    print("Loading target branch memories...")
    target_data = load_branch_memories(target_path, target_name)
    if not target_data:
        print(f"❌ ERROR: Failed to load target branch memories")
        return False

    print("✅ Memories loaded successfully")

    # Show preview
    show_merge_preview(
        source_name_upper,
        target_name_upper,
        source_path,
        target_path,
        source_data,
        target_data
    )

    # If preview only, stop here
    if preview_only:
        print("✅ Preview mode - no changes made")
        return True

    # Get user confirmation (unless force)
    if not force:
        if not get_merge_confirmation(source_name_upper, target_name_upper):
            print()
            print("⚠️ Merge cancelled by user")
            return False
    else:
        print("⚠️ Force mode - skipping confirmation")

    print()
    print("=" * 70)
    print("Starting merge...")
    print("=" * 70)
    print()

    # Create backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = target_path / ".backup"

    print(f"Creating backups...")
    target_name_upper = target_name.upper().replace("-", "_")

    local_file = target_path / f"{target_name_upper}.local.json"
    obs_file = target_path / f"{target_name_upper}.observations.json"
    mail_file = target_path / f"{target_name_upper}.ai_mail.json"
    project_file = target_path / f"{target_name_upper}.json"

    backup_paths = []
    for file in [local_file, obs_file, mail_file, project_file]:
        if file.exists():
            backup_path = backup_file(file, backup_dir, timestamp)
            if backup_path:
                backup_paths.append(backup_path.name)
            else:
                print(f"❌ ERROR: Failed to backup {file.name}")
                log_operation(
                    operation="branch_merge_failed",
                    success=False,
                    details=f"Failed to backup {file.name}",
                    error="Backup failed"
                )
                return False

    print(f"  ✅ Backed up {len(backup_paths)} files to {backup_dir}/")
    print()

    # Get statistics
    source_stats = analyze_branch(source_data)
    target_stats = analyze_branch(target_data)

    # Merge sessions
    print("Merging sessions...")
    merged_sessions = merge_sessions(
        source_data["local"].get("sessions", []),
        target_data["local"].get("sessions", []),
        source_name_upper
    )
    target_data["local"]["sessions"] = merged_sessions
    print(f"  {len(merged_sessions)} total sessions (renumbered sequentially)")
    print()

    # Merge observations
    print("Merging observations...")
    merged_obs = merge_observations(
        source_data["observations"].get("observations", []),
        target_data["observations"].get("observations", []),
        source_name_upper
    )
    target_data["observations"]["observations"] = merged_obs

    # Count total entries
    total_entries = sum(len(o.get("entries", [])) for o in merged_obs if isinstance(o, dict))
    print(f"  {total_entries} total observation entries (sorted by date)")
    print()

    # Merge emails
    print("Merging emails...")
    merged_mail = merge_emails(source_data["ai_mail"], target_data["ai_mail"])
    target_data["ai_mail"] = merged_mail
    total_emails = (
        merged_mail.get("summary", {}).get("inbox", {}).get("total", 0) +
        merged_mail.get("summary", {}).get("sent", {}).get("total", 0)
    )
    print(f"  {total_emails} total emails (counts combined)")
    print()

    # Update metadata
    print("Updating metadata...")
    merge_timestamp = datetime.now().strftime("%Y-%m-%d")
    target_data["project"] = update_merged_metadata(
        target_data.get("project", {}),
        source_name_upper,
        source_path,
        merge_timestamp,
        source_stats,
        target_stats
    )
    print(f"  Merge history recorded")
    print()

    # Save merged memories
    print("Saving merged memories...")
    if not save_merged_memories(target_path, target_name, target_data):
        print(f"❌ ERROR: Failed to save merged memories")
        print(f"Backups are available in {backup_dir}/")
        log_operation(
            operation="branch_merge_failed",
            success=False,
            details=f"Failed to save merged memories for {target_name_upper}",
            error="Save operation failed"
        )
        return False
    print(f"  ✅ All memory files saved successfully")
    print()

    # Update registry
    print("Updating registry...")
    if update_registry_for_merge(source_name_upper, target_name_upper, merge_timestamp):
        print(f"  ✅ Registry updated - {source_name_upper} marked as merged")
    else:
        print(f"  ⚠️ WARNING: Registry update failed")
        print(f"  Merge completed but registry may be inconsistent")
    print()

    # Summary
    print("=" * 70)
    print("✅ MERGE COMPLETE")
    print("=" * 70)
    print()
    print(f"Target: {target_name_upper} ({target_path})")
    print(f"  Sessions:     {len(merged_sessions)}")
    print(f"  Observations: {total_entries}")
    print(f"  Emails:       {total_emails}")
    print()
    print(f"Source: {source_name_upper}")
    print(f"  Status: MERGED (marked in registry)")
    print()
    print(f"Backups: {backup_dir}/")
    print(f"  {len(backup_paths)} files backed up")
    print()

    logger.info(f"Branch merge complete: {source_name_upper} → {target_name_upper} ({len(merged_sessions)} sessions, {total_entries} observations, {total_emails} emails)")
    log_operation(
        operation="branch_merge_complete",
        success=True,
        details=f"Merged {source_name_upper} → {target_name_upper}: {len(merged_sessions)} sessions, {total_entries} observations, {total_emails} emails"
    )
    return True


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='AIPass Branch Merge - Merge memories from source branch into target branch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: source_path, target_path, --preview, --force

  Merge branch memories from source into target

MERGE PROCESS:
  1. Validate both paths and load memories
  2. Show merge preview with statistics
  3. Get user confirmation (type both branch names)
  4. Backup target branch files
  5. Merge sessions (chronological order, renumbered)
  6. Merge observations (chronological order)
  7. Merge emails (combine counts)
  8. Update target metadata (merge_history)
  9. Save merged result to target
  10. Update registry (mark source as merged)

EXAMPLES:
  python3 branch_merge.py /home/aipass/old-feature /home/aipass/main-feature
  python3 branch_merge.py /path/to/source /path/to/target --preview
  python3 branch_merge.py /path/to/source /path/to/target --force

NOTES:
  - Source data comes FROM source_path
  - Merged data goes TO target_path
  - Source branch is marked as merged in registry
  - Backups created before merging
        """
    )
    parser.add_argument('source_path', help='Path to source branch (data comes FROM here)')
    parser.add_argument('target_path', help='Path to target branch (data goes TO here)')
    parser.add_argument('--preview', action='store_true', help='Show merge preview only, no changes')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()
    source_path = Path(args.source_path).resolve()
    target_path = Path(args.target_path).resolve()

    # Initialize JSON infrastructure
    config = load_config()
    data = load_data()

    try:
        success = merge_branches(source_path, target_path, args.preview, args.force)

        # Update statistics (skip if preview-only mode)
        if not args.preview:
            data["operations_total"] += 1
            if success:
                data["operations_successful"] += 1
                data["merges_completed"] += 1
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