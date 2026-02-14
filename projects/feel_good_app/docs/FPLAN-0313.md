# FPLAN-0313 - Feel Good App v2 - EAS Build + Notifications + Health + AI (MASTER PLAN)

**Created**: 2026-02-10
**Branch**: /home/aipass/projects/feel_good_app
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
echo "# Notepad - FPLAN-0313" > notepad.md
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
Transform the Feel Good App from an Expo Go prototype into a standalone Android APK with push notification reminders, Health Connect biometric integration, and an AI correlation engine that finds patterns between mood and health data.

### Reference Documentation
- `docs/01_framework_decision.md` - Framework choices (Expo SDK 54, React Native 0.81.5)
- `docs/02_health_apis.md` - Health Connect data types, ring integration, permission model
- `docs/03_market_analysis.md` - Competitive gap analysis, AI differentiator vision
- `docs/build_log.md` - Phase 1-3 decisions, issues, workarounds
- `app/src/features/health/types.ts` - Health data type definitions (already built)
- `app/src/features/insights/types.ts` - Correlation and nudge type definitions (already built)
- `app/src/store/moodStore.ts` - Zustand store pattern to follow
- `app/app/(tabs)/settings.tsx` - Notification toggle UI (already built, needs wiring)
- `app/app/(tabs)/insights.tsx` - Insights tab with placeholder cards to replace

### Success Criteria
1. APK installs on Patrick's Samsung Galaxy FE 24 without Expo Go
2. Scheduled notifications fire at configured times (morning + evening)
3. Health Connect reads real heart rate, steps, sleep, HRV from device
4. Insights tab shows correlations between mood entries and health metrics
5. App works offline, all data stays on-device

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

### Phase 1: EAS Development Build (Android APK)
**Goal:** Get a standalone APK that installs on Patrick's Samsung without Expo Go or dev server
**Agent Task:**
- Install `eas-cli` globally, `expo-dev-client` in project
- Configure `app.json` with `android.package` (com.aipass.feelgoodapp)
- Create `eas.json` with development profile (APK output, no credentials needed)
- Add `expo-dev-client` to plugins
- Run `eas build:configure` then `eas build --profile development --platform android`
- NOTE: May need Patrick to create Expo account if none exists. Check `eas whoami` first.
**Deliverables:** `eas.json`, updated `app.json`, downloadable APK URL
**Potential Blocker:** Expo account creation requires Patrick interaction

### Phase 2: Push Notifications (Scheduled Reminders)
**Goal:** Morning and evening mood check-in notifications that actually fire on the device
**Agent Task:**
- Install `expo-notifications` (SDK 54 compatible)
- Create notification service: `src/features/notifications/services/notificationService.ts`
  - `setupNotificationChannel()` - Android notification channel
  - `requestPermissions()` - Android 13+ opt-in
  - `scheduleMoodCheckin(hour, minute, type)` - Daily recurring trigger
  - `cancelAllScheduled()` and `listScheduled()`
- Create notification store: `src/store/notificationStore.ts` (Zustand + AsyncStorage)
  - Persists: enabled state, nudge frequency, scheduled notification IDs
- Wire Settings tab: notification toggle + nudge frequency → actual scheduled notifications
  - Off = cancel all, Gentle = 2x/day (9am, 8pm), Moderate = 4x/day, Active = smart timing
- Add `expo-notifications` to app.json plugins
- Add `SCHEDULE_EXACT_ALARM` permission for Android
- Handle notification tap → open app to Log tab
**Deliverables:** notificationService.ts, notificationStore.ts, updated settings.tsx, updated app.json

### Phase 3: Health Connect Integration (Android)
**Goal:** Read heart rate, steps, sleep, HRV from Android Health Connect into the app
**Agent Task:**
- Install `react-native-health-connect` v3.5.0 + `expo-health-connect` + `expo-build-properties`
- Configure app.json plugins (expo-health-connect, expo-build-properties with compileSdk 35, minSdk 26)
- Create health service: `src/features/health/services/healthConnectService.ts`
  - `initHealthConnect()` - Initialize SDK
  - `requestHealthPermissions()` - Runtime permission request
  - `readHeartRate(startDate, endDate)` - Heart rate samples
  - `readSteps(startDate, endDate)` - Step counts
  - `readSleep(startDate, endDate)` - Sleep sessions with stages
  - `readHRV(startDate, endDate)` - HRV RMSSD values
  - `getDailySummary(date)` - Aggregate all metrics for a day
- Create health store: `src/store/healthStore.ts` (Zustand + AsyncStorage)
  - Stores: daily health summaries, last sync timestamp, permission status
  - Method: `syncHealthData()` - pulls latest from Health Connect
