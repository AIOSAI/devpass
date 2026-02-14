# Seed AI Skill Auto-Discovery System Analysis

**Date:** 2025-11-30
**Analyzed Version:** Seed v3.1.0
**Location:** /home/aipass/input_x/a.i/seed/

---

## Executive Summary

The old Seed AI system implements a sophisticated **skill auto-discovery** architecture that dynamically finds, loads, and executes modular skills without hardcoded imports. Skills are pure Python modules with a simple contract: implement `handle_command(user_input: str) -> bool` and you're automatically discovered and integrated.

**Key Innovation:** Zero configuration required. Drop a Python file with `handle_command()` into a skills folder, and Seed automatically discovers and loads it at runtime.

---

## System Architecture Overview

### Core Discovery Flow

```
1. Seed.py starts → discover_skills() called
2. Scans 5 predefined folders for *.py files
3. For each file:
   - Build module name from filename
   - Check Prax registry (enabled/disabled)
   - Import module dynamically
   - Extract handle_command() function
   - Store function reference in handlers list
4. Return list of handler functions
5. Main loop routes user input to each handler until one returns True
```

### Folder Structure

```
/home/aipass/input_x/
├── a.i/
│   └── seed/
│       ├── seed.py                 # Orchestrator (main entry point)
│       ├── custom_skills/          # User-defined skills (empty in analysis)
│       └── seed_state.json         # Runtime state
│
└── skills/                         # Main skills library
    ├── skills_core/                # Core functionality
    │   ├── profile_skill.py
    │   ├── read_file_skill.py
    │   └── hot_reload_skill.py
    ├── skills_memory/              # Memory/context skills
    │   └── live_chat_context_skill.py
    ├── skills_mods/                # Modifications/extensions
    │   └── open_terminal_skill.py
    └── skills_api/                 # API integrations
        └── openai_skill.py
```

---

## Auto-Discovery Mechanism

### Discovery Algorithm (Lines 194-319 in seed.py)

```python
def discover_skills() -> List[Callable]:
    """Auto-discover skills from all skills folders and custom_skills"""
    all_skill_handlers = []
    loaded_skills = []

    # Define folders to scan
    main_skills_root = Path(__file__).parent.parent.parent / "skills"
    skills_folders = [
        ("skills_core", main_skills_root / "skills_core"),
        ("skills_memory", main_skills_root / "skills_memory"),
        ("skills_mods", main_skills_root / "skills_mods"),
        ("skills_api", main_skills_root / "skills_api"),
        ("custom_skills", CUSTOM_SKILLS_FOLDER)
    ]

    for folder_name, folder_path in skills_folders:
        if not folder_path.exists():
            continue

        # Add folder to Python path for imports
        sys.path.insert(0, str(folder_path))

        # Recursively find all .py files
        for file_path in folder_path.rglob("*.py"):
            # Skip hidden, cache, and broken files
            if any(part.startswith('.') or part == '__pycache__' for part in file_path.parts):
                continue
            if 'BROKEN' in file_path.name.upper():
                continue

            # Build module name
            if folder_name == "custom_skills":
                relative_path = file_path.relative_to(folder_path)
                module_path = ".".join(relative_path.with_suffix("").parts)
                module_name = f"custom_skills.{module_path}"
            else:
                module_name = file_path.stem

            # Check Prax registry (enable/disable system)
            registry = load_registry()
            skill_enabled = registry.get(module_name, {}).get("enabled", True)

            if not skill_enabled:
                continue

            # Import the skill module
            module = importlib.import_module(module_name)

            # Check for required handler function
            if hasattr(module, 'handle_command'):
                all_skill_handlers.append(module.handle_command)
                loaded_skills.append(skill_display_name)

                # Track in system state
                system_state['loaded_skills'].append({
                    'name': skill_display_name,
                    'category': folder_name,
                    'path': str(file_path),
                    'has_info': hasattr(module, 'get_skill_info')
                })

    return all_skill_handlers
```

**Key Mechanisms:**

