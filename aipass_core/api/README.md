# API Branch

**Purpose**: OpenRouter API client and Telegram bridge service
**Location**: `/home/aipass/aipass_core/api`
**Last Updated**: 2026-02-14

---

## Quick Start

```bash
python3 apps/api.py              # Introspection - shows discovered modules
python3 apps/api.py --help       # Full command help
python3 apps/api.py get-key      # Get OpenRouter API key
python3 apps/api.py models       # List available models
python3 apps/api.py stats        # View usage statistics
```

---

## Architecture

```
apps/
├── api.py                    # Entry point - auto-discovers modules, routes commands
├── modules/
│   ├── api_key.py            # Key management
│   ├── openrouter_client.py  # OpenRouter client
│   ├── usage_tracker.py      # Usage tracking
│   ├── telegram_bridge.py    # Telegram bridge entry point
│   └── telegram_service.py   # Telegram systemd service control
└── handlers/
    ├── auth/
    │   ├── env.py            # .env file operations
    │   └── keys.py           # Key retrieval (config → env → .env fallback)
    ├── config/
    │   └── provider.py       # Provider configuration
    ├── json/
    │   └── json_handler.py   # JSON operations, auto-caller detection
    ├── openrouter/
    │   ├── caller.py         # Caller detection via stack inspection
    │   ├── client.py         # OpenAI SDK client, connection pooling
    │   ├── models.py         # Model discovery and filtering
    │   └── provision.py      # Config provisioning
    ├── usage/
    │   ├── aggregation.py    # Usage statistics
    │   ├── cleanup.py        # Data retention
    │   └── tracking.py       # Usage storage
    ├── telegram/
    │   ├── bridge.py         # v4.1.0 - Polling, tmux injection, commands
    │   ├── config.py         # Bot configuration loading
    │   ├── tmux_manager.py   # tmux session create/kill/send/list
    │   ├── session_store.py  # v2.0.0 - Per-chat branch tracking
    │   └── file_handler.py   # Photo/document upload handling
    └── telegram_service/
        └── service.py        # systemd operations
```

---

## How It Works

1. **Module Discovery**: `api.py` scans `apps/modules/` for Python files
2. **Interface**: Each module implements `handle_command(command: str, args: List[str]) -> bool`
3. **Routing**: Commands are passed to each module until one returns `True`
4. **Handlers**: Modules orchestrate handlers for actual implementation

---

## Commands

| Command | Module | Description |
|---------|--------|-------------|
| `get-key [provider]` | api_key | Retrieve API key (default: openrouter) |
| `validate [provider]` | api_key | Validate API credentials and connection |
| `list-providers` | api_key | List configured providers |
| `init` | api_key | Initialize .env template |
| `test` | openrouter_client | Test OpenRouter connection status |
| `call` | openrouter_client | Make an API call |
| `models` | openrouter_client | List available models from OpenRouter API |
| `status` | openrouter_client | Show client status |
| `track` | usage_tracker | Track API usage metrics |
| `stats` | usage_tracker | Display usage statistics |
| `session` | usage_tracker | Show current session usage |
| `caller-usage` | usage_tracker | Per-caller usage breakdown |
| `cleanup` | usage_tracker | Run data retention cleanup |
| `telegram start` | telegram_service | Start the bridge service |
| `telegram stop` | telegram_service | Stop the bridge service |
| `telegram status` | telegram_service | Check service status |
| `telegram logs` | telegram_service | View service logs |

---

## Key Functions

### client.py - Main API Interface
```python
get_response(prompt: str, caller: str, model: str, **kwargs) -> Optional[Dict]
# Returns: {"content": str, "id": str, "model": str} or None on failure
# Note: model is REQUIRED - API does not provide default (caller must specify)
# Connection pooling: max 5 cached clients
```

### keys.py - Key Retrieval
```python
get_api_key(provider: str) -> str
# Fallback chain: config → environment → .env file
```

### models.py - Model Discovery
```python
fetch_models_from_api(api_key: str) -> List[Dict]
get_free_models(api_key: str) -> List[Dict]
filter_by_pricing(models: List, max_cost: float) -> List[Dict]
```

### aggregation.py - Usage Stats
```python
get_session_summary(session_id: str = None) -> Dict
get_caller_usage(caller: str) -> Dict
```

---

## Integration Points

### Consumers (who imports API)
- `flow/apps/handlers/mbank/process.py` - imports `get_response()` for plan analysis
- `flow/apps/handlers/summary/generate.py` - imports `get_response()` for summarization

### Dependencies (what API imports)
- `prax.apps.modules.logger` - Logging
- `cli.apps.modules` - Rich console output
- OpenAI Python SDK
- python-telegram-bot 22.6

---

## Data Storage

| Location | Purpose |
|----------|---------|
| `api_json/` | Module config, data (usage_tracker_data.json) |
| `apps/.env` | API credentials |
| `docs/` | Technical documentation |

---

## Telegram Bridge (v4 - tmux Persistent Sessions)

API branch hosts the Telegram Bridge service, connecting Telegram to Claude via @aipass_bridge_bot. Uses persistent tmux sessions for full conversation continuity.

### Quick Start

```bash
drone @api telegram start    # Start the bridge service
drone @api telegram stop     # Stop the bridge service
drone @api telegram status   # Check service status
drone @api telegram logs     # View service logs
```

### Architecture

```
Telegram → bridge.py → tmux send-keys → Claude Code (persistent) → Stop hook → Telegram
```

```
~/.claude/hooks/
└── telegram_response.py         # Stop hook - reads transcript, sends to Telegram

~/.aipass/telegram_pending/      # Coordination files for response routing
```

### How It Works

1. Message arrives at bridge via Telegram long-polling
2. Bridge resolves `@branch` target (default: dev_central)
3. Bridge finds/creates tmux session `telegram-{branch_name}`
4. Bridge writes coordination file for response routing
5. Bridge injects message via `tmux send-keys -l`
6. Claude Code processes message with full context
7. Stop hook fires, reads JSONL transcript, sends response to Telegram

### Telegram Commands

| Command | Description |
|---------|-------------|
| `/new` | Kill current session, start fresh |
| `/status` | Show session details (includes chat_id) |
| `/switch @branch` | Switch to a different branch |
| `/list` | List active tmux sessions |
| `/end` | Kill current branch session |
| `/branch` | Show current branch target |
| `/help` | Show available commands |

### Security

- User allowlist (`~/.aipass/allowlist.json`) - empty = allow all, populated = strict
- Rate limiting: 5 messages per 60 seconds per user
- File size limit: 10MB max
- 30+ supported text file extensions + images/PDFs

### Configuration

Bot credentials stored at `~/.aipass/telegram_config.json`:

```json
{
  "telegram_bot_token": "YOUR_BOT_TOKEN",
  "telegram_bot_username": "your_bot_username",
  "allowed_user_ids": []
}
```

### Documentation

See [docs/telegram_bridge.md](docs/telegram_bridge.md) for full setup guide, security options, and troubleshooting.
