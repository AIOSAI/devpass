# FPLAN-0314 - Speakeasy Voice-to-Text Rebuild (MASTER PLAN)

**Created**: 2026-02-11
**Branch**: /home/aipass/speakeasy
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
echo "# Notepad - FPLAN-0314" > notepad.md
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
Complete voice-to-text system rebuilt to AIPass standards. Press hotkey, speak, text appears in any application. Runs 100% locally with OpenAI Whisper (faster-whisper). Full 3-layer architecture with modules, handlers, tests, and Seed compliance.

### Reference Documentation
- Old codebase: `/home/aipass/speakeasy(disabled)/whisper-writer/` (WhisperWriter by savbell, GPL)
- Example branches: drone, ai_mail, trigger (3-layer architecture patterns)
- Seed standards: 13 checks (architecture, cli, diagnostics, documentation, encapsulation, error_handling, handlers, imports, json_structure, modules, naming, testing, trigger)

### Success Criteria
- Seed audit score 80%+
- Hotkey triggers recording, Whisper transcribes, text appears at cursor
- All core features: VAD, continuous mode, cursor lock, system tray
- Tests in tests/ directory
- Clean 3-layer architecture

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

### Phase 1: Foundation & Seed Compliance
**Goal:** Fix json_handler.py paths, achieve 100% Seed compliance, set up requirements.txt, build entry point
**Agent Task:** Fix json_handler.py to use Speakeasy paths. Update speakeasy.py entry point. Create proper requirements.txt. Ensure all __init__.py files correct.
**Deliverables:** Fixed json_handler.py, updated speakeasy.py, requirements.txt, 100% Seed on existing files

### Phase 2: Audio Engine
**Goal:** Build audio capture, WebRTC VAD, and faster-whisper transcription as handlers
**Agent Task:** Create audio_handler.py (sounddevice capture, WebRTC VAD), transcription_handler.py (faster-whisper integration), audio_module.py (orchestrates recording → transcription pipeline)
**Deliverables:** apps/handlers/audio_handler.py, apps/handlers/transcription_handler.py, apps/modules/audio_module.py

### Phase 3: Hotkey & Text Input
**Goal:** Build hotkey detection and text injection system
**Agent Task:** Create hotkey_handler.py (pynput/evdev listener), input_handler.py (text injection via pynput), input_module.py (orchestrates hotkey → record → type pipeline)
**Deliverables:** apps/handlers/hotkey_handler.py, apps/handlers/input_handler.py, apps/modules/input_module.py

### Phase 4: UI & Desktop Integration
**Goal:** Build PyQt5 overlay, system tray, cursor lock
**Agent Task:** Create ui_handler.py (PyQt5 status window, system tray), cursor_lock_handler.py (xdotool cursor locking), ui_module.py (orchestrates UI state)
**Deliverables:** apps/handlers/ui_handler.py, apps/handlers/cursor_lock_handler.py, apps/modules/ui_module.py

### Phase 5: Configuration & Service
**Goal:** Build config system and systemd service
**Agent Task:** Create config_handler.py (YAML config loading, schema validation), service files (systemd user unit), CLI interface in speakeasy.py (start/stop/status commands)
**Deliverables:** apps/handlers/config_handler.py, tools/speakeasy.service, updated speakeasy.py with CLI

### Phase 6: Testing, Integration & Polish
**Goal:** Full integration testing, Seed audit, documentation
**Agent Task:** Create test files for all modules/handlers. Integration test for full pipeline. Update README.md. Final Seed audit. GPL attribution for WhisperWriter.
**Deliverables:** tests/*.py, updated README.md, docs/architecture.md, Seed audit 80%+

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
drone @ai_mail send @dev_central "PRODUCTION STOPPED: FPLAN-0314" "Phase X halted. Issue: [description]. Attempted: [what was tried]. Awaiting guidance."
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

### Phase 1: Foundation & Seed Compliance
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed
- [x] Seed checklist passed (95% → fixed print() → expect higher)
- **Status:** Complete
- **Notes:** Fixed json_handler.py paths (SEED→SPEAKEASY), created requirements.txt, removed unused imports, removed print() statement. Seed audit: 95%

### Phase 2: Audio Engine
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed
- [ ] Seed checklist passed (deferred to Phase 6)
- **Status:** Complete
- **Notes:** Created audio_handler.py (195 lines), transcription_handler.py (165 lines), audio_module.py (223 lines). All imports verified. faster-whisper installed. WebRTC VAD + sounddevice capture working.

### Phase 3: Hotkey & Text Input
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed
- [ ] Seed checklist passed (deferred to Phase 6)
- **Status:** Complete
- **Notes:** Created hotkey_handler.py (5.3K), input_handler.py (4.3K), cursor_lock_handler.py (5.4K), input_module.py (6.5K). All module API tests passed. Handler guard working correctly.

### Phase 4: UI & Desktop Integration
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed
- [ ] Seed checklist passed (deferred to Phase 6)
- **Status:** Complete
- **Notes:** Created ui_handler.py (315 lines - tray icon, status window, notifications, sound playback), ui_module.py (278 lines - UI state orchestration). Fixed logger extra={"args": args} key conflict. PyQt5 Qt attribute Pyright warnings are expected false positives.

### Phase 5: Configuration & Service
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed
- [ ] Seed checklist passed (deferred to Phase 6)
- **Status:** Complete
- **Notes:** Created config_handler.py (263 lines - YAML config load/save/validate/merge), config_module.py (292 lines - config orchestration with CLI), config.yaml (30 lines - default config), tools/speakeasy.service (systemd unit). Updated speakeasy.py with start/stop/status commands. Fixed PyQt6→PyQt5 import.

### Phase 6: Testing, Integration & Polish
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed
- [x] Seed checklist passed (99%)
- **Status:** Complete
- **Notes:** Created 9 test files (197 passed, 4 skipped). Updated README.md with architecture/features/usage. Created docs/architecture.md. Added LICENSE (GPL-3.0) with WhisperWriter attribution. Refactored all 3 modules to thin orchestration (Modules 100%). Final Seed: 99%.

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

- [x] All phases complete
- [x] All sub-plans closed
- [x] Issues Log reviewed - High/Med issues addressed
- [x] Full branch audit: `drone @seed audit @branch` (99%)
- [x] Branch memories updated:
  - [x] `BRANCH.local.json` - full session log
  - [ ] `BRANCH.observations.json` - patterns learned
- [x] README.md updated (status, architecture, API - if build changed capabilities)
- [x] Artifacts reviewed (DEV_CENTRAL manages cleanup)
- [ ] Final email to DEV_CENTRAL:
  ```bash
  drone @ai_mail send @dev_central "FPLAN-0314 MASTER COMPLETE" "Full build summary: phases completed, deliverables, remaining issues (if any)"
  ```

**Completion Order:** Memories → README → Email (README before email - don't report complete with stale docs)

**Note:** DEV_CENTRAL will perform their own Seed audit for visibility into the work.

### Definition of Done
[What specifically defines the project complete?]

---

## Close Command

When ALL phases complete and checklist done:
```bash
drone @flow close FPLAN-0314
```
