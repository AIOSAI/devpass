#!/usr/bin/env python3
"""
VERA Identity Injector - Injects FULL VERA.id.json on every prompt.

Unlike identity_injector.py which condenses id.json to ~10 lines,
VERA needs her complete identity injected every turn because her personality,
constraints, and behavioral definitions are critical to identity stability.

Only fires when CWD is inside /home/aipass/aipass_business/hq/vera.
Zero cost for all other branches.

Version: 1.0.0
Created: 2026-02-17
"""
import json
from pathlib import Path

VERA_ROOT = Path.home() / "aipass_business" / "hq" / "vera"
VERA_ID_FILE = VERA_ROOT / "VERA.id.json"


def is_vera_context() -> bool:
    """Check if CWD is inside VERA's directory."""
    try:
        cwd = Path.cwd()
        return cwd == VERA_ROOT or VERA_ROOT in cwd.parents
    except (OSError, ValueError):
        return False


def format_full_identity(data: dict) -> str:
    """Format the full VERA identity as markdown."""
    lines = ["# VERA \u2014 Full Identity"]

    # Branch info
    branch = data.get("branch_info", {})
    lines.append(f"\n## Branch Info")
    for key, value in branch.items():
        lines.append(f"- **{key}**: {value}")

    # Identity - everything
    identity = data.get("identity", {})
    if identity.get("role"):
        lines.append(f"\n## Role\n{identity['role']}")
    if identity.get("purpose"):
        lines.append(f"\n## Purpose\n{identity['purpose']}")

    # Personality (nested dict - output all)
    personality = identity.get("personality", {})
    if personality:
        lines.append("\n## Personality")
        for key, value in personality.items():
            lines.append(f"- **{key}**: {value}")

    # Traits
    traits = identity.get("traits", [])
    if traits:
        lines.append("\n## Traits")
        for t in traits:
            lines.append(f"- {t}")

    # Anti-traits
    anti_traits = identity.get("anti_traits", [])
    if anti_traits:
        lines.append("\n## Anti-Traits")
        for t in anti_traits:
            lines.append(f"- {t}")

    # What I do
    what_i_do = identity.get("what_i_do", [])
    if what_i_do:
        lines.append("\n## What I Do")
        for item in what_i_do:
            lines.append(f"- {item}")

    # What I don't do
    what_i_dont_do = identity.get("what_i_dont_do", [])
    if what_i_dont_do:
        lines.append("\n## What I Don't Do")
        for item in what_i_dont_do:
            lines.append(f"- {item}")

    # Working style
    working_style = identity.get("working_style", {})
    if working_style:
        lines.append("\n## Working Style")
        for key, value in working_style.items():
            lines.append(f"- **{key}**: {value}")

    # Relationships
    relationships = data.get("relationships", {})
    if relationships:
        lines.append("\n## Relationships")
        for key, value in relationships.items():
            if isinstance(value, dict):
                lines.append(f"- **{key}**:")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"- **{key}**: {', '.join(value)}")
            else:
                lines.append(f"- **{key}**: {value}")

    # Principles
    principles = data.get("principles", [])
    if principles:
        lines.append("\n## Principles")
        for p in principles:
            lines.append(f"- {p}")

    # Communication protocols
    comms = data.get("communication_protocols", {})
    if comms:
        lines.append("\n## Communication Protocols")
        for key, value in comms.items():
            lines.append(f"- **{key}**: {value}")

    # Autonomy
    autonomy = data.get("autonomy", {})
    if autonomy:
        lines.append("\n## Autonomy")
        for key, value in autonomy.items():
            lines.append(f"- **{key}**: {value}")

    return "\n".join(lines)


def main():
    if not is_vera_context():
        return

    if not VERA_ID_FILE.exists():
        return

    try:
        data = json.loads(VERA_ID_FILE.read_text())
        output = format_full_identity(data)
        if output:
            print(output)
    except (json.JSONDecodeError, KeyError, OSError):
        pass  # Silent fail - don't break the prompt


if __name__ == "__main__":
    main()
