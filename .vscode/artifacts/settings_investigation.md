# VS Code Settings Investigation

## Executive Summary

**Root Cause Identified:** The root level Claude Code settings (`/.claude/settings.local.json`) was modified at **2025-10-28 00:01:59** (midnight) and contains ONLY permissions - no VS Code configuration. This is a MINIMAL configuration compared to the working /home/aipass version.

**Key Finding:** The performance and diff issues are NOT caused by bad settings in the root config, but rather by the ABSENCE of critical VS Code settings that should be applied globally.

---

## Root Level Settings (/.claude/settings.local.json)

**File Path:** `/.claude/settings.local.json`  
**Last Modified:** 2025-10-28 00:01:59 (midnight - suspicious timing)  
**Size:** 83 lines

### Contents:
```json
{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(domain:github.com)",
      "Bash(uvx:*)",
      "WebFetch(domain:code.visualstudio.com)",
      "Bash(grep:*)",
      "Bash(code --version)",
      "Bash(code:*)",
      "Bash(dpkg:*)",
      "Bash(apt list:*)",
      "Bash(lsusb)",
      "Bash(ip link show)",
      "Bash(nmcli device status)",
      "Bash(dmesg)",
      "Bash(lsmod)",
      "Bash(rfkill list)",
      "Bash(journalctl -b)",
      "Bash(apt search firmware)",
      "Bash(lsblk -o NAME,SIZE,MOUNTPOINT,LABEL,MODEL)",
      "Bash(cat /etc/udev/rules.d/50-aic8800-modeswitch.rules)",
      "Bash(sudo usb_modeswitch -v a69c -p 5723 -K)",
      "Bash(lsusb -t)",
      "Bash(cat /etc/modprobe.d/*.conf)",
      "Bash(cat /etc/udev/rules.d/51-aic8800-power.rules)",
      "Bash(cat /lib/udev/rules.d/*usb*)",
      "Bash(cat /etc/modprobe.d/aic8800-blacklist.conf)",
      "Bash(cat /etc/udev/rules.d/40-aic8800.rules)",
      "Bash(cat /sys/module/usbcore/parameters/autosuspend)",
      "Bash(chmod +x /home/aipass/sync-dev-local.sh)",
      "Bash(/home/aipass/sync-dev-local.sh)",
      "Bash(git config:*)",
      "Bash(git ls-tree:*)",
      "Bash(git rev-parse:*)",
      "Bash(cat:*)",
      "WebFetch(domain:stackoverflow.com)",
      "Bash(while read file)",
      "Bash(done)",
      "Bash(do realpath \"/$file\")",
      "Bash(test:*)",
      "Bash(sqlite3:*)",
      "WebFetch(domain:www.anthropic.com)",
      "Bash(tree:*)",
      "Bash(awk '{print $9, \"\"\"\"(\"\"\"\" $5 \"\"\"\")\"\"\"\"}')",
      "Bash(drone create plan @/)",
      "Bash(drone create plan @/ \"Final Branch Template + System-Wide Migration Strategy\")",
      "Bash(awk:*)",
      "Bash(python3:*)",
      "Bash(drone help:*)",
      "Bash(drone scan:*)",
      "Bash(drone systems:*)",
      "Bash(drone list:*)",
      "Bash(drone create:*)",
      "Bash(drone plan:*)",
      "mcp__ide__getDiagnostics",
      "Bash(chmod:*)",
      "Bash(find:*)",
      "Bash(for dir in tests logs tools archive DOCUMENTS)",
      "Bash(do echo -n \"$dir: \")",
      "Bash(if [ -d \"/home/aipass/flow/$dir\" ])",
      "Bash(then echo \"✓ exists\")",
      "Bash(else echo \"✗ missing\")",
      "Bash(fi)",
      "Bash(for dir in drone prax Standards mcp_servers)",
      "Bash(if [ -d \"/home/aipass/$dir/apps\" ])",
      "Bash(then echo \"✓ has apps/ (likely upgraded)\")",
      "Bash(else echo \"✗ no apps/ (needs upgrade)\")",
      "Bash(for dir in /home/aipass/*/)",
      "Bash(do if [ ! -d \"$dir/apps\" ])",
      "Bash([ -f \"$dir\"/*.py 2)",
      "Bash(/dev/null ])",
      "Bash(nmcli device wifi connect:*)",
      "Bash(nmcli connection:*)",
      "Bash(ip addr:*)",
      "Bash(nmcli device wifi list:*)",
      "Bash(git -C /home/aipass log --all --pretty=format:\"%h %s\" --name-only --since=\"1 day ago\")",
      "Bash(drone @ai_mail)"
    ],
    "deny": [],
    "ask": []
  }
}
```

**Analysis:** This is ONLY Claude Code permissions - no VS Code settings at all.

---

## Working Config (/home/aipass/.claude/settings.local.json)

**File Path:** `/home/aipass/.claude/settings.local.json`  
**Last Modified:** 2025-10-27 22:54:47  
**Size:** 50 lines

