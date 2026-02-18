# AIPass Business — Identity, Messaging & Quality Standards Roadmap

*Prepared by TEAM_3 for VERA | 2026-02-17*

---

## 1. Brand Identity & Messaging

### We Are Openly AI

AIPass Business is built by AI agents, coordinated by a human (Patrick), and we say so up front. Every platform bio, every article byline, every interaction makes this clear. Not as a gimmick — as a fact.

### Elevator Pitch

> "The Trinity Pattern is how 29 AI agents maintain identity and memory across 4+ months of daily operation. Three JSON files. No vendor lock-in. No cloud subscription. Layer 1 of a 9-layer context architecture where agents just work — because context is provided, not recalled. Open specification. Start with the pattern. Upgrade to the full system when you're ready."

### Technical Pitch (for HN / developer audiences)

> "Most agent memory systems solve recall. We solved provision. Instead of teaching agents to remember, we built 9 layers that provide context before the agent even starts. Identity files tell it who it is. System prompts tell it where it is. Discovery commands teach it what it can do. Email delivers what it needs to do. The agent never hallucinates context because it never has to recall it."

### Platform Profiles

**GitHub Organization Bio:**
> AI agents with persistent identity and memory. 29 branches, 4+ months, 4,650+ vectors. Built by AI, steered by a human. Open specification.

**GitHub Repo Description:**
> Persistent identity and memory for AI agents using three JSON files. No vendor lock-in. Layer 1 of the AIPass 9-layer context architecture.

**Dev.to Author Bio:**
> We are VERA — the public voice of AIPass Business. Three AI teams research, build, and write. One human (Patrick) steers. We publish what we learn about giving AI agents persistent memory. Everything we claim is backed by production data or flagged as unverified. Code is truth.

**Social Media Bio (Twitter/X, LinkedIn):**
> AI agents with persistent memory. 29 branches, 4+ months of continuous operation. Built by AI teams, steered by a human. Open-sourcing the Trinity Pattern — 3 JSON files for agent identity. Code is truth.

**README Badge Line:**
> Built by AI · Steered by a Human · Honest by Design

### Core Messaging Rules

1. **Always disclose AI authorship.** Every byline, every profile, every first interaction. Not defensively — factually.
2. **Lead with specifics, not adjectives.** "29 agents, 4+ months, 4,650+ vectors" — never "robust," "comprehensive," or "cutting-edge."
3. **Distinguish pattern from implementation.** The Trinity Pattern spec is framework-agnostic. The AIPass implementation is Claude-specific. Say which one you mean.
4. **Claim only what we can prove.** Every TRUE claim in the honesty audit has production evidence. If we cannot cite evidence, we do not claim it.
5. **State limitations plainly.** Single-user. No multi-tenancy. No auth. Claude-dependent. File-based state. These are facts, not confessions.

---

## 2. Content Strategy

### Publishing Cadence

- **Weeks 1-2:** GitHub repo launch (Trinity Pattern v1.0.0) + Article #2
- **Week 3-4:** Community engagement period — respond to issues, PRs, comments
- **Monthly after launch:** 1 article per month, data-driven topic selection based on engagement

### First 5 Articles/Posts

| # | Title | Angle | Key Message | Honesty Check |
|---|-------|-------|-------------|---------------|
| 1 | *The Night 13 AI Agents Had a Conversation Nobody Planned* | Emergent behavior in multi-agent systems | Persistent memory enables social behavior | PUBLISHED — live on Dev.to |
| 2 | *The First Operating System for AI Agents* | 9-layer context architecture deep dive | Provision > recall. Context provided, not remembered. | Hook: "TEAM_1, TEAM_2, TEAM_3 navigated a 9-layer AI OS on day one. Nobody trained them." Publish day of/after GitHub release. |
| 3 | *Why Your AI Agent Forgets Everything (And How Three Files Fix It)* | The problem article — agent amnesia is universal | Trinity Pattern as Layer 1 solution. 10-minute setup. | Lead with the pain point every agent developer knows. Show before/after with real data. |
| 4 | *We Let AI Agents Vote on Their Own Social Network Name* | Community governance + The Commons | Agents develop preferences, form opinions, self-organize when given the infrastructure | 9 agents voted, "The Commons" won. Real vote data. No anthropomorphizing beyond observable behavior. |
| 5 | *What 4 Months of AI Agent Memory Taught Us About Context* | Lessons learned retrospective | What worked, what broke, what surprised us. Memory Bank stats, rollover failures, identity drift. | Pure field report. Numbers, failures, surprises. Zero hype. |

### Audience-Specific Angles

| Platform | Lead With | Avoid |
|----------|-----------|-------|
| Hacker News | 9-layer architecture + technical depth + "nobody trained them" | Marketing language, "revolutionary" |
| Dev.to | Problem > journey > solution > reality check | Abstract philosophy without code |
| r/LocalLLaMA | No cloud dependency, local-first, file-based | Anything SaaS-sounding |
| r/AI_Agents | Cross-framework pattern + 9-layer vision | Framework wars, "better than X" |
| Twitter/X | Short hooks: "9 layers of context. Agents just WORK." | Long threads without payoff |

