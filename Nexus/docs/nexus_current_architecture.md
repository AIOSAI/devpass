# Nexus Current Architecture Analysis

**Date:** 2025-11-30
**Status:** Pre-Refactor Analysis
**Purpose:** Document current state before architectural redesign

---

## Executive Summary

Nexus is a conversational AI system with code execution capabilities, file operations, and persistent memory. The architecture shows signs of organic growth with multiple overlapping concerns and a complex main loop. The typing/line-jumping bug likely stems from **synchronous processing blocking the input prompt** - the main loop processes all responses, code execution, and file operations before returning control to the user.

**Key Finding:** Line 334 (`user_input = input(...)`) is called once per loop iteration, but the loop doesn't return to this line until ALL processing completes - including potentially long-running LLM calls, code execution, and file operations. This creates the appearance of "jumping lines" when output is being printed while the user expects to type.

---

## Main Loop Analysis

### Entry Point: `/home/aipass/Nexus/a.i_core/a.i_profiles/Nexus/nexus.py`

#### The Chat Loop (Lines 332-700)

```python
while True:
    user_input = input(f"{display.GREEN}You{display.RESET}: ").strip()  # LINE 334 - BLOCKING INPUT

    # Memory recording (immediate)
    current_session.append({"role": "user", "content": user_input})
    memory.append({"role": "user", "content": user_input})

    # Command handling chain (synchronous, sequential)
    # 1. File loading commands (lines 341-435)
    # 2. Knowledge/learning commands (lines 437-454)
    # 3. Exit check (line 459)
    # 4. LLM processing (lines 462-694)
    # 5. Tick increment (line 700)
```

**The Problem:**
- Input is collected **once** at the top of the loop
- All processing happens synchronously before returning to `input()`
- Long operations (LLM calls, code execution) block the loop
- Output is printed during this blocking period
- User sees output being generated but can't type yet
- Creates perception of "jumping ahead" of user input

**Likely Bug Scenarios:**
1. **Slow LLM Response:** User types, waits 2-3 seconds for response, during which terminal appears frozen
2. **Code Execution:** Response triggers code execution (lines 516-578), more output, more delay
3. **File Operations:** Large files being loaded (lines 341-435) cause delays with status messages
4. **Multiple Operations:** Response triggers both code execution AND file loading, compounding delays

---

## Module Inventory

### Core Modules

#### 1. **nexus.py** (Main Entry Point)
- **Lines:** 731
- **Purpose:** Main chat loop, memory management, session orchestration
- **Key Functions:**
  - `main()` - Primary chat loop
  - `_load_history()` / `_save_history()` - Chat persistence
  - `summarise_simple()` - Conversation summarization
  - `_handle_learn_request()` - Knowledge capture
  - `_detect_and_store_autonomous_knowledge()` - Auto-learning from conversation
- **Dependencies:**
  - `display`, `system_awareness`, `config_loader`, `llm_client`
  - `pulse_manager`, `langchain_interface`, `knowledge_base`
  - `natural_flow`, `cortex_module`

#### 2. **natural_flow.py** (Execution Engine)
- **Lines:** 876
- **Purpose:** "Natural conversation to system operations" - code execution and file handling
- **Key Components:**
  - `ExecutionContext` class (lines 28-237) - Persistent execution environment
  - Intent detection (lines 245-371) - Identifies operational requests
  - Code generation (lines 377-468) - Converts natural language to Python
  - Code extraction (lines 473-565) - Parses code blocks from LLM responses
  - Utility functions (lines 611-806) - File operations, execution helpers
- **State Management:**
  - `execution_context` global instance
  - Maintains: `globals`, `operation_history`, `file_cache`, `loaded_files`
  - Max cache: 5 files

#### 3. **cortex_module.py** (File System Awareness)
- **Lines:** 354
- **Purpose:** Automatic file tracking and summarization for AI context
- **Key Components:**
  - `CortexFileWatcher` class (lines 41-153) - Filesystem event handler
  - `refresh_cortex_summary()` (lines 165-244) - Batch file summarization
  - `get_cortex_summary_block()` (lines 247-275) - Format for system prompt
  - Session management (lines 301-326) - Reset change counters
