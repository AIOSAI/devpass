#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""
META:
  app: Nexus
  layer: apps
  purpose: Drone command handler for @nexus
  status: Active
"""

import sys
import json
import argparse
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

NEXUS_DIR = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    """Load a JSON file, return empty dict on failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _load_json_list(path: Path) -> list:
    """Load a JSON file as list, return empty list on failure."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _is_nexus_running() -> bool:
    """Check if a nexus.py process is running (not this drone app)."""
    import subprocess
    try:
        result = subprocess.run(
            ["pgrep", "-f", "python.*nexus\\.py"],
            capture_output=True, text=True, timeout=5
        )
        # Filter out this process itself
        pids = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
        import os
        own_pid = str(os.getpid())
        other_pids = [p for p in pids if p != own_pid]
        return len(other_pids) > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> bool:
    """Show Nexus operational status."""
    # Pulse data
    pulse_path = NEXUS_DIR / "data" / "pulse.json"
    pulse = _load_json(pulse_path)
    tick = pulse.get("current_tick", "?")
    sessions = pulse.get("total_sessions", "?")

    # Knowledge count
    kb_path = NEXUS_DIR / "data" / "knowledge_base.json"
    kb = _load_json_list(kb_path)

    # Summaries count
    sum_path = NEXUS_DIR / "data" / "session_summaries.json"
    summaries = _load_json_list(sum_path)

    # Skills count
    skills_dir = NEXUS_DIR / "handlers" / "skills"
    skill_count = 0
    if skills_dir.exists():
        for f in skills_dir.glob("*.py"):
            if not f.name.startswith("_") and f.name != "__init__.py":
                skill_count += 1

    # Running check
    running = _is_nexus_running()

    print("Nexus Status")
    print(f"  Pulse tick:     {tick}")
    print(f"  Sessions:       {sessions}")
    print(f"  Knowledge:      {len(kb)} entries")
    print(f"  Summaries:      {len(summaries)} stored")
    print(f"  Skills:         {skill_count} discovered")
    print(f"  Process:        {'running' if running else 'stopped'}")
    return True


def cmd_info(args: argparse.Namespace) -> bool:
    """Show Nexus identity and personality info."""
    # Identity
    id_path = NEXUS_DIR / "NEXUS.id.json"
    identity = _load_json(id_path)
    branch_info = identity.get("branch_info", {})
    ident = identity.get("identity", {})
    style = ident.get("working_style", {})

    # Profile modules
    profile_path = NEXUS_DIR / "config" / "profile.json"
    profile = _load_json(profile_path)
    core_mods = [m.get("name") for m in profile.get("core", {}).get("modules", [])]
    ext_mods = [m.get("name") for m in profile.get("modules", [])]
    all_mods = core_mods + ext_mods

    print("Nexus Identity")
    print(f"  Name:           {branch_info.get('branch_name', 'NEXUS')}")
    print(f"  Email:          {branch_info.get('email', '@nexus')}")
    print(f"  Role:           {ident.get('role', 'N/A')}")
    print(f"  Philosophy:     {style.get('mode', 'N/A')}")
    print(f"  Personality:    {profile.get('personality', 'N/A')}")
    if all_mods:
        print(f"  Modules:        {', '.join(all_mods)}")
    return True


# ---------------------------------------------------------------------------
# Main (drone entry point)
# ---------------------------------------------------------------------------

COMMANDS = {
    "status": cmd_status,
    "info": cmd_info,
}


def main():
    """Entry point for drone @nexus commands."""
    parser = argparse.ArgumentParser(
        description="Nexus - AIPass CoFounder and Conversational AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", nargs="?", help="Command to execute (status, info)")

    args = parser.parse_args()

    # No command: show introspection
    if not args.command:
        print("Nexus - AIPass CoFounder and Conversational AI")
        print()
        print("Available commands:")
        for name in COMMANDS:
            print(f"  {name}")
        print()
        print("Usage: drone @nexus <command>")
        return 0

    # Route command
    handler = COMMANDS.get(args.command)
    if handler:
        handler(args)
        return 0

    print(f"Unknown command: {args.command}")
    print(f"Available: {', '.join(COMMANDS.keys())}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
