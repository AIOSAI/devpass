# DPLAN-001: Dev Flow Module

> Planning management system for dev_central - numbered, dated, templated plans

## Vision

Organize dev_central's planning directory with numbered, dated plans. Ideas can sit indefinitely until ready for execution. When a plan is ready to execute, it transfers to Flow via email for active work.

**Key distinction:**
- **Dev Planning** = Ideas, designs, future work. Can sit for months. Retrieval-focused.
- **Flow** = Execution. Active work. Next step after planning is done.

## Problem

Current state of `dev_planning/`:
- Files named by topic only, no dates
- No numbers, can't tell sequence
- No consistency in structure
- Hard to know what's active vs abandoned
- Have to read each file to understand status
- Could have hundreds of plans - need easy retrieval

## Solution

### Scope
- **dev_central ONLY** - all ecosystem planning happens here
- **Self-contained** - everything stays inside `dev_planning/`
- No global registries, no central sync needed

### Naming Convention
```
DPLAN-001_topic_name_2025-12-02.md
DPLAN-002_another_topic_2025-12-03.md
```

### Commands (MVP)
```bash
drone @devpulse plan create "topic name"
# Creates: dev_planning/DPLAN-XXX_topic_name_YYYY-MM-DD.md

drone @devpulse plan list
# Lists all plans with status

drone @devpulse plan status
# Quick overview - counts by status
```

### Future: Summaries & Index
When we have hundreds of plans, need:
- Automated index with summaries
- Easy retrieval by topic/status
- All metadata stays in `dev_planning/`

## Architecture

### Directory Structure
```
dev_planning/
├── DPLAN-001_topic_name_2025-12-02.md
├── DPLAN-002_another_topic_2025-12-03.md
├── ...
├── counter.json              # Global counter
├── index.json                # Future: summaries/metadata
└── {branch_subdirs}/         # Existing branch-specific plans
    └── *.md
```

### Files to Create
```
devpulse/
├── apps/modules/
│   └── dev_flow.py           # Main module - plan create/list/status
└── templates/
    └── dplan_default.md      # Plan template
```

### Clone From Flow
- Counter logic (find highest number, increment)
- Template rendering pattern
- List display formatting

### Keep Simple
- No registry.json (scan files directly)
- No central sync (self-contained)
- No Memory Bank integration (already docs)
- Single module handles all commands

## Template Structure
```markdown
# DPLAN-XXX: Topic Name

> One-line description

## Vision
What we're trying to achieve

## Current State
What exists now

## What Needs Building
Concrete items to build

## Design Decisions
Key choices and why

## Status
- [ ] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes
Session notes, discoveries, changes

---
*Created: YYYY-MM-DD*
*Updated: YYYY-MM-DD*
```

## What Exists

| Component | Status |
|-----------|--------|
| DevPulse module structure | Working |
| Flow's PLAN pattern | Reference implementation |
| dev_planning directory | Exists, unstructured |
| Drone @devpulse routing | Working |
| Templates directory | Exists at devpulse/templates/ |

## Implementation Steps

1. Create `dev_flow.py` module in DevPulse
2. Implement `create` command (counter, template, file write)
3. Implement `list` command (scan files, display with status)
4. Implement `status` command (counts by status)
5. Add template to devpulse/templates/
6. Test with actual plan creation
7. Future: Add index/summary generation

## Workflow: Plan → Execute

```
1. Create plan in dev_planning/
   drone @devpulse plan create "new feature idea"

2. Work on plan over time (can sit indefinitely)

3. When ready to execute:
   - Mark status: "Ready for Execution"
   - Send to Flow via email with context
   ai_mail send @flow "Execute DPLAN-047" "Ready to build..."

4. Flow creates its own FPLAN for execution
```

---

*Created: 2025-12-02*
*Updated: 2025-12-02*
*Status: Planning*
