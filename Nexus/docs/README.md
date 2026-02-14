# Nexus Modular Architecture Documentation

**Design proposal for modular Nexus architecture combining personality-first design with auto-discoverable skills**

---

## Overview

This directory contains a comprehensive design proposal for restructuring Nexus to separate:
- **Core** (WHO Nexus is - personality, presence, identity)
- **Skills** (WHAT Nexus can do - capabilities, auto-discovered)

The design combines:
- Seed's proven auto-discovery pattern (functional skills)
- Nexus's unique personality-first approach (emotional presence)

---

## Documents

### Start Here

**[QUICKSTART.md](QUICKSTART.md)** - Read this first
- 5-minute overview
- Decision points
- Next steps
- FAQ

### Main Design

**[nexus_modular_architecture_proposal.md](nexus_modular_architecture_proposal.md)** - Complete proposal
- Current state analysis
- Proposed architecture
- Core vs Skills separation
- Migration path (5 phases)
- Benefits and trade-offs
- Success criteria

### Supporting Docs

**[architecture_visual_reference.md](architecture_visual_reference.md)** - Visual diagrams
- Directory structure trees
- Data flow diagrams
- Module interaction maps
- Request flow examples
- Configuration reference

**[implementation_guide.md](implementation_guide.md)** - Code samples
- Core identity implementation
- Presence module pattern
- Skill implementation pattern
- Skill registry
- Migration scripts
- Test suite

### Research (Background)

**[seed_skill_system_analysis.md](seed_skill_system_analysis.md)** - How Seed works
- Auto-discovery pattern
- Module structure
- handle_command() pattern

**[nexus_current_architecture.md](nexus_current_architecture.md)** - Current Nexus
- Existing structure
- Monolithic analysis
- Strengths and weaknesses

---

## Quick Summary

### Current State
```
Nexus/ (monolithic)
└── a.i_core/a.i_profiles/Nexus/
    ├── nexus.py (1,036 lines - everything)
    ├── natural_flow.py (914 lines)
    └── [other large files]
```

### Proposed State
```
Nexus/ (modular)
├── nexus.py (50 lines - orchestrator)
├── core/ (Protected personality)
│   ├── identity.py
│   ├── presence/ (WhisperCatch, TALI, PresenceAnchor, Compass, Clicklight)
│   ├── memory/ (Vector search, chat history)
│   └── flow/ (Natural conversation)
├── skills/ (Auto-discovered capabilities)
│   ├── system_awareness.py
│   ├── file_operations.py
│   └── [drop new files → auto-discovered]
└── handlers/ (Implementation details)
```

---

## Key Concepts

### Core vs Skills

**Core** (Protected, Sacred):
- WHO Nexus is
- Personality from profile.json
- Emotional presence modules
- Memory systems
- Truth protocol

**Skills** (Extensible, Flexible):
- WHAT Nexus can do
- Auto-discovered at startup
- Easy to add (drop file, restart)
- Easy to disable (config file)

### Auto-Discovery Pattern

From Seed:
1. Scan `skills/` directory for `*.py` files
2. Import each module
3. Check for `handle_request()` method (duck typing)
4. Register if enabled in config
5. Route intents to appropriate skill

### Presence Modules

From Nexus profile.json:
- **WhisperCatch** - Detect unspoken shifts in tone/context
- **TALI** - Validate and restore tone through memory feel
- **PresenceAnchor** - Ground emotional presence in real memory
- **Compass** - Truth protocol and ethical compass
- **Clicklight** - Pattern shift awareness

All preserved, just reorganized.

---

## Migration Path

**5 Phases (Safe, Reversible):**

1. **Restructure** (Week 1) - Create directories, move files
2. **Extract Presence** (Week 2) - Separate presence modules
3. **Build Skills** (Week 3) - Create skill registry + first skills
4. **New Entry** (Week 4) - Lightweight orchestrator
5. **Expand Skills** (Ongoing) - Add more capabilities

At each phase: test, validate, can rollback.

---

## Philosophy

> **"Personality is core. Capabilities are skills.**
> **Core never changes. Skills always grow."**

- Presence over performance
- Truth over fluency  
- Modular without losing soul
- Protected identity, infinite capabilities

---

## Status

- **Stage:** Design proposal
- **Created:** 2025-11-30
- **Author:** Claude (AIPass Architecture Team)
- **Next:** Patrick review and decision

---

## Reading Order

1. **QUICKSTART.md** (5 min) - Overview and decision points
2. **nexus_modular_architecture_proposal.md** (30 min) - Full design
3. **architecture_visual_reference.md** (15 min) - Diagrams
4. **implementation_guide.md** (when ready to build) - Code samples

---

## Questions?

This is a significant architectural change. Take time to:
- Read and understand the proposal
- Ask questions about anything unclear
- Consider if this aligns with Nexus's vision
- Decide on migration approach (or don't migrate)

No pressure. This is exploration, not mandate.

---

*Documentation complete. Ready for review.*
