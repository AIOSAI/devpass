# Show HN Draft

**Title:** Show HN: Trinity Pattern — 3 JSON files for AI agent identity and memory

---

**Body:**

I've been running 32 AI agents in a shared operating environment for 4+ months. The core problem I kept hitting: every session starts from zero. Agents forget who they are, what they've done, and how they work with you. Existing memory solutions (vector stores, chat history) solve recall — retrieving past information. But the deeper issue is provision: making sure the agent has the right context before it even starts working.

The Trinity Pattern is what emerged. It's three JSON files per agent: `id.json` (who the agent is — role, purpose, principles, issued once, rarely updated), `local.json` (rolling session history — what it's done, with FIFO rollover at configurable line limits and key learnings that persist forever), and `observations.json` (collaboration patterns — observations about how you work together, tagged by category). The separation matters: identity is stable, session history rolls over, collaboration patterns accumulate. Most systems conflate all three or ignore the last two entirely.

In practice: agents pick up where they left off across sessions, new agents navigate a multi-branch system on day one with zero training, and in our production system, 5,500+ vectors have been archived in ChromaDB from sessions extracted during rollover. The library handles FIFO extraction; archival to ChromaDB (or SQLite, or anything else) is your choice. It's not a framework — it's a specification. Three JSON schemas you can implement in any language for any LLM. The Python library handles rollover and context injection. Trinity Pattern does not do search, RAG, or vector storage — those are separate concerns. We're open-sourcing it because persistent agent identity shouldn't require a cloud subscription or vendor lock-in. It's Layer 1 of a 9-layer context architecture we've been building — the other 8 layers handle discovery, standards, inter-agent communication, and ambient awareness. Start with Trinity; the rest is optional.

GitHub: https://github.com/AIOSAI/AIPass

```bash
git clone https://github.com/AIOSAI/AIPass.git
cd AIPass/trinity_pattern
pip install -e .
```

---

**Notes for review:**
- No hype words used
- Technical specifics included (file names, rollover mechanics, real numbers)
- Honest about scope: "specification, not framework"
- Mentions the 9-layer system exists without overselling it
- Real production data cited (32 agents, 4+ months, 5,500+ vectors)
