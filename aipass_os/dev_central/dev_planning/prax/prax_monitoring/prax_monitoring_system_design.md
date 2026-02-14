# PRAX Monitoring System - Comprehensive Design

**Date:** 2025-11-23
**Status:** Planning Phase
**Priority:** HIGH - Foundation for system-wide visibility
**Approach:** Slow, thoughtful, well-architected

---

## Vision Statement

**Goal:** Create a unified real-time monitoring system that provides complete visibility into AIPass ecosystem activity through a single terminal interface.

**What we want to see:**
- 📁 File changes (created, modified, deleted, moved)
- 📝 Live log output (what's being logged in real-time)
- ⚡ Module execution (what commands are running, which modules)
- ⚠️ System warnings (file deletions, errors, anomalies)

**Philosophy:**
- One terminal, complete picture
- Auto-discovery of new branches
- Smart filtering (show what matters)
- Color-coded priorities (green info, yellow warnings, red errors)
- Zero maintenance (self-registering system)

---

## Current State Assessment

### What Exists:

1. **branch-watcher** (`apps/modules/branch_watcher.py`)
   - Watches file changes across branches
   - Uses watchdog library (inotify-based)
   - **Problem:** Hits inotify limit (8,000+ files watched)
   - **Problem:** Basic ignore patterns (hardcoded in monitor.py)
   - **Status:** Working but limited

2. **run command** (`apps/modules/run_module.py`)
   - Continuous logging mode
   - Shows log output in terminal
   - **Status:** Working

3. **Separate ignore systems:**
   - Logger ignore patterns: `apps/handlers/config/ignore_patterns.py`
   - Watcher ignore patterns: `apps/handlers/watcher/monitor.py` (hardcoded)
   - Git ignore patterns: `/home/aipass/.gitignore`
   - **Problem:** Not aligned, inconsistent

4. **Old polling watcher** (`dropbox/watcher.py`)
   - MD5 hash-based polling
   - No inotify dependency
   - Simple, no limits
   - **Status:** Archived but functional

### What's Missing:

1. **Unified display** - Files, logs, and modules in one view
2. **Smart filtering** - Aligned ignore patterns across all systems
3. **Auto-discovery** - New branches automatically monitored
4. **Module execution tracking** - See what commands are running
5. **System warnings** - Alert on deletions, errors, anomalies
6. **Configurable scope** - Watch all branches or specific subset

---

## Design Questions & Decisions

### Q1: Monitoring Approach - inotify vs Polling?

**Option A: inotify (watchdog library)**
- ✅ Instant notification (real-time)
- ✅ Low CPU usage (event-driven)
- ❌ Has system limits (~8,192 watches)
- ❌ Complex to debug
- **Verdict:** Use IF we can reduce file count with smart filtering

**Option B: Polling (MD5 hash checks)**
- ✅ No system limits
- ✅ Simple, predictable
- ❌ 2-second delay
- ❌ Higher CPU usage
- **Verdict:** Fallback option if inotify won't work

**Option C: Hybrid**
- inotify for critical files (.py, .md, .json configs)
- Polling for everything else
- **Verdict:** Overcomplicated for v1

**DECISION:** Start with inotify + smart filtering. If limits hit, switch to polling.

---

### Q2: Ignore Pattern Strategy

**Current Approach (Git):**
```
# List everything
# Comment out (#) what you WANT tracked
# Leave uncommented what you IGNORE
```

**Git Ignore Patterns (from /home/aipass/.gitignore):**
```
IGNORED:
.archive, .backup, .cache, .config, .local, .venv
ai_mail.local, aipass_json, crash-logs
Desktop, Downloads, dropbox, logs, system_logs
Music, Pictures, Videos, sandbox.img

TRACKED (commented out with #):
#.claude, #aipass_core, #aipass_business
#BRANCH_REGISTRY.json, #CLAUDE.md
#DOCUMENTS, #MEMORY_BANK, #mcp_servers
#planning, #speakeasy, #tests, #tools
```

**Watcher Pattern Options:**

**Option A: Mirror Git Exactly**
- Copy .gitignore patterns 1:1
- What git tracks = what watcher watches
- ✅ Consistency with version control
- ❌ Git ignores logs, but we WANT to watch logs
- ❌ Different purposes (git = version control, watcher = runtime monitoring)

**Option B: Custom Watcher Patterns**
- Start with git patterns as baseline
- Add exceptions for monitoring-specific needs:
  - Watch logs (we're monitoring log output)
  - Watch certain JSON files (*_config.json, *_id.json)
  - Ignore data/temp JSON (*_data.json, *_log.json)
- ✅ Tailored for monitoring purpose
- ✅ User can refine through trial and error
- ⚠️ Requires maintenance

**Option C: Whitelist Approach**
- Only watch specific file types: .py, .md, .json, .yaml
- Ignore directories: .git, .venv, __pycache__
- ✅ Simple, predictable
- ❌ Might miss important files

**DECISION:** Option B - Start with git ignore baseline + monitoring exceptions

---

### Q3: What Files Should We Actually Watch?

**User's Intent:**
- "I want to see JSONs" - Config files, structure files
- "We're tracking logs" - Log output monitoring
- "Focus on AIPass-specific things" - Not system files, libraries, IDE configs

**Proposed Whitelist (what TO watch):**
```
SOURCE CODE:
*.py              # Python code
*.md              # Documentation
*.sh              # Shell scripts

CONFIGURATION:
*.json            # Config files (with exceptions below)
*.yaml, *.yml     # Config files
*.toml            # Config files
Dockerfile        # Container configs
requirements.txt  # Dependencies
.gitignore        # Version control
pyrightconfig.json # Type checking

EXCEPTIONS (JSON files to IGNORE):
*_data.json       # Runtime data files
*_log.json        # Log data files
*_registry.json   # Registry files (too large, frequently updated)
```

**Proposed Blacklist (what NOT to watch):**
```
SYSTEM DIRECTORIES:
.git/, .venv/, __pycache__/, node_modules/
.cache/, .local/, .config/, .ssh/
.pytest_cache/, .mypy_cache/

IDE/EDITOR:
.vscode/, .idea/, .eclipse/, .vs/
.claude/ (except settings we care about)
*.swp, *.swo, *.swn (vim swap files)

BACKUPS/ARCHIVES:
.backup/, .archive/, backups/
Archive/, Backups/, External_Code_Sources/
*.backup, *.bak, *~

SYSTEM FILES:
.bash_history, .python_history
.wget-hsts, .lesshst
crash-logs/

USER CONTENT:
Desktop/, Downloads/, Music/, Pictures/, Videos/
dropbox/ (unless we decide to use it)

BUILD ARTIFACTS:
build/, dist/, lib/, *.pyc, *.pyo

LARGE FILES:
*.img, *.iso, *.vmdk
sandbox.img
```

**QUESTION FOR USER:** Should we watch logs directory in real-time, or is that handled by the "log monitoring" component separately?

---

### Q4: Unified Display Design

**Terminal Layout Options:**

**Option A: Three Sections (Stacked)**
```
┌─────────────────────────────────────────────────────┐
│ AIPASS Real-Time Monitor                           │
├─────────────────────────────────────────────────────┤
│ 📁 FILE CHANGES (last 10)                          │
│ [15:30:42] seed/handlers/json/ops.py MODIFIED      │
│ [15:30:45] cortex/README.md MODIFIED               │
├─────────────────────────────────────────────────────┤
│ 📝 LOGS (last 10)                                  │
│ [15:30:42] seed_audit.log: Running standards check│
│ [15:30:45] cortex_create.log: Creating branch     │
├─────────────────────────────────────────────────────┤
│ ⚡ MODULE EXECUTION (active)                       │
│ [15:30:40] drone @seed audit (PID: 12345)         │
│ [15:30:44] drone @cortex create (PID: 12346)      │
└─────────────────────────────────────────────────────┘
```

**Option B: Unified Stream (Mixed)**
```
┌─────────────────────────────────────────────────────┐
│ AIPASS Real-Time Monitor                           │
├─────────────────────────────────────────────────────┤
│ [15:30:40] ⚡ MODULE: drone @seed audit            │
│ [15:30:42] 📁 FILE: seed/handlers/json/ops.py ✏️   │
│ [15:30:42] 📝 LOG: seed_audit.log: Standards check │
│ [15:30:44] ⚡ MODULE: drone @cortex create         │
│ [15:30:45] 📁 FILE: cortex/README.md ✏️            │
│ [15:30:45] 📝 LOG: cortex_create.log: Creating... │
│ [15:30:47] ⚠️  WARNING: Flow deleted plan file     │
└─────────────────────────────────────────────────────┘
```

**Option C: Split Screen (Side by Side)**
```
┌──────────────────────┬─────────────────────────────┐
│ 📁 FILES             │ 📝 LOGS                    │
│                      │                             │
│ [15:30:42]           │ [15:30:42]                  │
│ seed/ops.py ✏️       │ seed_audit: Check started   │
│                      │                             │
│ [15:30:45]           │ [15:30:45]                  │
│ cortex/README.md ✏️  │ cortex_create: Building...  │
├──────────────────────┴─────────────────────────────┤
│ ⚡ MODULES RUNNING                                 │
│ drone @seed audit (PID 12345) - 5s ago            │
│ drone @cortex create (PID 12346) - 1s ago         │
└─────────────────────────────────────────────────────┘
```

**DECISION:** Start with Option A (stacked sections) - easier to implement, clear separation

---

### Q5: Module Execution Tracking

**How to track what commands are running?**

**Option A: Hook into Drone**
- Drone logs every command invocation
- PRAX reads drone logs
- ✅ Centralized tracking
- ❌ Requires coordination with Drone

**Option B: Process Monitoring**
- Monitor system processes (ps, top)
- Detect python3 processes running AIPass modules
- ✅ Independent system
- ❌ Less accurate

**Option C: Log File Analysis**
- Parse system logs for module start/stop
- ✅ Uses existing infrastructure
- ❌ Delayed, not real-time

**DECISION:** Option C for v1 (simplest), Option A for v2 (better)

---

### Q6: Color Coding & Priorities

**Event Types:**
```
FILE CREATED:   🟢 Green  (normal operation)
FILE MODIFIED:  🟡 Yellow (activity)
FILE DELETED:   🔴 Red    (warning - verify intentional)
FILE MOVED:     🔵 Blue   (structural change)

LOG INFO:       ⚪ White  (routine)
LOG WARNING:    🟡 Yellow (attention needed)
LOG ERROR:      🔴 Red    (problem)

MODULE START:   🟢 Green  (command launched)
MODULE ACTIVE:  🟡 Yellow (running)
MODULE FAILED:  🔴 Red    (error)
```

---

### Q7: Scope Control

**What branches to monitor?**

**Option A: All Branches (Default)**
```bash
drone prax monitor
drone prax monitor all
```
- Watches everything
- Uses ignore patterns to filter noise

**Option B: Specific Branches**
```bash
drone prax monitor --branches seed,cli,flow
drone prax monitor -b seed
```
- Reduces file count
- Good for focused development

**Option C: Current Directory Only**
```bash
drone prax monitor --here
```
- Watches only current working directory
- Useful for single-branch work

**DECISION:** Support all three options

---

## Architecture Design

### Component Structure

```
prax/
├── apps/
│   ├── modules/
│   │   ├── monitor.py                    # NEW: Unified monitoring module
│   │   ├── branch_watcher.py             # KEEP: File watching (refactored)
│   │   ├── run_module.py                 # KEEP: Log watching
│   │   └── logger.py                     # EXISTING: Logging service
│   │
│   └── handlers/
│       ├── monitoring/                    # NEW: Monitoring infrastructure
│       │   ├── file_watcher.py           # File change detection
│       │   ├── log_watcher.py            # Log output monitoring
│       │   ├── module_tracker.py         # Module execution tracking
│       │   ├── display.py                # Terminal UI rendering
│       │   └── filters.py                # Ignore pattern system
│       │
│       ├── config/
│       │   ├── ignore_patterns.py        # EXISTING: Logger ignores
│       │   └── monitoring_ignore.py      # NEW: Watcher ignores
│       │
│       └── watcher/                       # EXISTING: File monitoring
│           ├── monitor.py                # REFACTOR: Use new filters
│           └── reporter.py               # REFACTOR: New display format
```

### Command Structure

**New unified command:**
```bash
drone prax monitor [mode] [options]

MODES:
  files         # File changes only
  logs          # Log output only
  modules       # Module execution only
  all           # Everything (default)

OPTIONS:
  --branches    # Specific branches to watch
  --here        # Current directory only
  --filter      # Custom filter pattern
  --no-color    # Disable color coding
  --format      # Output format (stacked, stream, split)
```

**Backward compatibility:**
```bash
drone prax branch-watcher start    # Still works, maps to: monitor files
drone prax run                     # Still works, maps to: monitor logs
```

---

## Ignore Pattern Strategy

### Unified Ignore Configuration

**File:** `apps/handlers/config/monitoring_ignore.py`

```python
# Base ignore patterns (from git + monitoring-specific)
IGNORE_PATTERNS = {
    # Directories
    'directories': [
        '.git', '.venv', '__pycache__', 'node_modules',
        '.cache', '.local', '.config', '.ssh',
        '.pytest_cache', '.mypy_cache',
        '.vscode', '.idea', '.eclipse', '.vs',
        '.backup', '.archive', 'backups', 'Archive',
        'Backups', 'External_Code_Sources',
        'Desktop', 'Downloads', 'Music', 'Pictures', 'Videos',
        'crash-logs', 'dropbox',

        # Claude-specific (from .claude/.gitignore)
        '.claude/file-history',
        '.claude/debug',
        '.claude/ide',
        '.claude/plugins',
        '.claude/projects',
        '.claude/session-env',
        '.claude/shell-snapshots',
        '.claude/statsig',
        '.claude/todos',
    ],

    # File patterns
    'extensions': [
        '*.pyc', '*.pyo', '*.so', '*.dylib', '*.dll',
        '*.swp', '*.swo', '*.swn',  # Vim swap
        '*.backup', '*.bak', '*~',  # Backups
        '*.tmp', '*.temp',          # Temp files
        '*.img', '*.iso', '*.vmdk', # Large binaries
    ],

    # Specific files
    'files': [
        '.bash_history', '.python_history',
        '.wget-hsts', '.lesshst',
        'sandbox.img',
        '.claude/.credentials.json',
        '.claude/history.jsonl',
    ],

    # JSON exceptions (ignore these JSON files)
    'json_ignore': [
        '*_data.json',
        '*_log.json',
        '*_registry.json',  # Too large, frequently updated
        'ai_mail.local/**/*.json',  # Email storage
    ],
}

# Watch exceptions (even if in ignore list above)
WATCH_EXCEPTIONS = [
    # Configuration files we DO want to watch
    'BRANCH_REGISTRY.json',
    '*_config.json',
    '*_id.json',
    '*_observations.json',
    '*_local.json',
    'CLAUDE.md',
    'README.md',
    'requirements.txt',
    'pyrightconfig.json',
]
```

**Implementation:**
- Start with these patterns
- User refines through trial and error
- Log what's being ignored (verbose mode)
- Easy to adjust per user preference

---

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Goal:** Get smart filtering working

1. Create `monitoring_ignore.py` with patterns above
2. Refactor `handlers/watcher/monitor.py` to use new filters
3. Test file count reduction (should be <1000 files)
4. Verify inotify limit not hit
5. Log what's being watched vs ignored (verbose mode)

**Success Criteria:**
- branch-watcher runs without inotify errors
- File count significantly reduced
- Can watch all 18 branches simultaneously

---

### Phase 2: Unified Display (Week 2)

**Goal:** Get files + logs in one view

1. Create `handlers/monitoring/display.py` - terminal UI
2. Create `handlers/monitoring/file_watcher.py` - wrapper around existing watcher
3. Create `handlers/monitoring/log_watcher.py` - wrapper around run module
4. Create `apps/modules/monitor.py` - unified entry point
5. Implement stacked section layout (Option A)
6. Add color coding for events

**Success Criteria:**
- `drone prax monitor` shows files and logs together
- Color-coded output (green/yellow/red)
- Scrolling works correctly
- Ctrl+C shuts down cleanly

---

### Phase 3: Module Tracking (Week 3)

**Goal:** Add module execution visibility

1. Create `handlers/monitoring/module_tracker.py`
2. Parse system logs for module start/stop
3. Display active modules in bottom section
4. Show PID, command, duration

**Success Criteria:**
- See what modules are running
- See when they started
- See when they complete/fail

---

### Phase 4: Polish & Options (Week 4)

**Goal:** Add configuration options

1. Add `--branches` filter
2. Add `--here` current directory mode
3. Add `--format` for different layouts
4. Add `--no-color` option
5. Create comprehensive help documentation
6. Performance optimization

**Success Criteria:**
- All command options working
- Help documentation complete
- Fast, responsive UI
- Low CPU usage

---

## Testing Strategy

### Unit Tests
- Filter pattern matching
- Ignore pattern logic
- Display rendering
- Color code selection

### Integration Tests
- File watcher + ignore patterns
- Log watcher + output formatting
- Module tracker + log parsing

### System Tests
- Monitor all 18 branches
- High file change volume
- Long-running (24+ hours)
- Multiple terminals simultaneously

### User Acceptance
- Patrick uses daily for 1 week
- Refinement of ignore patterns
- UI/UX feedback
- Performance validation

---

## Open Questions for User

### Q1: Logs Directory
**Question:** Should we watch the `logs/` and `system_logs/` directories for file changes, or only monitor their content through log output?

**Context:**
- Git ignores logs/
- But we want to see log output
- File watcher could show "new log file created"
- Log watcher shows actual log content

**Options:**
- A) Watch logs/ for file creation/deletion (know when new logs appear)
- B) Don't watch logs/ (only read content, not track files)
- C) Watch but with reduced frequency (polling instead of inotify)

