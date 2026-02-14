# CLI Branch

**Universal Display & Output Service Provider for AIPass**

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
- `operation_start()` - Standard operation headers
- `operation_complete()` - Standard completion summaries

### Rich Console
- Direct access to Rich library console via `console` export
- Beautiful terminal formatting (tables, panels, columns)

## Usage

```python
# Import display functions
from cli.apps.modules.display import header, success, error, warning, section

# Import templates
from cli.apps.modules.templates import operation_start, operation_complete

# Import Rich console (lowercase service instance pattern)
from cli.apps.modules import console
console.print("[bold cyan]Formatted output[/bold cyan]")
```

## Architecture

```
cli/
├── apps/
│   ├── cli.py              # Entry point
│   ├── __init__.py
│   ├── modules/            # PUBLIC API (what branches import)
│   │   ├── __init__.py     # Exports: console, header, success, error, warning, section
│   │   ├── display.py      # Display functions + Rich console
│   │   └── templates.py    # Operation templates
│   ├── handlers/           # PRIVATE implementation
│   │   ├── __init__.py
│   │   ├── json/           # JSON operations
│   │   │   └── json_handler.py
│   │   └── templates/      # Template handling
│   ├── json_templates/     # JSON template storage
│   │   ├── custom/         # User templates
│   │   ├── default/        # Built-in templates (config, data, log)
│   │   └── registry/       # Template registry
│   ├── extensions/
│   └── plugins/
├── cli_json/               # CLI-specific JSON storage
│   └── error_handler_json/ # Error handler config/data/logs
└── README.md
```

## Dependency Model

CLI is a **foundation-level service provider**:
- All branches can import from CLI
- CLI does NOT import from other branches (prevents circular dependencies)
- CLI cannot import Prax (Prax imports CLI)

## Standards Compliance

- ✅ lowercase service instances (`console` pattern)
- ✅ Rich formatting throughout
- ✅ SEED module pattern (introspection/help/command handling)
- ✅ Service provider model
- ✅ 100% Seed audit compliance

## Contact

- Branch: CLI
- Path: `/home/aipass/aipass_core/cli`
- Email: aipass.system@gmail.com