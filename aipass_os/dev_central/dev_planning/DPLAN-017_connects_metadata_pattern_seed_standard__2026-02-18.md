# DPLAN-017: CONNECTS metadata pattern — Seed standard for file-level coupling

> Add `# CONNECTS:` metadata to code headers — a Seed standard that makes file-level coupling visible to agents and humans.

Tag: idea

## Vision
Files that must change together but have no import relationship are invisible coupling. Today, only human memory (Patrick) bridges this gap. CONNECTS makes it machine-readable: a comment block in the metadata header listing tightly-coupled files and what they share.

Goal: A Seed standard (new module or checklist item) that enforces/encourages CONNECTS declarations on files with hidden coupling. Agents can then discover coupling without burning research cycles.

## Current State
- First use: FPLAN-0355 Phase 1 added CONNECTS headers to dev_tracking.py, central_writer.py, cortex template, and template/ops.py (the dev.local section coupling)
- No Seed integration yet — just manually added comments
- Branch-level introspection exists (`drone @branch` shows capabilities) but file-level coupling is invisible
- The gap was proven in session 112: without Patrick's memory of dev.local's 4-file coupling, the FPLAN would have been incomplete

## What Needs Building
- [ ] Research: What does a Seed CONNECTS check look like? Advisory vs mandatory?
- [ ] Define: When should CONNECTS be added? (shared hardcoded values, must-change-together files, cross-branch coupling)
- [ ] Define: What CONNECTS should NOT cover (normal imports, loose coupling via events/email)
- [ ] Build: Seed module or checklist item that scans for CONNECTS and validates consistency
- [ ] Consider: Could CONNECTS be auto-detected? (files sharing identical string constants, etc.)
- [ ] Consider: CONNECTS aggregation — a central view of all coupling across the system

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| Enforcement level | Advisory (flag, don't fail) / Mandatory (fail audit) / Hybrid | Advisory with escalation | Start advisory, graduate to mandatory for critical files |
| Scope | File-level only / File + branch level / File + module level | File-level | Branch introspection already exists; file-level is the gap |
| Format | Comment block / JSON sidecar / Separate registry | Comment block in metadata header | Keeps it with the code, zero tooling needed to read |
| Auto-detection | Manual only / AI-assisted detection / Both | Both | Manual for now, AI-assisted detection as future evolution |

## Ideas
- Patrick: "If it's not connected to the system it gets lost" — conventions die, standards persist
- Patrick: "It's actually quite complicated" — needs direct work with Seed, not just a dispatch
- Could integrate with Memory Bank vectors — CONNECTS relationships as searchable metadata
- Potential Seed command: `drone @seed connects @branch` — show all coupling in a branch
- Long-term: CONNECTS could feed into automated change-impact analysis ("if you change this file, these also need updating")

## Relationships
- **Related DPLANs:** DPLAN-010 (DevPulse Evolution — where CONNECTS was first discussed)
- **Related FPLANs:** FPLAN-0355 (first implementation of CONNECTS in Phase 1)
- **Owner branches:** @seed (standard definition + enforcement), @dev_central (coordination)
- **Dependencies:** Needs Patrick + Seed direct collaboration — "quite complicated" per Patrick

## Status
- [x] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes
- Session 112: Emerged from dev.local simplification work. Patrick noticed that without his memory of how dev.local was connected across 4 files, the plan would have been incomplete.
- Initially proposed as "convention not standard" — Patrick pushed back: "if it's not a seed standard we have to remember, it will never be consistent. Today we good, 2 months its forgotten."
- Patrick confirmed this needs direct collaboration with Seed — not a simple dispatch. The design of what constitutes "hidden coupling" vs normal imports is nuanced.
- First CONNECTS headers already deployed in FPLAN-0355 Phase 1 (dev.local coupling files)

---
*Created: 2026-02-18*
*Updated: 2026-02-18*
