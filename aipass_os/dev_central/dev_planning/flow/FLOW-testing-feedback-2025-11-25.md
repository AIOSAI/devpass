# FLOW Testing Feedback - 2025-11-25

**Session:** Flow branch testing with Patrick
**Status:** In Progress
**Last Updated:** 2025-11-25 (Session 9 - continued)

---

## COMPLETED FIXES (2025-11-25)

### 1. API Response Type Bug
- **File:** `handlers/summary/generate.py:293`
- **Fix:** `response['content'].strip()` instead of `response.strip()`
- **Status:** DONE

### 2. Idempotency Check for Close
- **File:** `modules/close_plan.py:169-174`
- **Fix:** Added guard to prevent double-closing plans
- **Status:** DONE

### 3. Duplicate Memory Bank Check
- **File:** `handlers/mbank/process.py:389-392`
- **Fix:** Skip writing if memory file already exists
- **Status:** DONE

### 4. Template Auto-Delete on Close
- **File:** `modules/close_plan.py:177-199`
- **Fix:** Empty templates now deleted instead of archived (v2.3.0)
- **Status:** DONE

### 5. CLI --help Detection (Seed Audit)
- **Files:** `create_plan.py`, `list_plans.py`, `registry_monitor.py`, `aggregate_central.py`
- **Fix:** Added `def print_help()` functions to pass seed audit checker
- **Audit Score:** 97% → 98% overall, CLI 79% → 82%
- **Status:** DONE

### 6. --yes Flag for Close Command
- **File:** `handlers/plan/command_parser.py:123`
- **Fix:** Already implemented in v2.0.0 - confirmed working
- **Usage:** `drone @flow close 0170 --yes`
- **Status:** ALREADY DONE (Seed notified)

---

## REMAINING ISSUES (Need More Work)

### 1. CLI Rich Formatting
- **Problem:** No rich formatting in CLI output
- **Seed Response:** Flow is 100% compliant - may be terminal/Rich support issue
- **Action:** Test `python3 flow.py --help` directly, check Rich installed
- **Priority:** Low (investigate terminal, not code)

### 2. Plan Links Broken
- **Problem:** Links point to directory, not actual plan files
- **Action:** Fix link generation to point to PLAN####.md files
- **Priority:** High

### 3. Naming: "aggregate" → "plan central sync"
- **Problem:** "Starting central aggregation" not intuitive
- **Current:** `drone @flow aggregate`
- **Proposed:** Rename to better describe what it does
- **Note:** Semi-automated (runs on create/close/restore, not scheduled)
- **Priority:** Medium

### 4. ~~Memory Bank Storing Temp Files~~ DONE
- **Problem:** Temp/empty plans saved to memory bank (just marked -TEMP, not deleted)
- **Fix:** close_plan.py v2.3.0 now deletes empty templates instead of archiving
- **Status:** DONE (moved to completed section)

### 5. Clean Up Existing Duplicates
- **Problem:** 4+ duplicate entries in MEMORY_BANK/plans/
- **Files:** PLAN0030 (2 copies), plus -TEMP files that shouldn't exist
- **Action:** Manual review and cleanup
- **Priority:** Medium

### 6. Monitor Scan - No Verification
- **Problem:** `drone @flow monitor scan` says "success" but no proof
- **Action:** Add before/after stats, show what was healed
- **Priority:** Medium

### 7. CLI Output Messages
- **Problem:** "Starting central aggregation" confusing when instant
- **Action:** Remove "Starting" prefix, just show results
- **Priority:** Low

---

## Investigation Needed

### TRL (Type-Reference-Label) System
- **Background:** Basic setup, never properly tested for accuracy
- **Questions:**
  - Is TRL classification working correctly?
  - What categories exist?
  - How accurate is the AI classification?
- **Action:** Deep dive into TRL implementation
- **Priority:** Medium (separate task)

### AI Command Access (System-Wide)
- **Background:** --yes flags are workarounds, not solutions
- **Problem:** AI cannot respond to interactive prompts (input(), confirm())
- **Scope:** All 18 branches, all commands
- **Questions:**
  - Auto-detect AI vs human caller?
  - Global --non-interactive flag?
  - Different defaults for AI?
- **Action:** Drone challenged to audit all branches
- **Email Sent:** To @drone requesting full audit
- **Priority:** High (affects AI autonomy)

---

## NEXT PRIORITY ORDER

1. ~~Duplicate prevention~~ DONE (idempotency + mbank check)
2. ~~Temp file deletion~~ DONE (close_plan v2.3.0)
3. ~~CLI --help detection~~ DONE (4 modules fixed, 98% audit)
4. Fix plan links - **HIGH** (next up)
5. Clean up existing duplicates (manual)
6. Monitor scan verification
7. CLI output/naming cleanup

---

## Notes

- archive.temp files are REFERENCE - do not delete
- Check old implementations before reinventing
- Seed confirmed Rich formatting is compliant - terminal issue not code

