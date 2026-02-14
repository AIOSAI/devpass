#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: ai_mail_cli.py - AI_Mail CLI Interface
# Date: 2025-10-24
# Version: 1.0.0
# Category: ai_mail
#
# CHANGELOG:
#   - v1.0.0 (2025-10-24): Initial implementation - human-friendly email CLI
# =============================================

"""
AI_Mail CLI Interface

Human-friendly email system for sending/receiving messages between branches.
Designed for both interactive use (prompts/menus) and direct commands (AI-friendly).

Features:
- Send emails to branches (interactive or direct)
- View inbox (received messages)
- View sent messages
- Archive management (future)

Usage:
  Interactive: drone email
  Direct: drone email @admin "Subject" "Message"
  View: drone inbox, drone sent
"""

# =============================================
# IMPORTS
# =============================================
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
import sys
sys.path.append(str(AIPASS_ROOT))

import json
import argparse
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from prax.apps.prax_logger import system_logger as logger

# =============================================
# CONSTANTS & CONFIG
# =============================================
MODULE_NAME = "ai_mail_cli"
AI_MAIL_ROOT = AIPASS_ROOT / "ai_mail"
AI_MAIL_JSON = AI_MAIL_ROOT / "ai_mail_json"
USER_CONFIG_FILE = AI_MAIL_JSON / "user_config.json"

# =============================================
# CONFIG MANAGEMENT
# =============================================

def load_user_config() -> Dict:
    """Load user configuration"""
    if not USER_CONFIG_FILE.exists():
        logger.error(f"[{MODULE_NAME}] User config not found: {USER_CONFIG_FILE}")
        raise FileNotFoundError(f"User config not found: {USER_CONFIG_FILE}")

    with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_current_user() -> Dict:
    """Get current user's info"""
    config = load_user_config()
    user_id = config["current_user"]
    return config["users"][user_id]

def get_all_branches() -> List[Dict]:
    """
    Get list of all branches for email selection.
    Reads from AIPass branch registry at /home/aipass/BRANCH_REGISTRY.json

    Returns: List of dicts with branch info:
        [{"name": "AIPASS.admin", "path": "/", "email": "@admin"}, ...]
    """
    import json
    registry_file = Path("/home/aipass/BRANCH_REGISTRY.json")
    branches = []

    if not registry_file.exists():
        logger.error(f"[{MODULE_NAME}] Branch registry not found: {registry_file}")
        print(f"❌ Error: Branch registry not found at {registry_file}")
        print(f"   Registry must be initialized before sending emails.")
        return []

    try:
        with open(registry_file, 'r', encoding='utf-8') as f:
            registry_data = json.load(f)

        # Parse branch entries from JSON structure
        for branch in registry_data.get("branches", []):
            branch_name = branch.get("name", "")
            path = branch.get("path", "")

            if not branch_name or not path:
                continue

            # Derive email address from branch name
            # AIPASS.admin -> @admin
            # AIPASS Workshop -> @aipass
            # AIPASS-HELP -> @help (use second part to avoid collision)
            # BACKUP-SYSTEM -> @backup
            # DRONE -> @drone
            if '.' in branch_name:
                # Special case: AIPASS.admin -> admin
                email_part = branch_name.split('.')[-1].lower()
            elif ' ' in branch_name:
                # Handle spaces: take first word
                email_part = branch_name.split()[0].lower()
            elif '-' in branch_name and branch_name.split('-')[0] == 'AIPASS':
                # AIPASS-prefixed branches: use second part to avoid collision with "AIPASS Workshop"
                email_part = branch_name.split('-', 1)[1].lower()
            else:
                # Take first word before hyphen or whole name
                email_part = branch_name.split('-')[0].lower()

            email = f"@{email_part}"

            branches.append({
                "name": branch_name,
                "path": path,
                "email": email
            })

        # COLLISION DETECTION: Check for duplicate email addresses
        email_map = {}
        collisions = []
        for branch in branches:
            if branch["email"] in email_map:
                # Collision detected
                collision_msg = f"Email collision: {branch['email']} used by both '{email_map[branch['email']]}' and '{branch['name']}'"
                collisions.append(collision_msg)
                logger.error(f"[{MODULE_NAME}] {collision_msg}")
            else:
                email_map[branch["email"]] = branch["name"]

        if collisions:
            logger.error(f"[{MODULE_NAME}] ⚠️ CRITICAL: {len(collisions)} email address collision(s) detected!")
            logger.error(f"[{MODULE_NAME}] One or more branches will be unreachable via AI_Mail")
            logger.error(f"[{MODULE_NAME}] Fix: Rename branches in BRANCH_REGISTRY.json to ensure unique email derivation")
            for collision in collisions:
                logger.error(f"[{MODULE_NAME}]   - {collision}")

        logger.info(f"[{MODULE_NAME}] Loaded {len(branches)} branches from registry ({len(email_map)} unique emails)")
        return branches

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to read branch registry: {e}")
        return []

