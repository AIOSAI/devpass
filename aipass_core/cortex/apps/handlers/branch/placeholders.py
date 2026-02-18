#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: placeholders.py - Placeholder Replacement Handler
# Date: 2025-11-04
# Version: 1.0.0
# Category: cortex/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-04): Extracted from branch_lib, placeholder replacement functions
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Placeholder Replacement Handler

Functions for handling template placeholders:
- Placeholder replacement in strings
- Placeholder validation
- Replacements dictionary building
- Naming mismatch detection
"""

# Standard library imports
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Iterable, Any
import sys

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))


# =============================================================================
# PLACEHOLDER REPLACEMENT
# =============================================================================

def replace_placeholders(content: str, replacements: Dict[str, str]) -> str:
    """
    Replace placeholders in file content

    Placeholders must be in format: double-brace + NAME + double-brace

    Args:
        content: File content with placeholders
        replacements: Dict mapping placeholder names to replacement values

    Returns:
        Content with placeholders replaced
    """
    for placeholder, value in replacements.items():
        # Build pattern with double braces
        pattern = "{{" + placeholder + "}}"
        content = content.replace(pattern, value)
    return content


def validate_no_placeholders(
    content: str,
    file_path: str,
    allowed_placeholders: Optional[Iterable[str]] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Check if content still contains unreplaced placeholders.

    Args:
        content: File content to check
        file_path: Path to file (for error reporting)
        allowed_placeholders: Collection of placeholder tokens to ignore

    Returns:
        Tuple of (is_valid, list of placeholder details with line numbers and context)
        Each detail dict contains: {
            'placeholder': str,
            'line_number': int,
            'line_content': str (trimmed to 100 chars),
            'context': str (snippet showing location)
        }
    """
    pattern = r'\{\{([^}]+)\}\}'
    lines = content.split('\n')
    allowed = set(allowed_placeholders or [])

    placeholder_details = []

    for line_num, line in enumerate(lines, start=1):
        matches = re.findall(pattern, line)
        for placeholder in matches:
            if placeholder not in allowed:
                # Get context (±2 lines)
                start_line = max(0, line_num - 3)
                end_line = min(len(lines), line_num + 2)
                context_lines = lines[start_line:end_line]
                context = '\n'.join(f"  {start_line + i + 1:4d}: {l[:100]}"
                                   for i, l in enumerate(context_lines))

                placeholder_details.append({
                    'placeholder': placeholder,
                    'line_number': line_num,
                    'line_content': line.strip()[:100],
                    'context': context
                })

    if placeholder_details:
        return False, placeholder_details
    return True, []


def detect_unreplaced_placeholders(
    target_dir: Path,
    branch_name: str,
    allowed_placeholders: Optional[Iterable[str]] = None
) -> List[Tuple[Path, List[Dict[str, Any]]]]:
    """
    Scan standard branch memory files for unreplaced template placeholders.

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name (used to build expected filenames)
        allowed_placeholders: Placeholders that may legitimately remain

    Returns:
        List of tuples (Path to file, list of placeholders found)
    """
    branchname_upper = branch_name.upper().replace("-", "_")
    expected_files = [
        target_dir / f"{branchname_upper}.json",
        target_dir / f"{branchname_upper}.local.json",
        target_dir / f"{branchname_upper}.observations.json",
        target_dir / f"{branchname_upper}.ai_mail.json",
        target_dir / f"{branchname_upper}.id.json",
    ]

    issues: List[Tuple[Path, List[Dict[str, Any]]]] = []
    for file_path in expected_files:
        if not file_path.exists() or not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError) as exc:
            continue

        is_valid, placeholders = validate_no_placeholders(
            content,
            str(file_path),
            allowed_placeholders=allowed_placeholders
        )
        if not is_valid and placeholders:
            issues.append((file_path, placeholders))

    return issues


