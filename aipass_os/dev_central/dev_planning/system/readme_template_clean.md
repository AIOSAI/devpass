# Branch README Template (Clean - Direct Fill-In)

Use this template to update your branch README. Fill in actual values, not placeholders.

---

# [BRANCH_NAME]

**Purpose:** [One line - what this branch does]
**Location:** `[path]`
**Created:** [date]

---

## Architecture

- **Pattern:** Modular (apps/modules/handlers)
- **Entry Point:** `apps/[branch_name].py`
- **Module Interface:** `handle_command(args) -> bool`

---

## Directory Structure

```
[ACTUAL tree output - run: tree -L 3 apps/ or ls -la apps/]
```

---

## Modules

| Module | Purpose |
|--------|---------|
| [module_name.py] | [What it does - 1 line] |

*List all files in apps/modules/ that have handle_command()*

---

## Commands

| Command | Description |
|---------|-------------|
| `drone @[branch] [command]` | [What it does] |

*List actual commands this branch supports*

---

## Dependencies

- [List key imports/dependencies]
- Or: "Standard library only" / "See requirements.txt"

---

## Integration Points

| Direction | System | Purpose |
|-----------|--------|---------|
| Uses | [system] | [why] |
| Provides | [system] | [what] |

---

## Memory Files

- `[BRANCH].id.json` - Identity
- `[BRANCH].local.json` - Session history (600 lines max)
- `[BRANCH].observations.json` - Patterns (600 lines max)
- `DOCUMENTS/` - Long-term (10 files max)

---

## Notes

- **Status:** [Active / Minimal / In Development]
- **Last Updated:** [date]

---

*Truth only. No future plans. Current state as it exists NOW.*
