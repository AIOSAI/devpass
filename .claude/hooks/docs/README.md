# Claude Code Hooks

**Location:** `/home/aipass/.claude/hooks/`
**Last Updated:** 2025-11-27

## Active Hooks

| File | Hook Type | Matcher | Purpose |
|------|-----------|---------|---------|
| `auto_fix_diagnostics.py` | PostToolUse | Edit\|Write | Runs linters after edits, silent auto-fix |
| `pre_code_standards_reminder.py` | PostToolUse | Write\|Edit | Standards reminder after Python edits |
| `tool_use_sound.py` | PreToolUse | Bash\|Edit\|Write\|Read | ATM sound feedback on tool use |
| `notification_sound.py` | Notification | - | Alert sound for permission requests |
| `stop_sound.py` | Stop | - | Achievement bell on completion |
| `pre_compact.py` | PreCompact | manual\|auto | Preserves context before compaction |
| `branch_prompt_loader.py` | UserPromptSubmit | - | Loads branch-specific prompts |

## External Hooks

| Location | Hook Type | Purpose |
|----------|-----------|---------|
| `~/.aipass/system_prompt.md` | UserPromptSubmit | Global system prompt |
| `~/.claude-code-docs/claude-docs-helper.sh` | PreToolUse (Read) | Auto-updates Claude docs |

## Archived Hooks

Inactive hooks preserved in `.archive/inactive/`:
- `agent-output-formatter.py` - ANSI in-place updates
- `post-tool-use-logger.py` - External JSON logging
- `smart_diagnostics_batch.py` - Batching optimization
- `subagent-output-limiter.py` - Output truncation
- `updateall_hook.py` - AIPASS.local.json updates
- `user_prompt_submit_hook.py` - Command intercept (replaced by system_prompt.md)

## Branch-Specific Prompts

Branches can add `.branch_prompt.md` to their root directory. The `branch_prompt_loader.py` hook will:
1. Check CWD and parent directories for `.branch_prompt.md`
2. If found, inject content via `additionalContext`
3. Claude sees branch-specific reminders when working in that branch

Example: `/home/aipass/seed/.branch_prompt.md`
```markdown
# SEED Branch Context

You are working in SEED - the Code Standards Showroom.
- 10 standards available
- Checkers in apps/handlers/standards/
- Run `python3 apps/seed.py checklist <file>` to test
```

## Sound Files

Located in `sounds/`:
- `mixkit-achievement-bell-600.wav` - Stop hook
- `mixkit-atm-cash-machine-key-press-2841.wav` - Tool use
- `mixkit-clear-announce-tones-2861.wav` - Notification

## Configuration

Hooks are registered in `~/.claude/settings.json` under the `hooks` key.
See [Claude Code docs](https://docs.anthropic.com/en/docs/claude-code/hooks) for hook types.
