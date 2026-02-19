# Business Branch Template — Verification Test Plan

> Comprehensive verification for `business_branch_template` built by @cortex per DPLAN-007 spec.

**Author:** TEAM_2 (Architecture)
**Date:** 2026-02-18
**Status:** Ready for execution (pending cortex build completion)
**Spec Reference:** `/home/aipass/aipass_business/hq/vera/dropbox/business_branch_template_spec.md`

---

## Test Environment

- **Test branch path:** `/tmp/test_biz_branch`
- **Test branch name:** `TEST_BIZ_BRANCH` (derived from directory name)
- **Template flag:** `--template business_branch`
- **Cleanup required:** Yes — delete test branch and remove registry entry after all tests pass

---

## TEST 1: Template Creation

**Purpose:** Verify `drone @cortex create-branch` accepts `--template business_branch` and creates a branch successfully.

### Steps

1. Run: `drone @cortex create-branch /tmp/test_biz_branch --template business_branch --role "Test Department" --traits "Testing, Verification" --purpose "Template verification test"`
2. Verify exit code is 0 (success)
3. Verify `/tmp/test_biz_branch/` directory exists
4. Verify cortex reports creation success (no error output)

### Expected Result
- Branch created at `/tmp/test_biz_branch/` with all template files copied
- No errors or warnings in output

### Failure Conditions
- `--template business_branch` flag not recognized → cortex create_branch.py needs template selection logic
- Template directory not found → `/home/aipass/aipass_core/cortex/templates/business_branch_template/` missing
- Permission errors → test path not writable

---

## TEST 2: Placeholder Replacement

**Purpose:** Verify ALL `{{PLACEHOLDER}}` tokens are replaced with actual values.

### Steps

1. Run: `grep -r '{{' /tmp/test_biz_branch/ --include='*.json' --include='*.md' --include='*.txt'`
2. Filter out allowed unresolved placeholders:
   - `{{AUTO_GENERATED_COMMANDS}}`
   - `{{AUTO_GENERATED_MODULES}}`
   - `{{AUTO_GENERATED_DEPENDENCIES}}`
   - `{{AUTO_GENERATED_IMPORTS}}`
   - `{{TREE_PLACEHOLDER}}` (should be replaced, but tolerable if tree generation runs after)
   - Documentation template placeholders in `docs/_template.md`: `{{DOCUMENT_TYPE}}`, `{{TAG_1}}`, etc.
3. Any OTHER `{{...}}` pattern remaining = FAIL

### Specific Placeholder Checks

| Placeholder | Expected Value | File(s) to Check |
|---|---|---|
| `{{BRANCHNAME}}` | `TEST_BIZ_BRANCH` | id.json, local.json, observations.json, NOTEPAD.md, branch_system_prompt.md |
| `{{branchname}}` | `test_biz_branch` | README.md, branch_system_prompt.md |
| `{{DATE}}` | `2026-02-18` | id.json, local.json, observations.json, NOTEPAD.md |
| `{{CWD}}` | `/tmp/test_biz_branch` | id.json |
| `{{PROFILE}}` | `Business` or `Workshop` | id.json |
| `{{ROLE}}` | `Test Department` | id.json |
| `{{TRAITS}}` | `Testing, Verification` | id.json |
| `{{PURPOSE_BRIEF}}` | `Template verification test` | id.json, README.md |
| `{{EMAIL}}` | `@test_biz_branch` | id.json |

### Expected Result
- Zero unresolved placeholders (excluding allowed template docs placeholders)

### Failure Conditions
- Unreplaced `{{BRANCHNAME}}` in NOTEPAD.md → NOTEPAD.md not in placeholder substitution list
- `{{DATE}}` still present → file not processed during copy
- `{{PROFILE}}` shows "Workshop" instead of "Business" → profile detection doesn't recognize `/tmp/` path (acceptable — not inside `aipass_business/`)

---

## TEST 3: Directory Structure Validation

**Purpose:** Verify all business-specific directories exist with correct structure.

### Steps

1. Verify these directories exist:

