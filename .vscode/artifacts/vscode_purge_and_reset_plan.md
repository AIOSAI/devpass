# VS Code Complete Purge and Reset Plan

## Settings to Keep (Recommended)

**Essential Settings:**
- Terminal colors (lines 106-127) - Your custom terminal theme
- `files.readonlyInclude` (lines 97-105) - Protects backup/snapshot files
- `cSpell.userWords` (lines 13-45) - Your custom dictionary
- `window.zoomLevel: 1` - UI zoom preference
- `files.autoSave: "afterDelay"` - Auto-save behavior
- `workbench.startupEditor: "none"` - No welcome screen
- `workbench.iconTheme: "vscode-icons"` - Icon theme

**API Keys to Preserve:**
- `ai-commit.OPENAI_API_KEY` (line 58) - **IMPORTANT: Save this!**

**Git Settings (Will recreate clean):**
- `git.enabled: true`
- `git.path: "/usr/bin/git"`
- `git.scanRepositories: ["/", "/home/aipass"]`
- `git.autoRepositoryDetection: false`
- `git.autofetchPeriod: 60`

## Directories to Delete

**User-specific VS Code data (669MB):**
```
/home/aipass/.config/Code/
```

**Workspace data (486MB):**
```
/home/aipass/.vscode/
```

**Other VS Code locations:**
```
/home/aipass/.vscode-server/  (if exists - remote SSH)
```

## System-Wide Settings Location

**For system-wide settings (not user-specific), we'll use:**
```
/etc/code/settings.json
```
or
```
/usr/share/code/resources/app/product.json
```

**Better approach:** Create settings at `/etc/skel/.config/Code/User/settings.json`
- This becomes the default for ALL users
- New users get these settings automatically

## Purge Commands

```bash
# 1. Completely remove VS Code
sudo apt remove --purge code

# 2. Remove all user data
rm -rf /home/aipass/.config/Code
rm -rf /home/aipass/.vscode
rm -rf /home/aipass/.vscode-server  # If exists

# 3. Remove system cache
sudo rm -rf /var/cache/code

# 4. Reinstall VS Code
sudo apt update
sudo apt install code

# 5. Apply system-wide settings (option A - all users)
sudo mkdir -p /etc/skel/.config/Code/User
sudo cp /home/aipass/.vscode/DOCUMENTS/clean_settings.json /etc/skel/.config/Code/User/settings.json

# OR (option B - just this machine)
mkdir -p /home/aipass/.config/Code/User
cp /home/aipass/.vscode/DOCUMENTS/clean_settings.json /home/aipass/.config/Code/User/settings.json
```

## Clean Settings File (Minimal)

Located at: `/home/aipass/.vscode/DOCUMENTS/clean_settings.json`

This will contain ONLY:
- Terminal colors
- File protection patterns
- Custom dictionary
- Essential Git settings (clean, working)
- API key
- UI preferences

## Extensions to Reinstall

After purge, you'll need to reinstall extensions:
- GitHub Copilot
- GitLens
- Python
- vscode-icons
- Any other extensions you use

List your current extensions:
```bash
code --list-extensions > /home/aipass/.vscode/DOCUMENTS/extensions_backup.txt
```

Reinstall after purge:
```bash
cat /home/aipass/.vscode/DOCUMENTS/extensions_backup.txt | xargs -L 1 code --install-extension
```

## Post-Reset Checklist

- [ ] VS Code opens without errors
- [ ] Git integration works at root level (`/`)
- [ ] Discard/revert button appears and functions
- [ ] Terminal colors applied
- [ ] Extensions installed and activated
- [ ] No performance issues
- [ ] Diff viewing works (or acceptable limitation documented)

## Notes

**System-wide vs User-specific:**
- User-specific: `/home/aipass/.config/Code/User/settings.json`
- System-wide default: `/etc/skel/.config/Code/User/settings.json` (for new users)
- Machine-wide: Would require editing VS Code's default settings (not recommended)

**Recommendation:** Use user-specific but start completely fresh. System-wide settings are mainly useful for multi-user systems.
