#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: storage.py - Symbolic Fragment Storage Handler
# Date: 2026-02-04
# Version: 0.1.0
# Category: memory_bank/handlers/symbolic
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2026-02-04): Initial version - Fragmented Memory Phase 2
#
# CODE STANDARDS:
#   - Handler independence: No module imports
#   - Error handling: Return status dicts (3-tier architecture)
#   - File size: <300 lines target
# =============================================

"""
Symbolic Fragment Storage Handler

Stores symbolic memory fragments in ChromaDB for retrieval.
Fragments contain compressed symbolic dimensions as metadata for
both vector similarity search and dimension-based filtering.

Key Functions:
    - create_fragment() - create fragment from conversation analysis
    - store_fragment() - store single fragment in ChromaDB
    - store_fragments_batch() - batch storage for multiple fragments
    - flatten_dimensions() - convert nested dimensions to ChromaDB metadata
"""

import sys
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Infrastructure setup
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

# Handler imports (domain-organized, no modules)
from MEMORY_BANK.apps.handlers.vector import embedder


# =============================================================================
# CONSTANTS
# =============================================================================

COLLECTION_NAME = "symbolic_fragments"


# =============================================================================
# FRAGMENT CREATION
# =============================================================================

def create_fragment(
    analysis: Dict[str, Any],
    content: str | None = None,
    source_branch: str | None = None
) -> Dict[str, Any]:
    """
    Create a fragment from conversation analysis

    Takes output from analyze_conversation() and creates a storable
    fragment with unique ID, compressed content, and flattened dimensions.

    Args:
        analysis: Output from analyze_conversation() with dimensions and metadata
        content: Optional content override (defaults to generated essence)
        source_branch: Optional branch name for filtering (e.g., 'SEED')

    Returns:
        Dict with 'success', 'fragment' containing storable fragment
    """
    if not analysis:
        return {
            'success': False,
            'error': 'No analysis provided'
        }

    dimensions = analysis.get('dimensions', {})
    metadata = analysis.get('metadata', {})

    # Generate unique ID with UUID suffix for uniqueness
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid.uuid4().hex[:8]
    frag_id = f"frag_{timestamp_str}_{unique_suffix}"

    # Generate content essence if not provided
    if content is None:
        content = _generate_essence(dimensions, metadata)

    # Build fragment structure
    frag_data = {
        'id': frag_id,
        'content': content,
        'dimensions': {
            'technical': dimensions.get('technical', []),
            'emotional': dimensions.get('emotional', []),
            'collaboration': dimensions.get('collaboration', []),
            'learnings': dimensions.get('learnings', []),
            'triggers': dimensions.get('triggers', [])
        },
        'metadata': {
            'timestamp': metadata.get('timestamp', timestamp.isoformat()),
            'message_count': analysis.get('message_count', 0),
            'depth': metadata.get('depth', 'unknown'),
            'total_words': metadata.get('total_words', 0)
        }
    }

    if source_branch:
        frag_data['metadata']['source_branch'] = source_branch

    return {
        'success': True,
        'fragment': frag_data
    }


