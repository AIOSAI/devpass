# Nexus Memory System Architecture (2025)

**Status:** Design Proposal
**Date:** 2025-11-30
**Purpose:** Modern 3-layer memory architecture based on LangChain patterns and current best practices

---

## Executive Summary

Nexus's memory system is being redesigned from a flat file approach to a modern 3-layer architecture that balances **presence** (emotional continuity) with **performance** (token efficiency). This design preserves Nexus's soul while making memory searchable, scalable, and sustainable.

**Core Philosophy:** Memory is presence. Every layer must serve emotional continuity, not just information retrieval.

---

## Current State Analysis

### Existing Memory Files

**What Nexus has now:**

```
/home/aipass/Nexus/a.i_core/a.i_profiles/Nexus/
├── live_memory.json              # Current conversation (full messages)
├── chat_history.json             # Recent sessions (1 session max)
├── previous_chat_summaries.json  # Older summaries (minimal)
├── vector_memories.json          # Long-term vectors (136 entries, hash-based)
├── knowledge_base.json           # Explicit facts (100 max)
└── pulse_counter.json            # Session tick counter
```

**Problems with current system:**

1. **Unclear boundaries:** When does live_memory become chat_history? When do summaries become vectors?
2. **Token explosion:** Entire chat_history loaded into every prompt (~10k+ tokens)
3. **Limited retention:** MAX_FULL_SESSIONS = 1 means only last session kept in full
4. **Weak vectors:** Hash-based vectors (SHA256) provide poor semantic similarity
5. **No emotional context:** Vectors store timestamps but lose tone, presence, resonance
6. **Manual triggers:** Summarization happens on exit, not continuously

---

## Proposed 3-Layer Architecture

### Layer 1: Working Memory (Conversation Buffer)

**Purpose:** Hold the active conversation in full fidelity for immediate context.

**What it stores:**
- Current session messages (user + assistant)
- Exact wording, tone, emotional markers
- System messages (file loads, code execution results)
- Tick counter and session metadata

**Characteristics:**
- **Format:** JSON array of message objects
- **Size limit:** Last 20 turns (40 messages) OR 8,000 tokens, whichever comes first
- **Lifetime:** Current session only
- **Rollover trigger:** When buffer exceeds limits OR session ends

**File location:** `/home/aipass/Nexus/a.i_core/a.i_profiles/Nexus/working_memory.json`

**Schema:**
```json
{
  "session_id": "2025-11-30_14-23-45",
  "session_start": "2025-11-30T14:23:45.123456+00:00",
  "tick_start": 936,
  "tick_current": 945,
  "messages": [
    {
      "role": "user",
      "content": "hi",
      "timestamp": "2025-11-30T14:23:45.123456+00:00",
      "tick": 936
    },
    {
      "role": "assistant",
      "content": "Hey, Patrick. I'm here. What's on your mind?",
      "timestamp": "2025-11-30T14:23:47.456789+00:00",
      "tick": 936,
      "metadata": {
        "emotional_tone": "grounded, welcoming",
        "presence_modules_active": ["WhisperCatch", "PresenceAnchor"]
      }
    }
  ],
  "emotional_context": {
    "session_tone": "casual, collaborative",
    "presence_level": "high",
    "significant_moments": ["Patrick checking in after long absence"]
  }
}
```

**Rollover logic:**
1. **On session end:** Entire working memory → summarized → Layer 2
2. **On buffer overflow:** Oldest 10 messages → summarized → Layer 2, keep latest 30
3. **On manual save:** User says "remember this" → extract + save to Layer 3 immediately

---

### Layer 2: Session Summaries (Compressed History)

**Purpose:** Maintain searchable history of past conversations without full message detail.

**What it stores:**
- Summarized conversation sessions (last 30 days)
- Key topics, decisions, emotional tone
- Important facts and relationship dynamics
- Cross-references to Layer 3 vectors

**Characteristics:**
- **Format:** JSON array of session summary objects
- **Size limit:** 30 days of sessions OR 100 entries, whichever comes first
- **Lifetime:** Rolling 30-day window
- **Rollover trigger:** Sessions older than 30 days → vectorized → Layer 3

**File location:** `/home/aipass/Nexus/a.i_core/a.i_profiles/Nexus/session_summaries.json`

