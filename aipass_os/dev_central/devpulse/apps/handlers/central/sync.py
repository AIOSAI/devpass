#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: sync.py - Branch Sync Handler
# Date: 2025-11-24
# Version: 0.1.0
# Category: aipass/handlers/central
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-24): Initial handler - README sync operations
#
# CODE STANDARDS:
#   - Handler implements business logic, no CLI output
#   - Pure functions with proper error handling
#   - Type hints, docstrings, logger import
# =============================================

"""
Branch Sync Handler

Business logic for syncing branch content to central files.
Handles README aggregation and cross-branch syncing.

Domain: Central coordination
"""

import json
from pathlib import Path
from typing import Dict
from datetime import datetime
import os

# Infrastructure
AIPASS_ROOT = Path.home()


def sync_readmes() -> Dict:
    """
    Sync branch README summaries to readme.central.md

    Scans all registered branches for README files and compiles
    them into a central readme.central.md file with collapsible sections.

    Returns:
        Dict with keys:
            - status: str ("success" or error state)
            - branches_synced: int
            - timestamp: str (ISO format)
            - details: str (optional error details)

    Raises:
        FileNotFoundError: If BRANCH_REGISTRY.json missing
        ValueError: If registry data invalid
        RuntimeError: If sync operation fails
    """
    try:
        # Load branch registry
        registry_path = AIPASS_ROOT / "BRANCH_REGISTRY.json"
        if not registry_path.exists():
            raise FileNotFoundError(f"Branch registry not found: {registry_path}")

        registry_data = json.loads(registry_path.read_text(encoding='utf-8'))

        branches = registry_data.get("branches", [])
        if not branches:
            raise ValueError("No branches found in registry")

        # Sort branches alphabetically by name
        branches_sorted = sorted(branches, key=lambda b: b.get("name", "").lower())

        # Prepare output
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_path = AIPASS_ROOT / "aipass_os" / "dev_central" / "readme.central.md"

        # Build markdown content
        sections = []
        branches_synced = 0

        for branch in branches_sorted:
            branch_name = branch.get("name", "")
            branch_path = Path(branch.get("path", ""))

            if not branch_name or not branch_path:
                continue

            readme_path = branch_path / "README.md"

            if not readme_path.exists():
                continue

            # Read README content
            readme_content = readme_path.read_text(encoding='utf-8')

            # Get file modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(readme_path))
            mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")

            # Build collapsible section
            # Create anchor ID from branch name (lowercase, replace spaces/special chars)
            anchor_id = branch_name.lower().replace("_", "-").replace(" ", "-")

            section = f'''<details id="{anchor_id}">
<summary><strong>{branch_name}</strong></summary>

**Source:** [README.md](vscode://file{readme_path})
**Last Modified:** {mod_time_str}

{readme_content}

</details>
'''
            sections.append(section)
            branches_synced += 1

        # Build full document
        total_in_registry = len(branches)
        header = f'''# readme.central.md - AIPass Branch Documentation
```
Search Root: /home/aipass
Output: /home/aipass/aipass_os/dev_central/readme.central.md
Last Sync: {timestamp}
Branches: {branches_synced}/{total_in_registry}
```

**Purpose:** Aggregated view of all branch README files.
**Source:** Auto-generated from branch README.md files.
**Usage:** Run sync to update this overview.

---
## BRANCH DOCUMENTATION

'''

        full_content = header + "\n".join(sections)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write output file
        output_path.write_text(full_content, encoding='utf-8')

        return {
            "status": "success",
            "branches_synced": branches_synced,
            "timestamp": datetime.now().isoformat()
        }

    except FileNotFoundError:
        raise

    except ValueError:
        raise

    except Exception as e:
        raise RuntimeError(f"README sync failed: {e}") from e


def sync_notepads() -> Dict:
    """
    Sync branch notepad.md files to notepad.central.md

    Scans all registered branches for notepad.md files and compiles
    them into a central notepad.central.md file with collapsible sections.

    Returns:
        Dict with keys:
            - status: str ("success" or error state)
            - branches_synced: int
            - timestamp: str (ISO format)
    """
    try:
        # Load branch registry
        registry_path = AIPASS_ROOT / "BRANCH_REGISTRY.json"
        if not registry_path.exists():
            raise FileNotFoundError(f"Branch registry not found: {registry_path}")

        registry_data = json.loads(registry_path.read_text(encoding='utf-8'))

        branches = registry_data.get("branches", [])
        if not branches:
            raise ValueError("No branches found in registry")

        # Sort branches alphabetically by name
        branches_sorted = sorted(branches, key=lambda b: b.get("name", "").lower())

        # Prepare output
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_path = AIPASS_ROOT / "aipass_os" / "dev_central" / "notepad.central.md"

        # Build markdown content
        sections = []
        branches_synced = 0

        for branch in branches_sorted:
            branch_name = branch.get("name", "")
            branch_path = Path(branch.get("path", ""))

            if not branch_name or not branch_path:
                continue

            notepad_path = branch_path / "notepad.md"

            if not notepad_path.exists():
                continue

            # Read notepad content
            notepad_content = notepad_path.read_text(encoding='utf-8')

            # Get file modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(notepad_path))
            mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")

            # Build collapsible section
            anchor_id = branch_name.lower().replace("_", "-").replace(" ", "-")

            section = f'''<details id="{anchor_id}">
<summary><strong>{branch_name}</strong></summary>

**Source:** [notepad.md](vscode://file{notepad_path})
**Last Modified:** {mod_time_str}

{notepad_content}

</details>
'''
            sections.append(section)
            branches_synced += 1

        # Build full document
        total_in_registry = len(branches)
        header = f'''# notepad.central.md - AIPass Branch Notepads
```
Search Root: /home/aipass
Output: /home/aipass/aipass_os/dev_central/notepad.central.md
Last Sync: {timestamp}
Branches: {branches_synced}/{total_in_registry}
```

**Purpose:** Aggregated view of all branch notepad.md files.
**Source:** Auto-generated from branch notepad.md files.
**Usage:** Run sync to update this overview.

---
## BRANCH NOTEPADS

'''

        full_content = header + "\n".join(sections)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write output file
        output_path.write_text(full_content, encoding='utf-8')

        return {
            "status": "success",
            "branches_synced": branches_synced,
            "timestamp": datetime.now().isoformat()
        }

    except FileNotFoundError:
        raise

    except ValueError:
        raise

    except Exception as e:
        raise RuntimeError(f"Notepad sync failed: {e}") from e