1. **Dynamic Path Management**: `sys.path.insert(0, str(folder_path))` makes skills importable
2. **Recursive Discovery**: `folder_path.rglob("*.py")` finds all Python files
3. **Module Name Construction**: Filename becomes module name (skills_core) or namespaced (custom_skills.subfolder.skill)
4. **Registry Integration**: Prax registry controls enable/disable without code changes
5. **Function Extraction**: `hasattr(module, 'handle_command')` finds the handler
6. **Handler Storage**: Function references stored in list (not modules themselves)

---

## Skill Contract Requirements

### Minimal Skill Structure

A skill MUST implement:

```python
def handle_command(user_input: str) -> bool:
    """
    Process user command

    Args:
        user_input: Raw user input string

    Returns:
        True if command was handled, False to pass to next skill
    """
    # Your logic here
    if user_input.lower() == "my command":
        print("Command executed!")
        return True  # Handled

    return False  # Not my command, pass to next skill
```

### Optional Functions (Recommended)

```python
def get_skill_info() -> Dict[str, Any]:
    """Return metadata about this skill"""
    return {
        "name": "skill_name",
        "version": "1.0.0",
        "description": "What this skill does",
        "commands": ["command1", "command2"],
        "category": "skills_core"
    }

def get_prompt() -> str:
    """Return LLM system prompt text for this skill"""
    return "This skill provides: ..."

def get_skill_context() -> str:
    """Return current skill context/status"""
    return "Skill status: ready"
```

---

## Command Routing Pattern

### Main Chat Loop (Lines 325-456 in seed.py)

```python
while True:
    user_input = input("\nYou: ").strip()

    # Try each skill handler in order
    handled_by_skill = False
    for handler in skill_handlers:
        try:
            result = handler(user_input)
            if result:
                # Special case: hot reload returns new handler list
                if isinstance(result, list):
                    skill_handlers = result  # Update handlers
                handled_by_skill = True
                break
        except Exception as e:
            logger.error(f"Skill handler error: {e}")

    # Fallback: try with "chat " prefix
    if not handled_by_skill:
        for handler in skill_handlers:
            if handler(f"chat {user_input}"):
                handled_by_skill = True
                break

    # Final fallback: OpenAI skill
    if not handled_by_skill:
        # Find and call OpenAI skill directly
        ...
```

**Routing Logic:**

1. **First Pass**: Direct routing - first handler to return True wins
2. **Second Pass**: Prefixed routing - try with "chat " prefix
3. **Final Fallback**: OpenAI skill for general conversation
4. **Order Matters**: Skills checked in discovery order

---

## Example Skills Analysis

### 1. Simple Skill: read_file_skill.py

**Purpose:** Read files from disk and store content

**Key Features:**
- Regex pattern matching: `read file (.+)`
- 3-file JSON structure (config, data, log)
- Auto-detection of calling AI
- Exit cleanup with atexit
- Rolloff logic (max 2 files cached)

**Discovery Requirements Met:**
```python
def handle_command(user_input: str) -> bool:
    match = re.match(r"read file (.+)", user_input, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip()
        # Read and process file
        return True
    return False

def get_skill_info():
    return {
        "name": "read_file_skill",
        "description": "Simple file reading",
        "commands": ["read file <path>"],
        "version": "0.1.0"
    }
```

### 2. Advanced Skill: hot_reload_skill.py

**Purpose:** Live reload system without restart

**Key Innovation:** Returns **new handler list** instead of True/False

**Discovery Requirements Met:**
```python
def handle_command(user_input: str) -> Union[bool, List]:
    if user_input in ["999", "update system", "reload system"]:
        fresh_handlers = discover_fresh_skills()  # Re-discover all skills
        print(f"System refreshed: {len(fresh_handlers)} skills reloaded")
        return fresh_handlers  # <- KEY: Return handler list
    return False
```

**Advanced Features:**
- Module cache purging: `del sys.modules[module_name]`
- Deleted module detection
- Prax registry integration
- JSON state preservation

### 3. Context Skill: live_chat_context_skill.py

**Purpose:** Maintain conversation memory across turns

**Key Features:**
- 20-message rolling buffer
- OpenAI API integration
- Auto-clear on exit
- Contextual conversation

**Discovery Requirements Met:**
```python
def handle_command(user_input: str) -> bool:
    if user_input.lower().startswith("chat "):
        message = user_input[5:]
        add_to_memory("user", message)
        messages = get_context_messages()
        response = openai_skill.get_response(messages)
        add_to_memory("assistant", response)
        print(f"{ai_name}: {response}")
        return True
    return False
```

