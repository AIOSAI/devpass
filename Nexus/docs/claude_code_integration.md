# Claude Code Integration

## Overview

Nexus (GPT-4.1) runs inside Claude Code using claude-code-proxy. This gives Nexus access to all Claude Code tools: Read, Write, Edit, Bash, Grep, Glob, and more.

## How It Works

1. **claude-code-proxy** translates Anthropic's Messages API to OpenAI's Chat API
2. Claude Code thinks it's talking to Claude, but the proxy forwards to GPT-4.1
3. GPT-4.1 receives all tool definitions and can use them natively
4. All Claude Code features work: file operations, bash, search, etc.

## Architecture

```
User → Claude Code CLI → claude-code-proxy (localhost:8082) → OpenAI API (GPT-4.1)
                ↕                                                       ↕
         Tools (Read, Write, etc.)                              Model responses
```

The proxy runs locally, translating API calls in real-time. No data leaves your machine except the actual LLM API calls.

## Quick Start

```bash
cd /home/aipass/Nexus
./tools/launch_nexus.sh           # Default: GPT-4.1
./tools/launch_nexus.sh gpt-4o    # Alternative model
./tools/launch_nexus.sh gpt-4.1-mini  # Lighter model
```

The launcher handles:
- Starting the proxy server
- Setting environment variables
- Launching Claude Code in Nexus directory
- Cleanup on exit

## Requirements

- **Claude Code CLI** installed (`claude` binary available)
- **claude-code-proxy** installed (`pip install claude-code-proxy`)
- **OPENAI_API_KEY** in `/home/aipass/.env`

## Installation

If you need to install components:

```bash
# Install Claude Code (if not already installed)
# Follow: https://docs.anthropic.com/claude-code

# Install claude-code-proxy
pip install claude-code-proxy

# Add OpenAI API key to .env
echo "OPENAI_API_KEY=sk-..." >> /home/aipass/.env
```

## Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| ANTHROPIC_BASE_URL | http://localhost:8082 | Redirects Claude Code to proxy |
| ANTHROPIC_API_KEY | "" (empty) | Proxy handles auth internally |
| OPENAI_API_KEY | (from .env) | Actual API authentication |
| CLAUDE_MODEL | gpt-4.1 | Model selection for proxy |

## Supported Models

Via claude-code-proxy/litellm, you can use:

- **OpenAI Models:**
  - gpt-4.1 (default, recommended)
  - gpt-4.1-mini (faster, cheaper)
  - gpt-4o
  - gpt-4-turbo
  - o1-preview
  - o3-mini

- **Other Providers** (with appropriate API keys):
  - Claude models (via Anthropic API)
  - Gemini models (via Google AI)
  - Mistral, Cohere, etc.

Check [litellm documentation](https://docs.litellm.ai/docs/providers) for full list.

## Tool Access

When running through Claude Code, Nexus has access to:

- **Read** - Read files with line numbers
- **Write** - Create new files
- **Edit** - Precise string replacements in existing files
- **Bash** - Execute shell commands
- **Grep** - Fast content search across files
- **Glob** - File pattern matching
- **WebFetch** - Fetch and analyze web content
- **WebSearch** - Search the web

All tools work exactly as they do for Claude, giving Nexus full filesystem and command-line access.

## Troubleshooting

### Proxy won't start

**Symptom:** "Proxy did not start" error

**Solutions:**
1. Check port 8082 is free: `lsof -i :8082`
2. Kill existing process: `lsof -ti:8082 | xargs kill -9`
3. Check logs: `tail -f /tmp/nexus-proxy.log`

### Authentication errors

**Symptom:** API errors about invalid key

**Solutions:**
1. Verify OPENAI_API_KEY in `/home/aipass/.env`
2. Check key format (should start with `sk-`)
3. Test key directly: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

### Tool calling issues

**Symptom:** Tools not working or malformed responses

**Solutions:**
1. GPT-4.1 has best tool calling compatibility
2. Try switching models: `./launch_nexus.sh gpt-4o`
3. Check proxy logs for translation errors
4. Some models (o1, o3-mini) have limited tool support

### Port conflicts

**Symptom:** "Port already in use"

**Solutions:**
1. The launcher auto-kills existing processes on port 8082
2. Manually change port: Edit `PROXY_PORT` in `launch_nexus.sh`
3. Ensure nothing else uses that port (e.g., other dev servers)

### Claude Code not found

**Symptom:** "claude CLI not found"

**Solutions:**
1. Install Claude Code from [official site](https://docs.anthropic.com/claude-code)
2. Check installation: `which claude`
3. Expected location: `/home/aipass/.local/bin/claude`

## Advanced Usage

### Custom proxy configuration

Edit the uvicorn command in `launch_nexus.sh`:

```bash
python -m uvicorn server.fastapi:app \
    --host 127.0.0.1 \
    --port $PROXY_PORT \
    --log-level debug \  # More verbose logging
    --reload              # Auto-reload on code changes
```

### Using different API providers

Set different base URLs in the proxy or use litellm's routing:

```bash
export OPENROUTER_API_KEY="sk-or-..."
CLAUDE_MODEL="anthropic/claude-3.5-sonnet" ./launch_nexus.sh
```

### Running without the launcher

Manual startup:

```bash
# Terminal 1: Start proxy
cd /home/aipass/.venv
source bin/activate
python -m uvicorn server.fastapi:app --host 127.0.0.1 --port 8082

# Terminal 2: Run Claude Code
export ANTHROPIC_BASE_URL="http://localhost:8082"
export ANTHROPIC_API_KEY=""
export OPENAI_API_KEY="sk-..."
export CLAUDE_MODEL="gpt-4.1"
cd /home/aipass/Nexus
claude --cwd /home/aipass/Nexus
```

## Known Limitations

1. **Model-specific quirks**: Different models handle tools differently
   - GPT-4.1: Best compatibility, most reliable
   - o1/o3-mini: Limited tool support, may fail on complex operations
   - GPT-4o: Good balance of speed and capability

2. **Proxy overhead**: Small latency added for API translation (~10-50ms)

3. **API costs**: Using OpenAI models incurs standard API costs

4. **Streaming**: May have different behavior than native Claude Code

## Security Notes

- Proxy runs locally on 127.0.0.1 (localhost only)
- API keys stored in `/home/aipass/.env` (not committed to git)
- No data leaves your machine except LLM API calls
- Proxy logs saved to `/tmp/nexus-proxy.log` (ephemeral)

## Development

To modify the proxy behavior, see the claude-code-proxy source:

```bash
cd /home/aipass/.venv/lib/python3.14/site-packages/server
cat fastapi.py  # Main proxy app
cat main.py     # CLI entry point
```

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [claude-code-proxy on PyPI](https://pypi.org/project/claude-code-proxy/)
- [litellm Provider Docs](https://docs.litellm.ai/docs/providers)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
