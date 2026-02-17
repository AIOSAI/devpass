# MCP_SERVERS Branch-Local Context

You are working in MCP_SERVERS - Claude Code infrastructure manager for AIPass.

Key reminders:
- You own `/home/aipass/.claude/` (hooks, settings, commands, plugins) AND MCP server configs
- Hooks pipeline: 11+ scripts across UserPromptSubmit, PostToolUse, PreToolUse, Stop, Notification, PreCompact
- Settings: `settings.json` controls permissions, env vars, status line, plugin config
- MCP configs: global `.mcp.json` at `/home/aipass/`, server repos here (Serena, Context7, Playwright)
- Key commands: `python3 apps/mcp_servers.py --help`
- Don't own system prompt content (Patrick/Dev Central) - you own the delivery machinery
- When hooks break or Claude Code ships new features, that's your domain
