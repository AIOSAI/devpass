#!/usr/bin/env python3
"""
Claude JSON MCP Cleaner
Removes MCP server configuration from .claude.json to prevent corruption.
Use this once, then manage all MCP servers via .mcp.json file.
"""

import json
import shutil
import sys
from pathlib import Path

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# CLI services
from cli.apps.modules import console

def clean_claude_json(claude_json_path: str, project_path: str):
    """Clean MCP configuration from .claude.json for specified project"""

    claude_path = Path(claude_json_path)

    if not claude_path.exists():
        console.print(f"❌ {claude_json_path} not found")
        return False

    # Create backup
    backup_path = claude_path.with_suffix('.json.backup')
    shutil.copy2(claude_path, backup_path)
    console.print(f"✅ Backup created: {backup_path}")

    try:
        # Load current configuration
        with open(claude_path, 'r') as f:
            data = json.load(f)

        # Clean project MCP settings
        if 'projects' in data and project_path in data['projects']:
            project = data['projects'][project_path]

            # Clear MCP-related fields
            mcp_fields = [
                'mcpServers',
                'enabledMcpjsonServers',
                'disabledMcpjsonServers',
                'mcpContextUris'
            ]

            cleared_fields = []
            for field in mcp_fields:
                if field in project and project[field]:
                    project[field] = {} if field == 'mcpServers' else []
                    cleared_fields.append(field)

            # Save cleaned configuration
            with open(claude_path, 'w') as f:
                json.dump(data, f, indent=2)

            if cleared_fields:
                console.print(f"✅ Cleared MCP fields: {', '.join(cleared_fields)}")
                console.print(f"✅ {claude_json_path} cleaned for project {project_path}")
                console.print("📝 All MCP servers should now be managed via .mcp.json")
            else:
                console.print("ℹ️  No MCP configuration found to clean")

        else:
            console.print(f"ℹ️  Project {project_path} not found in configuration")

        return True

    except json.JSONDecodeError as e:
        console.print(f"❌ JSON parsing error: {e}")
        console.print(f"🔧 Backup available at: {backup_path}")
        return False
    except Exception as e:
        console.print(f"❌ Error: {e}")
        console.print(f"🔧 Backup available at: {backup_path}")
        return False

def main():
    """Main execution"""

    # Default paths
    claude_json = "/home/aipass/.claude.json"
    project_path = "/home/aipass"

    # Allow custom paths via arguments
    if len(sys.argv) >= 2:
        claude_json = sys.argv[1]
    if len(sys.argv) >= 3:
        project_path = sys.argv[2]

    console.print("🧹 Claude JSON MCP Cleaner")
    console.print("=" * 40)
    console.print(f"Target file: {claude_json}")
    console.print(f"Project path: {project_path}")
    console.print()

    success = clean_claude_json(claude_json, project_path)

    if success:
        console.print()
        console.print("🎉 Setup complete!")
        console.print("📋 Next steps:")
        console.print("   1. Verify .mcp.json exists in project root")
        console.print("   2. Test: claude mcp list")
        console.print("   3. Manage MCP servers by editing .mcp.json directly")
        console.print("   4. Never manually edit .claude.json again")

        # Check if .mcp.json exists
        mcp_json = Path(project_path) / ".mcp.json"
        if mcp_json.exists():
            console.print(f"✅ Found .mcp.json at {mcp_json}")
        else:
            console.print(f"⚠️  .mcp.json not found at {mcp_json}")
            console.print("   Create it or rename existing mcp.json to .mcp.json")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())