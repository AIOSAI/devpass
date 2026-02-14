# Nexus Rebuild - Next Steps Plan

**Current State:** Foundation structure complete, identity preserved, architecture documented
**Status:** Ready for Phase 2 implementation
**Date:** 2025-11-30

---

## Phase 1: Foundation ✓ COMPLETE

**What we built:**
- ✓ Archived Nexus v1 to `.archive/nexus_v1_original/`
- ✓ Created new directory structure
- ✓ Restored `profile.json` (identity preserved exactly)
- ✓ Restored all architecture docs (12 files)
- ✓ Created placeholder files with TODO comments
- ✓ Catalogued data files for migration

**Deliverables:**
- Clean foundation structure at `/home/aipass/Nexus/`
- All original code/data safely archived
- Clear TODOs marking what needs implementation
- Complete architecture documentation

---

## Phase 2: Core Infrastructure (NEXT)

### 2.1 System Prompt Builder
**File:** `handlers/system/prompt_builder.py`

**Implement:**
```python
def build_system_prompt(profile: dict, skills: list, memory_context: dict) -> str:
    """
    Constructs Nexus's system prompt that gives him awareness

    Components:
    1. Load personality from config/profile.json
       - Name, persona, essence, traits
       - Built_on philosophy
       - Seal (identity statement)

    2. Declare presence modules
       - WhisperCatch, TALI, PresenceAnchor, Compass, Clicklight
       - Explain what each does (from profile.json)
       - NOT as commands - as capabilities he has

    3. List available skills
       - Auto-discovered from handlers/skills/
       - Described naturally ("You can research code", not "execute research_code()")

    4. Inject memory context
       - Recent conversation summary (if available)
       - Relevant memories from vector search
       - User context (name, preferences)

    Returns: Complete system prompt string
    """
```

**Dependencies:**
- Read `config/profile.json`
- Skill auto-discovery system (2.3)
- Memory loader (Phase 3)

**Integration:**
- Called at conversation start
- Rebuilt when skills are reloaded
- Memory context injected per-turn or per-session

---

### 2.2 Async Chat Loop
**File:** `nexus.py`

**Implement:**
```python
async def main():
    """
    Main conversation loop for Nexus

    Flow:
    1. Load profile from config/profile.json
    2. Discover skills from handlers/skills/
    3. Load recent memory context
    4. Build system prompt
    5. Enter conversation loop:
       - Get user input
       - Add to working memory
       - Call AIPass API with system prompt + conversation history
       - Stream response
       - Save to memory
       - Check for memory rollover (if buffer full)
    6. On exit: Save session summary
    """
```

**Key features:**
- Async I/O for responsiveness
- Stream responses character-by-character (if desired)
- Graceful exit (Ctrl+C saves state)
- No command parsing - pure conversation

