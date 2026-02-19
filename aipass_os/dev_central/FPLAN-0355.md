# FPLAN-0355 - DevPulse Evolution and dev.local Simplification (MASTER PLAN)

**Created**: 2026-02-18
**Branch**: /home/aipass/aipass_os/dev_central
**Status**: Active
**Type**: Master Plan (Multi-Phase)

---

## What Are Flow Plans?

Flow Plans (FPLANs) are for **BUILDING** - autonomous construction of systems, features, modules. They're the structured way to execute work without constant human oversight.

**This is NOT for:**
- Research or exploration (use agents directly)
- Quick fixes (just do it)
- Discussion or planning (that happens before creating the FPLAN)

**This IS for:**
- Building new branches/modules
- Implementing features
- Multi-phase construction projects
- Autonomous execution

---

## Master Plan vs Default Plan

| | Master Plan | Default Plan |
|---|-------------|--------------|
| **Use when** | 3+ phases, complex build | Single focused task |
| **Structure** | Roadmap + sub-plans | Self-contained |
| **Phases** | Multiple, sequential | One |
| **Sub-plans** | Yes, one per phase | No |
| **Typical use** | Build entire branch | One phase of master |

**Pattern:**
```
Master Plan (roadmap)
├── Sub-plan Phase 1 (default template)
├── Sub-plan Phase 2 (default template)
├── Sub-plan Phase 3 (default template)
└── Sub-plan Phase 4 (default template)
```

**How to start:**
1. DEV_CENTRAL provides planning doc or instructions
2. Branch manager reads and understands scope
3. Branch manager creates master plan: `drone @flow create . "Build X" master`
4. Branch manager fills in phases, then executes autonomously

---

## Critical: Branch Manager Role

**You are the ORCHESTRATOR, not the builder.**

Your 200k context is precious. Burning it on file reads and code writing risks compaction during autonomous work. Agents have clean context - use them for ALL building.

| You Do (Orchestrator) | Agents Do (Builders) |
|-----------------------|----------------------|
| Create plans & sub-plans | Write code |
| Define phases | Run tests |
| Give agent instructions | Read/modify files |
| Review agent output | Research/exploration |
| Course correct | Heavy lifting |
| Update memories | Single-task execution |
| Send status emails | Build deliverables |
| Track phase progress | Quality checks on code |

**Master Plan Pattern:** Define all phases → Create sub-plan for Phase 1 → Deploy agent → Review → Close sub-plan → Email update → Next phase

---

## Seek Branch Expertise

Don't figure everything out alone. Other branches are domain experts - ask them first.

**Before building anything that touches another branch's domain:**
```bash
ai_mail send @branch "Question: [topic]" "I'm working on X and need guidance on Y. What's the best approach?"
```

**Common examples:**
- Building something with email? Ask @ai_mail how delivery works
- Need routing or @ resolution? Ask @drone
- Unsure about standards? Ask @seed for reference code
- Need persistent storage or search? Ask @memory_bank
- Event-driven behavior? Ask @trigger about their event system
- Dashboard integration? Ask @devpulse about update_section()

They have deep memory on their systems. A 1-email question saves you hours of guessing. For master plans spanning multiple domains, identify which branches to consult during phase definitions.

---

## Notepad

Keep `notepad.md` in your branch directory as a shared scratchpad during the build. Use it for:
- **Status updates** - Quick progress lines so Patrick can glance without asking
- **Questions for Patrick** - Non-urgent questions that can wait for his next visit
- **Notes to self** - Decisions made, things to revisit, gotchas discovered

Update it as you work - lightweight, not formal. Patrick checks it when he wants to, skips it when he's busy. Low friction both ways.

```bash
# Create it at plan start
echo "# Notepad - FPLAN-0355" > notepad.md
```

---

## Command Reference

When unsure about syntax, use `--help`:

```bash
# Flow - Plan management
drone @flow create . "Phase X: subject"      # Create sub-plan (. = current dir)
drone @flow create . "subject" master        # Create master plan
drone @flow close FPLAN-XXXX           # Close plan
drone @flow list                       # List active plans
drone @flow status                     # Plan status
drone @flow --help                     # Full help

# Seed - Quality gates
drone @seed checklist <file>           # 10-point check on file
drone @seed audit @branch              # Full branch audit (before master close)
drone @seed --help                     # Full help

# AI_Mail - Status updates
drone @ai_mail send @dev_central "Subject" "Message"
drone @ai_mail inbox                   # Check your inbox
drone @ai_mail --help                  # Full help

# Discovery
drone systems                          # All available modules
drone list @branch                     # Commands for branch
```

