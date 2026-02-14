#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: chroma_client.py - Shared ChromaDB Client Handler
# Date: 2026-02-04
# Version: 0.1.0
# Category: memory_bank/handlers/symbolic
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2026-02-04): Initial version - shared singleton ChromaDB client
#
# CODE STANDARDS:
#   - Handler independence: No module imports
#   - Error handling: Return status dicts (3-tier architecture)
# =============================================

"""
Shared ChromaDB Client Handler

Provides a singleton ChromaDB client to avoid "already exists with different settings"
errors when multiple handlers need to access the same database.

Key Functions:
    - get_chroma_client() - get shared ChromaDB PersistentClient
    - get_collection() - get or create a collection
"""

import sys
from typing import Dict, Any
from pathlib import Path

# Infrastructure setup
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_DB_PATH = Path.home() / "MEMORY_BANK" / ".chroma"

# Singleton client cache
_chroma_clients: Dict[str, Any] = {}


# =============================================================================
# CLIENT MANAGEMENT
# =============================================================================

def get_chroma_client(db_path: Path | None = None):
    """
    Get or create a shared ChromaDB client (singleton per path)

    Avoids "already exists with different settings" errors by reusing clients
    or falling back to existing instances.

    Args:
        db_path: Optional path to ChromaDB (default: MEMORY_BANK/.chroma)

    Returns:
        ChromaDB PersistentClient instance
    """
    import chromadb

    if db_path is None:
        db_path = DEFAULT_DB_PATH

    path_str = str(db_path)

    if path_str not in _chroma_clients:
        db_path.mkdir(parents=True, exist_ok=True)
        # Use simple PersistentClient without Settings to avoid pydantic compatibility issues
        _chroma_clients[path_str] = chromadb.PersistentClient(path=path_str)

    return _chroma_clients[path_str]


def get_collection(collection_name: str, db_path: Path | None = None, create: bool = True):
    """
    Get a collection from the shared ChromaDB client

    Args:
        collection_name: Name of the collection
        db_path: Optional path to ChromaDB
        create: If True, create collection if it doesn't exist

    Returns:
        Dict with 'success', 'collection' or 'error'
    """
    try:
        client = get_chroma_client(db_path)

        if create:
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"type": "symbolic_fragment"}
            )
        else:
            collection = client.get_collection(collection_name)

        return {
            'success': True,
            'collection': collection
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
