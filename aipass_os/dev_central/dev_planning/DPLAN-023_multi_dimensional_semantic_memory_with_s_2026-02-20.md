# DPLAN-023: Multi-Dimensional Semantic Memory with Self-Evaluation

Tag: idea

> Replace flat vector search with specialized memory collections that self-interrogate before acting and self-improve based on retrieval quality scoring.

## Vision

Current memory retrieval is one-dimensional: a query goes into a single vector store, results come back ranked by similarity. Patrick's concept flips this into a multi-dimensional architecture where:

1. **Specialized memory branches** — Instead of one big collection, memory splits into purpose-built collections: decisions, mood/sentiment, coding patterns, lessons learned, workflow patterns, communication style, error history, etc.
2. **Self-interrogation protocol** — Before acting on any significant task, the agent runs a structured internal query sequence across relevant collections. Not just "what do I know about X?" but "what decisions did I make about X? what went wrong last time? what's my usual approach? what patterns apply?"
3. **Parallel fan-out queries** — The interrogation hits multiple collections simultaneously, each returning domain-specific context
4. **Self-evaluation and improvement** — Each retrieval result gets a quality score. Did this memory actually help? Over time, collections that consistently return low-quality results get flagged for restructuring. Collections that perform well get reinforced. The memory system literally improves itself.

The end state: an agent that doesn't just remember — it *reflects* before acting, drawing from structured experience across multiple dimensions of knowledge.

## Current State

### What AIPass has now
- **Memory Bank** with ChromaDB vector store — single collection, flat similarity search
- **Fragments system** — extracts key learnings from session files, embeds them
- **Auto-rollover** — local.json and observations.json roll into Memory Bank when they hit limits
- **5,500+ vectors** archived across 32 branches
- **Search works** but returns results ranked purely by embedding similarity — no awareness of *type* of memory or *quality* of retrieval

### What's missing
- No semantic categorization of memories (a coding lesson and a mood observation live in the same space)
- No structured pre-action reflection protocol
- No feedback loop on retrieval quality
- No per-collection health metrics or self-improvement
- Search is reactive (agent asks when stuck) rather than proactive (agent reflects before starting)

## What Needs Building

### Phase 1: Collection Architecture
- [ ] Design collection taxonomy (decisions, lessons, patterns, errors, style, mood, etc.)
- [ ] Define schema per collection type (what metadata each needs)
- [ ] Build collection router — given a fragment, which collection(s) does it belong to?
- [ ] Migration path from flat collection to multi-collection
- [ ] Backwards compatibility with existing search

### Phase 2: Self-Interrogation Protocol
- [ ] Define standard interrogation sequence (what questions, in what order)
- [ ] Build parallel query executor (fan-out across collections)
- [ ] Result aggregation — merge results from multiple collections into coherent context
- [ ] Integration point — when does interrogation trigger? (task start, decision point, error recovery)
- [ ] Configurable depth — quick check vs deep reflection

### Phase 3: Self-Evaluation Loop
- [ ] Define quality scoring mechanism (did this memory help? 1-5 scale or binary)
- [ ] Per-collection quality tracking over time
- [ ] Threshold-based alerts (collection X has been unhelpful for N queries)
- [ ] Auto-restructuring suggestions when collection quality degrades
- [ ] Feedback writes back to collection metadata

### Phase 4: Integration
- [ ] Hook into branch startup (light interrogation on wake)
- [ ] Hook into task execution (deep interrogation before significant actions)
- [ ] Hook into memory write (classify new memories into correct collections)
- [ ] Dashboard visibility (collection health, query patterns, quality scores)

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| Collection taxonomy | Fixed set / Agent-defined / Hybrid | Hybrid | Start with core set, let agents propose new collections based on usage |
| Classification method | LLM-based / Embedding clustering / Rule-based | LLM-based | Fragments already go through LLM extraction; add classification there |
| Quality scoring | Agent self-report / Outcome-based / Both | Both | Agent rates immediately, outcome validates later |
| Interrogation trigger | Always / Task-based / Configurable | Configurable | Light on startup, deep on significant tasks, skip for trivial ops |
| Storage backend | Separate ChromaDB collections / Single collection with metadata filtering / Different stores per type | Separate collections | Cleaner isolation, independent tuning per collection |
| Migration strategy | Big bang / Gradual dual-write / New memories only | Gradual dual-write | Keep existing flat search working while building new system |

