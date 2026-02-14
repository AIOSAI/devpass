# Unified Trigger System Investigation

**Created:** 2025-11-30
**Status:** Investigation Complete
**Owner:** DEV_CENTRAL

---

## Goal

Create a unified trigger system that all branches can import (like Prax/CLI) for consistent event handling across the ecosystem.

---

## Current State - Trigger Analysis

### Summary Table

| Branch | Trigger Type | Library | Auto? | Manual? |
|--------|--------------|---------|-------|---------|
| MEMORY_BANK | Prax Logger Hook + File Watcher | prax + watchdog | Yes | Yes |
| FLOW | File Watcher + Commands | watchdog | Yes | Yes |
| CORTEX | Decorator + Commands | custom | Silent | Yes |
| PRAX | Multi-threaded Watcher | watchdog | Yes | Yes |
| SEED | Commands only | none | No | Yes |
| AI_MAIL | Error Watcher + Commands | watchdog | Yes | Yes |
| DRONE | Commands only | none | No | Yes |
| BACKUP_SYSTEM | Commands only | none | No | Yes |

### Key Findings

**1. Watchdog is the standard**
- 4 branches use `watchdog` library
- FileSystemEventHandler pattern is proven
- Observer + handler model works well

**2. Prax Logger Hook Pattern (KEY DISCOVERY)**
- Memory Bank piggybacks on Prax logger's `_ensure_watcher()`
- First log call from ANY branch → triggers startup checks
- No daemon needed, runs once per process
- Location: `prax/apps/modules/logger.py:92-118`
- Also triggers bulletin propagation (`check_and_propagate()`)
- **This pattern should be reused for unified triggers**

**3. No unified interface**
- Each branch implements its own watcher
- Duplicate code across branches
- No shared utilities

**4. Different event types**
- File changes (most common)
- Log entries (AI_MAIL, PRAX)
- Line count thresholds (MEMORY_BANK)
- Command execution (all)

**5. Manual commands are universal**
- All branches have `handle_command()` interface
- This is already standardized
- Automatic triggers are the problem area

---

## Current Implementations

### MEMORY_BANK Triggers
```
Location: apps/handlers/monitor/memory_watcher.py
Library: watchdog (optional) + Prax logger hook (primary)

Trigger 1: Prax Logger Hook (AUTOMATIC - no daemon needed)
- Prax logger's _ensure_watcher() calls check_and_rollover() on first log
- File: prax/apps/modules/logger.py:103-104
- Any branch logging → triggers Memory Bank startup check
- Pattern: "piggyback on existing infrastructure"

Trigger 2: Startup Check (DIRECT)
- check_and_rollover() can be called directly
- Checks all branches for over-limit files
- Also processes memory_pool, plans, code_archive

Trigger 3: File Watcher (OPTIONAL daemon)
- watchdog observer monitors memory files
- Real-time line count updates
- Start: python3 memory_bank.py watch
```

### FLOW Triggers
```
Location: apps/modules/registry_monitor.py
Library: watchdog (PlanFileWatcher)
Events: PLAN file created/deleted/moved → registry update
Start: flow registry start
```

### PRAX Triggers
```
Location: apps/handlers/monitoring/
Library: watchdog + threading
Events: File changes + log entries → event queue → display
Start: prax monitor
3 threads: display, file watcher, log watcher
```

### AI_MAIL Triggers
```
Location: apps/modules/error_monitor.py
Library: watchdog
Events: Log file changes → ERROR detection → email notification
Start: ai_mail error_monitor watch
```

### CORTEX Triggers
```
Location: apps/handlers/registry/decorators.py
Pattern: @ensure_valid_registry decorator
Events: Registry stale/mismatch → silent regeneration
Trigger: Automatic before update operations
```

---

## Proposed Unified System

### Concept

Create a trigger service (like CLI/Prax) that branches import:

```python
from aipass_core.triggers import (
    FileWatcher,
    LogWatcher,
    EventQueue,
    TriggerDecorator
)
```

### Components

**1. FileWatcher**
- Wraps watchdog.Observer
- Standard events: on_created, on_modified, on_deleted, on_moved
- Configurable patterns (*.json, *.md, etc.)
- Branch-aware path detection

**2. LogWatcher**
- Tails log files
- Pattern matching (ERROR, WARNING, etc.)
- Branch attribution

**3. EventQueue**
- Thread-safe priority queue
- Deduplication
- Configurable handlers

**4. TriggerDecorator**
- Decorator factory for auto-triggers
- Like Cortex's @ensure_valid_registry
- Reusable across branches

### Interface Design

```python
# Example usage in a branch
from aipass_core.triggers import FileWatcher, on_file_change

class MyBranchWatcher(FileWatcher):
    patterns = ["*.local.json", "*.observations.json"]

    @on_file_change("modified")
    def handle_memory_change(self, event):
        # Check line count, trigger rollover, etc.
        pass
```

### Where It Would Live