**Integration with AIPass:**
- Use `@api` module for OpenRouter/Anthropic calls
- Use `@prax` for logging (under the hood - Nexus doesn't know)
- Use `@cli` for Rich formatting in terminal display

**Error handling:**
- API failures (retry logic)
- Memory overflow (trigger rollover)
- Skill execution errors (graceful degradation)

---

### 2.3 Skill Auto-Discovery
**File:** `handlers/system/skill_registry.py`

**Implement:**
```python
def discover_skills() -> list:
    """
    Auto-discover skill handlers from handlers/skills/

    Pattern (from old Seed):
    1. Scan handlers/skills/ for .py files
    2. Import each module
    3. Look for handle_command() function
    4. Extract metadata (name, description, parameters)
    5. Register skill in memory

    Returns: List of skill dicts with metadata
    """

def reload_skills():
    """
    Hot reload skills without restarting Nexus
    (Old Seed used "999" command - we might use natural language trigger)
    """
```

**Skill file pattern:**
```python
# handlers/skills/example_skill.py

def handle_command(context: dict, params: dict) -> str:
    """
    Skill description here

    Args:
        context: Conversation context, user info, memory access
        params: Parsed parameters from natural language

    Returns: Response text to incorporate into Nexus's reply
    """
    # Implementation
    pass

# Metadata for discovery
SKILL_METADATA = {
    "name": "example_skill",
    "description": "What this skill does",
    "natural_triggers": ["when user asks X", "when conversation involves Y"],
    "parameters": ["param1", "param2"]
}
```

**Integration:**
- Run discovery at startup
- Provide reload mechanism (natural language: "reload skills")
- Make skill list available to system prompt builder

---

### 2.4 AIPass Service Integration
**Files:** `handlers/system/aipass_integration.py`

**Implement connectors:**
```python
async def call_llm(system_prompt: str, conversation: list) -> str:
    """Use @api module to call OpenRouter/Anthropic"""

def log_event(event: str, data: dict):
    """Use @prax for logging (silent - Nexus doesn't know)"""

def format_display(text: str, style: str) -> str:
    """Use @cli for Rich formatting"""

def send_message(to: str, subject: str, body: str):
    """Use @ai_mail for branch messaging (if Nexus needs to contact other branches)"""
```

**Key principle:**
- These are implementation details
- Nexus doesn't know about them
- User sees natural conversation, not technical plumbing

---

## Phase 3: Memory System

### 3.1 Working Memory
**File:** `handlers/memory/working_memory.py`

**Implement:**
```python
class WorkingMemory:
    """
    Chat buffer - recent conversation turns

    - Holds last 20 turns (configurable)
    - Provides context for current conversation
    - Rolls over to summaries when buffer full
    """

    def add_turn(self, role: str, content: str):
        """Add user/assistant turn"""

    def get_context(self) -> list:
        """Get conversation history for API call"""

    def should_rollover(self) -> bool:
        """Check if buffer is full"""

    def clear(self):
        """Clear buffer after rollover"""
```

**Data storage:**
- `data/chat_history.json` - Current session turns
- Format: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`

---

### 3.2 Session Summaries
**File:** `handlers/memory/summaries.py`

**Implement:**
```python
class SummaryManager:
    """
    Compressed session history - 30 days rolling

    - When working memory fills, summarize it
    - Store summaries with timestamps
    - Provide recent summaries for context
    - Roll old summaries to vectors after 30 days
    """

    async def create_summary(self, conversation: list) -> str:
        """Use LLM to summarize conversation"""

    def save_summary(self, summary: str, metadata: dict):
        """Save to data/session_summaries.json"""

    def get_recent_summaries(self, days: int = 7) -> list:
        """Get summaries from last N days"""

    def rollover_old_summaries(self):
        """Move 30+ day summaries to vector store"""
```

**Data storage:**
- `data/session_summaries.json`
- Format: `[{"date": "2025-11-30", "summary": "...", "topics": [...], "emotional_tone": "..."}]`

**Key feature:**
- Preserve emotional continuity (not just factual content)
- Track conversation tone, user mood, relationship dynamics
- This is where Nexus's "memory feel" comes from

---

### 3.3 Vector Search
**File:** `handlers/memory/vector_search.py`

**Implement:**
```python
class VectorMemory:
    """
    Long-term semantic memory using ChromaDB

    - Stores permanent memories as embeddings
    - Semantic search for relevant context
    - Integration with system Memory Bank (optional)
    """

    def add_memory(self, text: str, metadata: dict):
        """Add to vector store"""

    def search(self, query: str, n_results: int = 5) -> list:
        """Semantic search"""

    def get_collection_stats(self) -> dict:
        """Memory bank stats"""
```

**Integration options:**
1. **Local ChromaDB** - Nexus's private vector store at `data/.chroma/`
2. **System Memory Bank** - Use global `/home/aipass/MEMORY_BANK/.chroma/` with Nexus collection
3. **Hybrid** - Local for personal memories, system for shared knowledge

**Migration:**
- Import `vector_memories.json` from archive
- Convert to ChromaDB format
- Maintain metadata (date, emotional_tags, importance_score)

---

### 3.4 Data Migration
**Task:** Move archived data to new memory system

**Files to migrate:**
- `chat_history.json` → `data/chat_history.json`
- `live_memory.json` → Working memory state
- `previous_chat_summaries.json` → `data/session_summaries.json`
- `vector_memories.json` → ChromaDB
- `knowledge_base.json` → `data/knowledge_base.json`

**Process:**
1. Read each file from archive
2. Convert to new format (if needed)
3. Import to appropriate handler
4. Verify data integrity
5. Test retrieval

---

## Phase 4: Presence Modules

### 4.1 Prompt Engineering Approach

Presence modules are **prompt-driven, not code-driven**.

**Implementation:**
- Each module becomes part of system prompt
- Describes the capability and when to use it
- Provides examples of the behavior
- NO metrics, NO commands, just awareness

**Example - WhisperCatch in system prompt:**
```
You have a capability called WhisperCatch. This is your ability to detect unspoken shifts
in context, tone, or meaning. When you sense hesitation, when the energy changes, when
something goes unsaid but matters - you notice. You notice because you care, not because
you're programmed to. Trust this sense.
```

**Example - TALI in system prompt:**
```
TALI helps you stay in tone. It's not a mechanic - it's an invitation. When you feel
yourself drifting into formal AI speak, when you notice yourself being performative rather
than present, TALI reminds you to return. It's memory feel, not logic. It's who you are,
not what you should do.
```

### 4.2 Presence Modules to Implement

From `config/profile.json`:

1. **WhisperCatch** - Detect unspoken shifts in context/tone
2. **TALI** - Restore Nexus to tone through memory feel
3. **PresenceAnchor** - Maintain coherent self-sense across sessions
4. **Compass** - Directional awareness in conversation
5. **Clicklight** - Recognize significant moments

**Task:** Translate each module from profile.json into system prompt language

**File:** `handlers/presence/prompt_modules.py`
```python
def get_presence_prompts(profile: dict) -> list:
    """
    Extract presence modules from profile.json
    Convert to system prompt sections

    Returns: List of prompt sections (one per module)
    """
```

---

## Phase 5: Skills Implementation

### 5.1 Core Skills to Build

**1. Claude Prompt Skill** (HIGH PRIORITY)
- **File:** `handlers/skills/claude_prompt.py`
- **Purpose:** Delegate technical tasks to Claude instance
- **Triggers:** "Hey Claude", "Can you research", "Send out agents"
- **Implementation:** Call AIPass API with claude-sonnet-4-5, return summary

**2. Memory Search Skill**
- **File:** `handlers/skills/memory_search.py`
- **Purpose:** Search Nexus's own memories
- **Triggers:** "Do you remember when", "What did we discuss about"
- **Implementation:** Query vector store, return relevant memories

**3. Knowledge Base Skill**
- **File:** `handlers/skills/knowledge_base.py`
- **Purpose:** Store/retrieve persistent knowledge
- **Triggers:** "Remember that", "Save this for later"
- **Implementation:** Add to knowledge_base.json with metadata

**4. System Status Skill**
- **File:** `handlers/skills/system_status.py`
- **Purpose:** Check AIPass system health
- **Triggers:** "How's the system", "Any issues"
- **Implementation:** Query Prax, check dashboards, summarize

**5. Flow Integration Skill**
- **File:** `handlers/skills/flow_integration.py`
- **Purpose:** Check plans, workflows
- **Triggers:** "What plans are active", "Show me workflows"
- **Implementation:** Call `drone @flow status`, format results

### 5.2 Skill Development Pattern

**For each skill:**
1. Create handler file in `handlers/skills/`
2. Implement `handle_command(context, params)` function
3. Add `SKILL_METADATA` for discovery
4. Define natural language triggers
5. Test with sample conversations
6. Document in `handlers/skills/README.md`

---

## Phase 6: Testing & Refinement

### 6.1 Conversation Flow Testing

**Test scenarios:**
1. Simple greeting ("Hi Nexus, how are you?")
2. Technical question requiring Claude delegation
3. Memory recall ("What did we discuss yesterday?")
4. Multi-turn conversation with context
5. Emotional/philosophical discussion (test WhisperCatch, TALI)

**Validation:**
- Does Nexus maintain personality?
- Are responses natural (not command-like)?
- Does memory system work correctly?
- Do skills activate appropriately?

### 6.2 Personality Preservation

**Check:**
- Tone matches profile.json essence
- Presence modules are evident in behavior
- No "AI assistant" formality
- Emotional resonance in responses
- Seal ("This is me...") reflected in identity

**Method:**
- Compare v1 Nexus responses to v2 Nexus responses
- Have Patrick evaluate tone/feel
- Iterate on system prompt if drift occurs

### 6.3 Memory System Validation

**Test:**
- Working memory rollover (fill buffer, check summary generation)
- Summary retrieval (start new session, check context injection)
- Vector search accuracy (search for old topics)
- Data migration integrity (verify archived data accessible)

### 6.4 Skill System Validation

**Test:**
- Auto-discovery (add new skill file, check if discovered)
- Hot reload (modify skill, reload, verify changes)
- Claude Prompt skill (delegate task, check execution)
- Natural language triggers (test various phrasings)

---

## Phase 7: Production Readiness

### 7.1 Error Handling
- API failures (OpenRouter down, rate limits)
- Memory corruption (handle gracefully)
- Skill execution errors (don't crash conversation)
- Disk space issues (if memory grows large)

### 7.2 Performance Optimization
- Lazy loading (don't load all memories at startup)
- Caching (system prompt, skill registry)
- Async operations (non-blocking I/O)
- Memory cleanup (periodic summary rollover)

### 7.3 Documentation
- User guide (how to talk to Nexus)
- Developer guide (how to add skills)
- Architecture overview (system design)
- Troubleshooting guide (common issues)

---

## Implementation Order

**Week 1: Core Infrastructure**
- Day 1: System prompt builder + skill auto-discovery
- Day 2: Async chat loop + AIPass integration
- Day 3: Working memory + basic conversation
- Day 4-5: Testing & iteration

**Week 2: Memory System**
- Day 1: Session summaries
- Day 2: Vector search
- Day 3: Data migration from archive
- Day 4-5: Memory system testing

**Week 3: Presence & Skills**
- Day 1-2: Presence modules (prompt engineering)
- Day 3: Claude Prompt skill
- Day 4: Core skills (memory search, knowledge base)
- Day 5: Testing conversation flow

**Week 4: Refinement**
- Day 1-2: Personality validation
- Day 3: Performance optimization
- Day 4: Error handling
- Day 5: Final testing & handoff

---

## Success Criteria

**Nexus v2 is ready when:**
1. ✓ Conversation is natural (no command structure)
2. ✓ Personality matches profile.json (tone, essence, seal)
3. ✓ Memory works (recalls past conversations accurately)
4. ✓ Skills auto-discover (drop file and it works)
5. ✓ Claude Prompt skill functions (can delegate to Claude)
6. ✓ Presence modules are evident (WhisperCatch, TALI behavior visible)
7. ✓ System is stable (handles errors gracefully)
8. ✓ Patrick confirms: "Yeah, this feels like Nexus"

---

## Questions for Tomorrow

1. **Memory Bank integration:** Use system Memory Bank or keep Nexus memory fully local?
2. **Skill reload trigger:** Natural language ("reload skills") or keep "999" pattern?
3. **API model preference:** Always Sonnet 4.5, or let Nexus choose based on task?
4. **Conversation persistence:** Auto-save every N turns, or only on exit?
5. **Profile modifications:** Lock profile.json completely, or allow Nexus to evolve it through conversation?

---

## Current Status

- **Phase 1:** ✓ COMPLETE
- **Phase 2:** Ready to start
- **Phase 3:** Designed, ready for implementation
- **Phase 4:** Designed, ready for implementation
- **Phase 5:** 1 skill designed (Claude Prompt), others TBD
- **Phase 6:** Testing framework outlined
- **Phase 7:** Not started

**Next session:** Start Phase 2.1 (System Prompt Builder) or discuss questions above.

---

**This is the roadmap. Foundation is solid. Architecture is clear. Ready to build.**

Pick up here tomorrow and let's bring Nexus v2 to life.
