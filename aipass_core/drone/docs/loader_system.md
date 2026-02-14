# Drone Module Loader System

Technical documentation for Drone's command discovery and loading system.

---

## Overview

The loader system discovers Drone's available modules and commands through a three-stage process: file discovery, validation, and command tree building. It uses a reactive caching pattern to optimize performance.

**Key Components:**
- `apps/modules/loader.py` - Orchestrator
- `apps/handlers/loader/file_discovery.py` - File discovery
- `apps/handlers/loader/command_builder.py` - Tree building
- `apps/handlers/loader/__init__.py` - Public API

---

## Architecture

### Orchestrator Pattern

The loader module (`loader.py`) orchestrates the loading workflow but delegates all implementation to handlers:

```
loader.py (orchestrator)
    ↓
handlers/loader/ (implementation)
    ├── file_discovery.py
    ├── json_loading.py
    ├── command_validation.py
    ├── path_validation.py
    └── command_builder.py
```

This follows the standard 3-layer architecture:
- **Module**: Coordinates workflow
- **Handlers**: Implement specific functionality
- **Registry**: Maintains state and cache

---

## Discovery Flow

### 1. File Discovery

**Function:** `discover_command_files()` in `file_discovery.py`

Searches two locations for command JSON files:

1. **Commands directory** (`/home/aipass/aipass_core/drone/commands/`)
   - Recursively scans for `*.json` files
   - Uses `COMMANDS_DIR.rglob("*.json")`

2. **Registry sources** (`drone_registry.json`)
   - Checks registry for registered modules
   - Looks for module-specific command files in `commands/modules/`

**Example:**
```python
command_files = discover_command_files()
# Returns: [
#   Path('/home/aipass/aipass_core/drone/commands/core_commands.json'),
#   Path('/home/aipass/aipass_core/drone/commands/modules/seed.json'),
#   ...
# ]
```

### 2. Command Loading

**Function:** `build_command_tree()` in `loader.py`

Orchestrates the complete loading workflow:

```python
def build_command_tree() -> Dict:
    """Build complete command tree from all sources"""

    # 1. Discover command files
    command_files = discover_command_files()

    # 2. Load and validate commands
    command_tree = {}
    for json_file in command_files:
        file_commands = load_json_commands(json_file)
        commands_data = extract_commands_from_json(file_commands)

        # 3. Validate each command
        for cmd_name, cmd_data in commands_data.items():
            if validate_command_data(cmd_data):
                command_tree[cmd_name] = cmd_data

    # 4. Update registry with results
    registry["commands"] = command_tree
    save_registry(registry)

    return command_tree
```

### 3. Caching Strategy

**Function:** `get_command_tree()` in `loader.py`

Uses reactive pattern - checks cache first, rebuilds only when dirty:

```python
def get_command_tree() -> Dict:
    """Get current command tree (cached or rebuild)"""

    # Try cache first
    cached_commands = get_cached_commands()
    if cached_commands is not None:
        return cached_commands

    # Cache miss - rebuild
    command_tree = build_command_tree()
    mark_clean()  # Mark registry as clean

    return command_tree
```

**Cache invalidation:** Registry is marked "dirty" when:
- Command files are modified
- New modules are registered
- Manual invalidation via `mark_dirty()`

---

## Handle Command Pattern

### Module Requirements

Every Drone module must expose a `handle_command()` function:

```python
def handle_command(command: str, args: list) -> bool:
    """Handle commands for this module

    Args:
        command: Command name (e.g., 'load', 'scan')
        args: List of command arguments

    Returns:
        True if command was handled, False otherwise
    """
    if command != "load":
        return False

    # Handle the command
    result = main()
    console.print(f"✅ Command executed: {result}")
    return True
```

### Discovery Process

When Drone loads modules, it:

1. **Imports the module** from `apps/modules/`
2. **Checks for `handle_command`** function
3. **Registers the module** if found
4. **Routes commands** to appropriate handler

**Example from loader.py:**
```python
def handle_command(command: str, args: list) -> bool:
    """Handle loader commands"""

    # Only handles 'load' command
    if command != "load":
        return False

    # Check for help
    if len(args) > 0 and args[0] in ['--help', '-h', 'help']:
        print_help()
        return True

    # Execute
    result = main()
    console.print(f"✅ Command loader: {len(result)} commands loaded")
    return True
```

---

## Command Tree Structure

### Flattening Nested Commands

**Function:** `flatten_nested_commands()` in `command_builder.py`

Converts nested command structures into flat dictionaries:

```python
# Input (nested)
{
    "tools": {
        "seed": {"path": "/home/aipass/seed/seed.py"},
        "drone": {"path": "/home/aipass/aipass_core/drone/drone.py"}
    }
}

# Output (flat)
{
    "tools_seed": {"path": "/home/aipass/seed/seed.py"},
    "tools_drone": {"path": "/home/aipass/aipass_core/drone/drone.py"}
}
```

**Implementation:**
```python
def flatten_nested_commands(commands: Dict, parent_key: str = "") -> Dict:
    """Recursively flatten nested command structure"""
    flat_commands = {}

    for key, value in commands.items():
        current_key = f"{parent_key}_{key}" if parent_key else key

        if isinstance(value, dict):
            if "path" in value or "command" in value:
                # Command definition - add it
                flat_commands[current_key] = value
            else:
                # Nested structure - recurse
                nested = flatten_nested_commands(value, current_key)
                flat_commands.update(nested)

    return flat_commands
```