---

## What is a Master Plan?

Master Plans are for **complex multi-phase projects**. You define all phases upfront, then create focused sub-plans for each phase.

**When to use:**
- 3+ distinct sequential phases
- Work spanning multiple sessions
- Need clear phase completion milestones
- Complex builds requiring sustained focus

**Pattern:** Master Plan = Roadmap | Sub-Plans = Focused Execution

---

## Project Overview

### Goal
Streamline dev.local.md to Issues + Todos only, evolve DPLANs with tagging/summaries/dashboard integration, and validate Memory Bank archival pipeline — making DevPulse a mature planning system on par with Flow's infrastructure.

### Reference Documentation
- **DPLAN-010:** `/home/aipass/aipass_os/dev_central/dev_planning/DPLAN-010_devpulse_evolution_and_dev_local_simplif_2026-02-18.md`
- **Flow's plan system (reference architecture):**
  - Registry: `/home/aipass/aipass_core/flow/apps/handlers/close/flow_registry.json`
  - Summaries: `/home/aipass/aipass_core/flow/apps/handlers/close/plan_summaries.json`
  - Central aggregation: `/home/aipass/aipass_core/ai_central/PLANS.central.json`
  - Dashboard push: Flow's `central_push.py` handler
- **DevPulse current code:**
  - Plan handlers: `/home/aipass/aipass_os/dev_central/devpulse/apps/handlers/plan/`
  - Module: `/home/aipass/aipass_os/dev_central/devpulse/apps/modules/dev_flow.py`
  - Template: `/home/aipass/aipass_os/dev_central/devpulse/templates/dplan_default.md`
- **dev.local central system:**
  - Central JSON: `/home/aipass/aipass_core/ai_central/DEVPULSE.central.json`
  - Central writer: DevPulse `central_writer.py`
  - Section validation: DevPulse `dev_tracking.py`
  - Cortex template: Cortex branch template for dev.local.md
- **Memory Bank:**
  - TRL registry: `/home/aipass/aipass_core/flow/apps/handlers/close/flow_mbank_registry.json`
  - Plans archive: `/home/aipass/aipass_core/memory_bank/plans/`
  - ChromaDB search: `drone @memory_bank search "query"`

### Success Criteria
1. dev.local.md slimmed to Issues + Todos — across template, validation, central writer, and compliance
2. DPLANs have tag classification (idea, upgrade, proposal, bug, research, seed, infrastructure)
3. `drone @devpulse plan list` shows tags + AI-generated 1-line summaries
4. Dashboard shows DPLAN counts by status and tag
5. DPLAN close → Memory Bank archival pipeline validated end-to-end

---

## Branch Directory Structure

Every branch has dedicated directories. Use them correctly:

```
branch/
├── apps/           # Code (modules/, handlers/)
├── tests/          # All test files go here
├── tools/          # Utility scripts, helpers
├── artifacts/      # Agent outputs (reports, logs)
├── docs/           # Documentation
└── logs/           # Execution logs
```

**Rules:**
- Tests → `tests/` (not root, not random locations)
- Tools/scripts → `tools/`
- Agent artifacts → `artifacts/`
- Create subdirs if needed: `mkdir -p artifacts/reports artifacts/logs`
- **Never delete** - DEV_CENTRAL manages cleanup
- Future: artifacts auto-roll to Memory Bank

---

## Phase Definitions

Define ALL phases before starting work:

### Phase 1: dev.local Simplification
**Goal:** Strip dev.local.md to Issues + Todos only, with coordinated code updates across all hardcoded section references.
**Agent Task:**
- Graduate valid ideas from dev_central's dev.local.md to DPLANs (ones not already captured)
- Archive stale/built ideas (Fragmented Memory, Watcher Agent, etc.)
- Strip dev.local.md to Issues + Todos sections only
- Update cortex branch template (new branches get slimmed version)
- Update `dev_tracking.py` — section validation, aliases, accepted sections list
- Update `central_writer.py` — counting logic for new section set
- Update dev status compliance check — reference new sections
- Update `system_prompt.md` to reflect new dev.local sections
- Decision: existing branches keep their dev.local.md as-is (only new branches get slimmed template)
- Add `# CONNECTS:` metadata header lines to all coupled files (breadcrumb pattern for future editors)
- Leave sections hardcoded — just update values from 6→2
**Deliverables:**
- Updated dev_central/dev.local.md (Issues + Todos only)
- Updated cortex template
- Updated dev_tracking.py, central_writer.py, compliance check (with CONNECTS headers)
- List of ideas graduated to DPLANs vs archived