- Wire Settings tab: Health Connect toggle → permission request + data sync
- Wire Insights tab: Replace "Health Correlations" placeholder with real data display
  - Show daily health summary (avg HR, steps, sleep hours, HRV)
- Add health data to History tab entries (show health context alongside mood)
**Deliverables:** healthConnectService.ts, healthStore.ts, updated insights.tsx, updated settings.tsx, updated app.json

### Phase 4: AI Correlation Engine
**Goal:** Detect patterns between mood and health metrics, generate smart nudges
**Agent Task:**
- Install `simple-statistics` v7.8.8
- Create correlation engine: `src/features/insights/services/correlationEngine.ts`
  - `computeCorrelations(moodEntries, healthSummaries)` - Pearson correlation across all metric pairs
  - `detectPatterns(correlations)` - Translate raw correlations into human-readable insights
  - `generateNudges(patterns, currentHealth)` - Proactive suggestions based on detected patterns
  - Works with ANY amount of data (5 entries or 500)
  - Confidence scoring: "strong" (r > 0.7), "moderate" (r > 0.4), "weak" (r < 0.4)
- Create insights computation hook: `src/features/insights/hooks/useCorrelations.ts`
  - Combines mood store + health store data
  - Returns: top correlations, trend analysis, nudge suggestions
- Wire Insights tab: Replace both placeholder cards
  - "Health Correlations" → real correlation cards with confidence badges
  - "Smart Nudges" → AI-generated suggestions based on patterns
- Example insights the engine should produce:
  - "Your mood is 73% higher on days you sleep 7+ hours"
  - "Low HRV mornings correlate with stressed moods by afternoon"
  - "Walking 8000+ steps shows moderate correlation with 'good' mood entries"
**Deliverables:** correlationEngine.ts, useCorrelations.ts, updated insights.tsx, simple-statistics in package.json

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
drone @ai_mail send @dev_central "PRODUCTION STOPPED: FPLAN-0313" "Phase X halted. Issue: [description]. Attempted: [what was tried]. Awaiting guidance."
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

### Phase 1: EAS Development Build
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed
- **Status:** Complete (config only — APK build needs Patrick's Expo account)
- **Notes:** eas-cli v16.32.0 installed globally. eas.json + app.json configured. expo-dev-client, expo-notifications, react-native-health-connect, expo-health-connect, expo-build-properties, simple-statistics all installed. Android package: com.aipass.feelgoodapp.

### Phase 2: Push Notifications
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed
- **Status:** Complete
- **Notes:** notificationService.ts (channel setup, permission request, daily scheduling for off/gentle/moderate/active), notificationStore.ts (Zustand persist), settings.tsx wired, root _layout.tsx handles channel + sync on mount. 0 TS errors. Caught deprecated API (shouldShowBanner/shouldShowList required in v0.32).

### Phase 3: Health Connect Integration
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed
- **Status:** Complete
- **Notes:** healthConnectService.ts (init, permissions, read HR/HRV/steps/sleep, daily summary aggregation, sleep quality scoring), healthStore.ts (Zustand persist), settings.tsx Health Connect toggle wired, insights.tsx shows real health data grid. 0 TS errors. TimeRangeFilter type workaround (derived from ReadRecordsOptions).

### Phase 4: AI Correlation Engine
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed
- **Status:** Complete
- **Notes:** correlationEngine.ts (Pearson correlations via simple-statistics, mood-only patterns, human-readable insights, smart nudge generation), useCorrelations.ts hook (useMemo-wrapped), insights.tsx shows patterns section + nudge cards + "linked to mood" badges on health metrics. Works with 0 entries through 500+. 0 TS errors.

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
  drone @ai_mail send @dev_central "FPLAN-0313 MASTER COMPLETE" "Full build summary: phases completed, deliverables, remaining issues (if any)"
  ```

**Completion Order:** Memories → README → Email (README before email - don't report complete with stale docs)

**Note:** DEV_CENTRAL will perform their own Seed audit for visibility into the work.

### Definition of Done
1. APK installed and running on Samsung Galaxy FE 24 without Expo Go
2. Mood check-in notifications firing at scheduled times
3. Health Connect reading real biometric data from device
4. Insights tab showing correlation analysis between mood and health
5. All data persists locally via AsyncStorage
6. Build log updated with Phase 4 documentation
7. v4.0 snapshot created

---

## Close Command

When ALL phases complete and checklist done:
```bash
drone @flow close FPLAN-0313
```
