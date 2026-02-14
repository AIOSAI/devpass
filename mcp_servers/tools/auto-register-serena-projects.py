#!/usr/bin/env python3
"""
Serena Project Auto-Registration
Scans for .mcp.json files and auto-registers those directories as Serena projects.

Logic:
- Find all directories containing .mcp.json
- Create .serena/project.yml if missing (using directory name as project name)
- Update ~/.serena/serena_config.yml projects list
"""

import sys
from pathlib import Path
import yaml

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# CLI services
from cli.apps.modules import console


def find_mcp_projects(root_path: Path) -> list[Path]:
    """Find all directories containing .mcp.json"""
    projects = []

    # Paths to skip
    skip_patterns = [
        ".local/share/Trash",
        "backups/",
        ".backup/",
        ".archive/",
        "crash-logs/",
    ]

    for mcp_json in root_path.rglob(".mcp.json"):
        project_dir = mcp_json.parent

        # Skip excluded patterns
        if any(pattern in str(project_dir) for pattern in skip_patterns):
            continue

        projects.append(project_dir)

    return sorted(projects)


def ensure_project_yml(project_dir: Path) -> bool:
    """Ensure .serena/project.yml exists in project directory"""
    serena_dir = project_dir / ".serena"
    project_yml = serena_dir / "project.yml"

    if project_yml.exists():
        console.print(f"  ✅ {project_yml.relative_to(project_dir)} exists")
        return True

    # Create .serena directory if needed
    serena_dir.mkdir(exist_ok=True)

    # Create basic project.yml
    project_name = project_dir.name
    config = {
        "language": "python",
        "ignore_all_files_in_gitignore": True,
        "ignored_paths": [],
        "read_only": False,
        "excluded_tools": [],
        "initial_prompt": "",
        "project_name": project_name
    }

    with open(project_yml, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print(f"  ✨ Created {project_yml.relative_to(project_dir)}")
    return True


def update_serena_config(projects: list[Path], serena_config_path: Path) -> None:
    """Update ~/.serena/serena_config.yml with discovered projects"""

    if not serena_config_path.exists():
        console.print(f"❌ Serena config not found: {serena_config_path}")
        return

    # Load current config
    with open(serena_config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Get current projects (if any)
    current_projects = set(config.get("projects", []))

    # Add new projects (as strings, not dicts)
    new_projects = {str(p.resolve()) for p in projects}

    # Update projects list
    all_projects = sorted(current_projects | new_projects)
    config["projects"] = all_projects

    # Write back
    with open(serena_config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print(f"\n✅ Updated {serena_config_path}")
    console.print(f"   Total projects: {len(all_projects)}")


def main():
    """Main execution"""

    # Scan root
    scan_root = Path("/home/aipass")
    if len(sys.argv) > 1:
        scan_root = Path(sys.argv[1])

    console.print(f"🔍 Scanning for .mcp.json files in: {scan_root}")
    console.print()

    # Find projects
    projects = find_mcp_projects(scan_root)

    if not projects:
        console.print("❌ No .mcp.json files found")
        return 1

    console.print(f"Found {len(projects)} project(s) with .mcp.json:\n")

    # Process each project
    for project_dir in projects:
        console.print(f"📁 {project_dir}")
        ensure_project_yml(project_dir)
        console.print()

    # Update Serena config
    serena_config = Path.home() / ".serena" / "serena_config.yml"
    update_serena_config(projects, serena_config)

    console.print("\n🎉 Project registration complete!")
    console.print("📋 Registered projects:")
    for p in projects:
        console.print(f"   - {p}")

    console.print("\n⚠️  Restart Claude Code to apply changes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
