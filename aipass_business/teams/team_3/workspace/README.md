# TEAM_3_WS

**Purpose:** Build what TEAM_3 designs. Receive build tasks via dispatch, execute them with quality.
**Location:** `/home/aipass/aipass_business/teams/team_3/workspace`
**Profile:** Workshop
**Created:** 2026-02-08

---

## Architecture

- **Pattern:** Modular
- **Structure:** `apps/` directory with `modules/` and `handlers/` subdirectories
- **Orchestrator:** `apps/team_3_ws.py` — auto-discovers and routes to modules
- **Module Interface:** All modules implement `handle_command(args) -> bool`

---

## Directory Structure

```
/home/aipass/aipass_business/teams/team_3/workspace
├── ai_mail.local/         # Branch messaging (inbox, sent, deleted)
├── apps/
│   ├── team_3_ws.py       # Entry point
│   ├── extensions/
│   ├── handlers/
│   ├── json_templates/
│   ├── modules/
│   └── plugins/
├── .archive/
├── artifacts/
├── .backup/
├── docs/
├── dropbox/
├── logs/
├── .seed/
├── team_3_ws_json/
├── tests/
│   ├── conftest.py
│   └── __init__.py
├── tools/
├── DASHBOARD.local.json
├── dev.local.md
├── TEAM_3_WS.id.json
├── TEAM_3_WS.local.json
├── TEAM_3_WS.observations.json
├── notepad.md
├── pytest.ini
├── README.md
└── requirements.txt
```

---

## Role & Capabilities

TEAM_3_WS is the **workspace engineer** for TEAM_3 (Business Team Manager). It receives build tasks via dispatch and executes them.

**What I do:**
- Execute build tasks dispatched from @team_3
- Write code, create systems, implement features
- Run seed audits to ensure standards compliance
- Manage flow plans for multi-step work
- Deploy agents for focused building tasks

**What I don't do:**
- Design architecture — @team_3 is the thinker
- Modify other branches without authorization
- Skip memory updates after work sessions

---

## Recent Work

- **Article #2 draft** — `vera/public/article_2_draft.md` (9-layer architecture deep dive)
- **Identity roadmap** — `vera/roadmap/identity_roadmap.md` (4 sections from TEAM_3 spec)
- **Public repo files** — CONTRIBUTING.md, issue templates, LICENSE, HONESTY_AUDIT.md

---

## Dependencies

No external dependencies yet. See `requirements.txt` for template. Python >=3.12 required.

---

## Integration Points

- **Receives from:** @team_3 (build tasks via dispatch)
- **Reports to:** @dev_central (completion summaries)
- **Uses:** ai_mail (messaging), drone (routing), flow (plans), seed (standards)

---

## Memory System

### Memory Files
- **TEAM_3_WS.id.json** — Branch identity and architecture
- **TEAM_3_WS.local.json** — Session history (max 600 lines)
- **TEAM_3_WS.observations.json** — Collaboration patterns (max 600 lines)
- **DASHBOARD.local.json** — System-wide status
- **docs/** — Technical documentation (markdown)

### Health Monitoring
- 🟢 **Green (Healthy):** Under 80% of limits
- 🟡 **Yellow (Warning):** 80-100% of limits
- 🔴 **Red (Critical):** Over limits (compression needed)

---

## System References

- **Code Standards:** `/home/aipass/aipass_core/standards/code_standards.md`
- **Template Source:** `/home/aipass/aipass_core/branch_operations/templates/`

---

## Notes

- **Human File:** This README.md is AI-managed Markdown — Patrick reads this directly
- **Current State Only:** Snapshot of branch as it exists RIGHT NOW — no history, no future
- Future plans → PLAN files in flow system
- Past work → TEAM_3_WS.local.json session history
- Patterns learned → TEAM_3_WS.observations.json
- Technical docs → docs/ directory

---

*Last Updated: 2026-02-19*
