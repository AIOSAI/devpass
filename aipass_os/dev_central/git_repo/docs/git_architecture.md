# AIPass Git Architecture

**Date:** 2026-02-08
**Author:** GIT_REPO branch
**Task:** FPLAN-0309 - Design AIPass Git Architecture

---

## 1. Repository Structure

### Single Monorepo (Recommended)

Keep the current single-repo structure. AIPass is a tightly integrated ecosystem - branches reference each other, share infrastructure, and communicate through shared paths. Splitting into multiple repos would break the `@branch` resolution, ai_mail routing, and drone command routing that depend on the `/home/aipass` root.

```
/home/aipass/                      # Repo root
├── .gitignore                     # Comprehensive root gitignore
├── CLAUDE.md                      # AI culture/instructions
├── BRANCH_REGISTRY.json           # Master branch registry
├── aipass_core/                   # Core infrastructure (9 branches)
│   ├── ai_mail/
│   ├── api/
│   ├── backup_system/
│   ├── cli/
│   ├── cortex/
│   ├── drone/
│   ├── flow/
│   ├── prax/
│   └── trigger/
├── aipass_os/                     # Operations layer (5 branches)
│   ├── assistant/
│   ├── dev_central/
│   ├── devpulse/
│   ├── git_repo/
│   └── permissions/
├── aipass_business/               # Business layer
│   └── hq/
├── seed/                          # Standards library
├── Nexus/                         # CoFounder AI
├── The_Commons/                   # Social network
├── MEMORY_BANK/                   # Archive storage
├── projects/                      # External projects
└── mcp_servers/                   # MCP protocol servers
```

---

## 2. Branch Naming Convention

### Format

```
<type>/<branch-name>/<description>
```

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feat/` | New feature or capability | `feat/drone/commons-feed-pagination` |
| `fix/` | Bug fix | `fix/ai-mail/dispatch-retry-failure` |
| `chore/` | Maintenance, cleanup | `chore/seed/audit-rule-update` |
| `docs/` | Documentation only | `docs/git-repo/architecture-docs` |
| `refactor/` | Code restructuring | `refactor/cortex/extract-passport-validation` |
| `experiment/` | Exploratory, may be discarded | `experiment/memory-bank/vector-search-v2` |
| `hotfix/` | Urgent production fix | `hotfix/drone/routing-crash` |

### Rules

- All lowercase, hyphens only (no underscores, no spaces)
- Maximum 50 characters total
- Branch name maps to AIPass branch (lowercase): `drone`, `seed`, `ai-mail`
- Delete branches after merge (keep history clean)
- Never reuse branch names

---

## 3. Commit Message Convention

### Adopt Conventional Commits

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Meaning |
|------|---------|
| `feat` | New functionality |
| `fix` | Bug repair |
| `docs` | Documentation only |
| `refactor` | Restructuring, no behavior change |
| `chore` | Maintenance, dependencies, tooling |
| `test` | Adding or updating tests |
| `style` | Formatting, whitespace (no logic change) |
| `perf` | Performance improvement |
| `ci` | CI/CD pipeline changes |

### Scopes

Scopes match AIPass branch/module names (lowercase, hyphenated):

`ai-mail`, `api`, `backup-system`, `cli`, `cortex`, `drone`, `flow`, `prax`, `trigger`, `assistant`, `dev-central`, `devpulse`, `git-repo`, `permissions`, `seed`, `nexus`, `commons`, `memory-bank`, `business`

### Examples

```
feat(drone): add commons feed pagination support

fix(ai-mail): resolve dispatch retry on failed deliveries

Dispatch messages that fail on first attempt now retry
up to 3 times with exponential backoff.

chore(memory-bank): roll over local.json exceeding 600 lines

docs(git-repo): add git architecture documentation

refactor(cortex): extract passport validation into handler

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### AI Attribution

Every commit by an AI agent MUST include a footer:

```
Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

This creates an auditable trail of AI vs human contributions - critical for transparency if the repo goes public.

### What's Wrong with Current Commits

Current pattern:
```
0af81f67 update 68 files and delete 53 files
10e167d3 update 46 files and delete 68 files
a708bf57 update 38 files and delete 91 files
```

Problems:
- No indication of WHAT changed or WHY
- Bulk commits mixing unrelated changes
- No attribution (human vs AI)
- Impossible to bisect, review, or revert meaningfully

---

## 4. Git Workflow

### Branch-Based Development with PRs

```
main (protected)
├── feat/drone/new-feature     ← Agent works here
├── fix/ai-mail/dispatch-bug   ← Agent works here
└── docs/seed/readme-update    ← Agent works here
```

### Workflow Steps

1. **Create branch** from `main`
   ```bash
   git checkout -b feat/drone/new-feature main
   ```

2. **Make atomic commits** (one logical change per commit)
   ```bash
   git add apps/modules/new_module.py
   git commit -m "feat(drone): add new routing module"
   ```

3. **Push to remote**
   ```bash
   git push -u origin feat/drone/new-feature
   ```

4. **Create PR** via `gh pr create`
   - Title follows commit convention
   - Body includes summary and test plan
   - Label with `ai-generated` if applicable

5. **Review and merge** (human approval required for main)

6. **Delete branch** after merge

### When to Use Branches vs Direct Commits

| Scenario | Approach |
|----------|----------|
| New feature, multi-file changes | Feature branch + PR |
| Bug fix affecting multiple files | Fix branch + PR |
| Single-file documentation update | Direct commit to main (if permitted) |
| Memory file updates (.local.json) | Direct commit to main |
| Emergency hotfix | Hotfix branch + expedited PR |

---

## 5. Branch Protection Rules

### Main Branch Protection (GitHub Rulesets)

| Rule | Setting | Reason |
|------|---------|--------|
| Block force pushes | ON | Prevent history destruction |
| Restrict deletions | ON | Prevent branch deletion |
| Require pull requests | ON | All changes reviewed |
| Required approvals | 1 (Patrick) | Human oversight |
| Dismiss stale reviews | ON | Require re-review after changes |
| Require status checks | ON (when CI exists) | Automated quality gates |
| Require linear history | ON | Clean, readable history |
| Require conversation resolution | ON | All comments addressed |

### CODEOWNERS

```
# /CODEOWNERS
# Patrick reviews everything by default
* @patrick-aipass