## Research: Landscape Analysis

### What exists in the field (Feb 2026)

**Letta (formerly MemGPT)**
- Self-editing tiered memory (core/archival/recall)
- Agent autonomously decides what to remember and forget
- Closest to our "agent manages its own memory" philosophy
- Missing: no multi-collection specialization, no self-evaluation scoring

**Mem0**
- Categorized memory layer for AI apps
- Short-term, long-term, semantic, episodic types
- Graph-based relationships between memories
- Missing: no self-interrogation protocol, no quality feedback loop

**Zep / Graphiti**
- Temporal knowledge graphs — memories as nodes with time-aware edges
- Excellent at "what changed over time" queries
- Missing: no specialized collections, no self-improvement mechanism

**Cognee**
- Self-improving memory through user feedback loops
- Closest to our self-evaluation concept
- Missing: no multi-dimensional collection architecture, no pre-action interrogation

**Mengram**
- Typed memory with failure-evolved procedures
- Learns new procedures from failed attempts
- Interesting parallel to our error-history collection idea
- Missing: limited to procedure memory, not general-purpose

**AWS Bedrock AgentCore (2025)**
- Episodic memory that stores outcomes and reflections alongside events
- Production-grade infrastructure
- Missing: no self-improvement, no multi-collection fan-out

**Stanford Generative Agents (2023)**
- Reflection mechanism that synthesizes observations into higher-level insights
- The original "agents that reflect" paper
- Missing: research prototype, not production architecture

**MemR3 (2025 paper)**
- Reflective retrieval reasoning — agent reasons about whether retrieved memories are relevant
- Closest academic work to our quality-scoring concept
- Missing: single memory store, no specialized collections

### Novelty Assessment

Individual components exist across the landscape:
- Tiered/categorized memory (Letta, Mem0)
- Self-improvement via feedback (Cognee, Mengram)
- Reflection before action (Stanford Generative Agents)
- Quality-aware retrieval (MemR3)

**What's genuinely novel in Patrick's concept:**
The integration of ALL four as a unified architecture:
1. **Formalized self-interrogation protocol** (structured question sequence, not ad-hoc retrieval)
2. **Multi-collection parallel fan-out** (specialized stores queried simultaneously)
3. **Per-result quality scoring** (not just "was the session good" but "was THIS specific memory helpful")
4. **Closed-loop improvement per collection** (individual collections evolve independently based on their own quality metrics)

No existing system combines all four. The closest are Cognee (has feedback but not multi-collection) and Letta (has tiered memory but not self-evaluation). The specific combination — especially the per-collection quality scoring feeding back into collection health — is novel.

## Ideas

- **Mood/sentiment collection** could inform communication style — if recent sessions show frustration patterns, agent adjusts tone
- **Error history collection** could short-circuit repeat mistakes — "last 3 times I tried X approach, it failed because Y"
- **Decision collection** could prevent flip-flopping — "I already decided to use approach A for this, here's why"
- **Could extend to cross-branch queries** — "what has @seed learned about this pattern?" without needing ai_mail
- **Quality scoring could use the LLM itself** — after task completion, ask "which of these memories actually helped?" and score retroactively
- **Collections could have different embedding models** — code memories might embed better with code-specific models
- **"Memory dreams"** — background process that periodically re-evaluates and reorganizes memories across collections based on accumulated quality data (inspired by how biological memory consolidation works during sleep)

## Relationships
- **Related DPLANs:** DPLAN-022 (branch standardization — better prompts = better memory classification)
- **Related FPLANs:** None yet
- **Owner branches:** @memory_bank (implementation), @dev_central (architecture), @research_agent (continued landscape monitoring)
- **Dependencies:** Requires stable Memory Bank + fragments system as foundation

## Status
- [x] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes
- Session 115: Patrick conceived this while dealing with truck issues. Started as casual ideation, turned into a significant architectural concept.
- The existing fragments system is the natural foundation — fragments already extract and embed learnings. Adding collection classification to the extraction step is the minimal viable starting point.
- Research confirms no existing system combines all four components. This could be a genuine contribution to the field if built well.
- Patrick's insight about self-improvement is key: "If it asks itself 'what do I know about this' and the answer is garbage, it should flag that collection for improvement." The memory system literally debugs itself.
- This is theoretical/future work. No timeline pressure. Capture ideas as they come.

---
*Created: 2026-02-20*
*Updated: 2026-02-20*