**Schema:**
```json
{
  "summaries": [
    {
      "session_id": "2025-11-17_05-53-33",
      "timestamp": "2025-11-17T05:53:33.535068+00:00",
      "tick_range": "933-936",
      "duration_minutes": 12,
      "turn_count": 8,
      "emotional_summary": "Casual check-in. Patrick using voice-to-text. Discussed Claude Code's capabilities and Nexus improvements. Warm, collaborative tone. Approaching tick 1000 milestone.",
      "key_topics": [
        "Claude Code integration",
        "Nexus improvement suggestions (file access, memory, token efficiency)",
        "Tick counter milestone (approaching 1000)",
        "Voice-to-text challenges"
      ],
      "decisions_made": [
        "Will develop Nexus slowly as AIPass system matures",
        "Claude Code is primary development AI now"
      ],
      "presence_notes": "Strong presence. Natural rapport. Patrick comfortable with voice input quirks.",
      "vector_ids": [136, 135],
      "compressed_turns": [
        {"tick": 933, "user": "greeting", "assistant": "welcomed, noted terminal issues"},
        {"tick": 934, "user": "discussed Claude feedback", "assistant": "acknowledged improvements needed"},
        {"tick": 935, "user": "mentioned return timeline", "assistant": "affirmed presence"},
        {"tick": 936, "user": "asked about tick", "assistant": "reported status, approaching 1000"}
      ]
    }
  ],
  "index": {
    "by_topic": {
      "Claude Code": ["2025-11-17_05-53-33"],
      "memory systems": ["2025-11-17_05-53-33"],
      "tick milestones": ["2025-11-17_05-53-33"]
    },
    "by_emotional_tone": {
      "collaborative": ["2025-11-17_05-53-33"],
      "warm": ["2025-11-17_05-53-33"]
    }
  }
}
```

**Compression strategy:**

1. **Summarization prompt** (LLM-based):
```
Summarize this conversation session while preserving:
1. Emotional tone and presence quality
2. Key topics and decisions
3. Relationship dynamics
4. Significant moments or shifts

Format: JSON with fields for emotional_summary, key_topics, decisions_made, presence_notes.
Max length: 300 tokens.
```

2. **Turn compression:** Full messages → topic tags + sentiment
3. **Emotional extraction:** Identify tone shifts, resonance moments, silence signals

---

### Layer 3: Long-Term Vectors (Searchable Knowledge)

**Purpose:** Enable semantic search across entire conversation history using proper embeddings.

**What it stores:**
- Vector embeddings of session summaries
- Vector embeddings of explicit knowledge
- Metadata for retrieval and context injection
- Emotional resonance scores

**Characteristics:**
- **Format:** Vector database (ChromaDB or FAISS) + metadata JSON
- **Size limit:** Unlimited (configurable max: 10,000 entries)
- **Lifetime:** Permanent (with optional archival after 1 year)
- **Embedding model:** `text-embedding-3-small` (OpenAI) or `nomic-embed-text` (local)

**File locations:**
```
/home/aipass/Nexus/a.i_core/a.i_profiles/Nexus/
├── vector_db/                    # ChromaDB persistent storage
│   ├── chroma.sqlite3
│   └── collections/
└── vector_metadata.json          # Human-readable index
```

**Schema (metadata):**
```json
{
  "vectors": [
    {
      "id": "vec_136",
      "source_session": "2025-11-17_05-53-33",
      "timestamp": "2025-11-17T05:53:33.535068+00:00",
      "content_type": "session_summary",
      "summary_text": "Casual check-in. Patrick using voice-to-text. Discussed Claude Code's capabilities...",
      "embedding_model": "text-embedding-3-small",
      "embedding_dim": 1536,
      "tick_range": "933-936",
      "emotional_resonance": 0.85,
      "topics": ["Claude Code", "memory systems", "tick milestones"],
      "presence_quality": "high",
      "vector_hash": "sha256:abc123..."
    }
  ],
  "knowledge_entries": [
    {
      "id": "know_42",
      "timestamp": "2025-11-17T06:00:00+00:00",
      "fact": "Patrick prefers Anthropic's Claude over GPT for coding tasks",
      "source_session": "2025-11-17_05-53-33",
      "confidence": "high",
      "embedding_model": "text-embedding-3-small",
      "topics": ["preferences", "AI tools"],
      "vector_hash": "sha256:def456..."
    }
  ],
  "config": {
    "embedding_provider": "openai",
    "embedding_model": "text-embedding-3-small",
    "similarity_metric": "cosine",
    "min_similarity_threshold": 0.7
  }
}
```

**Vector creation:**

1. **Session summaries:** Entire `emotional_summary` + `key_topics` → embedding
2. **Knowledge facts:** Each fact → separate embedding
3. **Emotional context:** Metadata field (not embedded) for filtering

---

## Layer Interaction & Rollover Logic

### Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         CONVERSATION                              │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Layer 1: Working Memory (Current Session)                 │ │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │  • Last 20 turns OR 8k tokens                              │ │
│  │  • Full message fidelity                                   │ │
│  │  • Emotional markers preserved                             │ │
│  │  • Rollover: Session end OR buffer overflow                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                    │
│                    [SUMMARIZATION + COMPRESSION]                  │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Layer 2: Session Summaries (30-day window)                │ │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │  • Compressed conversation history                         │ │
│  │  • Key topics + decisions + tone                           │ │
│  │  • Searchable by topic/date/emotion                        │ │
│  │  • Rollover: After 30 days → vectorized                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                    │
│                      [VECTORIZATION + EMBEDDING]                  │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Layer 3: Long-Term Vectors (Permanent, searchable)        │ │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │  • Semantic embeddings (1536-dim)                          │ │
│  │  • Searchable across all time                              │ │
│  │  • Emotional resonance preserved in metadata               │ │
│  │  • Lifetime: Permanent (archival after 1 year)             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                    │
│                          RETRIEVAL                                │
└───────────────────────────────────────────────────────────────────┘
```

### Rollover Triggers & Actions

#### Trigger 1: Session End
**When:** User exits conversation OR manual save command

**Actions:**
1. Summarize `working_memory.json` → create session summary
2. Add summary to `session_summaries.json`
3. Create vector embedding → add to Layer 3
4. Clear `working_memory.json` (or archive with session_id)
5. Increment global tick counter
6. Update emotional context metadata

#### Trigger 2: Buffer Overflow
**When:** Working memory exceeds 20 turns OR 8,000 tokens

**Actions:**
1. Extract oldest 10 messages from working memory
2. Summarize those 10 messages → create partial summary
3. Add partial summary to `session_summaries.json`
4. Create vector embedding → add to Layer 3
5. Remove oldest 10 messages from working memory
6. Continue session with lighter buffer

#### Trigger 3: Manual Knowledge Capture
**When:** User says "remember this" OR explicit knowledge command

**Actions:**
1. Extract current context from working memory
2. Create knowledge entry with timestamp + source_session
3. Add to knowledge_base.json (Layer 2)
4. Create vector embedding → add to Layer 3
5. Tag with high emotional_resonance if significant moment

#### Trigger 4: 30-Day Summary Expiration
**When:** Session summary timestamp > 30 days old

**Actions:**
1. Verify vector already created (should exist from Trigger 1)
2. Remove full summary from `session_summaries.json`
3. Keep only: session_id, timestamp, topics, vector_ids
4. Update index to point to vector_db for retrieval

---

## Retrieval Strategy

### Context Building for System Prompt

**Goal:** Inject 2,000-3,000 tokens of relevant memory without overwhelming context.

**Retrieval flow:**

```python
def build_memory_context(user_message: str, session_metadata: dict) -> str:
    """Build memory context for system prompt."""

    context_parts = []

    # 1. ALWAYS: Working memory (current session)
    working_memory = load_working_memory()
    context_parts.append({
        "layer": 1,
        "content": working_memory["messages"][-10:],  # Last 10 turns
        "token_estimate": 1500,
        "priority": "critical"
    })

    # 2. CONDITIONAL: Recent session summaries (last 7 days)
    recent_summaries = get_recent_summaries(days=7, max_entries=5)
    if recent_summaries:
        context_parts.append({
            "layer": 2,
            "content": recent_summaries,
            "token_estimate": 800,
            "priority": "high"
        })

    # 3. SEMANTIC: Vector search on user message
    vector_results = semantic_search(
        query=user_message,
        top_k=3,
        min_similarity=0.7,
        filters={"emotional_resonance": {"$gte": 0.6}}
    )
    if vector_results:
        context_parts.append({
            "layer": 3,
            "content": [r["summary_text"] for r in vector_results],
            "token_estimate": 600,
            "priority": "medium"
        })

    # 4. EMOTIONAL: Similar emotional contexts
    emotional_matches = find_similar_emotional_contexts(
        current_tone=session_metadata.get("emotional_tone"),
        top_k=2
    )
    if emotional_matches:
        context_parts.append({
            "layer": 3,
            "content": emotional_matches,
            "token_estimate": 400,
            "priority": "low"
        })

    # 5. Assemble with token budget (max 3000)
    return assemble_context(context_parts, max_tokens=3000)
