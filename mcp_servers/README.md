# MCP_SERVERS Branch

MCP server integrations for the AIPass ecosystem.

## Purpose

Manages Model Context Protocol (MCP) server configurations and hosts cloned MCP server repositories. Provides utility scripts for configuration management across the system.

## MCP Servers

Four servers configured in the global config (`/home/aipass/.mcp.json`), available system-wide:

| Server | Description | Status |
|--------|-------------|--------|
| **Serena** | Project management and code navigation (`--project /home/aipass`) | Active |
| **Context7** | Documentation and library access | Active |
| **Playwright** | Browser automation (global only) | Active |
| **Sequential Thinking** | Step-by-step reasoning | Active |

A local config (`/home/aipass/mcp_servers/.mcp.json`) exists with 3 servers (no Playwright).

Reference server sources in `servers/src/`: everything, fetch, filesystem, git, memory, sequentialthinking, time.

## Configuration

- **Global:** `/home/aipass/.mcp.json` — primary config used by Claude Code across all branches
- **Local:** `/home/aipass/mcp_servers/.mcp.json` — branch-specific (3 servers, no Playwright)

Global config is the source of truth. Serena uses `--project /home/aipass` for system-wide access.

## Usage

```bash
python3 apps/mcp_servers.py --help    # View help with Rich formatting
python3 apps/mcp_servers.py           # Show discovered modules
drone @mcp_servers help               # Via Drone router
```

## Directory Structure

```
mcp_servers/
├── apps/
│   ├── mcp_servers.py         # Main orchestrator (modular, auto-discovery)
│   ├── handlers/json/         # JSON handler (json_handler.py)
│   ├── modules/               # Auto-discovered modules
│   ├── json_templates/        # JSON templates
│   ├── extensions/            # Extensions
│   └── plugins/               # Plugins
├── context7/                  # Context7 server (cloned repo)
├── playwright-mcp/            # Playwright server (cloned repo)
├── serena/                    # Serena server (cloned repo)
├── servers/                   # MCP reference servers (src/: everything, fetch, filesystem, git, memory, sequentialthinking, time)
├── tools/                     # Utility scripts (6 tools)
├── tests/                     # Test configuration
├── logs/                      # Application logs
├── docs/                      # Documentation
└── *.json                     # Memory files (id, local, observations)
```

## Tools

| Tool | Purpose |
|------|---------|
| `clean-claude-json-mcp.py` | Clean Claude JSON MCP configs |
| `auto-register-serena-projects.py` | Register projects with Serena |
| `fix-mcp-json-projects.py` | Fix MCP JSON project configs |
| `cleanup-local-configs.py` | Clean up local configurations |
| `apps_migration_fixer.py` | Fix app migrations |
| `convert_print.py` | Convert print statements to Rich console |

## Standards

- 100% AIPass standards compliance (verified 2025-11-29)
- Modular architecture with auto-discovery pattern
- Rich CLI output via `cli.apps.modules`
- Logging via `prax.apps.modules.logger`
- Handlers implement logic, modules orchestrate

## Contact

- Branch: @mcp_servers
- Email: aipass.system@gmail.com

*Last Updated: 2026-02-14*