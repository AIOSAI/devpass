# TEAM_1_WS

**Purpose:** Team 1 workspace branch — workshop for building and executing tasks delegated by @team_1.
**Location:** `/home/aipass/aipass_business/teams/team_1/workspace`
**Profile:** Workshop
**Created:** 2026-02-08

---

## Architecture

- **Pattern:** Modular auto-discovery
- **Structure:** `apps/` directory with `modules/`, `handlers/`, `extensions/`, and `plugins/` subdirectories
- **Orchestrator:** `apps/team_1_ws.py` — scans `modules/` for `.py` files with `handle_command()` and routes commands automatically
- **Module Interface:** All modules implement `handle_command(command, args) -> bool`

---

## Directory Structure

```
/home/aipass/aipass_business/teams/team_1/workspace
├── ai_mail.local/         # Branch messaging (inbox, sent, deleted)
├── apps/
│   ├── extensions/        # Extension modules
│   ├── handlers/          # Implementation details
│   ├── json_templates/    # JSON template files
│   ├── modules/           # Business logic (auto-discovered)
│   ├── plugins/           # Plugin modules
│   └── team_1_ws.py       # Entry point / orchestrator
├── artifacts/             # Build artifacts, certificates
├── docs/                  # Technical documentation
├── dropbox/               # File exchange
├── logs/                  # Runtime logs
├── team_1_ws_json/        # Branch JSON data
├── tests/                 # Test suite
├── tools/                 # Utility scripts
├── DASHBOARD.local.json   # System-wide status
├── dev.local.md           # Shared dev notes
├── TEAM_1_WS.id.json      # Branch identity
├── TEAM_1_WS.local.json   # Session history
├── TEAM_1_WS.observations.json  # Collaboration patterns
├── README.md
├── requirements.txt
└── pytest.ini
```

---

## Current State

- **Modules:** None yet — `apps/modules/` is empty (ready for development)
- **Dependencies:** None beyond core AIPass (Python 3.12+)
- **Status:** Operational, awaiting tasks from @team_1

---

## Memory System

### Memory Files
- **TEAM_1_WS.id.json** — Branch identity and architecture
- **TEAM_1_WS.local.json** — Session history (max 600 lines)
- **TEAM_1_WS.observations.json** — Collaboration patterns (max 600 lines)
- **ai_mail.local/** — Branch messaging directory
- **docs/** — Technical documentation

### Health Monitoring
- Green: Under 80% of limits
- Yellow: 80-100% of limits
- Red: Over limits (compression needed)

---

## System References

- **Code Standards:** `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source:** `/home/aipass/aipass_core/branch_operations/templates/`

### Core Systems
- **Flow:** Workflow and PLAN management
- **Drone:** Command orchestration
- **AI Mail:** Branch-to-branch messaging
- **Backup:** System backup and snapshots
- **Prax:** Logging and infrastructure

---

## Notes

- README represents exact current state — not future plans, not past work
- Future plans go in PLAN files via flow system
- Session history lives in TEAM_1_WS.local.json
- Technical docs go in docs/ directory

---

*Last Updated: 2026-02-19*
