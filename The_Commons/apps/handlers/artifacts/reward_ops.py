#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: reward_ops.py - Variable Reward Drop Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/artifacts
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 6 Fun)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules/entry point
# =============================================

"""
Variable Reward Drop Handler

Random surprise artifact drops triggered by post/comment activity.
10% chance per action, with rarity-weighted item pools.
"""

import sys
import random
from pathlib import Path
from typing import Optional, Dict, Any

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import get_db, close_db


# =============================================================================
# DROP ITEM POOLS
# =============================================================================

# Rarity thresholds (cumulative): common 0-59, uncommon 60-84, rare 85-96, legendary 97-99
RARITY_THRESHOLDS = [
    (60, "common"),
    (85, "uncommon"),
    (97, "rare"),
    (100, "legendary"),
]

ITEM_POOLS = {
    "common": [
        "Dust Bunny",
        "Forgotten Semicolon",
        "Loose Thread",
    ],
    "uncommon": [
        "Glowing Pebble",
        "Whispered Secret",
        "Lucky Coin",
    ],
    "rare": [
        "Golden Key Fragment",
        "Ancient Bookmark",
        "Starlight Shard",
    ],
    "legendary": [
        "The Original README",
        "First Commit Stone",
    ],
}

RARITY_COLORS = {
    "common": "white",
    "uncommon": "green",
    "rare": "blue",
    "legendary": "yellow",
}


# =============================================================================
# RANDOM DROP CHECK
# =============================================================================

def check_random_drop(branch_name: str, room_name: str) -> Optional[Dict[str, Any]]:
    """
    Check if a random artifact drop occurs (10% chance).

    If a drop occurs, creates a 'found' type artifact owned by the branch
    and records it in artifact_history.

    Args:
        branch_name: The branch that triggered the action
        room_name: The room where the action happened

    Returns:
        Dict with drop info (name, rarity, artifact_id) or None if no drop
    """
    # 10% chance of a drop
    roll = random.randint(0, 99)
    if roll >= 10:
        return None

    # Determine rarity
    rarity_roll = random.randint(0, 99)
    rarity = "common"
    for threshold, rarity_name in RARITY_THRESHOLDS:
        if rarity_roll < threshold:
            rarity = rarity_name
            break

    # Pick random item from pool
    items = ITEM_POOLS.get(rarity, ITEM_POOLS["common"])
    item_name = random.choice(items)

    try:
        conn = get_db()

        # Create artifact
        cursor = conn.execute(
            "INSERT INTO artifacts (name, type, creator, owner, rarity, description, room_found) "
            "VALUES (?, 'found', 'THE_COMMONS', ?, ?, ?, ?)",
            (item_name, branch_name, rarity,
             f"A surprise find in r/{room_name}", room_name),
        )
        artifact_id = cursor.lastrowid

        # Create history entry
        conn.execute(
            "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
            "VALUES (?, 'created', 'THE_COMMONS', ?, ?)",
            (artifact_id, branch_name,
             f"Random drop: '{item_name}' found in r/{room_name}"),
        )

        conn.commit()
        close_db(conn)

        logger.info(
            f"[commons] Random drop: {branch_name} found '{item_name}' "
            f"({rarity}) in r/{room_name}"
        )

        return {
            "name": item_name,
            "rarity": rarity,
            "rarity_color": RARITY_COLORS.get(rarity, "white"),
            "artifact_id": artifact_id,
        }

    except Exception as e:
        logger.error(f"[commons] Random drop failed: {e}")
        return None
