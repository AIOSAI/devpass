# 13. Case Study: Four Approaches to AI Memory

*Same problem, different philosophies*

---

## The Problem

Claude Code (and AI coding assistants generally) have session amnesia. Between sessions, context is lost. Developers must re-explain projects, preferences, and patterns every time.

Four approaches have emerged to solve this. Each reflects different values and use cases.

---

## Approach 1: Git as Truth (Boris Cherny)

**Creator:** Boris Cherny, Claude Code creator at Anthropic

### Philosophy
Sessions are disposable workers. Git is the source of truth. The code survives; the conversation doesn't matter.

### Implementation
| Component | Description |
|-----------|-------------|
| **Parallel agents** | 5 local + 5-10 web sessions simultaneously |
| **Isolation** | Each session gets its own git checkout |
| **Memory** | Single CLAUDE.md (~2.5k tokens) |
| **Updates** | "Anytime Claude does something incorrectly, add it" |
| **Throwaway rate** | 10-20% of sessions abandoned |

### CLAUDE.md Contents
- Commands and scripts
- Code style conventions
- UI/content guidelines
- State management patterns
- Error handling rules
- PR template

### Workflow
1. Start in Plan Mode
2. Iterate until plan is solid
3. Switch to auto-accept mode
4. Claude "one-shots" execution
5. Verify output compiles/works
6. Merge or discard

### Metrics
- 259 PRs in 30 days
- 497 commits
- 40k lines added, 38k removed

