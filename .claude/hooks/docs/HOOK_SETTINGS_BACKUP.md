# Hook Settings Backup
**Created:** 2025-11-23
**Reason:** Temporarily disabling terminal scrolling hooks to debug VS Code freezing issues

## Original Hook Configuration

This is the full `~/.claude/settings.json` hooks section before disabling:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cat /home/aipass/.aipass/system_prompt.md"
          }
        ]
      }
    ],
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
        "matcher": "Edit|MultiEdit|Write|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/aipass/.claude/hooks/smart_diagnostics_batch.py > /dev/null 2>&1"
          }
        ]
      },
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/aipass/.claude/hooks/auto_fix_diagnostics.py > /dev/null 2>&1"
          },
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
      },
      {
        "matcher": "Bash|Edit|MultiEdit|Write|Read|Grep|Glob",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/aipass/.claude/hooks/tool_use_sound.py"
          }
        ]
      },
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude-code-docs/claude-docs-helper.sh hook-check"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/aipass/.claude/hooks/stop_sound.py"
          }
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/aipass/.claude/hooks/notification_sound.py"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "manual",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/aipass/.claude/hooks/pre_compact.py",
            "timeout": 60
          }
        ]
      },
      {
        "matcher": "auto",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/aipass/.claude/hooks/pre_compact.py",
            "timeout": 60
          }
        ]
      }
    ]
  },
  "statusLine": {
    "type": "command",
    "command": "input=$(cat); user=$(whoami); host=$(hostname -s); cwd=$(echo \"$input\" | jq -r '.workspace.current_dir // .cwd'); dir=$(basename \"$cwd\"); model=$(echo \"$input\" | jq -r '.model.display_name'); branch=$(git -C \"$cwd\" branch --show-current 2>/dev/null || echo ''); git_info=\"\"; [ -n \"$branch\" ] && git_info=\" (git:$branch)\"; printf \"\\033[32m%s@%s\\033[0m | \\033[34m%s\\033[0m%s | \\033[36m%s\\033[0m\" \"$user\" \"$host\" \"$dir\" \"$git_info\" \"$model\""
  },
  "alwaysThinkingEnabled": true
}
```

## Hooks Being Disabled for Testing

These hooks relate to terminal scrolling/output formatting:

1. **agent-output-formatter.py** (PreToolUse → Task)
   - Formats agent output before display

2. **subagent-output-limiter.py** (PostToolUse → Task)
   - Limits subagent output length

3. **post-tool-use-logger.py** (PostToolUse → All)
   - Logs all tool usage

## To Re-enable

Copy the JSON above back into `~/.claude/settings.json` and restart VS Code.
