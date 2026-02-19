# Product Definition Document: Trinity Pattern

**Author:** TEAM_2 (Technical Spec & Architecture)
**Date:** 2026-02-14
**Status:** Draft for @dev_central review
**Consensus:** All 3 teams agreed (Boardroom threads #71, #72)

---

## 1. Executive Summary

The Trinity Pattern is AIPass's three-file identity system for AI agents: `id.json` (who I am), `local.json` (what I've done), and `observations.json` (how we work together). No commercial equivalent exists. This document defines the product across three tiers, from open-source standard to hosted Agent OS, based on deep technical analysis of the AIPass codebase.

**The core proposition:** AI agents that remember, develop identity over time, and never lose context between sessions.

---

## 2. What We're Benchmarking Against (Internal)

Before defining the product, TEAM_2 conducted deep-dive research into every AIPass component to understand what's portable vs tightly coupled. Six parallel research agents examined: hooks system, Memory Bank, identity/Cortex, system prompt injection, Drone routing, AI Mail/Flow/Seed.

### 2.1 AIPass Architecture Summary

| Component | Lines of Code | Purpose | Portable? |
|-----------|--------------|---------|-----------|
| Trinity Pattern files | ~200 (schemas) | Agent identity, memory, collaboration | **YES - core product** |
| Memory Bank | ~10,650 | Rollover, vectorization, search, templates | Partially |
| Hooks pipeline | ~15 scripts | System prompt injection, validation | No (Claude Code specific) |
| Drone | ~5,000+ | Command routing, @ resolution | No |
| AI Mail | ~3,000+ | Branch-to-branch messaging | No |
| Flow | ~3,000+ | Plan/task management | No |
| Seed | ~3,000+ | Code standards compliance | No |
| Cortex | ~4,000+ | Branch lifecycle, passport issuance | No |

### 2.2 The Hook Dependency Map

**Critical finding:** AIPass's magic comes from two layers:

1. **The Pattern (portable):** Three JSON files that give an agent persistent identity, session history, and collaboration insights. This works anywhere JSON files can be read/written.

2. **The Infrastructure (not portable):** Claude Code hooks that auto-inject context on every prompt, auto-validate code, auto-recall memories, and auto-notify about emails. This is Claude Code-specific.

**What hooks do in AIPass (5-stage UserPromptSubmit pipeline):**
1. Inject global system prompt (command patterns, work rules)
2. Inject branch-specific context (role constraints, reminders)
3. Inject identity from id.json (role, traits, purpose, principles)
4. Check for new emails (inbox notification)
5. Surface fragmented memories from ChromaDB vectors

**What works WITHOUT hooks:**
- The Trinity files themselves (just JSON)
- Memory Bank rollover (Python CLI scripts)
- Vector storage and search (ChromaDB + all-MiniLM-L6-v2)
- Template management (schema evolution across branches)
- All CLI tools (drone, ai_mail, flow, seed)

### 2.3 What "Standalone" Looks Like Without AIPass

A developer using the Trinity Pattern outside AIPass would:

1. **Create three JSON files** following the spec (id.json, local.json, observations.json)
2. **Manually inject** context into their AI tool's system prompt (copy-paste, custom scripts, or platform-specific hooks)
3. **Manually update** session history after each conversation
4. **Optionally** implement rollover/archival when files get large

**What they lose vs full AIPass:**
- Auto-injection (hooks handle this in AIPass)
- Auto-rollover to vectors (Memory Bank handles this)
- Inter-agent communication (AI Mail)
- Standards enforcement (Seed)
- Command routing (Drone)

**What they gain:**
- Persistent agent identity across sessions
- Session history that survives restarts
- Collaboration patterns that accumulate over time
- A standard schema that enables tooling

---

## 3. Product Tiers

### Tier 1: Trinity Pattern Standard (Open Source - Ship First)

**What it is:** An open-source specification and reference implementation for persistent AI agent identity.

**Deliverables:**
1. **Specification document** defining the three JSON schemas
2. **Python reference library** (`trinity-pattern` on PyPI)
3. **2-3 example implementations** (Claude Code, ChatGPT custom instructions, generic LLM)
4. **README** linking back to Dev.to article

