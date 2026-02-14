# Claude Code Hooks

Documentation for AIPass Claude Code hooks.

## Active Hooks

| Hook Type | File | Purpose |
|-----------|------|---------|
| UserPromptSubmit | `system_prompt.md` (via cat) | Global system prompt injection |
| UserPromptSubmit | `branch_prompt_loader.py` | Branch-specific context injection |
| UserPromptSubmit | `identity_injector.py` | Branch identity (role, traits, principles) |
| UserPromptSubmit | `email_notification.py` | Inbox status on each prompt |
| UserPromptSubmit | `fragmented_memory.py` | Fragmented memory recall |
| PostToolUse | `auto_fix_diagnostics.py` | Linters + Seed checklist after Edit/Write |
| PreToolUse | `tool_use_sound.py` | ATM click sound on tool use |
| PreToolUse | `claude-docs-helper.sh` | Auto-updates Claude docs (on Read) |
| Stop | `stop_sound.py` | Achievement bell on completion |
| Notification | `notification_sound.py` | Alert for permission prompts |
| PreCompact | `pre_compact.py` | Preserves context before compaction |

---

## Branch System Prompts

### How It Works

The `branch_prompt_loader.py` hook automatically:
1. Detects which branch you're working in (by finding `apps/` directory or `*.local.json`)
2. Creates `.aipass/branch_system_prompt.md` if it doesn't exist
3. Injects the content into every conversation

### Location

Each branch gets: `<branch_root>/.aipass/branch_system_prompt.md`

### Where It Doesn't Run

- At `/home/aipass` root (no branch-level injection there)
- In directories without `apps/` or `*.local.json`

---

## Archived Hooks

Inactive hooks in `.archive/`:
- `seed_standards_injector.py` - Seed standards injection before file creation (replaced by agent-first workflow)
- `pre_code_standards_reminder.py(disabled)` - Standards reminder after Python edits
- `pre_code_standards_reminder.py.backup` - Backup of above
- `auto_fix_diagnostics.py.backup` - Backup of diagnostics hook
- `agent-output-formatter.py`
- `post-tool-use-logger.py`
- `smart_diagnostics_batch.py`
- `subagent-output-limiter.py`
- `updateall_hook.py`
- `user_prompt_submit_hook.py`
- `SEED_INTEGRATION_SUMMARY.md`
- `TESTING_SEED_INTEGRATION.md`

---

*Last updated: 2026-02-07*
