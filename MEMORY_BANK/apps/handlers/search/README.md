# Search Handler

Vector search operations for Memory Bank's ChromaDB collections.

## Files

- `vector_search.py` - Core search handler with ChromaDB query functions
- `search_subprocess.py` - Subprocess wrapper for Python 3.12 compatibility

## Usage

### Via Subprocess (Recommended)

The subprocess wrapper ensures compatibility with Python 3.12 and ChromaDB dependencies.

```python
import subprocess
import json

# Prepare operation
operation = {
    "operation": "search",
    "query_embedding": [...],  # 384-dim list
    "collection_name": "seed_local",
    "n_results": 5
}

# Call subprocess
proc = subprocess.run(
    ["/home/aipass/MEMORY_BANK/apps/handlers/search/search_subprocess.py"],
    input=json.dumps(operation),
    capture_output=True,
    text=True
)

result = json.loads(proc.stdout)
```

## Operations

### 1. encode
Encode query text to embedding vector.

```json
{
  "operation": "encode",
  "query": "how does rollover work?"
}
```

Returns:
```json
{
  "success": true,
  "embedding": [...],  // 384-dim list
  "dimension": 384,
  "model": "all-MiniLM-L6-v2"
}
```

### 2. search
Search a specific collection.

```json
{
  "operation": "search",
  "query_embedding": [...],
  "collection_name": "seed_local",
  "n_results": 5,
  "where": {"branch": "SEED"},  // optional filter
  "db_path": null  // optional, defaults to MEMORY_BANK/.chroma
}
```

Returns:
```json
{
  "success": true,
  "collection": "seed_local",
  "exists": true,
  "count": 3,
  "ids": [...],
  "documents": [...],
  "metadatas": [...],
  "distances": [...]
}
```

### 3. search_all
Search across all collections.

```json
{
  "operation": "search_all",
  "query_embedding": [...],
  "n_results": 5,
  "where": null,
  "db_path": null
}
```

Returns:
```json
{
  "success": true,
  "collections_searched": 4,
  "total_results": 12,
  "results": {
    "seed_local": {
      "documents": [...],
      "metadatas": [...],
      "distances": [...],
      "ids": [...],
      "count": 3
    },
    ...
  }
}
```

### 4. list_collections
List all available collections.

```json
{
  "operation": "list_collections",
  "db_path": null
}
```

Returns:
```json
{
  "success": true,
  "collections": ["seed_local", "aipass_local", ...],
  "count": 4,
  "db_path": "/home/aipass/MEMORY_BANK/.chroma"
}
```

## Direct Import Usage

You can also import functions directly when running in the correct Python environment:

```python
from MEMORY_BANK.apps.handlers.search.vector_search import (
    encode_query,
    search_collection,
    search_all_collections,
    list_collections
)

# Encode query
result = encode_query("how does rollover work?")
embedding = result['embedding']

# Search collection
result = search_collection(
    query_embedding=embedding,
    collection_name="seed_local",
    n_results=10
)

# Search all collections
result = search_all_collections(
    query_embedding=embedding,
    n_results=5
)

# List collections
result = list_collections()
```

## Integration Pattern

1. **Encode once, search many**: Pre-encode queries when searching multiple collections
2. **Metadata filtering**: Use `where` parameter for targeted searches
3. **Distance threshold**: Lower distances = better matches (L2 distance)
4. **Batch operations**: Subprocess calls have ~2s startup cost, combine operations when possible

## Model Details

- Model: `all-MiniLM-L6-v2` (sentence-transformers)
- Dimension: 384
- Normalization: L2 normalized (required for distance calculations)
- Same model as `embedder.py` for compatibility
