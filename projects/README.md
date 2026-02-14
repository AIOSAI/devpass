# PROJECTS

**Purpose:** Project workshop - where real products get built
**Location:** `/home/aipass/projects`
**Profile:** Workshop
**Created:** 2025-11-23

---

## Overview

PROJECTS is the workshop of the AIPass ecosystem. Not a service branch - this is where things that face the outside world get built. Apps, tools, and products that people actually use. Work arrives from Patrick or DEV_CENTRAL as ideas with scaffolding, and gets built into working software here.

### What This Branch Does

- Builds and manages real projects (feel_good_app, guest_portal, youtube)
- Studies external repos for patterns and ideas
- Orchestrates development through agent delegation
- Takes handoffs from Patrick/DEV_CENTRAL and owns them to completion

### Current State

**Active Projects:** 3 (feel_good_app, guest_portal, youtube)
**External Repos:** 9 cloned for reference/study
**Status:** Active workshop with ongoing development

---

## Projects

### feel_good_app
React Native/Expo mood tracking app. Feature-complete core with timed tasks, habits, mood tracking, and insights. Most mature project in the workshop.
- **Location:** `feel_good_app/app/` (React Native source)
- **Key features:** Mood tracking, timed tasks, habit classification, skip reflections, insights tab
- **Recent work:** UTC timezone bug fix, timed tasks + habits feature

### guest_portal
Early-stage project with initial docs and notepad.
- **Location:** `guest_portal/`

### youtube
Early-stage project with initial docs and notepad.
- **Location:** `youtube/`

---

## Architecture

- **Pattern:** Auto-discovery module orchestration
- **Entry Point:** `apps/projects.py`
- **Module Interface:** Modules in `apps/modules/` implementing `handle_command(command, args) -> bool`

No custom modules deployed yet - the orchestrator framework is in place for future use.

---

## Directory Structure

```
/home/aipass/projects/
├── apps/
│   ├── projects.py          # Entry point (orchestrator)
│   ├── modules/             # Command modules (none yet)
│   ├── handlers/
│   │   └── json/
│   │       └── json_handler.py  # JSON utilities
│   ├── extensions/          # Future extensions
│   ├── plugins/             # Future plugins
│   └── json_templates/      # JSON file templates
├── feel_good_app/           # React Native mood tracker (active)
│   ├── app/                 # Source code
│   ├── design/              # Design assets
│   └── docs/                # Project docs
├── guest_portal/            # Guest portal project (early stage)
├── youtube/                 # YouTube project (early stage)
├── external_repos/          # Cloned repos for reference/study
│   ├── moltbot/             # Personal AI assistant
│   ├── claude-code-telegram/
│   ├── claudecode-telegram/
│   ├── ccbot/
│   ├── ccc/
│   ├── claude_office/
│   ├── gastown/
│   ├── happy-coder/
│   └── minibook/
├── artifacts/               # Old/experimental code
├── tests/                   # Test suite
├── tools/                   # Tooling
├── logs/                    # Log files
├── docs/                    # Branch documentation
└── ai_mail.local/           # Branch messaging
```

---

## Key Files

| File | Purpose |
|------|---------|
| `apps/projects.py` | Main orchestrator with auto-discovery |
| `apps/handlers/json/json_handler.py` | Self-healing JSON system |
| `PROJECTS.id.json` | Branch identity |
| `PROJECTS.local.json` | Session history |
| `PROJECTS.observations.json` | Collaboration patterns |

---

## Memory System

- **PROJECTS.id.json** - Branch identity (permanent)
- **PROJECTS.local.json** - Session history (max 600 lines, auto-rolls)
- **PROJECTS.observations.json** - Patterns learned (max 600 lines)
- **DASHBOARD.local.json** - System-wide status

---

## Dependencies

- Python 3.12+
- AIPass core infrastructure (prax, cli)

---

*Last Updated: 2026-02-14*
