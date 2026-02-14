#!/usr/bin/env python3
"""
Fix all .mcp.json files to use --project . (current directory)
This makes Serena auto-detect the project from the local .serena/project.yml
"""

import json
import sys
from pathlib import Path

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# CLI services
from cli.apps.modules import console


def fix_mcp_json(mcp_json_path: Path) -> bool:
    """Fix a single .mcp.json file to use --project ."""

    try:
        with open(mcp_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check if serena server exists
        if "mcpServers" not in data or "serena" not in data["mcpServers"]:
            return False

        serena = data["mcpServers"]["serena"]
        args = serena.get("args", [])

        # Find and update --project argument
        modified = False
        if "--project" in args:
            # Find index of --project
            idx = args.index("--project")
            if idx + 1 < len(args):
                old_value = args[idx + 1]
                if old_value != ".":
                    args[idx + 1] = "."
                    modified = True
                    console.print(f"  Updated: --project {old_value} → --project .")
        else:
            # Add --project . after start-mcp-server
            if "start-mcp-server" in args:
                idx = args.index("start-mcp-server")
                args.insert(idx + 1, "--project")
                args.insert(idx + 2, ".")
                modified = True
                console.print(f"  Added: --project .")

        if modified:
            serena["args"] = args
            with open(mcp_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        else:
            console.print(f"  No changes needed")
            return False

    except Exception as e:
        console.print(f"  ❌ Error: {e}")
        return False


def main():
    """Main execution"""

    # Find all .mcp.json files
    root = Path("/home/aipass")
    skip_patterns = [
        ".local/share/Trash",
        "backups/",
        ".backup/",
        ".archive/",
        "crash-logs/",
    ]

    mcp_jsons = []
    for mcp_json in root.rglob(".mcp.json"):
        # Skip excluded patterns
        if any(pattern in str(mcp_json) for pattern in skip_patterns):
            continue
        mcp_jsons.append(mcp_json)

    if not mcp_jsons:
        console.print("❌ No .mcp.json files found")
        return 1

    console.print(f"🔍 Found {len(mcp_jsons)} .mcp.json file(s)\n")

    modified_count = 0
    for mcp_json in sorted(mcp_jsons):
        console.print(f"📁 {mcp_json.parent}")
        if fix_mcp_json(mcp_json):
            modified_count += 1
        console.print()

    console.print(f"✅ Modified {modified_count} file(s)")
    console.print("⚠️  Restart Claude Code to apply changes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
