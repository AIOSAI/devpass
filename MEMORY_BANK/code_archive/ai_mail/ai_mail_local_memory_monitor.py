#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: local_memory_monitor.py - Memory Health Monitor
# Date: 2025-10-23
# Version: 1.0.0
# Category: ai_mail
#
# CHANGELOG:
#   - v1.0.0 (2025-10-23): Initial implementation - event-driven memory monitoring
# =============================================

"""
Local Memory Monitor - Event-Driven Memory Health System

Monitors branch registry for memory health status.
Sends AI_Mail notifications when files exceed compression threshold.

Architecture:
- Branches ping registry on startup (branch_ping.py)
- Monitor reads visual indicators from registry (not full files)
- Sends AI_Mail at 600+ lines with agent deployment instructions
- No polling - event-driven via registry updates

Follows AIPass Standards (STANDARDS.md Section 5.0):
- 3-file JSON pattern (config, data, log)
- Registry file (4th file exception for system coordination)
- Proper error handling and logging
"""

# =============================================
# IMPORTS
# =============================================
import sys
from pathlib import Path

# Universal import pattern
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.append(str(AIPASS_ROOT))

import json
import os
from datetime import datetime
import traceback
from typing import Dict, List, Tuple, Optional

# Prax logger integration
from prax.apps.prax_logger import system_logger as logger

# =============================================
# CONSTANTS & CONFIG
# =============================================
AI_MAIL_ROOT = AIPASS_ROOT / "ai_mail"
AI_MAIL_JSON = AI_MAIL_ROOT / "ai_mail_json"
CONFIG_FILE = AI_MAIL_JSON / "local_memory_monitor_config.json"
DATA_FILE = AI_MAIL_JSON / "local_memory_monitor_data.json"
LOG_FILE = AI_MAIL_JSON / "local_memory_monitor_log.json"
REGISTRY_FILE = AI_MAIL_JSON / "local_memory_monitor_registry.json"