### Phase 2: DPLAN Tagging
**Goal:** Add tag/classification to DPLANs so they can be filtered and categorized.
**Agent Task:**
- Add `Tag:` metadata line to DPLAN template (dplan_default.md)
- Define fixed tag vocabulary: idea, upgrade, proposal, bug, research, seed, infrastructure
- Update `status.py` (or create `tags.py` handler) to extract tags from DPLAN markdown
- Update `list.py` to display tags in output: `DPLAN-010 | DevPulse Evolution | Planning | (idea)`
- Update `create.py` to prompt/accept tag on creation
**Deliverables:**
- Updated DPLAN template with Tag field
- Tag extraction handler (tags.py or status.py update)
- Updated list display with tag column
- Updated create flow with tag support

### Phase 3: DPLAN List with Summaries
**Goal:** Add registry-based tracking and AI-generated summaries to DPLAN list, matching Flow's infrastructure.
**Agent Task:**
- Create `dplan_registry.json` (like flow_registry.json) — track plans with metadata (number, topic, status, tag, created date, closed date, file path)
- Build registry management handler (register on create, update on status change, remove on close)
- Add AI-generated summary support — generate on close, cache in `dplan_summaries.json`
- Enhanced list command: number, topic, tag, status, 1-line summary
- Add filter support: `drone @devpulse plan list --tag idea` or `--status planning`
- Lazy summary generation on list (if summary missing, generate and cache)
**Deliverables:**
- dplan_registry.json with all existing DPLANs populated
- dplan_summaries.json cache
- Updated list handler with summary + filter support
- Registry management handler

### Phase 4: Dashboard Integration
**Goal:** Push DPLAN data to dashboard so system-wide status is visible.
**Agent Task:**
- Push DPLAN data to DASHBOARD.local.json (devpulse section)
- Show: total plans, by-status breakdown, by-tag breakdown
- Create or update DEVPULSE.central.json at AI_CENTRAL (parallel to PLANS.central.json) to include DPLAN counts
- Wire dashboard push into create/close/status-change flows
- Verify PLANS.central.json tracking (may show 0 because no open FPLANs — test with a plan)
**Deliverables:**
- DASHBOARD.local.json devpulse section populated
- DEVPULSE.central.json updated with DPLAN counts
- Dashboard push integrated into plan lifecycle

### Phase 5: Memory Bank Archival Validation
**Goal:** Validate that DPLAN close → Memory Bank archival works end-to-end, confirm TRL tagging is correct.
**Agent Task:**
- Validate DPLAN close pipeline processes correctly (close.py → post_close_runner.py → mbank handler)
- Confirm TRL classification works for DPLANs (shared registry with FPLANs: flow_mbank_registry.json)
- Test: close a DPLAN and verify markdown appears in MEMORY_BANK/plans/ with correct TRL filename
- Test: verify ChromaDB embedding via `drone @memory_bank search` finds the closed plan
- Coordinate with @memory_bank to validate their side of the ingestion
- Document the full archival pipeline for future reference
**Deliverables:**
- Validated end-to-end close → archive → search pipeline
- Test results documented in artifacts/
- Any fixes to close/mbank handlers
- Pipeline documentation

---

## Execution Philosophy

### Autonomous Power-Through

Master plans are for **autonomous execution**. Don't halt production every phase waiting for DEV_CENTRAL review.

**The Pattern:**
- Power through all phases
- Accumulate issues as you go
- Deal with issues at the end
- DEV_CENTRAL reviews final result, not every step

**Why this works:**
- Context is precious - don't burn it chasing bugs
- Complete picture reveals which issues actually matter
- Many "bugs" resolve themselves when later phases complete
- DEV_CENTRAL time is for decisions, not babysitting

### The 2-Attempt Rule

When agent encounters an issue:

```
Attempt 1 → Failed?
    ↓
Attempt 2 → Failed?
    ↓
STOP. Mark as issue. Move on.
```

**Do NOT:**
- Try 5 different approaches
- Go down rabbit holes
- Burn context debugging
- Stop production for every error

**DO:**
- Note the issue clearly
- Note what was tried
- Move to next task
- Let branch manager decide priority

### Critical vs Non-Critical Issues

When you see an issue, decide:

| Question | If YES → | If NO → |
|----------|----------|---------|
| Does this block ALL future phases? | STOP. Investigate. | Continue. |
| Can the system work around this? | Continue. | STOP. Investigate. |
| Is this a syntax/import error? | Quick fix, continue. | - |
| Is this a logic/design problem? | Note it. Continue. | - |

