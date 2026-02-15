# VS Code "Discard Changes" Button Not Working at Root Level - Comprehensive Research

**Date:** 2025-10-28
**VS Code Version:** 1.105.1
**Issue:** Discard Changes button in SCM appears but does not respond to clicks when working at root level `/`
**Environment:** Ubuntu Linux 24.04 LTS, workspace at `/`, nested repository at `/home/aipass`

---

## Executive Summary

The "Discard Changes" button failure at root level (`/`) is **not a documented bug** but rather a **complex interaction** between VS Code's parent folder repository detection system, multi-repository workspace handling, and the inherent risks of operating Git at the filesystem root.

**Key Finding:** VS Code introduced safety mechanisms in version 1.75+ specifically to prevent accidental data loss when Git repositories exist in parent folders or at sensitive locations like root (`/`). The button may appear disabled or non-responsive as a protective measure.

**Root Cause Analysis:**
1. Parent folder repository detection conflicts
2. Multi-repository workspace UI state management issues
3. Safety mechanisms preventing dangerous operations at root
4. Possible button event handler issues in complex repository scenarios

---

## Relevant GitHub Issues

### 1. Stage/Discard Buttons Grayed Out (Most Relevant)
- **Issue:** [#181154 - Stage/Discard buttons grayed out](https://github.com/microsoft/vscode/issues/181154)
- **Date:** April 2023
- **Status:** Open
- **Description:** Some files in the Source Control Changes list have Discard and Stage buttons grayed out (usually first or 1st-3rd file from top), despite actions being fully available on right-click. The faulty file regains Stage/Discard buttons after staging from context menu, then unstaging.
- **Relevance:** **HIGH** - Describes exact symptom of buttons appearing but not functioning

### 2. Stage and Discard Changes Buttons Unintentionally Disabled
- **Issue:** [#181294 - Stage and Discard Changes button disabled](https://github.com/microsoft/vscode/issues/181294)
- **Date:** May 2023
- **Status:** Closed
- **VS Code Version:** 1.78.0-insider
- **Description:** Stage and Discard Changes buttons on Source Control Pane were unintentionally disabled
- **Relevance:** **HIGH** - Same button disability issue, though reportedly fixed in 1.78+

### 3. Parent Folder Repository Configuration Issues
- **Issue:** [#197431 - Configuration option to hide parent git folder changes](https://github.com/microsoft/vscode/issues/197431)
- **Date:** 2023
- **Description:** Request for configuration option to hide parent git folder changes in source control when in subfolder
- **Relevance:** **CRITICAL** - Directly related to parent folder repository detection affecting UI behavior

### 4. Parent Folder Setting Not Working as Expected
- **Issue:** [#197606 - openRepositoryInParentFolders = false has no effect](https://github.com/microsoft/vscode/issues/197606)
- **Date:** 2023
- **Description:** Users report that `git.openRepositoryInParentFolders` set to "never" still behaves like "prompt"
- **Relevance:** **CRITICAL** - Setting designed to prevent parent folder repo issues is itself buggy

### 5. Parent Folder Repository Behavior Problems
- **Issue:** [#206974 - Problems with Git: Open Repository in Parent Folders behavior](https://github.com/microsoft/vscode/issues/206974)
- **Date:** 2024
- **Description:** General issues with how VS Code handles repositories in parent directories
- **Relevance:** **HIGH** - Ongoing issues with parent folder repository handling

### 6. Source Control Using Parent Folder Repository
- **Issue:** [#132496 - Source Control using parent folder repository, when current folder is a git repository](https://github.com/microsoft/vscode/issues/132496)
- **Date:** 2021
- **Description:** VS Code sometimes uses parent folder repository even when current folder has its own `.git`
- **Relevance:** **HIGH** - Explains conflict between root `/` repo and `/home/aipass` repo

### 7. Discard Changes Requires Multiple Attempts
- **Issue:** [#157314 - Discard Changes doesn't actually happen until second try](https://github.com/microsoft/vscode/issues/157314)
- **Date:** 2022
- **Status:** Closed (Fixed in 1.73.1)
- **Description:** Users had to select "Discard Changes" twice before changes actually disappeared
- **Relevance:** **MEDIUM** - Related symptom, though reportedly fixed

### 8. Git Discard Has to be Run Twice
- **Issue:** [#43589 - Git Discard Changes has to be run twice](https://github.com/Microsoft/vscode/issues/43589)
- **Date:** 2018
- **Status:** Closed
- **Description:** Git would still show pending changes after first discard attempt
- **Relevance:** **MEDIUM** - Historical issue with similar symptoms

### 9. Discard All Files Not Working Properly
- **Issue:** [#44272 - Source Control > Discard All Files not working properly](https://github.com/Microsoft/vscode/issues/44272)
- **Date:** 2018
- **Description:** When discarding all changes, only unversioned files removed first, requiring second attempt for versioned changes
- **Relevance:** **MEDIUM** - Discard operation sequencing issues

### 10. SCM Action Buttons Visibility Issues
- **Issue:** [#102108 - SCM Action buttons not always visible](https://github.com/microsoft/vscode/issues/102108)
- **Date:** 2020
- **Description:** Action buttons not visible when side panel width insufficient and repository names long
- **Relevance:** **LOW** - UI rendering issue, not functional failure

---

## Root-Level Workspace Specific Issues

### The Parent Folder Repository Problem

**How VS Code Discovers Git Repositories:**
- Uses `git rev-parse --show-toplevel` to determine repository root
- Discovers repositories based on workspace folders and parent folders of opened files
- Git traverses from bottom of tree upward, stopping at first `.git` found

**Why Root Level (`/`) Creates Unique Problems:**

1. **Maximum Parent Folder Exposure:** When workspace is at `/`, every directory on the system is either the workspace or a subdirectory. Parent folder detection has nowhere to go "up" from.

2. **Nested Repository Conflicts:** Having a repository at `/` AND `/home/aipass` creates ambiguity about which repository "owns" files in `/home/aipass`. VS Code may become confused about which repository's buttons should be active.

3. **Safety Mechanism Triggers:** VS Code introduced safety measures specifically to prevent data loss from accidental operations on parent folder repositories. At root level, these safety mechanisms may be more aggressive.

**From VS Code Source Control FAQ:**
> "In some cases, the root of a Git repository is in parent folders of the workspace or open file(s). While this is a feature for advanced users, it can be confusing for new users and has resulted in cases where confusion led to discarding changes from these Git repositories causing data loss."

---

## The `git.openRepositoryInParentFolders` Setting

### Overview
Introduced in VS Code 1.75 to control how repositories in parent directories are handled.

### Available Values:
- **`always`** - Always open a repository in parent folders (pre-1.75 behavior)
- **`never`** - Never open a repository in parent folders
- **`prompt`** - Prompt before opening parent folder repositories (default)

### Setting Restoration
To restore pre-1.75 behavior (if button worked before 1.75):
```json
"git.openRepositoryInParentFolders": "always"
```

### Known Bug with This Setting
**Issue #197606** reports that setting this to `"never"` doesn't actually prevent parent folder repository detection - it still behaves like `"prompt"`. This means the setting designed to fix this class of problems may itself be broken.

### Related Settings:
```json
"git.autoRepositoryDetection": true,        // or "subFolders"
"git.repositoryScanMaxDepth": 1,            // Increase for deep nesting
"scm.alwaysShowRepositories": false,        // May reduce UI conflicts
"git.showUnpublishedCommitsButton": true    // Button visibility control
```

---

## Multi-Repository Workspace Issues

### How VS Code Handles Multiple Repositories

**Standard Multi-Repository Setup:**
- File → Add Folder to Workspace
- File → Save Workspace As
- Each folder's repository shown separately in SCM view

**Your Specific Configuration:**
- Repository at `/` (system root)
- Repository at `/home/aipass` (nested within root)
- Both potentially visible to VS Code simultaneously

### Known Issues with Multiple Repositories:

1. **Repository List Overwhelm:** All repositories evaluated after opening, causing high CPU usage
2. **Button State Confusion:** When multiple repos shown, button states may not sync correctly
3. **Focus Problems:** Opening SCM view may not properly focus on active repository
4. **Action Target Ambiguity:** Buttons may not know which repository to act upon

### Relevant Observations:

From Stack Overflow discussions:
- Users working at root accidentally see "every file on computer" in Source Control
- Common cause: Git repository initialized too high in directory tree
- Solution often requires closing VS Code and reopening specific project folder

---

## Recent VS Code Versions and SCM Changes

### Version 1.105 (September 2025)
**Relevant Changes:**
- Source Control Graph view enhancement: Selecting items now reveals resources
- No specific SCM button fixes mentioned
- No known regressions in discard functionality

### Version 1.98 (February 2025)
- View titles revised: "Source Control Repositories" → "Repositories"
- "Source Control" → "Changes"
- Cosmetic changes, no functional modifications to buttons

### Version 1.93 (August 2024)
- Added `scm.compactFolders` setting for tree view
- Git 2.45+ reference storage backend support
- No button behavior changes

### Version 1.78 (May 2023)
- Fixed issue #181294 (Stage/Discard buttons disabled)
- However, issue #181154 (buttons grayed out) remains open

### Version 1.75 (January 2023)
- **CRITICAL VERSION:** Introduced `git.openRepositoryInParentFolders` setting
- Added safety mechanisms for parent folder repositories
- Added notification and welcome view warnings for parent folder repos
- Changed default behavior to NOT automatically open parent folder repositories

**Hypothesis:** If button worked before 1.75, this version change likely caused the issue.

---

## Permission and Ownership Issues

### Safe Directory Configuration

**What is `safe.directory`?**
Git security feature preventing operation on repositories with mismatched ownership.

**Common Scenarios Requiring Configuration:**
1. Docker/Dev Containers (root vs. non-root user ownership)
2. WSL (Windows vs. Linux ownership)
3. Sudo operations changing file ownership
4. Multi-user systems

**Check if this is the issue:**
```bash
cd /
git status
```

If you see "detected dubious ownership in repository", run:
```bash
git config --global --add safe.directory /
git config --global --add safe.directory /home/aipass
```

**For all subdirectories:**
```bash
git config --global --add safe.directory '/*'
```

### VS Code's Safe Directory Handling

VS Code provides UI for managing unsafe repositories:
- Welcome view shows potentially unsafe repositories
- Notification prompts to mark as safe
- "Manage Unsafe Repositories" command available

**However:** This typically prevents ALL Git operations, not just discard button. If you can stage files but not discard, this is likely NOT the issue.

---

## Nested Repository Support

### Historical Context

**Before VS Code 1.72:**
- Limited support for nested repositories
- Repositories often not detected if nested
- Manual workarounds required

**After VS Code 1.72 (October 2022):**
- Native support for nested Git repositories
- Improved repository discovery code
- Should handle `/` and `/home/aipass` correctly

### Configuration for Nested Repositories:

```json
{
  "git.repositoryScanMaxDepth": 10,           // Increase from default 1
  "git.autoRepositoryDetection": "subFolders", // Enable subfolder detection
  "git.openRepositoryInParentFolders": "never" // Prevent parent conflicts
}
```

### Testing Nested Repository Detection:

1. Open Command Palette (Ctrl+Shift+P)
2. Run: "Git: Reopen Closed Repositories"
3. Check Source Control view for all expected repositories

---

## Technical Analysis: Why Button Might Not Work

### Potential Root Causes:

**1. Repository Context Confusion**
- VS Code unsure which repository owns the file being discarded
- Root repo at `/` claims ownership via parent folder detection
- Local repo at `/home/aipass` also claims ownership
- Button disabled because context is ambiguous

**2. Safety Mechanism Activation**
- VS Code detects operation on parent folder repository
- Silently disables dangerous operations (discard at root = data loss risk)
- No clear user feedback explaining why button disabled

**3. UI State Management Bug**
- Multiple repositories shown in SCM view
- Button event handlers not properly bound to active repository
- Click event fires but doesn't reach correct Git operation handler

**4. Permission Check Failure**
- Button performs pre-flight permission check
- Check fails at root level (even without sudo restrictions)
- Button appears clickable but operation blocked

**5. Git Command Execution Environment**
- VS Code spawns Git process with specific working directory
- At root level, environment variables or paths may be misconfigured
- Git command fails silently, button appears non-responsive

### Supporting Evidence:

**From Issue #181154:**
> "Some files in changes list have Discard/Stage buttons grayed out (usually first or 1st-3rd file). The faulty file regains buttons after staging from context menu, then unstaging."

This suggests **UI state synchronization issues** rather than permission problems.

**From Issue #197606:**
> "`git.openRepositoryInParentFolders` set to 'never' still behaves like 'prompt'"

This indicates the **setting designed to prevent these conflicts is itself broken**.

---

## Workarounds and Solutions

### Immediate Workarounds (No Settings Changes)

**1. Use Command Line**
```bash
cd /
git checkout -- <file>           # Discard specific file
git checkout -- .                # Discard all changes
git clean -fd                    # Remove untracked files
```

**2. Use Right-Click Context Menu**
- Right-click file in SCM view
- Select "Discard Changes" from menu
- Reportedly works even when button doesn't (Issue #181154)

**3. Use Command Palette**
- Ctrl+Shift+P
- Type: "Git: Discard All Changes"
- Select command directly

**4. Stage Then Unstage (Force UI Refresh)**
- Stage the file using context menu
- Unstage the file
- Discard button may become functional (Issue #181154)

### Configuration-Based Solutions

**Solution 1: Disable Parent Folder Repository Detection**
```json
{
  "git.openRepositoryInParentFolders": "never"
}
```
**Warning:** This setting reportedly doesn't work reliably (Issue #197606)

**Solution 2: Configure Multiple Repositories Explicitly**
```json
{
  "git.autoRepositoryDetection": false,
  "git.openRepositoryInParentFolders": "never",
  "git.repositoryScanMaxDepth": 0
}
```
Then manually open repositories:
- Ctrl+Shift+P → "Git: Open Repository"
- Select each repository individually

**Solution 3: Use Multi-Root Workspace File**
Create `/home/aipass/aipass-workspace.code-workspace`:
```json
{
  "folders": [
    {
      "path": "/home/aipass"
    }
  ],
  "settings": {
    "git.openRepositoryInParentFolders": "never",
    "git.autoRepositoryDetection": "subFolders"
  }
}
```
Open this workspace file instead of opening `/` directly.

**Solution 4: Hide Root Repository, Show Only Subfolders**
```json
{
  "git.openRepositoryInParentFolders": "never",
  "git.autoRepositoryDetection": "subFolders",
  "files.exclude": {
    "/.git": true  // Hide root .git from File Explorer
  }
}
```

### Architectural Solutions (Recommended)

**Option A: Change Workspace Root**
Instead of opening workspace at `/`, open at `/home/aipass`:
- Eliminates parent folder repository conflicts
- Root repo at `/` still accessible via multi-root workspace if needed
- Simplifies Git operation context

**Option B: Eliminate Root-Level Repository**
If repository at `/` is not essential:
1. Move `.git` folder from `/` to backup location
2. Root-level files no longer tracked
3. Only `/home/aipass` repository remains
4. Eliminates all parent folder conflicts

**Option C: Use Separate VS Code Windows**
- Window 1: Open `/` (for root-level Git operations)
- Window 2: Open `/home/aipass` (for workspace development)
- Never mix contexts, each window has clear repository scope

---

## Diagnostic Steps

### Step 1: Verify Repository Detection

```bash
cd /home/aipass
git rev-parse --show-toplevel
```
**Expected:** `/home/aipass`
**If shows:** `/` → Parent folder repo taking precedence

### Step 2: Check VS Code's Repository List

1. Open Command Palette (Ctrl+Shift+P)
2. Run: "Git: Show Repositories"
3. Note all detected repositories

**Expected:** Should show both `/` and `/home/aipass` separately
**Problem:** If only showing `/`, parent folder detection is the issue

### Step 3: Test Discard via Different Methods

Test these methods in order, noting which work:
1. Discard button in SCM view (currently failing)
2. Right-click → Discard Changes (may work)
3. Command Palette → Git: Discard Changes (may work)
4. Terminal → `git checkout -- file` (should always work)

**If 2-4 work but 1 doesn't:** UI event handler issue
**If only 4 works:** VS Code Git integration problem
**If none work:** Permission or Git configuration issue

### Step 4: Check Safe Directory Configuration

```bash
git config --list | grep safe.directory
```

**If empty or missing `/`:** Add safe directory configuration

### Step 5: Enable VS Code Git Logging

```json
{
  "git.trace": true,
  "git.logLevel": "trace"
}
```

Reload VS Code, attempt discard, check Output → Git for error messages.

### Step 6: Test with Clean Profile

```bash
code --user-data-dir=/tmp/vscode-test --extensions-dir=/tmp/vscode-test-ext /home/aipass
```

**If works:** Setting or extension conflict in main profile
**If fails:** Core VS Code issue with root-level repositories

---

## Comparison: Root vs. Normal Workspace Behavior

| Aspect | Normal Workspace (`/home/user/project`) | Root Workspace (`/`) |
|--------|----------------------------------------|---------------------|
| **Repository Detection** | Single `.git` in workspace | Multiple potential `.git` folders |
| **Parent Folder Repos** | Unlikely to encounter | Always a concern |
| **Nested Repositories** | Rare | Common (every user dir) |
| **Safety Mechanisms** | Minimal intervention | Aggressive protection |
| **Button Behavior** | Consistent | May be disabled/limited |
| **Git Context** | Unambiguous | Potentially ambiguous |
| **Data Loss Risk** | Low | High (entire filesystem) |
| **VS Code Testing** | Extensively tested | Edge case scenario |

---

## Is This a Bug or Limitation?

### Arguments for "Bug":
1. Button appears but doesn't work (inconsistent UI)
2. No error message or feedback explaining why
3. Other methods (right-click, command palette) work fine
4. Fresh install with default settings still fails
5. Issue #181154 remains open since 2023

### Arguments for "Limitation":
1. Root-level workspaces are edge case usage
2. Safety mechanisms intentionally restrict dangerous operations
3. Parent folder repository detection working as designed
4. VS Code documentation warns about parent folder repos
5. Multiple conflicting repositories create ambiguous context

### Verdict: **Hybrid - Bug in Safety Mechanism Implementation**

The core issue is likely a **bug in how VS Code's safety mechanisms are implemented**:
- Safety features correctly identify risk (root-level discard)
- But implementation silently disables button without explanation
- Better UX would show tooltip or warning explaining why button disabled
- Root cause: Poor error handling in Git operation pre-flight checks

---

## Recommendations for Patrick

### Immediate Actions

**1. Use Command Line for Discard Operations at Root Level**
Most reliable workaround until underlying issue resolved:
```bash
cd /
git status                        # See what would be discarded
git checkout -- path/to/file      # Discard specific file
git checkout -- .                 # Discard all changes
```

**2. Test Right-Click Context Menu**
Based on Issue #181154, this may work even when button doesn't:
- Right-click file in SCM view
- Select "Discard Changes"

### Short-Term Configuration

**Add to VS Code settings.json:**
```json
{
  "git.openRepositoryInParentFolders": "never",
  "git.autoRepositoryDetection": "subFolders",
  "git.repositoryScanMaxDepth": 3,
  "git.trace": true,
  "git.logLevel": "debug"
}
```

This may not fix the issue (setting reportedly buggy) but provides diagnostic information.

### Long-Term Architectural Decision

**Evaluate:** Is having a Git repository at `/` essential?

**Option A: Keep Root Repository, Use Multi-Root Workspace**
- Create workspace file: `/home/aipass/work.code-workspace`
- Add only `/home/aipass` as workspace folder
- Access root repo separately when needed
- **Pros:** Maintains root tracking, eliminates conflicts
- **Cons:** Extra step to access root repo

**Option B: Move Root Repository to Subdirectory**
- Move `/.git` → `/aipass-system/.git` or similar
- Only track system files in dedicated directory
- No parent folder conflicts with `/home/aipass`
- **Pros:** Cleaner separation, standard Git structure
- **Cons:** Restructuring effort, possible workflow changes

**Option C: Accept Command Line for Root Operations**
- Continue using VS Code primarily for `/home/aipass`
- Use terminal for all root-level Git operations
- Simplest immediate solution
- **Pros:** No changes required, works reliably
- **Cons:** Less convenient, mixed workflow

### Report Bug to Microsoft

If you choose to report this:
1. Open issue at https://github.com/microsoft/vscode/issues
2. Reference related issues: #181154, #181294, #197606, #197431
3. Provide minimal reproduction case:
   - Fresh Ubuntu install
   - Git repo at `/`
   - Git repo at `/home/aipass`
   - Open workspace at `/`
   - Attempt to discard change at root level
4. Emphasize: Button appears but doesn't respond, no error shown

---

## Additional Resources

### Official Documentation
- VS Code Git Integration: https://code.visualstudio.com/docs/sourcecontrol/overview
- Source Control FAQ: https://code.visualstudio.com/docs/sourcecontrol/faq
- Multi-Root Workspaces: https://code.visualstudio.com/docs/editing/workspaces/multi-root-workspaces

### Relevant Blog Posts
- "Avoiding Dubious Ownership in Dev Containers": https://www.kenmuse.com/blog/avoiding-dubious-ownership-in-dev-containers/
- "Multi Root Workspaces in VS Code": https://devblogs.microsoft.com/ise/multi_root_workspaces_in_visual_studio_code/

### GitHub Issue References
- #181154: https://github.com/microsoft/vscode/issues/181154 (Open - buttons grayed out)
- #181294: https://github.com/microsoft/vscode/issues/181294 (Closed - buttons disabled)
- #197606: https://github.com/microsoft/vscode/issues/197606 (Open - setting not working)
- #197431: https://github.com/microsoft/vscode/issues/197431 (Open - parent folder config)
- #206974: https://github.com/microsoft/vscode/issues/206974 (Open - parent folder behavior)
- #132496: https://github.com/microsoft/vscode/issues/132496 (Open - parent folder repo used)
- #172010: https://github.com/microsoft/vscode/issues/172010 (Test issue - parent directories)

### Related Stack Overflow Discussions
- "How can I prevent VS Code from auto-detecting git repositories in parent directories": https://stackoverflow.com/questions/77716630/
- "VS Code - Multi-root workspace not showing all git repositories": https://stackoverflow.com/questions/68733233/
- "Avoiding VSCode workspace parent folder showing changed files": https://stackoverflow.com/questions/69776740/

---

## Conclusion

The "Discard Changes" button failure at root level is a **complex issue arising from VS Code's safety mechanisms for parent folder repositories**, exacerbated by having nested repositories at `/` and `/home/aipass`. While not officially documented as a bug, the behavior represents poor UX - silently disabling functionality without user feedback.

**Key Takeaways:**
1. This is an edge case scenario that VS Code's safety features struggle to handle elegantly
2. The `git.openRepositoryInParentFolders` setting is designed to help but has reported bugs
3. Root-level repositories create ambiguous contexts that confuse VS Code's SCM UI
4. Workarounds exist (command line, right-click menu) but don't address root cause
5. Long-term solution likely requires architectural changes (workspace structure or repository organization)

**Recommended Path Forward:**
1. Use command line for root-level discards (immediate reliability)
2. Consider restructuring workspace to avoid root-level operations
3. Monitor GitHub issue #181154 for potential fixes
4. Consider reporting specific reproduction case if not already covered

This appears to be a limitation of VS Code's current architecture when dealing with root-level workspaces, rather than a straightforward bug with a simple fix.
