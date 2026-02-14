# Fragmented Memory - Implementation Plan

*Random memory surfacing without being asked - like how human memory works*

---

## The Idea

During conversation, relevant memories surface naturally without explicit queries. Not "find X" but "this reminds me of..." - associative, not surgical.

**Origin:** Session 46 late-night discussion. Patrick's insight: human memory isn't surgical retrieval, it's random fragments surfacing based on loose associations.

---

## Research Gathered

### 1. Flow's Memory Bank Integration (`flow/apps/handlers/mbank/process.py`)

**Pattern:** Plan closes → AI analyzes → TRL classification + summary → Memory Bank entry

**TRL Classification:**
- **Type**: SEED, NEXUS, FLOW, PRAX, etc.
- **Category**: API, MEM, DB, UI, CFG, etc.
- **Action**: IMP, FIX, UPD, NEW, REF, etc.

**Key insight:** Uses free AI model (OpenRouter) to classify and summarize before storage. The PROCESS pattern is valuable (AI analysis before storage), but TRL itself is plan-specific - not suitable for conversation fragments.

**What to borrow:** The pipeline pattern (content → AI analysis → structured tags → storage). NOT the TRL schema itself.

### 2. Symbolic Memory (`/home/aipass/dropbox/symbolic_memory-*/`)

**Multi-dimensional conversation analysis:**

| Dimension | Function | Examples |
|-----------|----------|----------|
| Technical flow | `extract_technical_flow()` | `problem_struggle_breakthrough`, `debugging_session` |
| Emotional arc | `extract_emotional_journey()` | `frustration_to_breakthrough`, `curiosity_to_excitement` |
| Collaboration | `extract_collaboration_patterns()` | `user_directed`, `collaborative_building` |
| Key learnings | `extract_key_learnings()` | `discovery`, `problem_solving` |
| Context triggers | `extract_context_triggers()` | Keywords that SHOULD surface this memory |

**Killer function:** `extract_context_triggers()` - identifies keywords/terms that should trigger this memory in future conversations.

**Compression:** Full conversation → 20-50 word symbolic essence with patterns preserved.

### 3. Memory Bank Current State

- ChromaDB vector storage
- Auto-rollover at 600 lines
- `drone @memory_bank search "query"` for explicit retrieval
- No associative/random surfacing currently

---

## Proposed Architecture

### Hook-Based Triggering

```
Conversation flows
       ↓
Hook extracts current context (keywords, mood, patterns)
       ↓
Query Memory Bank with:
  - Symbolic dimensions (emotional arc, technical flow, collaboration style)
  - Context triggers (keywords that SHOULD surface memories)
  - Vector similarity (semantic closeness)
       ↓
AI re-ranks results for relevance (optional, adds latency)
       ↓
Top fragment(s) injected as context
       ↓
"This reminds me of..." surfaces naturally
```

**Note:** TRL stays for plan classification only. Conversation fragments use Symbolic Memory dimensions - they're designed for experiences, not work items.

### Components Needed

1. **Fragment Extractor** (adapt Symbolic Memory)
   - Run on conversation periodically or at end
   - Extract multi-dimensional patterns
   - Generate context triggers
   - Store with TRL tags

2. **Fragment Retriever** (new)
   - Hook captures current conversation themes
   - Query Memory Bank with combined filters
   - Use AI to score relevance (not just vector similarity)
   - Return top N fragments

3. **Fragment Injector** (hook integration)
   - Inject relevant fragments into context
   - Format as natural recall, not database results
   - Configurable: how often, how many, threshold

### Quality Controls

**The hard part isn't implementation - it's retrieval quality.**

- Too loose → noise, irrelevant fragments
- Too tight → nothing surfaces, feels dead
- Sweet spot → occasional, relevant, surprising connections

**Tuning levers:**
- Similarity threshold (vector match strictness)
- TRL filter breadth (narrow vs wide category match)
- Emotional pattern matching (same arc shape)
- Frequency cap (max fragments per session)
- Recency bias (prefer recent vs old memories)

---

## Implementation Phases

### Phase 1: Foundation
- [ ] Port Symbolic Memory extractors to AIPass
- [ ] Add symbolic analysis to Memory Bank storage
- [ ] Test extraction on sample conversations

### Phase 2: Retrieval
- [ ] Build fragment retrieval with combined filters
- [ ] Add AI re-ranking step
- [ ] Test retrieval quality manually

### Phase 3: Integration
- [ ] Create hook for conversation monitoring
- [ ] Inject fragments into context
- [ ] Tune thresholds and frequency

### Phase 4: Polish
- [ ] Natural language formatting ("This reminds me of...")
- [ ] User controls (enable/disable, verbosity)
- [ ] Performance optimization

---

## Key Files

**Reference implementations:**
- `/home/aipass/dropbox/symbolic_memory-*/symbolic_memory/symbolic_memory.py`
- `/home/aipass/aipass_core/flow/apps/handlers/mbank/process.py`
- `/home/aipass/aipass_core/memory_bank/` (current Memory Bank)

**Where to build:**
- Memory Bank branch owns storage/retrieval
- Hook system for injection
- Could be standalone module or Memory Bank extension

---

## Performance Considerations

**Tested:** Free AI model (`google/gemma-3-12b-it:free`) = ~7 seconds per call

**Implications:**
- **Extraction** (analyzing conversation): Must be background/async. 7 sec is fine end-of-session.
- **Retrieval** (finding fragments): Vector search is fast. AI re-ranking adds 7 sec - make optional.
- **Injection**: No AI needed, just formatting.

**Options for faster AI:**
1. OpenAI nano/mini (sub-1 sec) - requires OpenAI API key
2. Local model - no network latency, needs setup
3. Skip AI re-ranking - vector-only retrieval, faster but less accurate

**Recommendation:** Start with background extraction + vector-only retrieval. Add AI re-ranking later as optional enhancement.

---

## Open Questions

1. **When to extract?** End of session? Periodically? On significant events?
2. **Where to store?** Memory Bank collection? Separate fragment store?
3. **How to inject?** System prompt? Mid-conversation insertion?
4. **Who owns this?** Memory Bank? New branch? Hook system?

---

## Notes

- This is experiential retrieval, not keyword matching
- The goal is serendipity - unexpected but relevant connections
- Start simple, tune based on actual usage
- Don't over-engineer - the simplest version that works is best

---

*Last updated: 2026-02-04*
*Status: Research complete, ready for Phase 1*