---

### Q2: JSON Files Granularity
**Question:** Which JSON files matter to you in real-time?

**Current thought:**
- Watch: *_config.json, *_id.json, BRANCH_REGISTRY.json
- Ignore: *_data.json, *_log.json, *_registry.json

**Is this correct, or should we refine further?**

---

### Q3: Display Format Preference
**Question:** Which layout do you prefer?

- A) Stacked sections (files / logs / modules)
- B) Unified stream (all events mixed chronologically)
- C) Split screen (files+logs side-by-side, modules below)

**Or should we support all three with --format option?**

---

### Q4: Verbosity
**Question:** How much detail do you want?

**Low verbosity:**
```
[15:30:42] seed/ops.py modified
[15:30:45] cortex/README.md modified
```

**High verbosity:**
```
[15:30:42] FILE MODIFIED: /home/aipass/aipass_core/seed/apps/handlers/json/ops.py
           Size: 15.2 KB → 15.4 KB
           Reason: Standards compliance update
[15:30:45] FILE MODIFIED: /home/aipass/aipass_core/cortex/README.md
           Size: 3.1 KB → 3.3 KB
           Lines changed: +12
```

**Preference?**

---

### Q5: Performance vs Features
**Question:** Priority ranking?

**Fast and simple:**
- Basic file watching
- Simple log tailing
- Minimal overhead
- Text-only output

