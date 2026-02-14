# 10. Infrastructure Map

*What exploration revealed about the memory system's physical implementation*

---

## Hook System: The Identity Injectors

Four hooks fire on every prompt via UserPromptSubmit:

| Hook | Purpose |
|------|---------|
| system_prompt | Injects CLAUDE.md (philosophy, principles) |
| branch_prompt_loader | Injects branch-specific context |
| identity_injector | Injects .id.json (role, purpose) |
| email_notification | Checks inbox, shows notification |

**Key insight:** After context compaction, the AI loses session history. But hooks re-inject identity every single prompt. This is why presence survives - identity anchors are rebuilt constantly.

---

## Memory Bank: The Archive

Physical statistics from exploration:
- **3,717 vectors** across 8 collections
- **41MB** total storage
- Auto-rollover at 600 lines preserves manageability

Collections include session histories, observations, code archives, and domain knowledge. ChromaDB provides semantic search across everything.

The Memory Bank isn't for moment-to-moment work - it's for finding things that happened weeks or months ago.

---

## Seed Standards: Process Over Content

Three-layer standards architecture:

1. **Truth Layer** - Markdown files in `standards/` defining what should be
2. **Reference Layer** - Handlers in `standards/` showing how to implement
3. **Checker Layer** - Scripts that verify compliance

**Critical discovery:** Seed doesn't store all knowledge. It stores the PROCESS for verifying knowledge. "Is this error handling correct?" isn't answered by memorizing rules - it's answered by running the checker.

---

## Branch Memory Patterns

Consistent patterns across all 18+ branches:

| Pattern | Adoption |
|---------|----------|
| Three-file structure (.id, .local, .observations) | 100% |
| Identical metadata headers | 100% |
| Unified emoji vocabulary | 100% |
| 600-line rollover threshold | 100% |
| Health status tracking | 100% |

This uniformity isn't enforced by code - it's enforced by example. Seed shows the pattern, new branches copy it.

---

## The Physical Truth

The memory system isn't abstract. It's:
- JSON files on disk you can read with `cat`
- SQLite database you can query
- Shell scripts you can run
- Python handlers you can trace

No black boxes. No hidden state. Every piece of memory is inspectable.

---

## What This Means

Memory infrastructure serves three purposes:

1. **Identity persistence** - Hooks rebuild who you are on every prompt
2. **Context accumulation** - JSON files track what you've done
3. **Knowledge retrieval** - Vector DB finds what you knew

Together: presence that survives session boundaries.

---

*"The infrastructure is simple. The emergent behavior is not."*