def detect_naming_mismatches(target_dir: Path, branch_name: str, file_renames: Dict[str, str]) -> List[Tuple[str, str]]:
    """
    Detect files with non-standard naming (hyphens instead of underscores)

    Args:
        target_dir: Path to branch directory
        branch_name: Branch name
        file_renames: Dict mapping template names to rename patterns

    Returns:
        List of tuples (wrong_name, correct_name)
    """
    mismatches = []
    branchname_upper = branch_name.upper().replace("-", "_")
    branchname_lower = branch_name.lower().replace("-", "_")

    # Check for each expected file with correct naming
    for template_name, pattern in file_renames.items():
        correct_name = pattern.format(BRANCHNAME=branchname_upper, branchname=branchname_lower)

        # Look for files that match the pattern but use different separator
        for item in target_dir.iterdir():
            if item.is_file() and item.name != correct_name:
                # Check if it's a similar name with hyphens or mixed separators
                item_name_normalized = item.name.replace("-", "_")
                correct_name_normalized = correct_name.replace("-", "_")

                if item_name_normalized == correct_name_normalized and item.name != correct_name:
                    mismatches.append((item.name, correct_name))

    return mismatches


def apply_placeholder_replacements_to_dict(
    data: Dict[str, Any],
    replacements: Dict[str, str]
) -> Dict[str, Any]:
    """
    Apply placeholder replacements to a JSON-compatible dictionary.

    Args:
        data: Dictionary loaded from template or merged result
        replacements: Placeholder replacement mapping

    Returns:
        Dictionary with placeholders replaced

    Raises:
        ValueError: If replacement results in invalid JSON structure
    """
    serialized = json.dumps(data, indent=2, ensure_ascii=False)
    serialized = replace_placeholders(serialized, replacements)
    try:
        return json.loads(serialized)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON after placeholder replacement: {exc}") from exc


def build_replacements_dict(branch_name: str, target_dir: Path, repo: str, profile: str, overrides: Optional[Dict[str, str]] = None) -> dict:
    """
    Build replacements dictionary for template placeholders.

    Args:
        branch_name: Branch name (lowercase with hyphens)
        target_dir: Target directory path
        repo: Git repository name
        profile: AIPass profile (Workshop, Business, etc.)
        overrides: Optional dict of placeholder overrides (e.g. ROLE, TRAITS, PURPOSE_BRIEF)

    Returns:
        Dictionary of template placeholders and their replacement values
    """
    branchname_upper = branch_name.upper().replace("-", "_")
    foldername_lower = branch_name.lower()
    now = datetime.now()

    replacements = {
        # Already implemented
        "BRANCHNAME": branchname_upper,
        "branchname": foldername_lower,  # Lowercase for .gitignore patterns
        "FOLDERNAME": foldername_lower,
        "BRANCH": foldername_lower,  # For {{BRANCH}}_json
        "CWD": str(target_dir),
        "DATE": now.strftime("%Y-%m-%d"),
        "TIMESTAMP": now.strftime("%Y-%m-%d"),
        "REPO": repo,
        "PROFILE": profile,

        # New auto-fills
        "INSTANCE_NAME": branchname_upper,  # Same as BRANCHNAME
        "EMAIL": f"@{foldername_lower}",  # Branch email address
        "AUTO_TIMESTAMP": now.strftime("%Y-%m-%d"),
        "AUTO_GENERATED_TREE": "{{TREE_PLACEHOLDER}}",  # Will be replaced after files copied

        # Memory file health indicators
        "HEALTH_STATUS": "🟢 Healthy",  # Initial status - updated by monitor
        "CURRENT_LINES": "0",  # Initial line count - updated after first session

        # Identity fields - empty unless provided via overrides
        "ROLE": "",
        "TRAITS": "",
        "PURPOSE_DESCRIPTION": "",
        "PURPOSE_BRIEF": "",
        "WHAT_I_DO": "",
        "WHAT_I_DONT_DO": "",
        "HOW_I_WORK": "",
        "RESPONSIBILITIES_LIST": "",
        "USAGE_INSTRUCTIONS": "",
        "BRANCH_DESCRIPTION": "",
        "branch_category": "",

        # Keep as placeholder (AI fills during updates)
        # AUTO_GENERATED_COMMANDS stays as {{AUTO_GENERATED_COMMANDS}}
    }

    # Apply overrides - allows CLI args to fill identity fields at creation time
    if overrides:
        for key, value in overrides.items():
            if key in replacements and value:
                replacements[key] = value

    return replacements
