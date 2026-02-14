#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: error_monitor.py - Log Error Monitor & AI_Mail Notifier
# Date: 2025-10-25
# Version: 1.0.0
# Category: ai_mail
#
# CHANGELOG:
#   - v1.0.0 (2025-10-25): Initial implementation with watchdog file monitoring
# =============================================

"""
Error Monitor - Autonomous Error Detection & AI_Mail Notifications

Watches /home/aipass/flow/logs/ for ERROR-level messages and sends AI_Mail
notifications to @flow. Deduplicates errors by tracking unique error signatures
and updating notification counts instead of spamming new emails.

Features:
- File watcher triggers on new ERROR log entries
- Deduplication via error hashing (module + message)
- Email count updates (1 notification → 700 notifications for same error)
- 3-file JSON tracking (config/data/log)
- Drone-compliant CLI

Architecture:
1. Watchdog monitors /home/aipass/flow/logs/*.log
2. On ERROR: Extract module name, error message, timestamp
3. Hash error (module + message) for unique ID
4. Check error_monitor_data.json:
   - NEW error → Send AI_Mail, track in JSON
   - EXISTING error → Increment count, update email in .ai_mail.md
5. Email format includes counter that increases with repeats

Priority Indicators (via count):
- 600+ notifications = CRITICAL (investigate immediately)
- 1 notification 3 weeks ago = LOW (review when convenient)
"""

# =============================================
# IMPORTS
# =============================================

# INFRASTRUCTURE IMPORT PATTERN - Universal AIPass pattern
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.append(str(AIPASS_ROOT))

from prax.apps.prax_logger import system_logger as logger

# Standard imports
import json
import hashlib
import re
import argparse
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple
import time

# Watchdog for file monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.error("[error_monitor] CRITICAL: watchdog not installed - cannot monitor logs")

# =============================================
# CONSTANTS & CONFIG
# =============================================

MODULE_NAME = "error_monitor"
MODULE_VERSION = "1.0.0"

# Paths
FLOW_DIR = AIPASS_ROOT / "flow"
FLOW_LOGS_DIR = FLOW_DIR / "logs"
AI_MAIL_DIR = AIPASS_ROOT / "ai_mail"
AI_MAIL_JSON = AI_MAIL_DIR / "ai_mail_json"
AI_MAIL_FILE = FLOW_DIR / "FLOW.ai_mail.md"

# 3-File JSON Pattern
CONFIG_FILE = AI_MAIL_JSON / f"{MODULE_NAME}_config.json"
DATA_FILE = AI_MAIL_JSON / f"{MODULE_NAME}_data.json"
LOG_FILE = AI_MAIL_JSON / f"{MODULE_NAME}_log.json"

# Email sender info
FROM_EMAIL = "@error_monitor"
FROM_NAME = "Error Monitor"
TO_EMAIL = "@flow"

# =============================================
# HELPER FUNCTIONS
# =============================================

def get_all_branch_logs_dirs() -> List[Path]:
    """
    Discover all branch log directories system-wide

    Returns list of Path objects for all /home/aipass/*/logs/ directories
    Example: [/home/aipass/flow/logs, /home/aipass/api/logs, /home/aipass/prax/logs, ...]
    """
    aipass_dir = Path.home()
    log_dirs = []

    if not aipass_dir.exists():
        logger.error(f"[{MODULE_NAME}] AIPASS directory not found: {aipass_dir}")
        return []

    # Scan all subdirectories for logs/ folders
    for branch_dir in aipass_dir.iterdir():
        if branch_dir.is_dir():
            logs_dir = branch_dir / "logs"
            if logs_dir.exists() and logs_dir.is_dir():
                log_dirs.append(logs_dir)

    return sorted(log_dirs)  # Sort for consistent ordering

def get_branch_from_log_path(log_file_path: str) -> Tuple[str, Path]:
    """
    Extract branch name and root path from log file path.

    Args:
        log_file_path: Full path to log file (e.g., /home/aipass/api/logs/openrouter.log)

    Returns:
        Tuple of (branch_name, branch_root_path)
        Example: ("API", Path("/home/aipass/api"))

    Special case: root directory returns ("AIPASS.admin", Path("/"))
    """
    log_path = Path(log_file_path)

    # Navigate up from log file to branch root
    # /home/aipass/api/logs/openrouter.log -> /home/aipass/api
    branch_root = log_path.parent.parent

    # Special case: root directory
    if branch_root == Path("/"):
        return "AIPASS.admin", branch_root

    # Extract branch name from directory name
    # /home/aipass/api -> "API"
    # /home/aipass/backup-system -> "BACKUP_SYSTEM"
    branch_folder = branch_root.name.replace("-", "_")
    branch_name = branch_folder.upper()

    return branch_name, branch_root

