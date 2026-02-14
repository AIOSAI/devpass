#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: branch_ping.py - Memory Health Monitor Ping
# Date: 2025-10-23
# Version: 1.0.0
# Category: ai_mail
#
# CHANGELOG:
#   - v1.0.0 (2025-10-23): Initial implementation - branch startup memory health check
# =============================================

"""
Branch Memory Health Ping Script

Called by branches on startup to:
1. Count lines in local.md and observations.md
2. Update visual health indicators in file headers
3. Ping registry with current status

Lightweight - reads only headers, counts lines, updates indicators.
Monitor reads these indicators instead of processing full 600-line files.
"""

# =============================================
# IMPORTS
# =============================================
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# =============================================
# CONSTANTS & CONFIG
# =============================================
# AI_Mail paths (independent branch as of 2025-10-26)
AIPASS_ROOT = Path.home() / "aipass_core"
AI_MAIL_ROOT = AIPASS_ROOT / "ai_mail"
AI_MAIL_JSON = AI_MAIL_ROOT / "ai_mail_json"
REGISTRY_PATH = AI_MAIL_JSON / "local_memory_monitor_registry.json"
THRESHOLDS = {
    "green": (0, 400),
    "yellow": (401, 550),
    "red": (551, float('inf'))
}

# =============================================
# HELPER FUNCTIONS
# =============================================
def get_branch_context():
    """Determine current branch name and directory"""
    cwd = Path.cwd()

    # Special case: root directory
    if cwd == Path("/"):
        return "AIPASS.admin", cwd

    # Extract branch name from last directory in path
    branch_folder = cwd.name.replace("-", "_")
    branch_name = branch_folder.upper()

    return branch_name, cwd

def count_file_lines(file_path):
    """Count total lines in file"""
    if not file_path.exists():
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        return len(f.readlines())

def get_status_from_count(line_count):
    """Determine status based on line count"""
    if THRESHOLDS["green"][0] <= line_count <= THRESHOLDS["green"][1]:
        return "green"
    elif THRESHOLDS["yellow"][0] <= line_count <= THRESHOLDS["yellow"][1]:
        return "yellow"
    else:  # red threshold
        return "red"

def ping_registry(branch_name, cwd, local_status, obs_status):
    """Update registry with branch status"""
    # Ensure registry directory exists
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load or create registry
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    else:
        registry = {
            "last_updated": "",
            "active_branches": {},
            "statistics": {
                "total_branches": 0,
                "green_status": 0,
                "yellow_status": 0,
                "red_status": 0
            }
        }

    # Update branch entry
    registry["active_branches"][str(cwd)] = {
        "branch_name": branch_name,
        "last_ping": datetime.now().isoformat(),
        "local_md": local_status,
        "observations_md": obs_status
    }

    # Update statistics
    registry["last_updated"] = datetime.now().isoformat()
    registry["statistics"]["total_branches"] = len(registry["active_branches"])

    # Count statuses
    green, yellow, red = 0, 0, 0
    for branch_data in registry["active_branches"].values():
        for file_type in ["local_md", "observations_md"]:
            status = branch_data[file_type]["status"]
            if status == "green":
                green += 1
            elif status == "yellow":
                yellow += 1
            elif status == "red":
                red += 1

    registry["statistics"]["green_status"] = green
    registry["statistics"]["yellow_status"] = yellow
    registry["statistics"]["red_status"] = red

    # Save registry
    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)

    return True

def update_json_memory_health(file_path, line_count, status_code):
    """Update memory_health in JSON file metadata"""
    if not file_path.exists():
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Update memory health in metadata
        if "metadata" in data and "memory_health" in data["metadata"]:
            data["metadata"]["memory_health"]["current_lines"] = line_count
            data["metadata"]["memory_health"]["status"] = status_code

            # Save updated file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
    except Exception:
        return False

    return False

def handle_ping(args):
    """Execute ping command - JSON memory files only"""
    try:
        # Get branch context
        branch_name, cwd = get_branch_context()

        # JSON file paths
        local_file = cwd / f"{branch_name}.local.json"
        obs_file = cwd / f"{branch_name}.observations.json"

        # Count lines
        local_count = count_file_lines(local_file)
        obs_count = count_file_lines(obs_file)

        # Get statuses
        local_status_code = get_status_from_count(local_count)
        obs_status_code = get_status_from_count(obs_count)

        # Update JSON memory health
        update_json_memory_health(local_file, local_count, local_status_code)
        update_json_memory_health(obs_file, obs_count, obs_status_code)

        # Prepare status data
        local_status = {
            "line_count": local_count,
            "status": local_status_code
        }

        obs_status = {
            "line_count": obs_count,
            "status": obs_status_code
        }

        # Ping registry
        ping_registry(branch_name, cwd, local_status, obs_status)

        if args.verbose:
            print(f"✓ Ping successful for {branch_name}")
            print(f"  local.json: {local_count} lines ({local_status_code})")
            print(f"  observations.json: {obs_count} lines ({obs_status_code})")

        return 0

    except Exception as e:
        if args.verbose:
            print(f"✗ Ping failed: {e}")
        return 1

