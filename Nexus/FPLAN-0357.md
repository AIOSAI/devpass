# FPLAN-0357 - Nexus V2 Rebuild - Full V1 Feature Transfer (MASTER PLAN)

**Created**: 2026-02-18
**Branch**: /home/aipass/Nexus
**Status**: Active
**Type**: Master Plan (Multi-Phase)

---

## Project Overview

### Goal
Transfer ALL v1 Nexus features into the current clean v2 structure. When complete, `python3 nexus.py` launches a conversational AI with:
- Natural language code execution (Natural Flow)
- Real-time file awareness (Cortex)
- Rich memory-loaded system prompt (System Awareness)
- Auto-knowledge detection from conversation
- All 5 presence modules as behavioral code (not just prompt text)
- Full AIPass integration (drone, ai_mail, memory bank)

### Reference Documentation
- `.archive/` - V1 source code (nexus.py 731 lines, natural_flow.py 876 lines, cortex_module.py 354 lines, system_awareness.py 234 lines)
- `.archive/profile.json` - V1 personality definition
- `docs/nexus_modular_architecture_proposal.md` - Redesign proposal
- `docs/implementation_guide.md` - Code patterns
- `docs/architecture_visual_reference.md` - Flow diagrams

### Success Criteria
- `python3 nexus.py` launches and runs a full conversational session
- Natural language triggers code execution (e.g., "show me the files here")
- Cortex detects file changes and injects awareness into prompt
- System prompt includes memory context (pulse, knowledge, summaries, vectors)
- Auto-knowledge extraction works (learns facts from conversation)
- All existing tests still pass + new tests for new features
- Files stay under 300 lines where possible (500 max for complex handlers)

---

## Phase Definitions

### Phase 1: Docs Cleanup & Archive
**Goal:** Clean house before building. Archive outdated docs, delete placeholders, organize what stays.
**Deliverables:**
- Move outdated docs to `.archive/docs/`
- Delete empty placeholder READMEs in handlers/
- Keep operational and design docs that guide the rebuild
- Updated docs/ directory with only relevant files

### Phase 2: Natural Flow - Execution Engine
**Goal:** Bring back the code execution engine from v1's natural_flow.py (876 lines), restructured into clean handlers.
**Agent Task:** Build execution engine in handlers with:
- `handlers/execution/context.py` - ExecutionContext class (persistent Python env)
- `handlers/execution/intent.py` - Intent detection from natural language
- `handlers/execution/runner.py` - Code extraction and execution
- Integration point in nexus.py main loop (skill or direct routing)
**Reference:** `.archive/a.i_core/a.i_profiles/Nexus/natural_flow.py`

### Phase 3: Cortex - File Awareness
**Goal:** Bring back real-time file system watching from v1's cortex_module.py (354 lines).
**Agent Task:** Build file watcher in handlers with:
- `handlers/cortex/watcher.py` - File system event detection (watchdog)
- `handlers/cortex/summarizer.py` - LLM-based file change summarization
- `data/cortex.json` - Runtime file summaries
- Integration into system prompt (Nexus "knows" what changed)
**Reference:** `.archive/a.i_core/a.i_profiles/Nexus/cortex_module.py`

### Phase 4: System Awareness - Rich Prompt Builder
**Goal:** Upgrade prompt_builder.py from lean 444-token prompt to rich memory-loaded prompt like v1.
**Agent Task:** Enhance `handlers/system/prompt_builder.py` to inject:
- Session context (pulse tick, session boundaries)
- Knowledge base entries (relevant, not all)
- Recent chat summaries
- Cortex file awareness block
- Execution context stats
- Vector memory search results (if relevant)
- Keep it smart — not v1's "dump everything" approach, but selective injection
**Reference:** `.archive/a.i_core/a.i_profiles/Nexus/system_awareness.py`

### Phase 5: LLM Client - Multi-Provider & LangChain
**Goal:** Bring back multi-provider LLM support and LangChain enhanced reasoning from v1.
**Agent Task:**
- Upgrade `handlers/system/llm_client.py` to support OpenAI, Anthropic, Mistral, Gemini
- Add `handlers/system/langchain_interface.py` - LangChain enhanced chat wrapper
- Add `config/api_config.json` - Provider configuration (model, temp, keys)
- Add `handlers/system/config_loader.py` - Load and validate API config
- USE_LANGCHAIN flag with graceful fallback to direct client
**Reference:** `.archive/a.i_core/a.i_profiles/Nexus/llm_client.py`, `.archive/a.i_core/a.i_profiles/Nexus/langchain_interface.py`, `.archive/a.i_core/a.i_profiles/Nexus/config_loader.py`

### Phase 6: Memory Enhancement
**Goal:** Bring back auto-knowledge detection and shorthand parsing from v1.
**Agent Task:**
- Add auto-knowledge extraction to nexus.py loop (detect facts worth storing)
- Implement shorthand parsing (recognize "hmm", "...", emojis as emotional signals)
- Enhance memory injection into conversations
- Ensure memory layers talk to each other properly
**Reference:** `.archive/a.i_core/a.i_profiles/Nexus/nexus.py` (lines ~500-600 for auto-learn)