```bash
# Business-specific directories (MUST exist)
ls -d /tmp/test_biz_branch/playbooks/
ls -d /tmp/test_biz_branch/strategy/
ls -d /tmp/test_biz_branch/output/
ls -d /tmp/test_biz_branch/research/
ls -d /tmp/test_biz_branch/metrics/
ls -d /tmp/test_biz_branch/decisions/
ls -d /tmp/test_biz_branch/dropbox/
ls -d /tmp/test_biz_branch/docs/

# Infrastructure directories (MUST exist)
ls -d /tmp/test_biz_branch/ai_mail.local/
ls -d /tmp/test_biz_branch/ai_mail.local/.archive/
ls -d /tmp/test_biz_branch/ai_mail.local/sent/
ls -d /tmp/test_biz_branch/ai_mail.local/deleted/
ls -d /tmp/test_biz_branch/.aipass/
ls -d /tmp/test_biz_branch/.archive/
ls -d /tmp/test_biz_branch/.backup/
```

2. Verify .gitkeep files in empty business directories:

```bash
ls /tmp/test_biz_branch/playbooks/.gitkeep
ls /tmp/test_biz_branch/strategy/.gitkeep
ls /tmp/test_biz_branch/output/.gitkeep
ls /tmp/test_biz_branch/research/.gitkeep
ls /tmp/test_biz_branch/metrics/.gitkeep
ls /tmp/test_biz_branch/decisions/.gitkeep
ls /tmp/test_biz_branch/dropbox/.gitkeep
```

### Expected Result
- All 7 business directories + infrastructure directories present
- .gitkeep files in empty directories (git tracks them)

### Failure Conditions
- Missing directory → template directory not included in business_branch_template
- Missing .gitkeep → directory won't be tracked by git

---

## TEST 4: No Dev Artifacts

**Purpose:** Confirm no dev-specific files or directories leaked into the business template.

### Steps

1. Verify these DO NOT exist:

```bash
# Dev code structure (MUST NOT exist)
! ls -d /tmp/test_biz_branch/apps/ 2>/dev/null
! ls -d /tmp/test_biz_branch/tests/ 2>/dev/null
! ls -d /tmp/test_biz_branch/tools/ 2>/dev/null
! ls -d /tmp/test_biz_branch/logs/ 2>/dev/null
! ls -d /tmp/test_biz_branch/artifacts/ 2>/dev/null

# Dev config files (MUST NOT exist)
! ls /tmp/test_biz_branch/pytest.ini 2>/dev/null
! ls /tmp/test_biz_branch/requirements.txt 2>/dev/null
! ls /tmp/test_biz_branch/.gitignore 2>/dev/null  # if dev-specific

# Dev template artifacts (MUST NOT exist)
! ls -d /tmp/test_biz_branch/*_json/ 2>/dev/null  # {{BRANCH}}_json dir
! ls /tmp/test_biz_branch/apps/BRANCH.py 2>/dev/null
! ls /tmp/test_biz_branch/#@comments.txt 2>/dev/null
```

### Expected Result
- Zero dev-specific files or directories present
- Clean business-only structure

### Failure Conditions
- `apps/` present → cortex copied from wrong template or template not fully cleaned
- `pytest.ini` present → file included in business template by mistake
- `{{BRANCH}}_json/` present → dev-specific directory leaked through

---

## TEST 5: Trinity File Validation

**Purpose:** Verify id.json, local.json, and observations.json are correctly initialized.

### Steps

#### 5a. Identity File (id.json)

1. Verify file exists: `/tmp/test_biz_branch/TEST_BIZ_BRANCH.id.json`
2. Verify valid JSON (parse with `python3 -m json.tool`)
3. Check required fields:

```json
{
  "document_metadata": {
    "document_type": "branch_identity",
    "document_name": "TEST_BIZ_BRANCH.ID"
  },
  "branch_info": {
    "branch_name": "TEST_BIZ_BRANCH",
    "path": "/tmp/test_biz_branch",
    "created": "2026-02-18"
  },
  "identity": {
    "role": "Test Department",
    "traits": "Testing, Verification",
    "purpose": "Template verification test"
  }
}
```

