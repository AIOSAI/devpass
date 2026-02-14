#!/usr/bin/env python3
"""
Cleanup local MCP and Serena configs - go back to simple global setup
Removes all branch-specific .mcp.json and .serena/project.yml files
Keeps only the root /home/aipass global config
"""

import sys
from pathlib import Path

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# CLI services
from cli.apps.modules import console


def main():
    """Remove all local configs except root"""

    root = Path("/home/aipass")

    # Find all .mcp.json files EXCEPT root
    console.print("🧹 Cleaning up local .mcp.json files...\n")
    mcp_jsons = [f for f in root.rglob(".mcp.json") if f.parent != root]

    for mcp_json in mcp_jsons:
        try:
            mcp_json.unlink()
            console.print(f"  ❌ Deleted: {mcp_json.relative_to(root)}")
        except Exception as e:
            console.print(f"  ⚠️  Failed to delete {mcp_json.relative_to(root)}: {e}")

    console.print(f"\n✅ Removed {len(mcp_jsons)} local .mcp.json files\n")

    # Find all .serena/project.yml files EXCEPT root
    console.print("🧹 Cleaning up local .serena/project.yml files...\n")
    project_ymls = [f for f in root.rglob(".serena/project.yml") if f.parent.parent != root]

    for yml in project_ymls:
        try:
            yml.unlink()
            console.print(f"  ❌ Deleted: {yml.relative_to(root)}")
            # Remove .serena dir if empty
            serena_dir = yml.parent
            if serena_dir.exists() and not any(serena_dir.iterdir()):
                serena_dir.rmdir()
                console.print(f"  ❌ Removed empty: {serena_dir.relative_to(root)}")
        except Exception as e:
            console.print(f"  ⚠️  Failed to delete {yml.relative_to(root)}: {e}")

    console.print(f"\n✅ Removed {len(project_ymls)} local .serena/project.yml files\n")

    # Clear projects list in Serena config (keep only root)
    serena_config = Path.home() / ".serena" / "serena_config.yml"
    if serena_config.exists():
        import yaml

        with open(serena_config, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        config["projects"] = [str(root)]

        with open(serena_config, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        console.print(f"✅ Updated {serena_config}")
        console.print(f"   Projects: ['{root}']\n")

    console.print("🎉 Cleanup complete!")
    console.print("📋 Global config:")
    console.print(f"   - Root .mcp.json: {root}/.mcp.json")
    console.print(f"   - Root .serena/project.yml: {root}/.serena/project.yml")
    console.print(f"   - Serena config: {serena_config}")
    console.print("\n⚠️  Restart Claude Code to apply changes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
