# TEAM_1_WS

**Purpose:** 
**Location:** `/home/aipass/aipass_business/hq/team_1_ws`
**Profile:** Workshop
**Created:** 2026-02-08

---

## Architecture

- **Pattern:** Modular
- **Structure:** `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator:** `apps/TEAM_1_WS.py` - auto-discovers and routes to modules
- **Module Interface:** All modules implement `handle_command(args) -> bool`

---

## Directory Structure

```
/home/aipass/aipass_business/hq/team_1_ws
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
│   └── team_1_ws.py
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
├── TEAM_1_WS.id.json
├── team_1_ws_json
├── TEAM_1_WS.local.json
├── TEAM_1_WS.observations.json
├── tests
│   ├── conftest.py
│   └── __init__.py
└── tools

17 directories, 19 files

```

*Auto-generated on file structure changes*

---

## Modules

{{AUTO_GENERATED_MODULES}}

*Scans `apps/modules/*.py` for files with `handle_command()`*

---

## Commands

{{AUTO_GENERATED_COMMANDS}}

*Pulled from drone @TEAM_1_WS - branch-specific commands only*

---

## Dependencies

{{AUTO_GENERATED_DEPENDENCIES}}

*Parsed from `requirements.txt` when it changes*

---

## Common Imports

{{AUTO_GENERATED_IMPORTS}}

*Scans module files for import statements - shows common dependencies*

---

## Key Capabilities

{{KEY_CAPABILITIES}}

---

## Usage Instructions

### Basic Usage
{{BASIC_USAGE}}

### Common Workflows
{{COMMON_WORKFLOWS}}

### Examples
{{EXAMPLES}}

---

## Integration Points

### Depends On
{{DEPENDS_ON}}

### Integrates With
{{INTEGRATES_WITH}}

### Provides To
{{PROVIDES_TO}}

---

## Memory System

### Memory Files
- **TEAM_1_WS.id.json** - Branch identity and architecture
- **TEAM_1_WS.local.json** - Session history (max 600 lines)
- **TEAM_1_WS.observations.json** - Collaboration patterns (max 600 lines)
- **TEAM_1_WS.ai_mail.json** - Branch messages
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
- **Past Work:** TEAM_1_WS.local.json session history
- **Working On:** Active PLANs
- **Patterns Learned:** TEAM_1_WS.observations.json
- **Technical Docs:** docs/ directory

### Automation Goal
Minimize AI token spend on updates - automate everything possible. Triggers fire on actual changes, not periodic checks.

---

## Notes

- **Human File:** This README.md is AI-managed Markdown - Patrick reads this directly
- **Current State Only:** Snapshot of branch as it exists RIGHT NOW - no history, no future
- **Auto vs Manual:** Automated sections = script-populated, Manual sections = AI writes when something fundamentally changes

---

*Last Updated: 2026-02-08*