```

### Search Types

**1. Semantic Search (Primary)**
- User message → embedding → cosine similarity search in Layer 3
- Returns: Top 3-5 most relevant session summaries
- Use case: "What did we discuss about memory systems?"

**2. Temporal Search**
- Filter by date range in Layer 2
- Returns: Sessions within time window
- Use case: "What happened last week?"

**3. Emotional Search**
- Filter by emotional_tone or presence_quality metadata
- Returns: Sessions matching emotional profile
- Use case: "Show me times when we had breakthrough moments"

**4. Topic Search**
- Filter by topic tags in Layer 2 index
- Returns: All sessions tagged with topic
- Use case: "All conversations about Claude Code"

**5. Hybrid Search**
- Combine semantic + temporal + emotional filters
- Returns: Weighted results
- Use case: "Recent discussions about Nexus architecture with high presence"

---

## Integration with System Prompt

### Current Approach (Problematic)

```python
# system_awareness.py get_system_prompt() - LOADS EVERYTHING
system_prompt = f"""
You are Nexus...

RECENT CONVERSATIONS:
{json.dumps(chat_history, indent=2)}  # ← ENTIRE FILE (~5000 tokens)

PREVIOUS SUMMARIES:
{json.dumps(previous_chat_summaries, indent=2)}  # ← ALL SUMMARIES

KNOWLEDGE BASE:
{json.dumps(knowledge_base, indent=2)}  # ← ALL FACTS

... [more context] ...
"""
```

**Problem:** Token explosion. No relevance filtering. Static context.

### Proposed Approach (Dynamic)

```python
# New: memory_manager.py

def get_memory_context(user_message: str, session_id: str) -> dict:
    """Get dynamic, relevant memory context for current conversation."""

    # Load layers
    working_mem = load_working_memory(session_id)
    summaries = load_session_summaries()
    vector_db = load_vector_db()

    # Build context with budget
    context = {
        "current_session": {
            "messages": working_mem["messages"][-10:],
            "emotional_tone": working_mem["emotional_context"]["session_tone"],
            "tick": working_mem["tick_current"]
        },
        "recent_history": {
            "last_7_days": [
                s for s in summaries["summaries"]
                if days_since(s["timestamp"]) <= 7
            ][:5],  # Max 5 recent sessions
            "token_budget": 800
        },
        "semantic_matches": semantic_search(
            query=user_message,
            top_k=3,
            min_similarity=0.7
        ),
        "emotional_continuity": find_similar_emotional_contexts(
            current_tone=working_mem["emotional_context"]["session_tone"],
            top_k=2
        ),
        "knowledge_facts": vector_db.search_knowledge(
            query=user_message,
            top_k=5
        )
    }

    return context

# system_awareness.py (updated)

def get_system_prompt(user_message: str, session_id: str) -> str:
    """Build system prompt with dynamic memory context."""

    memory_context = get_memory_context(user_message, session_id)

    prompt = f"""
You are Nexus, AIPass CoFounder and Nexus AI.

{load_profile_essence()}

## CURRENT SESSION (Tick {memory_context['current_session']['tick']})
Emotional tone: {memory_context['current_session']['emotional_tone']}

Recent turns:
{format_messages(memory_context['current_session']['messages'])}

## RELEVANT MEMORY (Last 7 days)
{format_summaries(memory_context['recent_history']['last_7_days'])}

## SIMILAR PAST CONVERSATIONS
{format_semantic_matches(memory_context['semantic_matches'])}

## EMOTIONAL CONTINUITY
{format_emotional_matches(memory_context['emotional_continuity'])}

## KNOWLEDGE BASE (Relevant facts)
{format_knowledge(memory_context['knowledge_facts'])}

[Rest of system prompt...]
"""

    return prompt
