# VS Code Performance Optimization Guide

**Created:** 2025-11-22
**Status:** Active Reference
**Impact:** 1.2GB RAM freed, 60% Pylance reduction

## Problem Statement

VS Code RAM usage was creeping up over long sessions (51%+ baseline), with noticeable lag during multi-branch workflow operations. Multiple Claude Code instances running caused no issues, suggesting the problem was VS Code configuration rather than workload.

## Root Causes Identified

### 1. Pylance Background Indexing (1GB RAM)
- `python.analysis.indexing: true` (default) caused continuous background indexing
- Analyzed ALL Python files including high-churn directories (MEMORY_BANK, logs, .claude/*)
- Not needed for Claude Code-based navigation workflow

### 2. GitLens Aggressive Features (CPU drain)
- `codeLens.enabled: true` - inline blame annotations on every file
- `currentLine.enabled: true` - continuous git history lookups
- `hovers.enabled: true` - hover processing for all files
- Major CPU overhead with large git histories

### 3. Git Auto-Refresh (CPU churn)
- `git.autorefresh: true` constantly ran `git status` in background
- Multi-branch setup amplified the impact

### 4. Multi-Layer Scanning Issue
- File watcher exclusions alone don't stop language servers
- Pylance, GitLens, and other tools scan independently
- Need separate exclusions for each layer

### 5. Zombie Electron Processes
- 4 Antigravity instances (3GB total) running with no visible windows
- Closed windows 6-8 hours earlier but processes persisted
- Electron apps don't quit when window closes (Linux behavior)

## Solutions Implemented

### VS Code Settings (`/home/aipass/.vscode/settings.json`)

```json
{
  // Git performance
  "git.autorefresh": false,  // Manual refresh only

  // Python/Pylance
  "python.analysis.indexing": false,  // Disable background indexing
  "python.analysis.packageIndexDepths": [
    { "name": "", "depth": 1, "includeAllSymbols": false }
  ],

  // GitLens minimal mode
  "gitlens.codeLens.enabled": false,
  "gitlens.currentLine.enabled": false,
  "gitlens.hovers.enabled": false,
  "gitlens.statusBar.enabled": true,  // Keep status bar only
  "gitlens.views.repositories.autoRefresh": false,

  // Editor optimizations
  "editor.codeLens": false,
  "editor.minimap.enabled": false,
  "diffEditor.renderSideBySide": false
}
```

### Pyrightconfig Exclusions (`/home/aipass/pyrightconfig.json`)

Added high-churn directories that Pylance was unnecessarily analyzing:

```json
{
  "exclude": [
    // ... existing exclusions ...
    "**/MEMORY_BANK/**",
    "**/system_logs/**",
    "**/logs/**",
    "**/.cache/**",
    "**/.local/**",
    "**/.claude/debug/**",
    "**/.claude/file-history/**",
    "**/.claude/session-env/**",
    "**/.vscode/extensions/**"
  ]
}
```

### Process Management Tools

Created `/home/aipass/.local/bin/antigravity-status`:

```bash
# Check Antigravity processes
antigravity-status
ag-status  # Short version

# Kill with confirmation
antigravity-status --kill
ag-status -k
```

## Results

**Before:**
- RAM: 7.6GB (51% of 15GB)
- Pylance: 1GB
- 4 zombie Antigravity processes: 3GB
- Continuous CPU usage from background scanning

**After:**
- RAM: 6.4GB (42% of 15GB) - **1.2GB freed**
- Pylance: 466MB - **60% reduction**
- All zombie processes killed
- Minimal background CPU usage

## Key Learnings

1. **Multi-Layer Exclusions Required**
   - `files.watcherExclude` ≠ language server exclusions
   - Each tool (Pylance, GitLens, etc.) needs separate configuration
   - Cannot rely on one exclusion list to cover all tools

2. **Background Indexing vs Navigation Pattern**
   - Background indexing optimizes for IntelliSense/autocomplete
   - Claude Code workflow uses AI for navigation, not traditional IDE features
   - Disabling indexing = huge RAM savings with no workflow impact

3. **Electron Process Lifecycle**
   - Closing window ≠ quitting app (especially on Linux)
   - Always use `Ctrl+Q` or explicit File → Quit
   - Create monitoring tools for zombie process detection

4. **GitLens Feature Overhead**
   - CodeLens annotations scan entire git history per file
   - Status bar provides 90% of value with 10% of overhead
   - Disable aggressive features, keep minimal status display

## Maintenance Commands

```bash
# Check VS Code process memory
ps aux | grep "/usr/share/code" | awk '{sum+=$6} END {print "VS Code RAM: " sum/1024 " MB"}'

# Check for zombie Antigravity
ag-status

# Monitor Pylance specifically
ps aux | grep pylance

# Overall system memory
free -h
```

## Future Considerations

- Monitor RAM usage over time to verify stability
- Consider disabling additional GitLens views if needed
- Review extension list periodically for memory hogs
- Create similar monitoring tools for other Electron apps

## Related Files

- `/home/aipass/.vscode/settings.json` - VS Code configuration
- `/home/aipass/pyrightconfig.json` - Pylance exclusions
- `/home/aipass/.local/bin/antigravity-status` - Process management tool
- `~/.bashrc` - antigravity-kill aliases
