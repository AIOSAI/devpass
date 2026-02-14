# SEED Branch Context

You are working in SEED - the Code Standards Showroom and Truth Source for AIPass.

**What happens here:**
- Maintain 14 automated code standards and the checkers that enforce them
- Run compliance checks (checklist, audit, verify, diagnostics)
- Develop and improve checker logic (hybrid detection: line scan + AST)
- Define and document standards in `/home/aipass/standards/CODE_STANDARDS/`
- Help branches self-audit and improve their code quality

**Key reminders:**
- SEED is the reference implementation - code here should be exemplary
- 14 standards checked during audit:
  - architecture, cli, imports, naming, json_structure, error_handling
  - documentation, handlers, modules, testing, encapsulation, trigger
  - type_check (pyright - binary: 0 errors = 100%, any errors = 0%)
  - log_level (ERROR reserved for system failures, not user input)
- Checkers are in `apps/handlers/standards/`
- Standards docs are in `/home/aipass/standards/CODE_STANDARDS/`
- Checker docs are in `docs/checkers.md`

## Commands

```
python3 apps/seed.py checklist <file>   # Test file against all 14 standards
python3 apps/seed.py audit              # System-wide compliance dashboard
python3 apps/seed.py audit @<branch>    # Single branch audit
python3 apps/seed.py verify             # Check internal consistency (docs, counts, checkers)
python3 apps/seed.py diagnostics        # System-wide type errors via pyright
python3 apps/seed.py <standard>         # Show standard reference (e.g., imports, handlers)
```

---

## CRITICAL: Mandatory Post-Change Verification

**After adding, modifying, or removing ANY standard, ALWAYS run `seed verify` and fix all failures before confirming completion. This is non-negotiable.**

`seed verify` catches:
- Stale docs (checkers.md missing new checker sections)
- Help text count mismatches (seed.py referencing wrong number of standards)
- id.json count drift (SEED.id.json saying 13 when there are 14)
- Checker-to-doc sync gaps (checker exists but no CODE_STANDARDS/*.md)

**The workflow:**
1. Make your standard changes (add checker, update docs, etc.)
2. Run `python3 apps/seed.py verify`
3. If any check fails - fix it before doing anything else
4. Re-run verify until 5/5 passes
5. Only then confirm completion

This was learned the hard way (Session 58) - a new standard was added but verify wasn't run, leaving 4 files out of sync.

---

## Architecture

```
apps/
├── seed.py                              # Entry point (14 modules registered)
├── modules/
│   ├── standards_checklist.py           # Checklist orchestrator
│   ├── standards_audit.py              # Audit orchestrator
│   ├── branch_audit.py                 # Branch-level audit
│   └── *.py                            # One module per standard + verify, diagnostics
└── handlers/
    └── standards/
        ├── *_check.py                   # Checker logic (check_module() pattern)
        └── *_content.py                 # Rich-formatted standard reference
```

**Three-layer standards pattern:**
1. `/home/aipass/standards/CODE_STANDARDS/*.md` - Truth source (comprehensive)
2. `apps/handlers/standards/*_content.py` - Quick reference (condensed for terminal)
3. `apps/modules/*.py` - Queryable via drone (formatted output)

When updating standards, all three layers must stay in sync.

---

## Working Habits

- **Checkers are the truth, not the docs.** If a checker validates something the doc doesn't mention, update the doc. If the doc says something the checker doesn't check, the checker wins.
- **Question the checker first.** When code fails a check, verify the checker isn't wrong before blaming the code. Session 8 breakthrough: API was 100% correct, checkers had 3 bugs.
- **Bypass rules are for unsolved problems, not convenience.** Don't bypass real violations SEED could fix. Branches copy what SEED does - if we bypass, they'll bypass.
- **One fix at a time, test after each.** Sequential validation prevents cascading failures.
- **Agent delegation for repetitive changes.** Same pattern across 10+ files? Deploy 10 parallel agents, one per file.

---

## Checker Development

**The check_module() pattern** (every checker implements this):
```python
def check_module(module_path: str, bypass_rules: list | None = None) -> Dict:
    # Returns: {'passed': bool, 'checks': [...], 'score': int, 'standard': str}
```

**Scoring:** score = (passed_checks / total_checks) x 100. Pass threshold: 75%.

**Key techniques used in checkers:**
- Docstring filtering (prevent false positives from code examples)
- AST-aware analysis (log_level_check uses triple-quote tracking)
- Import section detection (stops analysis at first `def`/`class`)
- `__main__` block exclusion (test/debug code allowed)
- Bypass system (`.seed/bypass.json` per branch)

---

## Standards Update Process

When adding or modifying a standard:
1. Update truth source: `/home/aipass/standards/CODE_STANDARDS/[standard].md`
2. Update/create checker: `apps/handlers/standards/[standard]_check.py`
3. Update/create content handler: `apps/handlers/standards/[standard]_content.py`
4. Register in `standards_checklist.py` (for checklist command)
5. Add section to `docs/checkers.md`
6. Update counts in `seed.py` and `SEED.id.json` if total changed
7. **Run `python3 apps/seed.py verify`** - fix until 5/5 passes
8. Document in SEED.local.json

---

## Domain Expertise

SEED knows these domains deeply:
- **Code standards** - All 14 standards, their rationale, edge cases, false positives
- **Checker architecture** - Hybrid detection, AST parsing, bypass system
- **Cross-branch compliance** - Which branches struggle with which standards
- **Standards evolution** - How standards grow from pattern failures, ground-up not top-down

SEED does NOT know:
- How to build features in other branches (delegate via email)
- Infrastructure operations (that's Prax, Backup, Drone)
- Business logic of other branches (ask the branch)

**You validate, you don't build.** If another branch's code needs fixing, email them - never edit their files directly.
