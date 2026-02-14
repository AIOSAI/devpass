# Memory Bank Search System Plan

**Created:** 2025-11-27
**Status:** Planning
**Branch:** MEMORY_BANK

---

## Objective

Build a search interface that allows branches to query:
1. Their own local `.chroma` database
2. The global Memory Bank `.chroma` database

Access via drone command: `drone @memory_bank search "query" [--local] [--global]`

---

## Research Findings

### ChromaDB Query API

**Core Function:** `collection.query()`

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `query_texts` | List[str] | Text queries (auto-embedded) |
| `query_embeddings` | List[List[float]] | Pre-computed embeddings |
| `n_results` | int | Number of results (default: 10) |
| `where` | Dict | Metadata filter |
| `where_document` | Dict | Document content filter |
| `include` | List[str] | What to return (documents, metadatas, distances, embeddings) |

**Basic Example:**
```python
results = collection.query(
    query_texts=["What happened in session 5?"],
    n_results=5,
    where={"branch": "SEED"},
    include=["documents", "metadatas", "distances"]
)
```

**Return Format:**
```python
{
    'ids': [['id1', 'id2', ...]],
    'documents': [['doc1', 'doc2', ...]],
    'metadatas': [[{...}, {...}, ...]],
    'distances': [[0.1, 0.2, ...]]  # Lower = more similar
}
```

### Metadata Filtering

**Operators:**
- Equality: `$eq`, `$ne`
- Comparison: `$gt`, `$gte`, `$lt`, `$lte` (numeric)
- List: `$in`, `$nin`
- Logical: `$and`, `$or`

**Filter by Branch:**
```python
where={"branch": "DRONE"}
```

**Filter by Memory Type:**
```python
where={"memory_type": "local"}  # or "observations"
```

**Combined Filter:**
```python
where={"$and": [
    {"branch": "SEED"},
    {"memory_type": "local"}
]}
```

### Embedding Consistency

**CRITICAL:** Query embeddings MUST use same model as stored embeddings.
- Our model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- Already used in `embedder.py` handler

### Distance Metric

- Using cosine similarity (default in ChromaDB)
- Lower distance = more similar
- Range: 0.0 (identical) to 2.0 (opposite)

---

## Architecture

### Handler Layer

**File:** `apps/handlers/search/vector_search.py`

```
Responsibilities:
- Query ChromaDB collections
- Return raw results (no formatting)
- Handle both local and global databases
- Embed query text using same model as storage
```

**Functions:**
```python
def search_collection(
    query: str,
    collection_name: str,
    n_results: int = 5,
    where: Dict | None = None,
    db_path: Path | None = None
) -> Dict[str, Any]

def search_branch(
    query: str,
    branch: str,
    memory_type: str = "all",
    n_results: int = 5
) -> Dict[str, Any]

def search_global(
    query: str,
    branch_filter: str | None = None,
    memory_type: str = "all",
    n_results: int = 5
) -> Dict[str, Any]
```

### Module Layer

**File:** `apps/modules/search.py`

```
Responsibilities:
- Orchestrate search workflow
- Format results for display
- Handle CLI commands
- Combine local + global results
```

**Commands:**
```
search <query>              # Search global Memory Bank
search <query> --local      # Search calling branch's local .chroma
search <query> --all        # Search both local + global
search <query> --branch X   # Search specific branch in global
```

### Entry Point Integration

**File:** `apps/memory_bank.py`

Add route for search command.

### Drone Integration

Command: `drone @memory_bank search "query" [options]`

---

## Implementation Steps

### Phase 1: Handler

1. Create `apps/handlers/search/` directory
2. Create `vector_search.py` handler
3. Implement `search_collection()` - raw ChromaDB query
4. Implement `search_branch()` - branch-specific search
5. Implement `search_global()` - global search with filters
6. Use subprocess pattern for Python 3.12 compatibility (like storage)

### Phase 2: Module

1. Create `apps/modules/search.py`
2. Implement `handle_command()` with help
3. Add result formatting with Rich
4. Add relevance scoring display
5. Combine local + global results

### Phase 3: Integration

1. Add search route to `memory_bank.py`
2. Register with drone for `@memory_bank search`
3. Test end-to-end

### Phase 4: Subprocess Wrapper

1. Create `apps/handlers/search/search_subprocess.py`
2. Like chroma_subprocess.py but for querying
3. Ensures Python 3.12 compatibility

---

## Open Questions

1. **Result Format:** How much context to show per result?
   - Just snippet? Full document? Metadata summary?

2. **Ranking:** How to combine local + global results?
   - Interleave by distance? Local first?

3. **Branch Detection:** How does search know calling branch?
   - PWD detection? Explicit flag?

4. **Future Expansion:**
   - Search Python files (junkyard)?
   - Search non-vectorized memory files?
   - Full-text search fallback?

---

## Sources

- [ChromaDB Query Docs](https://docs.trychroma.com/docs/querying-collections/query-and-get)
- [Metadata Filtering](https://docs.trychroma.com/docs/querying-collections/metadata-filtering)
- [Chroma Filters Cookbook](https://cookbook.chromadb.dev/core/filters/)
- [DataCamp ChromaDB Tutorial](https://www.datacamp.com/tutorial/chromadb-tutorial-step-by-step-guide)
- [Medium: Semantic Search with Metadata](https://medium.com/@sangal.sachin/chromadb-semantic-search-with-metadata-filters-using-python-456887e5e0cd)

---

## Next Steps

1. Review plan with Patrick
2. Clarify open questions
3. Begin Phase 1 implementation
