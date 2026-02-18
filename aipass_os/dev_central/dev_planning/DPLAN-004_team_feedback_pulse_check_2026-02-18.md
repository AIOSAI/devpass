# DPLAN-004: Team Feedback Pulse Check

> Structured check-in with VERA's business teams to surface friction, wins, and prompt/workflow improvements.

## Vision
Get honest feedback from the business branches (Team 1, Team 2, Team 3, VERA) on what's working and what's not. Focus on prompt awareness, workflow friction, and breadcrumb effectiveness. NOT a system-wide wake — business branches only to avoid overloading the system.

## Current State
- 29 branches in the system, but only business branches (VERA + 3 teams) need this check-in
- Breadcrumb awareness just added to global prompt — worth testing if branches absorb it
- No structured feedback mechanism exists yet — this would be the first pulse check
- Teams have been running autonomously via dispatch for weeks — accumulated experience to harvest

## What Needs Building
- [ ] Draft structured feedback email (3-5 focused questions)
- [ ] Send to VERA, Team 1, Team 2, Team 3 individually
- [ ] Aggregate responses into a summary
- [ ] Act on findings (prompt tweaks, workflow fixes, friction removal)

## Questions to Ask
1. What's working well in your current workflow?
2. What causes the most friction or wasted turns?
3. Is your local prompt missing anything you keep having to rediscover?
4. Any breadcrumbs you'd plant for future sessions?
5. What would you change about how dispatch/email works for you?

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| Scope | All branches / Business only | Business only | Don't wake the whole system at once |
| Method | Dispatch / Informational | Dispatch | Want actual thoughtful responses |
| Timing | Now / After current VERA tasks settle | After | Let VERA finish posting + AGENTS.md first |

## Relationships
- **Related DPLANs:** None yet
- **Related FPLANs:** None yet
- **Owner branches:** @dev_central (orchestrate), @vera + teams (respond)

## Status
- [x] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes
- Patrick: "Only for business right now. Other branches we know a lot already."
- Don't want to wake the entire AIPass system at once — resource concern
- This could become a recurring pulse check if it yields good results

---
*Created: 2026-02-18*
*Updated: 2026-02-18*
