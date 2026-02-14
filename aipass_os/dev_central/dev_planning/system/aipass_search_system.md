# Plan: AIPass Search System

*Created: 2025-11-26*
*Status: Concept/Placeholder*

---

## Problem

VS Code search returns 5000+ results - useless for finding specific AIPass content.

Need: Targeted search that ONLY searches AIPass ecosystem files with intelligent ranking.

---

## Vision

```bash
drone search "dashboard architecture"
```

Returns:
- Top 5 most relevant files
- Snippet preview with context
- Path + relevance score
- Not 5000 results - just what matters

---

## Potential Architecture

### Option A: Drone + Memory Bank (Vector Search)

```
User: drone search "plan closure workflow"
  ↓
Drone routes to search module
  ↓
Memory Bank queries ChromaDB vectors
  ↓
Returns semantically similar documents
  ↓
Ranked results with snippets
```

**Pros:**
- Semantic search (finds related concepts, not just keywords)
- Already building Memory Bank with ChromaDB
- Can search across all archived plans, observations, docs

**Cons:**
- Requires documents to be vectorized first
- More complex setup

### Option B: Simple Targeted Grep

```
User: drone search "dashboard"
  ↓
Drone runs grep on specific paths only:
  - /home/aipass/**/PLAN*.md
  - /home/aipass/**/*.id.json
  - /home/aipass/**/*.local.json
  - /home/aipass/**/*.observations.json
  - /home/aipass/aipass_os/dev_central/**/*.md
  ↓
Limited to 10 results, ranked by match quality
```

**Pros:**
- Simple, works now
- No vector DB dependency
- Fast for keyword search

**Cons:**
- No semantic understanding
- Just keyword matching

### Option C: Hybrid

- Start with targeted grep (Phase 1)
- Add vector search for Memory Bank archives (Phase 2)
- Merge results with smart ranking (Phase 3)

---

## Search Scope (What to Index)

### Priority 1 - Always Search
- `PLAN*.md` - All plans
- `*.id.json` - Branch identities
- `*.local.json` - Session histories (recent entries only)
- `*.observations.json` - Collaboration patterns
- `dev_central/planning/**/*.md` - System planning docs
- `DOCUMENTS/` folders - Long-term storage

### Priority 2 - Optional
- `README.md` files
- `apps/modules/*.py` docstrings
- `MEMORY_BANK/plans/` archives

### Never Search
- `__pycache__/`
- `.backup/`
- `node_modules/`
- Binary files

---

## Interface Ideas

```bash
# Basic search
drone search "error handling"

# Search specific type
drone search --plans "dashboard"
drone search --memory "vector database"
drone search --docs "architecture"

# Search specific branch
drone search @flow "close plan"

# Recent only (last 7 days)
drone search --recent "config migration"
```

---

## Integration Points

| System | Role |
|--------|------|
| **Drone** | CLI interface, command routing |
| **Memory Bank** | Vector storage, semantic search |
| **Dev Central** | Planning docs, architecture |
| **Flow** | Plan search, closed plan lookup |

---

## Questions to Resolve

1. **Who owns search?** Drone (router) or dedicated search branch?
2. **Vector vs keyword?** Start simple or go semantic from day 1?
3. **Index update frequency?** Real-time or periodic rebuild?
4. **Result format?** JSON for AI, or formatted for terminal?

---

## Success Criteria

- `drone search X` returns useful results in <2 seconds
- Top 5 results are relevant 80%+ of the time
- Patrick can find "that thing we planned" without remembering where
- No more 5000-result VS Code searches

---

## Related

- Memory Bank (ChromaDB integration)
- Drone (command routing)
- Dashboard architecture (example of findable planning doc)

---

*Placeholder for future implementation. The goal: "I know we did something about X" → instant answer.*