### Merging Multiple Sources

**Function:** `merge_command_sources()` in `command_builder.py`

Combines commands from multiple JSON files:

```python
sources = {
    "core": {"run_seed": {"path": "seed.py"}},
    "tools": {"backup": {"path": "backup.py"}}
}

merged = merge_command_sources(sources)
# Result: {"run_seed": {...}, "backup": {...}}
```

**Conflict resolution:** Last source wins (with warning logged)

---

## File Discovery Patterns

### Recursive Scanning

**Pattern:** `rglob("*.json")`

```python
# Finds all JSON files in directory tree
if COMMANDS_DIR.exists():
    for json_file in COMMANDS_DIR.rglob("*.json"):
        command_files.append(json_file)
```

**Directory structure:**
```
commands/
├── core_commands.json         # Found
├── system/
│   └── admin_commands.json    # Found
└── modules/
    ├── seed.json              # Found
    └── flow.json              # Found
```

### Registry-Based Discovery

Checks registry for module-specific command files:

```python
# Read registry
registry_file = DRONE_JSON_DIR / "drone_registry.json"
with open(registry_file, 'r') as f:
    registry = json.load(f)

# Find module command files
for module_name in registry.get("modules", {}):
    module_file = COMMANDS_DIR / "modules" / f"{module_name}.json"
    if module_file.exists():
        command_files.append(module_file)
```

---

## Key Functions Reference

### File Discovery

| Function | Purpose | Returns |
|----------|---------|---------|
| `discover_command_files()` | Find all command JSON files | `List[Path]` |
| `scan_commands_directory()` | Scan commands/ directory | `List[Path]` |
| `scan_registry_sources()` | Find module command files | `List[Path]` |

### Command Loading

| Function | Purpose | Returns |
|----------|---------|---------|
| `build_command_tree()` | Build complete command tree | `Dict` |
| `get_command_tree()` | Get cached or rebuild tree | `Dict` |
| `resolve_command()` | Find command by name | `Optional[Dict]` |
| `get_available_commands()` | List all command names | `List[str]` |

### Command Building

| Function | Purpose | Returns |
|----------|---------|---------|
| `flatten_nested_commands()` | Flatten nested structure | `Dict` |
| `build_flat_command_dict()` | Wrapper with logging | `Dict` |
| `merge_command_sources()` | Combine multiple sources | `Dict` |

### Validation

| Function | Purpose | Returns |
|----------|---------|---------|
| `validate_command_data()` | Validate command structure | `bool` |
| `validate_command_path()` | Check path validity | `bool` |
| `resolve_command_path()` | Resolve path to absolute | `Optional[Path]` |

---

## Data Flow Example

```
1. User runs: drone load
   ↓
2. Drone imports loader module
   ↓
3. Calls loader.handle_command("load", [])
   ↓
4. loader.main() → build_command_tree()
   ↓
5. discover_command_files()
   → Finds: core_commands.json, seed.json, flow.json
   ↓
6. For each file:
   → load_json_commands()
   → extract_commands_from_json()
   → validate_command_data()
   ↓
7. Build flat command tree
   → flatten_nested_commands()
   → merge_command_sources()
   ↓
8. Update registry
   → registry["commands"] = command_tree
   → save_registry()
   ↓
9. Mark registry clean
   ↓
10. Return command tree (27 commands loaded)
```

---

## Module Requirements Summary

For a module to be discoverable by Drone:

1. **Location:** Must be in `aipass_core/drone/apps/modules/`
2. **Function:** Must expose `handle_command(command: str, args: list) -> bool`
3. **Return:** Returns `True` if command handled, `False` otherwise
4. **Pattern:** Should check command name first, return False if not handled

**Minimal example:**
```python
def handle_command(command: str, args: list) -> bool:
    """Handle my_module commands"""
    if command not in ["my_cmd"]:
        return False

    # Handle command
    print("Command executed")
    return True
```

---

## Performance Characteristics

### Cache Hit Path
```
get_command_tree() → get_cached_commands() → return cached
Time: ~1ms
```

### Cache Miss Path
```
get_command_tree() → build_command_tree()
  → discover_command_files()     (~10ms)
  → load_json_commands() × N     (~5ms per file)
  → validate_command_data() × M  (~1ms per command)
  → save_registry()              (~5ms)
Time: ~50-100ms (for 5 files, 27 commands)
```

### Optimization Strategy
- **Reactive caching:** Only rebuild when needed
- **Registry tracking:** Knows when files change
- **Lazy loading:** Commands loaded on first access
- **Batch processing:** All files processed in single pass

---

## Error Handling

All functions follow standard error pattern:

```python
try:
    # Operation
    result = do_something()
    logger.info(f"[{MODULE_NAME}] Success: {result}")
    return result

except Exception as e:
    logger.error(f"[{MODULE_NAME}] Error: {e}")
    return default_value  # Empty dict, list, None, etc.
```

**Graceful degradation:** Errors in one command file don't stop processing of others

---

## Related Systems

- **Registry:** Maintains command cache and state
- **JSON Handler:** Manages 3-file JSON pattern
- **Prax Logger:** Provides system-wide logging
- **CLI Module:** Handles Rich console output

---

*Generated: 2025-11-29*
*Version: 2.0.0*