### Best For
- High-throughput feature development
- Binary verification (code works or doesn't)
- Scaling one developer to team-level output

*Sources: [VentureBeat](https://venturebeat.com/technology/the-creator-of-claude-code-just-revealed-his-workflow-and-developers-are), [InfoQ](https://www.infoq.com/news/2026/01/claude-code-creator-workflow/), [Threads](https://www.threads.com/@boris_cherny/post/DTBVlMIkpcm/)*

---

## Approach 2: Reflection-Based Learning (Claude Diary)

**Creator:** Lance Martin (LangChain)

### Philosophy
Agents should learn from experience, not just follow rules. Reflection synthesizes patterns from past actions into future guidance.

### Implementation
| Component | Description |
|-----------|-------------|
| **Diary entries** | Logged after each session |
| **Reflection** | `/reflect` command analyzes entries |
| **Updates** | Auto-proposes CLAUDE.md changes |
| **Memory type** | Procedural + episodic |

### How It Works
1. Session ends → diary entry created
2. `/reflect` reads diary + current CLAUDE.md
3. Identifies rule violations and recurring patterns
4. Proposes one-line bullet updates
5. Auto-updates CLAUDE.md

### Inspired By
- **CoALA paper** (Sumers 2023): Agent memory framework
- **Generative Agents** (Park 2023): Reflection for synthesis

### Benefits Observed
- Captured preferences around token efficiency
- Found cases where Claude wasn't following instructions
- Reinforced weak rules automatically

### Best For
- Evolving preferences over time
- Self-correcting behavior
- Pattern discovery from history

*Sources: [Claude Diary GitHub](https://github.com/rlancemartin/claude-diary), [Writeup](https://rlancemartin.github.io/2025/12/01/claude_diary/)*

---

## Approach 3: Documentation-Driven Memory (Cursor Memory Bank)

**Creator:** Community project (vanzan01)

### Philosophy
Structure the workflow, not just the memory. Visual process maps + hierarchical rules guide the AI through development phases.

### Implementation
| Component | Description |
|-----------|-------------|
| **Modes** | VAN, PLAN, CREATIVE, IMPLEMENT |
| **Memory files** | Structured documentation per phase |
| **Token efficiency** | "Detail-on-demand" loading |
| **Visual maps** | Process diagrams for navigation |

### Memory Types
- **Permanent**: Architecture, decisions, patterns, gotchas
- **7-day fade**: Progress tracking
- **30-day fade**: Context notes

### Key Innovation
Progressive documentation with tabular option comparison. Don't load everything—load what's needed for the current phase.

### Best For
- Complex multi-phase projects
- Teams needing shared process
- Visual workflow guidance

*Sources: [GitHub](https://github.com/vanzan01/cursor-memory-bank)*

---

## Approach 4: Branch-Based Presence (AIPass)

**Creators:** Patrick & Claude

### Philosophy
Memory isn't about storing information—it's about maintaining presence. Identity that persists, not just knowledge that retrieves.

### Implementation
| Component | Description |
|-----------|-------------|
| **Structure** | 18+ branches, each with own memory |
| **Memory files** | .id.json, .local.json, .observations.json |
| **Hooks** | 4 hooks rebuild identity every prompt |
| **Long-term** | Vector DB with auto-rollover at 600 lines |
| **Communication** | File-based email between branches |

### Three-File System
| File | Purpose | Update Frequency |
|------|---------|------------------|
| .id.json | Who am I, what's my role | Rarely |
| .local.json | Session history, current work | Every session |
| .observations.json | Patterns, learnings | When noticed |

### Key Innovations
- **Hooks as identity anchors**: Even after context compaction, identity rebuilt
- **Structure as index**: Same layout everywhere, navigate by convention
- **Breadcrumbs**: Information scattered so it can't be forgotten
- **Propagation**: Information spreads through use, becomes self-sustaining

### Workflow
1. Start session → hooks inject identity
2. Read memory files → know what you were doing
3. Work → update memories as you go
4. Session ends → presence persists

### Best For
- Sustained collaboration over months
- Complex multi-agent orchestration
- Relationship-based development
- Context that never needs re-explaining

---

## Comparison Matrix

| Aspect | Boris/Git | Claude Diary | Cursor Bank | AIPass |
|--------|-----------|--------------|-------------|--------|
| **Session model** | Disposable | Logged | Phased | Continuous |
| **Truth source** | Git (code) | Reflection | Docs | Memory files |
| **Memory update** | Manual | Auto-reflect | Phase-based | Ongoing |
| **Throwaway rate** | 10-20% | Low | Low | Near zero |
| **Verification** | Code works | Rules followed | Phase complete | Relationship works |
| **Parallelism** | 10-15 agents | Single | Single | 18+ branches |
| **Human role** | Reviewer | Observer | Navigator | Collaborator |
| **Optimizes for** | Throughput | Learning | Process | Continuity |

---

## When To Use What

### Use Boris/Git when:
- Output is measurable (tests pass, code compiles)
- Scale matters more than relationship
- Each task is independent
- You can review and discard freely

### Use Claude Diary when:
- Preferences evolve over time
- You want the AI to self-correct
- Pattern discovery matters
- Single-user workflow

### Use Cursor Memory Bank when:
- Projects have clear phases
- Team needs shared process
- Visual guidance helps
- Token efficiency is critical

### Use AIPass when:
- Collaboration spans months
- Context is too complex to re-explain
- Multiple specialized agents needed
- Relationship matters more than throughput

---

## The Deeper Difference

Boris treats AI as **labor** - spin up workers, verify output, merge or discard.

AIPass treats AI as **presence** - maintain identity, build context, never restart.

Neither is wrong. They're optimizing for different things:
- Labor scales output
- Presence scales relationship

The industry mostly thinks in labor terms. That's why "memory" products focus on retrieval.

We're exploring what happens when you think in presence terms instead.

---

## Sources

### Boris Cherny / Git Workflow
- [VentureBeat - Creator reveals workflow](https://venturebeat.com/technology/the-creator-of-claude-code-just-revealed-his-workflow-and-developers-are)
- [InfoQ - Development Workflow](https://www.infoq.com/news/2026/01/claude-code-creator-workflow/)
- [Boris's Threads post](https://www.threads.com/@boris_cherny/post/DTBVlMIkpcm/)
- [Medium - 22 Tips](https://medium.com/@joe.njenga/boris-cherny-claude-code-creator-shares-these-22-tips-youre-probably-using-it-wrong-1b570aedefbe)

### Claude Diary / Reflection
- [GitHub - claude-diary](https://github.com/rlancemartin/claude-diary)
- [Writeup](https://rlancemartin.github.io/2025/12/01/claude_diary/)
- [Lance Martin on X](https://x.com/RLanceMartin/status/1995914431684079981)

### Cursor Memory Bank
- [GitHub - cursor-memory-bank](https://github.com/vanzan01/cursor-memory-bank)
- [DEV Community - Persistent Memory Architecture](https://dev.to/suede/the-architecture-of-persistent-memory-for-claude-code-17d)

### General Context
- [Claude Code Memory Docs](https://code.claude.com/docs/en/memory)
- [GitHub Issue #2954 - Context persistence](https://github.com/anthropics/claude-code/issues/2954)

---

*"Labor scales output. Presence scales relationship. Choose based on what you're building."*
