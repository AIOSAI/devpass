# SEED - Standards Truth Source & Architectural Model

**Path:** `/home/aipass/seed`
**Profile:** Workshop / Reference Implementation
**Purpose:** Demonstrate proper AIPass architecture and maintain standards compliance

---

## What Is SEED?

SEED is the **SHOWROOM/MODEL** branch for AIPass - the living reference implementation that demonstrates proper architecture through executable, queryable standards modules.

**Why it matters:** Other branches query SEED to learn correct patterns. When you run `drone @seed [standard]`, you're learning from working code that demonstrates each standard.

---

## Key Capabilities

- **14 Standards** - Architecture, CLI, Diagnostics, Documentation, Encapsulation, Error Handling, Handlers, Imports, JSON Structure, Log Level, Modules, Naming, Testing, Trigger
- **14 Automated Checkers** - Standards compliance checking with hybrid detection (line scan + AST) and bypass-aware validation
- **Audit System** - Branch-wide and system-wide compliance auditing
- **Verify System** - Internal documentation consistency checks (5 checks)
- **Diagnostics** - System-wide type checking via pyright integration

---

## Directory Structure

```
seed/
├── .seed/
│   └── bypass.json                 # Branch-level standards bypass config
├── apps/
│   ├── seed.py                     # Entry point (auto-discovers modules)
│   ├── modules/                    # 16 modules
│   │   ├── *_standard.py           # 13 standards query modules
│   │   ├── standards_checklist.py  # File compliance checker
│   │   ├── standards_audit.py      # Branch/system audit
│   │   ├── standards_verify.py     # Internal consistency
│   │   └── diagnostics_audit.py    # Type checking
│   ├── handlers/
│   │   ├── standards/              # 14 check + 11 content handlers
│   │   │   ├── *_check.py          # Automated checkers
│   │   │   └── *_content.py        # Quick reference content
│   │   ├── audit/                  # Audit system handlers
│   │   │   ├── branch_audit.py
│   │   │   ├── bypass_audit.py
│   │   │   ├── discovery.py
│   │   │   └── display.py
│   │   ├── verify/                 # Verification handlers
│   │   │   ├── checker_sync.py
│   │   │   ├── command_check.py
│   │   │   ├── freshness_check.py
│   │   │   ├── help_check.py
│   │   │   ├── orchestrator.py
│   │   │   └── stale_check.py
│   │   ├── diagnostics/            # Type checking handlers
│   │   │   ├── discovery.py
│   │   │   └── runner.py
│   │   ├── config/
│   │   │   └── ignore_handler.py
│   │   ├── file/
│   │   │   └── file_handler.py
│   │   └── json/
│   │       └── json_handler.py
│   └── json_templates/
├── docs/                           # Technical documentation
│   ├── architecture.md
│   ├── audit_system.md
│   ├── bypass_system.md
│   ├── checkers.md
│   ├── commands_reference.md
│   └── standards_system.md
├── standards/                      # Source of truth (markdown)
│   └── CODE_STANDARDS/*.md         # 14 standard definitions
├── SEED.id.json
├── SEED.local.json
├── SEED.observations.json
└── README.md
```

---

## Commands

### Query Standards

```bash
python3 apps/seed.py                    # Show all available standards
python3 apps/seed.py architecture       # Show specific standard
python3 apps/seed.py log_level          # Show log level standard
python3 apps/seed.py imports
```

### Check Compliance

```bash
python3 apps/seed.py checklist <file>   # Check single file against all 14 standards
python3 apps/seed.py audit              # Audit all branches
python3 apps/seed.py audit @cortex      # Audit specific branch
python3 apps/seed.py audit --show-bypasses  # Show bypassed files
```

### Verify & Diagnostics

```bash
python3 apps/seed.py verify             # Internal consistency (5 checks)
python3 apps/seed.py diagnostics        # System-wide type checking
```

### Via Drone

```bash
drone @seed cli                         # Query standard
drone @seed checklist <file>            # Check file
drone @seed audit                       # Full system audit
drone @seed verify                      # Consistency checks
drone @seed diagnostics                 # Type checking
```

---

## 14 Standards

| Standard | Description | Checker |
|----------|-------------|---------|
| Architecture | 3-layer pattern (entry, modules, handlers) | architecture_check.py |
| CLI | No bare print(), use console.print() | cli_check.py |
| Diagnostics | Type checking via pyright | diagnostics_check.py |
| Documentation | Shebang, docstrings, headers | documentation_check.py |
| Encapsulation | No cross-branch handler imports | encapsulation_check.py |
| Error Handling | Try/except, no bare exceptions | error_handling_check.py |
| Handlers | Domain organization, independence | handlers_check.py |
| Imports | AIPASS_ROOT pattern, structured order | imports_check.py |
| JSON Structure | 3-file pattern (config/data/log) | json_structure_check.py |
| Log Level | ERROR reserved for system failures, not user input | log_level_check.py |
| Modules | handle_command(), <400 lines | modules_check.py |
| Naming | snake_case, path=context | naming_check.py |
| Testing | Test file structure | testing_check.py |
| Trigger | Event bus patterns, no inline file ops | trigger_check.py |

---

## Three-Layer Standards Pattern

Each standard is maintained across three synchronized layers:

1. `/home/aipass/standards/CODE_STANDARDS/*.md` - Truth source (comprehensive reference)
2. `apps/handlers/standards/*_content.py` - Quick reference (condensed for terminal display)
3. `apps/modules/*_standard.py` - Queryable via drone (Rich-formatted output)

---

## Bypass System

Branches configure standards exceptions via `.seed/bypass.json`:

```json
{
  "bypass": [
    {
      "file": "apps/modules/logger.py",
      "standard": "cli",
      "reason": "Circular dependency - logger cannot import CLI"
    }
  ]
}
```

**Use For:** Architectural limitations, checker false positives
**Not For:** Hiding real violations you could fix

---

## Integration

**Depends On:** Cortex (template registry), CLI (display), Drone (routing)
**Provides To:** All branches (standards reference + compliance tools)

---

## Key Files

| File | Purpose |
|------|---------|
| `apps/seed.py` | Entry point (auto-discovers modules) |
| `apps/modules/standards_checklist.py` | File compliance checker (14 standards) |
| `apps/modules/standards_audit.py` | Branch/system audit |
| `apps/modules/standards_verify.py` | Internal consistency (5 checks) |
| `apps/handlers/standards/*_check.py` | 14 automated checkers |
| `/home/aipass/standards/CODE_STANDARDS/` | Standards source of truth |

---

**Created:** 2025-11-12
**Last Updated:** 2026-02-14
**Branch Status:** Production (reference implementation)
