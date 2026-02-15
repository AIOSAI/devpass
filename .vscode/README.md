# .VSCODE

**Purpose:** VS Code configuration, extensions management, and performance monitoring
**Location:** `/home/aipass/.vscode`
**Profile:** AIPass Core Infrastructure
**Created:** 2025-11-22
---

## Architecture

- **Pattern:** Modular
- **Structure:** `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator:** `apps/vscode.py` - auto-discovers and routes to modules
- **Module Interface:** All modules implement `handle_command(args) -> bool`

---

## Directory Structure

```
.vscode/
├── ai_mail.local/              # AI Mail local storage
├── apps/                       # Application code
│   ├── vscode.py               # Main orchestrator
│   ├── __init__.py
│   ├── extensions/             # Extension-related code
│   │   └── __init__.py
│   ├── handlers/               # Request handlers
│   │   ├── __init__.py
│   │   ├── json/               # JSON handling
│   │   │   ├── __init__.py
│   │   │   └── json_handler.py
│   │   └── perf/               # Performance handling
│   │       ├── __init__.py
│   │       └── monitor.py
│   ├── json_templates/         # JSON template files
│   │   ├── __init__.py
│   │   ├── custom/
│   │   ├── default/
│   │   └── registry/
│   ├── modules/                # Feature modules
│   │   ├── __init__.py
│   │   └── perf_monitor.py
│   └── plugins/                # Plugin system
│       └── __init__.py
├── artifacts/                  # Research and documentation artifacts
│   ├── clean_settings.json
│   ├── discard_button_research.md
│   ├── extensions_backup.txt
│   ├── git_cli_alternatives.md
│   ├── PERFORMANCE_OPTIMIZATION.md
│   ├── scm_settings_analysis.md
│   ├── settings_backup_before_purge.json
│   ├── settings_investigation.md
│   ├── TERMINAL_STATUS_EXTENSION.md
│   ├── terminal_status_extension.md
│   └── vscode_purge_and_reset_plan.md
├── cli/                        # CLI tools (empty)
├── DOCUMENTS/                  # Extended memory
│   └── DOCUMENTS.template.json
├── dropbox/                    # Dropbox integration (empty)
├── extensions/                 # VS Code extensions (29 extensions)
│   ├── anthropic.claude-code-*
│   ├── ms-python.python-*
│   ├── ms-python.vscode-pylance-*
│   ├── github.copilot-*
│   ├── github.copilot-chat-*
│   ├── eamodio.gitlens-*
│   ├── esbenp.prettier-vscode-*
│   └── ... (22 more extensions)
├── logs/                       # Application logs
│   ├── json_handler.log
│   └── vscode.log
├── tests/                      # Test files
│   ├── conftest.py
│   └── __init__.py
├── tools/                      # Utility tools (empty)
├── .archive/                   # Archived files
├── .backup/                    # Backup storage
├── .claude/                    # Claude configuration
├── .vscode_json/               # VS Code JSON configs
│
├── .VSCODE.id.json             # Branch identity
├── .VSCODE.local.json          # Session history
├── .VSCODE.observations.json   # Collaboration patterns
├── .VSCODE.ai_mail.json        # Branch messages
├── .branch_meta.json           # Branch metadata
├── DASHBOARD.local.json        # Dashboard state
├── dev.local.md                # Development notes
├── notepad.md                  # Quick notes
├── settings.json               # VS Code settings
├── argv.json                   # VS Code arguments
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── .migrations.json            # Migration tracking
└── .gitignore                  # Git ignore rules
```

*Updated: 2025-11-24*

---

## Memory System

### Memory Files
- **.VSCODE.id.json** - Branch identity and architecture
- **.VSCODE.local.json** - Session history (max 600 lines)
- **.VSCODE.observations.json** - Collaboration patterns (max 600 lines)
- **.VSCODE.ai_mail.json** - Branch messages
- **DOCUMENTS/** - Extended memory (max 10 files, rollover to Memory Bank)

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
- **Past Work:** .VSCODE.local.json session history
- **Working On:** Active PLANs
- **Patterns Learned:** .VSCODE.observations.json
- **Extended Context:** DOCUMENTS/ directory

### Automation Goal
Minimize AI token spend on updates - automate everything possible. Triggers fire on actual changes, not periodic checks.

---

## Notes

- **Human File:** This README.md is AI-managed Markdown - Patrick reads this directly
- **Current State Only:** Snapshot of branch as it exists RIGHT NOW - no history, no future
- **Auto vs Manual:** Automated sections = script-populated, Manual sections = AI writes when something fundamentally changes

---

*Last Updated: 2025-11-24*