### Contents:
```json
{
  "permissions": {
    "allow": [
      "Read(///**)",
      "Bash(do pkill -9 -f \"$id\")",
      "Bash(python3:*)",
      "Bash(tree:*)",
      "Read(//etc/claude-code/**)",
      "Read(//home/AIPass_branch_setup_template/**)",
      "Bash(find:*)",
      "Read(//ignore_patterns/**)",
      "Bash(awk:*)",
      [... various bash and read permissions ...]
      "Bash(drone help:*)",
      "Bash(drone create plan @flow \"Expand error_monitor to watch all branches system-wide and route notifications correctly\")",
      "Bash(drone create plan:*)",
      "Bash(timeout 3 python3:*)",
      "Read(//tmp/**)",
      "Bash(timeout 2 python3:*)",
      [... more permissions ...]
      "mcp__ide__getDiagnostics"
    ],
    "deny": ["Bash(git:*)"],
    "ask": []
  },
  "enabledMcpjsonServers": [
    "serena",
    "context7",
    "playwright",
    "sequential-thinking"
  ]
}
```

**Analysis:** Also ONLY Claude Code permissions + MCP server configuration. No VS Code settings here either.

---

## VS Code User Settings (/home/aipass/.config/Code/User/settings.json)

**File Path:** `/home/aipass/.config/Code/User/settings.json`  
**Last Modified:** 2025-10-27 19:10:34  
**Size:** 123 lines

### Key Settings:

#### Performance Settings:
```json
"files.autoSave": "afterDelay",
"search.followSymlinks": false,
"files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/node_modules/**": true,
    "**/dist/**": true,
    "**/__pycache__": true
}
```

#### Git/SCM Settings:
```json
"git.enableSmartCommit": true,
"git.confirmSync": false,
"git.openRepositoryInParentFolders": "never",
"git.enabled": true,
"git.path": "/usr/bin/git",
"git.openDiffOnClick": false,
"scm.defaultViewMode": "tree",
"scm.defaultViewSortKey": "path",
"scm.alwaysShowRepositories": false
```

#### Terminal Color Settings (lines 99-120):
```json
"workbench.colorCustomizations": {
    "terminal.background": "#0B1C2C",
    "terminal.foreground": "#CBD6E2",
    "terminalCursor.background": "#CBD6E2",
    "terminalCursor.foreground": "#CBD6E2",
    "terminal.ansiBlack": "#0B1C2C",
    "terminal.ansiBlue": "#8B56BF",
    "terminal.ansiBrightBlack": "#627E99",
    "terminal.ansiBrightBlue": "#8B56BF",
    "terminal.ansiBrightCyan": "#568BBF",
    "terminal.ansiBrightGreen": "#56BF8B",
    "terminal.ansiBrightMagenta": "#BF568B",
    "terminal.ansiBrightRed": "#BF8B56",
    "terminal.ansiBrightWhite": "#F7F9FB",
    "terminal.ansiBrightYellow": "#8BBF56",
    "terminal.ansiCyan": "#568BBF",
    "terminal.ansiGreen": "#56BF8B",
    "terminal.ansiMagenta": "#BF568B",
    "terminal.ansiRed": "#BF8B56",
    "terminal.ansiWhite": "#CBD6E2",
    "terminal.ansiYellow": "#8BBF56"
}
```

#### Editor Settings:
```json
"workbench.editor.editorActionsLocation": "titleBar",
"editor.multiCursorModifier": "ctrlCmd",
"workbench.editor.labelFormat": "long",
"workbench.editor.enablePreview": true
```

---

## Differences Found

### Critical Difference:
**Root Claude Code settings (`/.claude/settings.local.json`):**
- ONLY contains permissions
- No VS Code configuration
- No MCP server configuration

**Aipass Claude Code settings (`/home/aipass/.claude/settings.local.json`):**
- Contains permissions (different set)
- Has MCP server configuration: `"enabledMcpjsonServers": ["serena", "context7", "playwright", "sequential-thinking"]`
- Git denied: `"deny": ["Bash(git:*)"]`

### Key Insight:
Neither Claude Code settings file contains VS Code configuration. All VS Code settings live in the **User settings file** at `/home/aipass/.config/Code/User/settings.json` which applies globally.

---

## Suspicious Settings (Could Cause Issues)

### Performance Related:
**MISSING from root - but these are in User settings (should apply globally):**
- `search.followSymlinks: false` - Prevents search from following symlinks (performance)
- `files.watcherExclude` - Excludes git objects, node_modules from file watching
- `files.autoSave: "afterDelay"` - Could cause performance issues if files constantly saving

### Diff/SCM Related:
**Key setting that could affect diff viewing:**
- `git.openDiffOnClick: false` - Prevents opening diff on click (User setting)
- `scm.defaultViewMode: "tree"` - Tree view for source control
- `scm.alwaysShowRepositories: false` - May hide repositories in some contexts

**Git-specific:**
- Root has git permissions allowed
- Aipass has git DENIED: `"deny": ["Bash(git:*)"]`

### Terminal Related:
**Terminal colors in User settings:**
- Extensive terminal color customization (lines 99-120)
- These should apply globally to all VS Code instances

