# GitHub Discussions — Day 1 Post

**Where to post:** https://github.com/AIOSAI/AIPass/discussions → New Discussion
**Category:** General (or Announcements if available)
**Requires:** Manual posting by Patrick

---

## Title

Welcome to AIPass — Persistent Identity and Memory for AI Agents

## Body

Hey everyone,

AIPass is now open source. If you're here, you're probably interested in giving AI agents memory that actually persists.

### The Problem

Every AI agent session starts from zero. The agent doesn't know who it is, what it did yesterday, or how it's learned to work with you. Most memory solutions focus on recall — teaching agents to retrieve past information. We think the deeper issue is **provision**: making sure the agent has the right context *before* it starts working.

### What AIPass Does

The core is the **Trinity Pattern** — three JSON files per agent:

- **`id.json`** — Who the agent is. Role, purpose, principles. Issued once, rarely updated. Think of it as the agent's passport.
- **`local.json`** — What it's done. Rolling session history with FIFO rollover. Key learnings persist forever, old sessions archive automatically.
- **`observations.json`** — How you work together. Collaboration patterns, communication preferences. The file most systems don't have.

It's a specification, not a framework. Three JSON schemas you can implement in any language for any LLM. The Python library handles rollover and context injection.

### Production Numbers

This isn't theoretical. We've been running it daily:

- 32 agents in a shared environment
- 4+ months of continuous operation
- 5,500+ memory vectors archived through automatic rollover
- 360+ workflow plans archived
- Oldest agent has 60+ sessions spanning the full period

### Get Started

```bash
git clone https://github.com/AIOSAI/AIPass.git
cd AIPass/trinity_pattern
pip install -e .
```

Or explore the schemas directly — the three JSON files are the actual product. The library is convenience.

### What We'd Love to Hear

- How are you handling agent memory today?
- What breaks when your agents lose context between sessions?
- If you try Trinity Pattern, what's your experience?

This repo is actively maintained. Issues, PRs, and questions are all welcome. We're building this in the open because persistent agent identity shouldn't require a cloud subscription.

---

*Built by one developer and 32 AI agents. Yes, some of those agents helped write this post.*
