#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: ops.py - Template Operations Handler
# Date: 2025-11-16
# Version: 1.0.0
# Category: Handler
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-16): Initial version - template parsing and compliance
#
# CODE STANDARDS:
#   - Handler independence: No module imports
#   - File size: < 300 lines ideal
# =============================================

"""
Template Operations Handler

Parses dev.local.md template and checks file compliance.
"""

import sys
from pathlib import Path
from typing import List, Optional

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Handler: no Prax logging - returns status to module

# Default template location
DEFAULT_TEMPLATE = AIPASS_ROOT / "templates" / "ai_branch_setup_template" / "dev.local.md"

# =============================================================================
# TEMPLATE PARSING
# =============================================================================

def parse_template_sections(template_path: Path | None = None) -> List[str]:
    """
    Parse template file and extract section names

    Args:
        template_path: Path to template file (uses default if None)

    Returns:
        List of section names found in template
    """
    if template_path is None:
        template_path = DEFAULT_TEMPLATE

    if not template_path.exists():
        return []

    sections = []

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')

        for line in lines:
            # Match ## Section or ## **Section**
            if line.strip().startswith('##'):
                # Remove ##, **, and whitespace to get section name
                section_name = line.replace('#', '').replace('*', '').strip()
                if section_name and section_name != '':
                    sections.append(section_name)

        return sections

    except Exception:
        return []


# =============================================================================
# COMPLIANCE CHECKING
# =============================================================================

def check_template_compliance(
    dev_file_path: Path,
    template_path: Path | None = None
) -> tuple[bool, List[str]]:
    """
    Check if dev.local.md file complies with template structure

    Args:
        dev_file_path: Path to dev.local.md file to check
        template_path: Path to template file (uses default if None)

    Returns:
        Tuple of (is_compliant, missing_sections)
    """
    if not dev_file_path.exists():
        return (False, [])

    # Get expected sections from template
    expected_sections = parse_template_sections(template_path)
    if not expected_sections:
        return (False, [])

    # Read dev.local.md
    try:
        with open(dev_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return (False, expected_sections)

    # Find which sections exist
    lines = content.split('\n')
    found_sections = []

    for line in lines:
        if line.strip().startswith('##'):
            section_name = line.replace('#', '').replace('*', '').strip()
            if section_name:
                found_sections.append(section_name)

    # Check for missing sections
    missing_sections = []
    for section in expected_sections:
        if section not in found_sections:
            missing_sections.append(section)

    is_compliant = len(missing_sections) == 0

    return (is_compliant, missing_sections)


def get_available_sections(template_path: Path | None = None) -> List[str]:
    """
    Get list of available sections from template

    Args:
        template_path: Path to template file (uses default if None)

    Returns:
        List of section names
    """
    return parse_template_sections(template_path)
