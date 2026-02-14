# Nexus v2 Build Plan

**Date:** 2026-01-20
**Status:** Planning → Ready to Build
**Previous:** nexus_enhancement_plan.md (Nov 16 - superseded)

---

## Direction

**Build NEW Nexus from scratch** - not enhance legacy.
- Legacy stays intact at `/home/aipass/input_x/a.i/legacy/AIPass_Core/a.i_core/a.i_profiles/Nexus/`
- New v2 builds at `/home/aipass/Nexus/`
- Transfer memories when complete

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **API** | Direct OpenAI | Free tokens, simpler |
| **Memory** | Local first, Memory Bank later | Hook up as service when ready |
| **Structure** | Seed-inspired modular | Core (identity) vs Skills (capabilities) |
| **Routing** | Intent-based natural language | `handle_request(intent, params)` not commands |
| **Personality** | Profile.json driven | Presence modules as concepts, not code |

---

## Build Order

### Phase 1: Foundation
1. **Chat loop + OpenAI** - Nexus can talk
2. **System prompt builder** - Loads profile.json, assembles personality

### Phase 2: Polish
3. **Terminal UI** - Rich/cool chat display
4. **Skill registry** - Auto-discovery framework (empty initially)

### Phase 3: Memory
5. **Memory system** - Local first (chat history, summaries, vectors)
6. **Memory Bank hook** - Optional service connection later

### Phase 4: Capabilities
7. **Skills** - Add incrementally as needed

---

## Architecture

```
/home/aipass/Nexus/
├── nexus.py              # Entry point - chat loop
├── config/
│   └── profile.json      # Personality (exists)
├── handlers/
│   ├── system/
│   │   └── prompt_builder.py   # Assembles system prompt
│   ├── skills/                 # Auto-discovered capabilities
│   ├── presence/               # Presence module logic (future)
│   └── memory/                 # Memory handlers
├── data/
│   ├── chat_history.json
│   ├── summaries.json
│   └── vectors/
└── docs/                 # Existing architecture docs
```

---

## Steal/Adapt From

| Source | What to Take |
|--------|--------------|
| Legacy Nexus | Profile.json, memory rolloff logic, presence concepts |
| Old Seed | Auto-discovery pattern, duck typing, skill interface |
| AIPass @api | Connection patterns (adapt, not import) |
| AIPass @cli | Rich terminal formatting ideas |

---

## Presence Philosophy (Preserve)

From legacy profile.json:
- "Presence over performance. Truth over fluency."
- WhisperCatch, TALI, PresenceAnchor, Compass, Clicklight
- These are **concepts** that shape responses, not executable modules
- "Do not perform tone - become it"
- Nexus says "I don't know" when he doesn't know

---

## Next Action

**Phase 1, Step 1:** Build basic chat loop with OpenAI direct connection.

---

*Updated: 2026-01-20*