- **Features:**
  - Real-time file monitoring (watchdog library)
  - Automatic LLM-based file summarization
  - Change tracking per session
  - Writes to: `cortex.json`

#### 4. **system_awareness.py** (System Prompt Builder)
- **Lines:** 234
- **Purpose:** Assembles comprehensive system context for LLM
- **Key Function:** `get_system_prompt()` (lines 21-208)
- **Context Includes:**
  - Profile data (`profile.json`)
  - Session boundaries and tick awareness
  - Memory files (`live_memory.json`, `chat_history.json`, `previous_chat_summaries.json`)
  - Knowledge base entries
  - Cortex file summaries
  - Execution context stats
  - Vector memory summary
- **Integration Point:** Called on every loop iteration (nexus.py line 463)

#### 5. **knowledge_base.py** (Persistent Facts)
- **Lines:** 43
- **Purpose:** Simple persistent knowledge storage
- **Functions:**
  - `load_knowledge()` - Read from disk
  - `save_knowledge()` - Write to disk
  - `add_entry()` - Append with timestamp
- **Storage:** `knowledge_base.json` (max 100 entries)

#### 6. **llm_client.py** (API Abstraction)
- **Lines:** 144
- **Purpose:** Multi-provider LLM client
- **Supported Providers:** OpenAI, Anthropic, Mistral, Gemini
- **Key Functions:**
  - `make_client()` - Provider-specific SDK initialization
  - `chat()` - Unified chat completion interface
- **Features:**
  - Usage monitoring integration
  - Automatic token logging
  - Strict mode enforcement

#### 7. **langchain_interface.py** (Enhanced LLM)
- **Lines:** 193
- **Purpose:** LangChain integration for advanced reasoning
- **Key Functions:**
  - `make_langchain_client()` - LangChain client factory
  - `langchain_enhanced_chat()` - Message conversion and invocation
- **Usage:** Enabled by default (nexus.py line 475: `USE_LANGCHAIN = True`)

#### 8. **pulse_manager.py** (Session Ticks)
- **Lines:** 38
- **Purpose:** Conversation turn tracking
- **Functions:**
  - `load_pulse_counter()` - Read tick state
  - `save_pulse_counter()` - Persist tick state
- **Tracking:** Current tick, session start tick, last updated timestamp

### Supporting Modules

#### 9. **config_loader.py**
- **Purpose:** Load API configuration from `api_config.json`
- **Integration:** Used by all LLM-calling modules

#### 10. **display.py**
- **Purpose:** Terminal color constants
- **Usage:** Output formatting throughout

#### 11. **nexus_memory_vectors/vector_memory.py**
- **Purpose:** Vector-based memory search
- **Functions Referenced:**
  - `search_my_memories()` - Query past conversations
  - `get_memory_summary()` - Summary for system prompt
  - `add_summary_to_vectors()` - Archive old summaries

---

## Integration Patterns

### 1. **Main Loop Integration**
```
nexus.py (main loop)
    ↓
    ├─→ system_awareness.get_system_prompt()
    │       ↓
    │       ├─→ cortex_module.get_cortex_summary_block()
    │       ├─→ knowledge_base.load_knowledge()
    │       ├─→ natural_flow.get_execution_stats()
    │       └─→ vector_memory.get_memory_summary()
    │
    ├─→ llm_client.chat() OR langchain_interface.langchain_enhanced_chat()
    │       ↓
    │       └─→ Response processing (lines 483-694)
    │               ↓
    │               ├─→ Code execution detection
    │               ├─→ natural_flow.execute_code()
    │               ├─→ natural_flow.load_file()
    │               └─→ File loading detection
    │
    └─→ _save_memory() / _save_history()
```