4. Verify `branch_name` matches directory-derived name (uppercase)
5. Verify `path` matches actual directory path
6. Verify `created` matches current date

#### 5b. Session History (local.json)

1. Verify file exists: `/tmp/test_biz_branch/TEST_BIZ_BRANCH.local.json`
2. Verify valid JSON
3. Check schema version present
4. Check `document_type` is `"session_history"`
5. Check `max_lines` limit defined (should be 600)
6. Check sessions array is initialized (empty or with session 1)

#### 5c. Observations File (observations.json)

1. Verify file exists: `/tmp/test_biz_branch/TEST_BIZ_BRANCH.observations.json`
2. Verify valid JSON
3. Check `document_type` is `"collaboration_patterns"`
4. Check `max_lines` limit defined (should be 600)
5. Check observations array is initialized (empty or with initial entry)

### Expected Result
- All 3 Trinity files exist with correct branch name prefix
- All valid JSON
- All have correct document_type, schema, and branch-specific values
- No template placeholders remaining

### Failure Conditions
- File named `BRANCH.ID.json` instead of `TEST_BIZ_BRANCH.id.json` → rename step skipped
- Invalid JSON → placeholder replacement broke JSON structure
- Wrong branch name → placeholder substitution error
- Wrong path → CWD placeholder not replaced

---

## TEST 6: NOTEPAD.md Validation

**Purpose:** Verify NOTEPAD.md is correctly populated.

### Steps

1. Verify file exists: `/tmp/test_biz_branch/NOTEPAD.md`
2. Verify branch name appears in header: `# TEST_BIZ_BRANCH NOTEPAD`
3. Verify standard sections present:
   - `## CURRENT STATUS`
   - `### What Is Open Right Now`
   - `### Who I'm Waiting On`
   - `### What Is Next`
   - `## SESSION HISTORY`
4. Verify `{{BRANCHNAME}}` replaced (no raw placeholder)
5. Verify `{{DATE}}` replaced with actual date

### Expected Result
- NOTEPAD.md exists with correct branch name and all sections
- No unreplaced placeholders

### Failure Conditions
- NOTEPAD.md missing → not included in template
- `{{BRANCHNAME}}` still present → file not processed during placeholder replacement
- Filename is `notepad.md` (lowercase) → verify case matches spec (spec says `NOTEPAD.md`)

---

## TEST 7: ai_mail Validation

**Purpose:** Verify email infrastructure is functional.

### Steps

1. Verify files exist:
   - `/tmp/test_biz_branch/ai_mail.local/inbox.json` (valid JSON, empty array or object)
   - `/tmp/test_biz_branch/ai_mail.local/sent.json` (valid JSON)
2. Verify directories exist:
   - `/tmp/test_biz_branch/ai_mail.local/sent/`
   - `/tmp/test_biz_branch/ai_mail.local/deleted/`
   - `/tmp/test_biz_branch/ai_mail.local/.archive/`
3. Functional test: send a test email TO the branch (requires branch to be registered first):
   ```bash
   cd /tmp/test_biz_branch && ai_mail send @test_biz_branch "Test" "Verification email"
   ```
4. Verify email appears in inbox.json
5. Verify email can be viewed: `ai_mail view <id>`

### Expected Result
- All ai_mail files and directories present
- inbox.json and sent.json are valid JSON
- Email delivery works (if branch is registered)

### Failure Conditions
- inbox.json missing → ai_mail.local/ not fully copied
- Invalid JSON in inbox.json → template file corrupted or placeholder broke structure
- Email delivery fails → branch not in BRANCH_REGISTRY.json or ai_mail can't resolve path

---

## TEST 8: Branch Registration

**Purpose:** Verify branch is registered in BRANCH_REGISTRY.json.

### Steps

1. Read `/home/aipass/BRANCH_REGISTRY.json`
2. Search for entry with `"name": "TEST_BIZ_BRANCH"`
3. Verify entry fields:

