# MEMORY_BANK

## Overview
MEMORY_BANK is the global vector-based memory system for the AIPass ecosystem. It provides semantic search across all branch memories and document archives.

## Data Sources
1. **Branch Memories** - Rolled over from `*.local.json` and `*.observations.json` when files exceed 600 lines
2. **Memory Pool** - Standalone documents dropped in `memory_pool/` for vectorization
3. **Flow Plans** - Closed plans from Flow system, exported to `plans/` with TRL metadata
4. **Code Archive** - Old/archived code indexed (not vectorized) for reference

## Purpose
- **Archive**: Store rolled-off memories and documents as 384-dimensional embeddings
- **Search**: One global semantic search across all historical content
- **Auto-Process**: New files in memory_pool auto-vectorized on next command
- **Preserve**: No knowledge lost, just transformed into searchable vectors

## Architecture

### Directory Structure
```
apps/
├── memory_bank.py          # Main entry point CLI
├── modules/
│   ├── rollover.py         # Rollover orchestration
│   └── search.py           # Search orchestration
├── handlers/
│   ├── intake/             # Memory pool processing
│   ├── json/               # JSON file operations
│   ├── monitor/            # Memory file watching + auto-processing
│   ├── rollover/           # Extraction and embedding
│   ├── search/             # Vector search subprocess
│   ├── storage/            # ChromaDB persistence
│   ├── tracking/           # Line counting and metadata
│   └── vector/             # Embedding operations

memory_pool/                # Drop files here for auto-vectorization
├── .archive/               # Archived files (beyond keep_recent limit)
└── *.md, *.txt, *.json     # Active files (kept: 5 most recent)

plans/                      # Closed Flow plans (auto-exported)
├── .archive/               # Archived plans (beyond keep_recent limit)
└── *-PLAN*.md              # Active plans (kept: 5 most recent)

code_archive/               # Archived code from across AIPass
├── ai_mail/                # Old AI_Mail code
├── api/                    # Old API code
├── backup/                 # Old backup code
├── error_handling/         # Old error handlers
├── migration/              # Migration scripts
├── misc/                   # Uncategorized
└── index.json              # Auto-generated catalog

memory_bank_json/
└── memory_bank.config.json # Configuration (retention, chunk size, etc.)
```

### Core Components
- **handlers/archive/** - Code archive indexing (extracts docstrings, functions, classes)
- **handlers/intake/** - Memory pool + plans processing (vectorize + archive)
- **handlers/monitor/** - Startup checks, auto-triggers rollover, pool, and plans processing
- **handlers/rollover/** - Extracts oldest entries from memory files
- **handlers/search/** - Vector similarity search via subprocess
- **handlers/symbolic/** - Fragmented memory extraction and retrieval
- **handlers/vector/** - Embedding operations (all-MiniLM-L6-v2)
- **handlers/storage/** - ChromaDB persistence layer

### Collections (ChromaDB)
| Collection | Source | Vectors |
|------------|--------|---------|
| `memory_pool_docs` | Archived documents | ~3,500 |
| `flow_plans` | Closed Flow plans | ~140 |
| `symbolic_fragments` | Fragmented memory | varies |
| `seed_local` | SEED branch memories | 56 |
| `aipass_local` | Root AIPASS memories | 24 |
| `drone_local` | DRONE branch memories | 16 |
| `*_local` | Other branch memories | varies |

### Storage Architecture
- **Global**: All vectors in `/home/aipass/MEMORY_BANK/.chroma/`
- **Local**: Branch-specific copies in `[branch]/.chroma/`
- **Dual Write**: Same vectors stored in both locations

## Auto-Processing

**Memory Pool** - Drop files, they get vectorized automatically:
1. Add `.md`, `.txt`, or `.json` file to `memory_pool/`
2. Next command (drone, seed, etc.) triggers startup check
3. Vectorizes all files to ChromaDB
4. Archives oldest beyond `keep_recent` (5) to `.archive/`
5. Search finds content immediately

**Flow Plans** - Closed plans auto-vectorized:
1. Flow closes a plan → exports to `plans/`
2. Startup check triggers plans_processor
3. Vectorizes with TRL metadata (Type-Category-Action)
4. Archives oldest beyond `keep_recent` (5) to `.archive/`
5. Searchable by topic or TRL tags

**Branch Memories** - Auto-rollover when exceeding 600 lines:
1. Memory file modified, exceeds 600 lines
2. Startup check detects overage
3. Extracts oldest sessions/entries
4. Embeds to vectors, stores in ChromaDB
5. File reduced to ~500 lines (100-line buffer)

## Usage

Note: Use Memory Bank's Python venv for all commands.

### Search
```bash
# Search all memories and documents
python3 apps/modules/search.py search "query"

# Filter by branch
python3 apps/modules/search.py search "query" --branch SEED

# Filter by type and limit results
python3 apps/modules/search.py search "query" --type local --n 10
```

### Memory Pool
```bash
# Check pool status
python3 apps/handlers/intake/pool_processor.py status

# Manual process (usually automatic)
python3 apps/handlers/intake/pool_processor.py
```

### Rollover
```bash
# Manual rollover (usually automatic)
python3 apps/modules/rollover.py
```

## Configuration

Edit `memory_bank_json/memory_bank.config.json`:

```json
{
  "memory_pool": {
    "enabled": true,
    "keep_recent": 5,
    "supported_extensions": [".md", ".txt", ".json"],
    "archive_path": "memory_pool/.archive"
  },
  "plans": {
    "enabled": true,
    "keep_recent": 5,
    "collection_name": "flow_plans",
    "archive_path": "plans/.archive"
  }
}
```

## Fragmented Memory

**Fragmented Memory** enables random relevant memories to surface during conversation without explicit queries - like human associative memory.

### Symbolic Dimensions
Conversations are analyzed across 5 symbolic dimensions:
- **Technical Flow** - problem/debug/breakthrough patterns
- **Emotional Journey** - frustration/excitement arcs
- **Collaboration** - user_directed/balanced dynamics
- **Key Learnings** - discoveries, insights
- **Context Triggers** - keywords that should surface this memory

### Usage
```bash
# Demo analysis
python3 apps/modules/symbolic.py demo

# Analyze conversation file
python3 apps/modules/symbolic.py analyze chat.json

# Search fragments
python3 apps/modules/symbolic.py fragments "debugging"

# Test hook surfacing
python3 apps/modules/symbolic.py hook-test "I'm stuck on this error"
```

### Configuration
Edit `apps/json_templates/custom/fragmented_memory_config.json`:
```json
{
  "enabled": true,
  "threshold": 0.3,
  "max_fragments_per_session": 3,
  "min_messages_between": 10,
  "cooldown_seconds": 300
}
```

## Technical Details
- **Embedding**: all-MiniLM-L6-v2 (384 dimensions)
- **Vector DB**: ChromaDB with persistent storage
- **Python**: 3.14 via isolated `.venv`
- **Similarity**: 40% minimum threshold filters noise

---

**Branch**: MEMORY_BANK | **Created**: 2025-11-08

*The memory never forgets - it just transforms.*