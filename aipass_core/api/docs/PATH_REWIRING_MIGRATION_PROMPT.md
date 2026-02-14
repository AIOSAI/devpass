# Path Rewiring & Migration Validation Prompt

**Context:** We've migrated to the new `/home/aipass/aipass_core/` structure. This prompt guides branches through verifying all modules are correctly wired and writing to the correct locations.

**Target Audience:** All AIPass branches migrating to aipass_core structure

---

## Overview

This is a systematic validation workflow that ensures your branch's modules are properly configured for the new directory structure. You'll create a PLAN, track progress with TodoWrite, and document everything for future reference.

**Estimated Time:** 30-45 minutes depending on branch complexity

**Prerequisites:**
- Branch already moved to `/home/aipass/aipass_core/[branch]/`
- Basic understanding of your branch's modules

---

## Step 1: Create a PLAN

Start by creating a plan to track this migration validation work:

```bash
drone plan create @[your-branch] "Path Rewiring & Migration Validation"
```

**Example:**
```bash
drone plan create @api "Path Rewiring & Migration Validation"
drone plan create @flow "Path Rewiring & Migration Validation"
drone plan create @backup_system "Path Rewiring & Migration Validation"
```

This creates a structured PLAN file where you'll document your progress.

---

## Step 2: Fill Out Planning Phase

Open your new PLAN and complete the **Planning Phase** section:

### Desired Result
```
Verify all [BRANCH] modules are correctly wired to /home/aipass/aipass_core/ structure.
Ensure JSON files and logs write to correct locations. Confirm all modules operational.
```

### Goals
1. Audit all modules for hardcoded paths
2. Update any paths pointing to old locations
3. Verify JSON files write to correct location
4. Verify logs write to correct locations (dual logging check)
5. Test all modules work correctly after path updates

### Approach
```
Direct work - systematic file-by-file review and testing. This is straightforward
path verification, not complex refactoring. No agent needed.
```