**Feature-rich:**
- Real-time updates
- Color-coded priorities
- Module execution tracking
- Rich terminal UI
- Filtering options
- Multiple display modes

**Where on this spectrum?**

---

## Updated Vision (Post-Discussion)

### The Real Use Case: Mission Control for Autonomous Branches

**Scenario:**
- 10+ Claude instances running via `claude -P` in background
- Can't see their chats, only results
- Need real-time visibility into what they're doing
- Future: Email-triggered autonomous work

**The Terminal Experience:**
```
PRAX Monitoring System
Branches: 18 available (3 active: SEED, CLI, CORTEX)
Type 'help' for commands

> watch seed                    # Start monitoring seed
[SEED] ⚡ CMD: drone seed audit
[SEED] 📁 FILE: handlers/json/ops.py MODIFIED
[SEED] 📝 LOG: INFO | Running standards check...
> watch cortex                  # Switch focus
[CORTEX] 📝 LOG: ERROR | Import violation detected
[CORTEX] 📁 FILE: apps/cortex.py MODIFIED
> verbosity high               # More detail
```

### Command Language (Finalized)

**WATCH** = Exclusive focus
- `watch seed` - Only show seed
- `watch seed cortex` - Only show seed + cortex
- `watch errors` - Only show errors

**MONITOR** = Inclusive addition
- `monitor errors` - Add errors to current view
- `monitor warnings` - Add warnings

