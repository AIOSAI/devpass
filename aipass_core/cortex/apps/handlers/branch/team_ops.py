#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: team_ops.py - Team Operations Handler
# Date: 2026-02-08
# Version: 1.0.0
# Category: cortex/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-08): Initial implementation - team creation with workspace
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Team Operations Handler

Functions for creating business team branches:
- Auto-increment team numbering
- Team template deployment
- Workspace branch creation inside team
- Dual registration (team + workspace)
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Internal handler imports
from cortex.apps.handlers.branch.metadata import (
    get_branch_name,
    get_git_repo,
    generate_tree
)
from cortex.apps.handlers.branch.placeholders import build_replacements_dict
from cortex.apps.handlers.branch.file_ops import (
    copy_template_contents,
    rename_files,
    rename_json_directory,
    smart_rename_memory_files,
    update_readme_tree_placeholders
)
from cortex.apps.handlers.branch.registry import register_branch


# =============================================================================
# CONSTANTS
# =============================================================================

TEAM_TEMPLATE_DIR = AIPASS_ROOT / "cortex" / "templates" / "team_template"
BRANCH_TEMPLATE_DIR = AIPASS_ROOT / "cortex" / "templates" / "branch_template"
DEFAULT_TEAM_ROOT = Path.home() / "aipass_business" / "hq"

EXCLUDE_PATTERNS = [
    "setup_instructions",
    "new_branch_setup.py",
    "upgrade_branch.py",
    ".git",
    "__pycache__",
]

TEAM_FILE_RENAMES = {
    "LOCAL.json": "{BRANCHNAME}.local.json",
    "OBSERVATIONS.json": "{BRANCHNAME}.observations.json",
    "BRANCH.ID.json": "{BRANCHNAME}.id.json",
}

WS_FILE_RENAMES = {
    "LOCAL.json": "{BRANCHNAME}.local.json",
    "OBSERVATIONS.json": "{BRANCHNAME}.observations.json",
    "AI_MAIL.json": "{BRANCHNAME}.ai_mail.json",
    "BRANCH.ID.json": "{BRANCHNAME}.id.json",
    "apps/BRANCH.py": "apps/{branchname}.py",
}

ALLOWED_PLACEHOLDERS = {
    "AUTO_GENERATED_COMMANDS", "TREE_PLACEHOLDER", "MODULE_NAME", "placeholder",
    "DOCUMENT_TYPE", "DOCUMENT_NAME", "TAG_1", "TAG_2", "TAG_3",
    "MODULE",
    "EMOJI_1", "EMOJI_1_DESCRIPTION", "EMOJI_2", "EMOJI_2_DESCRIPTION",
    "EMOJI_3", "EMOJI_3_DESCRIPTION",
    "BRIEF_SUMMARY", "MAIN_TOPIC", "KEY_POINT_1", "KEY_POINT_2", "KEY_POINT_3",
    "NARRATIVE_CONTENT", "SECTION_1_CONTENT", "SECTION_2_CONTENT",
    "SECTION_3_CONTENT", "CONCLUSION_CONTENT",
    "DOCUMENT_PURPOSE", "HOW_TO_USE", "PRIORITY_LEVEL", "TIMESTAMP",
    "PLACEHOLDER",
    "AUTO_GENERATED_MODULES", "AUTO_GENERATED_DEPENDENCIES", "AUTO_GENERATED_IMPORTS",
    "KEY_CAPABILITIES", "BASIC_USAGE", "COMMON_WORKFLOWS", "EXAMPLES",
    "DEPENDS_ON", "INTEGRATES_WITH", "PROVIDES_TO",
}


# =============================================================================
# AUTO-INCREMENT NAMING
# =============================================================================

def get_next_team_number(team_root: Path) -> int:
    """
    Determine next team number by scanning existing team_N directories.

    Args:
        team_root: Parent directory containing team directories

    Returns:
        Next available team number
    """
    if not team_root.exists():
        return 1

    existing_numbers = []
    for entry in team_root.iterdir():
        if entry.is_dir():
            match = re.match(r'^team_(\d+)$', entry.name)
            if match:
                existing_numbers.append(int(match.group(1)))

    if not existing_numbers:
        return 1

    return max(existing_numbers) + 1


