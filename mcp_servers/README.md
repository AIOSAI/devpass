# MCP_SERVERS Branch

Claude Code infrastructure layer for the AIPass ecosystem.

## Purpose

Manages the configuration layer that shapes how Claude operates across AIPass. Two domains:

1. **Claude Code config** (`/home/aipass/.claude/`) - hooks, settings, commands, plugins
2. **MCP server configs** - `.mcp.json` files and hosted server repositories

Every tool call in every agent across every dispatch passes through infrastructure this branch maintains.

## Claude Code Infrastructure

### Hooks Pipeline

11+ active hook scripts configured in `settings.json`:

| Hook Event | Scripts | Purpose |
|-----------|---------|---------|
| **UserPromptSubmit** | `system_prompt.md` (cat), `branch_prompt_loader.py`, `identity_injector.py`, `email_notification.py`, `fragmented_memory.py` | Context injection on every prompt |
| **PostToolUse** | `auto_fix_diagnostics.py` | Linters + Seed checklist after Edit/Write |
| **PreToolUse** | `tool_use_sound.py`, `claude-docs-helper.sh` | Tool sounds, docs updates |
| **Stop** | `stop_sound.py`, `telegram_response.py` | Completion sounds, Telegram notifications |
| **Notification** | `notification_sound.py` | Permission prompt alerts |
| **PreCompact** | `pre_compact.py` | Context preservation before compaction |

Hook scripts live in `/home/aipass/.claude/hooks/`.

### Settings & Permissions

`/home/aipass/.claude/settings.json` controls:
- Permission mode and deny rules (git reset, rebase, config, pull)
- Environment variables (`CLAUDE_CODE_DISABLE_AUTO_MEMORY`)
- Status line configuration
- Plugin enablement (pyright LSP)

### Commands & Skills

Slash commands in `/home/aipass/.claude/commands/`:
- `/docs` - Claude Code documentation helper
- `/updateall` - Update documentation command

### Plugins

Plugin infrastructure in `/home/aipass/.claude/plugins/`:
- **pyright-lsp** - Active (Python type checking)
- Marketplace infrastructure present for future additions

## MCP Servers

Four servers configured in the global config (`/home/aipass/.mcp.json`):

| Server | Description | Status |
|--------|-------------|--------|
| **Serena** | Project management and code navigation (`--project /home/aipass`) | Active |
| **Context7** | Documentation and library access | Active |
| **Playwright** | Browser automation (global only) | Active |
| **Sequential Thinking** | Step-by-step reasoning | Active |

Reference server sources in `servers/src/`: everything, fetch, filesystem, git, memory, sequentialthinking, time.

### Configuration

- **Global:** `/home/aipass/.mcp.json` - primary config, system-wide
- **Local:** `/home/aipass/mcp_servers/.mcp.json` - branch-specific (3 servers, no Playwright)

## Directory Structure

```
mcp_servers/
├── apps/
│   ├── mcp_servers.py         # Main orchestrator
│   ├── handlers/json/         # JSON handler
│   ├── modules/               # Auto-discovered modules
│   ├── json_templates/        # JSON templates
│   ├── extensions/            # Extensions
│   └── plugins/               # Plugins
├── context7/                  # Context7 server (cloned repo)
├── playwright-mcp/            # Playwright server (cloned repo)
├── serena/                    # Serena server (cloned repo)
├── servers/                   # MCP reference servers
├── tools/                     # Utility scripts (6 tools)
├── tests/                     # Test configuration
├── logs/                      # Application logs
├── docs/                      # Documentation
└── *.json                     # Memory files
```

## Standards

- 100% AIPass standards compliance (verified 2025-11-29)
- Modular architecture with auto-discovery pattern
- Rich CLI output via `cli.apps.modules`

## Contact

- Branch: @mcp_servers
- Email: aipass.system@gmail.com

*Last Updated: 2026-02-15*
