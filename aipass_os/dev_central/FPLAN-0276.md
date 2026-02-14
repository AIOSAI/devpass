# FPLAN-0276 - Log Level Classification - User Input vs System Errors

**Created**: 2026-01-30
**Branch**: /home/aipass/aipass_os/dev_central
**Status**: Active
**Type**: Standard Plan

---

## What Are Flow Plans?

Flow Plans (FPLANs) are for **BUILDING** - autonomous construction of systems, features, modules.

**This is NOT for:**
- Research or exploration (use agents directly)
- Quick fixes (just do it)
- Discussion or planning (that happens before creating the FPLAN)

**This IS for:**
- Building features or modules
- Single focused construction tasks
- Sub-plans within a master plan

---

## When to Use This vs Master Plan

| This (Default) | Master Plan |
|----------------|-------------|
| Single focused task | 3+ phases, complex build |
| Self-contained | Roadmap + multiple sub-plans |
| Quick build | Multi-session project |
| One phase of a master | Entire branch/system build |

**Need a master plan?** `drone @flow create "subject" master`

---

## Branch Directory Structure

Use dedicated directories - don't scatter files:

| Directory | Purpose |
|-----------|---------|
| `apps/` | Code (modules/, handlers/) |
| `tests/` | All test files |
| `tools/` | Utility scripts |
| `artifacts/` | Agent outputs |
| `docs/` | Documentation |

---

## Critical: Branch Manager Role

**You are the ORCHESTRATOR, not the builder.**

Your 200k context is precious. Burning it on file reads and code writing risks compaction during autonomous work. Agents have clean context - use them for ALL building.

| You Do (Orchestrator) | Agents Do (Builders) |
|-----------------------|----------------------|
| Create plans | Write code |
| Give instructions | Run tests |
| Review output | Read/modify files |
| Course correct | Research/exploration |
| Update memories | Heavy lifting |
| Send status emails | Single-task execution |

**Pattern:** Instruct agent → Wait for completion → Review output → Next step

---

## Command Reference

When unsure about syntax, use `--help`:

```bash
# Flow - Plan management
drone @flow create . "subject"         # Create plan (. = current dir)
drone @flow close FPLAN-XXXX           # Close plan
drone @flow list                       # List active plans
drone @flow --help                     # Full help

# Seed - Quality gates
drone @seed checklist <file>           # 10-point check on file
drone @seed audit @branch              # Full branch audit
drone @seed --help                     # Full help

# AI_Mail - Status updates
drone @ai_mail send @dev_central "Subject" "Message"
drone @ai_mail --help                  # Full help

# Discovery
drone systems                          # All available modules
drone list @branch                     # Commands for branch
```

---

## Planning Phase

### Goal
Distinguish user input errors from system errors in logging. User typing wrong command (not found, required, invalid) should log as WARNING, not ERROR. This prevents Prax from escalating user typos as system failures.

### Approach
1. **Research** - Identify all logger.error() calls for user validation (DONE: 17 instances, 11 files)
2. **Test on Flow** - Change user validation to logger.warning() and verify (DONE: working)
3. **Email Seed** - Request standard update to clarify log levels
4. **Roll out** - Apply to remaining branches (Prax, Backup, Cortex, Drone)
5. **Seed audit** - Run drone @seed audit @all to catch stragglers

### Reference Documents
- Seed standard: `/home/aipass/seed/standards/CODE_STANDARDS/error_handling.md`
- Prax log_watcher: `/home/aipass/aipass_core/prax/apps/handlers/monitoring/log_watcher.py`

### Log Level Classification (NEW STANDARD)
```
logger.error()   → System failures (file I/O, crashes, dependencies)
logger.warning() → User input issues (not found, required, invalid format)
logger.info()    → Successful operations, workflow events
```

---

## Agent Preparation (Before Deploying)

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

---

## Agent Instructions Template
```
You are working at [BRANCH_PATH].

TASK: [Specific single task]

CONTEXT:
- [What they need to know]
- Reference: [planning docs, existing code to study]
- First, READ the relevant files to understand current structure

DELIVERABLES:
- [Specific file or output expected]
- Tests → tests/
- Reports/logs → artifacts/reports/ or artifacts/logs/

CONSTRAINTS:
- Follow Seed standards (3-layer architecture)
- Do NOT modify files outside your task scope
- CROSS-BRANCH: Never modify other branches' files unless explicitly authorized by DEV_CENTRAL
- 2-ATTEMPT RULE: If something fails twice, note the issue and move on
- Do NOT go down rabbit holes debugging

WHEN COMPLETE:
- Verify code runs without syntax errors
- List files created/modified
- Note any issues encountered (with what was attempted)
```

---

## Execution Log

### 2026-01-30
- [x] Created FPLAN-0276
- [x] Research agents deployed: logger usage, Prax log_watcher, CLI methods
- [x] Found: 17 instances across 11 files (8 modules, 9 handlers)
- [x] Agent deployed to Flow: Update user validation logger.error → logger.warning
- [x] Flow test passed: Log shows WARNING, Prax won't escalate
- [x] DEV_CENTRAL memories updated
- [ ] Email Seed about standard update (NEXT SESSION)
- [ ] Roll out to remaining branches (NEXT SESSION)
- [ ] Seed audit @all (NEXT SESSION)

**Log Pattern:** Task → Agent → Outcome → Quality check → Next

**If production stops (critical blocker):**
```bash
drone @ai_mail send @dev_central "PRODUCTION STOPPED: FPLAN-0276" "Issue: [description]. Attempted: [what was tried]. Awaiting guidance."
```

---

## Notes

**Session 49 Notes:**
- User input errors and system errors were both logged as ERROR - causing Prax to escalate typos
- Seed's current standard says use logger.error for "validation errors" - ambiguous
- CLI display still shows "ERROR" to user (cli.error()) - that's correct (user feedback)
- System log now shows WARNING - Prax log_watcher only escalates ERROR level
- Handlers logging directly violates Seed standard ("handlers throw, modules log")
- 9 of 17 instances are in handlers - those need refactoring too (future work)

**Branches needing updates:**
- Flow: ✅ DONE (close_plan, restore_plan, aggregate_central)
- Prax: 4 instances (log_watcher, branch_detector, file_watcher)
- Backup: 2 instances (integrations.py)
- Cortex: 1 instance (registry.py)
- Drone: 2 instances (json_handler, registry ops)

---

## Completion Checklist

### Before Closing

- [ ] All goals achieved
- [ ] Agent output reviewed and verified
- [ ] Seed checklist on new code: `drone @seed checklist <file>`
- [ ] Branch memories updated:
  - [ ] `BRANCH.local.json` - session/work log
  - [ ] `BRANCH.observations.json` - patterns learned (if any)
- [ ] README.md updated (if build changed status/capabilities)
- [ ] Status email sent to DEV_CENTRAL:
  ```bash
  drone @ai_mail send @dev_central "FPLAN-0276 Complete" "Summary of what was done, any issues, outcomes"
  ```

**Completion Order:** Memories → README → Email (README before email - don't report complete with stale docs)

### Definition of Done
[What specifically defines complete for this plan?]

---

## Close Command

When all boxes checked:
```bash
drone @flow close FPLAN-0276
```