```
aipass_core/
├── triggers/               # New trigger service
│   ├── __init__.py
│   ├── apps/
│   │   └── triggers.py     # Entry point
│   ├── modules/
│   │   └── watcher.py      # Watcher orchestration
│   └── handlers/
│       ├── file_watcher.py  # watchdog wrapper
│       ├── log_watcher.py   # log tailing
│       ├── event_queue.py   # thread-safe queue
│       └── decorators.py    # trigger decorators
```

---

## Migration Path

### Phase 1: Build Core
- Create triggers branch in aipass_core
- Implement FileWatcher wrapper
- Implement EventQueue

### Phase 2: Migrate One Branch
- Choose MEMORY_BANK (simplest watcher)
- Refactor to use unified system
- Validate it works

### Phase 3: Migrate Others
- FLOW registry_monitor
- AI_MAIL error_monitor
- PRAX monitoring (most complex)

### Phase 4: Standardize
- All branches import from triggers
- Remove duplicate watchdog code
- Document patterns

---

## Benefits

1. **Consistency** - One way to do file watching
2. **Less code** - Shared utilities, no duplication
3. **Easier debugging** - Centralized logging
4. **Branch-aware** - Path → branch detection built-in
5. **Testable** - Mock the trigger service

---

## Open Questions

1. Should this be a new branch or extend Prax?
2. How to handle branch-specific event types?
3. Config: per-branch or centralized?
4. Startup: auto-start watchers or manual?

---

## Architectural Decision: Registration vs Convention

### Option A: Registration-Based (Explicit)

Branches explicitly register their triggers:

```python
# In branch's __init__.py or startup
from aipass_core.triggers import register

register.on_startup('memory_bank', check_and_rollover)
register.on_file_change('memory_bank', ['*.local.json'], update_line_counts)
```

**Pros:** Clear, explicit, no magic
**Cons:** Branches must know about triggers, still some coupling

### Option B: Convention-Based (Auto-Discovery)

Triggers module auto-discovers by convention:

```python
# branches/memory_bank/handlers/triggers.py (convention file)

def on_startup():
    """Called automatically on first logger use"""
    from .monitor.memory_watcher import check_and_rollover
    check_and_rollover()

def on_file_change():
    """Auto-wired file watcher"""
    return {
        'patterns': ['*.local.json', '*.observations.json'],
        'callback': update_line_counts
    }
```

Triggers module scans all branches for `handlers/triggers.py`, auto-wires everything.

**Pros:** Branches just follow convention, triggers module handles wiring
**Cons:** Magic (harder to debug), convention must be documented

### Option C: Hybrid (Config + Convention)

Each branch has `triggers.config.json`:

```json
{
  "on_startup": ["handlers.monitor.memory_watcher:check_and_rollover"],
  "on_file_change": {
    "patterns": ["*.local.json"],
    "handler": "handlers.tracking.line_counter:update_counts"
  }
}
```

Triggers module reads config, imports handlers, wires up.

**Pros:** Declarative, easy to understand, no code changes to branch
**Cons:** Another config file, string-based imports

### Separation of Concerns

| Component | Lives In | Responsibility |
|-----------|----------|----------------|
| Business logic | Branch handlers | What to DO when triggered |
| Trigger types | aipass_core/triggers | File watcher, startup hook, decorator |
| Wiring/registration | TBD | Connect triggers to handlers |

### Current Thinking

**Hybrid approach seems best:**
1. Triggers module provides mechanisms (watchers, hooks, decorators)
2. Branches have `triggers.py` or `triggers.config.json`
3. Prax logger calls `triggers.run_startup_hooks()` instead of hardcoded imports
4. Auto-discovery finds all registered hooks

This way:
- Zero coupling in Prax logger (just calls triggers)
- Branches own their trigger config
- Triggers module handles the infrastructure

---

## Option D: Event-Based (The Prax Pattern)

**Inspiration:** How Prax logger works - branches just use simple "words" (logger.info, logger.warning), Prax handles all the complexity.

### The Pattern

```python
# Branch code - simple event firing
from aipass_core.triggers import trigger

def save_memory_file(data, file_path):
    # ... do the save ...
    trigger.fire('memory_saved', branch='FLOW', file=file_path, lines=450)

def close_plan(plan_id):
    # ... close the plan ...
    trigger.fire('plan_closed', plan_id=plan_id)

def send_email(to, subject, message):
    # ... send email ...
    trigger.fire('email_sent', to=to, subject=subject)
```

### Triggers Module Has The Logic

```python
# Inside aipass_core/triggers/handlers.py

@on_event('memory_saved')
def handle_memory_saved(branch, file, lines):
    """All the rollover logic lives HERE, not in branches"""
    config = load_branch_config(branch)
    if lines > config.max_lines:
        execute_rollover(branch, file)
    update_dashboard_memory_status(branch, lines)

@on_event('plan_closed')
def handle_plan_closed(plan_id):
    """Registry update logic lives HERE"""
    update_flow_registry(plan_id, status='closed')
    refresh_dashboard_plans()
```

### Benefits

