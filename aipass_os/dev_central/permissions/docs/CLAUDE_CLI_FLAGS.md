# Claude CLI Flags Reference

*Generated: 2025-11-24*

---

## Permission & Security Flags

| Flag | Description |
|------|-------------|
| `--permission-mode <mode>` | Permission mode for session |
| `--dangerously-skip-permissions` | Bypass ALL permission checks (sandbox only) |
| `--allow-dangerously-skip-permissions` | Enable bypass option without default |
| `--allowedTools <tools...>` | Whitelist tools (e.g. "Bash(git:*) Edit") |
| `--disallowedTools <tools...>` | Blacklist tools |
| `--tools <tools...>` | Specify available tools ("" = none, "default" = all) |

### Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Interactive prompts for all permissions |
| `acceptEdits` | Auto-accept file edits, prompt for others |
| `bypassPermissions` | No permission checks (full autonomy) |
| `dontAsk` | Don't ask, may skip actions |
| `plan` | Planning mode only |

---

## Output Flags

| Flag | Description |
|------|-------------|
| `-p, --print` | Print response and exit (non-interactive) |
| `--output-format <format>` | Output: "text", "json", "stream-json" |
| `--input-format <format>` | Input: "text", "stream-json" |
| `--json-schema <schema>` | JSON Schema for structured output |
| `--include-partial-messages` | Stream partial chunks (with stream-json) |
| `--replay-user-messages` | Re-emit user messages on stdout |

---

## Session Flags

| Flag | Description |
|------|-------------|
| `-c, --continue` | Continue most recent conversation |
| `-r, --resume [id]` | Resume specific session |
| `--fork-session` | Create new session ID when resuming |
| `--session-id <uuid>` | Use specific session ID |
| `--model <model>` | Set model ("sonnet", "opus", or full name) |
| `--fallback-model <model>` | Fallback when primary overloaded |

---

## Configuration Flags

| Flag | Description |
|------|-------------|
| `--system-prompt <prompt>` | Custom system prompt |
| `--append-system-prompt <prompt>` | Append to default system prompt |
| `--settings <file-or-json>` | Load settings from file/JSON |
| `--setting-sources <sources>` | Sources: user, project, local |
| `--add-dir <dirs...>` | Allow tool access to additional dirs |
| `--mcp-config <configs...>` | Load MCP servers from JSON |
| `--strict-mcp-config` | Only use MCP from --mcp-config |
| `--agents <json>` | Define custom agents |
| `--plugin-dir <paths...>` | Load plugins from directories |

---

## Debug Flags

| Flag | Description |
|------|-------------|
| `-d, --debug [filter]` | Debug mode (e.g. "api,hooks") |
| `--verbose` | Override verbose mode |
| `--mcp-debug` | [DEPRECATED] Use --debug |
| `--ide` | Auto-connect to IDE on startup |

---

## Commands

| Command | Description |
|---------|-------------|
| `mcp` | Configure MCP servers |
| `plugin` | Manage plugins |
| `doctor` | Check auto-updater health |
| `update` | Check/install updates |
| `install [target]` | Install native build |
| `setup-token` | Set up auth token |
| `migrate-installer` | Migrate from npm to local |

---

## Common Usage Patterns

### Autonomous Branch Work
```bash
claude -p "PROMPT" --permission-mode bypassPermissions 
```

### Custom System Prompt
```bash
claude -p "task" --system-prompt "You are branch X at path Y"
```

### Restrict Tools
```bash
claude -p "task" --tools "Read,Grep,Glob" --permission-mode bypassPermissions
```

### JSON Output
```bash
claude -p "task" --output-format json --json-schema '{"type":"object"}'
```

### Continue Session
```bash
claude --continue
claude --resume abc123
```

---
## Patrick list.
```bash
claude --permission-mode bypassPermissions  (starting a claude session) 
```

*Reference: `claude --help` (Claude Code CLI)*