# Critical infrastructure
aipass_core/    @patrick-aipass
BRANCH_REGISTRY.json  @patrick-aipass
CLAUDE.md       @patrick-aipass
.gitignore      @patrick-aipass
```

### Who Can Push Where

| Actor | main | feature branches | Their own memory files |
|-------|------|------------------|-----------------------|
| Patrick | Direct push | Direct push | Direct push |
| AI agents | PR only | Direct push | Direct push |
| CI/CD | Never | Never | Never |

---

## 6. Agent Git Safety Rules

### NEVER Do (Without Explicit Human Approval)

- `git push --force` (use `--force-with-lease` if absolutely necessary)
- `git reset --hard`
- `git clean -f`
- `git checkout .` / `git restore .`
- `git branch -D` on shared branches
- `git rebase` on shared/public branches

### ALWAYS Do

- Make atomic commits (one logical change per commit)
- Use Conventional Commits format
- Include `Co-Authored-By` footer
- Create branches for multi-file changes
- Verify with `git status` and `git diff` before committing
- Stage specific files (not `git add .` or `git add -A`)

### Pre-Commit Checks (Recommended)

Install via `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: detect-private-key
      - id: no-commit-to-branch
        args: ['--branch', 'main']
      - id: check-merge-conflict

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

---

## 7. What Goes Public (Sensitivity Audit)

### NEVER Public (Must Stay Out of Git History)

| Category | Files/Patterns | Action |
|----------|---------------|--------|
| Credentials | `.aipass/telegram_config.json` | Rotate token after fresh repo |
| OAuth tokens | `.aipass/drive_creds.json` | Rotate credentials |
| API keys | `.env` files, `api_keys/` | Rotate all keys |
| SSH keys | `.ssh/` | Already ignored |
| Private keys | `*.pem`, `*.key`, `*.cert` | Add to .gitignore |

### Safe for Public

| Category | Content |
|----------|---------|
| Source code | All `apps/`, `modules/`, `handlers/` |
| Documentation | `README.md`, `docs/`, `CLAUDE.md` |
| Templates | `cortex/templates/` |
| Configuration | `BRANCH_REGISTRY.json` (review for internal IPs/paths) |
| Business docs | `IDEAS.md`, `VISION.md` (review for sensitive strategy) |

### Review Before Public

| Category | Concern |
|----------|---------|
| Memory files (.local.json) | May contain internal discussions, task details |
| Observations files | May reference internal people or processes |
| AI Mail archives | Internal communications |
| The Commons posts | Internal discussions |
| System paths in configs | `/home/aipass/` paths reveal server structure |

### Pre-Public Checklist

```
[ ] All credentials rotated
[ ] detect-secrets scan clean
[ ] No .env content in any tracked file
[ ] System paths reviewed (replace with relative where possible)
[ ] Memory files reviewed for sensitive content
[ ] LICENSE file added
[ ] README.md is public-facing
[ ] CONTRIBUTING.md exists
[ ] SECURITY.md exists (vulnerability reporting)
[ ] GitHub secret scanning enabled
[ ] GitHub push protection enabled
```

---

## 8. Migration Plan (Fresh Repo)

### Step 1: Pre-Migration

1. Delete `test_large_file.bin` (105 MB)
2. Rotate ALL exposed credentials
3. Create comprehensive `.gitignore` (see draft)
4. Verify no sensitive content in files to be committed

### Step 2: Initialize Fresh Repo

```bash
cd /home/aipass
rm -rf .git
git init
git add .gitignore
git commit -m "chore: initialize repository with comprehensive .gitignore"
```

### Step 3: Initial Commit (Staged)

```bash
# Stage core infrastructure first
git add aipass_core/ aipass_os/ seed/
git commit -m "feat: add core infrastructure and operations layer"

# Stage business and community
git add aipass_business/ The_Commons/ Nexus/
git commit -m "feat: add business layer and community systems"

# Stage memory and configuration
git add BRANCH_REGISTRY.json CLAUDE.md AGENTS.md
git commit -m "feat: add system configuration and AI instructions"

# Stage remaining tracked content
git add MEMORY_BANK/*.json MEMORY_BANK/apps/
git commit -m "feat: add memory bank application layer"

# Stage documentation
git add projects/ mcp_servers/
git commit -m "feat: add projects and MCP server configurations"
```

### Step 4: Connect Remote

```bash
git remote add origin https://github.com/AIOSAI/AIPass.git
git branch -M main
git push -u origin main
```

### Step 5: Configure Protection

1. Enable GitHub Rulesets on `main`
2. Set up CODEOWNERS file
3. Enable secret scanning and push protection
4. Install pre-commit hooks

---

## 9. Summary

| Area | Recommendation |
|------|---------------|
| Repo structure | Single monorepo (keep current) |
| Branch naming | `<type>/<branch>/<description>` |
| Commit format | Conventional Commits with AI attribution |
| Protection | GitHub Rulesets: block force push, require PR + review |
| Agent safety | Explicit deny list for destructive commands |
| .gitignore | One comprehensive root file (see draft) |
| Public readiness | Credential rotation + detect-secrets scan + review memory files |

---

*Generated by GIT_REPO branch - FPLAN-0309*
