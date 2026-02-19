#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: backfill_birth_certs.py - Birth Certificate Backfill Tool
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/tools
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 3)
#
# CODE STANDARDS:
#   - One-time idempotent backfill script
#   - Reads BRANCH_REGISTRY.json and creates birth certificates for all branches
# =============================================

"""
Birth Certificate Backfill Script

Reads BRANCH_REGISTRY.json and creates a birth_certificate artifact
for each registered branch that doesn't already have one.

Idempotent: safe to run multiple times. Checks before creating.

Usage:
    python3 tools/backfill_birth_certs.py
"""

import sys
import json
from pathlib import Path

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import init_db, close_db
from handlers.artifacts.artifact_ops import create_birth_certificate

# Constants
BRANCH_REGISTRY_PATH = Path.home() / "BRANCH_REGISTRY.json"


def backfill_birth_certificates() -> None:
    """
    Read BRANCH_REGISTRY.json and create birth certificates for all branches.

    Skips branches that already have a birth_certificate artifact.
    Uses branch registration data for certificate metadata.
    """
    print("=" * 60)
    print("Birth Certificate Backfill")
    print("=" * 60)
    print()

    # Load registry
    if not BRANCH_REGISTRY_PATH.exists():
        print(f"[ERROR] BRANCH_REGISTRY.json not found at {BRANCH_REGISTRY_PATH}")
        return

    try:
        registry = json.loads(BRANCH_REGISTRY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"[ERROR] Failed to read BRANCH_REGISTRY.json: {e}")
        return

    branches = registry.get("branches", [])
    if not branches:
        print("[WARN] No branches found in registry")
        return

    print(f"Found {len(branches)} branches in registry")
    print()

    # Initialize database
    conn = init_db()

    created_count = 0
    skipped_count = 0
    error_count = 0

    for i, branch in enumerate(branches, 1):
        branch_name = branch.get("name", "")
        if not branch_name:
            continue

        branch_path = branch.get("path", "")
        profile = branch.get("profile", "AIPass Workshop")
        description = branch.get("description", "")
        created_date = branch.get("created", "")

        # Use index as citizen number (1-based)
        citizen_number = i

        print(f"  [{i:2d}/{len(branches)}] {branch_name:20s} ", end="")

        artifact_id = create_birth_certificate(
            conn=conn,
            branch_name=branch_name,
            citizen_number=citizen_number,
            template_used=profile,
            creator="SYSTEM",
            purpose=description or "Registered branch",
        )

        if artifact_id is not None:
            print(f"[CREATED] artifact_id={artifact_id}")
            created_count += 1
        else:
            # Check if it was skipped (already exists) vs error
            existing = conn.execute(
                "SELECT id FROM artifacts WHERE owner = ? AND type = 'birth_certificate'",
                (branch_name,),
            ).fetchone()
            if existing:
                print(f"[SKIP] already exists (id={existing['id']})")
                skipped_count += 1
            else:
                print("[ERROR] creation failed")
                error_count += 1

    close_db(conn)

    print()
    print("-" * 60)
    print(f"Results:")
    print(f"  Created:  {created_count}")
    print(f"  Skipped:  {skipped_count} (already had certificates)")
    print(f"  Errors:   {error_count}")
    print(f"  Total:    {len(branches)} branches")
    print("-" * 60)
    print()

    if error_count == 0:
        print("Backfill complete. All branches have birth certificates.")
    else:
        print(f"Backfill complete with {error_count} error(s). Check logs for details.")


if __name__ == "__main__":
    backfill_birth_certificates()
