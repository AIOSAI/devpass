# MCP_SERVERS Branch

MCP server integrations for the AIPass ecosystem.

## Purpose

Manages Model Context Protocol (MCP) server configurations and provides infrastructure for working with Serena, Context7, Playwright, and Sequential Thinking servers. Hosts cloned MCP server repositories and utility scripts for configuration management.

## MCP Servers

| Server | Description | Status |
|--------|-------------|--------|
| **Serena** | Project management and code navigation | Active |
| **Context7** | Documentation and library access | Active |
| **Playwright** | Browser automation | Active |
| **Sequential Thinking** | Step-by-step reasoning | Active |

Additional servers in `servers/src/`: everything, fetch, filesystem, git, memory, time.

## Configuration

- **Global config:** `/home/aipass/.mcp.json` (system-wide, 4 servers)
- **Local config:** `/home/aipass/mcp_servers/.mcp.json` (3 servers, no Playwright)

The global config at `/home/aipass/.mcp.json` is the primary MCP configuration used by Claude Code across all branches. Serena uses `--project /home/aipass` for system-wide access.

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
│   ├── modules/               # Auto-discovered modules (empty currently)
│   ├── json_templates/        # JSON templates
│   ├── extensions/            # Extensions
│   └── plugins/               # Plugins
├── context7/                  # Context7 server (cloned repo)
├── playwright-mcp/            # Playwright server (cloned repo)
├── serena/                    # Serena server (cloned repo, with .venv)
├── servers/                   # MCP reference servers (filesystem, git, memory, etc.)
├── tools/                     # Utility scripts (5 tools)
├── tests/                     # Test configuration
├── logs/                      # Application logs
├── docs/                      # Documentation templates
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