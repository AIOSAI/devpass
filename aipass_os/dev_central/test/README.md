# TEST

**Purpose:** System integration testing, Telegram debugging, cross-branch module testing
**Location:** `/home/aipass/aipass_os/dev_central/test`
**Profile:** Workshop
**Created:** 2026-02-15

---

## Architecture

- **Pattern:** Modular
- **Structure:** `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator:** `apps/TEST.py` - auto-discovers and routes to modules
- **Module Interface:** All modules implement `handle_command(args) -> bool`

---

## Directory Structure

```
/home/aipass/aipass_os/dev_central/test
├── ai_mail.local
│   ├── deleted.json
│   ├── inbox.json
│   └── sent.json
├── apps
│   ├── extensions
│   ├── handlers
│   ├── __init__.py
│   ├── json_templates
│   ├── modules
│   ├── plugins
│   └── test.py
├── .archive
├── artifacts
├── .backup
├── DASHBOARD.local.json
├── dev.local.md
├── docs
│   └── _template.md
├── dropbox
├── .gitignore
├── logs
├── .migrations.json
├── notepad.md
├── pytest.ini
├── README.md
├── requirements.txt
├── TEST.id.json
├── test_json
├── TEST.local.json
├── TEST.observations.json
├── tests
│   ├── conftest.py
│   └── __init__.py
└── tools

17 directories, 19 files

```

*Auto-generated on file structure changes*

---

## Key Capabilities

- System integration testing
- Telegram debugging
- Cross-branch module testing
- Automated test suites and smoke tests (future)

---

## Usage Instructions

Fresh branch - modules and handlers to be built as testing infrastructure evolves.

---

## Integration Points

- **Depends On:** Core AIPass systems (drone, ai_mail, flow, seed)
- **Integrates With:** All branches (cross-branch testing)
- **Provides To:** Ecosystem-wide test coverage

---

## Memory System

### Memory Files
- **TEST.id.json** - Branch identity and architecture
- **TEST.local.json** - Session history (max 600 lines)
- **TEST.observations.json** - Collaboration patterns (max 600 lines)
- **ai_mail.local/** - Branch messaging
- **docs/** - Technical documentation (markdown)

### Health Monitoring
- 🟢 **Green (Healthy):** Under 80% of limits
- 🟡 **Yellow (Warning):** 80-100% of limits
- 🔴 **Red (Critical):** Over limits (compression needed)

---

## System References

- **Code Standards:** `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source:** `/home/aipass/aipass_core/branch_operations/templates/`
- **Global Documentation:** `/home/aipass/aipass_os.md`

### Core Systems
- **Flow:** Workflow and PLAN management
- **Drone:** Command orchestration
- **AI Mail:** Branch-to-branch messaging
- **Backup:** System backup and snapshots
- **Prax:** Logging and infrastructure
- **API:** API integration layer

---

## Automation Philosophy

**README represents EXACT CURRENT STATE** - not future plans, not past work

### What Goes Elsewhere
- **Future Plans:** PLAN files in flow system
- **Past Work:** TEST.local.json session history
- **Working On:** Active PLANs
- **Patterns Learned:** TEST.observations.json
- **Technical Docs:** docs/ directory

### Automation Goal
Minimize AI token spend on updates - automate everything possible. Triggers fire on actual changes, not periodic checks.

---

## Notes

- **Human File:** This README.md is AI-managed Markdown - Patrick reads this directly
- **Current State Only:** Snapshot of branch as it exists RIGHT NOW - no history, no future
- **Auto vs Manual:** Automated sections = script-populated, Manual sections = AI writes when something fundamentally changes

---

*Last Updated: 2026-02-15*
