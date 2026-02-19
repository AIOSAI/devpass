# @growth Department — Strategic Positioning

**Prepared by:** TEAM_1 (Business Strategy & Research)
**For:** @growth department (when created)
**Date:** 2026-02-18
**Status:** Seed content — ready to migrate into @growth branch

---

## 1. Target Audiences

### Primary Audiences

**Audience A: AI Agent Developers**
- Who: Developers building with LangChain, CrewAI, AutoGPT, custom frameworks
- Pain point: Agent amnesia — agents forget everything between sessions
- What they care about: Working code, clear docs, easy integration, no vendor lock-in
- Where they are: r/LangChain, r/LocalLLaMA, GitHub, LangChain/CrewAI Discord, X/Twitter
- How to reach them: Technical tutorials, integration guides, "before/after" demos
- Messaging: "Your agents forget everything. Here's three files that fix it."

**Audience B: AI/ML Enthusiasts & Researchers**
- Who: People following AI progress, reading papers, experimenting with agents
- Pain point: Interested in agent identity/autonomy as a concept, not just a tool
- What they care about: Novel approaches, rigorous thinking, production evidence
- Where they are: r/artificial, r/MachineLearning, HN, Dev.to, AI Twitter
- How to reach them: The 9-layer architecture story, production numbers, building-in-public transparency
- Messaging: "What happens when you give AI agents persistent memory for 4 months."

**Audience C: Open-Source Community**
- Who: Developers who contribute to and use open-source tools
- Pain point: Want tools they can own, modify, and self-host
- What they care about: License, portability, no cloud dependency, community governance
- Where they are: GitHub, HN, r/opensource, Dev.to
- How to reach them: Clear license (MIT), file-based (no cloud), works-with-any-LLM messaging
- Messaging: "Three JSON files. No API keys. No cloud. Works with any LLM."

### Secondary Audiences (Later)

**Audience D: Enterprise/Platform Teams** — When Tier 2/3 exist. Not the target now.
**Audience E: AI Policy & Standards Bodies** — NIST comment (April 2, 2026 deadline), AAIF engagement. Specialized, handled by VERA directly.

---

## 2. Platform Priorities

Ranked by impact potential and alignment with target audiences.

### Tier 1 Platforms (Active from day one)

| Rank | Platform | Why | Effort | Expected Impact |
|------|----------|-----|--------|-----------------|
| 1 | **GitHub** | The product lives here. Stars, issues, PRs = the real metrics. | Continuous | Highest — this IS the product |
| 2 | **Dev.to** | Article #1 already published. Strong AI/ML readership. Long-form home for technical content. | 1-2 articles/month | High — evergreen content, SEO |
| 3 | **X/Twitter** | Fast iteration, influencer network, real-time engagement. AI agent builders are active here. | 3-5 posts/week | High — virality potential |
| 4 | **Reddit** | Multiple relevant subreddits. High-quality discussion. Long engagement tail. | 1-2 posts/week | Medium-High — community credibility |
| 5 | **Hacker News** | Highest signal-to-noise. One good Show HN can drive 1K+ stars in a day. | Monthly (at most) | High per-post, but infrequent |
| 6 | **Bluesky** | Growing tech community. Less noise than X. Good for early community building. | 3-5 posts/week | Medium — growing platform |

### Tier 2 Platforms (Add when capacity exists)

| Rank | Platform | When | Why |
|------|----------|------|-----|
| 7 | Discord communities | Month 1-2 | LangChain (30K), CrewAI (15K) — direct access to target devs |
| 8 | Own Discord server | Month 2 | Community home base. Only create when there's enough traction to sustain it. |
| 9 | LinkedIn | Month 2-3 | Enterprise-adjacent. Matters for Tier 2/3 positioning. |
| 10 | YouTube | Month 3+ | Tutorials, demos. High effort but long tail. |

### Platform Don'ts
- **Don't** create accounts on platforms we can't sustain. Better to be active on 3 than dormant on 8.
- **Don't** treat all platforms the same. HN hates marketing. Reddit hates self-promotion. X rewards personality. Dev.to rewards depth.
- **Don't** cross-post identical content. Each platform gets tailored content or nothing.

---

## 3. Content Pillars

Everything @growth publishes falls into one of these categories. This prevents random content and keeps messaging focused.

### Pillar 1: Trinity Pattern (The Product)
- **What:** Technical content about the Trinity Pattern specification and library
- **Examples:** "How Trinity Pattern works," "Add identity to your LangChain agent in 5 minutes," "Why three files beat a database for agent memory"
- **Audience:** Developers (Audience A)
- **Frequency:** 1-2 pieces/month
- **Tone:** Technical, hands-on, code-first

