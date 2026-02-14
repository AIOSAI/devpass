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
│   ├── search.py           # Search orchestration
│   └── symbolic.py         # Fragmented memory orchestration
├── handlers/
│   ├── archive/            # Code archive indexing
│   ├── intake/             # Memory pool + plans processing
│   ├── json/               # JSON file operations
│   ├── learnings/          # Key learnings + recently_completed management
│   ├── monitor/            # Memory file watching + auto-processing
│   ├── rollover/           # Extraction and embedding
│   ├── schema/             # JSON normalization
│   ├── search/             # Vector search subprocess
│   ├── storage/            # ChromaDB persistence
│   ├── symbolic/           # Fragmented memory (extractors, retrieval, hooks)
│   ├── tracking/           # Line counting and metadata
│   └── vector/             # Embedding operations
├── tests/                  # Unit tests (symbolic extractors, storage, retrieval)

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
├── drone/                  # Old Drone code
├── error_handling/         # Old error handlers
├── flow/                   # Old Flow code
├── migration/              # Migration scripts
├── misc/                   # Uncategorized
├── prax/                   # Old Prax code
└── index.json              # Auto-generated catalog

memory_bank_json/
└── memory_bank.config.json # Configuration (retention, chunk size, etc.)
```

### Core Components
- **handlers/archive/** - Code archive indexing (extracts docstrings, functions, classes)
- **handlers/intake/** - Memory pool + plans processing (vectorize + archive)
- **handlers/learnings/** - Key learnings and recently_completed list management (timestamps, limits, vectorization of pruned entries)
- **handlers/monitor/** - Startup checks, auto-triggers rollover, pool, and plans processing; syncs line count metadata
- **handlers/rollover/** - Extracts oldest entries from memory files
- **handlers/schema/** - JSON normalization utilities
- **handlers/search/** - Vector similarity search via subprocess
- **handlers/storage/** - ChromaDB persistence layer
- **handlers/symbolic/** - Fragmented memory: 5 extractors, storage, retrieval, hook surfacing
- **handlers/tracking/** - Line counting and metadata sync
- **handlers/vector/** - Embedding operations (all-MiniLM-L6-v2)

### Collections (ChromaDB)
| Collection | Source | Vectors |
|------------|--------|---------|
| `memory_pool_docs` | Archived documents | ~3,500 |
| `flow_plans` | Closed Flow plans | ~392 |
| `seed_local` | SEED branch memories | 71 |
| `drone_local` | DRONE branch memories | 48 |
| `dev_central_local` | DEV_CENTRAL branch memories | 31 |
| `memory_bank_local` | MEMORY_BANK branch memories | 26 |
| `dev_central_key_learnings` | DEV_CENTRAL pruned learnings | 25 |
| `aipass_local` | Root AIPASS memories | 24 |
| `flow_local` | FLOW branch memories | 18 |
| `api_local` | API branch memories | 11 |
| `trigger_local` | TRIGGER branch memories | 10 |
| `dev_central_recently_completed` | DEV_CENTRAL pruned completions | 7 |
| `cortex_local` | CORTEX branch memories | 6 |
| `cortex_observations` | CORTEX observation memories | 6 |
| `symbolic_fragments` | Fragmented memory | 3 |
| **Total** | **15 collections** | **~4,180** |

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

### Via Drone (preferred)
```bash
# Search all memories and documents
drone @memory_bank search "query"

# Help and available commands
drone @memory_bank --help

# System status
drone @memory_bank status
```

### Direct (use Memory Bank's .venv Python)
```bash
# Search with filters
python3 apps/modules/search.py search "query"
python3 apps/modules/search.py search "query" --branch SEED
python3 apps/modules/search.py search "query" --type local --n 10

# Memory pool status / manual process
python3 apps/handlers/intake/pool_processor.py status
python3 apps/handlers/intake/pool_processor.py

# Manual rollover (usually automatic)
python3 apps/modules/rollover.py

# Key learnings management
python3 apps/handlers/learnings/manager.py process-file --file <path>
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
- **Python**: 3.12 via isolated `.venv` (system uses 3.14; venv required for ChromaDB compatibility)
- **Similarity**: 40% minimum threshold filters noise

---

**Branch**: MEMORY_BANK | **Created**: 2025-11-08 | **Last Updated**: 2026-02-14

*The memory never forgets - it just transforms.*