# =============================================
# HELPER FUNCTIONS
# =============================================
def create_config_if_missing():
    """Create default config file if it doesn't exist"""
    if not CONFIG_FILE.exists():
        # Ensure parent directory exists
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Default config structure
        default_config = {
            "module_name": "local_memory_monitor",
            "timestamp": datetime.now().isoformat(),
            "config": {
                "enabled": True,
                "version": "1.0.0",
                "thresholds": {
                    "green": {
                        "min": 0,
                        "max": 400,
                        "emoji": "🟢 Healthy"
                    },
                    "yellow": {
                        "min": 401,
                        "max": 550,
                        "emoji": "🟡 Approaching"
                    },
                    "red": {
                        "min": 551,
                        "max": 9999,
                        "emoji": "🔴 Compress Now"
                    },
                    "email_trigger": 600
                },
                "email_template": {
                    "subject": "Memory Compression Required - {file_type} at {line_count} lines",
                    "body": "---\n**From:** Local Memory Monitor\n**Date:** {date}\n**Subject:** Memory Compression Required\n\nHello {branch_name},\n\nYour {file_type} has reached {line_count} lines and requires compression.\n\n**REQUIRED ACTION:**\n\nYou must deploy a compression agent to reduce your memory file from {line_count} lines to 400 lines.\n\n**Instructions:**\n\n1. Deploy an agent with the following prompt:\n\n```\nCompress my {file_type} file from {line_count} lines to 400 lines following the compression rules:\n\n- Top 25% (most recent): Keep mostly intact\n- Next 25%: Reduce slightly (combine details)\n- Next 25%: Reduce more (summary format)\n- Last 25% (oldest): Delete if needed for space\n\nPreserve:\n- All session headers and dates\n- Key achievements and milestones\n- Critical errors and resolutions\n- Important patterns and learnings\n\nRemove:\n- Routine status updates\n- Redundant information\n- Low-value details\n- Completed temporary tasks\n\nMaintain chronological order (newest first).\n```\n\n2. After compression completes:\n   - Verify file is ~400 lines\n   - Test that nothing critical was lost\n   - Send AI-Mail response to `/AIPASS.admin.ai-mail.md` confirming completion\n\n**Why this matters:**\n\nMemory files over 600 lines impact startup performance and context clarity. Regular compression keeps your memory efficient and relevant.\n\n**Questions?**\n\nContact Admin branch or check compression rules in your {file_type} header.\n\n- Local Memory Monitor\n---"
                },
                "files_to_monitor": [
                    "local.md",
                    "observations.md"
                ],
                "check_frequency_hours": 24
            }
        }

        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Config file auto-created: {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Failed to create config file: {e}")
            raise

def load_config():
    """Load configuration from JSON"""
    create_config_if_missing()  # Auto-heal first

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise

def load_data():
    """Load runtime data from JSON"""
    if not DATA_FILE.exists():
        # Create default data structure
        data = {
            "last_updated": datetime.now().isoformat(),
            "runtime_state": {
                "current_status": "initialized",
                "last_check": None,
                "total_emails_sent": 0,
                "total_branches_monitored": 0
            },
            "statistics": {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "emails_sent_today": 0,
                "last_reset_date": datetime.now().date().isoformat()
            }
        }
        save_data(data)
        return data

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    """Save runtime data to JSON"""
    data["last_updated"] = datetime.now().isoformat()

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_registry():
    """Load branch registry"""
    if not REGISTRY_FILE.exists():
        return {
            "last_updated": "",
            "active_branches": {},
            "statistics": {
                "total_branches": 0,
                "green_status": 0,
                "yellow_status": 0,
                "red_status": 0
            }
        }

    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def log_operation(operation: str, message: str, success: bool = True, details: Dict | None = None):
    """Log operation to module log file"""
    if not LOG_FILE.exists():
        log_data = {
            "entries": [],
            "summary": {"total_entries": 0, "last_entry": None, "next_id": 1}
        }
    else:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

    entry = {
        "id": log_data["summary"]["next_id"],
        "timestamp": datetime.now().isoformat(),
        "level": "INFO" if success else "ERROR",
        "operation": operation,
        "message": message,
        "success": success
    }

    if details:
        entry["details"] = details

    # Prepend (newest first)
    log_data["entries"].insert(0, entry)
    log_data["summary"]["total_entries"] += 1
    log_data["summary"]["last_entry"] = entry["timestamp"]
    log_data["summary"]["next_id"] += 1

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def send_ai_mail(branch_path: str, branch_name: str, file_type: str, line_count: int, config: Dict):
    """Send AI_Mail to branch about compression requirement"""
    # Build AI_Mail file path
    ai_mail_path = Path(branch_path) / f"{branch_name}.ai_mail.md"

    if not ai_mail_path.exists():
        log_operation("send_ai_mail", f"AI_Mail file not found for {branch_name}", False)
        return False

    # Format email from template
    template = config["config"]["email_template"]["body"]
    email = template.format(
        branch_name=branch_name,
        file_type=file_type,
        line_count=line_count,
        date=datetime.now().strftime("%Y-%m-%d")
    )

    # Read current AI_Mail file
    with open(ai_mail_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find Unread Messages section and insert
    unread_marker = "## 📨 Unread Messages"

    if unread_marker not in content:
        log_operation("send_ai_mail", f"Unread section not found in {branch_name} AI_Mail", False)
        return False

    # Insert after marker
    parts = content.split(unread_marker)
    new_content = parts[0] + unread_marker + "\n\n" + email + "\n" + parts[1]

    # Write back
    with open(ai_mail_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    log_operation("send_ai_mail", f"Sent compression email to {branch_name} for {file_type}", True, {
        "branch": branch_name,
        "file": file_type,
        "lines": line_count
    })

    return True

# =============================================
# MAIN FUNCTIONS
# =============================================
def check_registry_and_send_emails():
    """Main monitoring function - check registry and send emails if needed"""
    try:
        logger.info("Starting memory health check")

        # Load config and data
        config = load_config()
        data = load_data()
        registry = load_registry()

        email_trigger = config["config"]["thresholds"]["email_trigger"]
        emails_sent = 0

        logger.info(f"Checking {len(registry['active_branches'])} branches for compression needs (trigger: {email_trigger} lines)")

        # Check each branch
        for branch_path, branch_data in registry["active_branches"].items():
            branch_name = branch_data["branch_name"]

            # Check local.md
            local_status = branch_data.get("local_md", {})
            if local_status.get("line_count", 0) >= email_trigger:
                logger.warning(f"Branch {branch_name} local.md at {local_status['line_count']} lines - sending compression email")
                if send_ai_mail(branch_path, branch_name, "local.md", local_status["line_count"], config):
                    emails_sent += 1

            # Check observations.md
            obs_status = branch_data.get("observations_md", {})
            if obs_status.get("line_count", 0) >= email_trigger:
                logger.warning(f"Branch {branch_name} observations.md at {obs_status['line_count']} lines - sending compression email")
                if send_ai_mail(branch_path, branch_name, "observations.md", obs_status["line_count"], config):
                    emails_sent += 1

        # Update statistics
        data["runtime_state"]["last_check"] = datetime.now().isoformat()
        data["runtime_state"]["total_emails_sent"] += emails_sent
        data["runtime_state"]["total_branches_monitored"] = len(registry["active_branches"])
        data["statistics"]["total_operations"] += 1
        data["statistics"]["successful_operations"] += 1
        data["statistics"]["emails_sent_today"] += emails_sent

        save_data(data)

        # Log summary
        log_operation("check_registry", f"Monitoring complete - {emails_sent} emails sent", True, {
            "branches_checked": len(registry["active_branches"]),
            "emails_sent": emails_sent
        })

        logger.info(f"Memory health check complete - {len(registry['active_branches'])} branches checked, {emails_sent} emails sent")
        print(f"✅ Monitor check complete - {len(registry['active_branches'])} branches, {emails_sent} emails sent")
        return 0

    except Exception as e:
        # Update failure stats
        try:
            data = load_data()
            data["statistics"]["failed_operations"] += 1
            save_data(data)
        except:
            pass

        log_operation("check_registry", f"Monitor check failed: {str(e)}", False)
        logger.error(f"Memory health check failed: {str(e)}\n{traceback.format_exc()}")
        print(f"❌ Monitor check failed: {str(e)}")
        return 1

def show_status():
    """Display current monitor status"""
    logger.info("Retrieving monitor status")
    data = load_data()
    registry = load_registry()

    print("\n=== Local Memory Monitor Status ===")
    print(f"Last Check: {data['runtime_state']['last_check'] or 'Never'}")
    print(f"Total Branches: {registry['statistics']['total_branches']}")
    print(f"🟢 Green: {registry['statistics']['green_status']}")
    print(f"🟡 Yellow: {registry['statistics']['yellow_status']}")
    print(f"🔴 Red: {registry['statistics']['red_status']}")
    print(f"\nEmails Sent (Total): {data['runtime_state']['total_emails_sent']}")
    print(f"Emails Sent (Today): {data['statistics']['emails_sent_today']}")
    print(f"Operations (Success/Fail): {data['statistics']['successful_operations']}/{data['statistics']['failed_operations']}")
    print()

    logger.info("Status retrieved successfully")
    return 0

# =============================================
# CLI/EXECUTION
# =============================================
def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Local Memory Monitor - Memory health monitoring system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: check, status

  check  - Check registry and send emails if needed
  status - Display current monitor status

EXAMPLES:
  python3 local_memory_monitor.py check
  python3 local_memory_monitor.py status
        """
    )

    parser.add_argument('command',
                       choices=['check', 'status'],
                       help='Command to execute')

    args = parser.parse_args()

    if args.command == 'check':
        return check_registry_and_send_emails()
    elif args.command == 'status':
        return show_status()

if __name__ == "__main__":
    exit(main())