**Critical (stop production):**
- Core module won't import at all
- Database/file system inaccessible
- Fundamental architecture wrong

**Non-critical (note and continue):**
- One command throws error but others work
- Registry not updating properly
- Edge case not handled
- Test failing but code runs

**Pattern:** Note issue → Continue building → Fix at end with complete picture

### False Positives Awareness

Seed audits are helpful but not infallible.

**When Seed flags something:**
1. Check if the code is actually correct from your understanding
2. If you're confident it's right → mark as false positive, move on
3. If you're unsure → note it, continue, review later

**Don't stop production for:**
- Style preferences (comments, spacing)
- Patterns that differ from Seed's but still work
- Checks that don't apply to your context

### Forward Momentum Summary
- **Don't stop to fix bugs during phases** - Note them, keep moving
- **Get complete picture first** - All phases done, THEN systematic fixes
- **Prevents:** Bug-fixing rabbit holes, premature optimization, scope creep
- **DEV_CENTRAL reviews at END** - not every phase

### Production Stop Protocol

If something causes production to STOP (critical blocker), **immediately email DEV_CENTRAL**:

```bash
drone @ai_mail send @dev_central "PRODUCTION STOPPED: FPLAN-0355" "Phase X halted. Issue: [description]. Attempted: [what was tried]. Awaiting guidance."
```

**Never leave a branch stopped without reporting.** DEV_CENTRAL needs visibility into all work.

### Monitoring Resources

For quick status checks and debugging, these resources are available:

| Resource | Location | Purpose |
|----------|----------|---------|
| Branch logs | `logs/` directory | Local execution logs |
| JSON tree | `apps/json_templates/` | Module firing status |
| Prax monitor | `drone @prax monitor` | Real-time system events |
| Seed audit | `drone @seed audit @branch` | Code quality check |

Use these when you need to confirm status or investigate issues.

