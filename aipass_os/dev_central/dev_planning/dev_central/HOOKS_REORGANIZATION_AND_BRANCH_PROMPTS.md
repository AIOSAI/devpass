# Hooks Reorganization & Branch-Specific Prompts Plan
**Date:** 2025-11-27
**Owner:** @aipass
**Status:** COMPLETE

---

## Overview

Two related initiatives:
1. **Hooks Reorganization** - Clean up messy hooks directory and settings.json
2. **Branch-Specific Prompts** - Add per-branch system prompts that fire only in that branch

---

## Part 1: Hooks Reorganization

### Current State (Messy)

**settings.json issues:**
- 200+ permission entries (many one-off bash commands)
- No organization or grouping
- Hard to maintain

**hooks/ directory:**
- 13 Python files mixed together
- 7 active, 6 inactive (no clear distinction)
- No documentation of what's active/why

### Current Active Hooks

| Hook Type | File | Purpose |
|-----------|------|---------|
| UserPromptSubmit | system_prompt.md | Injects system-wide prompt info |
| PostToolUse | auto_fix_diagnostics.py | Runs linters after edits |
| PostToolUse | pre_code_standards_reminder.py | Standards reminder after Python edits |
| PreToolUse | tool_use_sound.py | ATM sound on tool use |
| PreToolUse | claude-docs-helper.sh | Auto-updates Claude docs |
| Stop | stop_sound.py | Achievement bell on completion |
| Notification | notification_sound.py | Alert sound for permissions |
| PreCompact | pre_compact.py | Preserves context before compaction |

### Inactive Hooks (in directory but not settings.json)

| File | Purpose | Action Needed |
|------|---------|---------------|
| smart_diagnostics_batch.py | Batching optimization | May be merged into auto_fix |
| post-tool-use-logger.py | External JSON logging | Keep for debugging opt-in |
| agent-output-formatter.py | ANSI in-place updates | Evaluate usefulness |
| subagent-output-limiter.py | Output truncation | Evaluate usefulness |
| updateall_hook.py | Updates AIPASS.local.json | May be deprecated |
| user_prompt_submit_hook.py | Command intercept | Replaced by system_prompt.md |

### Proposed Directory Structure

```
/home/aipass/.claude/hooks/
├── README.md                    # Documentation
├── active/
│   ├── feedback/               # User feedback (sounds)
│   │   ├── tool_use_sound.py
│   │   ├── stop_sound.py
│   │   └── notification_sound.py
│   ├── quality/                # Code quality
│   │   ├── auto_fix_diagnostics.py
│   │   └── pre_code_standards_reminder.py
│   ├── context/                # Context management
│   │   ├── pre_compact.py
│   │   └── branch_prompt_loader.py  # NEW
│   └── system/
│       └── (external hooks referenced by path)
├── inactive/
│   ├── smart_diagnostics_batch.py
│   ├── post-tool-use-logger.py
│   ├── agent-output-formatter.py
│   ├── subagent-output-limiter.py
│   └── deprecated/
│       ├── updateall_hook.py
│       └── user_prompt_submit_hook.py
├── utils/
│   └── view-logs.sh
└── sounds/
    └── *.wav
```

### settings.json Cleanup

**Permissions:**
- Group by category (git, python, drone, etc.)
- Remove one-off commands that accumulated
- Add comments explaining groups

**Hooks:**
- Update paths to new organized structure
- Add comments documenting each hook

---

## Part 2: Branch-Specific Prompts

### Concept

Each branch can have a `.branch_prompt.md` file that gets injected into system prompt ONLY when working in that branch directory.

### Benefits

- Branch-specific reminders without cluttering global prompt
- Each branch owns their context (same pattern as memory files)
- Small focused prompts (50-100 tokens each)
- Complements global prompt, doesn't replace

### Implementation

**New hook:** `branch_prompt_loader.py`

```python
#!/usr/bin/env python3
"""
Branch Prompt Loader - Injects branch-specific prompts based on CWD
"""
import os
import json
from pathlib import Path

def main():
    cwd = Path.cwd()

    # Check for branch prompt in current directory
    branch_prompt = cwd / ".branch_prompt.md"

    # Also check parent directories up to /home/aipass
    search_path = cwd
    while search_path != Path.home() and search_path != Path("/"):
        candidate = search_path / ".branch_prompt.md"
        if candidate.exists():
            branch_prompt = candidate
            break
        search_path = search_path.parent

    if branch_prompt.exists():
        content = branch_prompt.read_text().strip()
        result = {
            "result": "success",
            "systemMessage": f"[Branch: {branch_prompt.parent.name}]",
            "additionalContext": f"\n# Branch-Specific Context\n{content}\n"
        }
    else:
        result = {"result": "success"}

    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

**Hook registration (settings.json):**
```json
{
  "UserPromptSubmit": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "cat /home/aipass/.aipass/system_prompt.md"
        },
        {
          "type": "command",
          "command": "python3 /home/aipass/.claude/hooks/active/context/branch_prompt_loader.py"
        }
      ]
    }
  ]
}
```

### Example Branch Prompts

**SEED:** `/home/aipass/seed/.branch_prompt.md`
```markdown
# SEED Branch Context

You are working in SEED - the Code Standards Showroom.