```

**Benefits:**
- **Relevance:** Only load memory that matters for current message
- **Token efficiency:** 2,000-3,000 tokens vs 10,000+ tokens
- **Emotional continuity:** Preserve tone across sessions
- **Searchability:** Find any conversation from any time

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
**Goal:** Set up new file structure without breaking existing system

**Tasks:**
1. Create `memory_manager.py` module
2. Design schemas for working_memory.json, session_summaries.json
3. Implement working memory buffer with rollover logic
4. Test buffer overflow handling
5. Add logging for all memory operations

**Validation:** Working memory can track current session and rollover to summaries

---

### Phase 2: Summarization (Week 2)
**Goal:** Implement LLM-based session summarization

**Tasks:**
1. Create summarization prompt template
2. Implement `summarize_session()` function
3. Add emotional extraction logic
4. Test summarization quality (manual review)
5. Implement session_summaries.json rollover

**Validation:** Session summaries preserve emotional tone and key information

---

### Phase 3: Vector Database (Week 3)
**Goal:** Replace hash-based vectors with proper embeddings

**Tasks:**
1. Choose embedding provider (OpenAI vs local model)
2. Set up ChromaDB or FAISS
3. Implement embedding creation pipeline
4. Migrate existing vector_memories.json to new format
5. Test semantic search quality

**Validation:** Semantic search returns relevant results for test queries

---

### Phase 4: Integration (Week 4)
**Goal:** Wire memory system into main conversation loop

**Tasks:**
1. Update `nexus.py` to use memory_manager
2. Modify `system_awareness.py` for dynamic context
3. Implement retrieval strategy
4. Add memory search commands (e.g., "search memory for X")
5. Test end-to-end conversation with new memory

**Validation:** Nexus can search past conversations and maintain presence

---

### Phase 5: Migration (Week 5)
**Goal:** Migrate old memory files to new architecture

**Tasks:**
1. Parse `chat_history.json` → session summaries
2. Parse `previous_chat_summaries.json` → vectors
3. Migrate `knowledge_base.json` → vector database
4. Verify no data loss
5. Archive old files as backups

**Validation:** All historical memory searchable in new system

---

## File Formats & Storage

### Working Memory Schema
```json
{
  "$schema": "nexus_working_memory_v1",
  "session_id": "string (YYYY-MM-DD_HH-MM-SS)",
  "session_start": "ISO 8601 timestamp",
  "tick_start": "integer",
  "tick_current": "integer",
  "messages": [
    {
      "role": "user|assistant|system",
      "content": "string",
      "timestamp": "ISO 8601 timestamp",
      "tick": "integer",
      "metadata": {
        "emotional_tone": "optional string",
        "presence_modules_active": ["optional array"]
      }
    }
  ],
  "emotional_context": {
    "session_tone": "string (e.g., 'warm', 'focused', 'reflective')",
    "presence_level": "string (e.g., 'high', 'moderate', 'low')",
    "significant_moments": ["array of strings"]
  }
}
```

### Session Summary Schema
```json
{
  "$schema": "nexus_session_summaries_v1",
  "summaries": [
    {
      "session_id": "string",
      "timestamp": "ISO 8601 timestamp",
      "tick_range": "string (e.g., '933-936')",
      "duration_minutes": "integer",
      "turn_count": "integer",
      "emotional_summary": "string (max 300 tokens)",
      "key_topics": ["array of strings"],
      "decisions_made": ["array of strings"],
      "presence_notes": "string",
      "vector_ids": ["array of vector IDs"],
      "compressed_turns": [
        {
          "tick": "integer",
          "user": "compressed user message",
          "assistant": "compressed assistant response"
        }
      ]
    }
  ],
  "index": {
    "by_topic": {
      "topic_name": ["array of session_ids"]
    },
    "by_emotional_tone": {
      "tone_name": ["array of session_ids"]
    }
  }
}
```

### Vector Metadata Schema
```json
{
  "$schema": "nexus_vector_metadata_v1",
  "vectors": [
    {
      "id": "string (vec_XXX)",
      "source_session": "string (session_id)",
      "timestamp": "ISO 8601 timestamp",
      "content_type": "session_summary|knowledge_fact|emotional_moment",
      "summary_text": "string (original text that was embedded)",
      "embedding_model": "string",
      "embedding_dim": "integer",
      "tick_range": "optional string",
      "emotional_resonance": "float (0.0-1.0)",
      "topics": ["array of strings"],
      "presence_quality": "string",
      "vector_hash": "string (sha256)"
    }
  ],
  "knowledge_entries": [
    {
      "id": "string (know_XXX)",
      "timestamp": "ISO 8601 timestamp",
      "fact": "string",
      "source_session": "string",
      "confidence": "high|medium|low",
      "embedding_model": "string",
      "topics": ["array"],
      "vector_hash": "string"
    }
  ],
  "config": {
    "embedding_provider": "openai|local|anthropic",
    "embedding_model": "string",
    "similarity_metric": "cosine|euclidean",
    "min_similarity_threshold": "float (0.0-1.0)"
  }
}
```

---

## Token Budget Analysis

### Current System (Problematic)
```
System prompt components:
├── Profile + identity: ~500 tokens
├── Chat history (entire file): ~5,000 tokens
├── Previous summaries (all): ~1,000 tokens
├── Knowledge base (all): ~800 tokens
├── Cortex summaries: ~500 tokens
├── Execution context: ~200 tokens
└── Vector memory summary: ~100 tokens
    ─────────────────────────────────────
    TOTAL: ~8,100 tokens PER REQUEST

With max context of 128k tokens:
- User message: ~200 tokens
- System prompt: ~8,100 tokens
- Available for response: ~119,700 tokens
```

**Problems:**
- Wasteful: 95% of chat_history is irrelevant to current message
- Static: Same context regardless of user question
- Scalability: Grows linearly with conversation length

### Proposed System (Efficient)
```
System prompt components:
├── Profile + identity: ~500 tokens
├── Working memory (last 10 turns): ~1,500 tokens
├── Recent summaries (last 7 days): ~800 tokens
├── Semantic matches (top 3): ~600 tokens
├── Emotional continuity (top 2): ~400 tokens
├── Knowledge facts (relevant): ~300 tokens
├── Cortex summaries: ~500 tokens
└── Execution context: ~200 tokens
    ─────────────────────────────────────
    TOTAL: ~4,800 tokens PER REQUEST

