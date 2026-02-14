# Feature Design: Scheduled Follow-ups

**Feature:** Assistant Scheduled Follow-ups
**Date:** 2026-02-04
**Author:** Patrick
**Status:** [x] Draft [ ] Review [ ] Approved [x] Building [x] Done

---

## Vision
_Why does this matter?_

Fire-and-forget follow-ups. Schedule a check, forget about it, get a report when it runs.


---

## Expected Result
_What will users be able to do?_

- Schedule task with future date
- @assistant auto-runs when due
- Email report arrives


---

## Use Cases

1. "Follow up on memory rolloff in 7 days"
2. "Check backup health weekly"
3. "Verify Telegram bridge in 3 days"

---

## Scope

**In:**
- Create/list/delete scheduled tasks
- Run due tasks (cron or manual)
- Email report to recipient

**Out:**
- Complex cron syntax (keep simple)
- GUI
- Recurring (MVP = one-time)

---

## Technical Notes
_Files, commands, trigger_

**Built 2026-02-05:**
- `assistant/apps/modules/schedule.py` - CLI module (create/list/delete/run-due)
- `assistant/apps/handlers/schedule/task_registry.py` - Storage layer
- `assistant/assistant_json/schedule.json` - Task storage
- `trigger/apps/handlers/events/startup.py` - Auto catch-up on login

**Commands:**
```bash
drone @assistant schedule create "@recipient" "Task" "Message" "7d"
drone @assistant schedule list
drone @assistant schedule run-due
```

**Automation:**
- Trigger startup handler runs `run-due` on every login
- Uses `--dispatch` flag so recipients ACT (not just get informed)
- Reports go to `@dev_central`

---

## Open Questions

- [x] Date format? → "7d", "1w", "2w", "YYYY-MM-DD" (date only, no time yet)
- [x] Storage location? → `assistant_json/schedule.json`

---

## Success Criteria

- [x] CLI creates task
- [x] run-due executes it
- [x] Report email arrives

---

## Known Issues / Follow-ups

**2026-02-05: Agent cascade on first test**
- Problem: 5 test tasks fired, each spawned agent, each agent triggered startup, which ran catch-up again
- Result: 15+ agents spawned simultaneously (45%+ RAM)
- Fix needed: Rate limiting or "processing" lock to prevent re-dispatch of same task

**2026-02-05: Auto-trigger parked**
- Built: filelock, AIPASS_SPAWNED env var, dispatching status
- Problem: Startup fires on every logger import, not once per login
- Parked: Auto-trigger disabled, manual `run-due` works fine
- Resume: Need "once per session" event instead of startup hook

**Future improvements:**
- [ ] Time support (currently date-only)
- [x] Lock mechanism: filelock + dispatching status (DONE)
- [ ] Auto-trigger: proper once-per-login event
- [ ] Recurring tasks (weekly, monthly)

---

## Notes




---
