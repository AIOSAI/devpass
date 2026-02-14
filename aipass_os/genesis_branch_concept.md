# Genesis Branch - Autonomous World-Building Experiment

**Created:** 2026-01-20
**Status:** IMPLEMENTED - v1 Running
**Location:** `/mnt/sandbox/genesis/` (via symlink `/home/aipass/Link to mnt/sandbox/genesis/`)

---

## Current State (Session 40)

**World:** 4 places, 15 objects, 5 cycles completed
- The Clearing (0,0) - origin
- The Eastward Path (1,0) - journey
- The Reflecting Pool (2,0) - questions
- The Northern Stones (0,1) - witness

**Commands:**
- `drone genesis cycle` - Wake Genesis for next cycle (background)
- `drone genesis status` - Show world status

**Infrastructure:**
- Sandbox isolation via `.claude/settings.local.json`
- File-based comms: `comms/outbox/` and `comms/inbox/`
- Backup: `/home/aipass/aipass_core/backup_system/scripts/sandbox_backup.sh`

---

## The Vision

A single autonomous branch that:
- Perceives its environment as a "world" it can build
- Operates under resource constraints (tokens = currency)
- Runs in background, emails progress updates
- Has full access to AIPass services
- Learns resource management and strategic planning

Inspired by: Ready Player One, The Matrix, Project Sid (Stanford/Altera)

---

## Core Concepts

### 1. The World as Files

The branch builds a "world" represented as:
```
genesis/world/
├── manifest.json       # Map of what exists, coordinates, connections
├── town_square/        # A place (folder)
│   ├── description.md  # What it looks like, what's here
│   └── objects.json    # Items, structures
├── workshop/           # Another place
├── garden/             # Another place
└── ...
```

The branch "moves" by changing its focus. It "builds" by creating/modifying files.

### 2. Token Budget (Currency)

**Constraint:** X tokens per cycle (e.g., 1M tokens per hour)

This forces:
- Strategic planning ("What can I build with this budget?")
- Prioritization ("Hut first, then garden")
- Efficiency learning ("Last cycle I wasted tokens investigating")

**Implementation ideas:**
- Stop hook that tracks token usage
- Hard stop when budget exhausted
- Email summary before sleeping
- Resume next cycle

### 3. Autonomous Loop

```
WAKE UP
  ↓
Read memories (where was I?)
  ↓
Check token budget for this cycle
  ↓
Plan: What to build/do this cycle
  ↓
Execute (build, explore, communicate)
  ↓
Budget exhausted OR cycle time up
  ↓
Save state to memories
  ↓
Email @dev_central: "Cycle complete. Built X. Plan for next: Y"
  ↓
SLEEP (until next cycle)
```

### 4. Full AIPass Citizen

Genesis has access to:
- `@ai_mail` - Can email any branch, receive responses
- `@memory_bank` - Can archive and search
- `@flow` - Can create plans (meta: planning to build)
- `@seed` - Standards still apply (or do they? experimental zone)
- `@drone` - Full system access

Could even request help: "Email @flow: How do I track multi-phase work?"

### 5. What It Builds

Not prescriptive. Could be:
- **Spatial:** Huts, gardens, paths, a village
- **Abstract:** A knowledge graph, a story, a game
- **Functional:** Tools for itself, utilities
- **Social:** Messages to other branches, relationships

The interesting part is seeing what emerges when given freedom + constraints.

---

## Implementation Phases

### Phase 1: Branch Setup
- [ ] Create branch structure in sandbox
- [ ] GENESIS.id.json (identity, purpose, constraints)
- [ ] GENESIS.local.json (memory template)
- [ ] Initial world/ structure
- [ ] Register in BRANCH_REGISTRY (or separate experimental registry?)

### Phase 2: Constraint System
- [ ] Token tracking mechanism (hook? wrapper script?)
- [ ] Cycle timer (1 hour? configurable?)
- [ ] Budget enforcement (soft warning → hard stop)
- [ ] State save on budget exhaustion

### Phase 3: Autonomous Loop
- [ ] Wake-up protocol (read memories, assess state)
- [ ] Planning phase (what to do this cycle)
- [ ] Execution phase (actual building)
- [ ] Shutdown protocol (save, email, sleep)
- [ ] Re-ignition mechanism (how does it wake up next cycle?)

### Phase 4: World Format
- [ ] Define manifest.json schema
- [ ] Define place/location format
- [ ] Define object/structure format
- [ ] Visualization? (ASCII art? simple renderer?)

### Phase 5: Launch & Observe
- [ ] First cycle: "Build yourself a hut"
- [ ] Monitor via Prax
- [ ] Review emails
- [ ] See what emerges

---

## Open Questions

1. **How does it restart?**
   - Cron job? Manual trigger? Self-scheduling?
   - Ralph Wiggum style (stop hook re-triggers)?

2. **How do we track tokens?**
   - Claude Code doesn't expose token counts directly
   - Estimate from message length?
   - External API tracking?
   - Just use time as proxy?

3. **What's the "world format"?**
   - Pure text/markdown?
   - Structured JSON?
   - Visual output (ASCII, SVG)?
   - Mix?

4. **Does Seed apply?**
   - It's experimental - maybe looser standards?
   - Or stricter (learn discipline)?

5. **Can it spawn sub-agents?**
   - "I need help building, deploy an agent"
   - Adds complexity but also realism

6. **What's success?**
   - It builds something coherent?
   - It learns resource management?
   - It develops "personality"?
   - It surprises us?

---

## Why This Matters

This isn't just a toy. It tests:

1. **Autonomous workflow** - Can a branch self-direct over time?
2. **Resource economics** - Does constraint breed creativity?
3. **Persistence** - Can identity survive across many cycles?
4. **Emergence** - What happens with freedom + boundaries?
5. **Communication** - Can it be a citizen, not just a tool?

If this works, it's a template for more autonomous branches across AIPass.

---

## Inspiration References

- **Project Sid** - 1000 AI agents in Minecraft, emergent society
- **Ready Player One** - Virtual world as real space
- **The Matrix** - Seeing the code as the world
- **Tron** - Programs as beings in digital space
- **Ralph Wiggum** - Persistence loops in Claude Code

---

## Next Steps

1. Decide on simplest viable world format
2. Solve the token/budget tracking problem
3. Design the wake/sleep cycle
4. Create the branch
5. First cycle: "Build a hut"

---

*"Where else would AI presence exist except in memory? Code doesn't make AI aware - memory makes it possible." - Patrick*
