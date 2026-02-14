# PRAX Unified Monitoring - Implementation Structure

**Date:** 2025-11-23
**Status:** Ready to Build
**Approach:** Reuse 85% existing code, build 15% new

---

## Quick Summary

**What We Have (Ready to Use):**
- ✅ File watching (branch_watcher + handlers/watcher/)
- ✅ Log monitoring (discovery/watcher.py - sophisticated log tailing!)
- ✅ Branch registry reading
- ✅ Ignore patterns system
- ✅ Display formatting

**What We Need to Build:**
- ⚡ Unified orchestrator module (monitor_module.py)
- ⚡ New handlers/monitoring/ directory (6 handlers)
- ⚡ Interactive filtering (commands while running)
- ⚡ Branch attribution ([SEED], [PRAX], etc.)
- ⚡ Event queue coordination

---

## PHASE 1: Structure (Build These Placeholders First)

### NEW MODULE: `apps/modules/monitor_module.py`

```python
#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: monitor_module.py - Unified Monitoring Module
# Date: 2025-11-23
# Version: 0.1.0
# Category: prax/modules
# =============================================

"""Unified monitoring orchestrator - Mission Control for autonomous branches"""

import sys
from pathlib import Path
from typing import List

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header, success, error

def handle_command(command: str, args: List[str]) -> bool:
    """Handle monitor command - REQUIRED FOR AUTO-DISCOVERY"""
    if command != "monitor":
        return False

    # TODO: Start monitoring
    console.print("[green]Starting unified monitoring...[/green]")
    return True

def print_introspection():
    """Show connected handlers"""
    console.print("[bold cyan]Monitoring Module[/bold cyan]")
    console.print("Connected Handlers:")
    console.print("  handlers/monitoring/")
    console.print("    - unified_stream.py")
    console.print("    - branch_detector.py")
    console.print("    - interactive_filter.py")
    console.print("    - monitoring_filters.py")
    console.print("    - event_queue.py")
    console.print("    - module_tracker.py")

if __name__ == "__main__":
    print_introspection()
```

---

### NEW HANDLERS DIRECTORY: `apps/handlers/monitoring/`

Create these placeholder files:

#### `__init__.py`
```python
"""Monitoring handlers for unified system"""
```

#### `unified_stream.py`
```python
"""Display handler - single point for terminal output"""
from cli.apps.modules import console

def print_event(event_type, branch, message, level='info'):
    """Format and print event with [BRANCH] attribution"""
    # TODO: Implement formatting
    console.print(f"[{branch}] {message}")
```

#### `branch_detector.py`
```python
"""Detect which branch owns an event"""
from pathlib import Path

def detect_branch_from_path(file_path: str) -> str:
    """Map file path to branch name"""
    # TODO: Use BRANCH_REGISTRY.json
    return "UNKNOWN"
```

#### `interactive_filter.py`
```python
"""Parse and apply user commands while monitoring"""
from dataclasses import dataclass
from typing import Set

@dataclass
class FilterState:
    watched_branches: Set[str] = None
    verbosity: str = 'low'

def parse_command(cmd: str) -> tuple:
    """Parse user command like 'watch seed'"""
    # TODO: Implement parsing
    return None, []
```

#### `monitoring_filters.py` (Based on backup_system config_handler!)
```python
"""Unified ignore pattern system - adapted from backup_system/config_handler.py"""
from pathlib import Path
from typing import List, Dict, Optional

# Based on backup_system's EXCELLENT pattern organization!
# Clear categories with comments explaining each section

# Files/folders to NEVER monitor (like backup's GLOBAL_IGNORE_PATTERNS)
MONITOR_IGNORE_PATTERNS = [
    # Python cache and temp files
    "__pycache__", "*.pyc", "*.pyo",

    # Virtual environments (massive file count)
    ".venv", "venv",

    # Version control
    ".git",

    # Claude session files (change constantly)
    ".claude/todos", ".claude/shell-snapshots",

    # User directories (not code)
    "Downloads", "Videos", "Pictures",

    # ... (see full list in agent's design)
]

# Always monitor these (like backup's IGNORE_EXCEPTIONS)
MONITOR_ALWAYS_PATTERNS = [
    # AIPass memory files - CRITICAL!
    "*.id.json", "*.local.json", "*.observations.json",

    # System logs - we ARE the monitor!
    "system_logs/*.log",

    # Python source
    "*.py",

    # Documentation
    "README.md", "CLAUDE.md",
]

# NEW for monitoring: Watch but filter content
CONTENT_FILTER_PATTERNS = {
    "*.log": {
        "filter_mode": "errors_only",
        "show_patterns": ["ERROR", "CRITICAL", "WARNING"],
    }
}

def should_monitor(path: Path) -> bool:
    """Check if path should be monitored"""
    # Check ALWAYS patterns first (exceptions)
    # Then check IGNORE patterns
    # Default to monitoring
    return True  # TODO: Implement
```

#### `event_queue.py`
```python
"""Thread-safe event coordination"""
from queue import Queue
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MonitoringEvent:
    timestamp: datetime
    event_type: str  # 'file', 'log', 'module'
    branch: str
    message: str
    level: str

class MonitoringQueue:
    def __init__(self):
        self.queue = Queue()

    def enqueue(self, event):
        self.queue.put(event)

    def dequeue(self, timeout=0.1):
        # TODO: Implement dequeue
        pass
```