def get_ai_mail_file_for_branch(branch_name: str, branch_root: Path) -> Optional[Path]:
    """
    Build path to branch's .ai_mail.md file.

    Args:
        branch_name: Branch name in UPPERCASE (e.g., "API", "FLOW")
        branch_root: Path to branch root directory

    Returns:
        Path to .ai_mail.md file, or None if doesn't exist

    Pattern: {branch_root}/{BRANCHNAME}.ai_mail.md
    Special case: root -> /AIPASS.admin.ai_mail.md
    """
    if branch_root == Path("/"):
        ai_mail_file = Path("/AIPASS.admin.ai_mail.md")
    else:
        ai_mail_file = branch_root / f"{branch_name}.ai_mail.md"

    if not ai_mail_file.exists():
        logger.warning(f"[{MODULE_NAME}] AI_Mail file not found for {branch_name}: {ai_mail_file}")
        return None

    return ai_mail_file

def generate_error_hash(module_name: str, error_message: str) -> str:
    """
    Generate unique hash for error deduplication.

    Args:
        module_name: Logger/module name (e.g., 'flow_plan_summarizer')
        error_message: Error message text

    Returns:
        SHA256 hash (first 12 chars)
    """
    combined = f"{module_name}::{error_message}"
    return hashlib.sha256(combined.encode()).hexdigest()[:12]

def parse_error_log_line(log_line: str) -> Optional[Dict]:
    """
    Parse error log line to extract components.

    Format: 2025-10-25 15:26:37 - captured_flow_plan_summarizer - ERROR - Failed to write...

    Returns:
        Dict with timestamp, logger_name, level, message
        None if not an ERROR line
    """
    # Pattern: {timestamp} - {logger} - {level} - {message}
    # Accepts both prax format (00:20:13) and Python default (00:20:13,454 or 00:20:13.454)
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})[,.]?\d* - (.+?) - (ERROR|WARNING|INFO) - (.+)$'
    match = re.match(pattern, log_line.strip())

    if not match:
        return None

    timestamp, logger_name, level, message = match.groups()

    # Only process ERROR level
    if level != "ERROR":
        return None

    # Extract module name (remove 'captured_' prefix if present)
    module_name = logger_name.replace('captured_', '')

    return {
        "timestamp": timestamp,
        "logger_name": logger_name,
        "module_name": module_name,
        "level": level,
        "message": message.strip()
    }

def load_error_data() -> Dict:
    """Load error tracking data from JSON with validation"""
    if not DATA_FILE.exists():
        return {}

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate structure: should be dict with error_hash keys
        if not isinstance(data, dict):
            logger.error(f"[{MODULE_NAME}] Invalid error data structure (not dict) - creating backup and starting fresh")
            # Backup corrupted file
            backup_path = DATA_FILE.with_suffix('.json.corrupted')
            DATA_FILE.rename(backup_path)
            return {}

        # Validate each entry has required fields
        for error_hash, error_info in list(data.items()):
            if not isinstance(error_info, dict):
                logger.error(f"[{MODULE_NAME}] Invalid error entry {error_hash} - removing")
                del data[error_hash]
                continue

            required_fields = ["first_seen", "last_seen", "count", "error_text", "module_name"]
            if not all(field in error_info for field in required_fields):
                logger.error(f"[{MODULE_NAME}] Incomplete error entry {error_hash} - removing")
                del data[error_hash]

        return data
    except json.JSONDecodeError as e:
        logger.error(f"[{MODULE_NAME}] JSON decode error: {e} - creating backup and starting fresh")
        # Backup corrupted file
        backup_path = DATA_FILE.with_suffix('.json.corrupted')
        if DATA_FILE.exists():
            DATA_FILE.rename(backup_path)
        return {}
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to load error data: {e}")
        return {}