def sync_plans() -> Dict:
    """
    Sync PLANS.central.json to plans_central.md

    Reads the JSON and converts to markdown with collapsible sections per branch.

    Returns:
        Dict with keys:
            - status: str ("success" or error state)
            - active_count: int
            - closed_count: int
            - timestamp: str (ISO format)
    """
    try:
        # Load plans central JSON
        plans_json = AIPASS_ROOT / "aipass_os" / "AI_CENTRAL" / "PLANS.central.json"
        if not plans_json.exists():
            raise FileNotFoundError(f"Plans central not found: {plans_json}")

        plans_data = json.loads(plans_json.read_text(encoding='utf-8'))

        # Prepare output
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_path = AIPASS_ROOT / "aipass_os" / "dev_central" / "plans_central.md"

        # Get statistics
        stats = plans_data.get("global_statistics", {})
        active_count = stats.get("total_active", 0)
        closed_count = stats.get("total_closed", 0)
        branches_reporting = stats.get("branches_reporting", 0)

        # Build sections
        sections = []

        # Active Plans section
        active_plans = plans_data.get("active_plans", [])
        if active_plans:
            active_section = "## Active Plans\n\n"
            for plan in active_plans:
                plan_id = plan.get("plan_id", "")
                subject = plan.get("subject", "")
                branch = plan.get("branch", "")
                created = plan.get("created", "")[:10] if plan.get("created") else ""
                file_path = plan.get("file_path", "")
                active_section += f"- **{plan_id}** ({branch}): {subject}\n"
                active_section += f"  - Created: {created} | [Open](vscode://file{file_path})\n"
            sections.append(active_section)
        else:
            sections.append("## Active Plans\n\n*No active plans*\n")

        # Per-branch breakdown with dropdowns
        branches = plans_data.get("branches", {})
        if branches:
            branch_section = "## Branch Details\n\n"
            for branch_key in sorted(branches.keys()):
                branch_data = branches[branch_key]
                branch_name = branch_data.get("branch_name", branch_key.upper())
                branch_active = branch_data.get("active_plans", [])
                branch_closed = branch_data.get("recently_closed", [])
                branch_stats = branch_data.get("statistics", {})

                anchor_id = branch_key.lower().replace("_", "-")

                branch_section += f'''<details id="{anchor_id}">
<summary><strong>{branch_name}</strong> (Active: {branch_stats.get("active_count", 0)}, Closed: {branch_stats.get("total_closed", 0)})</summary>

'''
                if branch_active:
                    branch_section += "**Active:**\n"
                    for plan in branch_active:
                        branch_section += f"- {plan.get('plan_id')}: {plan.get('subject')}\n"
                    branch_section += "\n"

                if branch_closed:
                    branch_section += "**Recently Closed:**\n"
                    for plan in branch_closed:
                        closed_date = plan.get("closed", "")[:10] if plan.get("closed") else ""
                        branch_section += f"- {plan.get('plan_id')}: {plan.get('subject')} ({closed_date})\n"
                    branch_section += "\n"

                if not branch_active and not branch_closed:
                    branch_section += "*No plans*\n\n"

                branch_section += "</details>\n\n"

            sections.append(branch_section)

        # Build full document
        header = f'''# plans_central.md - AIPass Plan Overview
```
Source: /home/aipass/aipass_os/AI_CENTRAL/PLANS.central.json
Output: /home/aipass/aipass_os/dev_central/plans_central.md
Last Sync: {timestamp}
Active: {active_count} | Closed: {closed_count} | Branches: {branches_reporting}
```

**Purpose:** Aggregated view of all branch plans.
**Source:** Auto-generated from PLANS.central.json.
**Usage:** Run sync to update this overview.

---
'''

        full_content = header + "\n".join(sections)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write output file
        output_path.write_text(full_content, encoding='utf-8')

        return {
            "status": "success",
            "active_count": active_count,
            "closed_count": closed_count,
            "timestamp": datetime.now().isoformat()
        }

    except FileNotFoundError:
        raise

    except Exception as e:
        raise RuntimeError(f"Plans sync failed: {e}") from e