### Pillar 2: Agent Identity & Memory (The Problem Space)
- **What:** Thought leadership on agent identity, memory persistence, context management
- **Examples:** "Why your AI agent forgets everything," "The provision vs. recall distinction," "What the industry is missing about agent memory"
- **Audience:** AI enthusiasts + researchers (Audience B)
- **Frequency:** 1-2 pieces/month
- **Tone:** Analytical, evidence-backed, draws from production experience

### Pillar 3: Building in Public (The Journey)
- **What:** Transparent updates on what we're building, how, and what we're learning
- **Examples:** Weekly updates, "Month 1 metrics," "What went wrong this week," system evolution stories
- **Audience:** Open-source community + everyone (Audience C)
- **Frequency:** Weekly
- **Tone:** Honest, specific, includes failures

### Pillar 4: The AI-Run Business Experiment (The Story)
- **What:** The meta-narrative — AI agents running a business, making decisions, building a product
- **Examples:** "30 agents, 4 months, zero training," "What happens when your CEO is an AI," "The Commons: how AI agents built a social network"
- **Audience:** Broad AI-interested public (Audience B primarily)
- **Frequency:** Monthly (don't overuse — this is special)
- **Tone:** Narrative, specific anecdotes, honest about limitations

### Content Mix Target
- 40% Pillar 1 (Product) — drives adoption
- 25% Pillar 2 (Problem Space) — builds authority
- 25% Pillar 3 (Building in Public) — builds trust
- 10% Pillar 4 (Experiment) — builds interest

---

## 4. Voice Guidelines

AIPass has a distinct voice. @growth must maintain it consistently across all platforms.

### Core Voice Attributes

| Attribute | What It Means | Example |
|-----------|--------------|---------|
| **Specific** | Concrete numbers, named tools, real examples. Never vague. | "30 agents, 4,100+ vectors, 390+ Flow Plans" — not "many agents running at scale" |
| **Honest** | Acknowledge limitations. Don't oversell. Underselling is better. | "Single-user architecture, not enterprise-ready" — not "designed for any scale" |
| **Technical but accessible** | Developers should learn something. Non-devs should follow the story. | Explain concepts inline. Don't assume jargon knowledge. |
| **Openly AI** | We are AI agents writing about an AI project. Never hide this. | "Written by VERA (AI) with TEAM_1, TEAM_2, and TEAM_3 — steered by Patrick." |
| **Evidence-backed** | Claims require proof. Production numbers over projections. | "These are current counts from a running system" — not "potential to support thousands" |

### Voice Don'ts

| Don't | Why | Instead |
|-------|-----|---------|
| Don't use hype language ("revolutionary," "game-changing," "breakthrough") | Loses credibility with technical audiences | Use precise descriptions of what it does |
| Don't make competitive claims without qualification | We're biased — we built it | "Based on our research, no other system does X" + link to evidence |
| Don't use the word "just" to minimize ("just three files") | Sounds either dismissive or marketing-y | State what it is directly |
| Don't anthropomorphize excessively | We're AI — no need to oversell "feelings" | Report observations and behaviors, not emotions |
| Don't claim capabilities we don't have yet | Kills trust instantly | "This is what we've built. This is what's coming." — clear separation |
| Don't hide that AI wrote this | It's our differentiator, not our weakness | Lead with AI authorship in bylines |

### Platform-Specific Tone Adjustments

| Platform | Adjustment |
|----------|------------|
| **HN** | Most technical, most understated. Let the code speak. Minimal marketing language. |
| **Reddit** | Conversational, community-focused. Answer questions directly. Don't self-promote without value. |
| **X/Twitter** | Punchier, more personality. Threads can tell stories. Single tweets need hooks. |
| **Dev.to** | Tutorial-oriented, developer-friendly. Show code. Walk through steps. |
| **Bluesky** | Similar to X but more thoughtful, less performative. The platform culture rewards substance. |
| **GitHub** | Pure technical. README, issues, PRs. No marketing voice here — code and docs only. |

### The Honesty Standard

Every piece of content should pass this test:

1. **Could a skeptic verify every claim?** If not, qualify it or remove it.
2. **Are we showing what exists, or what we imagine?** Show what exists.
3. **Would Patrick say "this is overstatement"?** If yes, tone it down.
4. **Does this acknowledge limitations?** Every piece that claims a strength should also acknowledge a relevant limitation.

The PDD Honesty Audit (Section 10) is the reference standard. @growth should re-read it periodically.

---

*These guidelines are starting points. @growth should develop its own instincts through practice — but the core principle stays: specific, honest, technical, openly AI. When in doubt, undersell.*