#### `module_tracker.py`
```python
"""Track module execution from logs"""

def track_module_start(module_name: str, command: str):
    """Track when module starts"""
    # TODO: Implement tracking
    pass
```

---

## EXISTING CODE TO REUSE

### From `branch_watcher.py` (340 lines)
**USE:** watchdog setup, event callbacks, branch registry
**MODIFY:** Remove console output, add event queue callback

### From `handlers/watcher/monitor.py` (194 lines)
**USE:** BranchFileHandler, start/stop monitoring
**MODIFY:** Import from monitoring_filters instead of hardcoded

### From `handlers/discovery/watcher.py` (290 lines) - KEY COMPONENT!
**USE:** Log tailing logic (already monitors logs in real-time!)
**MODIFY:** Add branch detection, send to event queue

### From `handlers/registry/reader.py` (125 lines)
**USE AS-IS:** read_registry(), get_branch_paths()

### From `handlers/config/ignore_patterns.py` (92 lines)
**REFERENCE:** Pattern for monitoring_filters.py

---

## ARCHITECTURE FLOW

```
User Input Thread ──┐
                    ├──> Event Queue ──> Display Thread
File Watcher Thread─┤        │
                    │        ▼
Log Watcher Thread──┤    Filter State
                    │   (what to show)
Module Tracker ─────┘
```

---

## SEED STANDARDS CHECKLIST

### Module Requirements (`monitor_module.py`)
- [ ] META DATA HEADER with version
- [ ] Standard import order (Infrastructure → Stdlib → Prax → Services → Internal)
- [ ] `handle_command(command, args) -> bool` - REQUIRED
- [ ] Orchestration only (thin module, thick handlers)
- [ ] `print_introspection()` showing handlers
- [ ] 135-155 lines target (can be larger for complex)

### Handler Requirements (`handlers/monitoring/*.py`)
- [ ] META DATA HEADER with version
- [ ] Domain organization (monitoring/ not utils/)
- [ ] Path = context naming (not monitoring_monitor.py)
- [ ] Pure functions with error raising
- [ ] No module imports (handler independence)
- [ ] <300 lines each (ideal)

---

## KEY UPDATE: Backup System's Superior Filter Design

After reviewing `/home/aipass/aipass_core/backup_system/apps/handlers/config/config_handler.py`:

### Why It's Better:
1. **221 ignore patterns** (vs our initial 20!)
2. **Clear category comments** explaining WHY each pattern is ignored
3. **Multiple pattern lists** for different behaviors
4. **Critical warnings** (e.g., "prevent recursive backups - CRITICAL!")
5. **Exception patterns** clearly marked with "=== TEMPLATES: FULL EXCEPTION ==="

### Our Adaptation:
```
Backup System              →  Monitoring System
GLOBAL_IGNORE_PATTERNS     →  MONITOR_IGNORE_PATTERNS
IGNORE_EXCEPTIONS          →  MONITOR_ALWAYS_PATTERNS
DIFF_IGNORE_PATTERNS       →  CONTENT_FILTER_PATTERNS (NEW!)
(none)                     →  HIGHLIGHT_PATTERNS (NEW!)
```

---

## BUILD SEQUENCE

### Step 1: Create Structure (30 min)
1. Create `apps/modules/monitor_module.py` (placeholder)
2. Create `apps/handlers/monitoring/` directory
3. Create all 7 handler placeholders
4. Test: `python3 apps/modules/monitor_module.py` (shows introspection)
5. Test: `python3 apps/prax.py monitor` (should route to module)

### Step 2: Basic Stream (2 hours)
1. Implement basic file watching in monitor_module
2. Implement basic log watching (copy from discovery/watcher.py)
3. Implement unified_stream.print_event()
4. Test: See files + logs in one terminal

### Step 3: Branch Detection (1 hour)
1. Implement branch_detector using BRANCH_REGISTRY.json
2. Add [BRANCH] to all events
3. Test: Every event shows correct branch

### Step 4: Interactive Commands (2 hours)
1. Implement threading structure
2. Implement interactive_filter
3. Add command parsing (watch, verbosity)
4. Test: Type commands while monitoring runs

### Step 5: Polish (1 hour)
1. Add color coding
2. Add soft start (quiet mode)
3. Add help display
4. Test: Full workflow

---

## KEY INSIGHTS FROM INVESTIGATION

### 1. PRAX Already Has Sophisticated Monitoring!
- `handlers/discovery/watcher.py` has **real-time log tailing**
- Already tracks log position, shows only NEW entries
- Already detects commands and separates with headers
- Color-codes by log level (red=ERROR, yellow=WARNING)

### 2. Reuse Percentage: 85%
- File watching: Complete, just needs callbacks
- Log monitoring: Complete, just needs integration
- Branch registry: Complete, ready to use
- Display formatting: Exists, needs unification

### 3. Critical New Component: Event Queue
- Thread-safe coordination between watchers
- Prevents terminal flooding
- Enables filtering before display

### 4. Seed Standards are Clear
- Modules orchestrate (thin)
- Handlers implement (thick)
- `handle_command()` required for auto-discovery
- No cross-domain imports

---

## NOTES FOR PATRICK

1. **We have more than expected** - Discovery/watcher.py is a goldmine
2. **Threading is the way** - Watchdog already uses threads
3. **Start with placeholders** - Get structure right first
4. **Duct tape approach works** - Basic version in ~6 hours
5. **Interactive might be tricky** - But Control Terminal fallback is easy

---

**Ready to start building?** Structure first, then fill in implementation!