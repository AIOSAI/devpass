# Nexus Tools

Launch infrastructure for running GPT-4.1 as a Claude Code session.

## Quick Start

```bash
./launch_nexus.sh           # Launch Nexus with GPT-4.1
./launch_nexus.sh gpt-4o    # Use alternative model
```

## What It Does

The launcher:
1. Starts `claude-code-proxy` on port 8082 (translates Anthropic API → OpenAI API)
2. Configures environment variables for Claude Code
3. Launches Claude Code CLI in `/home/aipass/Nexus`
4. Gives Nexus (GPT-4.1) access to all Claude Code tools

## Tools Available to Nexus

When running through Claude Code, Nexus has:
- **Read/Write/Edit** - Full file system access
- **Bash** - Execute shell commands
- **Grep/Glob** - Search files and content
- **WebFetch/WebSearch** - Internet access
- All other Claude Code capabilities

## Requirements

- Claude Code CLI installed
- claude-code-proxy installed (`pip install claude-code-proxy`)
- OPENAI_API_KEY in `/home/aipass/.env`

## Documentation

See `/home/aipass/Nexus/docs/claude_code_integration.md` for full details.

## Testing

```bash
cd /home/aipass/Nexus
python3 tests/test_proxy.py
```