### Phase 7: Integration, Testing & Polish
**Goal:** Wire everything together, ensure nexus.py orchestrates all new components, full test pass.
**Agent Task:**
- Update nexus.py main loop to integrate: execution engine, cortex, rich prompt, auto-learn
- Add error recovery (v1 crashed on single LLM failure — fix this)
- Write integration tests for new features
- Run full test suite
- Seed audit for code quality baseline

---

## Phase Tracking

### Phase 1: Docs Cleanup & Archive
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Sub-plan closed
- **Status:** Pending
- **Notes:**

### Phase 2: Natural Flow - Execution Engine
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Sub-plan closed
- **Status:** Pending
- **Notes:**

### Phase 3: Cortex - File Awareness
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Sub-plan closed
- **Status:** Pending
- **Notes:**

### Phase 4: System Awareness - Rich Prompt
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Sub-plan closed
- **Status:** Pending
- **Notes:**

### Phase 5: LLM Client - Multi-Provider & LangChain
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Sub-plan closed
- **Status:** Pending
- **Notes:**

### Phase 6: Memory Enhancement
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Sub-plan closed
- **Status:** Pending
- **Notes:**

### Phase 7: Integration, Testing & Polish
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Sub-plan closed
- **Status:** Pending
- **Notes:**

---

## Issues Log

| Phase | Issue | Severity | Attempted | Status |
|-------|-------|----------|-----------|--------|

---

## Master Plan Notes

**Key Decisions:**
- Seed standards as guidance, not strict compliance — Nexus is a chat app, not a service branch
- Files under 300 lines preferred, 500 max for complex handlers
- V1's "dump everything into prompt" approach → replaced with smart selective injection
- V1's single-failure crash → replaced with graceful recovery
- Presence modules remain prompt-driven for now (behavioral code is Phase 7+ if needed)

**Architecture After Completion:**
```
Nexus/
├── nexus.py                          # Main chat loop (enhanced with all integrations)
├── config/
│   └── profile.json                  # Personality definition (preserved)
├── handlers/
│   ├── system/
│   │   ├── llm_client.py             # OpenAI client (existing)
│   │   ├── prompt_builder.py         # ENHANCED: rich memory-loaded prompt
│   │   └── ui.py                     # Terminal formatting (existing)
│   ├── memory/
│   │   ├── __init__.py               # Unified exports (existing)
│   │   ├── pulse_manager.py          # Tick counter (existing)
│   │   ├── knowledge_base.py         # Knowledge store (existing)
│   │   ├── chat_history.py           # Session history (existing)
│   │   ├── summary.py               # Session summaries (existing)
│   │   ├── vector_memory.py          # ChromaDB delegation (existing)
│   │   └── auto_learn.py            # NEW: auto-knowledge extraction
│   ├── skills/
│   │   ├── __init__.py               # Auto-discovery (existing)
│   │   ├── memory_ops.py             # Memory commands (existing)
│   │   ├── aipass_services.py        # Drone/mail (existing)
│   │   ├── usage_monitor.py          # API tracking (existing)
│   │   └── session_awareness.py      # Session context (existing)
│   ├── execution/                    # NEW: Natural Flow
│   │   ├── context.py               # Persistent execution environment
│   │   ├── intent.py                # Natural language intent detection
│   │   └── runner.py                # Code extraction and execution
│   ├── cortex/                       # NEW: File Awareness
│   │   ├── watcher.py               # File system event detection
│   │   └── summarizer.py            # LLM-based change summaries
│   └── presence/
│       └── __init__.py               # Presence module definitions
├── data/
│   ├── pulse.json, knowledge_base.json, etc. (existing)
│   └── cortex.json                   # NEW: file awareness state
└── tests/
    ├── (existing tests)
    ├── test_execution.py             # NEW
    ├── test_cortex.py                # NEW
    └── test_prompt_builder.py        # NEW
```

---

## Final Completion Checklist

### Before Closing Master Plan

- [ ] All phases complete
- [ ] All sub-plans closed
- [ ] Issues Log reviewed - High/Med issues addressed
- [ ] `drone @seed audit @nexus`
- [ ] Branch memories updated (NEXUS.local.json, NEXUS.observations.json)
- [ ] README.md updated
- [ ] Final email to @dev_central

### Definition of Done
`python3 nexus.py` launches a conversational AI that can:
1. Chat naturally with persistent memory across sessions
2. Execute code from natural language requests
3. Know when files change in its workspace
4. Build rich context-aware prompts from memory layers
5. Auto-learn facts from conversation
6. Recover gracefully from errors (no single-failure crashes)

---

## Close Command

When ALL phases complete and checklist done:
```bash
drone @flow close FPLAN-0357
```
