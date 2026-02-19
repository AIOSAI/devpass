#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: central_writer.py - DEVPULSE Central File Writer
# Date: 2025-11-27
# Version: 0.2.0
# Category: devpulse/handlers
#
# CHANGELOG (Max 5 entries):
#   - v0.2.0 (2026-02-18): Slim to 2 sections (Issues + Todos) per FPLAN-0355
#   - v0.1.0 (2025-11-27): Initial implementation - central file writer
#
# CONNECTS:
#   - dev_local/ops.py (section validation - must match sections here)
#   - cortex template (branch generation - NOT owned by devpulse)
#   - template/ops.py (dev status compliance)
#
# CODE STANDARDS:
#   - Handler tier 3: pure functions, raises exceptions
#   - No Prax imports (handler tier 3)
#   - No CLI imports or logger calls
# =============================================

"""
DEVPULSE Central File Writer Handler

Provides functionality to update DEVPULSE.central.json with branch summaries.
This is DEVPULSE's "API output" - AIPASS reads it to populate dashboards.

Handler tier 3: Pure functions that raise exceptions for modules to catch.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import re
import sys

# Avoid conflict with local json handler package
# Import stdlib json directly from its location
import importlib.util
_json_spec = importlib.util.find_spec('json', package=None)
# Filter out any handlers path from the spec's submodule search locations
if _json_spec and _json_spec.origin:
    # Ensure we get stdlib json, not local handlers/json
    _stdlib_json_path = None
    for path in sys.path:
        if 'handlers' not in path:
            potential_json = Path(path) / 'json.py'
            if potential_json.exists():
                _stdlib_json_path = str(potential_json)
                break

    # Fallback: use standard import with cleaned sys.modules
    if 'json' in sys.modules and hasattr(sys.modules['json'], 'dump'):
        _json = sys.modules['json']
    else:
        # Remove any cached json module that's not stdlib
        if 'json' in sys.modules:
            del sys.modules['json']
        # Import with explicit path exclusion
        _original_path = sys.path.copy()
        sys.path = [p for p in sys.path if 'handlers' not in p]
        import json as _json
        sys.path = _original_path
else:
    import json as _json


# Constants
AIPASS_ROOT = Path.home()
CENTRAL_FILE = AIPASS_ROOT / "aipass_os" / "AI_CENTRAL" / "DEVPULSE.central.json"


def _count_section_items(content: str, section_name: str) -> int:
    """
    Count non-empty items in a markdown section.

    Args:
        content: Markdown file content
        section_name: Name of section (e.g., "Notes", "Issues")

    Returns:
        Count of non-empty items in section

    Raises:
        ValueError: If section format is invalid
    """
    # Find section header (case insensitive)
    section_pattern = rf'^## {section_name}\s*$'
    lines = content.split('\n')

    section_start = None
    for i, line in enumerate(lines):
        if re.match(section_pattern, line, re.IGNORECASE):
            section_start = i
            break

    if section_start is None:
        return 0

    # Count items until next section or end
    count = 0
    for i in range(section_start + 1, len(lines)):
        line = lines[i].strip()

        # Stop at next section header
        if line.startswith('## '):
            break

        # Skip separators and empty lines
        if line in ['---', ''] or not line:
            continue

        # Count bullet points or dated entries
        if line.startswith('-') or re.match(r'^\[[\d-]+ [\d:]+\]', line):
            # Only count if not just a dash
            if line.strip() != '-':
                count += 1

    return count


def _read_dev_file(branch_path: Path) -> Optional[str]:
    """
    Read dev.local.md file for a branch.

    Args:
        branch_path: Path to branch directory

    Returns:
        File content or None if file doesn't exist

    Raises:
        IOError: If file exists but cannot be read
    """
    dev_file = branch_path / "dev.local.md"

    if not dev_file.exists():
        return None

    try:
        with open(dev_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Failed to read {dev_file}: {e}")


def _get_branch_summary(branch_path: Path) -> Dict[str, int]:
    """
    Get summary counts for a branch's dev.local.md.

    Args:
        branch_path: Path to branch directory

    Returns:
        Dictionary with counts: {"notes": N, "issues": N, "todos": N, "ideas": N}

    Raises:
        IOError: If file cannot be read
        ValueError: If file format is invalid
    """
    content = _read_dev_file(branch_path)

    if content is None:
        return {"issues": 0, "todos": 0}

    try:
        return {
            "issues": _count_section_items(content, "Issues"),
            "todos": _count_section_items(content, "Todos")
        }
    except Exception as e:
        raise ValueError(f"Failed to parse dev.local.md at {branch_path}: {e}")


def _discover_branches() -> List[Tuple[str, Path]]:
    """
    Discover all branches that have dev.local.md files.

    Searches in:
    - /home/aipass (root level branches)
    - /home/aipass/aipass_core/* (core services)
    - /home/aipass/aipass_os/* (OS services)

    Returns:
        List of tuples: [(branch_name, branch_path), ...]

    Raises:
        IOError: If directory traversal fails
    """
    branches = []

    try:
        # Root level branches
        for item in AIPASS_ROOT.iterdir():
            if item.is_dir() and (item / "dev.local.md").exists():
                # Use uppercase directory name as branch name
                branches.append((item.name.upper(), item))

        # Core services
        core_dir = AIPASS_ROOT / "aipass_core"
        if core_dir.exists():
            for item in core_dir.iterdir():
                if item.is_dir() and (item / "dev.local.md").exists():
                    branches.append((item.name.upper(), item))

        # OS services
        os_dir = AIPASS_ROOT / "aipass_os"
        if os_dir.exists():
            for item in os_dir.iterdir():
                if item.is_dir() and (item / "dev.local.md").exists():
                    branches.append((item.name.upper(), item))

        return sorted(branches, key=lambda x: x[0])

    except Exception as e:
        raise IOError(f"Failed to discover branches: {e}")


def update_central() -> Dict[str, Any]:
    """
    Update DEVPULSE.central.json with current branch summaries.

    This is the main handler function that:
    1. Discovers all branches with dev.local.md files
    2. Counts notes/issues/todos/ideas in each branch
    3. Writes summary to DEVPULSE.central.json

    Returns:
        Dictionary with update results:
        {
            "success": True,
            "branches_processed": 5,
            "timestamp": "2025-11-27T12:00:00",
            "file_path": "/home/aipass/aipass_os/AI_CENTRAL/DEVPULSE.central.json"
        }

    Raises:
        IOError: If file operations fail
        ValueError: If data validation fails
        PermissionError: If cannot write to central file
    """
    # Discover branches
    branches = _discover_branches()

    # Build summaries
    branch_summaries = {}
    for branch_name, branch_path in branches:
        try:
            summary = _get_branch_summary(branch_path)
            # Only include branches that have content
            if any(summary.values()):
                branch_summaries[branch_name] = summary
        except Exception as e:
            # Re-raise with branch context
            raise ValueError(f"Failed to process branch {branch_name}: {e}")

    # Build central data structure
    timestamp = datetime.now().isoformat()
    central_data = {
        "service": "devpulse",
        "last_updated": timestamp,
        "branch_summaries": branch_summaries
    }

    # Ensure parent directory exists
    CENTRAL_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write to central file
    try:
        with open(CENTRAL_FILE, 'w', encoding='utf-8') as f:
            _json.dump(central_data, f, indent=2, ensure_ascii=False)
    except PermissionError as e:
        raise PermissionError(f"Cannot write to {CENTRAL_FILE}: {e}")
    except Exception as e:
        raise IOError(f"Failed to write central file: {e}")

    # Return success result
    return {
        "success": True,
        "branches_processed": len(branch_summaries),
        "timestamp": timestamp,
        "file_path": str(CENTRAL_FILE)
    }


def get_central_data() -> Dict[str, Any]:
    """
    Read current DEVPULSE.central.json data.

    Returns:
        Dictionary with central file data

    Raises:
        FileNotFoundError: If central file doesn't exist
        ValueError: If JSON is invalid
    """
    if not CENTRAL_FILE.exists():
        raise FileNotFoundError(f"Central file not found: {CENTRAL_FILE}")

    try:
        with open(CENTRAL_FILE, 'r', encoding='utf-8') as f:
            return _json.load(f)
    except _json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in central file: {e}")
    except Exception as e:
        raise IOError(f"Failed to read central file: {e}")


if __name__ == "__main__":
    # Test implementation
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    console.print()
    console.print(Panel.fit(
        "[bold cyan]DEVPULSE CENTRAL WRITER - Test Run[/bold cyan]",
        border_style="bright_blue"
    ))
    console.print()

    try:
        result = update_central()
        console.print("[green]✓ Success![/green]")
        console.print(f"  Branches processed: {result['branches_processed']}")
        console.print(f"  Timestamp: {result['timestamp']}")
        console.print(f"  File: {result['file_path']}")
        console.print()

        # Show summary
        data = get_central_data()
        console.print("[yellow]Branch Summaries:[/yellow]")
        for branch, summary in data['branch_summaries'].items():
            console.print(f"  [cyan]{branch}[/cyan]:")
            for key, value in summary.items():
                if value > 0:
                    console.print(f"    {key}: {value}")
        console.print()

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print()
