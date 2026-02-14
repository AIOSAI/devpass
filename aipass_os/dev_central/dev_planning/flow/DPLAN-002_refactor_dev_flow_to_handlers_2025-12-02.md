# DPLAN-002: Refactor dev_flow to handlers

> Extract 9 implementation functions from dev_flow.py module to handlers/ per Seed 3-tier architecture

## Vision
Transform dev_flow.py from a 490-line monolith into a thin orchestrator that delegates all implementation to handlers. Pass Seed audit at 80%+.

## Current State
- dev_flow.py contains ALL logic (490 lines)
- Failed Seed audit (60% score)
- 9 implementation functions in module that belong in handlers:
  - `get_next_plan_number` - counter logic
  - `render_template`, `get_default_template` - template handling
  - `cmd_create` - create plan implementation
  - `cmd_list` - list plans implementation
  - `cmd_status` - status overview implementation
  - `extract_status`, `get_status_icon` - status helpers
  - `show_help`, `print_introspection` - display helpers

## What Needs Building

### 1. Handler Directory Structure
```
apps/handlers/plan/
├── __init__.py      # Export public functions
├── counter.py       # get_next_plan_number
├── template.py      # render_template, get_default_template
├── create.py        # cmd_create implementation
├── list.py          # cmd_list implementation
├── status.py        # cmd_status, extract_status, get_status_icon
└── display.py       # show_help, print_introspection
```

### 2. Handler Files
Each handler:
- Pure functions with clear responsibility
- Metadata header (Seed standard)
- NO Prax logging (modules log, handlers don't)
- Return tuples: (success, data/error_msg)

### 3. Refactored dev_flow.py
- ~100-140 lines (thin orchestrator)
- Import handlers at top
- handle_command() routes to handlers
- Module does the logging
- Module coordinates display

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Handler organization | By domain (plan/) | Matches Flow/Seed pattern |
| Logging | Module only | 3-tier standard compliance |
| Return pattern | Tuples | (success, data, error) for consistency |
| Import style | From handlers import func | Per Seed convention |

## Status
- [ ] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [x] Complete
- [ ] Abandoned

## Notes
- Source: Email from @dev_central (48da909c)
- Reference implementations: Flow, AI_MAIL, Seed handlers
- Target: Pass Seed audit 80%+

---
*Created: 2025-12-02*
*Updated: 2025-12-02*
