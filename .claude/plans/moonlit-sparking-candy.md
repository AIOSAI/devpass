# MASTER PLAN: Error Dispatch System Overhaul

## Context

The error dispatch system is broken in multiple ways, causing cascading notification floods that interrupt Patrick's active work at DEV_CENTRAL. Root causes identified by 3 investigation agents:

1. **DEV_CENTRAL gets auto-dispatched** - No protection. Error agents spawn while Patrick is working, reply to themselves, creating feedback loops
2. **Error routing broken** - system_logs/ errors route to "unknown" → @dev_central instead of owning branch. Trigger's fix from earlier session isn't active (cached old code in memory)
3. **No notification throttling** - Every email fires a desktop notify-send. 20+ emails = 20+ notifications flooding the screen
4. **Dedup is memory-only** - Log watcher hash set lost on restart, max 1000 entries
5. **reply_to hardcoded to @dev_central** - All error notifications send replies back to DEV_CENTRAL regardless of target branch
6. **No rate limiting** on error dispatches - same error can fire multiple times rapidly

## Affected Files

| File | Owner | Issue |
|------|-------|-------|
| `ai_mail/apps/handlers/email/delivery.py` | @ai_mail | No dispatch protection for DEV_CENTRAL, unthrottled notifications |
| `trigger/apps/handlers/events/error_detected.py` | @trigger | reply_to hardcoded to @dev_central, no rate limit |
| `trigger/apps/handlers/log_watcher.py` | @trigger | Memory-only dedup, needs disk persistence |
| `BRANCH_REGISTRY.json` | @cortex | No `no_auto_dispatch` flag exists |

---

## Phase 1: Stop the Bleeding (DEV_CENTRAL Protection)
**Owner: @ai_mail**
**Priority: CRITICAL**

### Tasks:
1. Add `no_auto_dispatch` list to delivery.py - hardcode `@dev_central` as protected
   - Emails still delivered to inbox (we can read them)
   - Agent spawn blocked - no auto-execute for protected branches
   - Log the block: "Dispatch blocked: @dev_central is protected from auto-dispatch"
2. Add notification rate limiting to `_send_desktop_notification()`
   - Max 3 notifications per 30 seconds per recipient
   - Use a simple in-memory timestamp list
   - After limit: silent delivery (email still arrives, no desktop popup)
3. Fix reply_to on error notifications - should be `@trigger` not `@dev_central`
   - This is in error_detected.py but @ai_mail should validate: if `reply_to == to_branch`, warn in logs

### Verification:
- Send test email to @dev_central with `--dispatch` → should deliver but NOT spawn agent
- Send 10 rapid test emails → only 3 desktop notifications should appear
- Check delivery logs confirm blocking messages

---

## Phase 2: Fix Error Routing (Trigger Overhaul)
**Owner: @trigger**
**Priority: HIGH**

### Tasks:
1. **Fix reply_to** in error_detected.py - change from `'@dev_central'` to `'@trigger'`
   - Trigger should receive investigation reports, not DEV_CENTRAL
   - Trigger can escalate to @dev_central if needed
2. **Persist dedup hashes to disk** in log_watcher.py
   - Write hashes to `trigger_data.json` (already exists for other state)
   - Load on startup, save after each new hash
   - Keep max 2000 hashes (increase from 1000)
3. **Add rate limiting** on error_detected dispatches
   - Max 3 dispatches per branch per 10 minutes
   - After limit: log "Rate limited: {branch} has {n} recent dispatches, skipping"
   - Reset counter after cooldown period
4. **Verify system_logs branch mapping** is working
   - The earlier fix added SYSTEM_LOGS_BRANCH_MAP but process had cached old code
   - Ensure log_watcher picks up new code (document restart procedure)
5. **Add error context notes** to dispatch messages
   - Include: error count (how many times this error occurred), first seen timestamp, last seen timestamp
   - Include surrounding log lines (2 lines before, 2 lines after the error)

