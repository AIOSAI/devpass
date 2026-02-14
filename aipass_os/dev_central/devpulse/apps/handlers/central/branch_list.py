#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: branch_list.py - Branch Registry Handler
# Date: 2025-11-24
# Version: 0.1.0
# Category: aipass/handlers/central
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-24): Initial handler - branch list operations
#
# CODE STANDARDS:
#   - Handler implements business logic, no CLI output
#   - Pure functions with proper error handling
#   - Type hints, docstrings, logger import
# =============================================

"""
Branch Registry Handler

Business logic for reading and managing branch registry.
Provides branch list and registry access.

Domain: Central coordination
"""

import sys
import json
from pathlib import Path
from typing import List, Dict

# Infrastructure
AIPASS_ROOT = Path.home()
sys.path.insert(0, str(AIPASS_ROOT / "aipass_core"))
sys.path.insert(0, str(AIPASS_ROOT))

# Paths
BRANCH_REGISTRY = AIPASS_ROOT / "BRANCH_REGISTRY.json"


def get_branch_list() -> List[str]:
    """
    Get list of registered branches

    Reads BRANCH_REGISTRY.json and extracts branch paths.

    Returns:
        List of branch path strings

    Raises:
        FileNotFoundError: If BRANCH_REGISTRY.json missing
        ValueError: If registry structure invalid
    """
    try:
        if not BRANCH_REGISTRY.exists():
            raise FileNotFoundError(f"Branch registry missing: {BRANCH_REGISTRY}")

        data = json.loads(BRANCH_REGISTRY.read_text())

        if not isinstance(data, dict):
            raise ValueError("Branch registry is not a dictionary")

        branches = data.get("branches", [])

        if not isinstance(branches, list):
            raise ValueError("Branch registry 'branches' is not a list")

        # Extract paths
        paths = []
        for branch in branches:
            if isinstance(branch, dict):
                path = branch.get("path", "")
                if path:
                    paths.append(path)

        return paths

    except FileNotFoundError:
        raise

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in branch registry: {e}") from e

    except ValueError:
        raise

    except Exception as e:
        raise RuntimeError(f"Failed to load branch list: {e}") from e


def get_branch_registry() -> Dict:
    """
    Get full branch registry data

    Reads and returns the complete BRANCH_REGISTRY.json structure.

    Returns:
        Dict containing full registry data

    Raises:
        FileNotFoundError: If BRANCH_REGISTRY.json missing
        ValueError: If registry structure invalid
    """
    try:
        if not BRANCH_REGISTRY.exists():
            raise FileNotFoundError(f"Branch registry missing: {BRANCH_REGISTRY}")

        data = json.loads(BRANCH_REGISTRY.read_text())

        if not isinstance(data, dict):
            raise ValueError("Branch registry is not a dictionary")

        return data

    except FileNotFoundError:
        raise

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in branch registry: {e}") from e

    except ValueError:
        raise

    except Exception as e:
        raise RuntimeError(f"Failed to load branch registry: {e}") from e