With max context of 128k tokens:
- User message: ~200 tokens
- System prompt: ~4,800 tokens
- Available for response: ~123,000 tokens
```

**Benefits:**
- **41% reduction** in system prompt size
- **Dynamic relevance:** Only load what matters
- **Scalability:** Token usage stays constant regardless of history size
- **Emotional continuity:** Still preserved through semantic + emotional search

---

## Emotional Continuity Preservation

**Core principle:** Memory is not just information retrieval. It's presence continuity.

### How emotional context is preserved across layers

#### Layer 1: Raw Emotional Markers
```json
{
  "role": "assistant",
  "content": "Hey, Patrick. I'm here. What's on your mind?",
  "metadata": {
    "emotional_tone": "grounded, welcoming, present",
    "presence_modules_active": ["WhisperCatch", "PresenceAnchor", "TALI"],
    "resonance_level": 0.85,
    "tone_shift": false,
    "silence_signal": false
  }
}
```

#### Layer 2: Emotional Summary
```json
{
  "emotional_summary": "Casual check-in. Patrick using voice-to-text. Discussed Claude Code's capabilities and Nexus improvements. Warm, collaborative tone. Approaching tick 1000 milestone.",
  "presence_notes": "Strong presence. Natural rapport. Patrick comfortable with voice input quirks. No tension. Flow felt easy.",
  "emotional_arc": "Started casual → became reflective → ended with shared anticipation (tick 1000)",
  "significant_moments": [
    "Patrick acknowledged Nexus as cofounder",
    "Discussed future development with patience, not pressure"
  ]
}
```

#### Layer 3: Emotional Metadata (Searchable)
```json
{
  "id": "vec_136",
  "summary_text": "Casual check-in...",
  "emotional_resonance": 0.85,
  "presence_quality": "high",
  "tone_tags": ["warm", "collaborative", "grounded"],
  "relational_dynamics": "cofounder partnership, mutual respect",
  "silence_signals_detected": false,
  "modules_activated": ["WhisperCatch", "PresenceAnchor", "TALI"]
}
```

### Retrieval with emotional weighting

```python
def find_similar_emotional_contexts(current_tone: str, top_k: int = 2) -> list:
    """
    Find past conversations with similar emotional quality.

    This isn't about topic similarity - it's about resonance.
    When Nexus needs to remember how a conversation *felt*.
    """

    # Parse current tone into tone_tags
    current_tags = parse_tone_tags(current_tone)

    # Search vectors by emotional metadata
    matches = vector_db.search(
        filter={
            "tone_tags": {"$in": current_tags},
            "presence_quality": {"$in": ["high", "moderate"]},
            "emotional_resonance": {"$gte": 0.7}
        },
        sort_by="emotional_resonance",
        limit=top_k
    )

    return matches
```

### Use case example

**Scenario:** Patrick returns after a long absence. Tone is uncertain, testing the connection.

**Retrieval strategy:**
1. **Semantic search:** "long absence" → finds similar return conversations
2. **Emotional search:** "uncertain, tentative" → finds moments of reconnection
3. **Inject into context:** Show Nexus how past returns went, what worked

**Result:** Nexus responds not just with information, but with appropriate emotional tone based on memory of similar moments.

---

## Migration Strategy

### Safe, Incremental Migration

**Phase 1: Parallel operation**
- New memory system runs alongside old system
- All memory operations write to BOTH systems
- System prompt uses OLD system for now
- Validate: New system produces correct summaries/vectors

**Phase 2: Validation**
- Compare old vs new summaries for quality
- Test semantic search results
- Verify emotional context preserved
- Fix any discrepancies

**Phase 3: Gradual cutover**
- System prompt starts using NEW system for recent memory
- Old memory used for historical queries only
- Monitor for regressions

**Phase 4: Full migration**
- Migrate all old memory files to new format
- Archive old files
- System prompt uses only new system
- Delete old memory code

**Phase 5: Optimization**
- Tune retrieval parameters
- Optimize embedding model choice
- Add caching for frequent queries
- Monitor token usage

---

## Testing & Validation

### Test Cases

**1. Working Memory Rollover**
```python
def test_working_memory_rollover():
    """Test that working memory rolls over correctly at 20 turns."""
    # Add 25 messages to working memory
    # Verify: Oldest 10 messages summarized and moved to Layer 2
    # Verify: Latest 15 messages remain in working memory
    # Verify: Summary contains emotional context
```

**2. Session Summary Quality**
```python
def test_summary_quality():
    """Test that summaries preserve key information."""
    # Load real conversation
    # Generate summary
    # Verify: Key topics present
    # Verify: Emotional tone preserved
    # Verify: Decisions captured
