# Central Systems v1 - Planning Index

*Created: 2025-11-24*
*Scope: Dashboard unification, email automation, bulletin board, central aggregation*

---

## Vision

Transform AIPASS into a command center where:
- All notifications surface to one dashboard
- Low-priority tasks execute autonomously
- System-wide announcements propagate via bulletin board
- We rarely leave this level - just orchestrate

---

## Documents in This Folder

### 1. unified_dashboard_architecture.md
**Date:** 2025-11-24
**Status:** Draft
**Focus:** Single DASHBOARD.local.json with sections for each service

**Key concepts:**
- Each service (Flow, AI_Mail, Memory Bank, Bulletin Board) gets a section
- Services only touch their own section
- Quick status block for instant startup check
- Migration path from fragmented files

**Central files managed:**
- BULLETIN_BOARD_central.json (created)
- Propagation to branch dashboards

---

### 2. ai_mail_autonomous_execution.md
**Date:** 2025-11-24
**Status:** Draft
**Focus:** Priority-based autonomous execution via AI_Mail

**Key concepts:**
- Add `priority` field to email messages (low/normal/high/critical)
- Add `auto_execute` flag
- Delivery hook triggers `claude -p` for low priority + auto_execute
- Branch executes task, sends confirmation

**Approach:** Trigger at delivery time (AI_Mail side)

---

### 3. email_triggered_automation_plan.md
**Date:** 2025-11-19
**Status:** Ready for Implementation (comprehensive)
**Focus:** Watcher-based autonomous execution via PRAX

**Key concepts:**
- PRAX email_watcher.py monitors all branch inboxes
- Triggers `claude -p` when new unread messages detected
- Rate limiting, cooldowns, execution modes (auto/notify/manual)
- Kill switch, audit logging, systemd service
- Phased rollout (MVP → Production → Intelligence)

**Approach:** Watcher monitors inboxes (PRAX side)

**Already tested:**
- Successfully executed autonomous cleanup across 8 branches
- 100% success rate with `--permission-mode acceptEdits`

---

## How These Relate

```
                    ┌─────────────────────────────────────┐
                    │     UNIFIED DASHBOARD ARCHITECTURE   │
                    │     (How branches SEE notifications) │
                    └─────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
        ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
        │  AI_MAIL      │  │  EMAIL        │  │  BULLETIN     │
        │  AUTONOMOUS   │  │  TRIGGERED    │  │  BOARD        │
        │  EXECUTION    │  │  AUTOMATION   │  │  (Future)     │
        │               │  │               │  │               │
        │ (Delivery-    │  │ (Watcher-     │  │ (Propagate    │
        │  triggered)   │  │  triggered)   │  │  to branches) │
        └───────────────┘  └───────────────┘  └───────────────┘
```

**Two approaches to automation:**
1. **AI_Mail side:** Add priority field, trigger at delivery time
2. **PRAX side:** Watcher monitors inboxes, triggers on new messages

These could work together:
- Priority field enables AI_Mail to trigger immediate execution for urgent items
- PRAX watcher handles batch processing on schedule
- Dashboard shows status of both

---

## Central Files (AI_CENTRAL)

| File | Status | Purpose |
|------|--------|---------|
| `PLANS.central.json` | Exists, working | All branch plans aggregated |
| `BULLETIN_BOARD_central.json` | Created 2025-11-24 | System-wide announcements |
| `MARKETPLACE.central.json` | Future | Cross-branch module sharing |
| `MEMORY.central.json` | Future | Memory Bank stats |

---

## Implementation Priority

### Phase 1: Dashboard Unification
- [ ] Define DASHBOARD.local.json schema with sections
- [ ] Migrate Flow's dashboard write to sections.flow
- [ ] Migrate AI_Mail's summary to sections.ai_mail
- [ ] Test with one branch (seed or drone)

### Phase 2: Automation
- [ ] Add priority field to email messages
- [ ] Build email_watcher.py MVP (from detailed plan)
- [ ] Test autonomous execution
- [ ] Add safety features (cooldowns, kill switch)

### Phase 3: Bulletin Board
- [ ] Build bulletin propagator at AIPASS level
- [ ] Push to branch dashboards
- [ ] Acknowledgement tracking
- [ ] Completion flow

### Phase 4: Central Aggregation
- [ ] Build dev_central.py module
- [ ] readme.central.md aggregation
- [ ] devpulse.central.md auto-sync
- [ ] Memory Bank stats surfacing

---

## Key Decisions Needed

1. **Automation trigger:** AI_Mail delivery vs PRAX watcher vs both?
2. **Dashboard format:** Pure JSON or keep some markdown?
3. **Bulletin propagation:** Push on create or pull on startup?
4. **Priority for build:** Dashboard first or automation first?

---

## Related Files

- `/home/aipass/aipass_os/AI_CENTRAL/BULLETIN_BOARD_central.json` - Created
- `/home/aipass/aipass_os/AI_CENTRAL/PLANS.central.json` - Existing
- `/home/aipass/aipass_os/dev_central/devpulse.central.md` - Working aggregation example
- `/home/aipass/apps/modules/dev_central.py` - Empty placeholder for central aggregation code

---

*This folder tracks the evolution of AIPASS central systems - from fragmented notifications to unified orchestration.*
