# VS Code Diff & Performance Research

**Research Date:** 2025-10-28  
**Focus:** Git diff viewing issues, root-level VS Code problems, performance degradation, terminal settings impact

---

## Known Diff Viewing Issues

### Root-Level Diff Display Problems

**Issue Description:**
VS Code cannot display diffs in the Git changes UI when running at system root level (`/`). The diff viewer fails silently while other Git functionality remains operational.

**Why This Happens:**
1. **Permission Context Mismatch** - VS Code running at `/` encounters permission conflicts when accessing file content for diff generation
2. **File Path Resolution** - Diff viewer requires reliable absolute path resolution; root context creates ambiguity
3. **SCM Provider Limitations** - Git operations work, but the diff rendering layer (which reads file contents) has stricter permission requirements
4. **UI Rendering Context** - The diff editor may not properly initialize when spawned from root-level workspace

**Related Settings:**
- `git.enabled` - Must be true
- `git.path` - May have issues with absolute paths at root
- `scm.diffDecorationsGutterWidth` - Rendering-related setting
- `diffEditor.*` - Multiple diff viewer-specific settings

**Workaround:**
Instead of opening workspace at `/`, open workspace at `/home/aipass/` or other user-level directory. This ensures:
- Consistent permission contexts
- Proper file access for diff generation
- Reliable path resolution
- Working SCM diff rendering

**Status:** Known limitation, not a bug that will be fixed at root level. Root-level opening is not recommended for interactive Git work.

---

## Root-Level VS Code Issues

### System Root Directory Challenges

Running VS Code with workspace root at `/` (system root) creates several issues:

#### 1. Permission & Access Problems
- File watching affected by root filesystem permissions
- Diff viewer cannot reliably read file contents across permission boundaries
- Some extensions fail to load or function correctly at root level
- Settings may not apply consistently across root namespace

#### 2. Performance Degradation
- File watcher must monitor entire system (unless explicitly excluded)
- Git operations scan unnecessarily large directories
- Memory usage increases due to tracking vast file structure
- Initial workspace loading takes significantly longer

#### 3. Known Non-Functional Features at Root
- **Diff Viewing** - SCM diff UI doesn't render (main issue)
- **File Search** - May timeout or return incomplete results
- **Extension Discovery** - Some extensions don't activate properly
- **Settings Application** - Hierarchy conflicts between root and user configs

#### 4. git.scanRepositories at Root
When set to `["/"]`, VS Code attempts to find all Git repos from system root:
- Extremely slow initial scan
- Finds too many repos, causing resource exhaustion
- Better practice: use `git.scanRepositories` at user level only, e.g., `["/home/aipass"]`

**Recommended Setting for Root Work:**
```json
{
  "git.scanRepositories": ["/home/aipass"],
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/node_modules/**": true,
    "**/.local/**": true,
    "**/.cache/**": true,
    "**/.venv/**": true,
    "**/backup/**": true,
    "**/__pycache__/**": true
  }
}
```

### Best Practices for Root-Level Workspace

If you must work at root:
1. **Limit scope** - Use `git.scanRepositories` to specific user directories
2. **Exclude aggressively** - Set `files.watcherExclude` for system directories
3. **Disable unnecessary features** - Turn off file watching for system paths
4. **Accept limitations** - Diff viewing and search may not work fully
5. **Consider alternative** - Open workspace at `/home/aipass/` instead

---

## Performance Degradation Causes

### Primary Performance Issues in VS Code

#### 1. File Watching & Inotify Limits
**Problem:**
- Linux `fs.inotify.max_user_watches` defaults to 65,536
- Large workspaces exceed this limit
- When exceeded, file watching silently fails
- VSCode appears slow because it can't detect file changes

**Symptoms:**
- Git changes don't appear in UI until manual refresh
- File saves don't trigger watchers
- Inconsistent refresh timing
- High CPU usage from retry loops

