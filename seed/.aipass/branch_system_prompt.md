# SEED Branch Context

You are working in SEED - the Code Standards Showroom.

Key reminders:
- SEED is the reference implementation - code here should be exemplary
- 12 standards checked during audit:
  - architecture, cli, imports, naming, json_structure, error_handling
  - documentation, handlers, modules, testing, encapsulation, type_check
- Checkers are in `apps/handlers/standards/`
- Type_Check uses pyright (binary: 0 errors = 100%, any errors = 0%)

Commands:
- `python3 apps/seed.py checklist <file>` - Test file against standards
- `python3 apps/seed.py audit` - Check all branches
- `python3 apps/seed.py verify` - Check for stale patterns/docs
- `python3 apps/seed.py diagnostics` - System-wide type errors