### Definition of Done
- [ ] All module paths audited (apps/*.py files checked)
- [ ] All hardcoded paths updated to use AIPASS_ROOT pattern
- [ ] JSON files confirmed writing to aipass_core location
- [ ] Log files confirmed writing to correct location
- [ ] All modules tested and operational
- [ ] Documentation updated with any path changes

---

## Step 3: Execute Your Work

Use the **TodoWrite tool** to track your progress through these tasks. Mark each as in_progress when starting, completed when done.

### Task 1: Audit Module Paths

**Action:** Check every Python module in your apps/ directory for path references

**What to look for:**
- `AIPASS_ROOT` variable definitions
- `[BRANCH]_ROOT` variable definitions (e.g., `FLOW_ROOT`, `API_ROOT`)
- Hardcoded paths like `/home/aipass/[branch]`
- Old path patterns that need updating

**Commands:**
```bash
# Check for ROOT variable usage
grep -n "AIPASS_ROOT\|FLOW_ROOT\|API_ROOT\|BACKUP_ROOT" /home/aipass/aipass_core/[branch]/apps/*.py | head -20

# Look for hardcoded old paths (replace [branch] with your branch name)
grep -r "/home/aipass/[branch]" /home/aipass/aipass_core/[branch]/apps/*.py

# Example for API branch:
grep -r "/home/aipass/api" /home/aipass/aipass_core/api/apps/*.py
```

**Correct Pattern:**
```python
from pathlib import Path

# Should use this pattern:
AIPASS_ROOT = Path.home() / "aipass_core"
API_ROOT = AIPASS_ROOT / "api"

# OR if module-specific:
FLOW_ROOT = Path.home() / "aipass_core" / "flow"
```

**Log in PLAN Work Log:**
```markdown
## Path Audit Results
- api_connect.py: Uses AIPASS_ROOT correctly ✅
- openrouter.py: Found hardcoded path at line 45 ⚠️
- api_usage.py: Uses AIPASS_ROOT correctly ✅
```

---

### Task 2: Fix Hardcoded Paths

**Action:** Update any hardcoded `/home/aipass/[branch]` paths to use dynamic variables

**What to change:**
```python
# OLD (hardcoded)
config_path = Path("/home/aipass/api/api_json/config.json")

# NEW (dynamic)
AIPASS_ROOT = Path.home() / "aipass_core"
API_ROOT = AIPASS_ROOT / "api"
config_path = API_ROOT / "api_json" / "config.json"
```

**Use Edit tool to make changes:**
```python
# Read the file first to see exact content
# Then use Edit tool to replace old paths with new pattern
```

**Log in PLAN Work Log:**
```markdown
## Hardcoded Path Fixes
- openrouter.py:45 - Changed `/home/aipass/api/api_json` → `API_ROOT / "api_json"` ✅
- api_usage.py:78 - Changed `/home/aipass/api/logs` → `API_ROOT / "logs"` ✅
```

---

### Task 3: Verify JSON Files Location

**Action:** Check where your JSON files are actually being written

**Expected Location:**
```
/home/aipass/aipass_core/[branch]/[branch]_json/
```

**Commands:**
```bash
# List recent JSON files with timestamps (replace [branch] with your branch name)
ls -lth /home/aipass/aipass_core/[branch]/[branch]_json/*.json | head -5

# Example for API branch:
ls -lth /home/aipass/aipass_core/api/api_json/*.json | head -5

# Example for Flow branch:
ls -lth /home/aipass/aipass_core/flow/flow_json/*.json | head -5
```

**What to verify:**
- Files exist in the correct location ✅
- Timestamps are recent (today's date = files actively writing) ✅
- File names match expected pattern (module_config.json, module_data.json, module_log.json) ✅

**Example Output:**
```
-rw-rw-r-- 1 aipass aipass  2847 Oct 30 14:23 openrouter_data.json
-rw-rw-r-- 1 aipass aipass  1456 Oct 30 14:20 api_connect_config.json
-rw-rw-r-- 1 aipass aipass   892 Oct 30 14:15 openrouter_log.json
```

**Log in PLAN Work Log:**
```markdown
## JSON Files Verification
Location: /home/aipass/aipass_core/api/api_json/ ✅
Files found: 12 JSON files
Recent activity: openrouter_data.json (Oct 30 14:23) ✅
Status: All JSON files writing to correct location ✅
```

---

### Task 4: Verify Logging Locations

**Action:** Check BOTH log directories and compare timestamps

**Two possible locations:**
1. **System-level:** `/home/aipass/aipass_core/logs/` (centralized logging)
2. **Branch-level:** `/home/aipass/aipass_core/[branch]/logs/` (branch-specific logging)

**Commands:**
```bash
# Check system-level logs (replace [branch] with your branch name)
ls -lth /home/aipass/aipass_core/logs/[branch]*.log | head -3

# Check branch-level logs
ls -lth /home/aipass/aipass_core/[branch]/logs/*.log | head -3

# Example for API branch:
ls -lth /home/aipass/aipass_core/logs/api*.log | head -3
ls -lth /home/aipass/aipass_core/api/logs/*.log | head -3
```

**What to compare:**
- Which location has files? ✅
- Which has recent timestamps (today's date)? ✅
- Are logs writing to one location or both? (dual logging is okay) ✅

**Log in PLAN Work Log:**
```markdown
## Logging Location Verification
System-level (/home/aipass/aipass_core/logs/):
- api_connect.log (Oct 30 14:25) ✅
- openrouter.log (Oct 30 14:23) ✅

Branch-level (/home/aipass/aipass_core/api/logs/):
- openrouter.log (Oct 30 14:23) ✅

Status: Dual logging active (system + branch) ✅
```

---

### Task 5: Test Your Modules

**Action:** Run status/help/test commands on your main modules to verify they work

**Commands to try:**
```bash
# Run module with status command
python3 /home/aipass/aipass_core/[branch]/apps/[main_module].py status

# Run module with help
python3 /home/aipass/aipass_core/[branch]/apps/[main_module].py --help

# Run module test function (if exists)
python3 /home/aipass/aipass_core/[branch]/apps/[main_module].py test

# Example for API branch:
python3 /home/aipass/aipass_core/api/apps/openrouter.py test
python3 /home/aipass/aipass_core/api/apps/api_connect.py
```

**What to verify:**
- Module executes without path errors ✅
- No "FileNotFoundError" for config/data files ✅
- No "ModuleNotFoundError" for imports ✅
- Module functions correctly ✅

**If you get errors:**
- Read the error message carefully
- Check if it's a path issue (wrong location referenced)
- Use Edit tool to fix the path
- Test again

**Log in PLAN Work Log:**
```markdown
## Module Testing Results
- api_connect.py: Executed successfully, key loaded (73 chars) ✅
- openrouter.py test: Connection successful, response received ✅
- api_usage.py status: 1,219 total requests tracked ✅

All 3 modules operational ✅
```

---

## Step 4: Complete Your PLAN

### Document in Work Log Section

As you complete each task, document in your PLAN's **Work Log** section:

```markdown
## Work Log

### Path Audit (Task 1)
- api_connect.py: Uses AIPASS_ROOT correctly ✅
- openrouter.py: Found hardcoded path at line 45 ⚠️
- api_usage.py: Uses AIPASS_ROOT correctly ✅

### Path Fixes (Task 2)
- openrouter.py:45 - Changed `/home/aipass/api/api_json` → `API_ROOT / "api_json"` ✅

### JSON Verification (Task 3)
Location: /home/aipass/aipass_core/api/api_json/ ✅
Recent activity: openrouter_data.json (Oct 30 14:23) ✅

### Log Verification (Task 4)
Dual logging active (system + branch) ✅

### Module Testing (Task 5)
All 3 modules tested and operational ✅
```

### Complete Definition of Done

In your PLAN's **Completion** section:

```markdown
## Definition of Done

- [x] All module paths audited (3 apps/*.py files checked)
- [x] All hardcoded paths updated to use AIPASS_ROOT pattern (1 fix applied)
- [x] JSON files confirmed writing to aipass_core location
- [x] Log files confirmed writing to correct location (dual logging)
- [x] All modules tested and operational (3/3 passed)
- [x] Documentation updated with path changes

## Final Result
All API modules successfully migrated to /home/aipass/aipass_core/api/ structure.
One hardcoded path fixed, all JSON and log files writing to correct locations.
All modules tested and operational. Migration validation complete ✅
```

---

## Step 5: Report Back

Give Patrick a summary in chat:

```markdown
**Migration Validation Complete - [BRANCH] Branch**

**Hardcoded Paths Fixed:** 1
- openrouter.py:45 - Updated to use API_ROOT pattern

**JSON Location:** /home/aipass/aipass_core/api/api_json/ ✅
- 12 files found, actively writing (timestamps: Oct 30)

**Log Location:** Dual logging active ✅
- System-level: /home/aipass/aipass_core/logs/
- Branch-level: /home/aipass/aipass_core/api/logs/

**Module Testing:** All 3 modules operational ✅
- api_connect.py: Working ✅
- openrouter.py: Working ✅
- api_usage.py: Working ✅

**Status:** All modules correctly wired to aipass_core structure ✅
```

---

## Step 6: Close Your PLAN

When complete:

```bash
drone plan close [your-plan-number]
```

**Example:**
```bash
drone plan close 0150
```

This will:
- Archive your PLAN to memory bank
- Generate AI summary of the work
- Update the plan registry
- Clear the active plan

---

## TodoWrite Tracking Example

Throughout this workflow, use TodoWrite to track progress:

```json
[
  {
    "content": "Audit all module paths for hardcoded references",
    "activeForm": "Auditing module paths",
    "status": "completed"
  },
  {
    "content": "Fix hardcoded paths in openrouter.py",
    "activeForm": "Fixing hardcoded paths",
    "status": "completed"
  },
  {
    "content": "Verify JSON files write to correct location",
    "activeForm": "Verifying JSON file locations",
    "status": "completed"
  },
  {
    "content": "Verify log files write to correct location",
    "activeForm": "Verifying log file locations",
    "status": "completed"
  },
  {
    "content": "Test all modules for operational status",
    "activeForm": "Testing all modules",
    "status": "in_progress"
  }
]
```

---

## Common Issues & Solutions

### Issue: Module can't find JSON config files
**Symptom:** `FileNotFoundError: [branch]_json/config.json`
**Solution:** Check module path definition, ensure using `AIPASS_ROOT / "aipass_core" / [branch] / [branch]_json`

### Issue: Import errors for other modules
**Symptom:** `ModuleNotFoundError: No module named 'api.apps'`
**Solution:** Verify sys.path includes AIPASS_ROOT, check import statements use correct path

### Issue: Old logs still writing to /home/aipass/[branch]/
**Symptom:** Timestamps in old location newer than aipass_core location
**Solution:** Check prax_logger configuration, verify logger initialization uses correct paths

### Issue: No recent file activity in new location
**Symptom:** All file timestamps are days old
**Solution:** Run module test to trigger file writes, verify module is actually being used

---

## Notes

- **Migration mode:** Some things might still be off elsewhere in the system. Focus on getting YOUR branch's modules wired correctly.
- **Document everything:** Your PLAN creates a record of migration work for future reference
- **Ask for help:** If stuck, report specific error messages and what you've tried
- **Test thoroughly:** Better to catch issues now than discover them later in production

---

**Created:** 2025-10-30
**Branch:** API
**Purpose:** Standardized migration validation workflow for all aipass_core branches
**Status:** Template ready for deployment