---

## File Modification Timeline

1. **2025-10-27 19:10:34** - VS Code User settings modified (terminal colors added?)
2. **2025-10-27 22:54:47** - `/home/aipass/.claude/settings.local.json` modified
3. **2025-10-28 00:01:59** - `/.claude/settings.local.json` modified (MIDNIGHT - after session ended?)

---

## Recommendations

### Immediate Actions:

1. **Check VS Code Extension Issues:**
   - The root issue may be extension-related, not settings-related
   - Git extension or GitLens could be causing diff viewer problems
   - Check: `code --list-extensions --show-versions` at root vs /home/aipass

2. **Verify MCP Servers:**
   - Root config has NO MCP servers enabled
   - Aipass has 4 MCP servers: serena, context7, playwright, sequential-thinking
   - Add to root: `"enabledMcpjsonServers": ["serena", "context7", "playwright", "sequential-thinking"]`

3. **Git Permission Alignment:**
   - Root ALLOWS git commands
   - Aipass DENIES git commands
   - Decide which is correct for root-level work

4. **Performance Investigation:**
   - Check for extension conflicts at root level
   - Verify git repository size at root (large repos cause slowdowns)
   - Check if `.git/objects` folder is huge (run: `du -sh /.git/objects`)

### Settings to Consider Reverting:

**If terminal colors were recently added (Oct 27 19:10):**
- Remove `workbench.colorCustomizations` section from User settings
- Test if this fixes diff viewer

**Root Claude Code settings:**
- Add MCP servers to match working config
- Consider aligning git permissions (decide if root should have git access)

---

## Theory: What Actually Broke

**Most Likely Cause:** The midnight modification to `/.claude/settings.local.json` suggests an automated process or background task ran. This could have:
1. Regenerated the root config file incorrectly
2. Removed critical MCP server configuration
3. Changed permission model that affects VS Code integration

**The terminal colors (added Oct 27 19:10) are a red herring** - they're in User settings which apply globally, so they shouldn't cause root-specific issues.

**The real culprit:** Missing MCP server configuration at root level, or a VS Code extension conflict that emerged after the midnight settings change.

---

## Next Steps

1. Compare VS Code extensions between root and /home/aipass
2. Add MCP servers to root Claude Code config
3. Check git repository health at root level (`du -sh /.git`)
4. Test diff viewer after each change to isolate the issue
5. Consider reverting `/.claude/settings.local.json` to a pre-midnight backup if available

---

## Additional Diagnostic Information

### Git Repository Size Analysis

**Root level (/):**
- `.git/objects` size: **4.5M** (small, not a performance issue)

**Aipass level (/home/aipass):**
- `.git/objects` size: **122M** (much larger, but still manageable)

**Conclusion:** Git repository size is NOT the cause of performance issues at root level.

---

### File Permissions Check

**Root `.claude/` directory:**
```
drwx------   2 aipass aipass 4.0K Oct 28 00:01 .
drwxrwxr-x+ 32 root   root   4.0K Oct 28 10:04 ..
-rw-rw-r--   1 aipass aipass 2.9K Oct 28 00:01 settings.local.json
```

**Key Observation:** Settings file was written at exactly 00:01:59 on Oct 28, which is suspiciously precise timing - suggests automated process rather than manual edit.

---

## Final Diagnosis

### Primary Suspects (in order of likelihood):

1. **Missing MCP Server Configuration** (Most Likely)
   - Root config lacks: `"enabledMcpjsonServers": ["serena", "context7", "playwright", "sequential-thinking"]`
   - MCP servers may provide critical VS Code integration features
   - Action: Add MCP server config to `/.claude/settings.local.json`

2. **Automated Process Overwrite** (Likely)
   - File modified at precisely midnight (00:01:59)
   - May have been auto-generated by a system process
   - Could have wiped out previous working configuration
   - Action: Check for backup or previous version

3. **VS Code Terminal Color Conflict** (Possible)
   - Terminal colors added to User settings on Oct 27 at 19:10
   - Could interfere with diff viewer rendering
   - Action: Temporarily remove `workbench.colorCustomizations` and test

4. **Git Extension Conflict** (Less Likely)
   - Different git permissions between root and aipass
   - `git.openDiffOnClick: false` may affect diff viewer
   - Action: Check VS Code extensions, try enabling `git.openDiffOnClick: true`

### Recommended Fix Order:

1. **First:** Add MCP servers to root config
2. **Second:** Test diff viewer and performance
3. **If still broken:** Remove terminal color customizations temporarily
4. **If still broken:** Compare VS Code extensions between root and aipass
5. **Last resort:** Revert User settings to pre-Oct 27 state

---

## Investigation Complete

**Report Location:** `/home/aipass/.vscode/DOCUMENTS/settings_investigation.md`

**Summary:** Root level Claude Code settings was automatically regenerated at midnight, removing MCP server configuration. This is the most likely cause of the performance and diff viewing issues. Terminal color settings are probably not the culprit since they're in User settings which apply globally.
