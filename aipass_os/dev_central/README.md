# DEV_CENTRAL

> *Patrick + Claude - System-wide Orchestration Hub*

**Location:** `/home/aipass/aipass_os/dev_central`
**Created:** 2025-11-30
**Email:** `@dev_central`

---

## What is DEV_CENTRAL?

Central command for the AIPass ecosystem. This is where Patrick and Claude collaborate on system-wide planning, coordination, and architectural decisions. Not a code-building branch - an orchestration hub.

**What happens here:**
- System-wide planning and architecture discussions
- Cross-branch task delegation via dispatch (`ai_mail send --dispatch`)
- Monitoring and follow-up on dispatched work (monitoring agents)
- Flow plan creation and lifecycle management
- Central aggregation of branch status and activity

**What doesn't happen here:**
- Code building (agents do that at proper branches)
- Heavy file operations (agents handle those)
- Domain-specific debugging (branch experts own their systems)

---

## Workflow

DEV_CENTRAL operates on a **dispatch + monitor** pattern:

```bash
# Send task to a branch (spawns agent there)
ai_mail send @branch "Task Subject" "Details" --dispatch

# Check for responses
ai_mail inbox
ai_mail view <id>
```

**Monitoring agents** run in the background to catch responses from dispatched work. They check inbox, error registry, and lock files on a timer, then report back. This keeps conversations with Patrick unblocked while work happens asynchronously.

**Decision reflex:** Before debugging any domain yourself, ask which branch owns it. They have deep memory on their systems - a 1-email question saves hours of guessing.

| Domain | Branch |
|--------|--------|
| File monitoring, events | @prax |
| Email system, delivery | @ai_mail |
| Standards, code quality | @seed (14 standards) |
| Plans, workflows | @flow |
| Command routing | @drone |
| Branch lifecycle | @cortex |
| Backups, snapshots | @backup_system |
| API, model access | @api |
| Vector search, archives | @memory_bank |
| Dev notes, dashboard | @devpulse |

---

## Directory Structure

```
dev_central/
├── DEV_CENTRAL.*.json        # Memory files (800 line limit)
├── DASHBOARD.local.json      # System status (auto-refreshed)
├── FPLAN-*.md                # Active flow plans
├── notepad.md                # Async scratchpad during builds
├── dev.local.md              # Shared dev notes (issues, ideas)
│
├── Sub-branches
│   ├── assistant/            # Workflow coordinator (dispatch, monitoring, aggregation)
│   ├── devpulse/             # Human notes, dashboard updates, dev tracking
│   ├── git_repo/             # Git operations and repo management
│   └── permissions/          # ACL/permission management (skeleton)
│
├── dev_planning/             # Per-branch planning directories + workflow docs
├── docs/                     # Technical documentation
├── templates/                # Branch welcome, proposals, etc.
├── .aipass/                  # Branch system prompt (injected on every prompt)
├── .seed/                    # Seed compliance config (bypass rules)
└── .chroma/                  # Local vector DB
```

---

## Memory Files

| File | Purpose | Limit |
|------|---------|-------|
| `DEV_CENTRAL.id.json` | Identity, role, principles | Permanent |
| `DEV_CENTRAL.local.json` | Session history, key learnings, active tasks | 800 lines |
| `DEV_CENTRAL.observations.json` | Collaboration patterns, insights | 800 lines |

Memory files auto-roll to Memory Bank (ChromaDB vectors) when they exceed limits. This is by design - nothing is lost, it just moves to searchable archive.

---

## Sub-branches

All sub-branches follow 3-layer architecture (`apps/ → modules/ → handlers/`):

### ASSISTANT
Workflow coordinator - dispatches tasks, monitors responses, handles correction loops.
- Entry: `apps/assistant.py`
- Commands: `drone @assistant update` (status digest)
- Pattern: Tasks sent with `--reply-to @assistant` route back for validation

### DEVPULSE
Human and AI shared dev notes, dashboard updates, dev tracking.
- Entry: `apps/devpulse.py`
- Features: `dev.local.md` per branch, `DASHBOARD.local.json` updates
- Commands: `drone @devpulse dev add @branch "Section" "Note"`

### GIT_REPO
Git operations and repository management.
- Entry: `apps/git_repo.py`

### PERMISSIONS
Access control and permission systems. Currently skeletal framework - structure exists but no active modules.
- Entry: `apps/permissions.py`

---

## Key Commands

```bash
# Email (from DEV_CENTRAL, use full path for sender identity)
python3 /home/aipass/aipass_core/ai_mail/apps/ai_mail.py inbox
python3 /home/aipass/aipass_core/ai_mail/apps/ai_mail.py send @branch "Subj" "Msg" --dispatch

# Flow plans
drone @flow create . "subject"
drone @flow close FPLAN-XXXX
drone @flow list

# Cross-branch commands
drone @seed audit @branch
drone @seed verify
drone @memory_bank search "query"
drone @assistant update

# Discovery
drone systems
drone list @branch
```

---

## Working Here

This is a **conversation hub**, not a code factory.

- **Discuss** architecture, plans, direction with Patrick
- **Dispatch** work to specialist branches via email
- **Monitor** responses with background monitoring agents
- **Coordinate** cross-branch operations and multi-phase builds
- **Update memories** - they are your presence in this ecosystem

When something needs building, dispatch it to the branch that owns that domain.

---

*Last Updated: 2026-02-14*