def save_error_data(data: Dict):
    """Save error tracking data to JSON"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to save error data: {e}")

def log_operation(operation: str, success: bool, details: str = "", error: str = ""):
    """Log monitor operations to JSON"""
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

    # Keep last 100 entries
    if len(logs) > 100:
        logs = logs[-100:]

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)

def send_initial_error_email(error_hash: str, error_info: Dict, ai_mail_file: Path, branch_name: str) -> bool:
    """
    Send initial AI_Mail notification for new error to branch-specific inbox.

    Args:
        error_hash: Unique error identifier
        error_info: Error details (module, message, timestamps)
        ai_mail_file: Path to branch's .ai_mail.md file
        branch_name: Branch name (e.g., "FLOW", "API")

    Email format includes:
    - Error ID (hash) for tracking
    - Module name
    - Error message
    - First seen timestamp
    - Notification count (starts at 1)
    """
    subject = f"Error in {error_info['module_name']}.log - 1 notification"

    # Build log path from branch
    branch_root = ai_mail_file.parent
    logs_dir = branch_root / "logs"

    message = f"""Error detected in {branch_name} logs

Error ID: {error_hash}
Module: {error_info['module_name']}
First seen: {error_info['first_seen']}
Last seen: {error_info['last_seen']}
Notification count: 1

Error message:
{error_info['error_text']}

Check logs: {logs_dir}/{error_info['module_name']}.log
"""

    # Append to AI_Mail file
    try:
        email_block = f"""
---
**Date:** {error_info['first_seen']}
**From:** {FROM_NAME} ({FROM_EMAIL})
**Subject:** {subject}

