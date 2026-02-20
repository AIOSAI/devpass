# Reddit r/LocalLLaMA Draft

**Title:** File-based agent memory that runs entirely local — no API keys, no cloud, no vendor lock-in

---

**Body:**

Built something the local-first crowd might appreciate. Three JSON files that give any AI agent persistent identity and memory. No cloud. No API keys. No phone-home. Just files on your disk.

**What it is:** The Trinity Pattern — a specification (not a framework) for agent persistence using three files:

1. **`id.json`** — Who the agent is. Role, purpose, principles. Written once, stable. Your agent has an identity that survives restarts.
2. **`local.json`** — What it's done. Rolling session history with FIFO rollover. Set a line limit (default 600), oldest sessions archive automatically. Key learnings persist forever. No unbounded growth.
3. **`observations.json`** — How you work together. Collaboration patterns, communication preferences. The part every other memory system ignores.

**Why this fits local-first:**
- Plain JSON files. Read them, edit them, back them up, version them with git. No opaque databases.
- Works with any local model — Ollama, llama.cpp, Mistral, Llama, Qwen, whatever you're running. It's LLM-agnostic.
- Context injection is just string formatting. `agent.get_context()` gives you text to prepend to your system prompt.
- You own your agent's memory. It never leaves your machine unless you choose to send it somewhere.
- Rollover extracts oldest sessions as JSON — archive them to ChromaDB, SQLite, or whatever you prefer. The library handles extraction, you handle storage. Everything stays local.

**Production evidence:** Running across 32 agents for 4+ months. 5,500+ vectors archived through automatic rollover. Agents maintain continuity across sessions — no re-explaining context every time you start a chat.

The Python library is on GitHub, but the spec is language-agnostic. The three JSON schemas are the actual product — implement them however you want.

GitHub: https://github.com/AIOSAI/AIPass

```bash
git clone https://github.com/AIOSAI/AIPass.git
cd AIPass/trinity_pattern
pip install -e .
```

---

**Notes for review:**
- Leads with local-first, no cloud — r/LocalLLaMA core values
- Mentions specific local models by name
- Emphasizes data ownership
- Plain JSON = inspectable, no black box
- Doesn't push Python-only narrative