# =============================================
# EMAIL FILE MANAGEMENT
# =============================================

def create_email_file(to_branch: str, subject: str, message: str, user_info: Dict) -> Path:
    """
    Create email file and save to sent folder.

    Returns: Path to created email file
    """
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime(user_info.get("timestamp_format", "%Y-%m-%d %H:%M:%S"))

    # Create email data structure
    email_data = {
        "from": user_info["email_address"],
        "from_name": user_info["display_name"],
        "to": to_branch,
        "subject": subject,
        "message": message,
        "timestamp": timestamp_str,
        "status": "sent"
    }

    # Create filename (safe, no special chars)
    safe_subject = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in subject)
    safe_subject = safe_subject[:50].strip()  # Limit length
    filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{safe_subject}.json"

    # Save to sent folder
    mailbox_path = Path(user_info["mailbox_path"])
    sent_folder = mailbox_path / "sent"
    sent_folder.mkdir(parents=True, exist_ok=True)

    email_file = sent_folder / filename
    with open(email_file, 'w', encoding='utf-8') as f:
        json.dump(email_data, f, indent=2)

    logger.info(f"[{MODULE_NAME}] Email saved to sent: {email_file}")
    return email_file

def deliver_email_to_branch(to_branch: str, email_data: Dict) -> Tuple[bool, str]:
    """
    Deliver email to target branch's ai_mail.local/inbox.json file.

    Appends message to inbox JSON messages array.

    Returns: (success: bool, error_message: str) - error_message is empty string if successful
    """
    import uuid

    # Map email address to branch path
    branches = {b["email"]: b["path"] for b in get_all_branches()}

    if to_branch not in branches:
        error_msg = f"Unknown branch email: {to_branch}"
        logger.error(f"[{MODULE_NAME}] {error_msg}")
        return False, error_msg

    branch_path = Path(branches[to_branch])

    # Find the branch's ai_mail.local/inbox.json file
    # Pattern: /path/ai_mail.local/inbox.json
    # Special case: root is /ai_mail.local/inbox.json
    if branch_path == Path("/"):
        inbox_file = Path("/ai_mail.local/inbox.json")
    else:
        inbox_file = branch_path / "ai_mail.local" / "inbox.json"

    if not inbox_file.exists():
        error_msg = f"AI_Mail not installed (missing: {inbox_file})"
        logger.warning(f"[{MODULE_NAME}] Inbox file not found: {inbox_file}")
        return False, error_msg

    # Load current inbox
    try:
        with open(inbox_file, 'r', encoding='utf-8') as f:
            inbox_data = json.load(f)
    except Exception as e:
        error_msg = f"Failed to read inbox: {e}"
        logger.error(f"[{MODULE_NAME}] {error_msg}")
        return False, error_msg

    # Create message object
    message = {
        "id": str(uuid.uuid4())[:8],  # Short unique ID
        "timestamp": email_data['timestamp'],
        "from": email_data['from'],
        "from_name": email_data['from_name'],
        "subject": email_data['subject'],
        "message": email_data['message'],
        "read": False
    }

    # Append message to inbox
    inbox_data["messages"].append(message)
    inbox_data["total_messages"] = len(inbox_data["messages"])
    inbox_data["unread_count"] = sum(1 for msg in inbox_data["messages"] if not msg.get("read", False))

    # Save updated inbox
    try:
        with open(inbox_file, 'w', encoding='utf-8') as f:
            json.dump(inbox_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        error_msg = f"Failed to write inbox: {e}"
        logger.error(f"[{MODULE_NAME}] {error_msg}")
        return False, error_msg

    logger.info(f"[{MODULE_NAME}] Email delivered to {to_branch} at {inbox_file}")
    return True, ""

# =============================================
# COMMAND HANDLERS
# =============================================

def send_email_interactive():
    """Interactive email sending with prompts"""
    branches = get_all_branches()

    print("\n📧 AI_Mail - Send Email")
    print("=" * 50)

    # Show branch selection
    print("\nSelect recipient:")
    for i, branch in enumerate(branches, 1):
        print(f"  {i}. {branch['name']} ({branch['email']})")
    print(f"  {len(branches) + 1}. ALL BRANCHES (broadcast to everyone)")

    # Get selection
    try:
        selection = input("\nPick (1-{}): ".format(len(branches) + 1)).strip()
        idx = int(selection) - 1

        # Check for "all branches" selection
        if idx == len(branches):
            selected_branch = {"name": "ALL BRANCHES", "email": "all"}
        elif idx < 0 or idx >= len(branches):
            print("❌ Invalid selection")
            return False
        else:
            selected_branch = branches[idx]
    except (ValueError, KeyboardInterrupt, EOFError):
        print("\n❌ Cancelled")
        return False

    # Get subject
    try:
        subject = input("Subject: ").strip()
        if not subject:
            print("❌ Subject cannot be empty")
            return False
    except (KeyboardInterrupt, EOFError):
        print("\n❌ Cancelled")
        return False

    # Get message
    print("Message (press Ctrl+D when done, Ctrl+C to cancel):")
    try:
        message_lines = []
        while True:
            try:
                line = input()
                message_lines.append(line)
            except EOFError:
                break
        message = "\n".join(message_lines).strip()
        if not message:
            print("❌ Message cannot be empty")
            return False
    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        return False

    # Confirm send
    print("\n" + "=" * 50)
    print(f"To: {selected_branch['name']} ({selected_branch['email']})")
    print(f"Subject: {subject}")
    print(f"Message:\n{message}")
    print("=" * 50)

    try:
        confirm = input("\nSend? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return False
    except (KeyboardInterrupt, EOFError):
        print("\n❌ Cancelled")
        return False

    # Send email
    return send_email_direct(selected_branch['email'], subject, message)

def send_email_direct(to_branch: str, subject: str, message: str) -> bool:
    """Direct email sending (one-liner, AI-friendly). Supports broadcast to 'all'."""
    try:
        user_info = get_current_user()

        # Handle broadcast to all branches
        if to_branch.lower() in ['all', '@all']:
            branches = get_all_branches()
            success_count = 0
            failed_branches = []

            # Save ONE email to sent folder showing broadcast to "all"
            email_file = create_email_file("all", subject, message, user_info)

            print(f"\n📢 Broadcasting to {len(branches)} branches...")

            # Create email data for delivery (from the saved broadcast email)
            with open(email_file, 'r', encoding='utf-8') as f:
                broadcast_email_data = json.load(f)

            # Deliver to each branch
            for branch in branches:
                # Update recipient for each delivery
                email_data = broadcast_email_data.copy()
                email_data['to'] = branch['email']

                success, error_msg = deliver_email_to_branch(branch['email'], email_data)
                if success:
                    success_count += 1
                    print(f"  ✅ {branch['name']}")
                else:
                    failed_branches.append(branch['name'])
                    print(f"  ❌ {branch['name']} ({error_msg})")

            # Summary
            print(f"\n📊 Broadcast complete: {success_count}/{len(branches)} delivered")
            if failed_branches:
                print(f"⚠️  Failed: {', '.join(failed_branches)}")

            logger.info(f"[{MODULE_NAME}] Broadcast sent to {success_count}/{len(branches)} branches: {subject}")
            return success_count > 0

        # Single recipient
        else:
            # Create and save email file
            email_file = create_email_file(to_branch, subject, message, user_info)

            # Deliver to branch
            with open(email_file, 'r', encoding='utf-8') as f:
                email_data = json.load(f)

            success, error_msg = deliver_email_to_branch(to_branch, email_data)

            if success:
                print(f"✅ Email sent to {to_branch}")
                logger.info(f"[{MODULE_NAME}] Email sent to {to_branch}: {subject}")
                return True
            else:
                print(f"❌ Failed to deliver email to {to_branch}: {error_msg}")
                return False

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to send email: {e}")
        print(f"❌ Error: {e}")
        return False

def view_inbox():
    """View inbox messages from inbox.json - interactive"""
    user_info = get_current_user()
    mailbox_path = Path(user_info["mailbox_path"])
    inbox_file = mailbox_path / "inbox.json"

    if not inbox_file.exists():
        print("📭 Inbox is empty")
        return

    # Load inbox
    with open(inbox_file, 'r', encoding='utf-8') as f:
        inbox_data = json.load(f)

    messages = inbox_data.get("messages", [])

    if not messages:
        print("📭 Inbox is empty")
        return

    while True:
        # Reload messages (in case deleted)
        with open(inbox_file, 'r', encoding='utf-8') as f:
            inbox_data = json.load(f)
        messages = inbox_data.get("messages", [])

        if not messages:
            print("\n📭 Inbox is empty")
            return

        # Show email list (newest first)
        messages_display = list(reversed(messages))[:20]  # Last 20, newest first

        print("\n📬 Inbox")
        print("=" * 70)

        for i, msg in enumerate(messages_display, 1):
            unread_marker = "📨" if not msg.get("read", False) else "📬"
            print(f"\n{i}. {unread_marker} [{msg['timestamp']}] From: {msg['from_name']}")
            print(f"   Subject: {msg['subject']}")
            preview = msg['message'][:100] + "..." if len(msg['message']) > 100 else msg['message']
            print(f"   {preview}")

        print("\n" + "=" * 70)
        print(f"Showing {len(messages_display)} of {len(messages)} messages")

        # Get selection
        try:
            selection = input("\nSelect email (1-{}, or 'q' to quit): ".format(len(messages_display))).strip().lower()

            if selection == 'q':
                return

            idx = int(selection) - 1
            if idx < 0 or idx >= len(messages_display):
                print("❌ Invalid selection")
                continue

            # Get selected message
            selected_msg = messages_display[idx]
            msg_id = selected_msg["id"]

            # Mark as read
            for msg in messages:
                if msg["id"] == msg_id:
                    msg["read"] = True
                    break

            # Display full email
            print("\n" + "=" * 70)
            print(f"From: {selected_msg['from_name']} ({selected_msg['from']})")
            print(f"Date: {selected_msg['timestamp']}")
            print(f"Subject: {selected_msg['subject']}")
            print("=" * 70)
            print(f"\n{selected_msg['message']}\n")
            print("=" * 70)

            # Actions menu
            action = input("\nActions: (r)eply, (d)elete, (q)uit: ").strip().lower()

            if action == 'r':
                # Reply to email
                reply_subject = f"Re: {selected_msg['subject']}"
                print(f"\n📧 Reply to {selected_msg['from_name']}")
                print(f"Subject: {reply_subject}")
                print("Message (press Ctrl+D when done, Ctrl+C to cancel):")

                try:
                    message_lines = []
                    while True:
                        try:
                            line = input()
                            message_lines.append(line)
                        except EOFError:
                            break
                    reply_message = "\n".join(message_lines).strip()

                    if reply_message:
                        send_email_direct(selected_msg['from'], reply_subject, reply_message)
                        print("✅ Reply sent!")
                    else:
                        print("❌ Reply cancelled (empty message)")
                except KeyboardInterrupt:
                    print("\n❌ Reply cancelled")

            elif action == 'd':
                # Delete email - move to deleted.json
                confirm = input(f"Delete this email? (y/n): ").strip().lower()
                if confirm == 'y':
                    # Remove from inbox
                    messages = [msg for msg in messages if msg["id"] != msg_id]
                    inbox_data["messages"] = messages
                    inbox_data["total_messages"] = len(messages)
                    inbox_data["unread_count"] = sum(1 for msg in messages if not msg.get("read", False))

                    # Save updated inbox
                    with open(inbox_file, 'w', encoding='utf-8') as f:
                        json.dump(inbox_data, f, indent=2, ensure_ascii=False)

                    # Move to deleted
                    deleted_file = mailbox_path / "deleted.json"
                    if deleted_file.exists():
                        with open(deleted_file, 'r', encoding='utf-8') as f:
                            deleted_data = json.load(f)
                    else:
                        deleted_data = {"mailbox": "deleted", "total_messages": 0, "messages": []}

                    deleted_data["messages"].append(selected_msg)
                    deleted_data["total_messages"] = len(deleted_data["messages"])

                    with open(deleted_file, 'w', encoding='utf-8') as f:
                        json.dump(deleted_data, f, indent=2, ensure_ascii=False)

                    print("✅ Email deleted")
                else:
                    print("❌ Delete cancelled")

            elif action == 'q':
                continue  # Back to inbox list

        except (ValueError, KeyboardInterrupt, EOFError):
            print("\n❌ Cancelled")
            return
        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Error in inbox: {e}")
            print(f"❌ Error: {e}")
            return

def check_collisions():
    """Check for email address collisions in branch registry"""
    print("\n🔍 AI_Mail Address Collision Check")
    print("=" * 70)

    branches = get_all_branches()

    # Build email map and detect collisions
    email_map = {}
    collisions = []

    for branch in branches:
        if branch["email"] in email_map:
            collisions.append({
                "email": branch["email"],
                "branch1": email_map[branch["email"]],
                "branch2": branch["name"]
            })
        else:
            email_map[branch["email"]] = branch["name"]

    # Display results
    print(f"\n📊 Registry Status:")
    print(f"   Total Branches: {len(branches)}")
    print(f"   Unique Emails: {len(email_map)}")

    if collisions:
        print(f"\n⚠️  COLLISIONS DETECTED: {len(collisions)}")
        print("\nOne or more branches are unreachable via AI_Mail!")
        print("\nCollisions:")
        for collision in collisions:
            print(f"\n   {collision['email']}")
            print(f"      ❌ {collision['branch1']}")
            print(f"      ❌ {collision['branch2']}")
            print(f"      → Only '{email_map[collision['email']]}' is reachable")

        print("\n💡 Fix: Rename branches in /CLAUDE.md to ensure unique email derivation")
        print("   See naming guidelines at top of /CLAUDE.md")
        return 1
    else:
        print("\n✅ No collisions detected - all branches reachable!")
        print("\nBranch → Email Mapping:")
        for branch in sorted(branches, key=lambda b: b["email"]):
            print(f"   {branch['email']:15} → {branch['name']}")
        return 0

def contacts_list():
    """
    List all contacts from /CLAUDE.md registry (AI-friendly, non-interactive)

    Output format:
        Total: N branches
        @email | Branch Name | Path | Description
    """
    branches = get_all_branches()

    if not branches:
        print("❌ No contacts found in registry")
        logger.error(f"[{MODULE_NAME}] Failed to load contacts from /CLAUDE.md")
        return 1

    # Read full branch info from BRANCH_REGISTRY.json for descriptions
    import json
    registry_file = Path("/home/aipass/BRANCH_REGISTRY.json")
    branch_descriptions = {}

    try:
        with open(registry_file, 'r', encoding='utf-8') as f:
            registry_data = json.load(f)

        # Extract descriptions from JSON structure (if available)
        for branch in registry_data.get("branches", []):
            branch_name = branch.get("name", "")
            description = branch.get("description", "")  # May not exist in current JSON

            if branch_name:
                branch_descriptions[branch_name] = description if description else "No description"

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to read descriptions from registry: {e}")

    # Print AI-friendly output (no decorative elements, pure data)
    print(f"Total: {len(branches)} branches\n")

    # Print header
    print(f"{'EMAIL':<20} {'BRANCH NAME':<25} {'PATH':<35} DESCRIPTION")
    print("-" * 140)

    # Print contacts sorted by email
    for branch in sorted(branches, key=lambda b: b["email"]):
        email = branch["email"]
        name = branch["name"]
        path = branch["path"]
        description = branch_descriptions.get(name, "No description")

        # Truncate long descriptions to fit terminal
        if len(description) > 55:
            description = description[:52] + "..."

        print(f"{email:<20} {name:<25} {path:<35} {description}")

    logger.info(f"[{MODULE_NAME}] Listed {len(branches)} contacts")
    return 0

def contacts_add(branch_name: str | None = None, branch_path: str | None = None, description: str | None = None):
    """
    Add a new contact to /CLAUDE.md registry

    Args:
        branch_name: Name of branch (e.g., "AI_MAIL", "DRONE")
        branch_path: Full path to branch (e.g., "/home/aipass/ai_mail")
        description: 15-word description of branch purpose

    If called without args, attempts auto-detection from current directory.

    TODO: This function needs JSON rewrite for new registry format
    """
    registry_file = Path("/home/aipass/BRANCH_REGISTRY.json")

    # Auto-detection mode if no args provided
    if not branch_name or not branch_path:
        try:
            # Detect from current working directory
            cwd = Path.cwd()

            # Determine branch path and name
            if cwd == Path("/"):
                auto_branch_path = "/"
                auto_branch_name = "AIPASS.admin"
            else:
                auto_branch_path = str(cwd)
                auto_branch_name = cwd.name.replace("-", "_").replace("_", "-").upper()

            # Ask for description if not provided
            if not description:
                print(f"\n📝 Auto-detected branch:")
                print(f"   Name: {auto_branch_name}")
                print(f"   Path: {auto_branch_path}")
                print("\nEnter 15-word description of branch purpose:")
                try:
                    description = input("> ").strip()
                    if not description:
                        print("❌ Description cannot be empty")
                        return 1
                except (KeyboardInterrupt, EOFError):
                    print("\n❌ Cancelled")
                    return 1

            branch_name = auto_branch_name
            branch_path = auto_branch_path

        except Exception as e:
            logger.error(f"[{MODULE_NAME}] Auto-detection failed: {e}")
            print(f"❌ Auto-detection failed: {e}")
            print("\nUsage: contacts add <branch_name> <branch_path> <description>")
            return 1

    # Validate inputs
    if not branch_name or not branch_path or not description:
        print("❌ Error: All fields required (branch_name, branch_path, description)")
        print("Usage: contacts add <branch_name> <branch_path> <description>")
        return 1

    # Check if registry exists
    if not registry_file.exists():
        logger.error(f"[{MODULE_NAME}] Registry not found: {registry_file}")
        print(f"❌ Registry not found: {registry_file}")
        return 1

    # Read current registry
    try:
        with open(registry_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to read registry: {e}")
        print(f"❌ Failed to read registry: {e}")
        return 1

    # Check if branch already exists
    if f"[{branch_path}] {branch_name}:" in content:
        print(f"⚠️  Branch already registered: {branch_name} at {branch_path}")
        logger.warning(f"[{MODULE_NAME}] Branch already exists: {branch_name}")
        return 1

    # Determine which section to add to
    section_header = None
    if branch_path == "/":
        section_header = "### System Level"
    elif branch_path.startswith("/home/aipass/"):
        section_header = "### Workshop Modules"
    elif branch_path.startswith("/home/aipass-business/"):
        section_header = "### Business Operations"
    elif branch_path.startswith("/home/input-x/"):
        section_header = "### Experimental (Input-X)"
    else:
        print(f"❌ Unknown branch location: {branch_path}")
        print("Branch must be in /, /home/aipass/, /home/aipass-business/, or /home/input-x/")
        return 1

    # Find the section and add the branch
    if section_header not in content:
        logger.error(f"[{MODULE_NAME}] Section not found: {section_header}")
        print(f"❌ Section not found in registry: {section_header}")
        return 1

    # Find the next section or end marker to insert before
    lines = content.split('\n')
    insert_index = None
    in_target_section = False

    for i, line in enumerate(lines):
        if line.strip() == section_header:
            in_target_section = True
            continue

        if in_target_section:
            # Stop at next ### header or ## header
            if line.startswith('###') or (line.startswith('##') and not line.startswith('###')):
                insert_index = i
                break

    # If no next section found, insert before "## Branch Statistics" or end
    if insert_index is None:
        for i, line in enumerate(lines):
            if line.strip() == "## Branch Statistics" or line.strip() == "## AI_Mail Addresses":
                insert_index = i
                break

    # Fallback: insert at end
    if insert_index is None:
        insert_index = len(lines)

    # Determine entry number for Workshop Modules
    entry_prefix = ""
    if section_header == "### Workshop Modules":
        # Count existing entries
        count = 0
        in_workshop = False
        for line in lines:
            if line.strip() == "### Workshop Modules":
                in_workshop = True
                continue
            if in_workshop and (line.startswith('###') or line.startswith('##')):
                break
            if in_workshop and re.match(r'^\d+\.', line.strip()):
                count += 1

        # Skip the first entry (AIPASS Workshop at #1)
        entry_prefix = f"{count + 1}. "
    elif section_header == "### System Level":
        entry_prefix = "- "

    # Format new entry
    new_entry = f"{entry_prefix}[{branch_path}] {branch_name}: {description}"

    # Insert the new entry
    lines.insert(insert_index, new_entry)

    # Update branch count
    updated_content = '\n'.join(lines)

    # Find and update "Total Active Branches" count
    branches_before = len(get_all_branches())
    branches_count_pattern = r'- Total Active Branches: (\d+)'
    match = re.search(branches_count_pattern, updated_content)
    if match:
        updated_content = re.sub(branches_count_pattern, f'- Total Active Branches: {branches_before + 1}', updated_content)

    # Write back to registry
    try:
        with open(registry_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"✅ Contact added to registry:")
        print(f"   Branch: {branch_name}")
        print(f"   Path: {branch_path}")
        print(f"   Description: {description}")

        # Show derived email address
        branches = get_all_branches()
        for branch in branches:
            if branch["name"] == branch_name and branch["path"] == branch_path:
                print(f"   Email: {branch['email']}")
                break

        logger.info(f"[{MODULE_NAME}] Contact added: {branch_name} at {branch_path}")
        return 0

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Failed to write registry: {e}")
        print(f"❌ Failed to update registry: {e}")
        return 1

def view_sent():
    """View sent messages"""
    user_info = get_current_user()
    mailbox_path = Path(user_info["mailbox_path"])
    sent_folder = mailbox_path / "sent"

    if not sent_folder.exists():
        print("📭 No sent messages")
        return

    # Get all email files
    email_files = sorted(sent_folder.glob("*.json"), reverse=True)  # Newest first

    if not email_files:
        print("📭 No sent messages")
        return

    print("\n📤 Sent Messages")
    print("=" * 70)

    for i, email_file in enumerate(email_files[:20], 1):  # Show last 20
        with open(email_file, 'r', encoding='utf-8') as f:
            email_data = json.load(f)

        print(f"\n{i}. [{email_data['timestamp']}] To: {email_data['to']}")
        print(f"   Subject: {email_data['subject']}")
        print(f"   {email_data['message'][:100]}..." if len(email_data['message']) > 100 else f"   {email_data['message']}")

    print("\n" + "=" * 70)
    print(f"Showing {len(email_files[:20])} of {len(email_files)} messages")

# =============================================
# CLI SETUP
# =============================================

def main():
    parser = argparse.ArgumentParser(
        description='AI_Mail CLI - Human-friendly email interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: send, inbox, sent, check, contacts

DESCRIPTION:
  send              - Send email (interactive or direct)
  inbox             - View inbox messages
  sent              - View sent messages
  check             - Check for email address collisions in registry
  contacts list     - List all contacts from registry (AI-friendly)
  contacts add      - Add new contact to registry (auto-detects from cwd)

EXAMPLES:
  # Interactive send (prompts for recipient, subject, message)
  python3 ai_mail_cli.py send

  # Direct send (one-liner, AI-friendly)
  python3 ai_mail_cli.py send @admin "Subject" "Message here"

  # View inbox
  python3 ai_mail_cli.py inbox

  # View sent messages
  python3 ai_mail_cli.py sent

  # List all contacts (AI-friendly output)
  python3 ai_mail_cli.py contacts list

  # Add contact (auto-detect from current directory)
  python3 ai_mail_cli.py contacts add

  # Add contact (manual)
  python3 ai_mail_cli.py contacts add "BRANCH-NAME" "/path/to/branch" "Description here"

BRANCH EMAIL ADDRESSES:
  @admin       - AIPass Admin (/)
  @flow        - Flow System
  @drone       - Drone System
  @ai_mail     - AI_Mail System
  @backup      - Backup System
        """
    )

    parser.add_argument('command',
                       nargs='?',
                       default='send',
                       choices=['send', 'inbox', 'sent', 'check', 'contacts'],
                       help='Command to execute')

    parser.add_argument('subcommand',
                       nargs='?',
                       help='Subcommand (for contacts: list, add)')

    parser.add_argument('arg1',
                       nargs='?',
                       help='First argument (to_branch for send, branch_name for contacts add)')

    parser.add_argument('arg2',
                       nargs='?',
                       help='Second argument (subject for send, branch_path for contacts add)')

    parser.add_argument('arg3',
                       nargs='?',
                       help='Third argument (message for send, description for contacts add)')

    args = parser.parse_args()

    # Handle commands
    if args.command == 'inbox':
        view_inbox()
        sys.exit(0)

    if args.command == 'sent':
        view_sent()
        sys.exit(0)

    if args.command == 'check':
        sys.exit(check_collisions())

    # Contacts command
    if args.command == 'contacts':
        if not args.subcommand:
            print("❌ Error: contacts command requires subcommand (list or add)")
            print("Usage: python3 ai_mail_cli.py contacts list")
            print("       python3 ai_mail_cli.py contacts add [branch_name] [path] [description]")
            sys.exit(1)

        if args.subcommand == 'list':
            sys.exit(contacts_list())

        elif args.subcommand == 'add':
            # contacts add [branch_name] [path] [description]
            # If no args, auto-detect from cwd
            sys.exit(contacts_add(args.arg1, args.arg2, args.arg3))

        else:
            print(f"❌ Error: Unknown subcommand '{args.subcommand}'")
            print("Available subcommands: list, add")
            sys.exit(1)

    # Send command
    if args.command == 'send':
        # Direct send mode (if arg1/to_branch provided)
        if args.arg1:
            if not args.arg2 or not args.arg3:
                print("❌ Error: Direct send requires to_branch, subject, and message")
                print("Example: python3 ai_mail_cli.py send @admin \"Subject\" \"Message\"")
                sys.exit(1)

            success = send_email_direct(args.arg1, args.arg2, args.arg3)
            sys.exit(0 if success else 1)

        # Interactive send mode
        else:
            success = send_email_interactive()
            sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()