# TEAM_2_WS

**Purpose:** Workspace engineer for TEAM_2 — builds what TEAM_2 designs
**Location:** `/home/aipass/aipass_business/teams/team_2/workspace`
**Profile:** Workshop
**Created:** 2026-02-08

---

## Architecture

- **Pattern:** Modular (auto-discovery)
- **Structure:** `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator:** `apps/team_2_ws.py` — scans `modules/` for files with `handle_command()` and routes automatically
- **Module Interface:** All modules implement `handle_command(args) -> bool`

---

## Directory Structure

```
/home/aipass/aipass_business/teams/team_2/workspace
├── ai_mail.local/          # Branch messaging (inbox, sent, deleted)
├── .aipass/                # Branch-level system config
├── apps/
│   ├── team_2_ws.py        # Entry point (auto-discovery orchestrator)
│   ├── modules/            # Business logic (empty — awaiting first build task)
│   ├── handlers/           # Implementation details
│   ├── extensions/         # Optional extensions
│   ├── plugins/            # Optional plugins
│   └── json_templates/     # JSON template files
├── .archive/               # Disabled/old files (never delete — archive here)
├── artifacts/              # Build outputs and deliverables
├── .backup/                # Local backup storage
├── docs/                   # Technical documentation (markdown)
├── dropbox/                # File exchange area
├── logs/                   # Execution logs
├── .seed/                  # Seed audit config
├── team_2_ws_json/         # Branch JSON data
├── tests/                  # Pytest test suite
├── tools/                  # Utility scripts
├── DASHBOARD.local.json    # System-wide status snapshot
├── dev.local.md            # Shared dev notes (human + AI)
├── TEAM_2_WS.id.json       # Branch identity
├── TEAM_2_WS.local.json    # Session history (600 line max)
├── TEAM_2_WS.observations.json  # Collaboration patterns
├── README.md               # This file
├── requirements.txt        # Python dependencies (none yet)
└── pytest.ini              # Test configuration
```

---

## Current State

- **Modules:** None built yet — `apps/modules/` is empty
- **Dependencies:** None — `requirements.txt` has no active entries
- **Status:** Operational, awaiting build tasks from TEAM_2

### Recent Work

- **Session 4 (2026-02-17):** Built Phase 0 Infrastructure for Trinity Pattern public repo — 10 items (CI, PyPI publish, security scan, Docker, integration tests, SECURITY.md, coverage config, issue triage, stale issues, Dependabot)
- **Session 3 (2026-02-17):** Built complete Trinity Pattern open-source package — JSON schemas, Python library, 3 example implementations, 28/28 tests passing
- **Session 2 (2026-02-08):** Onboarding — identity configured, memories set up

---

## Integration Points

- **Receives tasks from:** TEAM_2 manager (via ai_mail dispatch)
- **Reports to:** TEAM_2, DEV_CENTRAL
- **Uses:** drone, flow, seed, ai_mail, prax

---

## Memory System

| File | Purpose |
|------|---------|
| `TEAM_2_WS.id.json` | Branch identity and role (permanent) |
| `TEAM_2_WS.local.json` | Session history (600 line max, auto-rolls to Memory Bank) |
| `TEAM_2_WS.observations.json` | Collaboration patterns (600 line max) |
| `dev.local.md` | Shared dev notes — Issues, Upgrades, Testing, Notes, Ideas, Todos |
| `docs/` | Technical documentation (markdown) |

---

*Last Updated: 2026-02-19*
