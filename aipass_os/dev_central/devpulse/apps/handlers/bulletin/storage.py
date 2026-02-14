#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: storage.py - Bulletin Storage Handler
# Date: 2025-11-24
# Version: 0.1.0
# Category: aipass/handlers/bulletin
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-24): Initial handler - bulletin storage operations
#
# CODE STANDARDS:
#   - Handler tier 3 - pure functions, raises exceptions
#   - No module imports (handlers independence)
#   - Domain organized storage operations
# =============================================

"""
Bulletin Storage Handler

Handles loading and saving bulletin data to central storage.
Pure functions with proper error handling.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

# Infrastructure
AIPASS_ROOT = Path.home()

# Paths
AI_CENTRAL = AIPASS_ROOT / "aipass_os" / "AI_CENTRAL"
BULLETIN_CENTRAL = AI_CENTRAL / "BULLETIN_BOARD_central.json"


def load_bulletins() -> Dict:
    """
    Load central bulletin board from storage

    Returns:
        Dict: Bulletin data with 'bulletins' list and 'metadata' dict

    Raises:
        json.JSONDecodeError: If JSON is malformed
        FileNotFoundError: If parent directory doesn't exist
    """
    if not BULLETIN_CENTRAL.exists():
        return {"bulletins": [], "metadata": {}}

    return json.loads(BULLETIN_CENTRAL.read_text())


def save_bulletins(data: Dict) -> bool:
    """
    Save central bulletin board to storage

    Args:
        data: Bulletin data to save

    Returns:
        bool: True if saved successfully

    Raises:
        OSError: If file write fails
        json.JSONEncodeError: If data cannot be serialized
    """
    # Update metadata timestamp
    if "metadata" not in data:
        data["metadata"] = {}
    data["metadata"]["last_updated"] = datetime.now().isoformat()

    # Ensure directory exists
    BULLETIN_CENTRAL.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    BULLETIN_CENTRAL.write_text(json.dumps(data, indent=2))
    return True