### Agent Deployment Per Phase
Each phase = focused agent deployment:
1. Create sub-plan: `drone @flow create . "Phase X: [name]"`
2. Write agent instructions in sub-plan
3. Deploy agent with single-task focus
4. Review agent output (don't rebuild yourself)
5. Seed checklist on new code
6. Close sub-plan
7. Update memories
8. Email status to @dev_central
9. Next phase

### Agent Preparation (Before Deploying)

Agents can't work blind. They need context before they build.

**Your Prep Work (as orchestrator):**
1. [ ] Know where agent will work (branch path, key directories)
2. [ ] Identify files agent needs to reference or modify
3. [ ] Gather any specs, planning docs, or examples to include
4. [ ] Prepare COMPLETE instructions (agents are stateless)

**Agent's First Task (context building):**
- Agent should explore/read relevant files BEFORE writing code
- "First, read X and Y to understand the current structure"
- "Look at Z for the pattern to follow"
- Context-first, build-second

**What Agents DON'T Have:**
- No prior conversation history
- No memory files loaded automatically
- No knowledge of other branches
- Only what you put in their instructions

**Your instructions determine success - be thorough and specific.**

### Agent Instructions Template
```
You are working at [BRANCH_PATH].

TASK: [Specific single task for this phase]

CONTEXT:
- [What they need to know]
- Reference: [planning docs, existing code to study]
- First, READ the relevant files to understand current structure

DELIVERABLES:
- [Specific file or output expected]
- Tests → tests/
- Reports/logs → artifacts/reports/ or artifacts/logs/

CONSTRAINTS:
- Follow Seed standards (3-layer architecture: apps/modules/handlers)
- Do NOT modify files outside your task scope
- CROSS-BRANCH: Never modify other branches' files unless explicitly authorized by DEV_CENTRAL in the planning doc
- 2-ATTEMPT RULE: If something fails twice, note the issue and move on
- Do NOT go down rabbit holes debugging

WHEN COMPLETE:
- Verify code runs without syntax errors
- List files created/modified
- Note any issues encountered (with what was attempted)
```

---

## Phase Tracking

### Phase 1: dev.local Simplification
- [x] Sub-plan created: Dispatched directly (no sub-FPLAN needed)
- [x] Agent deployed: @devpulse + @cortex dispatched in parallel
- [x] Agent completed: Both replied successfully
- [x] Output reviewed: Code changes verified, dev.local.md confirmed slimmed
- [ ] Seed checklist passed
- [x] Sub-plan closed
- [ ] Memories updated
- [x] Email sent to @dev_central (self — we are dev_central)
- **Status:** Complete
- **Notes:** DevPulse updated ops.py, central_writer.py, template/ops.py with CONNECTS headers + 2-section validation. Cortex updated branch template. DevPulse graduated 6 ideas to DPLANs (011-016), archived stale/built items. Hardcoded sections left as-is per Patrick — revisit later. No push script exists for existing branches — only pull/aggregation (sync-devepulse.sh). DPLAN-017 created for CONNECTS Seed standard idea.

### Phase 2: DPLAN Tagging
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Seed checklist passed
- [ ] Sub-plan closed
- [ ] Memories updated
- [ ] Email sent to @dev_central
- **Status:** Pending
- **Notes:** Straightforward. Template update + handler update + list display update.

### Phase 3: DPLAN List with Summaries
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Seed checklist passed
- [ ] Sub-plan closed
- [ ] Memories updated
- [ ] Email sent to @dev_central
- **Status:** Pending
- **Notes:** Heaviest code phase. Registry JSON + management handlers + AI summary integration. Reference Flow's flow_registry.json and plan_summaries.json closely.

### Phase 4: Dashboard Integration
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Seed checklist passed
- [ ] Sub-plan closed
- [ ] Memories updated
- [ ] Email sent to @dev_central
- **Status:** Pending
- **Notes:** Depends on Phase 3 registry existing. Wire dashboard push into plan lifecycle events.

### Phase 5: Memory Bank Archival Validation
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Seed checklist passed
- [ ] Sub-plan closed
- [ ] Memories updated
- [ ] Email sent to @dev_central
- **Status:** Pending
- **Notes:** Depends on DPLAN close feature (currently being built by @devpulse agent). Need @memory_bank coordination. TRL confirmed as keeper — validate it works for DPLANs.

---

## Issues Log

Track issues here as you encounter them. Don't fix during build - log and continue.

| Phase | Issue | Severity | Attempted | Status |
|-------|-------|----------|-----------|--------|
| 1 | [description] | Low/Med/High | [what was tried] | Open/Resolved |
| 2 | [description] | Low/Med/High | [what was tried] | Open/Resolved |

**Severity Guide:**
- **High:** Blocks future phases, must fix before continuing
- **Med:** Affects functionality but can work around
- **Low:** Cosmetic, edge case, or false positive

**End of Build:** Review this log. Tackle High→Med→Low. Some Low issues may not need fixing.

---

## Master Plan Notes

**Cross-Phase Patterns:**
- Hardcoded section names appear in 4+ files — update all together in Phase 1, but leave hardcoded (no config abstraction this round)
- Add `# CONNECTS:` lines to metadata headers of tightly-coupled files (dev_tracking.py, central_writer.py, cortex template, compliance check) — makes entanglement visible at the code level

**Decisions:**
- Hardcoded sections: Leave as hardcoded, just update values from 6→2. Revisit configurable approach next time. (Patrick: "leave hard codes for now, maybe we sort it next time we look at this")
- File link metadata: Add `# CONNECTS:` block to metadata headers of coupled files — breadcrumb pattern for future editors

**Blockers & Resolutions:**
[None yet]

**Adjustments:**
[None yet]

---

## Final Completion Checklist

### Before Closing Master Plan

- [ ] All phases complete
- [ ] All sub-plans closed
- [ ] Issues Log reviewed - High/Med issues addressed
- [ ] Full branch audit: `drone @seed audit @branch`
- [ ] Branch memories updated:
  - [ ] `BRANCH.local.json` - full session log
  - [ ] `BRANCH.observations.json` - patterns learned
- [ ] README.md updated (status, architecture, API - if build changed capabilities)
- [ ] Artifacts reviewed (DEV_CENTRAL manages cleanup)
- [ ] Final email to DEV_CENTRAL:
  ```bash
  drone @ai_mail send @dev_central "FPLAN-0355 MASTER COMPLETE" "Full build summary: phases completed, deliverables, remaining issues (if any)"
  ```

**Completion Order:** Memories → README → Email (README before email - don't report complete with stale docs)

**Note:** DEV_CENTRAL will perform their own Seed audit for visibility into the work.

### Definition of Done
1. dev.local.md across the system uses only Issues + Todos sections
2. All code references (template, validation, central writer, compliance) updated for new sections
3. DPLANs support tag classification with fixed vocabulary
4. `plan list` shows tags + AI summaries
5. `plan list --tag X` and `--status X` filtering works
6. DASHBOARD.local.json shows DPLAN status/tag counts
7. DPLAN close → Memory Bank archival produces TRL-named markdown + ChromaDB vector
8. All phases have passing Seed checklists

---

## Close Command

When ALL phases complete and checklist done:
```bash
drone @flow close FPLAN-0355
```