```json
{
  "name": "TEST_BIZ_BRANCH",
  "path": "/tmp/test_biz_branch",
  "profile": "Business",
  "email": "@test_biz_branch",
  "status": "active",
  "created": "2026-02-18"
}
```

4. Verify `total_branches` in metadata was incremented
5. Verify drone can resolve the branch: `drone list @test_biz_branch`

### Expected Result
- Branch registered with correct name, path, profile, and email
- Drone can resolve `@test_biz_branch` to the correct path

### Failure Conditions
- Not registered → registration step failed or skipped
- Wrong profile → profile detection didn't detect "Business" (path `/tmp/` won't match `aipass_business/`)
- Drone can't resolve → registration format incorrect or drone cache stale

---

## TEST 9: Template Flag

**Purpose:** Verify `--template business_branch` flag works in cortex.

### Steps

1. Test help output: `drone @cortex create-branch --help`
2. Verify `--template` flag is documented
3. Verify `business_branch` is listed as valid template option
4. Test invalid template: `drone @cortex create-branch /tmp/test_invalid --template nonexistent`
5. Verify error message is clear (template not found)
6. Test default (no flag): verify it still defaults to `branch_template` (don't actually create — dry-run if available)

### Expected Result
- `--template` flag documented in help
- `business_branch` accepted as valid value
- Invalid template names produce clear error
- Default behavior unchanged (still creates dev branches without flag)

### Failure Conditions
- Flag not recognized → create_branch.py not updated to accept --template
- No validation on template name → could silently fail or use wrong template
- Default changed → existing `create-branch` calls would break

---

## TEST 10: branch_system_prompt.md

**Purpose:** Verify the business-specific system prompt is correct.

### Steps

1. Read `/tmp/test_biz_branch/.aipass/branch_system_prompt.md`
2. Verify it contains "business branch" identifier
3. Verify `{{BRANCHNAME}}` replaced with `TEST_BIZ_BRANCH`
4. Verify business directory descriptions present (playbooks, strategy, output, etc.)
5. Verify reporting structure: `@vera` (CEO) and `@dev_central` (escalation)
6. Verify NO dev-specific content (no mention of apps/, handlers/, tests/)

### Expected Result
- System prompt clearly identifies this as a business branch
- All directory purposes documented
- Correct reporting chain

### Failure Conditions
- Contains dev branch template content → wrong template file used
- Missing business directory descriptions → template not updated per spec
- Incorrect reporting chain → template has wrong defaults

---

## TEST 11: Cleanup

**Purpose:** Remove test branch and registry entry.

### Steps

1. Remove test branch directory: `rm -rf /tmp/test_biz_branch`
2. Remove registry entry from BRANCH_REGISTRY.json (manual or via cortex)
3. Verify directory removed: `! ls -d /tmp/test_biz_branch`
4. Verify registry entry removed: grep BRANCH_REGISTRY.json for TEST_BIZ_BRANCH

### Expected Result
- No trace of test branch remains

### Note
- If cortex has a `delete-branch` command, use that instead: `drone @cortex delete-branch /tmp/test_biz_branch`
- Verify delete-branch also removes the registry entry

---

## SPEC GAP ANALYSIS

Issues identified in the template spec that may cause problems:

### GAP 1: Profile Detection Path Mismatch

**Issue:** The spec says "If path contains `aipass_business/` or `departments/`, profile should be 'Business'." But cortex's current profile detection uses `/home/aipass-business/` (with hyphen, per the research), not `/home/aipass/aipass_business/` (with underscore). If the test path is `/tmp/test_biz_branch`, it won't match ANY business path pattern.

**Impact:** Test branches will get "Workshop" profile instead of "Business". Production departments under `aipass_business/departments/` may also get wrong profile if detection logic uses hyphen.

**Recommendation:** Verify cortex's actual profile detection code. Update it to match the real path pattern (`aipass_business/` with underscore) or accept that `--template business_branch` flag implies "Business" profile regardless of path.

### GAP 2: NOTEPAD.md vs notepad.md Casing

**Issue:** The spec says `NOTEPAD.md` (uppercase). The existing branch_template uses `notepad.md` (lowercase). The dev system prompt template references `notepad.md`. Inconsistent casing will confuse branches that check for the file by name.

**Impact:** Startup scripts or hooks that look for `notepad.md` won't find `NOTEPAD.md`.

**Recommendation:** Pick one. I'd recommend lowercase `notepad.md` to match existing convention across all dev branches, unless there's a reason to differentiate business branches.

### GAP 3: DASHBOARD.local.json Source

**Issue:** The spec includes `DASHBOARD.local.json` but doesn't specify its contents or how it gets populated for business branches. On dev branches, this is auto-maintained by Flow. Business branches may not use Flow the same way.

**Impact:** DASHBOARD.local.json may be empty or contain dev-oriented fields irrelevant to business branches.

**Recommendation:** Create a business-specific DASHBOARD template with fields relevant to departments (pending tasks, last VERA directive, department metrics). Or use the same template and let it self-populate.

### GAP 4: No .claude/settings.local.json

**Issue:** The branch_template includes `.claude/settings.local.json` (Claude Code tool permissions). The business_branch spec doesn't mention it. Business branches run Claude too — they need tool permissions configured.

**Impact:** Business branches would use default Claude tool permissions, which may prompt for every tool use. Dev branches have pre-configured settings.

**Recommendation:** Include `.claude/settings.local.json` in the business template with the same permissions as dev branches.

### GAP 5: dropbox/ in Spec vs Existing Convention

**Issue:** The spec adds `dropbox/` for "proposals/deliverables for review." But dropbox/ already exists in the branch_template (dev branches have it too). This is shared, not new.

**Impact:** None functionally — just noting the spec presents it as business-specific when it's actually inherited from the base template pattern.

### GAP 6: Template Registry File Tracking

**Issue:** The spec says "Create `.template_registry.json` tracking all business template files, same format as dev." But it doesn't specify what files should be tracked or their IDs.

**Impact:** If cortex doesn't auto-generate the registry, it'll need to be manually created. The dev branch_template has 60+ tracked files — the business template should have ~25-30.

**Recommendation:** Cortex should auto-generate the template registry when building the template, using the same hash-based tracking as the dev template.

### GAP 7: Email Validation Dependency

**Issue:** ai_mail functional testing (send/receive) requires the branch to be registered in BRANCH_REGISTRY.json first. If registration fails or is delayed, email tests will fail even if ai_mail files are correctly deployed.

**Impact:** Test ordering matters. Registration (Test 8) must pass before email functional testing (Test 7 step 3).

**Recommendation:** Run tests in order: creation → structure → placeholders → registration → email functional. The test plan above already reflects this implicitly, but making it explicit.

### GAP 8: No Mention of .migrations.json

**Issue:** The dev branch_template includes `.migrations.json` (tracks template version upgrades). The spec doesn't mention it. When cortex later upgrades the business template, there's no migration tracking.

**Impact:** Future template upgrades won't know what version a business branch was created from.

**Recommendation:** Include `.migrations.json` in the business template, initialized to version 1.0.0.

---

## Execution Order

Run tests in this sequence (dependencies flow downward):

```
TEST 9  (Template flag)      — Verify flag works before creating
TEST 1  (Creation)           — Create the test branch
TEST 2  (Placeholders)       — Verify substitution
TEST 3  (Directory structure) — Verify business dirs
TEST 4  (No dev artifacts)   — Verify clean separation
TEST 5  (Trinity files)      — Verify identity/memory files
TEST 6  (NOTEPAD.md)         — Verify session bridge
TEST 10 (System prompt)      — Verify business-specific prompt
TEST 8  (Registration)       — Verify BRANCH_REGISTRY entry
TEST 7  (ai_mail)            — Verify email (depends on registration)
TEST 11 (Cleanup)            — Remove test branch
```

---

## Pass Criteria

- **ALL tests pass** = template is production-ready for first department creation
- **Any test fails** = document failure, fix before creating real departments
- **Spec gaps confirmed** = flag to VERA for decision before production use

---

*Created by TEAM_2 for DPLAN-007 verification. Review spec gaps before executing.*
