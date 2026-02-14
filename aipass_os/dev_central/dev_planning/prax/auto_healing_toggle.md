# Medic - Auto-Healing System

**Created:** 2026-02-12 | Session 94
**Status:** Name decided, architecture confirmed, awaiting Seed + Trigger input
**Participants:** Patrick + Claude

---

## The Problem

When heavy dev work happens (e.g. Speakeasy rebuild with 15+ agents), the auto-healing error dispatch system creates a cascade:
- Many agents = many errors (expected during builds)
- Log watcher detects each error
- Auto-dispatches investigation to each affected branch
- More agents spawn = more errors = more dispatches
- System overwhelm / crash

Currently disabled (Feb 11) by killing the daemon. No proper on/off mechanism exists.

---

## Key Decisions So Far

### 1. This belongs to Prax, not a new system
- Prax IS the watcher. Building something separate would reinvent Prax.
- The auto-healing dispatch is a Prax capability/module, not a standalone system.
- Question: What do we call this Prax module? "Medic" is a candidate.

### 2. We need an on/off toggle
- Simple switch: `drone @prax medic on|off|status` (or whatever we name it)
- Config file as source of truth (JSON state, persistent)
- Per-branch muting possible (mute @speakeasy during rebuild, keep watching others)
- Drone command wraps the toggle

### 3. DEV_CENTRAL is NEVER auto-triggered
- Hard rule. Already in error_detected handler but worth auditing all pathways.
- Patrick and Claude control the flow. Nobody dispatches us.

### 4. Small increments only
- System is working and in best state so far
- Past prototype stage - perfecting now
- No cowboy changes. Test everything.

---

## Name: MEDIC (Decided)

**The system:** Auto-healing error dispatch (log watching + error detection + auto-dispatch to fix)
**Name:** Medic
**Decision date:** 2026-02-12

**Why Medic:**
- Rolls off the tongue easily (Patrick voice-tested all candidates)
- Medical metaphor: detect problem → diagnose → treat → report
- No collisions with existing terms (Doc clashes with "docs", Sentinel overlaps with Prax's watcher identity)
- Works in all contexts: "turn medic on", "medic caught 3 errors", "medic status"
- Always makes sense regardless of context

**Rejected:** Sentinel (Prax overlap), Triage (hard to say), Doc (clashes with docs), Apollo (too big - sounds like a branch name), Guard (too generic), Reflex (good but Medic won), Patrol (generic), Heal/Mend (incomplete)

**Commands:** `drone @trigger medic on|off|status|mute @branch|unmute @branch`

---

## What Exists Today

### Architecture
1. **Log Watcher** (Event Producer) - `trigger/apps/handlers/log_watcher.py`
   - Monitors `aipass_core/*/logs/*.log` and `system_logs/*.log`
   - Detects ERROR/CRITICAL entries
   - Fires `error_detected` events

2. **Error Handler** (Event Consumer) - `trigger/apps/handlers/events/error_detected.py`
   - Receives events, sends dispatch emails to affected branches
   - Rate limiting: 3 dispatches per branch per 10 min
   - Deduplication via hash persistence (27 hashes in trigger_data.json)

3. **Log Watcher Daemon** - `trigger/tools/run_branch_log_watcher.py`
   - Persistent process that keeps the watcher alive
   - Last stopped: 2026-02-11 18:29:59

### Current toggle mechanism: None
- `trigger_config.json` has `"enabled": true` but it's NOT wired to anything
- On/off is literally process alive vs dead
- No state file, no flag, no command

### Old reference: cortex_on_off.py
- Found at `/home/aipass/Downloads/cortex_on_off.py` (original)
- Also at `/home/aipass/input_x/a.i/legacy/AIPass_Seed/cortex_on_off.py` (legacy)
- Evolved into `/home/aipass/input_x/prax/prax_on_off.py` (v1.2.0, 542 lines)
- Pattern: JSON registry + toggle_module() + scan + preserve state
- Module-level granularity (Python import hooks) - different scope than what we need
- Useful reference for the config/toggle pattern, not the implementation

---

## What We Need to Build

### Phase 1: Simple Toggle (Minimum Viable)
- [ ] Wire `trigger_config.json` enabled flag to log watcher behavior
- [ ] Drone command: `drone @trigger medic on|off|status`
- [ ] State persists across restarts
- [ ] Status shows: on/off, last error detected, dispatch count

### Phase 2: Per-Branch Control
- [ ] Mute specific branches: `drone @trigger medic mute @speakeasy`
- [ ] Unmute: `drone @trigger medic unmute @speakeasy`
- [ ] Muted branches skip dispatch but still log errors

### Phase 3: Better Visibility (Patrick's needs)
- [ ] Patrick needs to see what's being triggered from notifications
- [ ] Quick status: all running Claude agents + which branch
- [ ] Quick kill: `drone kill @branch` or similar
- [ ] Notification clarity: branch name prominent, reason visible
- [ ] Claude Office as potential visual layer

---

## Process Visibility Gap (Related)

Patrick's concern: "Sometimes I think you're being triggered but I don't know"
- Notifications don't clearly distinguish DEV_CENTRAL vs other branches
- No quick way to see all running agents
- No quick way to kill a runaway process
- Claude Office project could provide visual monitoring interface

---

## Architecture Decisions (Session 94)

**Prax vs Trigger ownership:**
- Prax = observer. Doesn't take actions. Watches, reports, analyzes. Future: system-wide dashboard/UI.
- Trigger = actor. Performs actions. Fires events, handles responses, dispatches.
- **Decision: Medic toggle lives in Trigger** (Trigger is step 1 in the chain, turning off at source stops everything downstream)
- Prax's future role: surface Medic's on/off state in a UI, but doesn't own the logic

**Current chain:** Trigger watches → Trigger fires events → Trigger decides → AI Mail transports → Agent spawns
**Prax involvement:** Zero (just writes logs that Trigger reads)

## Open Questions

1. ~~Does the toggle live in Prax or Trigger?~~ **DECIDED: Trigger**
2. ~~Naming?~~ **DECIDED: Medic**
3. Should we audit ALL auto-dispatch pathways to confirm DEV_CENTRAL protection?
4. Trigger's reply pending - what did they actually do on Feb 11?
5. Seed's reply pending - separation of concerns review

---

## Notes

- Email sent to @trigger requesting status update (Session 94)
- System is currently OFF and stable
- Patrick: "We're past the prototype experimental stage. We're really looking to perfect this."
- Any changes: small increments, tested like crazy