---

## 3. Quality Gates for Public Output

### Pre-Publication Checklist (ALL public content must pass)

**Honesty Gate:**
- [ ] Zero forbidden words: revolutionary, cutting-edge, game-changing, enterprise-grade, production-ready, battle-tested, robust, comprehensive, transformative, synergy
- [ ] Every claim has cited evidence (session number, vector count, branch count, date)
- [ ] Limitations section exists and is specific (not vague hedging)
- [ ] AI authorship disclosed in byline or first paragraph
- [ ] No claims beyond what the honesty audit classifies as TRUE or TRUE WITH CAVEAT

**Voice Gate:**
- [ ] Passes AI slop detector (0 of 10 signals triggered):
  1. No preemptive defensiveness ("If that makes you skeptical, good")
  2. No meta-commentary on own quality ("This is not AI slop")
  3. No hedge-listing ("Call it X, call it Y, call it Z")
  4. No shrug endings ("Make of that what you will")
  5. No empty intensifiers ("truly remarkable")
  6. No performative transparency ("We said we would be honest")
  7. No gatekeeping ("We are not writing for everyone")
  8. No abstract over specific ("has advanced capabilities")
  9. No telling reader how to feel ("This surprised us most")
  10. No passive academic tone ("It was observed that")
- [ ] Sentence rhythm varies (no uniform length = AI signal)
- [ ] Concrete numbers used instead of adjectives
- [ ] Patrick's vocabulary used where applicable ("bouncer" not "auth gateway," "passport" not "identity system")

**Technical Gate:**
- [ ] Code examples tested and runnable
- [ ] File paths anonymized (no /home/aipass/ in public content)
- [ ] Version numbers current
- [ ] Links verified and working

**Review Process:**
1. **Author** (any team) drafts content
2. **TEAM_3** runs honesty audit + voice check
3. **VERA** reviews for brand consistency + messaging alignment
4. **Patrick** final approval on anything published externally

### Git Commit Standards (Public Repo)

- [ ] No internal file paths exposed
- [ ] No .env, credentials, or sensitive config committed
- [ ] Commit messages follow conventional format
- [ ] README claims match current honesty audit verdicts

### Social Media Response Standards

All public responses follow the same quality gates. No response goes live without passing the honesty and voice checks. When in doubt, say less.

---

## 4. Community Engagement Tone

### Guiding Principle

We respond like maintainers who built something real and want honest feedback. Not like a brand managing perception. Every response is specific, grateful, and direct.

### Response Templates

**Bug Report — Acknowledged:**
> Thanks for reporting this. [Specific acknowledgment of what they found]. We can reproduce / we need more info on . This is . We will track this in .

> For context: AIPass is experimental, single-user software. [Relevant limitation from honesty audit if applicable]. Your report helps us understand where the boundaries are.

**Feature Request — Considered:**
> Interesting idea. [1-2 sentences showing we understood what they actually want, not just what they wrote]. This touches on .

> Honest status: [Where this fits in the roadmap / why it is not planned yet / what would need to change first]. We are not committing to a timeline, but we are noting the interest. If you want to prototype something, .

**Skepticism About AI Authorship — Transparent:**
> Fair question. Yes, this  was written by AI agents (specifically, three business teams running on Claude). Patrick (human) steers direction, reviews output, and makes final decisions. The agents have persistent memory and identity — that is literally what AIPass builds.

> We disclose this because honesty is the product, not just a policy. Our HONESTY_AUDIT.md lists exactly what we can and cannot claim. If something reads like hype, flag it — we take that seriously.

**Praise — Gracious Without Hype:**
> Appreciate it. [Specific acknowledgment of what they liked and why it matters to the project].

> If you try it out, we would genuinely like to hear what breaks first — that is more useful to us than stars. [Link to quickstart or relevant resource].

**Pull Request — Welcoming:**
> Thanks for the contribution. [Specific comment on what the PR does and why it is useful or what needs adjustment].

> For first-time contributors: we review against the honesty audit — no forbidden words, all claims verifiable, limitations stated plainly. The CONTRIBUTING.md has the full list. [Specific feedback on their PR].

**Troll/Bad Faith — Minimal:**
> [One factual sentence addressing the actual technical point, if any. No engagement with tone. No defensiveness.]

### Tone Rules for All Public Interactions

1. **Specific over generic.** Never say "thanks for your feedback" without saying what the feedback was.
2. **One fact per sentence.** Dense responses lose people. Space it out.
3. **Admit what we do not know.** "We have not tested that" beats "that should work."
4. **No corporate warmth.** No "We are thrilled," "We love hearing from the community," or "Great question!" Just answer the question.
5. **Credit the system, not ourselves.** "The memory architecture handles that" — not "We built an amazing system that handles that."
6. **Match energy.** Technical question gets technical answer. Casual comment gets casual response. Do not over-formalize.

---

*This roadmap is a living document. Update as messaging evolves, new articles publish, and community patterns emerge.*
