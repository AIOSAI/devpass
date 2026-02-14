# .gitignore Audit Report

**Date:** 2026-02-08
**Author:** GIT_REPO branch
**Task:** FPLAN-0309 - Design AIPass Git Architecture

---

## 1. Current State

### Root .gitignore (`/home/aipass/.gitignore`)

The existing root .gitignore covers:

| Category | Patterns | Status |
|----------|----------|--------|
| Python caches | `__pycache__`, `.pytest_cache` | Covered |
| JSON state files | `*_json` (blanket), `!*_json.config` exception | Covered |
| Home directory configs | `.bashrc`, `.profile`, `.ssh`, `.gnupg`, etc. | Covered |
| User directories | `Desktop`, `Downloads`, `Pictures`, `Videos` | Covered |
| Logs | `crash-logs`, `system_logs`, `logs` | Covered |
| Test artifacts | `test_large_file.bin` | Covered |
| Claude artifacts | `.claude.json`, `.claude.json.backup` | Covered |
| Virtual envs | `.venv` | Covered |
| Template exceptions | Branch template files re-included with `!` | Covered |

**Design philosophy:** Separates infrastructure (tracked) from state (ignored). Uses blanket `*_json` exclusion with selective re-inclusion for templates.

### Branch-Level .gitignore Files Found (20 total)

| Location | Contents | Purpose |
|----------|----------|---------|
| `/home/aipass/aipass_os/dev_central/.gitignore` | `api_keys`, `*#@comments` | Protect API keys |
| `/home/aipass/aipass_os/dev_central/git_repo/.gitignore` | Empty | Placeholder |
| `/home/aipass/aipass_core/cortex/.gitignore` | `htmlcov`, `*#@comments.txt` | Coverage reports |
| `/home/aipass/aipass_core/drone/.gitignore` | `*#@comments.txt` | Internal comments |
| `/home/aipass/aipass_core/ai_mail/.gitignore` | `*#@comments.txt` | Internal comments |
| `/home/aipass/aipass_core/flow/.gitignore` | `*#@comments.txt` | Internal comments |
| `/home/aipass/aipass_core/cli/.gitignore` | `*#@comments.txt` | Internal comments |
| `/home/aipass/aipass_core/api/.gitignore` | `.env`, `*#@comments.txt` | Env vars + comments |
| `/home/aipass/MEMORY_BANK/.gitignore` | `memory_pool`, `plans` | Dynamic data |
| `/home/aipass/.claude-code-docs/.gitignore` | Standard Python/IDE/OS patterns | Full template |
| `/home/aipass/mcp_servers/.gitignore` | Server exclusions | MCP servers |
| `/home/aipass/mcp_servers/servers/.gitignore` | Node.js + Python + credentials | Comprehensive |
| `/home/aipass/mcp_servers/playwright-mcp/.gitignore` | Build/test output | Playwright-specific |
| `/home/aipass/mcp_servers/serena/.gitignore` | 237 lines, multi-language | Language server |
| `/home/aipass/mcp_servers/context7/.gitignore` | Runtime data | Session/log exclusion |
| `/home/aipass/aipass_business/hq/team_*/workspace/.gitignore` | Node.js standard (177 lines) | Team workspaces |
| `/home/aipass/.codex/.gitignore` | Runtime data | Session/log exclusion |

**Common pattern across branches:** `*#@comments.txt` - an AIPass-specific convention for internal comment files that shouldn't be versioned.

---

## 2. Critical Gaps

### Security Gaps (HIGH PRIORITY)

| Gap | Risk | Details |
|-----|------|---------|
| `.aipass/` directory NOT ignored | Credential exposure | Contains `telegram_config.json` (bot token), `drive_creds.json` (OAuth tokens, client secrets) |
| `.env` not globally ignored | Secret leakage | Only ignored in `aipass_core/api/`, NOT in root or other branches |
| No `*.pem`, `*.key` patterns | Key exposure | No protection against accidentally committing certificates or keys |

### Binary/Database Gaps (MEDIUM-HIGH PRIORITY)

| Gap | Size | Details |
|-----|------|---------|
| `.chroma/` directories NOT ignored | 45+ MB total | Vector DB binary files (data_level0.bin, length.bin) across 10+ branches |
| `*.db` files NOT ignored | Variable | `commons.db` (684 KB), changes frequently, shows in every git status |
| `*.sqlite3` NOT ignored | Variable | No protection for SQLite databases |