Key reminders:
- SEED is the reference implementation - code here should be exemplary
- 10 standards available: architecture, cli, imports, naming, json_structure, error_handling, documentation, handlers, modules, testing
- Checkers are in apps/handlers/standards/
- Standards content is in apps/handlers/standards/*_content.py
- Run `python3 apps/seed.py checklist <file>` to test changes
```

**PRAX:** `/home/aipass/aipass_core/prax/.branch_prompt.md`
```markdown
# PRAX Branch Context

You are working in PRAX - the System-Wide Logging Infrastructure.

Key reminders:
- PRAX is a foundational service - other branches import from it
- logger.py CANNOT import CLI (circular dependency documented Session 4)
- print() in bootstrap functions is intentional (not a bug)
- 261 modules discovered across ecosystem
- Branch watcher monitors file changes
```

**MEMORY_BANK:** `/home/aipass/MEMORY_BANK/.branch_prompt.md`
```markdown
# MEMORY_BANK Branch Context

You are working in MEMORY_BANK - Central Memory Archive System.

Key reminders:
- Uses ChromaDB + sentence-transformers for vector search
- Entry point is apps/memory_bank.py (lowercase)
- Uses dedicated .venv with Python 3.12
- Dual storage: local (branch) + global (MEMORY_BANK)
- Run with: .venv/bin/python apps/memory_bank.py
```

---

## Implementation Steps

### Phase 1: Hooks Reorganization - COMPLETE

1. [x] ~~Create new directory structure in hooks/~~ (Simplified: kept flat structure)
2. [x] ~~Move active hooks to categorized folders~~ (Active hooks stay in place)
3. [x] Move inactive hooks to `.archive/inactive/`
4. [x] ~~Update settings.json paths~~ (No path changes needed)
5. [x] Test all hooks still work (9 active hooks verified)
6. [x] Create README.md documentation
7. [x] Clean up permissions list in settings.json (200+ removed, kept deny list only)

**Actual Implementation (Simpler than planned):**
- Kept active hooks in flat structure (no subdirectories)
- Archived 6 inactive hooks to `/home/aipass/.claude/hooks/.archive/inactive/`
- Cleaned settings.json: removed all accumulated permissions, kept only deny list for dangerous git commands
- Created comprehensive README.md documenting all hooks

### Phase 2: Branch Prompts - COMPLETE

1. [x] Create branch_prompt_loader.py (v2.0 with auto-creation)
2. [x] Add to UserPromptSubmit hooks
3. [x] Test with SEED branch prompt (working)
4. [x] Auto-creation of `.aipass/branch_system_prompt.md` for all branches
5. [x] Document pattern in `/home/aipass/.claude/hooks/README.md`

**v2.0 Evolution:**
- Changed from `.branch_prompt.md` to `.aipass/branch_system_prompt.md`
- Auto-creates `.aipass/` directory and placeholder on first visit
- Placeholder includes template and "NEEDS CONFIGURATION" status
- Branches customize at their own pace - no manual setup needed

---

## Files Created/Modified

**Created:**
- [x] `/home/aipass/.claude/hooks/README.md` - Hook documentation
- [x] `/home/aipass/.claude/hooks/branch_prompt_loader.py` - Branch prompt injection (v2.0)
- [x] `/home/aipass/seed/.aipass/branch_system_prompt.md` - SEED (customized)
- [x] Auto-created on first visit: Any branch gets `.aipass/branch_system_prompt.md`

**Modified:**
- [x] `/home/aipass/.claude/settings.json` - Cleaned permissions, added branch_prompt_loader hook

**Archived to `.archive/inactive/`:**
- agent-output-formatter.py
- post-tool-use-logger.py
- smart_diagnostics_batch.py
- subagent-output-limiter.py
- updateall_hook.py
- user_prompt_submit_hook.py

---

## Rollback Plan

If issues occur:
1. Keep backup of original settings.json
2. Original hooks still exist (just moved)
3. Can revert paths in settings.json to restore

---

## Success Criteria

- [x] All active hooks still functioning (9 hooks verified)
- [x] Directory structure is organized and documented (README.md created)
- [x] Branch prompts fire only in their respective branches (tested with SEED)
- [x] Global prompt still works alongside branch prompts (confirmed)
- [x] No increase in startup latency (branch prompt check is fast)

---

## Current Active Hooks (Post-Cleanup)

| Hook Type | File | Purpose |
|-----------|------|---------|
| UserPromptSubmit | system_prompt.md | Global system prompt |
| UserPromptSubmit | branch_prompt_loader.py | Branch-specific context |
| PostToolUse | auto_fix_diagnostics.py | Linters after edits |
| PostToolUse | pre_code_standards_reminder.py | Standards reminder |
| PreToolUse | tool_use_sound.py | ATM click sound |
| PreToolUse | claude-docs-helper.sh | Auto-updates Claude docs |
| Stop | stop_sound.py | Achievement bell |
| Notification | notification_sound.py | Permission alert |
| PreCompact | pre_compact.py | Context preservation |

---

## No Remaining Work

All tasks complete. The system is now self-sustaining:
- Hook auto-creates `.aipass/branch_system_prompt.md` on first visit to any branch
- Placeholder tells branch "NEEDS CONFIGURATION" with template
- Branches customize at their own pace
- No manual setup required

---

*Plan created: 2025-11-27*
*Phase 1 completed: 2025-11-27*
*Phase 2 completed: 2025-11-27*