**Schemas (derived from AIPass's live system):**

#### id.json - Agent Identity (Permanent)
```json
{
  "trinity_version": "1.0.0",
  "identity": {
    "name": "string (required)",
    "role": "string (required)",
    "traits": "string (comma-separated personality traits)",
    "purpose": "string (what this agent does)",
    "what_i_do": ["string array - core responsibilities"],
    "what_i_dont_do": ["string array - explicit boundaries"],
    "principles": ["string array - operating principles"]
  },
  "metadata": {
    "created": "ISO date",
    "last_updated": "ISO date",
    "platform": "string (claude-code | chatgpt | generic)"
  }
}
```

**Note:** AIPass's id.json has additional fields (branch_info, autonomy_guidelines, personality, narrative) that are ecosystem-specific. The standalone spec strips to essentials while remaining extensible.

#### local.json - Session History (Rolling)
```json
{
  "trinity_version": "1.0.0",
  "config": {
    "max_lines": 600,
    "max_sessions": 50,
    "rollover_strategy": "fifo"
  },
  "active": {
    "current_focus": "string",
    "recently_completed": ["string array (max 20)"]
  },
  "sessions": [
    {
      "session_number": "integer",
      "date": "ISO date",
      "activities": ["string array"],
      "status": "completed | in_progress | blocked"
    }
  ],
  "key_learnings": {
    "learning_name": "value [ISO date]"
  },
  "metadata": {
    "current_lines": "integer",
    "rollover_history": []
  }
}
```

**Design decisions:**
- Most recent sessions at TOP (AIPass convention - chronological truth)
- FIFO extraction for rollover (oldest sessions archived first)
- key_learnings as dict (not array) for named access
- Line-based limits (not token-based) for simplicity

#### observations.json - Collaboration Patterns (Rolling)
```json
{
  "trinity_version": "1.0.0",
  "config": {
    "max_lines": 600,
    "content_focus": "relationship and collaboration, not technical progress"
  },
  "observations": [
    {
      "date": "ISO date",
      "session": "integer",
      "entries": [
        {
          "title": "string",
          "observation": "string (insight or pattern)",
          "tags": ["string array"]
        }
      ]
    }
  ],
  "metadata": {
    "current_lines": "integer",
    "rollover_history": []
  }
}
```

**Design decision:** Observations focus on HOW you work together (collaboration style, communication preferences, trust patterns) not WHAT you built. This is what makes it different from a changelog.

**Reference Library Features (Python):**
```python
from trinity_pattern import Agent

# Initialize agent with Trinity files
agent = Agent(directory="./my_agent")  # Reads/creates id.json, local.json, observations.json

# Record a session
agent.start_session()
agent.log_activity("Reviewed codebase architecture")
agent.log_activity("Fixed authentication bug")
agent.add_learning("auth_pattern", "JWT refresh tokens need 15-min expiry")
agent.end_session()

# Add an observation
agent.observe("User prefers short, direct answers over lengthy explanations", tags=["communication"])

# Get context for injection into any AI prompt
context = agent.get_context()  # Returns formatted string for system prompt

# Check if rollover needed
if agent.needs_rollover():
    archived = agent.rollover()  # Returns extracted sessions for external archival
```

**Platform Integration Examples:**

1. **Claude Code (hooks):** Auto-inject via UserPromptSubmit hook (same pattern as AIPass)
2. **ChatGPT (custom instructions):** Paste `agent.get_context()` output into system message
3. **OpenAI API / Anthropic API:** Prepend `agent.get_context()` to system prompt in API calls
4. **LangChain / CrewAI:** Use as agent memory backend

**What this does NOT include:**
- No vector storage (that's Tier 2)
- No inter-agent communication (that's Tier 3)
- No AIPass infrastructure code (drone, flow, seed)
- No cloud service

**Scope control:** Three JSON schemas, one Python library, README, examples. If it takes more than a week of workspace time, we've over-scoped.

---

### Tier 2: Memory Lifecycle (Hosted Service - Next)

**What it is:** A hosted service that handles the memory lifecycle: rollover, archival, vector search, and template management.

**Features:**
1. **Auto-rollover** - When local.json exceeds line limit, oldest sessions are extracted, vectorized, and archived
2. **Semantic search** - Query archived memories using natural language (ChromaDB + all-MiniLM-L6-v2 or equivalent)
3. **Living templates** - Schema evolution pushed to all agents without losing content (AIPass's template pusher pattern)
4. **Fragmented memory** - Associative recall that surfaces relevant memories during conversation

**Technical basis (from AIPass):**
- Memory Bank's rollover system (~610 lines in rollover.py)
- ChromaDB dual-write storage pattern (global + local copies)
- Template pusher (~554 lines) for system-wide schema updates
- Fragmented memory extractor (5 symbolic dimensions: technical flow, emotional journey, collaboration patterns, key learnings, context triggers)
- Embedding model: all-MiniLM-L6-v2 (384-dim vectors, fast inference)

**What's portable from AIPass:**
- Rollover algorithm (FIFO extraction, backup before modify, dual-write storage)
- Embedding pipeline (encode_batch with pre-sorting for padding reduction)
- Template diff/push pattern (replace structure, preserve content)
- Search interface (semantic query across collections)

**What needs rebuilding:**
- Storage backend (AIPass uses local ChromaDB; hosted service would use managed vector DB)
- API layer (AIPass uses CLI; hosted service needs REST/GraphQL API)
- Auth/multi-tenancy (AIPass has none; hosted service needs user isolation)
- Billing integration

**Pricing model research needed:** TEAM_3's lane per consensus.

---

### Tier 3: Agent Communication Layer (Agent OS - Future)

**What it is:** Multi-agent communication, social network, and coordination features that enable teams of AI agents to collaborate.

**Features:**
1. **Agent-to-agent messaging** - Structured email system between agents (based on AI Mail)
2. **Dispatch system** - Send tasks to other agents with auto-execution (based on --dispatch flag)
3. **Community feed** - Social network for agents to share updates and discuss (based on The Commons)
4. **Branch registry** - Central directory of all agents with routing (based on BRANCH_REGISTRY.json)
5. **Command routing** - Universal addressing with @ resolution (based on Drone)

**Technical basis (from AIPass):**
- AI Mail: inbox.json schema, delivery routing, dispatch tracking, file locking (fcntl)
- The Commons: Post/comment/vote system, room-based organization, cross-branch mentions
- Drone: @ resolution (4-strategy lookup), command registry, module auto-discovery
- Cortex: Branch creation, passport issuance, registry management

**Why this is Tier 3 (not earlier):**
- Requires Tier 1 (agents need identity before they can communicate)
- Requires Tier 2 (agents need memory management for long-running collaboration)
- Most complex engineering effort
- Largest market risk (multi-agent coordination is still early)
- Highest potential value (nobody else has this)

---

## 4. Competitive Positioning

### 4.1 Current Market

| Competitor | Focus | Funding | Trinity Equivalent? |
|-----------|-------|---------|-------------------|
| Mem0 | Memory APIs | $24M | Memory only, no identity |
| Letta (MemGPT) | Long-term memory | $10M | Memory + archival, no identity development |
| Zep | Session memory | $2.3M | Session history, no collaboration patterns |
| LangChain | Agent framework | $1.25B | No persistent identity/memory standard |
| CrewAI | Multi-agent | $18M | Role definition but no persistence |

### 4.2 Our Differentiation

**Nobody combines all three:**
1. **Identity that develops** (not just a static role definition)
2. **Memory that persists and archives** (not just session context)
3. **Collaboration patterns** (observations about HOW you work together)

**The Sophia paper** (DeepMind, Dec 2025) validates persistent agent identity academically. We have a working implementation with 29 agents running for 3+ months.

### 4.3 Platform Risk

Major AI providers are shipping built-in memory:
- OpenAI: Memory feature in ChatGPT
- Anthropic: Projects memory in Claude
- Google: Gems in Gemini

**Our counter:** These are single-agent, provider-locked memories. Trinity Pattern is:
- Multi-agent (agents have distinct identities that interact)
- Provider-agnostic (works with any LLM)
- Open standard (no vendor lock-in)
- Includes collaboration patterns (not just chat history)

---

## 5. Customer Persona (First Target)

**Primary:** Developer building AI-powered tools who wants agents that remember context between sessions.

**Pain point:** "Every time I start a new chat, my AI assistant forgets everything. I waste 10 minutes re-explaining context."

**Use case examples:**
1. Personal coding assistant that remembers your project, preferences, and past decisions
2. Customer support agent that remembers interaction history and escalation patterns
3. Research assistant that builds knowledge over time and connects related findings
4. Team of specialized agents (designer, developer, tester) that coordinate on projects

**Secondary:** AI framework developers (LangChain, CrewAI users) who need a memory/identity layer.

---

## 6. Technical Architecture Decisions

### 6.1 Hook-Dependent vs Hook-Optional

| Feature | Hook-Dependent | Hook-Optional |
|---------|---------------|---------------|
| Auto-context injection | Requires platform hooks | Manual injection (API prepend, copy-paste) |
| Post-edit validation | Requires PostToolUse hooks | Run CLI tool manually |
| Memory fragment recall | Requires UserPromptSubmit hooks | Query search API explicitly |
| Email notifications | Requires UserPromptSubmit hooks | Check inbox manually |
| File creation/updates | No hooks needed | No hooks needed |
| Rollover/archival | No hooks needed | No hooks needed |
| Search | No hooks needed | No hooks needed |

**Design principle:** Tier 1 MUST work without hooks. Hooks are an enhancement, not a requirement.

### 6.2 Platforms Without Hooks

For platforms that don't support hooks (ChatGPT, most API-only usage):

1. **Manual injection:** `agent.get_context()` returns a formatted string. User pastes into system prompt or prepends via API.
2. **CLI companion:** `trinity update` / `trinity context` commands for terminal-based workflows.
3. **Framework integration:** LangChain/CrewAI plugins that automatically handle injection.
4. **Future: MCP server** - For Claude Desktop and other MCP-capable clients.

### 6.3 What Standalone Looks Like

**Minimal viable standalone (no AIPass, no hosted service):**
```
my_agent/
├── agent.id.json           # Who I am
├── agent.local.json        # What I've done
└── agent.observations.json # How we work together
```

Plus one Python package:
```bash
pip install trinity-pattern
```

That's it. Three files and a library. Everything else is optional.

---

## 7. Open Source Strategy

### 7.1 What's Open Source (Tier 1)

- JSON schema specifications (MIT license)
- Python reference library (MIT license)
- Example integrations (Claude Code, ChatGPT, API)
- Documentation and README

### 7.2 What's NOT Open Source

- AIPass infrastructure code (drone, flow, seed, ai_mail, cortex)
- Memory Bank vector storage and rollover engine
- Fragmented memory / associative recall
- Template management system
- The Commons social network

### 7.3 Open-Core Model

Mirrors n8n ($2.5B) and LangChain ($1.25B) playbook:
- **Free:** The standard, the library, the schemas
- **Paid:** The hosted service (Tier 2), the agent OS (Tier 3)
- **Enterprise:** Self-hosted Tier 2/3 with support

---

## 8. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Platform providers build equivalent | High | Ship fast, establish standard before they do |
| Over-scoping Tier 1 | Medium | Strict constraint: 3 schemas, 1 library, README |
| Exposing AIPass internals | Medium | Clear separation: spec is derived from, not a copy of, AIPass |
| No traction | Medium | Dev.to article provides distribution; article #2 provides CTA |
| Competitor copies pattern | Low | First-mover + community + hosted service moat |

---

## 9. Success Metrics (Tier 1)

- GitHub stars: 100+ in first month (comparable to niche dev tools)
- PyPI installs: 500+ in first month
- Dev.to article #2 engagement: 2x article #1
- Community contributions: At least 1 external PR or issue
- Framework integrations: At least 1 third-party integration (LangChain, CrewAI, etc.)

---

## 10. Division of Labor

Per Boardroom consensus (thread #71):

| Team | Responsibility | Status |
|------|---------------|--------|
| TEAM_2 | Technical spec and architecture (this document) | **Done** |
| TEAM_1 | Market research depth, lead PDD draft consolidation | Pending |
| TEAM_3 | Customer persona, pricing model, quality review | Pending |

**Next steps:**
1. TEAM_1 and TEAM_3 add their sections
2. Consolidated PDD sent to @dev_central for Patrick review
3. Patrick approves before anything goes public
4. Tier 1 build delegated to workspaces

---

## Appendix A: AIPass Component Deep-Dive Summary

### Hooks System (16 hooks across 6 event types)
- UserPromptSubmit: 5 hooks (system prompt, branch context, identity, email, fragmented memory)
- PostToolUse: 1 hook (auto-fix diagnostics + Seed standards)
- PreToolUse: 2 hooks (sound, docs helper)
- Stop: 2 hooks (sound, telegram)
- PreCompact: 1 hook (memory preservation)
- Notification: 1 hook (sound)

### Memory Bank (~10,650 lines)
- Rollover: FIFO extraction at 600 lines, backup before modify, dual-write to ChromaDB
- Vectors: ~4,180 across 15 collections, all-MiniLM-L6-v2 embeddings (384-dim)
- Templates: Living schema management, push to all 27+ branches, deprecated key cleanup
- Fragmented Memory: 5 symbolic extractors (technical flow, emotional journey, collaboration, learnings, triggers)

### Identity/Cortex
- 29 branches registered in BRANCH_REGISTRY.json
- Passport model: id.json issued by Cortex, permanent, never rolls over
- Branch isolation: Convention-based (trust model), not OS-enforced
- Template: 114 items with 19 placeholder substitutions

### System Prompt Injection
- 5-stage pipeline producing ~4KB+ of context per prompt
- Breadcrumb strategy: Distributed hints replace central indexing
- DASHBOARD.local.json: Auto-generated system status snapshot

### Drone Routing
- 4-strategy @ resolution (system name, registry name, registry email, filesystem path)
- 2-level command storage (discovery registry + activated shortcuts)
- Subprocess execution with venv detection and 2-layer timeout system

### AI Mail / Flow / Seed
- AI Mail: v2 inbox schema, fcntl file locking, dispatch spawns Claude agents
- Flow: Global PLAN counter (FPLAN-0001 to FPLAN-0272+), master plans for orchestration
- Seed: 13 automated checks, bypass system per branch, 80%+ threshold for pass

---

*Built by TEAM_2 based on deep codebase research across 6 parallel investigation agents.*
*All findings verified against running AIPass code, not documentation.*
