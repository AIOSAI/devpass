#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: ops.py - Dev.local.md Operations Handler
# Date: 2025-11-16
# Version: 1.1.0
# Category: Handler
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2026-02-18): Slim to 2 sections (Issues + Todos) per FPLAN-0355
#   - v1.0.0 (2025-11-16): Initial version - extracted from devpulse_dev_tracking.py
#
# CONNECTS:
#   - central_writer.py (section counting for DEVPULSE.central.json)
#   - cortex template (branch generation - NOT owned by devpulse)
#   - template/ops.py (dev status compliance)
#
# CODE STANDARDS:
#   - Handler independence: No module imports, only same-package imports allowed
#   - File size: < 300 lines ideal
#   - Auto-detection pattern for calling module
# =============================================

"""
Dev.local.md Operations Handler

Core operations for reading and writing to dev.local.md files.
Handler for DEVPULSE branch - manages development tracking markdown files.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Handler: no Prax logging - returns status to module

# =============================================================================
# SECTION ALIASES & VALIDATION
# =============================================================================

VALID_SECTIONS = ["Issues", "Todos"]

SECTION_ALIASES = {
    "issue": "Issues",
    "todo": "Todos",
}


def resolve_section_alias(section_name: str) -> tuple[str, bool]:
    """
    Resolve section aliases and validate section name.

    Args:
        section_name: User-provided section name

    Returns:
        Tuple of (resolved_name, is_valid)
    """
    # Exact match (case-insensitive)
    for valid in VALID_SECTIONS:
        if section_name.lower() == valid.lower():
            return (valid, True)

    # Alias match
    alias_key = section_name.lower()
    if alias_key in SECTION_ALIASES:
        return (SECTION_ALIASES[alias_key], True)

    return (section_name, False)


# =============================================================================
# FILE OPERATIONS
# =============================================================================

def find_dev_local_file(branch_path: Path) -> Optional[Path]:
    """
    Find dev.local.md in branch directory

    Args:
        branch_path: Path to branch directory

    Returns:
        Path to dev.local.md or None if not found
    """
    dev_file = branch_path / "dev.local.md"
    if not dev_file.exists():
        return None
    return dev_file


def resolve_branch(branch_arg: str) -> Optional[Path]:
    """
    Resolve @branch notation or path to absolute path

    DRONE ADAPTATION: DRONE now resolves @branch to full paths before passing to modules.
    This function handles both legacy @branch notation and new path-based arguments.

    Examples:
        @flow → /home/aipass/aipass_core/flow
        /home/aipass/aipass_core/flow → /home/aipass/aipass_core/flow (DRONE resolved)
        @drone → /home/aipass/aipass_core/drone
        @MEMORY_BANK → /home/aipass/MEMORY_BANK
        . → current working directory

    Args:
        branch_arg: Branch notation (@branch), full path (from DRONE), or .

    Returns:
        Resolved path or None if not found
    """
    if branch_arg == ".":
        return Path.cwd()

    # DRONE ADAPTATION: Handle paths that DRONE already resolved
    # If it's already a path (starts with /), use it directly
    if branch_arg.startswith("/"):
        branch_path = Path(branch_arg)
        if not branch_path.exists():
            return None
        return branch_path.resolve()

    # Legacy @branch notation (for direct calls)
    if branch_arg.startswith("@"):
        branch_name = branch_arg[1:]  # Remove @

        # Try aipass_core/ first (most branches)
        branch_path = AIPASS_ROOT / branch_name
        if branch_path.exists():
            return branch_path

        # Try home directory root (for branches like MEMORY_BANK, mcp_servers, etc.)
        home_branch_path = Path.home() / branch_name
        if home_branch_path.exists():
            return home_branch_path

        # Not found in either location
        return None

    # Treat as relative path
    branch_path = Path(branch_arg)
    if not branch_path.exists():
        return None
    return branch_path.resolve()


# =============================================================================
# SECTION OPERATIONS
# =============================================================================

def find_section(content: str, section_name: str) -> Optional[tuple[int, int]]:
    """
    Find section in markdown content

    Looks for:
    - ## Section
    - ## **Section**

    Args:
        content: Markdown content
        section_name: Section name to find

    Returns:
        Tuple of (start_line, end_line) or None if not found
    """
    lines = content.split('\n')
    start_line = None
    end_line = None

    # Find section header
    for i, line in enumerate(lines):
        # Match ## Section or ## **Section**
        if line.strip().startswith('##'):
            # Remove ##, **, and whitespace to get section name
            header_text = line.replace('#', '').replace('*', '').strip()
            if header_text.lower() == section_name.lower():
                start_line = i
                break

    if start_line is None:
        return None

    # Find end of section (next --- or end of file)
    for i in range(start_line + 1, len(lines)):
        if lines[i].strip() == '---':
            end_line = i
            break

    if end_line is None:
        end_line = len(lines)

    return (start_line, end_line)


def append_to_section(content: str, section_name: str, entry: str) -> Optional[str]:
    """
    Append entry to section before the --- separator

    Args:
        content: Markdown content
        section_name: Section name
        entry: Entry text to append

    Returns:
        Updated content or None if section not found
    """
    section_bounds = find_section(content, section_name)
    if section_bounds is None:
        return None

    start_line, end_line = section_bounds
    lines = content.split('\n')

    # Insert before --- separator (or at end of section)
    insert_pos = end_line

    # Add the entry
    lines.insert(insert_pos, entry)

    return '\n'.join(lines)


def format_entry(text: str, timestamp_format: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format entry with timestamp

    Args:
        text: Entry text
        timestamp_format: Timestamp format string

    Returns:
        Formatted entry with timestamp
    """
    timestamp = datetime.now().strftime(timestamp_format)
    return f"- [{timestamp}] {text}"


# =============================================================================
# WRITE OPERATIONS
# =============================================================================

def write_entry_to_dev_local(
    branch_path: Path,
    section_name: str,
    entry_text: str,
    timestamp_format: str = "%Y-%m-%d %H:%M"
) -> tuple[bool, str]:
    """
    Write entry to dev.local.md section

    Args:
        branch_path: Path to branch directory
        section_name: Section name to write to
        entry_text: Entry text
        timestamp_format: Timestamp format

    Returns:
        Tuple of (success, resolved_section_name_or_error_reason)
    """
    # Resolve section alias
    resolved_name, is_valid = resolve_section_alias(section_name)
    if not is_valid:
        available = ", ".join(VALID_SECTIONS)
        return (False, f"Unknown section '{section_name}'. Available sections: {available}")

    # Find dev.local.md
    dev_file = find_dev_local_file(branch_path)
    if dev_file is None:
        return (False, f"dev.local.md not found in {branch_path}")

    # Read content
    try:
        with open(dev_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return (False, f"Could not read {dev_file}")

    # Format entry
    formatted_entry = format_entry(entry_text, timestamp_format)

    # Append to section
    updated_content = append_to_section(content, resolved_name, formatted_entry)
    if updated_content is None:
        return (False, f"Section '{resolved_name}' not found in {dev_file.name}")

    # Write updated content
    try:
        with open(dev_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return (True, resolved_name)
    except Exception:
        return (False, f"Could not write to {dev_file}")