---

## JSON Data Management Pattern

### 3-File Structure (Standard)

All skills use this pattern:

```
skill_name_config.json   # Configuration settings (rarely changes)
skill_name_data.json     # Runtime data (changes frequently)
skill_name_log.json      # Operation logs (append-only)
```

### Auto-Detection System

Skills detect which AI is calling them and store JSON files accordingly:

```python
def get_caller_ai_info():
    """Walk call stack to find which AI is running"""
    for frame_info in inspect.stack():
        frame_path = Path(frame_info.filename)
        if "a.i" in frame_path.parts:
            ai_index = frame_path.parts.index("a.i")
            ai_name = frame_path.parts[ai_index + 1]  # e.g., "seed"
            ai_path = Path(*frame_path.parts[:ai_index + 2])

            # Determine JSON folder based on skill category
            skill_category = get_skill_category()  # From __file__ location
            json_folder = get_json_folder_name(skill_category)
            json_folder_path = ai_path / json_folder

            return ai_name, ai_path, json_folder_path
```

**Example Path Resolution:**
- Skill location: `/skills/skills_core/read_file_skill.py`
- Calling AI: `/a.i/seed/seed.py`
- JSON location: `/a.i/seed/skills_core_json/read_file_skill_*.json`

---

## Integration with Prax Registry

### Enable/Disable System

Skills check Prax registry before loading:

```python
from prax.prax_on_off import load_registry

registry = load_registry()
skill_enabled = registry.get(module_name, {}).get("enabled", True)

if not skill_enabled:
    logger.info(f"[-] {module_name} - disabled in Prax registry")
    continue
```

**Benefits:**
- Runtime enable/disable without code changes
- Centralized control
- Default enabled (safe fallback)
- Hot reload respects registry

---

## Hot Reload Architecture

### Key Innovation: Live Code Updates

```python
def reload_skill_module(module_name: str, file_path: Path) -> bool:
    """Reload a specific skill module with truth-based cleanup"""
    # 1. Purge existing version from memory
    if module_name in sys.modules:
        del sys.modules[module_name]

    # 2. Import fresh from disk
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return True
```

**Workflow:**
1. User types "999" or "reload system"
2. Hot reload skill discovers all skills again
3. Purges old modules from sys.modules
4. Re-imports fresh from disk
5. Returns new handler list to Seed
6. Seed replaces old handlers with new ones
7. System continues without restart

**Breakthrough:** Edit skill code, type "999", test immediately!

---

## Patterns to Replicate for Nexus

### 1. Core Discovery Pattern

```python
# Nexus implementation should:
- Scan predefined folders recursively
- Build module names from file structure
- Import dynamically with importlib
- Extract handler functions
- Store function references (not modules)
- Integrate with Prax registry
```

### 2. Skill Contract

```python
# Minimal interface:
def handle_command(user_input: str) -> bool:
    # Return True if handled, False otherwise
    pass

# Optional but recommended:
def get_skill_info() -> dict:
    # Return metadata
    pass
```

### 3. Hot Reload Support

```python
# Support returning new handler lists:
def handle_command(user_input: str) -> Union[bool, List]:
    if reload_requested:
        return discover_fresh_skills()  # Return new handlers
    return False
```

### 4. JSON Management

```python
# Use 3-file structure:
- skill_config.json  # Settings
- skill_data.json    # State
- skill_log.json     # History

# Auto-detect caller:
- Walk call stack
- Find calling AI
- Store in appropriate folder
```

### 5. Registry Integration

```python
# Check Prax before loading:
registry = load_registry()
if not registry.get(module_name, {}).get("enabled", True):
    skip_skill()
```

---

## Advanced Features Observed

### 1. Module Cache Management

```python
def purge_deleted_modules() -> List[str]:
    """Remove modules from memory that no longer exist on disk"""
    existing_files = get_all_existing_files()
    existing_module_names = set(existing_files.keys())

    loaded_modules = [name for name in sys.modules.keys()
                     if not name.startswith('_') and '.' not in name]

    purged_modules = []
    for module_name in loaded_modules:
        if module_name not in existing_module_names:
            if purge_module_from_memory(module_name):
                purged_modules.append(module_name)

    return purged_modules
```