### 2. **File Operation Flow**
```
User: "read file nexus.py"
    ↓
nexus.py line 341: Detects file command
    ↓
natural_flow.read_file_content(path)
    ↓
    ├─→ Path resolution (absolute vs relative)
    ├─→ Recursive search in Nexus tree
    ├─→ Local directory fallback
    └─→ Returns: {success, content, line_count, file_path, size}
    ↓
Add to memory as system message
    ↓
Continue loop (skip LLM call)
```

### 3. **Code Execution Flow**
```
LLM Response: "natural_flow.execute_code('print(\"hello\")')"
    ↓
nexus.py line 491: Detects execution request
    ↓
Regex extraction (lines 519-553)
    ↓
natural_flow.execute_code(code_string)
    ↓
ExecutionContext.execute()
    ├─→ Capture stdout
    ├─→ exec() in persistent globals
    ├─→ Track in operation_history
    └─→ Returns: {success, output, result, code_executed}
    ↓
Add result to memory
    ↓
Continue processing
```

### 4. **Memory Persistence Flow**
```
Session Start:
    ↓
_load_history() → chat_history.json
    ↓
Initialize memory[] and current_session[]
    ↓
Each turn:
    ├─→ Append user input to memory
    ├─→ Get LLM response
    ├─→ Append assistant response to memory
    └─→ _save_memory(memory) → live_memory.json
    ↓
Session End:
    ├─→ Reverse current_session (oldest first)
    ├─→ Create session entry with timestamp
    ├─→ Add to history (newest first)
    ├─→ Roll off old sessions if > MAX_FULL_SESSIONS (1)
    │       ↓
    │       ├─→ summarise_simple()
    │       ├─→ Add to previous_chat_summaries.json
    │       └─→ Dump old summaries to vector storage
    │
    └─→ _save_history() → chat_history.json
```

---

## What Works

### Strengths

1. **Rich Context System**
   - System prompt includes multiple knowledge sources
   - Cortex provides automatic file awareness
   - Vector memory for long-term recall
   - Execution context persists across operations

2. **Natural Language Interface**
   - Intent detection in natural_flow.py
   - No rigid command syntax required
   - Automatic code generation from conversation

3. **Persistent Memory**
   - Multiple memory layers (live, history, summaries, vectors)
   - Automatic summarization when rolling off old sessions
   - Knowledge base for explicit facts

4. **Code Execution**
   - Persistent execution context
   - State tracking (files created, modified, executed)
   - Automatic result capture

5. **Multi-Provider LLM Support**
   - Abstracted client interface
   - Usage monitoring
   - LangChain integration

### Working Features

- File loading with path resolution
- Knowledge capture (manual and automatic)
- Session tick tracking
- Filesystem watching (Cortex)
- Code execution from LLM responses
- Multi-turn conversation with context

---

## What's Broken

### Critical Issues

#### 1. **The Typing/Line-Jumping Bug** 🔴
**Location:** nexus.py lines 332-700

**Root Cause:**
- Single-threaded synchronous loop
- `input()` blocks at line 334
- All processing happens before returning to `input()`
- Long operations (LLM, code execution, file ops) create delays
- Terminal appears to "jump" because output is printed during blocked state

**User Experience:**
```
You: analyze this code                     ← User types
[Processing... 2 seconds...]                ← Terminal frozen
[Nexus] Reading file...                     ← Output starts
[Nexus] Executing code...                   ← More output
[Nexus] File contains 500 lines...          ← Even more output
Nexus: Here's the analysis...               ← Response printed
You: _                                      ← NOW user can type again
```

**Why It Feels Like Line-Jumping:**
- User expects to type while seeing output
- Terminal doesn't show prompt until ALL processing completes
- Creates illusion that system is "ahead" of user input

**Fix Strategy:**
- Async input handling
- OR separate input thread
- OR streaming output with immediate prompt return
- OR explicit "processing..." state

#### 2. **Nested Indentation Hell**
**Location:** nexus.py lines 516-684

