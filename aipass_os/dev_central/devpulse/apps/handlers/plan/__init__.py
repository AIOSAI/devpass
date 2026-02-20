#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: plan handlers - Public API
# Date: 2025-12-02
# Version: 1.0.0
# Category: devpulse/handlers/plan
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-12-02): Initial version - exports handler functions
#
# CODE STANDARDS:
#   - Exports public API for plan handlers
#   - Internal imports only (no cross-branch access)
# ==============================================

"""
Plan Handlers - Public API

Exports functions for D-PLAN operations.
"""

from .counter import get_next_plan_number, VALID_PLAN_TYPES
from .template import render_template, get_default_template
from .create import create_plan
from .list import list_plans
from .status import get_status_summary, extract_status, get_status_icon, extract_tag, extract_description, VALID_TAGS
from .display import show_help, print_introspection
from .close import close_plan, normalize_plan_number, get_open_plans, archive_plan
from .registry import (
    register_plan, update_plan_status, populate_from_filesystem,
    load_registry, get_summary, save_plan_summary
)
from .dashboard import push_all as push_dashboard
