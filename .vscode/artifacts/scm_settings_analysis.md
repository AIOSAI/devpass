# SCM Settings Analysis - Discard Button Investigation

## Critical Findings

**Changes Made on 2025-10-27 18:32 (Yesterday):**
Three settings were removed from the User settings, which is causing the discard button malfunction:

1. `git.autoRepositoryDetection: false` - **REMOVED**
2. `git.scanRepositories: ["/", "/home/aipass"]` - **REMOVED**  
3. `scm.alwaysShowRepositories: false` → changed to `true`
4. `git.openRepositoryInParentFolders: "never"` → changed to `"always"`

## Current SCM Settings (All Config Files)

### /home/aipass/.config/Code/User/settings.json (Active User Settings)

**Git Settings:**
```json
{
  "git.enableSmartCommit": true,
  "git.confirmSync": false,
  "git.openRepositoryInParentFolders": "never",  // Currently set
  "git.enabled": true,
  "git.path": "/usr/bin/git",
  "git.openDiffOnClick": false,
  "git.autofetch": true,                        // MISSING in current
  "git.autofetchPeriod": 60,                    // MISSING in current
  "git.autoRepositoryDetection": false,         // MISSING - This is critical!
  "git.scanRepositories": ["/", "/home/aipass"] // MISSING - This is critical!
}
```

**SCM Settings:**
```json
{
  "scm.defaultViewMode": "tree",
  "scm.defaultViewSortKey": "path",
  "scm.alwaysShowRepositories": false  // Currently set to false
}
```

### Previous Working Settings (VWWo.json from 2025-10-27 18:32)

**Key differences:**
```json
{
  "git.openRepositoryInParentFolders": "always",    // Was "always"
  "scm.alwaysShowRepositories": true,                // Was "true"
  // These were present:
  "git.autoRepositoryDetection": false,
  "git.scanRepositories": ["/", "/home/aipass"]
}
```

### Workspace Settings
- **/.vscode/settings.json** - Does NOT exist (directory exists but file is empty)
- **/home/aipass/.vscode/settings.json** - Does NOT exist

## Root Cause Analysis

**The discard button stopped working because:**

1. **Missing `git.autoRepositoryDetection`** - VS Code can't properly detect the Git repository at root level without explicit configuration
2. **Missing `git.scanRepositories`** - Without this, VS Code doesn't know to look for repos at `/` and `/home/aipass`
3. **Changed `scm.alwaysShowRepositories`** - Affects how repositories are displayed in the SCM view
4. **Changed `git.openRepositoryInParentFolders`** - May affect how VS Code navigates the repo structure

## Settings That Control Discard Button

The discard/revert changes functionality relies on:

1. **`git.enabled`** - Enables/disables Git integration (currently: `true` ✓)
2. **`git.path`** - Path to git executable (currently: `"/usr/bin/git"` ✓)
3. **`git.autoRepositoryDetection`** - **MISSING** - Tells VS Code how to find repos
4. **`git.scanRepositories`** - **MISSING** - Explicit list of repo paths to monitor
5. **`scm.defaultViewMode`** - Controls tree vs list view (currently: `"tree"`)
6. **`scm.alwaysShowRepositories`** - Shows/hides repository selector

## Settings That Control Icons/Decorations

1. **`git.decorations.enabled`** - NOT found (uses default)
2. **`workbench.iconTheme`** - Set to `"vscode-icons"` (may affect file icons)
3. **`scm.defaultViewMode`** - Set to `"tree"` (affects layout)

## Recently Changed Settings (Last 2 Days)

**File: VWWo.json - Modified: 2025-10-27 18:32:39**
- Removed `git.autoRepositoryDetection: false`
- Removed `git.scanRepositories: ["/", "/home/aipass"]`
- Changed `scm.alwaysShowRepositories: false` → `true`
- Changed `git.openRepositoryInParentFolders: "never"` → `"always"`

**Current settings.json - Modified: 2025-10-28 11:57:02 (Today)**
- Shows the settings WITHOUT the critical repository detection configs

## Settings to Check/Change - SOLUTION

**Add these lines back to `/home/aipass/.config/Code/User/settings.json`:**

```json
{
  "git.autoRepositoryDetection": false,
  "git.scanRepositories": [
    "/",
    "/home/aipass"
  ],
  "git.autofetch": true,
  "git.autofetchPeriod": 60
}
```

**Optionally revert these (may help but not critical):**
```json
{
  "git.openRepositoryInParentFolders": "always",  // Change from "never" to "always"
  "scm.alwaysShowRepositories": true              // Change from false to true
}
```

## Comparison: Root vs /home/aipass Workspaces

**Root level (`/`):**
- No workspace settings file exists (/.vscode/settings.json doesn't exist)
- Empty .vscode directory at root
- Relies entirely on User settings

**Working level (`/home/aipass`):**
- No workspace settings file exists either
- Also relies on User settings
- Difference: When the critical settings existed, VS Code could track both repos

**Why it works at /home/aipass but not at `/`:**
The `/home/aipass` directory is listed in the `git.scanRepositories` array (when present), so VS Code explicitly monitors it. The root `/` is also listed, but when those settings were removed, VS Code fell back to automatic detection which doesn't work well with `git.autoRepositoryDetection: false` being removed.

## Additional Notes

- No special keybindings affecting SCM found
- No SCM-related extensions installed (only Copilot extensions)
- The icon change Patrick mentioned is likely due to the view mode or repository display changes
- File history shows this was an intentional settings change on Oct 27th at 6:32 PM

## Recommended Actions

1. **Restore the missing settings** to `/home/aipass/.config/Code/User/settings.json`
2. **Reload VS Code window** (Ctrl+Shift+P → "Reload Window")
3. **Verify** the discard button appears and functions at root level
4. If still having issues, also try reverting the `scm.alwaysShowRepositories` and `git.openRepositoryInParentFolders` settings