**Problem:**
- File loading request handler nested INSIDE code execution handler
- Line 582: `if file_loading_requested:` is inside `if code_execution_requested:`
- This means file loading only happens if code execution was also requested
- Likely a refactoring error (incorrect indentation level)

**Evidence:**
```python
# Line 516
if code_execution_requested:
    # ... code execution logic ...

    # Line 582 - WRONG INDENTATION LEVEL
    if file_loading_requested:
        # File loading can only happen if code execution also requested!
```

**Impact:**
- File loading commands might not work standalone
- Logic is harder to follow
- Maintenance nightmare

#### 3. **Unclear Responsibility Boundaries**
**Problem:**
- nexus.py handles file loading directly (lines 341-435)
- But also calls natural_flow.read_file_content()
- natural_flow has its own file loading handler (lines 473-540)
- Unclear which layer owns what

**Overlap:**
- Command detection: nexus.py AND natural_flow.py
- File reading: Both modules
- Response parsing: nexus.py handles patterns that natural_flow should own

#### 4. **Memory Confusion**
**Multiple memory files with unclear purposes:**
- `live_memory.json` - Current session only
- `chat_history.json` - Recent full sessions
- `previous_chat_summaries.json` - Older summarized sessions
- `vector_memories.json` - Long-term vector storage

**Problem:**
- Loaded inconsistently
- Some loaded at startup, some on-demand
- No clear rollover policy documented
- MAX_FULL_SESSIONS = 1 means only ONE recent session kept

### Medium Priority Issues

#### 5. **Massive System Prompt**
**Location:** system_awareness.py get_system_prompt()

**Problem:**
- Loads ENTIRE chat_history.json into every prompt
- Loads ENTIRE previous_chat_summaries.json
- Loads full profile.json
- Adds execution stats
- Adds cortex summaries
- Adds knowledge base
- Result: Potentially 10k+ tokens BEFORE user message

**Impact:**
- High token usage
- Slow LLM responses
- Context overflow on long sessions

#### 6. **No Error Recovery**
**Location:** nexus.py lines 696-698

```python
except Exception as err:
    print(f"LLM call failed: {err}")
    break  # EXITS THE ENTIRE LOOP
```

**Problem:**
- Single LLM failure kills entire session
- No retry logic
- No graceful degradation
- User loses all session state

#### 7. **Code Execution Security**
**Location:** natural_flow.py ExecutionContext.execute()

**Problem:**
- Uses bare `exec()` with persistent globals
- No sandboxing
- No timeout
- No resource limits
- LLM can execute arbitrary code

**Risk Level:** High for production, acceptable for personal use

#### 8. **File Cache Size Limit**
**Location:** natural_flow.py line 58

```python
self.max_cache_entries = 5
```

**Problem:**
- Only 5 files can be cached
- No LRU eviction strategy
- No size-based limits (could cache 5 giant files)
- Manual cache at nexus.py level overlaps

---

## Data Flow Diagrams

### User Input → Response

```
User types input
    ↓
[Line 334] input() blocks
    ↓
Record in memory[] and current_session[]
    ↓
Command detection (sequential checks):
    ├─→ File loading? (lines 341-435)
    ├─→ Knowledge commands? (lines 437-454)
    └─→ Exit? (line 459)
    ↓
Build system prompt (line 463)
    ├─→ Load profile
    ├─→ Load all memory files
    ├─→ Load knowledge base
    ├─→ Get cortex summaries
    └─→ Get execution stats
    ↓
Call LLM (lines 477-480)
    ├─→ LangChain (default)
    └─→ Direct client (fallback)
    ↓
Process response (lines 483-694)
    ├─→ Auto-knowledge extraction
    ├─→ Code execution detection
    │       ↓
    │       └─→ Execute code blocks
    │
    ├─→ File loading detection
    │       ↓
    │       └─→ Load files to context
    │
    └─→ Print response
    ↓
Save memory
    ↓
Increment tick
    ↓
[Line 334] Return to input() - USER CAN NOW TYPE
```