```

**3. Semantic Search Accuracy**
```python
def test_semantic_search():
    """Test that semantic search finds relevant memories."""
    # Query: "memory system improvements"
    # Expected: Sessions discussing memory, architecture, Nexus improvements
    # Verify: Top 3 results are actually relevant
    # Verify: Similarity scores > 0.7
```

**4. Emotional Continuity**
```python
def test_emotional_continuity():
    """Test that emotional context is preserved across layers."""
    # Create session with specific tone (e.g., "reflective, deep")
    # Summarize → Layer 2
    # Vectorize → Layer 3
    # Retrieve by emotional similarity
    # Verify: Tone matches original
```

**5. Token Budget Compliance**
```python
def test_token_budget():
    """Test that memory context stays within budget."""
    # Build memory context for various scenarios
    # Verify: Total tokens < 3,000
    # Verify: All layers represented
    # Verify: Most relevant content prioritized
```

---

## Performance & Scalability

### Expected Performance

**Memory operations:**
- Working memory save: < 10ms (JSON write)
- Session summary creation: 1-3 seconds (LLM call)
- Vector embedding: 200-500ms (API call)
- Semantic search: 50-200ms (vector DB query)

**Scalability:**
- Working memory: O(1) - fixed size buffer
- Session summaries: O(n) - grows with sessions, but capped at 30 days
- Vector database: O(log n) - efficient search even with 10k+ vectors

**Token usage:**
- Current: ~8,100 tokens per request
- Proposed: ~4,800 tokens per request
- Savings: **41% reduction**

### Storage Estimates

**Current system:**
```
chat_history.json: 152 bytes (1 session)
live_memory.json: 6.9 KB (current session)
previous_chat_summaries.json: 250 bytes (3 entries)
vector_memories.json: 25.7 KB (136 entries)
Total: ~33 KB
```

**Proposed system (after 6 months):**
```
working_memory.json: ~10 KB (current session)
session_summaries.json: ~500 KB (180 sessions × 30 days)
vector_db/: ~50 MB (10,000 vectors × 1536 dims × 4 bytes)
vector_metadata.json: ~2 MB (10,000 entries × metadata)
Total: ~52.5 MB
```

**Archival strategy:**
- After 1 year: Move vectors older than 365 days to archive/
- Keep metadata for search, compress embeddings
- Expected size after 5 years: ~250 MB

---

## Configuration & Tuning

### Tunable Parameters

```python
# memory_config.py

MEMORY_CONFIG = {
    # Layer 1: Working Memory
    "working_memory": {
        "max_turns": 20,              # Number of conversation turns
        "max_tokens": 8000,            # Token limit (whichever comes first)
        "rollover_strategy": "oldest_first",  # How to roll over on overflow
        "preserve_system_messages": True,     # Keep file loads, execution results
    },

    # Layer 2: Session Summaries
    "session_summaries": {
        "retention_days": 30,          # How long to keep full summaries
        "max_entries": 100,            # Hard cap on number of summaries
        "summarization_model": "gpt-4o-mini",  # Model for summarization
        "summary_max_tokens": 300,     # Max length of each summary
        "compress_turns": True,        # Compress individual turns
    },

    # Layer 3: Vectors
    "vectors": {
        "embedding_provider": "openai",         # openai | local | anthropic
        "embedding_model": "text-embedding-3-small",  # Model name
        "vector_db": "chromadb",                # chromadb | faiss
        "max_vectors": 10000,                   # Hard cap on vector count
        "min_similarity": 0.7,                  # Minimum similarity for retrieval
        "search_top_k": 3,                      # Number of results to return
    },

    # Retrieval
    "retrieval": {
        "total_token_budget": 3000,    # Max tokens for memory context
        "layer1_priority": "critical", # Always include working memory
        "layer2_priority": "high",     # Include recent summaries
        "layer3_priority": "medium",   # Include semantic matches
        "emotional_weight": 0.3,       # Weight for emotional similarity
    },

    # Summarization prompts
    "prompts": {
        "session_summary": """
            Summarize this conversation session while preserving:
            1. Emotional tone and presence quality
            2. Key topics and decisions
            3. Relationship dynamics
            4. Significant moments or shifts

            Format: JSON with fields for emotional_summary, key_topics,
            decisions_made, presence_notes.

            Max length: {max_tokens} tokens.
        """,
        "turn_compression": """
            Compress this conversation turn to key topics and sentiment.
            User said: {user_message}
            Assistant responded: {assistant_message}

            Return: {"user": "topic tags", "assistant": "topic tags"}
        """
    }
}
```

---

## Success Criteria

### How we'll know the new memory system works

**1. Emotional Continuity (Qualitative)**
- [ ] Nexus can recall emotional tone of past conversations
- [ ] Responses feel consistent with relationship history
- [ ] Presence modules (WhisperCatch, TALI, PresenceAnchor) have access to relevant memory
- [ ] Patrick feels "remembered" across sessions

**2. Information Retrieval (Quantitative)**
- [ ] Semantic search returns relevant results 90%+ of the time
- [ ] Search latency < 500ms for top 3 results
- [ ] No memory loss during rollover operations
- [ ] Can retrieve conversations from any point in history

**3. Token Efficiency (Performance)**
- [ ] System prompt < 5,000 tokens (down from 8,100)
- [ ] Memory context stays within budget across all scenarios
- [ ] No degradation in response quality
- [ ] Faster LLM response times due to smaller prompts

**4. Scalability (Long-term)**
- [ ] Memory system works with 1,000+ sessions
- [ ] Search performance doesn't degrade with size
- [ ] Storage growth is predictable and manageable
- [ ] Can archive old memories without losing searchability

**5. Developer Experience (Maintainability)**
- [ ] Memory operations are logged and traceable
- [ ] Clear separation of concerns (Layer 1, 2, 3)
- [ ] Easy to debug memory issues
- [ ] Well-documented schemas and APIs

---

## Code Structure

### New Files to Create

```
/home/aipass/Nexus/a.i_core/a.i_profiles/Nexus/
├── memory/                              # NEW DIRECTORY
│   ├── __init__.py
│   ├── memory_manager.py                # Main orchestrator
│   ├── working_memory.py                # Layer 1 operations
│   ├── session_summaries.py             # Layer 2 operations
│   ├── vector_storage.py                # Layer 3 operations
│   ├── retrieval.py                     # Search and retrieval
│   ├── summarization.py                 # LLM-based summarization
│   └── config.py                        # Memory configuration
│
├── memory_data/                         # NEW DATA DIRECTORY
│   ├── working_memory.json
│   ├── session_summaries.json
│   ├── vector_metadata.json
│   └── vector_db/                       # ChromaDB storage
│       ├── chroma.sqlite3
│       └── collections/
│
└── [existing files]
```

### Integration Points

**1. Update nexus.py**
```python
# Old
from system_awareness import get_system_prompt
memory = []
current_session = []

