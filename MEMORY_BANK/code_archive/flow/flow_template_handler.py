#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: flow_template_handler.py
# Date: 2025-10-24
# Version: 1.0.0
# Description: Template handler for scalable PLAN template system - loads templates from shared templates directory
#
# CHANGELOG:
#   - v1.0.0 (2025-10-24): Initial implementation with get_template() function
# =============================================

"""
Flow Template Handler - Scalable Template System
==================================================

PURPOSE:
--------
Manages PLAN templates stored as markdown files in the shared templates directories.
Enables unlimited custom templates without code changes.

USAGE:
------
from apps.flow_template_handler import get_template

# Get default template
content = get_template("default", number=101, location="flow", subject="My Task")

# Get master plan template
content = get_template("master", number=102, location="flow/DOCUMENTS", subject="Big Project")

# Get custom template (future)
content = get_template("api", number=103, location="api", subject="API Development")

TEMPLATES DIRECTORY:
--------------------
Primary location (shared across branches):
    /home/aipass/aipass_core/templates/flow/

Template examples:
├── default.md (standard plan template)
├── master.md (master plan template for multi-phase projects)
└── ... (unlimited templates)

ADDING NEW TEMPLATES:
---------------------
1. Create .md file in /home/aipass/aipass_core/templates/flow/ directory
2. Use placeholders: {number}, {subject}, {location}, {today}
3. That's it - no code changes needed!

Author: Flow Branch
Date: 2025-10-24
Version: 1.0.0
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# =============================================
# PATH SETUP
# =============================================

AIPASS_ROOT = Path.home() / "aipass_core"
FLOW_ROOT = AIPASS_ROOT / "flow"
sys.path.append(str(AIPASS_ROOT))

# Import logger
from prax.apps.modules.prax_logger import system_logger as logger

# =============================================
# CONFIGURATION
# =============================================

# Module identity
MODULE_NAME = "flow_template_handler"

# Template directory
TEMPLATES_DIR = AIPASS_ROOT / "templates" / "flow"

# Fallback if template not found (use default)
DEFAULT_TEMPLATE = "default"


def _template_search_dirs() -> list[Path]:
    """
    Determine the ordered list of directories to search for templates.
    """
    return [TEMPLATES_DIR]


def _find_template_file(template_name: str) -> Path:
    """
    Locate the requested template (or default fallback) across supported directories.

    Raises:
        FileNotFoundError: When neither the requested nor default template exists anywhere.
    """
    search_paths = _template_search_dirs()

    # Look for the requested template
    candidate = search_paths[0] / f"{template_name}.md"
    if candidate.exists():
        return candidate

    # Fallback to default template
    default_candidate = search_paths[0] / f"{DEFAULT_TEMPLATE}.md"
    if default_candidate.exists():
        logger.warning(
            f"[{MODULE_NAME}] Template '{template_name}' not found. "
            f"Falling back to default template in {search_paths[0]}."
        )
        return default_candidate

    # Nothing found – raise helpful error
    searched = ", ".join(str(path) for path in search_paths)
    error_msg = (
        f"Templates not found. Searched for '{template_name}.md' and "
        f"'{DEFAULT_TEMPLATE}.md' in: {searched}"
    )
    logger.error(f"[{MODULE_NAME}] {error_msg}")
    raise FileNotFoundError(error_msg)

# =============================================
# TEMPLATE LOADING
# =============================================

def get_template(template_name: str = "default",
                 number: int = 0,
                 location: str = "",
                 subject: str = "") -> str:
    """
    Load and format a PLAN template from the configured template directories.

    Args:
        template_name: Name of template file (without .md extension)
        number: PLAN number for formatting
        location: Plan location (relative path)
        subject: Plan subject/title

    Returns:
        Formatted template content with placeholders replaced

    Examples:
        >>> get_template("default", 101, "flow", "My Task")
        # Returns default.md with {number}→101, {subject}→"My Task", etc.

        >>> get_template("master", 102, "flow/DOCUMENTS", "Big Project")
        # Returns master.md with placeholders filled
    """
    try:
        # Resolve template file (with fallback handling across directories)
        template_file = _find_template_file(template_name)

        # Read template file
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Get current date for {today} placeholder
        today = datetime.now().strftime('%Y-%m-%d')

        # Format template with placeholders
        formatted_content = template_content.format(
            number=f"{number:04d}",  # Format as 4-digit number (0001, 0042, 0101)
            subject=subject,
            location=location,
            today=today
        )

        logger.info(f"[{MODULE_NAME}] Loaded template '{template_name}' successfully")
        return formatted_content

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Template loading failed: {e}")
        raise


def list_templates() -> list[str]:
    """
    List all available templates across the configured template directories.

    Returns:
        List of template names (without .md extension)

    Example:
        >>> list_templates()
        ['default', 'master', 'api', 'webapp']
    """
    try:
        template_names: set[str] = set()
        search_dirs = _template_search_dirs()

        for base_dir in search_dirs:
            if not base_dir.exists():
                logger.warning(f"[{MODULE_NAME}] Templates directory not found: {base_dir}")
                continue

            for template_file in base_dir.glob("*.md"):
                template_names.add(template_file.stem)

        sorted_templates = sorted(template_names)
        logger.info(f"[{MODULE_NAME}] Found {len(sorted_templates)} templates: {sorted_templates}")
        return sorted_templates

    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Error listing templates: {e}")
        return []


# =============================================
# CLI COMMAND HANDLERS
# =============================================

def handle_list():
    """List all available templates."""
    templates = list_templates()
    if not templates:
        search_dirs = _template_search_dirs()
        print("No templates found. Checked directories:")
        for path in search_dirs:
            print(f"  - {path}")
        return 0
    
    print("Available templates:")
    for template in templates:
        print(f"  - {template}")
    return 0


def handle_show(template_name: str, number: int = 0, location: str = "", subject: str = ""):
    """Show template content."""
    try:
        content = get_template(template_name, number=number, location=location, subject=subject)
        print(content)
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error loading template: {e}")
        return 1


def handle_test():
    """Test template system with default and master templates."""
    print(f"Flow Template Handler v1.0.0")
    print("Template search order:")
    for path in _template_search_dirs():
        print(f"  - {path}")
    print()

    # List available templates
    print("Available templates:")
    templates = list_templates()
    for template in templates:
        print(f"  - {template}")
    print()

    # Test default template
    print("Testing default template:")
    try:
        content = get_template("default", number=999, location="test", subject="Test Plan")
        print(f"✓ Default template loaded ({len(content)} characters)")
        print(f"  First line: {content.split(chr(10))[0]}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    print()

    # Test master template
    print("Testing master template:")
    try:
        content = get_template("master", number=888, location="test", subject="Test Master Plan")
        print(f"✓ Master template loaded ({len(content)} characters)")
        print(f"  First line: {content.split(chr(10))[0]}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    return 0


# =============================================
# MAIN
# =============================================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Flow Template Handler - Scalable PLAN template system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: list, show, test

  list - List all available templates
  show - Display a template with optional parameters
  test - Run template system tests

OPTIONS:
  --template TEMPLATE   Template name (for show command)
  --number NUMBER       Plan number (default: 0)
  --location LOCATION   Plan location/path
  --subject SUBJECT     Plan subject/title

EXAMPLES:
  python3 flow_template_handler.py list
  python3 flow_template_handler.py show --template default --number 101 --subject "My Task"
  python3 flow_template_handler.py show --template master --number 102 --location "flow/DOCUMENTS" --subject "Big Project"
  python3 flow_template_handler.py test
        """
    )

    parser.add_argument('command',
                       nargs='?',
                       choices=['list', 'show', 'test'],
                       default='test',
                       help='Command to execute')

    parser.add_argument('--template', type=str, default='default',
                       help='Template name (for show command)')
    parser.add_argument('--number', type=int, default=0,
                       help='Plan number for formatting')
    parser.add_argument('--location', type=str, default='',
                       help='Plan location (relative path)')
    parser.add_argument('--subject', type=str, default='',
                       help='Plan subject/title')

    args = parser.parse_args()

    if args.command == 'list':
        return handle_list()
    elif args.command == 'show':
        return handle_show(args.template, number=args.number, location=args.location, subject=args.subject)
    elif args.command == 'test':
        return handle_test()
    else:
        parser.print_help()
        return 1


# =============================================
# MODULE TESTING
# =============================================

if __name__ == "__main__":
    sys.exit(main())
