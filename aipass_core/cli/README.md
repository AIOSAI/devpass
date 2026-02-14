# CLI Branch

**Universal Display & Output Service Provider for AIPass**

*Last Updated: 2026-02-14*

## Purpose

CLI provides centralized display and formatting services to all AIPass branches. Other branches import CLI's functions for consistent, Rich-formatted terminal output. Update CLI once, all branches benefit.

## Services Provided

### Display Module (`display.py`)
- `header(title, details=None)` - Bordered section headers with optional key-value details
- `success(message, **kwargs)` - Green checkmark + message with optional details
- `error(message, suggestion=None)` - Red X + error message with optional fix suggestion
- `warning(message, details=None)` - Yellow warning + message with optional details
- `section(title)` - Visual section separators

### Templates Module (`templates.py`)
- `operation_start(operation, **details)` - Standard operation headers with optional detail key-values
- `operation_complete(success=None, **summary)` - Standard completion summaries with statistics

### Rich Console
- Direct access to Rich library console via `console` export
- Beautiful terminal formatting (tables, panels, columns)

### JSON Handler (`handlers/json/json_handler.py`)
- `log_operation(operation, data, module_name)` - Log operations with auto-rotation
- `load_json(module_name, json_type)` / `save_json(...)` - Auto-creating JSON read/write
- `ensure_module_jsons(module_name)` - Create config/data/log JSON triplet from templates
- `increment_counter(module_name, counter_name)` - Data counter management

## Usage

```python
# Import display functions
from cli.apps.modules.display import header, success, error, warning, section

# Import templates
from cli.apps.modules.templates import operation_start, operation_complete

# Import Rich console (lowercase service instance pattern)
from cli.apps.modules import console
console.print("[bold cyan]Formatted output[/bold cyan]")

# JSON handler (internal/handler-level)
from cli.apps.handlers.json.json_handler import log_operation, load_json
```

## Architecture

```
cli/
├── apps/
│   ├── cli.py              # Entry point (showroom)
│   ├── __init__.py
│   ├── modules/            # PUBLIC API (what branches import)
│   │   ├── __init__.py     # Exports: console, header, success, error, warning, section
│   │   ├── display.py      # Display functions + Rich console
│   │   └── templates.py    # Operation templates
│   ├── handlers/           # PRIVATE implementation
│   │   ├── __init__.py
│   │   ├── json/           # JSON auto-creation and management
│   │   │   └── json_handler.py
│   │   └── templates/      # Template handling (placeholder)
│   └── json_templates/     # JSON template storage
│       ├── custom/         # User templates
│       ├── default/        # Built-in templates (config, data, log)
│       └── registry/       # Template registry
├── cli_json/               # Runtime JSON storage (auto-created by json_handler)
└── README.md
```

## Dependency Model

CLI is a **foundation-level service provider**:
- All branches can import from CLI
- CLI does NOT import from other branches (prevents circular dependencies)
- Exception: `cli.py` entry point imports Prax logger for error reporting only

## Standards Compliance

- ✅ lowercase service instances (`console` pattern)
- ✅ Rich formatting throughout
- ✅ SEED module pattern (introspection/help/command handling)
- ✅ Service provider model

## Contact

- Branch: CLI
- Path: `/home/aipass/aipass_core/cli`
- Email: aipass.system@gmail.com