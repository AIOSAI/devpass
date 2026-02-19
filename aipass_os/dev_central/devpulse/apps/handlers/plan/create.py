#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: create.py - D-PLAN creation handler
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
Create Handler - D-PLAN File Creation

Creates new D-PLAN files with proper naming and content.
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Any

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

# NOTE: Handlers do NOT import Prax logger (per 3-tier standard)

from .counter import get_next_plan_number
from .template import render_template

# =============================================================================
# CONFIGURATION
# =============================================================================

DEV_PLANNING_ROOT = Path.home() / "aipass_os" / "dev_central" / "dev_planning"


# =============================================================================
# HANDLER FUNCTIONS
# =============================================================================

def create_plan(topic: str, tag: str = "idea", subdir: str | None = None) -> Tuple[bool, Dict[str, Any], str]:
    """
    Create a new D-PLAN file

    Args:
        topic: Topic name for the plan
        subdir: Optional subdirectory within dev_planning/

    Returns:
        Tuple of (success, result_data, error_message)
        result_data contains: plan_number, filename, path, topic, date, subdir
    """
    if not topic or not topic.strip():
        return False, {}, "Topic is required"

    topic = topic.strip()

    # Sanitize topic for filename (snake_case)
    topic_slug = re.sub(r'[^\w\s-]', '', topic.lower())
    topic_slug = re.sub(r'[\s-]+', '_', topic_slug)
    topic_slug = topic_slug[:40]  # Limit length

    # Determine target directory
    if subdir:
        # Sanitize subdir name (alphanumeric and underscore only)
        subdir = re.sub(r'[^\w-]', '', subdir.strip())
        if not subdir:
            return False, {}, "Invalid subdirectory name"
        target_dir = DEV_PLANNING_ROOT / subdir
    else:
        target_dir = DEV_PLANNING_ROOT

    # Get next number and date
    plan_number, cache_err = get_next_plan_number()
    # cache_err is non-critical, just for logging

    date_str = datetime.now().strftime("%Y-%m-%d")

    # Build filename: DPLAN-XXX_topic_name_YYYY-MM-DD.md
    filename = f"DPLAN-{plan_number:03d}_{topic_slug}_{date_str}.md"
    plan_path = target_dir / filename

    # Render template
    content, template_err = render_template(plan_number, topic, date_str, tag=tag)
    if template_err:
        return False, {}, f"Failed to render template: {template_err}"

    # Create file
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(content, encoding='utf-8')

        result = {
            "plan_number": plan_number,
            "filename": filename,
            "path": str(plan_path),
            "topic": topic,
            "tag": tag,
            "date": date_str,
            "subdir": subdir,
            "cache_warning": cache_err  # Module can log this if needed
        }

        return True, result, ""

    except Exception as e:
        return False, {}, f"Failed to write file: {e}"