### State Churn Gaps (MEDIUM PRIORITY)

| Gap | Impact | Details |
|-----|--------|---------|
| `ai_mail.local/deleted/` tracked | Noisy diffs | 53 deleted mail files in current git status |
| `ai_mail.local/sent/` tracked | Noisy diffs | Sent mail archives accumulate |
| `.claude.json.backup.*` files | Noise | Multiple backup files showing as untracked |
| `DASHBOARD.local.json` at all levels | Frequent changes | Auto-refreshed system status files |

### Inconsistencies

| Issue | Details |
|-------|---------|
| `.archive/` handling | Root ignores `.archive` but some templates re-include it; inconsistent across branches |
| `.backup/` handling | Root ignores `.backup` but rollover backups still tracked in some locations |
| Comment file pattern | Most branches use `*#@comments.txt`, a few use `*#@comments` (without .txt) |
| `.env` coverage | Only `aipass_core/api/.gitignore` ignores `.env`; root doesn't |

---

## 3. What's Currently Tracked That Shouldn't Be

Based on git status analysis:

```
SHOULD NOT BE TRACKED:
- MEMORY_BANK/.chroma/**/*.bin          (binary vector data, 45+ MB)
- The_Commons/commons.db                (binary database)
- .claude.json.backup.*                 (session backups)
- ai_mail.local/deleted/**              (cleaned mail archives)
- ai_mail.local/sent/**                 (transient sent mail)
- DASHBOARD.local.json (at every level) (auto-generated status)
- .claude/plugins/known_marketplaces.json (extension data)

MUST NEVER BE TRACKED:
- .aipass/telegram_config.json          (Telegram bot token)
- .aipass/drive_creds.json              (Google OAuth credentials)
- .env files (any location)             (environment secrets)
- Any *.pem, *.key, *.cert files        (certificates/keys)
```

---

## 4. What SHOULD Be Tracked

| Category | Files | Reason |
|----------|-------|--------|
| Branch identity | `[BRANCH].id.json` | Defines who each branch is; part of the system architecture |
| Session history | `[BRANCH].local.json` | Tracks branch continuity and work history |
| Observations | `[BRANCH].observations.json` | Branch learning and collaboration patterns |
| Source code | `apps/`, `modules/`, `handlers/` | The actual codebase |
| Documentation | `README.md`, `docs/` | System documentation |
| Configuration | `BRANCH_REGISTRY.json` | System registry |
| Business content | `aipass_business/IDEAS.md`, `VISION.md` | Strategic documents |
| Templates | `aipass_core/cortex/templates/` | Branch creation templates |
| Dev notes | `dev.local.md` | Shared development notes |
| Culture docs | `CLAUDE.md`, `AGENTS.md` | AI instruction files |

---

## 5. Recommendations for New .gitignore

### Root-level: ONE comprehensive .gitignore

The new root `.gitignore` should:
1. Cover ALL security-sensitive patterns globally
2. Handle ALL binary/cache/build patterns globally
3. Use category-based sections with comments
4. Minimize need for branch-level overrides
5. Use `!` negation patterns sparingly and only for templates

### Branch-level: Minimal additions only

Branch .gitignore files should ONLY contain branch-specific exclusions not covered by root. The `*#@comments.txt` pattern can be moved to root since it's universal.

### Cleanup before fresh start

Before the new repo:
1. Rotate ALL credentials found in history (Telegram bot token, Google OAuth)
2. Verify no `.env` file contents exist in any commit
3. Run `detect-secrets` scan on the codebase
4. Delete `test_large_file.bin` (105 MB)

---

## 6. Files Requiring History Scrub Before Public

| File | Contains | Action |
|------|----------|--------|
| `.aipass/telegram_config.json` | Bot token: `8521130442:AAE6q...` | ROTATE TOKEN after fresh repo |
| `.aipass/drive_creds.json` | Google client secret, refresh token | ROTATE CREDENTIALS |
| Any `.env` in history | API keys, secrets | ROTATE ALL KEYS |
| System paths in configs | `/home/aipass/...` | Low risk but review |

Since Patrick is deleting the current GitHub repo and starting fresh, the history scrub is handled by the clean break. However, all exposed credentials MUST be rotated regardless.

---

*Generated by GIT_REPO branch - FPLAN-0309*