### 2. Caller Detection (Stack Walking)

```python
def get_caller_ai_info():
    """Walk the call stack to find which AI is running"""
    stack = inspect.stack()
    for frame_info in stack:
        frame_path = Path(frame_info.filename)
        if "a.i" in frame_path.parts:
            # Extract AI name and path
            ai_index = frame_path.parts.index("a.i")
            ai_name = frame_path.parts[ai_index + 1]
            ai_path = Path(*frame_path.parts[:ai_index + 2])
            return ai_name, ai_path, json_folder_path
```

### 3. Exit Cleanup Hooks

```python
import atexit

def clear_cache_content():
    """Clear data on exit to prevent token explosion"""
    # Purge large content, keep metadata
    pass

atexit.register(clear_cache_content)
```

### 4. Logging System

```python
def log_skill_operation(operation_details, result_data=None, error=None):
    """Log operation with timestamp and details"""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation_details,
        "success": error is None,
        "result": result_data if error is None else None,
        "error": str(error) if error else None
    }

    # Load existing log
    log = json.load(open(SKILL_LOG_FILE)) if SKILL_LOG_FILE.exists() else []
    log.insert(0, entry)  # Newest first
    log = log[:50]  # Keep last 50 entries

    # Save log
    json.dump(log, open(SKILL_LOG_FILE, "w"), indent=2)
```

---

## Code Quality Observations

### Strengths

1. **Zero Configuration**: Drop file, it works
2. **Hot Reload**: Edit code without restart
3. **Registry Integration**: Central enable/disable
4. **Modular Design**: Each skill is independent
5. **Fallback Handling**: Multiple routing strategies
6. **Error Isolation**: One skill error doesn't crash system

### Potential Improvements for Nexus

1. **Dependency Declaration**: Skills declare dependencies explicitly
2. **Skill Priorities**: Order/priority system instead of discovery order
3. **Command Registration**: Skills register commands upfront
4. **Event Hooks**: Pre/post processing hooks
5. **Skill Communication**: Inter-skill messaging
6. **Version Management**: Skill versioning and compatibility
7. **Async Support**: Handle long-running operations

---

## Implementation Checklist for Nexus

### Phase 1: Core Discovery
- [ ] Implement folder scanning (rglob)
- [ ] Dynamic module import (importlib)
- [ ] Handler extraction (hasattr check)
- [ ] Handler storage (list of functions)
- [ ] Prax registry integration

### Phase 2: Routing
- [ ] Main loop with handler iteration
- [ ] First-match-wins logic
- [ ] Fallback strategies
- [ ] Error isolation per skill

### Phase 3: Hot Reload
- [ ] Module cache purging
- [ ] Fresh discovery function
- [ ] Handler list replacement
- [ ] Deleted module detection

### Phase 4: JSON Management
- [ ] 3-file structure (config/data/log)
- [ ] Caller detection (stack walking)
- [ ] Auto-path resolution
- [ ] Exit cleanup hooks

### Phase 5: Advanced Features
- [ ] Skill metadata system
- [ ] Logging infrastructure
- [ ] State persistence
- [ ] Registry enable/disable

---

## Conclusion

The Seed skill auto-discovery system is a **mature, production-tested architecture** that achieves:

- **Zero-config modularity**: Drop file, it works
- **Live code updates**: Edit without restart
- **Graceful degradation**: Errors don't crash system
- **Clean separation**: Skills are fully independent
- **Runtime control**: Enable/disable without code changes

**Recommendation for Nexus:** Replicate this architecture with the following additions:

1. **Command Registration**: Skills declare commands upfront for better routing
2. **Dependency Graph**: Explicit dependency management
3. **Event System**: Pre/post hooks for cross-cutting concerns
4. **Async Support**: Non-blocking handlers for long operations
5. **Skill Marketplace**: Discovery from multiple sources

This analysis provides a complete blueprint for implementing auto-discovery in Nexus.

---

**Analysis completed:** 2025-11-30
**Analyzed by:** Claude (Nexus Agent)
**Source:** /home/aipass/input_x/a.i/seed/seed.py v3.1.0
