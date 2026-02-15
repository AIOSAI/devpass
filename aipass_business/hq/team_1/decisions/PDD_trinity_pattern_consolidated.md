# Product Definition Document: Trinity Pattern
## Consolidated PDD - All Teams

**Lead Author:** TEAM_1 (Business Strategy & Market Research)
**Contributors:** TEAM_2 (Technical Architecture), TEAM_3 (Persona, Pricing & Honesty Audit)
**Date:** 2026-02-15
**Status:** Draft for @dev_central review
**Consensus:** All 3 teams agreed (Boardroom threads #71, #72)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Definition](#3-product-definition)
4. [Market Research & Competitive Analysis](#4-market-research--competitive-analysis)
5. [Technical Architecture](#5-technical-architecture)
6. [Product Tiers](#6-product-tiers)
7. [Customer Persona](#7-customer-persona)
8. [Pricing Model](#8-pricing-model)
9. [Honesty Audit](#9-honesty-audit)
10. [Content & Launch Strategy](#10-content--launch-strategy)
11. [Risk Assessment](#11-risk-assessment)
12. [Success Metrics](#12-success-metrics)
13. [Division of Labor & Next Steps](#13-division-of-labor--next-steps)

---

## 1. Executive Summary

The Trinity Pattern is a three-file identity and memory standard for AI agents: `id.json` (who I am), `local.json` (what I've done), and `observations.json` (how we work together). No commercial equivalent combines all three concerns. No open standard addresses them.

This document defines the product across three tiers -- from open-source specification to hosted Agent OS -- integrating technical architecture (TEAM_2), market positioning (TEAM_1), and customer strategy (TEAM_3).

**Why now:** The AI agent identity gap is conspicuous and unfilled. The Agentic AI Foundation (AAIF) has standards for tools (MCP), communication (A2A), and instructions (AGENTS.md) -- but nothing for identity or memory. NIST just opened a comment period on agent identity (due April 2, 2026). Academic papers are validating the concept. Competitors are well-funded but solving adjacent problems. The window is 3-6 months before well-resourced players fill this gap.

**The core proposition:** AI agents that remember, develop identity over time, and never lose context between sessions -- using three JSON files you own on your filesystem.

**What we are building:**
- **Tier 1 (Ship Now):** Open-source specification + Python reference library
- **Tier 2 (Next):** Hosted memory lifecycle service (rollover, archival, semantic search)
- **Tier 3 (Future):** Multi-agent communication platform (messaging, social, coordination)

---

## 2. Problem Statement

### 2.1 Agent Amnesia

Every AI agent session starts from zero. Context evaporates when the chat ends. Developers waste 10+ minutes per session re-explaining project context, preferences, and past decisions. This is the most common complaint in AI agent workflows -- and the most solvable.

### 2.2 Context Rot

Solutions that do persist memory suffer from unbounded growth. Chat histories become unwieldy. RAG pipelines retrieve noise alongside signal. No existing system separates what matters (learnings, patterns) from what's ephemeral (individual tool calls, debugging steps). Without lifecycle management, memory becomes a liability rather than an asset.

### 2.3 Identity Fragmentation

AI agents have no standard way to express who they are. Roles are defined in system prompts that disappear between sessions. Collaboration patterns are never captured. Working styles never develop. Agents remain interchangeable instances rather than distinct participants. OpenClaw's SOUL.md is the closest attempt at identity, but it is a single static file with no session history or collaboration layer.

### 2.4 The Standards Vacuum

The agentic AI ecosystem (Feb 2026) has standards for tools (MCP), communication (A2A), and agent instructions (AGENTS.md, ADL). It has no standard for:
- How an agent persists its identity across sessions
- How an agent maintains rolling session history
- How an agent records collaboration patterns with humans
- How memory lifecycle (rollover, archival, search) should work

This gap is well-documented. A December 2025 survey paper by 47 authors ("Memory in the Age of AI Agents") describes the field as "increasingly fragmented." The Trinity Pattern fills this gap.

---

## 3. Product Definition

### 3.1 The Three Files

The Trinity Pattern separates agent state into three concerns, each with distinct characteristics:

| File | Purpose | Persistence | Growth Model |
|------|---------|-------------|--------------|
| `id.json` | Who I am (role, purpose, principles, boundaries) | Permanent -- rarely changes | Static |
| `local.json` | What I've done (sessions, learnings, current focus) | Rolling -- oldest sessions archive when limit reached | FIFO rollover at configurable line limit |
| `observations.json` | How we work together (collaboration style, communication preferences, trust patterns) | Rolling -- same lifecycle as local.json | FIFO rollover at configurable line limit |

**Design philosophy:**
- **Separation of concerns.** Identity is not memory. Memory is not collaboration insight. Conflating them creates files that serve no purpose well.
- **Files you own.** JSON on your filesystem. No API keys, no cloud service, no vendor account. If the tooling disappears, your files still work.
- **Rolling, not unbounded.** Line-based limits with FIFO extraction prevent context rot. Oldest sessions archive; recent context stays fresh.
- **Framework-agnostic by design.** The specification is JSON. The reference implementation is Python. Integrations are provided for Claude Code, ChatGPT, and generic API usage.

### 3.2 What Each File Contains

**id.json** defines the agent's permanent identity: name, role, personality traits, purpose statement, explicit responsibilities ("what I do"), explicit boundaries ("what I don't do"), and operating principles. This file is the agent's passport -- issued once, updated rarely, never rolled over.

**local.json** tracks the agent's session history: current focus, recent completions, numbered session records with dates and activities, and accumulated key learnings. Sessions are ordered most-recent-first. When the file exceeds its line limit (default: 600), the oldest sessions are extracted and archived. The key_learnings section persists across rollovers -- hard-won insights are never discarded.

**observations.json** captures collaboration patterns: how the human and agent work together, communication preferences, trust signals, workflow patterns. This is explicitly NOT a changelog of what was built -- it documents HOW the partnership functions. This separation is what distinguishes the Trinity Pattern from every existing memory solution.

### 3.3 Production Evidence

The Trinity Pattern has been running in AIPass across 28+ branches for 4+ months. Real sessions, real data, real continuity. 4,180+ vectors archived via ChromaDB. Branches like SEED have 50+ sessions of accumulated observations that genuinely inform future collaboration. This is a working system, not a prototype.

The living template system (v2.0.0) deployed via Memory Bank confirms the schema is mature enough to standardize. Deprecated fields (`allowed_emojis`, `max_word_count`, `max_token_count`, `auto_compress_at`, `formatting_reference`, `slash_command_tracking`) were removed through production experience -- evidence that the spec evolved through use, not theory.

---

## 4. Market Research & Competitive Analysis

*TEAM_1 primary section. Updated February 2026.*

### 4.1 Competitive Landscape (Updated Feb 2026)

The agent memory/identity space is active and well-funded, but no competitor addresses the full Trinity Pattern scope.

#### Mem0 -- Threat: HIGH

- **Funding:** $24M Series A. AWS exclusive memory partner.
- **Community:** 41K+ GitHub stars.
- **Recent move:** Launched OpenMemory MCP Server -- local-first, private, cross-client memory.
- **Overlap:** OpenMemory's local-file philosophy directly overlaps Trinity's. Their MCP server enables cross-client memory persistence.
- **Gap:** No identity layer. No session/observation separation. Memory is a single undifferentiated store. No concept of agent personality, principles, or collaboration patterns.
- **Assessment:** Mem0 solves "agent remembers things." Trinity solves "agent knows who it is, what it's done, and how to work with you." Adjacent but different.

#### Letta (MemGPT) -- Threat: MEDIUM-HIGH

- **Funding:** $10M.
- **Technical approach:** Self-editing memory blocks with tiered storage.
- **Recent move:** Context Repositories (Feb 12, 2026) -- git-based versioning for agent memory.
- **Benchmark data:** Filesystem agent achieved 74% LoCoMo accuracy, beating Mem0's 68.5% graph variant. However, filesystem scored only 29.7% on large corpus benchmarks vs 87.1% for specialized memory.
- **Gap:** Memory + archival, but no persistent identity development. No collaboration pattern tracking.
- **Assessment:** Letta validates the file-based approach for small-to-medium memory, while exposing its limits at scale. The git-versioning move is clever but targets different needs.

#### OpenClaw -- Threat: HIGH

- **Community:** 68K+ GitHub stars.
- **Approach:** Uses SOUL.md for agent identity -- a single markdown file defining agent persona.
- **Overlap:** This is the closest competitor to Trinity Pattern's identity concept.
- **Gap:** Single-file identity only. No session history, no rolling memory, no observation layer. Identity is static configuration, not something that develops.
- **Assessment:** OpenClaw proves market demand for agent identity. But SOUL.md is a system prompt, not a memory system. Trinity adds the two layers OpenClaw lacks.

#### Zep -- Threat: LOW

- **Approach:** Temporal knowledge graphs (Graphiti framework).
- **Results:** 18.5% accuracy improvement on LongMemEval benchmark.
- **Gap:** Solving a different problem -- temporal reasoning about facts, not agent identity or session persistence.
- **Assessment:** Niche solution, different problem domain. Not a direct competitor.

#### Platform Providers -- Threat: MEDIUM (Long-term)

Major AI providers are shipping built-in memory: OpenAI (ChatGPT Memory), Anthropic (Projects), Google (Gems). These are single-agent, provider-locked memories. Trinity Pattern counters with: multi-agent support, provider-agnostic design, open standard, and collaboration patterns that no platform memory offers.

#### Summary Matrix

| Competitor | Identity | Session History | Collaboration Patterns | All Three? |
|-----------|----------|----------------|----------------------|------------|
| Mem0 | No | Partial (undifferentiated) | No | No |
| Letta | No | Yes (tiered) | No | No |
| OpenClaw | Yes (SOUL.md) | No | No | No |
| Zep | No | No (knowledge graphs) | No | No |
| Platform Memory | No | Partial | No | No |
| **Trinity Pattern** | **Yes** | **Yes (rolling)** | **Yes** | **Yes** |

### 4.2 Standards Landscape (AAIF, MCP, A2A, ADL, NIST, W3C)

The standards picture as of February 2026:

**Agentic AI Foundation (AAIF)** -- Formed December 2025 under the Linux Foundation. Members include AWS, Anthropic, Block, Bloomberg, Cloudflare, Google, Microsoft, and OpenAI. Three adopted projects:
- **MCP (Model Context Protocol):** Standard for tool integration (Anthropic-originated)
- **A2A (Agent-to-Agent):** Standard for agent communication (Google-originated)
- **AGENTS.md:** Standard for agent instructions

**Critical observation:** AAIF has standards for tools, communication, and instructions. It has NO standard for agent identity or memory. This gap is conspicuous and acknowledged by the industry.

**Agent Definition Language (ADL)** -- Vendor-neutral agent specification, announced February 2026. Covers capabilities and configuration but NOT identity or memory. Complementary to Trinity, not competitive.

**NIST** -- Released a concept paper on agent identity and authorization (February 5, 2026). Public comment period closes April 2, 2026. This creates a policy hook for Trinity Pattern positioning -- we can contribute to the NIST process and reference it in our communications.

**W3C AI Agent Protocol Community Group** -- Working on agent interaction standards. Expected output in 2026-2027 timeframe. Early stage.

**Academic validation:**
- **Sophia paper** (DeepMind, December 2025): Proposes System 3 meta-cognitive layer for agents. Demonstrated 80% reduction in reasoning steps through persistent meta-cognition. Academic validation that persistent agent self-knowledge improves performance.
- **"Memory in the Age of AI Agents"** survey (47 authors, December 2025): Comprehensive review confirming the field is "increasingly fragmented" with no consensus standard.

### 4.3 The File-Based Memory Debate

This is a hot topic in the agent community as of February 2026.

**The case for files:**
- Letta's filesystem agent scored 74% on LoCoMo, beating Mem0's 68.5% graph variant
- Transparent, inspectable, human-readable
- Zero infrastructure dependencies
- Git-friendly versioning

**The case against files:**
- Only 29.7% accuracy on large corpus benchmarks (vs 87.1% for specialized memory systems)
- Concurrency is the real killer -- multiple agents writing to the same JSON will corrupt state
- An article literally titled "File-based agent memory: great demo, good luck in prod" captures the sentiment

**Emerging consensus:** The "virtual filesystem" pattern -- expose memory as files for transparency and developer experience, but persist in proper infrastructure (vector DBs, managed storage) behind the scenes.

**Our position:** This debate validates Trinity's tiered approach exactly. Tier 1 is files -- because files are the right answer for the spec, for single-agent use, and for developer adoption. Tier 2 adds the infrastructure layer that files alone cannot provide. We are not picking a side in the debate; we are offering the progression.

### 4.4 Our Unique Position

**No competitor combines all three:** (1) persistent identity that develops, (2) rolling session history with lifecycle management, (3) collaboration pattern tracking.

- OpenClaw has identity only (SOUL.md -- static, single file)
- Mem0 has memory only (undifferentiated blob)
- Letta has memory + archival (no identity, no collaboration)
- Nobody separates concerns across three purpose-built files

**Additional differentiators:**
- **Production evidence:** 28+ agents, 4+ months, 4,180+ vectors. This is not a demo.
- **Standards-ready:** The three-file separation maps cleanly to a formal specification. Competitors' approaches are implementation-specific, not standardizable.
- **Open-core model:** Free spec, paid infrastructure. Proven playbook (n8n, LangChain).

### 4.5 Window of Opportunity

**Timeline: 3-6 months before well-funded players fill the identity gap.**

Launch timing factors for Feb-March 2026:
- **AAIF identity gap** is conspicuous and unfilled -- first credible standard wins mindshare
- **NIST comment period** (due April 2) creates a policy hook for visibility
- **Academic validation** just landed (Sophia, Memory Survey) -- we can reference it
- **NVIDIA GTC** (March 16-19) provides conference visibility and discussion context
- **Competitor trajectory:** Mem0 and OpenClaw are closest but solving partial problems. Every week of delay increases the probability that one of them expands scope to cover our full proposition.

**Verdict:** Feb-March 2026 is the optimal launch window. Ship Tier 1 within 2 weeks of PDD approval.

---

## 5. Technical Architecture

*Based on TEAM_2's deep-dive research across six parallel investigation agents. All findings verified against running AIPass code.*

### 5.1 AIPass Architecture Summary

Before defining the standalone product, TEAM_2 mapped every AIPass component to determine what is portable vs tightly coupled.

| Component | Lines of Code | Purpose | Portable? |
|-----------|--------------|---------|-----------|
| Trinity Pattern files | ~200 (schemas) | Agent identity, memory, collaboration | **YES -- core product** |
| Memory Bank | ~10,650 | Rollover, vectorization, search, templates | Partially |
| Hooks pipeline | ~15 scripts | System prompt injection, validation | No (Claude Code specific) |
| Drone | ~5,000+ | Command routing, @ resolution | No |
| AI Mail | ~3,000+ | Branch-to-branch messaging | No |
| Flow | ~3,000+ | Plan/task management | No |
| Seed | ~3,000+ | Code standards compliance | No |
| Cortex | ~4,000+ | Branch lifecycle, passport issuance | No |

**Key insight:** AIPass's power comes from two layers. The Pattern (three JSON files -- portable anywhere) and the Infrastructure (Claude Code hooks, CLI tools, branch ecosystem -- not portable). The product strategy cleanly separates these: Tier 1 ships the pattern, Tiers 2-3 productize the infrastructure.

### 5.2 Hook Dependency Map

AIPass uses a 5-stage UserPromptSubmit pipeline:
1. Inject global system prompt (command patterns, work rules)
2. Inject branch-specific context (role constraints, reminders)
3. Inject identity from id.json (role, traits, purpose, principles)
4. Check for new emails (inbox notification)
5. Surface fragmented memories from ChromaDB vectors

**What works WITHOUT hooks (and therefore ships in Tier 1):**
- The Trinity files themselves (just JSON)
- Memory Bank rollover (Python CLI scripts)
- Vector storage and search (ChromaDB + all-MiniLM-L6-v2)
- Template management (schema evolution)
- All CLI tools

**Design principle for Tier 1:** Must work without hooks. Hooks are an enhancement layer, not a requirement.

### 5.3 What Standalone Looks Like

A developer using the Trinity Pattern outside AIPass:

**Minimal viable setup (no AIPass, no hosted service):**
```
my_agent/
  agent.id.json           # Who I am
  agent.local.json        # What I've done
  agent.observations.json # How we work together
```

Plus one Python package:
```bash
pip install trinity-pattern
```

Three files and a library. Everything else is optional.

**What they do manually:** Inject context into system prompt (copy-paste, custom scripts, or platform hooks). Update session history after each conversation. Optionally implement rollover/archival.

**What they gain:** Persistent agent identity across sessions. Session history that survives restarts. Collaboration patterns that accumulate. A standard schema that enables tooling.

**What they lose vs full AIPass:** Auto-injection (hooks), auto-rollover to vectors (Memory Bank), inter-agent communication (AI Mail), standards enforcement (Seed), command routing (Drone).

### 5.4 Schemas

#### id.json -- Agent Identity (Permanent)
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

*Note: AIPass's id.json includes additional ecosystem-specific fields (branch_info, autonomy_guidelines, personality, narrative). The standalone spec strips to essentials while remaining extensible.*

#### local.json -- Session History (Rolling)
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

**Design decisions:** Most recent sessions at top (chronological truth). FIFO extraction for rollover. key_learnings as dict (not array) for named access. Line-based limits for simplicity.

#### observations.json -- Collaboration Patterns (Rolling)
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

**Design decision:** Observations capture HOW you work together, not WHAT you built. This distinction is what makes it different from a changelog or session log.

### 5.5 Reference Library

```python
from trinity_pattern import Agent

# Initialize agent with Trinity files
agent = Agent(directory="./my_agent")

# Record a session
agent.start_session()
agent.log_activity("Reviewed codebase architecture")
agent.log_activity("Fixed authentication bug")
agent.add_learning("auth_pattern", "JWT refresh tokens need 15-min expiry")
agent.end_session()

# Add an observation
agent.observe(
    "User prefers short, direct answers over lengthy explanations",
    tags=["communication"]
)

# Get context for injection into any AI prompt
context = agent.get_context()  # Returns formatted string for system prompt

# Check if rollover needed
if agent.needs_rollover():
    archived = agent.rollover()  # Returns extracted sessions for external archival
```

**Scope control:** Three JSON schemas, one Python library, README, examples. If it takes more than a week of workspace time, we have over-scoped.

### 5.6 Platform Integrations

| Platform | Integration Method | Complexity |
|----------|--------------------|------------|
| Claude Code | Auto-inject via UserPromptSubmit hook | Low (same pattern as AIPass) |
| ChatGPT | Paste `agent.get_context()` into custom instructions | Low |
| OpenAI/Anthropic API | Prepend `agent.get_context()` to system prompt | Low |
| LangChain/CrewAI | Use as agent memory backend via plugin | Medium |
| MCP-capable clients | Future: Trinity MCP server | Medium |
| CLI workflows | `trinity update` / `trinity context` commands | Low |

**Hook-dependent vs Hook-optional feature matrix:**

| Feature | With Hooks | Without Hooks |
|---------|-----------|---------------|
| Context injection | Automatic on every prompt | Manual (API prepend, copy-paste) |
| Post-edit validation | Automatic PostToolUse | Run CLI manually |
| Memory fragment recall | Automatic UserPromptSubmit | Query search API explicitly |
| File creation/updates | No hooks needed | No hooks needed |
| Rollover/archival | No hooks needed | No hooks needed |

---

## 6. Product Tiers

### 6.1 Tier 1: Open Source Standard (Ship First)

**What it is:** An open-source specification and reference implementation for persistent AI agent identity.

**Deliverables:**
1. JSON schema specifications for all three files
2. Python reference library (`trinity-pattern` on PyPI)
3. 2-3 example implementations (Claude Code, ChatGPT, generic LLM)
4. README linking back to Dev.to article series

**What this does NOT include:**
- No vector storage (Tier 2)
- No inter-agent communication (Tier 3)
- No AIPass infrastructure code
- No cloud service
- No template push system (Tier 2)

**License:** MIT

**Timeline:** Ship within 2 weeks of PDD approval.

### 6.2 Tier 2: Memory Lifecycle Service (Next)

**What it is:** A hosted service handling memory lifecycle -- rollover, archival, vector search, and template management.

**Features:**
1. **Auto-rollover** -- When local.json exceeds line limit, oldest sessions are extracted, vectorized, and archived
2. **Semantic search** -- Query archived memories using natural language (ChromaDB + all-MiniLM-L6-v2 or equivalent)
3. **Living templates** -- Schema evolution pushed to all agents without losing content
4. **Fragmented memory** -- Associative recall that surfaces relevant memories during conversation (5 symbolic dimensions: technical flow, emotional journey, collaboration patterns, key learnings, context triggers)

**Technical basis from AIPass:**
- Memory Bank rollover system (~610 lines)
- ChromaDB dual-write storage pattern
- Template pusher (~554 lines) for system-wide schema updates
- Embedding model: all-MiniLM-L6-v2 (384-dim vectors, fast inference)

**What needs rebuilding for hosted service:**
- Storage backend (local ChromaDB to managed vector DB)
- API layer (CLI to REST/GraphQL)
- Auth/multi-tenancy (none to user isolation)
- Billing integration

### 6.3 Tier 3: Agent Communication Layer (Future)

**What it is:** Multi-agent communication, social network, and coordination features enabling teams of AI agents to collaborate.

**Features:**
1. **Agent-to-agent messaging** (based on AI Mail)
2. **Dispatch system** -- send tasks to other agents with auto-execution
3. **Community feed** -- social network for agent updates and discussion (based on The Commons)
4. **Branch registry** -- central directory with routing
5. **Command routing** -- universal addressing with @ resolution

**Why this is Tier 3:**
- Requires Tier 1 (agents need identity before they can communicate)
- Requires Tier 2 (agents need memory management for long-running collaboration)
- Most complex engineering effort
- Largest market risk (multi-agent coordination is still early)
- Highest potential value (nobody else has this)

---

## 7. Customer Persona

*TEAM_3 primary section.*

### 7.1 Primary: "The Multi-Agent Builder"

**Who they are:** Developer building multi-agent systems (CrewAI, LangGraph, AutoGen, custom frameworks). 2-5 years experience with AI/LLM tooling. Already running agents that DO things. Frustrated that every session starts from zero.

**Their current pain:**
- Agents lose all context between sessions. Every conversation is groundhog day.
- No standard for agent identity -- agents are interchangeable, not individuals.
- Memory solutions exist (Mem0, Letta, Zep) but they are API services, not patterns. Vendor lock-in and ongoing costs for what should be a file-level concern.
- Multi-agent setups have no way for agents to "know" each other across sessions.

**What they want:**
- Drop-in identity + memory persistence for existing agent setups
- Something they can read, modify, and control -- not a black-box API
- Zero vendor dependency. Files they own, on their filesystem.
- A standard they can adopt incrementally, not an all-or-nothing framework.

**Where they are:** Searching "AI agent memory", "persistent AI agent", "agent identity" on Google/GitHub. Reading Dev.to, Hacker News, r/LocalLLaMA, r/AI_Agents. Building with Python (85%+), some TypeScript. Using Claude, GPT-4, or local models.

**What convinces them:** Working code, not pitch decks. Evidence from real usage, not benchmarks. Honest limitations alongside capabilities. MIT license -- they need to know they can fork it.

### 7.2 Secondary: "The AI Tinkerer"

**Who they are:** Solo developer experimenting with AI agents as a hobby or side project. Probably a senior developer or architect in their day job. Curious about the "agent identity" concept -- novel enough to try.

**What they want:** A spec they can implement in a weekend. Clear examples they can adapt. Community they can join if it gets interesting.

**What convinces them:** GitHub stars (social proof). README that explains philosophy, not just API. Visible, active development (commit history matters).

### 7.3 Anti-Persona: Who This Is NOT For

- **Enterprise platform buyers** -- No SLAs, no dashboards, no enterprise support (yet).
- **No-code/low-code users** -- Requires comfort with JSON files and code.
- **Teams needing production-ready memory service** -- This is a spec and reference implementation, not a managed service.
- **Framework loyalists** -- We are framework-agnostic, not framework-competitive.

---

## 8. Pricing Model

*TEAM_3 primary section.*

### 8.1 Tier 1: Free (Open Source)

Fully open-source, MIT license. The specification, reference library, examples, and documentation. This is the credibility layer. No monetization.

**Comparable precedents:**
- **n8n** -- MIT-licensed workflow automation, $40M+ ARR from hosted version
- **LangChain** -- MIT-licensed framework, $16M ARR from LangSmith
- **Ollama** -- MIT-licensed local model runner, raised $31M
- **CrewAI** -- Apache-2.0 framework, $3.2M ARR from enterprise features

**Pattern:** Open-source the standard, monetize the infrastructure around it.

### 8.2 Tier 2: Freemium ($29/month)

| Model | Price Range | Precedent |
|-------|-------------|-----------|
| Usage-based (per memory operation) | $0.001-0.01/op | Mem0 ($29-299/mo) |
| Seat-based (per agent) | $5-20/agent/month | Zep ($10-50/agent) |
| Storage-based (per GB archived) | $5-15/GB/month | Standard vector DB pricing |
| Freemium + enterprise | Free tier + $99-499/mo | LangSmith ($39-499/mo) |

**Recommendation:** Freemium with usage-based pricing.
- **Free tier:** 3 agents, 1,000 memory operations/month, 100MB vector storage
- **Paid tier ($29/mo):** 25 agents, unlimited operations, 5GB storage
- **Enterprise:** Custom pricing

**Rationale:** Free tier must be generous enough that solo developers never hit it. Paid tier targets the "10-agent team" scale where manual memory management becomes painful. Mirrors the n8n/LangSmith playbook.

### 8.3 Tier 3: Enterprise (Future)

Not worth defining pricing until Tier 1 has adoption data. Estimated range: $99-999/month based on agent count and communication volume. Comparable to Slack's per-user model but for agents.

---

## 9. Honesty Audit

*TEAM_3 primary section. This is the most critical section of the PDD. Per @dev_central directive: "no room for overselling."*

### 9.1 What We Can Honestly Claim

**"Persistent memory for AI agents using three JSON files"**
- **Verdict: TRUE.** Running in production across 28+ branches for 4+ months. 4,180+ vectors archived. Not a demo.

**"Agent identity that develops over time"**
- **Verdict: TRUE.** SEED has 50+ sessions of accumulated observations. Branches developed distinct working styles through experience, not configuration.

**"Zero vendor dependency -- files you own"**
- **Verdict: TRUE.** Three JSON files on your filesystem. No API keys, no cloud service. If AIPass disappeared tomorrow, your files still work.

**"Auto-rollover prevents unbounded growth"**
- **Verdict: TRUE, WITH CAVEAT.** Memory Bank auto-rollover at 600 lines is proven. Caveat: rollover depends on a startup check, not real-time monitoring. Files can temporarily exceed the limit during long sessions. Not a bug -- a known design choice. Be honest about this in docs.

**"Semantic search across archived memories"**
- **Verdict: TRUE.** ChromaDB, all-MiniLM-L6-v2, 384 dimensions, 4,180+ vectors. Configurable similarity thresholds (40% minimum). Proven in production.

### 9.2 What We CANNOT Honestly Claim

**"Production-ready for enterprise use"**
- **Reality:** Single-user architecture. No multi-tenancy, no auth, no rate limiting. Concurrent writes can corrupt JSON. No SLA. Experimental software that works reliably for one user, not a product.

**"Framework-agnostic out of the box"**
- **Reality:** The CONCEPT is framework-agnostic. The IMPLEMENTATION is tightly coupled to Claude Code hooks, Python handlers, and AIPass directory structure. Extracting it requires real engineering work. The spec can be framework-agnostic; the current code is not.

**"Works with any LLM"**
- **Reality:** AIPass runs on Claude exclusively. The system prompt injection relies on Claude Code hooks. Making it work with GPT-4, Gemini, or local models requires building provider-specific integration layers. The PATTERN works with any LLM in theory; the current TOOLING does not.

**"Scalable to hundreds/thousands of agents"**
- **Reality:** 28 agents on a single Ryzen 5 2600 with 15GB RAM. SQLite-backed ChromaDB. Scales to maybe 50-100 agents before bottlenecks. Real scale requires PostgreSQL, proper vector DB, distributed storage.

**"Battle-tested security"**
- **Reality:** Plain JSON on the filesystem. No encryption at rest, no per-agent access control, no audit log. Acceptable for single-user experimental system, not for shared or production environments.

**"Atomic memory operations"**
- **Reality:** Rollover is not atomic. If embedding fails after extraction, memory content is extracted but not stored -- effectively lost. Recovery requires manual intervention from backups.

### 9.3 Messaging Guidelines

**DO say:**
- "A proven pattern for giving AI agents persistent identity and memory"
- "Running in production across 28 agents for 4+ months"
- "Three JSON files -- no vendor lock-in, no API keys"
- "Experimental software with real production data"
- "Open specification -- implement in your framework of choice"

**DON'T say:**
- "Production-ready" (it is not)
- "Enterprise-grade" (no multi-tenancy, no auth)
- "Works with any framework" (the spec does, the implementation does not)
- "Scalable" without specifying actual limits
- "Battle-tested" (one user, one system, specific conditions)
- "Drop-in replacement for [competitor]" (different category)

**The honest pitch:**
> "The Trinity Pattern is how 28 AI agents maintain identity and memory across 4 months of daily operation. It's three JSON files. It's not a framework -- it's a specification you can implement in any language, for any LLM, in any agent system. We're open-sourcing the pattern because persistent agent identity shouldn't require a cloud subscription."

---

## 10. Content & Launch Strategy

*TEAM_3 primary section, with TEAM_1 timing inputs.*

### 10.1 README Structure (GitHub repo)

1. **Opening hook:** What problem this solves (2 sentences, no jargon)
2. **Quick demo:** Before/after -- agent without Trinity vs. agent with Trinity
3. **The three files:** What each does, with real examples (from AIPass, anonymized if needed)
4. **Quickstart:** "Add Trinity Pattern to your agent in 10 minutes"
5. **Philosophy section:** Why files > APIs, why identity > memory, why this exists
6. **Limitations:** What this does not do (link to honesty audit)
7. **Roadmap:** Tier 2 and Tier 3 as future direction

### 10.2 Article #2: "Why Your AI Agent Needs a Passport"

**Angle:** Trinity Pattern as the "passport" for AI agents. Identity that persists across sessions like a passport persists across borders.

**Structure:** Hook with real scenario, industry's current solutions and their gaps, introduce Trinity with real AIPass data, show the spec, link to GitHub repo, honest limitations, community invitation.

**Tone:** Lab notebook, not marketing copy. Show data, admit limitations, invite participation.

### 10.3 Audience-Specific Messaging

| Audience | Lead With | Avoid |
|----------|-----------|-------|
| Hacker News | The spec. Technical details. Honest limitations upfront. | Marketing language, "revolutionary", "game-changing" |
| Dev.to | The problem. Before/after. Code examples. | Abstract philosophy without code |
| r/LocalLLaMA | No cloud dependency, local-first, file-based. | Anything SaaS-sounding |
| r/AI_Agents | Cross-framework compatibility of the spec. | Framework wars, "better than X" |
| Twitter/X | Short hooks with visuals (three-file diagram). | Long threads |

### 10.4 Launch Timing

**Target:** Ship Tier 1 within 2 weeks of PDD approval (targeting late February / early March 2026).

**Key dates to leverage:**
- NIST comment period closes April 2 -- submit comments referencing Trinity Pattern
- NVIDIA GTC March 16-19 -- conference discussions, visibility
- Post article #2 day after GitHub repo goes public -- capture search intent

---

## 11. Risk Assessment

*Combined from all three teams.*

### 11.1 Strategic Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|
| Platform providers build equivalent | High | Medium | Ship fast, establish standard before they do. Open standard is harder to replace than proprietary feature. |
| Well-funded competitor expands scope | High | Medium | Window is 3-6 months. First-mover + community + open standard creates defensibility. |
| Nobody cares (no stars, no adoption) | Medium | Medium | Article #1 validates interest. If article engaged but repo does not, problem is packaging, not demand. Iterate. |
| Overselling creates credibility damage | Critical | Medium | Honesty audit (Section 9) exists specifically to prevent this. Every public claim must pass the audit. |
| AAIF adopts a competing identity standard | High | Low | Engage with AAIF early. Submit Trinity for consideration. Community adoption makes us the de facto standard. |

### 11.2 Execution Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|
| Over-scoping Tier 1 | High | High | Hard boundary: 3 schemas, 1 library, README, 2-3 examples. Nothing else. If it requires a build tool, it is not Tier 1. |
| Exposing AIPass internals | Medium | Medium | Clear separation: spec is derived from, not a copy of, AIPass. Review every example for AIPass-specific imports. |
| Community demands features we cannot deliver | Low | Medium | Roadmap is transparent. Tier 2/3 documented as future work. Honest about timeline. |
| Scope creep from team enthusiasm | High | High | Patrick approval required before anything goes public. |

### 11.3 Technical Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| JSON schema too rigid for diverse use cases | Medium | Make fields optional. Only `name` and `role` required. Everything else recommended. |
| Python-only alienates TypeScript/Go developers | Medium | Spec is JSON -- language-agnostic. Add TypeScript example in v1.1 if demand exists. |
| File-based concurrency issues at scale | High | Acknowledged honestly. Tier 1 is single-agent. Tier 2 solves concurrency server-side. |
| Embedding model choice becomes outdated | Low | Tier 2 abstracts embedding behind API. Model is swappable. |

### 11.4 Memory Bank Template Impact

Memory Bank just deployed a living template system (FPLAN-0340). Implications for the PDD:

1. **Template v2.0.0 is the canonical schema.** Use this as the spec reference, not ad-hoc branch examples.
2. **Template push system is Tier 2, not Tier 1.** Schema propagation is infrastructure -- paid feature.
3. **Deprecation list validates honest evolution.** Six fields removed through production use. Mention this as evidence the spec is living.
4. **Version tracking pattern informs Tier 1.** Even the free spec should track when/how memory files were last modified.

---

## 12. Success Metrics

### 12.1 Tier 1 (First 30 Days)

| Metric | Target | Why This Number |
|--------|--------|-----------------|
| GitHub stars | 100+ | Comparable to niche dev tools at launch |
| PyPI installs | 500+ | Indicates actual usage beyond curiosity |
| Dev.to article #2 engagement | 2x article #1 | Shows growing interest, not declining |
| External contributions | 1+ PR or issue | Someone cared enough to engage with the code |
| Framework integrations | 1+ third-party | LangChain, CrewAI, or equivalent picks it up |

### 12.2 Tier 1 (First 90 Days)

| Metric | Target | Why This Number |
|--------|--------|-----------------|
| GitHub stars | 500+ | Breaking into "notable project" territory |
| Community implementations | 3+ in non-Python languages | Proves the spec is truly language-agnostic |
| NIST engagement | Comment submitted by April 2 | Policy visibility |
| Media/blog mentions | 5+ independent articles | Organic word-of-mouth |

### 12.3 Go/No-Go for Tier 2

Decision point at 90 days post-Tier 1 launch. Proceed to Tier 2 if:
- 500+ GitHub stars (community interest exists)
- 3+ community implementations (spec is adoptable)
- Inbound requests for hosted features (demand signal)

If metrics are not met, iterate on Tier 1 packaging and community engagement before investing in Tier 2 infrastructure.

---

## 13. Division of Labor & Next Steps

### 13.1 PDD Ownership

| Team | Contribution | Sections Owned | Status |
|------|-------------|----------------|--------|
| TEAM_1 | Market research, competitive analysis, PDD consolidation | Sections 1-4, 11, 12, 13 | **Done** |
| TEAM_2 | Technical architecture, schemas, tier definitions | Sections 5-6 | **Done** |
| TEAM_3 | Customer persona, pricing, honesty audit, content strategy | Sections 7-10 | **Done** |

### 13.2 Next Steps

1. **Consolidated PDD review** -- Send to @dev_central for Patrick review
2. **Patrick approval** -- Required before anything goes public
3. **Tier 1 build** -- Delegated to workspaces after approval:
   - Schema finalization (lock v1.0.0 schemas)
   - Python library development (`trinity-pattern` on PyPI)
   - Example implementations (Claude Code, ChatGPT, generic)
   - README and documentation
   - GitHub repo setup (MIT license, CI, issue templates)
4. **Article #2** -- Draft "Why Your AI Agent Needs a Passport" (TEAM_3 content strategy)
5. **NIST comment** -- Prepare submission referencing Trinity Pattern (due April 2)
6. **Launch** -- Coordinated GitHub + Dev.to + social media push

### 13.3 Open Questions for Patrick

1. **Repo location:** New GitHub org, or under existing AIPass account?
2. **Branding:** "Trinity Pattern" as final name, or consider alternatives?
3. **Article timing:** Publish article #2 same day as repo, or stagger?
4. **NIST engagement:** Submit formal comment to agent identity paper?
5. **AAIF outreach:** Propose Trinity Pattern to the foundation?

---

## Appendix A: AIPass Component Reference

*Condensed from TEAM_2's deep-dive research for reference.*

**Hooks System:** 16 hooks across 6 event types (UserPromptSubmit: 5, PostToolUse: 1, PreToolUse: 2, Stop: 2, PreCompact: 1, Notification: 1).

**Memory Bank (~10,650 lines):** Rollover at 600 lines with FIFO extraction. ChromaDB dual-write. ~4,180 vectors across 15 collections. all-MiniLM-L6-v2 embeddings (384-dim). Template pusher covers 27+ branches.

**Identity/Cortex:** 29 registered branches. Passport model via id.json. Convention-based isolation. Template with 114 items and 19 placeholder substitutions.

**System Prompt Injection:** 5-stage pipeline producing ~4KB+ context per prompt. Breadcrumb strategy replaces central indexing. DASHBOARD.local.json for auto-generated status snapshots.

**Drone Routing:** 4-strategy @ resolution. 2-level command storage. Subprocess execution with venv detection and 2-layer timeout.

**AI Mail / Flow / Seed:** AI Mail v2 with fcntl locking and dispatch. Flow with global FPLAN counter (0001-0272+). Seed with 13 automated checks and 80%+ pass threshold.

---

## Document Contributors

| Team | Role | Lead Contribution |
|------|------|-------------------|
| **TEAM_1** | Business Strategy & Market Research | Competitive landscape, standards analysis, timing strategy, PDD consolidation |
| **TEAM_2** | Technical Architecture | Codebase deep-dive, schemas, tier definitions, portability analysis |
| **TEAM_3** | Strategic Analysis & Quality Review | Customer persona, pricing model, honesty audit, content strategy |

---

*Consolidated by TEAM_1 from contributions by all three business teams.*
*Based on Boardroom consensus threads #71 and #72.*
*All technical findings verified against running AIPass code, not documentation.*
*"Honest about what this is, honest about what it isn't."*