# =============================================================================
# TEAM CREATION
# =============================================================================

def create_team(target_dir: Path) -> Dict[str, Any]:
    """
    Create new business team from team template with workspace.

    Args:
        target_dir: Path where team will be created

    Returns:
        Dict with creation results:
            - success: bool
            - error: str (if failed)
            - team_name: str
            - team_upper: str
            - team_copied: list
            - team_renamed: list
            - team_reg: str
            - ws_name: str
            - ws_upper: str
            - ws_copied: list
            - ws_renamed: list
            - ws_reg: str
            - phases: list of phase status messages
    """
    result: Dict[str, Any] = {
        'success': False,
        'error': None,
        'phases': []
    }

    if not TEAM_TEMPLATE_DIR.exists():
        result['error'] = f"Team template not found at: {TEAM_TEMPLATE_DIR}"
        return result

    if not BRANCH_TEMPLATE_DIR.exists():
        result['error'] = f"Branch template not found at: {BRANCH_TEMPLATE_DIR}"
        return result

    try:
        target_dir.mkdir(parents=True, exist_ok=True)

        branch_name = get_branch_name(target_dir)
        branchname_upper = branch_name.upper().replace("-", "_")
        repo = get_git_repo(target_dir)

        result['team_name'] = branch_name
        result['team_upper'] = branchname_upper
        result['path'] = str(target_dir)

        # =================================================================
        # PHASE 1: Create team manager directory from team template
        # =================================================================
        replacements = build_replacements_dict(branch_name, target_dir, repo, "Business Team Manager")

        smart_rename_memory_files(target_dir, branch_name)

        copied, _skipped, validation_errors = copy_template_contents(
            TEAM_TEMPLATE_DIR, target_dir, replacements, branch_name,
            EXCLUDE_PATTERNS, TEAM_FILE_RENAMES, ALLOWED_PLACEHOLDERS
        )

        if validation_errors:
            result['error'] = f"Team template validation errors: {validation_errors}"
            return result

        renamed, _missing = rename_files(target_dir, branch_name, TEAM_FILE_RENAMES)
        rename_json_directory(target_dir, branch_name)

        team_reg = register_branch(target_dir, branch_name, branchname_upper)

        tree_output = generate_tree(target_dir)
        update_readme_tree_placeholders(target_dir, tree_output)

        result['team_copied'] = copied
        result['team_renamed'] = renamed
        result['team_reg'] = team_reg
        result['phases'].append(f"Team manager created: {branchname_upper}")

        # =================================================================
        # PHASE 2: Create workspace branch inside team directory
        # =================================================================
        ws_dir = target_dir / "workspace"
        ws_name = f"{branch_name}_ws"
        ws_upper = ws_name.upper().replace("-", "_")

        ws_dir.mkdir(parents=True, exist_ok=True)

        ws_replacements = build_replacements_dict(ws_name, ws_dir, repo, "Business Team Workspace")
        smart_rename_memory_files(ws_dir, ws_name)

        ws_copied, _ws_skipped, ws_errors = copy_template_contents(
            BRANCH_TEMPLATE_DIR, ws_dir, ws_replacements, ws_name,
            EXCLUDE_PATTERNS, WS_FILE_RENAMES, ALLOWED_PLACEHOLDERS
        )

        if ws_errors:
            result['error'] = f"Workspace validation errors: {ws_errors}"
            return result

        ws_renamed, _ws_missing = rename_files(ws_dir, ws_name, WS_FILE_RENAMES)
        rename_json_directory(ws_dir, ws_name)

        ws_reg = register_branch(ws_dir, ws_name, ws_upper)

        ws_tree = generate_tree(ws_dir)
        update_readme_tree_placeholders(ws_dir, ws_tree)

        result['ws_name'] = ws_name
        result['ws_upper'] = ws_upper
        result['ws_path'] = str(ws_dir)
        result['ws_copied'] = ws_copied
        result['ws_renamed'] = ws_renamed
        result['ws_reg'] = ws_reg
        result['phases'].append(f"Workspace created: {ws_upper}")

        result['success'] = True
        return result

    except Exception as e:
        result['error'] = str(e)
        return result
