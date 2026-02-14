#!/usr/bin/env python3
"""
Identity Injector - Injects branch identity (branch_info + identity) on every prompt.

Reads from [BRANCH].id.json and outputs the core identity fields.
Works at any directory level - finds the branch root and loads its identity.

Version: 1.0.0
Created: 2025-11-27
"""
import json
from pathlib import Path

AIPASS_ROOT = Path.home()


def find_branch_root() -> Path | None:
    """Find the branch root directory. Returns AIPASS_ROOT if at root level."""
    cwd = Path.cwd()

    # If at AIPASS root, that IS the branch
    if cwd == AIPASS_ROOT:
        return AIPASS_ROOT

    # Search upward for branch indicators
    search_path = cwd
    while search_path >= AIPASS_ROOT:
        has_apps = (search_path / "apps").is_dir()
        has_id = list(search_path.glob("*.id.json"))

        if has_apps or has_id:
            return search_path

        if search_path == AIPASS_ROOT:
            return AIPASS_ROOT

        search_path = search_path.parent

    return AIPASS_ROOT


def find_id_file(branch_root: Path) -> Path | None:
    """Find the id.json file for a branch."""
    id_files = list(branch_root.glob("*.id.json"))
    if id_files:
        return id_files[0]
    return None


def format_identity(data: dict) -> str:
    """Format branch_info + identity for injection."""
    lines = []

    # Branch info
    branch = data.get("branch_info", {})
    name = branch.get("branch_name", "UNKNOWN")
    lines.append(f"# {name} Identity")
    lines.append(f"Path: {branch.get('path', 'unknown')}")
    lines.append(f"Email: {branch.get('email', 'unknown')}")

    # Identity
    identity = data.get("identity", {})
    if identity.get("role"):
        lines.append(f"Role: {identity['role']}")
    if identity.get("traits"):
        lines.append(f"Traits: {identity['traits']}")
    if identity.get("purpose"):
        lines.append(f"Purpose: {identity['purpose']}")

    # What I do (condensed)
    what_i_do = identity.get("what_i_do", [])
    if what_i_do:
        lines.append("Do: " + " | ".join(what_i_do[:4]))  # First 4, condensed

    # What I don't do (condensed)
    what_i_dont_do = identity.get("what_i_dont_do", [])
    if what_i_dont_do:
        lines.append("Don't: " + " | ".join(what_i_dont_do[:3]))  # First 3

    # Principles (just list)
    principles = data.get("principles", [])
    if principles:
        lines.append("Principles: " + " • ".join(principles))

    return "\n".join(lines)


def main():
    branch_root = find_branch_root()
    if not branch_root:
        return

    id_file = find_id_file(branch_root)
    if not id_file or not id_file.exists():
        return

    try:
        data = json.loads(id_file.read_text())
        output = format_identity(data)
        if output:
            print(f"\n{output}")
    except (json.JSONDecodeError, KeyError):
        pass  # Silent fail - don't break the prompt


if __name__ == "__main__":
    main()
