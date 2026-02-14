#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: template.py - D-PLAN template management
# Date: 2025-12-02
# Version: 1.0.0
# Category: devpulse/handlers/plan
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-12-02): Extracted from dev_flow.py module
#
# CODE STANDARDS:
#   - Handler independence: NO cross-domain imports
#   - NO Prax logging (per 3-tier: modules log, handlers don't)
#   - Pure business logic only
# ==============================================

"""
Template Handler - D-PLAN Templates

Manages template loading and rendering for D-PLAN documents.
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
from typing import Tuple

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

# NOTE: Handlers do NOT import Prax logger (per 3-tier standard)

# =============================================================================
# CONFIGURATION
# =============================================================================

DEVPULSE_ROOT = Path.home() / "aipass_os" / "dev_central" / "devpulse"
TEMPLATE_FILE = DEVPULSE_ROOT / "templates" / "dplan_default.md"

DEFAULT_TEMPLATE = """# DPLAN-{{NUMBER}}: {{TOPIC}}

> One-line description

## Vision
What we're trying to achieve

## Current State
What exists now

## What Needs Building
Concrete items to build

## Design Decisions
Key choices and why

## Status
- [x] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes
Session notes, discoveries, changes

---
*Created: {{DATE}}*
*Updated: {{DATE}}*
"""


# =============================================================================
# HANDLER FUNCTIONS
# =============================================================================

def get_default_template() -> str:
    """
    Return built-in default template

    Returns:
        Template string with {{NUMBER}}, {{TOPIC}}, {{DATE}} placeholders
    """
    return DEFAULT_TEMPLATE


def render_template(
    plan_number: int,
    topic: str,
    date_str: str
) -> Tuple[str, str]:
    """
    Render D-PLAN template with variables

    Loads custom template if available, falls back to default.
    Replaces {{NUMBER}}, {{TOPIC}}, {{DATE}} placeholders.

    Args:
        plan_number: The D-PLAN number (e.g., 42)
        topic: Topic name
        date_str: Date string (YYYY-MM-DD)

    Returns:
        Tuple of (rendered_content, error_message)
        Error message is empty on success
    """
    # Try to load custom template
    template_content = None
    if TEMPLATE_FILE.exists():
        try:
            template_content = TEMPLATE_FILE.read_text(encoding='utf-8')
        except Exception:
            template_content = None

    if template_content is None:
        template_content = get_default_template()

    # Replace placeholders
    content = template_content.replace("{{NUMBER}}", f"{plan_number:03d}")
    content = content.replace("{{TOPIC}}", topic)
    content = content.replace("{{DATE}}", date_str)

    return content, ""
