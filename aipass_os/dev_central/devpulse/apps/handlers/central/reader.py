#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: reader.py - Central File Reader Handler
# Date: 2025-11-27
# Version: 0.1.0
# Category: aipass/handlers/central
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-27): Initial handler - read all .central.json files
#
# CODE STANDARDS:
#   - Handler tier 3 - pure functions, raises exceptions
#   - No CLI imports, caller handles logging
# =============================================

"""
Central File Reader Handler

Reads all .central.json files from AI_CENTRAL directory.
Used by dashboard refresh to collect service data.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

# Infrastructure
AIPASS_ROOT = Path.home()
AI_CENTRAL_DIR = AIPASS_ROOT / "aipass_os" / "AI_CENTRAL"

# Known central files and their service owners
CENTRAL_FILES = {
    "bulletin_board": "BULLETIN_BOARD_central.json",
    "plans": "PLANS.central.json",
    "ai_mail": "AI_MAIL.central.json",
    "memory_bank": "MEMORY_BANK.central.json",
    "devpulse": "DEVPULSE.central.json"
}


def get_central_path(service: str) -> Path:
    """
    Get path to a service's central file.

    Args:
        service: Service name (bulletin_board, plans, ai_mail, etc)

    Returns:
        Path to the central file

    Raises:
        KeyError: If service not in known list
    """
    if service not in CENTRAL_FILES:
        raise KeyError(f"Unknown service: {service}. Known: {list(CENTRAL_FILES.keys())}")
    return AI_CENTRAL_DIR / CENTRAL_FILES[service]


def read_central_file(service: str) -> Optional[Dict]:
    """
    Read a single service's central file.

    Args:
        service: Service name (bulletin_board, plans, ai_mail, etc)

    Returns:
        Dict with central data, or None if file doesn't exist/invalid

    Raises:
        KeyError: If service not in known list
    """
    path = get_central_path(service)

    if not path.exists():
        return None

    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def read_all_centrals() -> Dict[str, Optional[Dict]]:
    """
    Read all known central files.

    Returns:
        Dict mapping service names to their central data.
        Value is None if file missing or invalid JSON.

    Example:
        {
            "bulletin_board": {"bulletins": [...]},
            "plans": {"active_plans": [...]},
            "ai_mail": {"branch_stats": {...}},
            "memory_bank": None,  # file missing
            "devpulse": {"branch_summaries": {...}}
        }
    """
    results = {}
    for service in CENTRAL_FILES:
        results[service] = read_central_file(service)
    return results


def list_central_files() -> List[Dict]:
    """
    List all central files with their status.

    Returns:
        List of dicts with service, path, exists, valid keys
    """
    results = []
    for service, filename in CENTRAL_FILES.items():
        path = AI_CENTRAL_DIR / filename
        exists = path.exists()
        valid = False

        if exists:
            try:
                json.loads(path.read_text())
                valid = True
            except json.JSONDecodeError:
                pass

        results.append({
            "service": service,
            "path": str(path),
            "exists": exists,
            "valid": valid
        })

    return results