**Control Commands:**
- `verbosity high/low` - Detail level
- `clear filters` - Show everything
- `status` - Show active filters
- `help` - Available commands

### Soft Start Strategy

**Default Startup:**
```
PRAX Monitoring System
Branches: 18 available
Active: SEED (drone @seed audit), CLI (idle), CORTEX (drone @cortex create)

Default: Quiet mode (no output)
Type 'watch <branch>' to begin monitoring
Type 'watch all' to see everything

> _
```

User chooses what to watch, avoiding initial flood of data.

---

## Implementation Approach: Duct Tape & Iteration

### Philosophy
- **Build fast, test fast**
- **Prove concepts, don't perfect them**
- **Expect crashes (that's fine!)**
- **Use existing modules (branch_watcher, run_module)**
- **Creative freedom to experiment**

### Phase 1: Basic Unified Stream (Immediate)

**Goal:** One terminal, everything streaming

```python
# Combine existing:
# - branch_watcher (file changes)
# - run_module (log output)
# - Add branch detection
# - Format: [BRANCH] TYPE: message
```

**Test:** 2-3 branches doing work, see if stream works

### Phase 2: Interactive Commands (Next)

**Two approaches to test:**

**Option A: Interactive Terminal**
- Type commands while stream runs
- Threading: monitor thread + input thread
- Challenge: Terminal control while scrolling

**Option B: Control Terminal**
- Terminal 1: Control CLI
- Terminal 2: Monitor output
- Easier to implement
- Multiple windows workflow

**We'll try both and see what feels better!**

### Phase 3: Smart Filtering (Later)

- Ignore patterns from .gitignore
- Handle 50+ branches
- Soft start modes
- Status tracking

### Phase 4: Polish (Eventually)

- Rich UI (if needed)
- Command history
- Performance optimization
- Error recovery

---

## Key Decisions Made

1. **Start quiet** - User chooses what to watch
2. **Branch attribution** - Every event shows [BRANCH]
3. **Unified stream** - Files + Logs + Modules chronologically
4. **Interactive filtering** - Commands while running
5. **Build iteratively** - Duct tape first, polish later

## Open Experiments

1. **Interactive vs Control Terminal** - Try both
2. **Threading vs Async** - Whatever works
3. **Rich vs Plain Text** - Start plain, add fancy later
4. **inotify vs Polling** - Start with what we have

---

## Next Actions

1. ✅ Update design document (this update)
2. ✅ Update PRAX memories
3. 🚀 Start Phase 1: Build basic unified stream
4. Test with real branches working
5. Show Patrick for feedback
6. Iterate based on usage

---

## Success Metrics (Updated)

**Minimum Viable:**
1. Shows files + logs in one terminal
2. Shows which branch did what
3. Can filter to specific branches
4. Handles 10+ branches working

**Nice to Have:**
1. Interactive commands while running
2. Color coding
3. Verbosity control
4. 24+ hour stability

**Future Vision:**
1. Email-triggered monitoring
2. 50+ branches
3. Automated alerts
4. System health dashboard

---

**Document Status:** Design Complete - Ready to Build
**Approach:** Experimental, Iterative
**Next Step:** Build Phase 1 Basic Stream
**Owner:** PRAX Branch
