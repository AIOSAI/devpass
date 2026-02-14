# Claude Code Terminal Jumping Fix

## Problem Statement

Claude Code terminal jumping and scrolling is caused by excessive output being displayed directly in the terminal. When Claude Code or its subagents produce large amounts of output (file contents, command results, search results, etc.), the terminal buffer overflows, causing:

- Rapid terminal scrolling
- Screen jumping
- Difficulty reading responses
- Terminal instability
- Poor user experience

## Solution Overview

The fix uses **output suppression + external logging** to prevent terminal overflow while maintaining complete transparency. This is a production-tested, universal solution.

## Architecture

### Three-Component System

1. **Output Suppression Hooks** - Intercept and truncate large outputs
2. **External Logging System** - Log everything to files instead of terminal
3. **Minimal Status Display** - Show only essential updates in terminal

## Implementation

### Files Created

```
~/.claude/hooks/
├── subagent-output-limiter.py    # Truncates subagent outputs
├── agent-output-formatter.py      # Minimal status updates
├── post-tool-use-logger.py        # Silent external logging
└── view-logs.sh                   # Log viewer utility

~/.claude/logs/hooks/
├── hook-execution.log             # Detailed execution log
├── current-session.log            # Session summary
├── command_history.log            # Bash commands only
├── post_tool_use.json             # Structured JSON logs
└── truncation.log                 # Truncation events
```

### Hook Configuration

**settings.json** (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/aipass/.claude/hooks/subagent-output-limiter.py"
          }
        ]
      },
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/aipass/.claude/hooks/post-tool-use-logger.py"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/aipass/.claude/hooks/agent-output-formatter.py"
          }
        ]
      }
    ]
  }
}
```

## Component Details

### 1. Subagent Output Limiter

**Purpose:** Truncates large subagent outputs to prevent terminal overflow

**Configuration:**
- Max lines: 500
- Max characters: 100,000
- Logs truncations to: `truncation.log`

**Behavior:**
- Only processes `Task` (subagent) tool results
- Truncates output if it exceeds limits
- Shows summary: original size vs truncated size
- Directs users to logs for full output

### 2. Agent Output Formatter

**Purpose:** Shows minimal, in-place status updates for agent execution

**Features:**
- Single-line status updates
- ANSI escape codes for in-place updates (no scrolling)
- Color-coded status indicators
- Timestamps

**Example Output:**
```
[10:59:23] ● Task - Exploring codebase structure
```

### 3. Post-Tool-Use Logger

**Purpose:** Silently logs all tool executions to external files

**Logs Created:**
- `hook-execution.log` - Full execution details (human-readable)
- `post_tool_use.json` - Structured JSON logs
- `command_history.log` - Bash commands only
- `current-session.log` - Session summary

**Features:**
- Auto-rotating logs (10MB max per file, keeps last 5)
- Silent operation (minimal terminal feedback)
- Complete audit trail
- Never breaks Claude Code (fails silently)

### 4. Log Viewer Script

**Usage:**

```bash
# Show recent activity
~/.claude/hooks/view-logs.sh

# Show last N full executions
~/.claude/hooks/view-logs.sh last 10

# Search for specific commands
~/.claude/hooks/view-logs.sh search "git"

# Show statistics
~/.claude/hooks/view-logs.sh stats

# Follow logs in real-time
~/.claude/hooks/view-logs.sh follow

# Clear all logs
~/.claude/hooks/view-logs.sh clear
```

## Benefits

✅ **Clean Terminal** - No more jumping or scrolling
✅ **Full Transparency** - Everything logged externally
✅ **Better Performance** - Reduced terminal rendering overhead
✅ **Audit Trail** - Complete command and output history
✅ **Universal** - Works for all users and environments
✅ **Scalable** - Handles large outputs without crashes

## Environment Requirements

### ✅ Recommended Environments

- bash (recommended for maximum compatibility)
- zsh
- Native terminal emulators (Terminal.app, Alacritty, kitty, etc.)

### ❌ Do NOT Use

- tmux
- GNU screen
- byobu
- Any terminal multiplexer

**Reason:** Terminal multiplexers add additional buffering and escape sequence handling that interferes with Claude Code's output control and hook execution.

## Configuration Details

### Output Limits

```python
# subagent-output-limiter.py
MAX_OUTPUT_LINES = 500      # Maximum lines shown in terminal
MAX_OUTPUT_CHARS = 100000   # Maximum characters (100KB)
```

### Log Rotation

```python
# post-tool-use-logger.py
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB per log file
MAX_LOG_FILES = 5                # Keep last 5 rotated logs
```

Adjust these values based on your needs.

## Troubleshooting

### Hooks Not Running

Check if hooks are executable:
```bash
ls -la ~/.claude/hooks/*.py
chmod +x ~/.claude/hooks/*.py
```

### Logs Not Being Created

Verify log directory exists:
```bash
mkdir -p ~/.claude/logs/hooks
```

### Output Still Too Large

Reduce limits in `subagent-output-limiter.py`:
```python
MAX_OUTPUT_LINES = 250      # Reduce from 500
MAX_OUTPUT_CHARS = 50000    # Reduce from 100000
```

### View Hook Errors

Check if hooks are producing errors:
```bash
~/.claude/hooks/view-logs.sh search "error"
```

## Maintenance

### Clear Old Logs

```bash
~/.claude/hooks/view-logs.sh clear
```

### Monitor Log Size

```bash
du -sh ~/.claude/logs/hooks/
```

### View Recent Activity

```bash
~/.claude/hooks/view-logs.sh stats
```

## Implementation Date

**Created:** 2025-11-12
**Author:** SuperClaude (via AIPass system)
**Status:** Active and operational

## Related Files

- Hook implementations: `~/.claude/hooks/`
- Settings: `~/.claude/settings.json`
- Logs: `~/.claude/logs/hooks/`
- Documentation: `/home/aipass/.claude/docs/terminal-jumping-fix.md`

## Notes

- Hooks are stateless and fail silently to prevent breaking Claude Code
- All hooks pass through input unchanged on error
- Logging is asynchronous and non-blocking
- Full backward compatibility with existing hooks maintained
