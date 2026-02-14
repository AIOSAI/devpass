#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""Vector memory wrapper for Nexus v2 - uses Memory Bank's ChromaDB subprocess"""

import json
import sys
import subprocess
from pathlib import Path
from typing import Optional

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Memory Bank ChromaDB subprocess paths
MEMORY_BANK_VENV_PYTHON = Path.home() / "MEMORY_BANK" / ".venv" / "bin" / "python3"
CHROMA_SUBPROCESS_SCRIPT = Path.home() / "MEMORY_BANK" / "apps" / "handlers" / "storage" / "chroma_subprocess.py"

COLLECTION_NAME = "nexus_memories"

def _call_chroma_subprocess(operation: str, **kwargs) -> dict:
    """Call Memory Bank's ChromaDB subprocess with JSON I/O."""
    if not MEMORY_BANK_VENV_PYTHON.exists():
        return {"error": "Memory Bank venv not found", "success": False}

    if not CHROMA_SUBPROCESS_SCRIPT.exists():
        return {"error": "ChromaDB subprocess script not found", "success": False}

    try:
        # Build request
        request = {
            "operation": operation,
            "collection": COLLECTION_NAME,
            **kwargs
        }

        # Call subprocess
        result = subprocess.run(
            [str(MEMORY_BANK_VENV_PYTHON), str(CHROMA_SUBPROCESS_SCRIPT)],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return {"error": f"Subprocess failed: {result.stderr}", "success": False}

        # Parse response
        return json.loads(result.stdout)

    except subprocess.TimeoutExpired:
        return {"error": "Subprocess timeout", "success": False}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response: {e}", "success": False}
    except Exception as e:
        return {"error": f"Subprocess error: {e}", "success": False}

def store_memory(text: str, metadata: Optional[dict] = None) -> bool:
    """Store a memory in vector database."""
    result = _call_chroma_subprocess(
        "add",
        documents=[text],
        metadatas=[metadata] if metadata else None
    )

    if not result.get("success", False):
        # Graceful fallback - log but don't crash
        return False

    return True

def search_memories(query: str, n: int = 5) -> list:
    """Search vector memories by semantic similarity."""
    result = _call_chroma_subprocess(
        "query",
        query_texts=[query],
        n_results=n
    )

    if not result.get("success", False):
        # Graceful fallback - return empty list
        return []

    # Extract documents from response
    documents = result.get("documents", [[]])[0] if result.get("documents") else []
    metadatas = result.get("metadatas", [[]])[0] if result.get("metadatas") else []

    # Combine documents and metadata
    results = []
    for i, doc in enumerate(documents):
        results.append({
            "text": doc,
            "metadata": metadatas[i] if i < len(metadatas) else {}
        })

    return results

def get_memory_count() -> int:
    """Get count of stored vector memories."""
    result = _call_chroma_subprocess("count")

    if not result.get("success", False):
        # Graceful fallback - return 0
        return 0

    return result.get("count", 0)
