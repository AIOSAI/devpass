#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: decorators.py - Registry Auto-Healing Decorators
# Date: 2025-11-08
# Version: 1.0.0
# Category: cortex/handlers
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-08): Initial implementation - Auto-healing decorator
#
# CODE STANDARDS:
#   - Error handling: Use error handler system (apps/handlers/error/)
# =============================================

"""
Registry Auto-Healing Decorators

Provides decorators to ensure registry validity and freshness before operations.
Automatically triggers registry regeneration when:
- Mismatches detected between registry and filesystem
- Registry is stale (ignore config newer than registry)
"""

import sys
import os
from pathlib import Path
from functools import wraps
from typing import Tuple

# INFRASTRUCTURE IMPORT PATTERN
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from cortex.apps.handlers.registry.meta_ops import (
    load_template_registry,
    validate_template_registry
)

TEMPLATE_DIR = AIPASS_ROOT / "cortex" / "templates" / "branch_template"


# =============================================================================
# REGISTRY FRESHNESS CHECKS
# =============================================================================

def is_registry_stale() -> Tuple[bool, str]:
    """
    Check if template registry is stale compared to .registry_ignore.json

    Returns:
        Tuple of (is_stale: bool, reason: str)

    Logic:
        Registry is stale if .registry_ignore.json is newer than .template_registry.json
        This means ignore patterns changed but registry wasn't regenerated
    """
    registry_file = TEMPLATE_DIR / ".template_registry.json"
    ignore_file = TEMPLATE_DIR / ".registry_ignore.json"

    # If registry doesn't exist, it's definitely stale
    if not registry_file.exists():
        return (True, "Registry file missing")

    # If ignore file doesn't exist, registry is current (nothing to compare)
    if not ignore_file.exists():
        return (False, "No ignore config to compare")

    # Compare modification times
    registry_mtime = os.path.getmtime(registry_file)
    ignore_mtime = os.path.getmtime(ignore_file)

    if ignore_mtime > registry_mtime:
        return (True, "Ignore config is newer than registry")

    return (False, "Registry is current")


def ensure_valid_registry(func):
    """
    Decorator to validate registry freshness and validity before function executes

    Auto-heals registry if:
    - Registry is stale (ignore config changed)
    - Mismatches detected between registry and filesystem

    Ensures template filesystem is always the source of truth.

    Usage:
        @ensure_valid_registry
        def update_branch(target_dir: Path) -> bool:
            # Registry guaranteed valid and fresh here
            ...

    Pattern:
        1. Check if registry is stale (ignore config newer)
        2. Load template registry
        3. Validate against filesystem
        4. If stale or mismatches → regenerate registry (silent)
        5. Execute wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        needs_regeneration = False
        regeneration_reason = []

        # Check 1: Registry freshness (timestamp-based)
        is_stale, stale_reason = is_registry_stale()
        if is_stale:
            needs_regeneration = True
            regeneration_reason.append(stale_reason)

        # Check 2: Registry validity (structure-based)
        template_registry, error = load_template_registry()
        if template_registry:
            mismatches = validate_template_registry(template_registry, TEMPLATE_DIR)
            if mismatches:
                needs_regeneration = True
                regeneration_reason.append(f"{len(mismatches)} registry mismatches")

        # Auto-heal if needed
        if needs_regeneration:
            reason_str = ", ".join(regeneration_reason)

            # Import regenerate function (lazy import to avoid circular deps)
            from cortex.apps.modules.regenerate_template_registry import regenerate_registry

            # Regenerate registry (silent - decorator should work silently)
            success = regenerate_registry()

        # Execute wrapped function
        return func(*args, **kwargs)

    return wrapper
