#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: git_commands.py - Git Command Cheatsheet
# Date: 2025-10-30
# Version: 1.0.0
# Category: git_repo
#
# CHANGELOG (Max 5 entries - remove oldest when adding new):
#   - v1.0.0 (2025-10-30): Initial implementation - git cheatsheet printer
# =============================================

"""
Git Command Cheatsheet

Quick reference for common git commands. Just type 'drone git' to see the full list.
"""

# DRONE_COMMAND: git
# DESCRIPTION: git cheatsheet
# COMMAND: python3 {module_path}
# ARGS_OPTIONAL: category

# DRONE_COMMAND: git <category>
# DESCRIPTION: git category help
# COMMAND: python3 {module_path} {category}
# ARGS_REQUIRED: category

import argparse
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Initialize Rich console
console = Console()

# Configuration
SCRIPT_DIR = Path(__file__).resolve().parent.parent
CHEATSHEET_FILE = SCRIPT_DIR / "git_repo_json/git_cheatsheet.json"

def load_cheatsheet():
    """Load git cheatsheet from JSON"""
    try:
        with open(CHEATSHEET_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"❌ Error loading cheatsheet: {e}")
        sys.exit(1)

def print_all_commands():
    """Print all git commands organized by category"""
    data = load_cheatsheet()

    console.print("=" * 70)
    console.print("GIT COMMAND CHEATSHEET")
    console.print("=" * 70)
    console.print()

    # Print all categories
    for category, commands in data["common_commands"].items():
        console.print(f"{category}:")
        for cmd in commands:
            console.print(f"  {cmd}")
        console.print()

    # Print custom notes
    if data.get("custom_notes"):
        console.print("Notes:")
        for note in data["custom_notes"]:
            console.print(f"  {note}")
        console.print()

    console.print("=" * 70)
    console.print("💡 TIP: Use 'drone git <category>' for specific section")
    console.print("   Categories: status, basic, branch, undo, remote, stash, emergency")
    console.print("=" * 70)

def print_category(category_key):
    """Print commands for a specific category"""
    data = load_cheatsheet()

    # Match category key (flexible matching)
    category_map = {
        "status": "Status & Info",
        "info": "Status & Info",
        "basic": "Basic Operations",
        "branch": "Branching",
        "undo": "Undoing Changes",
        "remote": "Remote Operations",
        "stash": "Stashing",
        "emergency": "Emergency Fixes",
        "fix": "Emergency Fixes",
        "fav": "My Commands" #Patrick added this section for his favorite commands
    }

    full_category = category_map.get(category_key.lower())

    if not full_category or full_category not in data["common_commands"]:
        console.print(f"❌ Unknown category: {category_key}")
        console.print(f"Available: {', '.join(category_map.keys())}")
        sys.exit(1)

    console.print("=" * 70)
    console.print(f"GIT COMMANDS - {full_category}")
    console.print("=" * 70)
    console.print()

    for cmd in data["common_commands"][full_category]:
        console.print(f"  {cmd}")

    console.print()
    console.print("=" * 70)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Git Command Cheatsheet - Quick reference for common git commands',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: status, info, basic, branch, undo, remote, stash, emergency, fix, fav

CATEGORY REFERENCE:
  status      - Status & Info commands
  info        - Status & Info commands (alias)
  basic       - Basic Operations commands
  branch      - Branching commands
  undo        - Undoing Changes commands
  remote      - Remote Operations commands
  stash       - Stashing commands
  emergency   - Emergency Fixes commands
  fix         - Emergency Fixes commands (alias)
  fav         - My Commands (Patrick's favorite commands) 

EXAMPLES:
  python git_commands.py
  python git_commands.py status
  python git_commands.py branch
  python git_commands.py emergency
        """
    )

    parser.add_argument('category', nargs='?',
                       choices=['status', 'info', 'basic', 'branch', 'undo', 'remote', 'stash', 'emergency', 'fix', 'fav'],
                       help='Git command category to display')

    args = parser.parse_args()

    # Check if category specified
    if args.category:
        print_category(args.category)
    else:
        print_all_commands()

if __name__ == "__main__":
    main()