def handle_status(args):
    """Show current memory health status"""
    try:
        branch_name, cwd = get_branch_context()
        local_md = cwd / f"{branch_name}.local.md"
        observations_md = cwd / f"{branch_name}.observations.md"

        local_count = count_file_lines(local_md)
        obs_count = count_file_lines(observations_md)

        local_status_code, local_status_emoji = get_status_from_count(local_count)
        obs_status_code, obs_status_emoji = get_status_from_count(obs_count)

        print(f"Branch: {branch_name}")
        print(f"Directory: {cwd}")
        print(f"\nMemory Health Status:")
        print(f"  local.md:         {local_status_emoji} ({local_count}/600 lines)")
        print(f"  observations.md:  {obs_status_emoji} ({obs_count}/600 lines)")
        
        return 0

    except Exception as e:
        print(f"Error getting status: {e}", file=sys.stderr)
        return 1

def handle_registry(args):
    """View registry contents"""
    try:
        if not REGISTRY_PATH.exists():
            print("Registry not yet created")
            return 0

        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)

        print("Memory Health Registry")
        print(f"Last Updated: {registry.get('last_updated', 'N/A')}")
        print(f"\nStatistics:")
        stats = registry.get('statistics', {})
        print(f"  Total Branches: {stats.get('total_branches', 0)}")
        print(f"  🟢 Green:  {stats.get('green_status', 0)}")
        print(f"  🟡 Yellow: {stats.get('yellow_status', 0)}")
        print(f"  🔴 Red:    {stats.get('red_status', 0)}")

        if args.detailed:
            print(f"\nActive Branches:")
            for path, data in registry.get('active_branches', {}).items():
                print(f"\n  {data.get('branch_name', 'Unknown')} ({path})")
                print(f"    Last Ping: {data.get('last_ping', 'N/A')}")
                local = data.get('local_md', {})
                obs = data.get('observations_md', {})
                print(f"    local.md:        {local.get('line_count', 0)} lines ({local.get('status', 'unknown')})")
                print(f"    observations.md: {obs.get('line_count', 0)} lines ({obs.get('status', 'unknown')})")

        return 0

    except Exception as e:
        print(f"Error reading registry: {e}", file=sys.stderr)
        return 1

def handle_thresholds(args):
    """Show compression thresholds"""
    print("Memory Compression Thresholds:")
    print(f"  🟢 Green:  0 - {THRESHOLDS['green'][1]} lines")
    print(f"  🟡 Yellow: {THRESHOLDS['yellow'][0]} - {THRESHOLDS['yellow'][1]} lines")
    print(f"  🔴 Red:    {THRESHOLDS['red'][0]}+ lines (compression required)")
    return 0

# =============================================
# MAIN FUNCTIONS
# =============================================
def main():
    """Main execution with CLI support"""
    parser = argparse.ArgumentParser(
        description='Branch Memory Health Monitor Ping - Startup memory health check for branches',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: ping, status, registry, thresholds, --verbose, --detailed

  ping       - Execute memory health ping and update registry (default)
  status     - Show current memory health status for this branch
  registry   - View registry contents and statistics
  thresholds - Display compression thresholds

OPTIONS:
  --verbose  - Show detailed output (used with ping)
  --detailed - Show detailed registry information (used with registry)

EXAMPLES:
  python3 branch_ping.py
  python3 branch_ping.py ping --verbose
  python3 branch_ping.py status
  python3 branch_ping.py registry
  python3 branch_ping.py registry --detailed
  python3 branch_ping.py thresholds
        """
    )

    parser.add_argument('command',
                       nargs='?',
                       choices=['ping', 'status', 'registry', 'thresholds'],
                       default='ping',
                       help='Command to execute (default: ping)')

    parser.add_argument('--verbose',
                       action='store_true',
                       help='Show detailed output for ping command')

    parser.add_argument('--detailed',
                       action='store_true',
                       help='Show detailed information for registry command')

    args = parser.parse_args()

    # Route to command handlers
    if args.command == 'ping':
        return handle_ping(args)
    elif args.command == 'status':
        return handle_status(args)
    elif args.command == 'registry':
        return handle_registry(args)
    elif args.command == 'thresholds':
        return handle_thresholds(args)
    else:
        parser.print_help()
        return 0

# =============================================
# CLI/EXECUTION
# =============================================
if __name__ == "__main__":
    sys.exit(main())