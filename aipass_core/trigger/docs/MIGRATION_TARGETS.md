# Migration Targets

**Event handling code that should move FROM other branches TO Trigger**

---

## Priority 1: Immediate Candidates ✅ COMPLETED

### Flow: registry_monitor.py ✅ MIGRATED

**Status:** COMPLETED (Phase 1, Session 7)

**What was migrated:**
- Created `trigger/apps/handlers/events/plan_file.py` with 3 handlers
- Flow's PlanFileWatcher now fires `trigger.fire('plan_file_created/deleted/moved')`
- Trigger handlers update Flow's registry - decoupled, clean

**Events added:** `plan_file_created`, `plan_file_deleted`, `plan_file_moved`

---

### Prax: watcher.py (module discovery)

**Location:** `/home/aipass/aipass_core/prax/apps/handlers/discovery/watcher.py`

**Status:** PENDING - Lower priority, module discovery is tightly coupled to Prax

**What it does:**
- Watches Python files in ECOSYSTEM_ROOT
- Auto-registers new modules to registry

---

### Prax: log_watcher.py ✅ MIGRATED

**Status:** COMPLETED (Phase 2, Session 11)

**What was migrated:**
- Created `trigger/apps/handlers/watchers/log_watcher.py` - centralized log watching
- Created `trigger/apps/handlers/events/error_logged.py` - sends AI_Mail on errors
- Created `trigger/apps/handlers/events/warning_logged.py` - hook for future aggregation

**Events added:** `error_logged`, `warning_logged`

---

## Priority 2: Error Monitoring ✅ COMPLETED

### AI_Mail: error_monitor.py ✅ MIGRATED

**Status:** COMPLETED (Phase 2, Session 11)

**What was migrated:**
- Error detection moved to Trigger's log_watcher
- `error_logged` event fires when errors detected
- AI_Mail notification handled by `error_logged.py` handler

---

### AI_Mail: log_watcher.py ✅ MIGRATED

**Status:** COMPLETED (Phase 2, Session 11)

**What was migrated:**
- Consolidated into Trigger's centralized log watching
- Pattern matching and error hash calculation handled by Trigger
- Unique error detection logic preserved

---

## Priority 3: Cross-Branch Coordination ✅ COMPLETED

### DevPulse: bulletin propagation ✅ MIGRATED

**Status:** COMPLETED (Phase 3, Session 13)

**What was migrated:**
- Created `trigger/apps/handlers/events/bulletin_created.py`
- Propagates bulletins to all branches when `bulletin_created` event fires
- Trigger now owns system-wide bulletin coordination

**Events added:** `bulletin_created`

---

### AI_Mail: local_memory_monitor.py ✅ MIGRATED

**Status:** COMPLETED (Phase 3, Session 13)

**What was migrated:**
- Created `trigger/apps/handlers/events/memory_threshold_exceeded.py`
- Sends compression notifications when threshold exceeded
- Memory threshold monitoring now event-driven

**Events added:** `memory_threshold_exceeded`

---

## Priority 4: Future Consolidation - EVALUATED

### Prax: monitor_module.py - STAYS IN PRAX

**Status:** Evaluated (Phase 4, Session 14) - No migration needed

**Assessment:**
- ~589 lines of threading, queues, interactive console
- This is an EVENT CONSUMER, not event producer
- Prax monitor consumes events for real-time display
- Trigger is EVENT PRODUCER - fires events
- Relationship: Complement, not duplicate

**Conclusion:** monitor_module stays in Prax. It's the consumer side of the event architecture.

---

### Drone: activation.py - STAYS IN DRONE

**Status:** Evaluated (Phase 4, Session 14) - No migration needed

**Assessment:**
- ~366 lines of pure CRUD for command registry
- Maps registered commands to drone command names
- Not event-driven at all - just command routing

**Conclusion:** activation.py is command routing, not event handling. Stays in Drone.

---

## Migration Strategy - COMPLETE

### Phase 1: Filesystem Events ✅ COMPLETED (Session 7)
- Flow's registry_monitor watchdog fires events to Trigger
- Events: `plan_file_created`, `plan_file_deleted`, `plan_file_moved`
- Trigger handlers update Flow's registry

### Phase 2: Log Events ✅ COMPLETED (Session 11)
- Centralized log watching in Trigger
- AI_Mail error detection moved to Trigger
- Events: `error_logged`, `warning_logged`

### Phase 3: System Events ✅ COMPLETED (Session 13)
- Bulletin propagation handled by Trigger
- Memory threshold monitoring event-driven
- Events: `bulletin_created`, `memory_threshold_exceeded`

### Phase 4: Evaluation ✅ COMPLETED (Session 14)
- Prax monitor_module: Stays in Prax (event consumer, not producer)
- Drone activation.py: Stays in Drone (command routing, not events)

**Migration scope finalized. 11 event handlers registered.**

---

## What Stays Where

**Stays in Prax:**
- Logging logic (how to format, where to write)
- Log aggregation and display
- Monitor UI/display (consuming events, not detecting them)

**Stays in AI_Mail:**
- Message formatting and sending
- Inbox management
- Email routing

**Stays in Flow:**
- Plan creation/closing logic
- Registry read operations
- Plan metadata management

**Moves to Trigger:**
- All watchdog file watchers
- All event detection loops
- All threshold monitoring
- All cross-branch coordination triggers

---

*Last updated: 2026-02-02*