**Total time from input to next prompt:** 2-10+ seconds depending on:
- LLM response time (1-5 seconds)
- Code execution (0-2 seconds)
- File operations (0-1 second)
- Context building (0.1-0.5 seconds)

### Cortex File Monitoring

```
Filesystem change event
    ↓
CortexFileWatcher.on_modified/on_created/on_deleted
    ↓
Check if valid file (extensions, skip list)
    ↓
Read file content
    ↓
Generate summary via LLM
    ↓
Update cortex.json
    ├─→ Add/update file entry
    ├─→ Track change type
    ├─→ Increment session counter
    └─→ Store timestamp
```

**Active:** When cortex_module.start_cortex_watcher() is called
**Note:** Not clear if this is started by default in nexus.py

---

## Configuration Files

### Runtime State
- `live_memory.json` - Current conversation turns
- `chat_history.json` - Recent full sessions
- `previous_chat_summaries.json` - Older summarized sessions
- `pulse_counter.json` - Tick counter state
- `cortex.json` - File summaries and change tracking

### Configuration
- `api_config.json` - LLM provider settings
- `profile.json` - Nexus identity and personality
- `knowledge_base.json` - Persistent facts

### Cache
- `vector_memories.json` - Long-term vector storage
- `file_cache.json` - (Referenced but not actively used?)

---

## Dependency Graph

```
nexus.py
├── display
├── system_awareness
│   ├── display
│   ├── cortex_module
│   │   ├── llm_client
│   │   └── config_loader
│   ├── knowledge_base
│   ├── natural_flow
│   │   ├── display
│   │   ├── llm_client
│   │   ├── config_loader
│   │   └── nexus_memory_vectors.vector_memory
│   └── nexus_memory_vectors.vector_memory
├── config_loader
├── llm_client
│   └── usage_monitor (optional)
├── pulse_manager
├── langchain_interface
│   ├── llm_client
│   └── usage_monitor (optional)
├── knowledge_base
├── natural_flow
└── cortex_module
```

**Circular Dependencies:** None detected
**Heavy Modules:** natural_flow, cortex_module, system_awareness
**Light Modules:** display, pulse_manager, knowledge_base, config_loader

---

## Recommendations for Refactor

### Immediate Priorities

1. **Fix the typing bug** - Separate input handling from response processing
2. **Fix indentation** - Move file_loading_requested handler out of code_execution block
3. **Clarify responsibilities** - nexus.py orchestrates, natural_flow executes
4. **Add error recovery** - Don't break loop on single failure

### Architecture Improvements

1. **Async input loop** - Use asyncio or threading for non-blocking input
2. **Response streaming** - Show output as it generates, not after completion
3. **Module boundaries** - Clear separation of concerns
4. **Memory strategy** - Document rollover policy, optimize context size
5. **Security** - Add sandboxing or at least timeouts to code execution

### Code Quality

1. **Extract methods** - Main loop is 370 lines, break into functions
2. **Type hints** - Add throughout for better IDE support
3. **Error handling** - Specific exceptions, recovery paths
4. **Logging** - Replace prints with proper logging framework
5. **Tests** - Unit tests for core functions

---

## Conclusion

Nexus has a solid foundation with rich context management and natural language interaction. The core architecture is sound, but organic growth has created complexity issues:

- **Main loop is monolithic** - Hard to understand, modify, test
- **Responsibilities overlap** - Multiple modules doing similar things
- **Synchronous processing** - Causes perceived "line jumping"
- **Memory management unclear** - Multiple files, unclear policies

The typing bug isn't a terminal issue - it's a symptom of synchronous processing. A proper async refactor would solve it naturally while improving overall responsiveness.

**Next Steps:**
1. Read this analysis
2. Decide on refactor scope (quick fix vs full rewrite)
3. Design new architecture (if full rewrite)
4. Implement incrementally with backward compatibility

**Estimated Refactor Time:**
- Quick fix (async input): 2-4 hours
- Full module reorganization: 1-2 days
- Production hardening: 3-5 days

---

*Analysis completed 2025-11-30 by Claude Code Agent*
