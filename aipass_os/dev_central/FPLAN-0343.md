# FPLAN-0343 - Scheduler Cron + Telegram Notifications (MASTER PLAN)

**Created**: 2026-02-15
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
echo "# Notepad - FPLAN-0343" > notepad.md
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
Cron-based scheduler that triggers every 30 minutes, sends Telegram notifications via a dedicated scheduler bot, and reports results. No Claude agent spawns - lightweight Python script execution only.

### Reference Documentation
- Existing scheduler code: `/home/aipass/aipass_os/dev_central/assistant/apps/modules/schedule.py` (386 lines)
- Task registry: `/home/aipass/aipass_os/dev_central/assistant/apps/handlers/schedule/task_registry.py` (451 lines)
- Schedule data: `/home/aipass/aipass_os/dev_central/assistant/assistant_json/schedule.json`
- Telegram send pattern (urllib, no deps): `/home/aipass/.claude/hooks/telegram_response.py` lines 245-283 (`send_to_telegram()`)
- Scheduler bot config: `/home/aipass/.aipass/scheduler_config.json`
- Existing bridge bot config pattern: `/home/aipass/.aipass/telegram_config.json`
- Disabled auto-trigger code: `/home/aipass/aipass_core/trigger/apps/handlers/events/startup.py` lines 258-274 (DO NOT re-enable this - cron replaces it)

### Success Criteria
1. Cron fires every 30 minutes
2. Patrick receives Telegram notification "Scheduler triggered at {time}"
3. Scheduler runs `schedule run-due` to process any due tasks
4. Patrick receives Telegram notification with results summary
5. All notifications come from the dedicated @aipass_scheduler_bot (NOT the bridge bot)

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

### Phase 1: Telegram Notification Handler
**Goal:** Build a reusable `telegram_notifier.py` handler that sends messages via the scheduler bot
**Agent Task:** Create `apps/handlers/schedule/telegram_notifier.py` with:
- `load_config()` - loads `/home/aipass/.aipass/scheduler_config.json`
- `send_notification(message)` - sends message to Patrick via scheduler bot using urllib (copy pattern from `/home/aipass/.claude/hooks/telegram_response.py` `send_to_telegram()` function)
- `notify_triggered(event_name)` - sends "🔔 Scheduler: {event_name} triggered at {time}"
- `notify_complete(event_name, summary)` - sends "✅ Scheduler: {event_name} complete\n{summary}"
- `notify_error(event_name, error)` - sends "❌ Scheduler: {event_name} failed\n{error}"
- Use stdlib only (urllib.request, json) - NO external dependencies
- Follow Seed 3-layer patterns
**Deliverables:** `apps/handlers/schedule/telegram_notifier.py`

### Phase 2: Cron Trigger Script
**Goal:** Build the script that cron actually executes every 30 minutes
**Agent Task:** Create `apps/scheduler_cron.py` with:
- Load telegram_notifier
- Send "triggered" notification
- Run `schedule run-due` by importing and calling the schedule module's run-due logic directly (NOT subprocess - import from `apps/modules/schedule.py` or `apps/handlers/schedule/task_registry.py`)
- Collect results: how many tasks were due, how many executed, any failures
- Send "complete" notification with summary
- Log to `logs/scheduler_cron.log` (simple file append with timestamp)
- Handle ALL errors gracefully - if anything fails, send error notification, don't crash silently
- Script must be executable standalone: `python3 apps/scheduler_cron.py`
- IMPORTANT: Add shebang line `#!/usr/bin/env python3` and make executable
**Deliverables:** `apps/scheduler_cron.py`, `logs/` directory created

### Phase 3: Cron Installation + Live Test
**Goal:** Install crontab entry and verify the full loop works
**Agent Task:**
- Install crontab entry: `*/30 * * * * cd /home/aipass/aipass_os/dev_central/assistant && /usr/bin/python3 apps/scheduler_cron.py >> logs/scheduler_cron.log 2>&1`
- Run `scheduler_cron.py` manually once to verify it works end-to-end
- Verify Patrick received both Telegram notifications (triggered + complete)
- Check `logs/scheduler_cron.log` has output
- Verify crontab is installed: `crontab -l`
- Clean up the 1 overdue test task in schedule.json (id: 0d770b0a, "Test backup health" due 2026-02-11)
**Deliverables:** Crontab installed, manual test successful, log output verified

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
drone @ai_mail send @dev_central "PRODUCTION STOPPED: FPLAN-0343" "Phase X halted. Issue: [description]. Attempted: [what was tried]. Awaiting guidance."
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

### Phase 1: [Name]
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Seed checklist passed
- [ ] Sub-plan closed
- [ ] Memories updated
- [ ] Email sent to @dev_central
- **Status:** Pending / In Progress / Complete
- **Notes:** [Outcomes, issues, adjustments]

### Phase 2: [Name]
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Seed checklist passed
- [ ] Sub-plan closed
- [ ] Memories updated
- [ ] Email sent to @dev_central
- **Status:** Pending / In Progress / Complete
- **Notes:** [Outcomes, issues, adjustments]

### Phase 3: [Name]
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Seed checklist passed
- [ ] Sub-plan closed
- [ ] Memories updated
- [ ] Email sent to @dev_central
- **Status:** Pending / In Progress / Complete
- **Notes:** [Outcomes, issues, adjustments]

### Phase 4: [Name]
- [ ] Sub-plan created: FPLAN-____
- [ ] Agent deployed
- [ ] Agent completed
- [ ] Output reviewed
- [ ] Seed checklist passed
- [ ] Sub-plan closed
- [ ] Memories updated
- [ ] Email sent to @dev_central
- **Status:** Pending / In Progress / Complete
- **Notes:** [Outcomes, issues, adjustments]

[Copy template for additional phases]

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
[Patterns discovered that span multiple phases]

**Blockers & Resolutions:**
[Significant blockers and how resolved]

**Adjustments:**
[Changes to planned phases - scope changes, phases added/merged]

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
  drone @ai_mail send @dev_central "FPLAN-0343 MASTER COMPLETE" "Full build summary: phases completed, deliverables, remaining issues (if any)"
  ```

**Completion Order:** Memories → README → Email (README before email - don't report complete with stale docs)

**Note:** DEV_CENTRAL will perform their own Seed audit for visibility into the work.

### Definition of Done
[What specifically defines the project complete?]

---

## Close Command

When ALL phases complete and checklist done:
```bash
drone @flow close FPLAN-0343
```
