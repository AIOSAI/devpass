# DPLAN-001: Actions - Autonomous Schedulable Plugin System

> **Actions** (`@assistant actions`) - Self-contained, toggleable action plugins that scale from simple text reminders to complex autonomous workflows. Each action = one plugin, plug in and it works.

## Vision

Build an **Actions** system where every scheduled/automated action is a self-contained plugin that can be:
- **Created** easily via drone command or ASSISTANT conversation
- **Listed** with status (enabled/disabled, next run, last run)
- **Toggled** on/off without touching code (`drone @assistant actions enable/disable <id>`)
- **Scaled** from 1 to 10,000 plugins without architectural changes

**The spectrum of actions (simple to complex):**
1. **Text reminders** - "Follow up on FPLAN-0056 in 1 week" (one-shot)
2. **Recurring checks** - "Run system health check every Sunday at 3pm"
3. **Data gathering** - "After 1 week, generate report on how X performed"
4. **Test suites** - "Run weekly unit tests, produce report"
5. **Autonomous workflows** - Complex multi-step automations

**Why actions as plugins, not just handlers:**
- Handlers are internal plumbing. Actions are user-facing units.
- "Plug it in, it works. Unplug it, it stops." Zero code changes.
- Each action is independent - adding one never breaks another.
- The system (Trigger event bus, handlers, scheduler) is the engine. Actions are what you mount on it.

**Command interface:** `drone @assistant actions <subcommand>`
- Args may vary by handler routing as complexity grows, but the base pattern is consistent.
- ASSISTANT owns and manages all actions as the operations manager.

## Current State

**What exists today:**

1. **TRIGGER** (`/home/aipass/aipass_core/trigger/`)
   - Event bus with pub/sub pattern (`trigger.fire()`, `trigger.on()`)
   - 11 event handlers in `handlers/events/`, each its own file
   - Single registration point: `registry.py` → `setup_handlers()`
   - No toggle mechanism (except Medic which has its own on/off)
   - No CLI for listing/enabling/disabling individual handlers

2. **ASSISTANT Scheduler** (`/home/aipass/aipass_os/dev_central/assistant/`)
   - Fire-and-forget scheduled tasks via `schedule.json`
   - Cron triggers every 30 min (scheduler_cron.py + assistant_wakeup.py)
   - Tasks have status (pending/dispatching/completed) but no enable/disable
   - Telegram notifications working (assistant_bot + scheduler_bot)

3. **Gap:** No unified Actions interface. No on/off toggling. No drone commands for managing actions. No self-describing action plugin format.

## What Needs Building

### Core Action Infrastructure
- [ ] **Action format** - Standard structure for an action plugin file (metadata + logic)
- [ ] **Action registry** - JSON registry tracking all actions with state (enabled/disabled, schedule, last_run, next_run)
- [ ] **Action loader** - Auto-discovers action plugin files, reads metadata, registers them
- [ ] **Toggle mechanism** - Enable/disable without code changes (registry state, not file renaming)

### CLI Interface
- [ ] `drone @assistant actions list` - Show all actions with status, schedule, last/next run
- [ ] `drone @assistant actions enable <id>` - Turn on an action
- [ ] `drone @assistant actions disable <id>` - Turn off an action
- [ ] `drone @assistant actions add "description" --due "1w Sunday" [--recurring]` - Create simple action
- [ ] `drone @assistant actions status <id>` - Detailed info on one action
- [ ] `drone @assistant actions run <id>` - Force-run an action now (for testing)
- Note: Args will evolve as handler routing grows more complex

### Scheduling Layer
- [ ] **One-shot scheduling** - "Do X at time Y" then done
- [ ] **Recurring scheduling** - "Do X every Y" (daily, weekly, custom cron)
- [ ] **Natural language timing** - "in 1 week", "next Sunday afternoon", "every Monday 9am"
- [ ] **Cron integration** - How actions get triggered (existing cron? new approach?)

### Action Types (progressive complexity)
- [ ] **Type 1: Reminder** - Text message at scheduled time (Telegram/ai_mail)
- [ ] **Type 2: Check** - Run a command, report result
- [ ] **Type 3: Report** - Gather data, format, deliver
- [ ] **Type 4: Workflow** - Multi-step autonomous sequence
- [ ] **Type 5: Custom** - Full Python handler for complex logic

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| **Naming** | ~~events / routines / jobs / plugins / automations~~ | **ACTIONS** | Decided. `@assistant actions`. Clean, no conflicts, natural in conversation. |
| **Where it lives** | Trigger extension / ASSISTANT module / New system | **ASSISTANT** | Actions are ASSISTANT's domain. Ops manager owns the actions. |
| **Action format** | Python file with metadata dict / YAML config + handler / JSON definition | TBD | Simple actions shouldn't need Python |
| **Storage** | One file per action / Central registry JSON / Both | TBD | Registry for state, files for logic? |
| **Scheduling engine** | Extend existing cron / APScheduler / Custom | TBD | Existing cron works but is basic |
| **Simple vs complex creation** | All via CLI / Simple via CLI, complex via file / Mixed | TBD | Text reminders shouldn't need a .py file |

### Open Questions
1. ~~What's the name?~~ **DECIDED: Actions** (`@assistant actions`)
2. ~~Does this extend Trigger, live in ASSISTANT, or become its own system?~~ **DECIDED: Lives in ASSISTANT** - actions are the ops manager's domain
3. Should simple actions (reminders) be just JSON entries (no Python file needed)?
4. How do complex action plugins define their multi-step workflows?
5. What's the relationship between existing Trigger handlers and new action plugins?

## Status
- [x] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes

### Session 12 - 2026-02-15 (Patrick + ASSISTANT via Telegram)

**Origin:** Patrick asked about the event/scheduler/trigger system - do events have on/off? Are they plugins?

**Key insights from conversation:**
- Current handlers ARE conceptually plugins - they're just missing toggle infrastructure
- Patrick's vision: "we just want to plug this event in and it's going to work with the system, easy, fast, separate"
- Scale thinking: plan for 10,000 events even if we start with 10
- The system (Trigger bus, handlers, scheduler) is the engine. Plugins mount on it.
- Simple creation flow: `drone @assistant actions add "follow up on FPLAN-0056" --due "1w Sunday"`
- Each plugin independent - turn on, turn off, add, remove, no side effects

**Patrick's direction:**
- Not building tonight - developing the idea first
- Will become a Master Flow Plan (FPLAN) when ready for execution
- ~~Patrick thinking on the name~~ → **DECIDED: Actions** (`@assistant actions`)
- Naming shortlist was: actions, runners, routines. Actions won - clean, no conflicts, natural in conversation, no typing issues
- "routines" eliminated - Patrick noted it's a dyslexic "trigger" and hard to type
- "runners" eliminated - CI/test runner baggage, "running runners" redundancy
- Actions confirmed as ASSISTANT module: `drone @assistant actions <subcommand>`
- Args will build out as handler routing grows more complex - base pattern is set
- Where it lives: ASSISTANT branch. Actions = ops manager's domain.

**Decisions locked in this session:**
1. Name: **Actions**
2. Command: `drone @assistant actions`
3. Home: ASSISTANT branch (not Trigger, not standalone)

**Still open for next session:**
- Action plugin file format (Python vs JSON vs mixed)
- Storage approach (files, registry, or both)
- Scheduling engine (extend cron or build new)
- How simple vs complex actions differ in structure

---
*Created: 2026-02-15*
*Updated: 2026-02-15*