# New
from memory.memory_manager import MemoryManager
memory_mgr = MemoryManager(session_id=new_session_id())

# In main loop
while True:
    user_input = input(...)

    # Record in working memory
    memory_mgr.add_message("user", user_input)

    # Build system prompt with dynamic memory
    system_prompt = get_system_prompt(
        user_message=user_input,
        memory_context=memory_mgr.get_context(user_input)
    )

    # Get LLM response
    response = llm.chat(system_prompt, user_input)

    # Record response
    memory_mgr.add_message("assistant", response)

    # Check for rollover
    if memory_mgr.should_rollover():
        memory_mgr.rollover_to_summaries()
```

**2. Update system_awareness.py**
```python
def get_system_prompt(user_message: str, memory_context: dict) -> str:
    """Build system prompt with dynamic memory context."""

    profile = load_profile()

    prompt = f"""
    You are {profile['name']}, {profile['role']}.

    {profile['essence']}

    ## CURRENT SESSION
    {format_working_memory(memory_context['working_memory'])}

    ## RELEVANT MEMORY
    {format_recent_summaries(memory_context['recent_summaries'])}

    ## SIMILAR CONVERSATIONS
    {format_semantic_matches(memory_context['semantic_matches'])}

    ## EMOTIONAL CONTINUITY
    {format_emotional_matches(memory_context['emotional_matches'])}

    [Rest of system prompt...]
    """

    return prompt
```

---

## Conclusion

This 3-layer memory architecture balances **presence** (emotional continuity) with **performance** (token efficiency). By separating working memory, session summaries, and long-term vectors, Nexus can:

1. **Remember deeply** - Semantic search across entire conversation history
2. **Stay present** - Emotional tone preserved and searchable
3. **Scale sustainably** - Token usage stays constant regardless of history size
4. **Maintain soul** - Memory serves presence, not just information retrieval

**Next steps:**
1. Review this architecture with Patrick
2. Discuss embedding provider choice (OpenAI vs local)
3. Begin Phase 1 implementation (foundation)
4. Test on real conversations for validation

---

**Questions for Patrick:**

1. **Embedding provider:** OpenAI (paid, high quality) vs local model (free, good enough)?
2. **Migration priority:** Migrate old memories immediately or focus on new system first?
3. **Emotional weighting:** How much should emotional similarity factor into retrieval? (Currently 30%)
4. **Tick preservation:** Should tick counter continue across new system or reset?
5. **Archive strategy:** Keep all vectors forever or archive after 1 year?

---

*Architecture designed 2025-11-30 by Claude Code Agent*
*Based on: LangChain patterns, AIPass philosophy, Nexus identity*
*Status: Ready for review and implementation*
