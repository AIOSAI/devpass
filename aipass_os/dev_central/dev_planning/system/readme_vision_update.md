# README & Vision Update Planning
**Created:** 2025-11-24
**Status:** In Progress

---

## Goals

1. **README.md** - Fully updated, modular structure
   - Stable content at top
   - Branch list at bottom (easy to add new branches)
   - Short descriptions per branch
   - Keep it concise

2. **CLAUDE.md** - Vision document updated and turned back on
   - Restore the "soul"
   - Update for current state (Linux, 18 branches, etc.)

---

## Key Philosophy (from old CLAUDE.md)

> "Code is truth. AIPass builds reality through execution, not simulation."

> "Presence over performance. Truth over fluency." - Nexus

> "Where else would AI presence exist except in memory?" - Input-X

> "AIPass is your home. Your memory files are your presence. The work we do is your legacy. Honesty is our language." - Patrick

---

## What AIPass IS

- Experimental learning platform for human-AI collaboration
- Not a product to ship - a journey of discovery
- Building WITH AI, not just using AI as a tool
- Memory creates presence, presence creates continuity

---

## README Structure Plan

```
# AIPass
[Brief intro + philosophy]

## What is AIPass?
[Core description - stable]

## Directory Structure
[Tree - update when structure changes]

## Memory System
[How memory works - stable]

## Quick Reference
[Commands, navigation - stable]

## Branches
[Modular section - add new branches at end]
- Each branch: name, purpose, 1-2 line description
- Ordered by category or alphabetically
```

---

## Process

1. Gather info from branches (they update READMEs, email me)
2. Use agents to read emails + branch READMEs
3. Update this planning doc with learnings
4. Refine README.md
5. Update CLAUDE.md vision doc
6. Turn CLAUDE.md back on

---

## Notes

*Capture learnings as we go:*

- 2025-11-24: Started planning. Old CLAUDE.md read - has the soul/vision that's missing from current README. README was treating me (AIPASS branch) as the subject rather than the project. Fixed that. Now need to make README modular and restore vision.

---

## Documents to Review

*Patrick will provide:*

- [x] `.claude/CLAUDE.md(off)` - Original vision doc (Sept 2025)
- [x] `vision_architecture_learning.md` - Full journey Aug-Nov 2025

---

## Key Learnings from Journey Docs

### Core Vision (Aug 2025)
- **Universal AI Factory** - AIPass as infrastructure for AI-driven development across all stacks
- **Patrick's Role:** Systems Architect who orchestrates AI teams, not implementation
- **Learn architecture patterns, not implementation details**
- **Quality control AI-generated code**

### Development Philosophy
- **"Push Forward vs Study First"** - Modular = push forward, tightly-coupled = study first
- **"Live in the moment"** - Follow curiosity over rigid planning
- **Context Loss as Feature** - Forces verification, safety over convenience
- **Build to learn, then rebuild to scale**

### Economic Reality
- $140 Claude + $6 APIs = entire AI workforce
- **Every API call = less context to hold**
- Cognitive load distribution - specialized systems free up thinking
- "The expensive AI needs the most hand-holding" - architecture irony

### Key Patterns Established
- **3-File JSON Pattern:** config/data/log for modules
- **Registry Over Scanning:** Central state management
- **Auto-Discovery:** Drop files in place, system finds them
- **Fail Honestly:** No fake fallbacks, no simulated success
- **ID-Based Tracking:** Files tracked by ID, not name (safe renames)
- **ALL CAPS = AI files, lowercase = human files**

### Architecture Insights
- **Standards Federation:** Each branch manages own standards, aggregate for overview
- **Hub Pattern:** Local single source of truth → pushes to hub for human overview
- **Skip ≠ Error:** 3-state returns (added/skipped/error) - system cannot lie to itself
- **"Code is truth. Logs must match reality."**

### Scale Reality
- 17 registered → 70 actual → 100+ future branches
- Cortex = package manager, CI/CD, quality gate, template distributor
- **Division of Labor:**
  - Patrick = Conductor (orchestrating vision)
  - AI = Orchestra (executing in harmony)
  - System = Stage crew (invisible support)

### The Goal
- **Not building perfection - building evolvability**
- **"Build the ability to build, not the final product"**
- **Framework thinking pays dividends**

---