def _generate_essence(dimensions: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    """
    Generate compressed symbolic essence from dimensions

    Creates a human-readable summary that captures the conversation's
    symbolic meaning for embedding and display.

    Args:
        dimensions: Extracted symbolic dimensions
        metadata: Conversation metadata

    Returns:
        String essence suitable for embedding
    """
    parts = []

    # Technical flow
    technical = dimensions.get('technical', [])
    if technical and 'no_conversation' not in technical:
        parts.append(f"Technical: {', '.join(technical)}")

    # Emotional arc
    emotional = dimensions.get('emotional', [])
    if emotional and 'neutral' not in emotional:
        parts.append(f"Emotional: {', '.join(emotional)}")

    # Collaboration patterns
    collaboration = dimensions.get('collaboration', [])
    if collaboration and 'no_interaction' not in collaboration:
        parts.append(f"Collaboration: {', '.join(collaboration)}")

    # Key learnings
    learnings = dimensions.get('learnings', [])
    if learnings and 'no_insights' not in learnings:
        parts.append(f"Learnings: {', '.join(learnings)}")

    # Context triggers
    triggers = dimensions.get('triggers', [])
    if triggers:
        parts.append(f"Context: {', '.join(triggers[:5])}")

    # Add depth indicator
    depth = metadata.get('depth', 'unknown')
    if depth != 'unknown':
        parts.append(f"Depth: {depth}")

    if not parts:
        return "General conversation with no distinctive symbolic patterns"

    return ". ".join(parts)


# =============================================================================
# METADATA FLATTENING
# =============================================================================

def flatten_dimensions(fragment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten fragment dimensions for ChromaDB metadata storage

    ChromaDB metadata must be flat (string/int/float/bool).
    This converts nested dimensions to indexed keys.

    Args:
        fragment: Fragment dict with nested dimensions

    Returns:
        Dict with 'success', 'metadata' containing flattened metadata
    """
    if not fragment:
        return {
            'success': False,
            'error': 'No fragment provided'
        }

    dimensions = fragment.get('dimensions', {})
    metadata = fragment.get('metadata', {})

    flat = {}

    # Flatten each dimension list to indexed keys
    for dim_name, dim_values in dimensions.items():
        if dim_name == 'triggers':
            # Store triggers as comma-separated string for contains search
            flat['triggers'] = ','.join(dim_values) if dim_values else ''
        else:
            # Store other dimensions as indexed keys
            for i, value in enumerate(dim_values[:5]):  # Limit to 5 per dimension
                flat[f'{dim_name}_{i}'] = value

    # Add metadata fields
    flat['timestamp'] = metadata.get('timestamp', '')
    flat['message_count'] = metadata.get('message_count', 0)
    flat['depth'] = metadata.get('depth', 'unknown')
    flat['total_words'] = metadata.get('total_words', 0)

    if 'source_branch' in metadata:
        flat['source_branch'] = metadata['source_branch']

    return {
        'success': True,
        'metadata': flat
    }


# =============================================================================
# STORAGE FUNCTIONS
# =============================================================================

def store_fragment(
    fragment: Dict[str, Any],
    db_path: Path | None = None
) -> Dict[str, Any]:
    """
    Store a single fragment in ChromaDB

    Generates embedding from fragment content and stores with
    flattened dimensions as metadata.

    Args:
        fragment: Fragment dict from create_fragment()
        db_path: Optional ChromaDB path (default: MEMORY_BANK/.chroma)

    Returns:
        Dict with 'success', storage details
    """
    if not fragment:
        return {
            'success': False,
            'error': 'No fragment provided'
        }

    # Import shared client
    from MEMORY_BANK.apps.handlers.symbolic.chroma_client import get_chroma_client

    frag_content = fragment.get('content', '')
    frag_id = fragment.get('id', '')

    if not frag_content or not frag_id:
        return {
            'success': False,
            'error': 'Fragment missing content or id'
        }

    # Generate embedding
    embed_result = embedder.encode_batch([frag_content])
    if not embed_result.get('success'):
        return {
            'success': False,
            'error': f"Embedding failed: {embed_result.get('error', 'Unknown error')}"
        }

    embed_vectors = embed_result.get('embeddings', [])
    if not embed_vectors:
        return {
            'success': False,
            'error': 'No embedding generated'
        }

    embed_vec = embed_vectors[0]
    if hasattr(embed_vec, 'tolist'):
        embed_vec = embed_vec.tolist()

    # Flatten dimensions for metadata
    flat_result = flatten_dimensions(fragment)
    if not flat_result.get('success'):
        return flat_result

    flat_meta = flat_result['metadata']

    try:
        client = get_chroma_client(db_path)

        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"type": "symbolic_fragment"}
        )

        # Store fragment
        collection.add(
            ids=[frag_id],
            embeddings=[embed_vec],
            documents=[frag_content],
            metadatas=[flat_meta]
        )

        return {
            'success': True,
            'fragment_id': frag_id,
            'collection': COLLECTION_NAME,
            'total_fragments': collection.count()
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Storage failed: {e}"
        }


def store_fragments_batch(
    fragments: List[Dict[str, Any]],
    db_path: Path | None = None
) -> Dict[str, Any]:
    """
    Store multiple fragments in ChromaDB in batch

    More efficient than storing one at a time when processing
    multiple conversations.

    Args:
        fragments: List of fragment dicts from create_fragment()
        db_path: Optional ChromaDB path (default: MEMORY_BANK/.chroma)

    Returns:
        Dict with 'success', batch storage details
    """
    if not fragments:
        return {
            'success': True,
            'message': 'No fragments to store',
            'stored': 0
        }

    # Late import
    import chromadb
    from chromadb.config import Settings

    # Extract content for batch embedding
    content_list = []
    valid_frags = []

    for frag in fragments:
        frag_content = frag.get('content', '')
        frag_id = frag.get('id', '')
        if frag_content and frag_id:
            content_list.append(frag_content)
            valid_frags.append(frag)

    if not valid_frags:
        return {
            'success': False,
            'error': 'No valid fragments to store'
        }

    # Batch embedding
    embed_result = embedder.encode_batch(content_list)
    if not embed_result.get('success'):
        return {
            'success': False,
            'error': f"Batch embedding failed: {embed_result.get('error', 'Unknown error')}"
        }

    embed_vectors = embed_result.get('embeddings', [])
    if len(embed_vectors) != len(valid_frags):
        return {
            'success': False,
            'error': 'Embedding count mismatch'
        }

    # Prepare batch data
    batch_ids = []
    batch_embeddings = []
    batch_documents = []
    batch_metadatas = []

    for i, frag in enumerate(valid_frags):
        vec = embed_vectors[i]
        if hasattr(vec, 'tolist'):
            vec = vec.tolist()

        flat_result = flatten_dimensions(frag)
        if not flat_result.get('success'):
            continue

        batch_ids.append(frag['id'])
        batch_embeddings.append(vec)
        batch_documents.append(frag['content'])
        batch_metadatas.append(flat_result['metadata'])

    # Import shared client
    from MEMORY_BANK.apps.handlers.symbolic.chroma_client import get_chroma_client

    try:
        client = get_chroma_client(db_path)

        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"type": "symbolic_fragment"}
        )

        # Batch store
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_documents,
            metadatas=batch_metadatas
        )

        return {
            'success': True,
            'stored': len(batch_ids),
            'collection': COLLECTION_NAME,
            'total_fragments': collection.count()
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Batch storage failed: {e}"
        }
