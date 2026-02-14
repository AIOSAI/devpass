# Draft .gitignore for AIPass

**Deploy to:** `/home/aipass/.gitignore`

Below is the complete `.gitignore` ready for deployment. Copy the content between the markers.

---

```gitignore
# ============================================
# AIPass Root .gitignore
# Comprehensive monorepo coverage
# Last updated: 2026-02-08
# ============================================

# ==========================================
# SECURITY - Credentials & Secrets
# ==========================================
# CRITICAL: These must NEVER be in git

# Environment files
.env
.env.*
!.env.example
!.env.template

# AIPass credentials directory
.aipass/telegram_config.json
.aipass/drive_creds.json
.aipass/google_token.json
.aipass/*_creds.json
.aipass/*_credentials.json
.aipass/*_token.json
.aipass/*_secret.json

# Keys and certificates
*.pem
*.key
*.cert
*.p12
*.pfx
*.keystore

# API keys
api_keys
api_keys/

# Generic secrets
*_secret*
*_credentials*
credentials.json
secrets.json
*.secret

# ==========================================
# PYTHON
# ==========================================

__pycache__/
*.py[cod]
*$py.class
*.so

# Virtual environments
.venv/
venv/
ENV/
env/

# Testing
.pytest_cache/
htmlcov/
.coverage
.coverage.*
coverage.xml
nosetests.xml
.tox/
.nox/
.hypothesis/

# Type checking
.mypy_cache/
.pytype/
.dmypy.json

# Build/Distribution
*.egg
*.egg-info/
dist/
build/
sdist/
wheels/

# Jupyter
.ipynb_checkpoints/

# ==========================================
# NODE.JS
# ==========================================

node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
.npm
.yarn/cache
.yarn/unplugged
.pnp.*
package-lock.json
yarn.lock

# ==========================================
# DATABASES & BINARY DATA
# ==========================================

# SQLite
*.sqlite3
*.sqlite3-journal
*.db
*.db-journal
!**/.chroma/*.sqlite3

# ChromaDB vector stores (binary, large, regenerable)
.chroma/

# ==========================================
# IDE & EDITOR
# ==========================================

.idea/
*.swp
*.swo
*~
*.sublime-project
*.sublime-workspace

# ==========================================
# OPERATING SYSTEM
# ==========================================

.DS_Store
Thumbs.db
Desktop.ini
._*

# ==========================================
# HOME DIRECTORY (Linux User Profile)
# ==========================================
# These exist because repo root = /home/aipass

.bash_history
.bash_history-*.tmp
.bash_logout
.bashrc
.profile
.cache
.config**
.dotnet
.gnupg
.idlerc
.lesshst
.local
.npm-global
.npmrc
.pki
.python_history
.ssh
.sudo_as_admin_successful
.var
.wget-hsts

# User directories (not code)
Desktop
Downloads
Pictures
Videos

# ==========================================
# LOGS & TEMPORARY FILES
# ==========================================

*.log
logs/
crash-logs/
system_logs/
*.tmp
*.bak
*.orig

# ==========================================
# AIPASS SPECIFIC
# ==========================================

# Internal comment files (convention across all branches)
*#@comments.txt
*#@comments

# Sandbox/test artifacts
sandbox.img
test_large_file.bin

# Claude session artifacts
.claude.json
.claude.json.backup
.claude.json.backup.*
.commands.json
.cached_template
.claude/plugins/known_marketplaces.json

# Codex / Context7 runtime data
.codex/log
.codex/sessions
.codex/history.jsonl
.codex/internal_storage.json

# Backup system rollover files
*.local.json.bak
.backup/

# Mail archives (deleted mail is transient)
**/ai_mail.local/deleted/

# Memory Bank runtime data (not source)
MEMORY_BANK/memory_pool
MEMORY_BANK/plans

# MCP server implementations (cloned, not source)
mcp_servers/.playwright-mcp
mcp_servers/playwright-mcp
mcp_servers/context7
mcp_servers/serena
mcp_servers/servers

# ==========================================
# TEMPLATE EXCEPTIONS (Re-include)
# ==========================================
# Branch templates MUST be tracked - they define system architecture

!**/aipass_core/cortex/templates/branch_template/.archive
!**/aipass_core/cortex/templates/branch_template/.backup
!/aipass_core/cortex/templates/branch_template/{{BRANCH}}_json
!**/aipass_core/cortex/templates/branch_template/ai_mail.local
!**/aipass_core/cortex/templates/branch_template/dropbox
!**/aipass_core/cortex/templates/branch_template/logs
!**/aipass_core/cortex/templates/branch_template/.migrations.json

# VSCode user settings (tracked for consistency)
!**/.config/Code/User/

# ==========================================
# ARCHIVE DIRECTORIES
# ==========================================
# .archive is used instead of deletion across AIPass

.archive
!**/aipass_core/cortex/templates/branch_template/.archive
```

---

## Notes on This Draft

### Decisions Made

1. **`.chroma/` globally ignored** - These are binary vector database files. They're large, change frequently, and can be regenerated. The `!**/.chroma/*.sqlite3` exception preserves the Chroma metadata DB if needed for schema tracking.

2. **`*.db` globally ignored** - commons.db and any SQLite databases. These are runtime data, not source code. Exception made for Chroma's internal sqlite3.

3. **`ai_mail.local/deleted/` ignored** - Deleted mail is transient cleanup noise. Inbox and sent folders remain tracked to preserve communication history.

4. **Memory files (.local.json, .observations.json, .id.json) TRACKED** - These are the identity and continuity of each branch. They ARE the system. Deliberately NOT in .gitignore.

5. **`DASHBOARD.local.json` TRACKED** - While it changes frequently, it provides system-wide status snapshots that have historical value.

6. **MCP server subdirectories ignored** - These are cloned third-party tools, not AIPass source code. They have their own repos.

### What This Draft Does NOT Cover

- `.archive/` directories at branch level: Currently globally ignored. If some should be tracked, add `!` exceptions.
- `projects/` subdirectory exclusions: Will need project-specific .gitignore files as projects are added.
- Team workspace build outputs: Covered by the global `node_modules/` and `dist/` patterns.

### Validation Checklist

Before deploying:
```
[ ] Run: git add -n . | head -50  (dry-run to see what would be staged)
[ ] Verify no .env files would be staged
[ ] Verify no credential files would be staged
[ ] Verify .chroma/ directories excluded
[ ] Verify commons.db excluded
[ ] Verify test_large_file.bin excluded
[ ] Verify memory files (.local.json etc.) INCLUDED
[ ] Verify branch template exceptions work
```

---

*Generated by GIT_REPO branch - FPLAN-0309*