### Verification:
- Inject fake ERROR line into `/home/aipass/system_logs/telegram_bridge.log`
- Verify dispatch goes to `@api` (not @dev_central)
- Verify reply_to is `@trigger`
- Inject 5 rapid errors → only 3 dispatches should fire
- Restart trigger, inject same error → dedup should prevent re-dispatch

---

## Phase 3: Error Handling Standards
**Owner: @ai_mail**
**Priority: MEDIUM**

### Tasks:
1. **Every error notification must contain a structured note:**
   ```
   ERROR ID: {hash}
   BRANCH: {branch} (@{email})
   MODULE: {module}
   LOG FILE: {path}
   TIMESTAMP: {time}
   OCCURRENCE: {count} times in last {window}
   CONTEXT: {2 lines before + error + 2 lines after}
   ```
2. **Dispatch bounce messages must be clear:**
   - Current: vague "branch busy" message
   - New: "Dispatch to @{branch} blocked: active agent PID {pid} running since {time}. Email delivered to inbox for manual review."
3. **Reduce stale lock timeout** from 30 minutes to 10 minutes
   - Dead agents shouldn't block dispatches for half an hour

### Verification:
- Trigger an error dispatch → verify structured note format
- Trigger dispatch while agent running → verify clear bounce message
- Kill an agent without cleanup → verify lock clears after 10 min

---

## Phase 4: Comprehensive Testing
**Owner: DEV_CENTRAL (orchestrate)**
**Priority: HIGH - do this AFTER Phases 1-3**

### Test Plan:
1. **DEV_CENTRAL protection test:**
   - `ai_mail send @dev_central "Test" "Testing" --dispatch` → should deliver but NOT spawn
   - Error in system_logs → should NOT dispatch to @dev_central at all (goes to owning branch)

2. **Error routing per branch:**
   - Inject fake ERROR into `aipass_core/drone/logs/drone.log` → dispatch to @drone
   - Inject fake ERROR into `aipass_core/flow/logs/flow.log` → dispatch to @flow
   - Inject fake ERROR into `system_logs/telegram_bridge.log` → dispatch to @api
   - Inject fake ERROR into `system_logs/telegram_chats.log` → dispatch to @api

3. **Rate limiting test:**
   - Inject 10 rapid errors into one branch log → max 3 dispatches
   - Send 10 emails to one branch rapidly → max 3 desktop notifications

4. **Dedup persistence test:**
   - Inject error → verify dispatched
   - Restart trigger process
   - Inject same error → verify NOT dispatched (dedup survived restart)

5. **Lock mechanism test:**
   - Dispatch to a branch → verify lock created
   - Try second dispatch → verify bounced with clear message
   - Kill agent → verify lock clears within 10 min
   - Try dispatch again → verify succeeds

6. **Telegram bridge test:**
   - Patrick sends message from phone
   - Verify bridge handles it (or errors are properly routed to @api)

7. **Drone backup routing test:**
   - `drone @backup_system drive-sync` → verify command executes (no emails)
   - Any errors during sync → verify dispatched to @backup_system (not @dev_central)

### Success Criteria:
- Zero notification floods
- DEV_CENTRAL inbox stays clean during error storms
- Every error dispatch contains structured context
- Branches receive their own errors and handle them
- Patrick can work at DEV_CENTRAL without interruption

---

## Execution Order

1. **Phase 1** → Dispatch to @ai_mail (CRITICAL - stops the bleeding)
2. **Phase 2** → Dispatch to @trigger (HIGH - fixes routing)
3. Wait for both to confirm with test results
4. **Phase 3** → Dispatch to @ai_mail (MEDIUM - quality improvements)
5. **Phase 4** → DEV_CENTRAL orchestrates testing
6. Create Flow plan to track: `drone @flow create . "Error Dispatch System Overhaul" master`
