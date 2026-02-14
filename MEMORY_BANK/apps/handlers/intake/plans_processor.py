#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: plans_processor.py - Flow Plans Intake Handler
# Date: 2025-11-29
# Version: 0.1.0
# Category: memory_bank/handlers/intake
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-29): Initial version - process plans/ files to vectors
#
# CODE STANDARDS:
#   - Pure handler: No orchestration, just processing logic
#   - Stateless functions
#   - Returns dict with success/error
# =============================================

"""
Flow Plans Intake Handler

Processes markdown files from plans directory:
1. Reads plan files exported by Flow
2. Chunks large files for embedding
3. Vectorizes via ChromaDB (flow_plans collection)
4. Archives old files based on retention config

All settings read from memory_bank.config.json
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Paths
MEMORY_BANK_ROOT = Path.home() / "MEMORY_BANK"
CONFIG_PATH = MEMORY_BANK_ROOT / "memory_bank_json" / "memory_bank.config.json"
CHROMA_PATH = MEMORY_BANK_ROOT / ".chroma"


def load_config() -> dict:
    """Load plans config from memory_bank.config.json"""
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        return config.get('plans', {})
    except Exception as e:
        return {'enabled': False, 'error': str(e)}


def get_plans_path() -> Path:
    """Get the plans directory path from config"""
    config = load_config()
    plans_dir = config.get('path', 'plans')
    return MEMORY_BANK_ROOT / plans_dir


def get_plan_files(extensions: List[str] = None) -> List[Path]:
    """
    Get all files from plans directory sorted by modification time (newest first).

    Args:
        extensions: List of extensions to include (e.g., ['.md'])

    Returns:
        List of Path objects sorted newest to oldest
    """
    if extensions is None:
        extensions = ['.md']

    plans_path = get_plans_path()
    if not plans_path.exists():
        return []

    files = []
    for ext in extensions:
        files.extend(plans_path.glob(f'*{ext}'))

    # Sort by modification time, newest first
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return files


def read_file_content(file_path: Path) -> dict:
    """
    Read content from a file.

    Returns:
        dict with 'success', 'content', 'metadata'
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        stat = file_path.stat()

        return {
            'success': True,
            'content': content,
            'metadata': {
                'filename': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'extension': file_path.suffix
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def chunk_content(content: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict[str, Any]]:
    """
    Split content into overlapping chunks for embedding.

    Args:
        content: Full text content
        chunk_size: Target size per chunk (characters)
        overlap: Overlap between chunks

    Returns:
        List of dicts with 'text' and 'chunk_index'
    """
    if len(content) <= chunk_size:
        return [{'text': content, 'chunk_index': 0}]

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(content):
        end = start + chunk_size

        # Try to break at paragraph or sentence
        if end < len(content):
            # Look for paragraph break
            para_break = content.rfind('\n\n', start, end)
            if para_break > start + chunk_size // 2:
                end = para_break + 2
            else:
                # Look for sentence break
                sentence_break = content.rfind('. ', start, end)
                if sentence_break > start + chunk_size // 2:
                    end = sentence_break + 2

        chunk_text = content[start:end].strip()
        if chunk_text:
            chunks.append({
                'text': chunk_text,
                'chunk_index': chunk_index
            })
            chunk_index += 1

        start = end - overlap if end < len(content) else len(content)

    return chunks


def extract_plan_metadata(filename: str) -> dict:
    """
    Extract TRL metadata from plan filename.

    Format: {path}-{TYPE}-{CATEGORY}-{ACTION}-PLAN{NUM}-{DATE}.md
    Example: -home-aipass-seed-SEED-SEC-IMP-PLAN0201-20251129.md

    Returns:
        dict with type, category, action, plan_number
    """
    metadata = {}

    # Extract PLAN number
    if 'PLAN' in filename:
        try:
            plan_part = filename.split('PLAN')[1]
            plan_num = ''.join(c for c in plan_part.split('-')[0] if c.isdigit())
            metadata['plan_number'] = plan_num
        except Exception:
            pass

    # Extract TRL tags (look for uppercase segments before PLAN)
    parts = filename.replace('.md', '').split('-')
    uppercase_parts = [p for p in parts if p.isupper() and len(p) <= 6 and p != 'PLAN']

    if len(uppercase_parts) >= 3:
        metadata['type'] = uppercase_parts[0]  # e.g., SEED
        metadata['category'] = uppercase_parts[1]  # e.g., SEC
        metadata['action'] = uppercase_parts[2]  # e.g., IMP
        metadata['trl_tag'] = f"{uppercase_parts[0]}-{uppercase_parts[1]}-{uppercase_parts[2]}"

    return metadata


def process_file_to_vectors(file_path: Path, collection_name: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> dict:
    """
    Process a single plan file: read, chunk, and store vectors.

    Args:
        file_path: Path to the file
        collection_name: ChromaDB collection name
        chunk_size: Characters per chunk
        chunk_overlap: Overlap between chunks

    Returns:
        dict with 'success', 'chunks_stored', 'error'
    """
    # Read file
    read_result = read_file_content(file_path)
    if not read_result['success']:
        return read_result

    content = read_result['content']
    file_metadata = read_result['metadata']

    # Extract plan-specific metadata from filename
    plan_metadata = extract_plan_metadata(file_path.name)

    # Chunk content
    chunks = chunk_content(content, chunk_size, chunk_overlap)

    # Import ChromaDB and sentence transformers (late import for venv compatibility)
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer

        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        collection = client.get_or_create_collection(name=collection_name)
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Generate embeddings and store
        documents = []
        ids = []
        metadatas = []

        for chunk in chunks:
            doc_id = f"plan_{file_path.stem}_{chunk['chunk_index']}"
            documents.append(chunk['text'])
            ids.append(doc_id)

            # Combine file and plan metadata
            chunk_metadata = {
                'source': file_metadata['filename'],
                'chunk_index': chunk['chunk_index'],
                'total_chunks': len(chunks),
                'processed_at': datetime.now().isoformat(),
                'type': 'flow_plan'
            }
            # Add TRL metadata if available
            chunk_metadata.update(plan_metadata)
            metadatas.append(chunk_metadata)

        # Batch encode
        embeddings = model.encode(documents).tolist()

        # Upsert (update if exists, insert if not)
        collection.upsert(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )

        return {
            'success': True,
            'file': file_metadata['filename'],
            'chunks_stored': len(chunks),
            'collection': collection_name,
            'plan_metadata': plan_metadata
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def archive_old_plans(keep_recent: int, archive_path: str = 'plans/.archive') -> dict:
    """
    Archive plans beyond the keep_recent limit.

    Args:
        keep_recent: Number of files to keep in plans/
        archive_path: Subdirectory for archived files

    Returns:
        dict with 'success', 'archived_count', 'kept_count'
    """
    config = load_config()
    extensions = config.get('supported_extensions', ['.md'])

    files = get_plan_files(extensions)

    if len(files) <= keep_recent:
        return {
            'success': True,
            'archived_count': 0,
            'kept_count': len(files),
            'message': 'No plans need archiving'
        }

    # Files to keep (most recent)
    keep_files = files[:keep_recent]
    archive_files = files[keep_recent:]

    # Create archive directory
    archive_dir = MEMORY_BANK_ROOT / archive_path
    archive_dir.mkdir(parents=True, exist_ok=True)

    archived_count = 0
    errors = []

    for file_path in archive_files:
        try:
            dest = archive_dir / file_path.name
            # If file exists in archive, add timestamp
            if dest.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                dest = archive_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"

            shutil.move(str(file_path), str(dest))
            archived_count += 1
        except Exception as e:
            errors.append(f"{file_path.name}: {e}")

    return {
        'success': len(errors) == 0,
        'archived_count': archived_count,
        'kept_count': len(keep_files),
        'errors': errors if errors else None
    }


def process_plans() -> dict:
    """
    Main entry point: Process all plans files.

    Reads config, processes files to vectors, archives old files.

    Returns:
        dict with full processing results
    """
    config = load_config()

    if not config.get('enabled', False):
        return {'success': False, 'error': 'plans processing is disabled in config'}

    keep_recent = config.get('keep_recent', 50)
    collection_name = config.get('collection_name', 'flow_plans')
    chunk_size = config.get('chunk_size', 1000)
    chunk_overlap = config.get('chunk_overlap', 100)
    extensions = config.get('supported_extensions', ['.md'])
    archive_path = config.get('archive_path', 'plans/.archive')

    # Get all files
    files = get_plan_files(extensions)

    if not files:
        return {
            'success': True,
            'message': 'No plans to process',
            'files_processed': 0
        }

    results = {
        'success': True,
        'files_found': len(files),
        'files_processed': 0,
        'total_chunks': 0,
        'errors': [],
        'processed_files': []
    }

    # Process each file
    for file_path in files:
        result = process_file_to_vectors(
            file_path,
            collection_name,
            chunk_size,
            chunk_overlap
        )

        if result['success']:
            results['files_processed'] += 1
            results['total_chunks'] += result.get('chunks_stored', 0)
            results['processed_files'].append({
                'file': result['file'],
                'chunks': result.get('chunks_stored', 0),
                'trl': result.get('plan_metadata', {}).get('trl_tag', 'unknown')
            })
        else:
            results['errors'].append(f"{file_path.name}: {result.get('error')}")

    # Archive old files
    archive_result = archive_old_plans(keep_recent, archive_path)
    results['archive'] = archive_result

    if results['errors']:
        results['success'] = False

    return results


def get_plans_status() -> dict:
    """
    Get current status of plans processing.

    Returns:
        dict with file counts, config, and collection info
    """
    config = load_config()
    extensions = config.get('supported_extensions', ['.md'])
    files = get_plan_files(extensions)

    # Get collection count
    collection_count = 0
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        collection_name = config.get('collection_name', 'flow_plans')
        if collection_name in [c.name for c in client.list_collections()]:
            collection = client.get_collection(name=collection_name)
            collection_count = collection.count()
    except Exception:
        pass

    return {
        'enabled': config.get('enabled', False),
        'files_in_plans': len(files),
        'keep_recent': config.get('keep_recent', 50),
        'vectors_stored': collection_count,
        'collection_name': config.get('collection_name', 'flow_plans'),
        'newest_file': files[0].name if files else None,
        'oldest_file': files[-1].name if files else None
    }


# Standalone execution for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        status = get_plans_status()
        print(json.dumps(status, indent=2))
    else:
        print("Processing plans...")
        result = process_plans()
        print(json.dumps(result, indent=2))