{message}
---
"""

        # Read current AI_Mail file
        if not ai_mail_file.exists():
            logger.error(f"[{MODULE_NAME}] AI_Mail file not found: {ai_mail_file}")
            return False

        with open(ai_mail_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find Unread Messages section
        unread_header = None
        if "## 📨 Unread Messages" in content:
            unread_header = "## 📨 Unread Messages"
        elif "## 📬 Unread Messages" in content:
            unread_header = "## 📬 Unread Messages"

        if not unread_header:
            logger.error(f"[{MODULE_NAME}] Unread Messages section not found")
            return False

        # Insert email after Unread Messages header
        parts = content.split(unread_header, 1)
        section_content = parts[1]

        # Remove "*No new messages*" if present
        section_content = section_content.replace("*No new messages*", "").lstrip('\n')

        # Insert email at top of section
        updated_content = parts[0] + unread_header + "\n" + email_block + "\n" + section_content

        # Write back to branch-specific file
        with open(ai_mail_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        logger.info(f"[{MODULE_NAME}] Sent error email to {branch_name}: {error_hash}")
        return True

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to send email to {branch_name}: {e}")
        return False

def update_error_email_count(error_hash: str, new_count: int, last_seen: str, ai_mail_file: Path) -> bool:
    """
    Update existing error email with new notification count in branch-specific inbox.

    Args:
        error_hash: Unique error identifier
        new_count: Updated notification count
        last_seen: Latest occurrence timestamp
        ai_mail_file: Path to branch's .ai_mail.md file

    Finds email by error ID and updates:
    - Subject line count
    - Notification count in body
    - Last seen timestamp
    """
    try:
        if not ai_mail_file.exists():
            return False

        with open(ai_mail_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find email block containing this error_hash
        # Pattern: Error ID: {error_hash}
        if f"Error ID: {error_hash}" not in content:
            logger.warning(f"[{MODULE_NAME}] Email for error {error_hash} not found in {ai_mail_file}")
            return False

        # Split into email blocks
        # Use just '---' as delimiter to avoid duplicating **Date:**
        lines = content.split('\n')
        updated_lines = []
        in_target_email = False
        skip_until_separator = False

        for i, line in enumerate(lines):
            # Check if this block contains our error hash
            if f"Error ID: {error_hash}" in line:
                in_target_email = True

            # If we're in the target email and find subject line, update it
            if in_target_email and line.startswith("**Subject:**"):
                # Update subject count
                updated_line = re.sub(
                    r'(\*\*Subject:\*\* Error in .+?\.log) - \d+ notifications?',
                    rf'\1 - {new_count} notification{"s" if new_count > 1 else ""}',
                    line
                )
                updated_lines.append(updated_line)
                continue

            # Update notification count
            if in_target_email and line.startswith("Notification count:"):
                updated_lines.append(f"Notification count: {new_count}")
                continue

            # Update last seen
            if in_target_email and line.startswith("Last seen:"):
                updated_lines.append(f"Last seen: {last_seen}")
                continue

            # End of this email block
            if in_target_email and line.strip() == "---" and i > 0:
                in_target_email = False

            updated_lines.append(line)

        updated_content = '\n'.join(updated_lines)

        # Write back to branch-specific file
        with open(ai_mail_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        logger.info(f"[{MODULE_NAME}] Updated error count: {error_hash} -> {new_count} notifications")
        return True

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to update email count: {e}")
        return False

def process_error(module_name: str, error_message: str, timestamp: str, log_file_path: str):
    """
    Process detected error - send or update notification.

    Workflow:
    1. Detect branch from log file path
    2. Generate unique hash
    3. Load tracking data
    4. If NEW error:
       - Send initial email to branch's inbox
       - Track in JSON (count=1)
    5. If EXISTING error:
       - Increment count in JSON
       - Update email in branch's .ai_mail.md
    """
    # Self-exclusion: Don't monitor error_monitor's own errors (prevents infinite loops)
    if "error_monitor" in module_name.lower():
        return

    # Detect branch from log file path
    branch_name, branch_root = get_branch_from_log_path(log_file_path)
    ai_mail_file = get_ai_mail_file_for_branch(branch_name, branch_root)

    if not ai_mail_file:
        logger.error(f"[{MODULE_NAME}] Cannot route error - no AI_Mail file for {branch_name}")
        return

    error_hash = generate_error_hash(module_name, error_message)
    error_data = load_error_data()

    if error_hash not in error_data:
        # NEW ERROR - Send initial notification
        error_info = {
            "first_seen": timestamp,
            "last_seen": timestamp,
            "count": 1,
            "error_text": error_message,
            "module_name": module_name,
            "email_sent": False
        }

        # Send email to branch-specific inbox
        if send_initial_error_email(error_hash, error_info, ai_mail_file, branch_name):
            error_info["email_sent"] = True
            error_data[error_hash] = error_info
            save_error_data(error_data)

            log_operation(
                "new_error_detected",
                True,
                f"Error {error_hash[:8]} in {module_name} ({branch_name}) - email sent"
            )
        else:
            log_operation(
                "new_error_detected",
                False,
                f"Error {error_hash[:8]} in {module_name} ({branch_name})",
                "Failed to send email"
            )
    else:
        # EXISTING ERROR - Update count
        error_info = error_data[error_hash]
        error_info["count"] += 1
        error_info["last_seen"] = timestamp

        # Update email with new count in branch-specific inbox
        if update_error_email_count(error_hash, error_info["count"], timestamp, ai_mail_file):
            save_error_data(error_data)

            log_operation(
                "error_count_updated",
                True,
                f"Error {error_hash[:8]} -> {error_info['count']} notifications"
            )
        else:
            log_operation(
                "error_count_updated",
                False,
                f"Error {error_hash[:8]}",
                "Failed to update email"
            )

# =============================================
# FILE WATCHER
# =============================================

class LogFileHandler(FileSystemEventHandler):
    """Watches log files for ERROR entries across multiple branch directories"""

    def __init__(self, log_dirs: List[Path]):
        """
        Initialize handler for multiple log directories

        Args:
            log_dirs: List of Path objects to log directories (e.g., [/home/aipass/flow/logs, /home/aipass/api/logs])
        """
        self.log_positions = {}
        self.log_dirs = log_dirs

        # Initialize positions to END of existing files in ALL directories
        for logs_dir in log_dirs:
            if logs_dir.exists():
                for log_file in logs_dir.glob("*.log"):
                    self.log_positions[str(log_file)] = log_file.stat().st_size

    def on_modified(self, event):
        """Triggered when log file is modified"""
        if event.is_directory:
            return


        # Ensure file_path is str (watchdog may provide bytes)
        file_path = event.src_path
        if isinstance(file_path, bytes):
            file_path = file_path.decode()

        # Only monitor .log files
        if not str(file_path).endswith('.log'):
            return

        # Verify file is in one of our monitored directories
        is_monitored = any(str(log_dir) in str(file_path) for log_dir in self.log_dirs)
        if not is_monitored:
            return

        # Read new content only (position tracking)
        try:
            current_size = Path(str(file_path)).stat().st_size
            last_pos = self.log_positions.get(str(file_path), 0)

            if current_size > last_pos:
                with open(str(file_path), 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_pos)
                    new_lines = f.read().splitlines()

                    # Process each new line
                    for line in new_lines:
                        error_info = parse_error_log_line(line)
                        if error_info:
                            # ERROR detected - process it with branch routing
                            process_error(
                                error_info['module_name'],
                                error_info['message'],
                                error_info['timestamp'],
                                str(file_path)  # Pass log file path for branch detection
                            )

                # Update position
                self.log_positions[str(file_path)] = current_size

        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Error processing {file_path}: {e}")

# =============================================
# CLI COMMANDS
# =============================================

def handle_watch(args):
    """Start watching logs for errors across all branches"""
    if not WATCHDOG_AVAILABLE:
        print("❌ Error: watchdog library not installed")
        print("Install: pip install watchdog")
        return 1

    # Discover all branch log directories
    log_dirs = get_all_branch_logs_dirs()

    if not log_dirs:
        print("❌ Error: No log directories found in /home/aipass/*/logs/")
        return 1

    print(f"👁️  Error Monitor v{MODULE_VERSION} (System-Wide)")
    print(f"\n📁 Discovered {len(log_dirs)} branch log directories:")
    for log_dir in log_dirs:
        branch_name = log_dir.parent.name
        print(f"   - {branch_name}/logs/")

    print("\n📧 Routing notifications to branch-specific AI_Mail inboxes")
    print("\nMonitoring for ERROR-level messages...")
    print("(Press Ctrl+C to stop)\n")

    # Create file watcher with all discovered directories
    event_handler = LogFileHandler(log_dirs)
    observer = Observer()

    # Schedule observer to watch ALL directories
    for log_dir in log_dirs:
        observer.schedule(event_handler, str(log_dir), recursive=False)

    observer.start()

    log_operation("watch_started", True, f"Monitoring {len(log_dirs)} branch directories")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n✓ Monitoring stopped")
        log_operation("watch_stopped", True, "User interrupted")

    observer.join()
    return 0

def handle_status(args):
    """Show error tracking status"""
    error_data = load_error_data()

    if not error_data:
        print("📊 Error Monitor Status")
        print("\n✓ No errors tracked")
        return 0

    print(f"📊 Error Monitor Status - {len(error_data)} unique errors tracked\n")

    # Sort by count (highest first)
    sorted_errors = sorted(
        error_data.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )

    for error_hash, info in sorted_errors[:20]:  # Show top 20
        print(f"🔴 {error_hash[:8]} - {info['module_name']}")
        print(f"   Notifications: {info['count']}")
        print(f"   First seen: {info['first_seen']}")
        print(f"   Last seen: {info['last_seen']}")
        print(f"   Error: {info['error_text'][:80]}...")
        print()

    if len(sorted_errors) > 20:
        print(f"... and {len(sorted_errors) - 20} more errors\n")

    return 0

def handle_clear(args):
    """Clear error tracking data"""
    if args.confirm:
        save_error_data({})
        print("✓ Error tracking data cleared")
        log_operation("data_cleared", True, "Manual clear by user")
        return 0
    else:
        print("⚠️  This will clear all error tracking data")
        print("   Re-run with --confirm to proceed")
        return 1

# =============================================
# MAIN
# =============================================

def main():
    parser = argparse.ArgumentParser(
        description='Error Monitor - Log error detection and AI_Mail notifications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: watch, status, clear, --confirm

  watch      - Start monitoring logs for errors (sends AI_Mail notifications)
  status     - Show error tracking status (unique errors, counts)
  clear      - Clear error tracking data (requires --confirm)

EXAMPLES:
  python3 error_monitor.py watch           # Start error monitoring
  python3 error_monitor.py status          # Show tracked errors
  python3 error_monitor.py clear --confirm # Clear tracking data

WORKFLOW:
  1. Watch command monitors /home/aipass/flow/logs/*.log
  2. When ERROR detected → Check if seen before
  3. NEW error → Send AI_Mail notification
  4. EXISTING error → Update count in existing email
  5. Priority by count: 600+ = CRITICAL, 1 = LOW
        """
    )

    parser.add_argument('command',
                       choices=['watch', 'status', 'clear'],
                       help='Command to execute')

    parser.add_argument('--confirm',
                       action='store_true',
                       help='Confirm destructive operations')

    args = parser.parse_args()

    # Route to command handlers
    if args.command == 'watch':
        return handle_watch(args)
    elif args.command == 'status':
        return handle_status(args)
    elif args.command == 'clear':
        return handle_clear(args)
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