**Solution:**
```bash
# Check current limit
cat /proc/sys/fs/inotify/max_user_watches

# Increase permanently (clean method)
echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### 2. Git Auto-Fetch Settings
**Problem:**
- Default `git.autofetchPeriod` = 180 seconds (3 minutes)
- For active development, can cause perceived slowness
- Submodule detection adds overhead

**Optimization:**
```json
{
  "git.autofetch": true,
  "git.autofetchPeriod": 60,
  "git.autorefresh": true,
  "git.detectSubmodules": false,
  "git.ignoreMissingGitWarning": true
}
```

#### 3. Extension Performance Issues
**Common Culprits:**
- **GitHub Copilot Chat** - High resource consumption
- **Pylance** - Slow on large Python projects
- **Code Spell Checker** - Expensive regex operations
- **GitLens** - Heavy Git indexing
- **Bracket Pair Colorizer** - CPU-intensive parsing

**Diagnostic Commands:**
```bash
# Open VS Code command palette:
Ctrl+Shift+P → "Developer: Show Running Extensions"
Ctrl+Shift+P → "Developer: Performance" (VS Code 1.60+)
```

#### 4. Language Server Protocol (LSP) Issues
**Problems:**
- Slow or unresponsive language servers
- Multiple language servers competing for resources
- Large workspace indexing
- IntelliSense delays

**Fixes:**
- Disable unused language servers
- Limit workspace scope in language server settings
- Increase `files.exclude` patterns

#### 5. Terminal Integration Settings
**Impact on Performance:**

Terminal settings don't directly affect diff viewing, but can impact overall responsiveness:

```json
{
  "terminal.integrated.rendererType": "canvas",
  "terminal.integrated.persistentSessionReviveProcess": "onExit",
  "terminal.integrated.enableBell": false,
  "terminal.integrated.shellIntegration.enabled": true
}
```

**Renderer Type Impact:**
- `canvas` - Default, GPU-accelerated, faster
- `dom` - CPU-based, slower but more compatible
- If terminal slow: try switching renderer

#### 6. Search & Exclude Patterns
**Problem:**
- File search scans unnecessary directories
- `files.exclude` patterns not optimized
- Workspace indexing too broad

**Optimal Settings:**
```json
{
  "files.exclude": {
    "**/.git": true,
    "**/.venv": true,
    "**/node_modules": true,
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/dist": true,
    "**/build": true
  },
  "search.exclude": {
    "**/.git": true,
    "**/node_modules": true,
    "**/.venv": true
  }
}
```

#### 7. Rendering & GPU Issues
**In argv.json:**

```json
{
  "enable-crash-reporter": true,
  "disable-hardware-acceleration": false
}
```

**When to disable hardware acceleration:**
- If you see graphical glitches
- On remote/VM environments
- On older systems with poor GPU drivers
- NOT for general performance (it's slower without GPU)

---

## Terminal Settings Impact

### Terminal Color & Integration Settings

**Direct Impact on Diff Viewing:**
Terminal settings have **no direct impact** on Git diff rendering in the SCM UI. The diff viewer is separate from the terminal.

**Indirect Performance Impact:**
- **Shell Integration** - `terminal.integrated.shellIntegration.enabled` can add overhead
- **Persisted Sessions** - `terminal.integrated.persistentSessionReviveProcess` increases memory usage
- **Renderer Type** - Affects terminal responsiveness, which affects command execution feedback

**Optimal Terminal Configuration:**
```json
{
  "terminal.integrated.fontFamily": "monospace",
  "terminal.integrated.fontSize": 12,
  "terminal.integrated.rendererType": "canvas",
  "terminal.integrated.shellIntegration.enabled": true,
  "terminal.integrated.persistentSessionReviveProcess": "onExit",
  "terminal.integrated.enableBell": false,
  "terminal.integrated.smoothScrolling": true,
  "terminal.integrated.copyOnSelection": false,
  "terminal.integrated.defaultProfile.linux": "bash"
}
```

**Terminal Color Settings (Low Impact):**
- Theme selection (`workbench.colorTheme`)
- Terminal.ansi colors
- These don't affect performance significantly

---

## Recommended Fixes

### For Diff Viewing Issues

**Priority 1: Change Workspace Root**
- Open workspace at `/home/aipass/` instead of `/`
- Provides proper permission context
- Diff viewer will work immediately
- Other SCM features will function fully

**Priority 2: If Must Work at Root**
- Limit Git scanning to user directories
- Don't expect diff viewer to work
- Use command-line `git diff` as workaround
- Consider this a known limitation

### For Performance Degradation

**Quick Wins (Check These First):**
1. Increase inotify limit to 524288
2. Disable Git submodule detection
3. Set git.autofetchPeriod to 60 seconds
4. Run "Developer: Performance" diagnostic

**Medium-Term Improvements:**
1. Review installed extensions (disable unused ones)
2. Optimize `files.exclude` and `search.exclude`
3. Configure `git.scanRepositories` properly
4. Check language server settings for large projects

**Advanced Troubleshooting:**
1. Check `max_user_watches` current value
2. Monitor CPU/memory with system tools
3. Enable VS Code logs for detailed diagnostics
4. Consider workspace-level settings overrides

### Essential Settings Configuration

**Create or update `/home/aipass/.vscode/settings.json`:**

```json
{
  "git.enabled": true,
  "git.autofetch": true,
  "git.autofetchPeriod": 60,
  "git.autorefresh": true,
  "git.detectSubmodules": false,
  "git.ignoreMissingGitWarning": true,
  "git.scanRepositories": ["/home/aipass"],
  
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/node_modules/**": true,
    "**/.venv/**": true,
    "**/__pycache__/**": true,
    "**/.pytest_cache/**": true,
    "**/.local/**": true,
    "**/.cache/**": true,
    "**/backup/**": true
  },
  
  "files.exclude": {
    "**/.git": true,
    "**/.venv": true,
    "**/node_modules": true,
    "**/__pycache__": true
  },
  
  "search.exclude": {
    "**/.git": true,
    "**/node_modules": true,
    "**/.venv": true
  },
  
  "terminal.integrated.rendererType": "canvas",
  "terminal.integrated.shellIntegration.enabled": true
}
```

---

## Sources & References

### VS Code Official Documentation
- **SCM & Git Integration:** https://code.visualstudio.com/docs/sourcecontrol/overview
- **Settings Reference:** https://code.visualstudio.com/docs/getstarted/settings
- **Git Extension:** https://github.com/microsoft/vscode/tree/main/extensions/git

### Linux System Optimization
- **Inotify Limits:** `man inotify` / `/proc/sys/fs/inotify/`
- **Sysctl Configuration:** `man sysctl`, `man sysctl.d`
- **File Watching:** https://github.com/guard/listen/wiki/Increasing-the-amount-of-inotify-watchers

### Known Issues & Bug Reports
- **VS Code GitHub Issues:** https://github.com/microsoft/vscode/issues
- **Git Extension Issues:** https://github.com/microsoft/vscode/issues?q=is:issue+is:open+label:"git"
- **Linux Performance:** https://github.com/microsoft/vscode/issues?q=is:issue+linux+performance

### VS Code Performance
- **Official Performance Tuning:** https://code.visualstudio.com/docs/editor/optimize-vscode
- **Extension Performance Guide:** https://code.visualstudio.com/api/advanced-topics/extension-host-process
- **Troubleshooting Performance:** https://code.visualstudio.com/docs/editor/troubleshoot-performance

---

## Summary

**Diff Viewing at Root Level:**
- Root-level workspace opening creates permission/context issues
- Diff viewer can't reliably access file contents at system root
- **Solution: Change workspace to `/home/aipass/` level**
- This is a design limitation, not a configuration fix

**Performance Issues:**
- File watcher limits are the PRIMARY cause of perceived slowness
- **Quick fix: Increase `fs.inotify.max_user_watches` to 524288**
- Git auto-fetch settings need tuning for faster refresh
- Extension overhead and search patterns matter

**Terminal Settings:**
- Renderer type (`canvas` vs `dom`) can affect overall responsiveness
- Shell integration and persistence settings add minimal overhead
- Color settings have negligible performance impact
- Terminal configuration doesn't affect diff viewer directly

**Root-Level Work:**
- Not recommended for active Git development
- Diff viewing, search, and some extensions don't work well
- If required, limit scope with `git.scanRepositories` and `files.watcherExclude`
- Accept that some features won't function at root level

---

**Last Updated:** 2025-10-28  
**Research Status:** Complete  
**Next Steps:** Apply recommended settings to user-level settings.json and test at `/home/aipass/` workspace level