1. **Branches stay simple** - just fire events, no logic about what happens
2. **Triggers owns all logic** - easy to update, one place to change
3. **Prax-like simplicity** - import, use simple verbs, done
4. **Decoupled** - branch doesn't know about rollover, dashboard, etc.
5. **Testable** - mock trigger.fire() in tests
6. **Extensible** - add new reactions without touching branch code

### The "Words" (Events)

Like Prax has `info`, `warning`, `error`, triggers would have:

| Event | When Fired | Triggers Module Reacts |
|-------|------------|------------------------|
| `memory_saved` | After saving *.local.json | Check lines, rollover, update dashboard |
| `plan_created` | After creating PLAN file | Register in flow, update dashboard |
| `plan_closed` | After closing plan | Update registry, refresh dashboard |
| `error_logged` | After logging ERROR | Send notification email |
| `branch_started` | On branch startup | Run startup checks |

### Separation

| What | Where | Example |
|------|-------|---------|
| Business action | Branch handler | Actually save the file |
| Event announcement | Branch handler | `trigger.fire('memory_saved')` |
| Reaction logic | Triggers module | Check threshold, rollover, dashboard |

**Branches don't need trigger logic. They just announce what happened.**

---

## Research: Existing Python Event Libraries (2025-11-30)

### Library Comparison

| Library | Stars | Last Updated | Best For |
|---------|-------|--------------|----------|
| **Blinker** | 2,000+ | Nov 2024 | Most use cases, Flask ecosystem |
| **pymitter** | 146 | Jul 2025 | Namespaces, wildcards, TTL |
| **psygnal** | 117 | Oct 2025 | Type safety, dataclass events |
| **PyPubSub** | 204 | Mar 2019 | Desktop apps, mature API |
| **python-dispatch** | 42 | Jun 2023 | Zero dependencies, property observers |

### Top Recommendation: Blinker

```python
from blinker import signal

# Create named signal
memory_saved = signal('memory-saved')

# Connect handler
@memory_saved.connect
def on_save(sender, **kwargs):
    print(f"Saved: {kwargs['lines']} lines")

# Fire event
memory_saved.send('flow', lines=450)
```

**Why Blinker:**
- 11M+ weekly PyPI downloads
- Flask/Pallets ecosystem (battle-tested)
- Named signals work across modules without imports
- Weak references prevent memory leaks
- Simple API, minimal boilerplate

### Lessons from Django/Flask Signals

**What they do right:**
1. **Weak references by default** - auto-cleanup, no memory leaks
2. **Always `**kwargs`** - forward compatibility
3. **Sender filtering** - only receive from specific sources
4. **Simple API** - create, connect, send (that's it)
5. **~500 lines** - keep it simple!

**What to avoid:**
- ❌ Heavy processing in handlers (delegate to workers)
- ❌ Modifying data in signal handlers (just notify)
- ❌ Assuming execution order
- ❌ Overusing signals (direct calls are clearer when appropriate)

### AIPass Implementation Strategy

**Phase 1: Start Custom (~50 lines)**
```python
# aipass_core/triggers/core.py
class Trigger:
    _handlers = {}

    @classmethod
    def on(cls, event, handler):
        """Register handler for event"""
        cls._handlers.setdefault(event, []).append(handler)

    @classmethod
    def off(cls, event, handler):
        """Remove handler for event"""
        if event in cls._handlers:
            cls._handlers[event].remove(handler)

    @classmethod
    def fire(cls, event, **data):
        """Fire event to all handlers"""
        for handler in cls._handlers.get(event, []):
            try:
                handler(**data)
            except Exception as e:
                print(f"Handler error: {e}")

trigger = Trigger()
```

**Usage in branches:**
```python
from aipass_core.triggers import trigger

# Fire events (branches just announce)
trigger.fire('memory_saved', branch='FLOW', lines=450)
trigger.fire('plan_closed', plan_id='PLAN0123')
trigger.fire('error_logged', branch='SEED', message='Import failed')
```

**Handlers in triggers module:**
```python
# aipass_core/triggers/handlers.py

def setup_handlers():
    trigger.on('memory_saved', handle_memory_saved)
    trigger.on('plan_closed', handle_plan_closed)

def handle_memory_saved(branch, lines, **kwargs):
    """All rollover logic lives here"""
    if lines > get_threshold(branch):
        execute_rollover(branch)
    update_dashboard(branch, lines)

def handle_plan_closed(plan_id, **kwargs):
    """Registry update logic lives here"""
    update_flow_registry(plan_id)
    refresh_dashboard()
```

**Phase 2: Upgrade to Blinker (when needed)**
- Need async support
- Memory leaks become an issue
- Want sender filtering
- Need temporary connections / muting

**Phase 3: External Broker (only if distributed)**
- Kafka/Redis for cross-process events
- Only if AIPass goes multi-machine

---

## Notes

- This is a significant architectural change
- Current system works, just inconsistent
- Low priority unless triggers become a problem
- Pattern is proven (watchdog + handler)
- **Research complete: Blinker is the gold standard**
- **Start custom, upgrade to library when complexity warrants**

---

*Investigation complete: 2025-11-30*
*8 branches analyzed via parallel agents*
