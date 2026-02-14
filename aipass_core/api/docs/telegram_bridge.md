# Telegram Bridge Service (v4 - tmux Persistent Sessions)

**Branch:** API
**Created:** 2026-02-03
**Updated:** 2026-02-12

---

## Overview

The Telegram Bridge connects Telegram messages to AIPass, allowing users to interact with Claude via Telegram. Uses persistent tmux sessions for full conversation continuity - Claude Code runs continuously, messages are injected via `tmux send-keys`, responses captured via Claude Code's Stop hook.

## Key Concepts

- **Long Polling**: Bot uses Telegram's polling API to receive messages
- **tmux Persistent Sessions**: Claude Code runs continuously in named tmux sessions (`telegram-{branch}`)
- **Stop Hook Response Delivery**: Claude's Stop hook reads JSONL transcript and sends response to Telegram
- **Coordination Files**: `~/.aipass/telegram_pending/` bridges the gap between bridge and Stop hook
- **Branch Targeting**: `@branch_name` prefix routes messages to different tmux sessions
- **Systemd User Service**: Runs in user space, no root required
- **Drone Integration**: Managed via `drone @api telegram` commands

## Architecture

```
Telegram → bridge.py (polling) → tmux send-keys → Claude Code (persistent)
                                                        ↓
Telegram ← Stop hook (telegram_response.py) ← JSONL transcript
```

### Flow Detail

1. Telegram message arrives at bridge via long-polling
2. Bridge resolves `@branch` target (default: dev_central)
3. Bridge checks/creates tmux session `telegram-{branch_name}`
4. Bridge writes `~/.aipass/telegram_pending/telegram-{branch}.json` with `{chat_id, bot_token, timestamp}`
5. Bridge injects message via `tmux send-keys -t telegram-{branch} -l "message" Enter`
6. Claude Code processes message naturally (full context, hooks, identity)
7. Stop hook fires on completion, reads JSONL transcript
8. Stop hook checks pending dir, extracts assistant text, sends to Telegram via Bot API
9. Stop hook cleans up pending file

## Service Management

### Start the Service

```bash
drone @api telegram start
```

### Stop the Service

```bash
drone @api telegram stop
```

### Check Status

```bash
drone @api telegram status
```

### View Logs

```bash
drone @api telegram logs
```

### Manual systemctl Commands

```bash
systemctl --user start telegram-bridge
systemctl --user stop telegram-bridge
systemctl --user status telegram-bridge
systemctl --user enable telegram-bridge   # Auto-start on login
```

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/new` | Kill current tmux session, start fresh (clean Claude context) |
| `/status` | Show active session details (branch, uptime, message count) |
| `/switch @branch` | Switch chat's target to a different branch |
| `/list` | List all active `telegram-*` tmux sessions |
| `/end` | Kill the tmux session for current branch |
| `/branch` | Show which branch current chat is targeting |
| `/help` | Show available commands |

## Files

| File | Purpose |
|------|---------|
| `apps/modules/telegram_bridge.py` | Bridge entry point (direct start) |
| `apps/modules/telegram_service.py` | Service control module |
| `apps/handlers/telegram/bridge.py` | v4.0.0 - Polling, tmux injection, commands |
| `apps/handlers/telegram/config.py` | Configuration loading |
| `apps/handlers/telegram/tmux_manager.py` | tmux session create/kill/send/list |
| `apps/handlers/telegram/session_store.py` | v2.0.0 - Per-chat branch tracking (JSON + fcntl) |
| `apps/handlers/telegram/file_handler.py` | Photo/document download and prompt building |
| `apps/handlers/telegram_service/service.py` | systemd operations |
| `~/.claude/hooks/telegram_response.py` | Stop hook - reads transcript, sends to Telegram |
| `~/.aipass/telegram_pending/` | Coordination directory for pending responses |
| `~/.config/systemd/user/telegram-bridge.service` | Service unit file |
| `~/.aipass/telegram_config.json` | Bot credentials |
| `~/.aipass/telegram_sessions.json` | Session store (chat_id → branch mapping) |
| `~/system_logs/telegram_bridge.log` | Bridge service logs |
| `~/system_logs/telegram_hook.log` | Stop hook logs |

## Configuration

Create `~/.aipass/telegram_config.json`:

```json
{
  "telegram_bot_token": "YOUR_BOT_TOKEN",
  "telegram_bot_username": "your_bot_username",
  "allowed_user_ids": []
}
```

### Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `telegram_bot_token` | string | Yes | Bot token from @BotFather |
| `telegram_bot_username` | string | Yes | Bot username (without @) |
| `allowed_user_ids` | array | No | List of Telegram user IDs allowed to use the bot |

### Security: User Allowlist

The `allowed_user_ids` field controls who can interact with the bot:

- **Empty array `[]`**: All users can use the bot (default, for testing)
- **With IDs `[123456789]`**: Only listed user IDs can use the bot

To find a user's Telegram ID, check the bot logs when they send a message:
```
[MESSAGE] From: @username (Name, ID: 123456789) | Chat: ...
```

### Security: Rate Limiting

The bridge includes built-in rate limiting:
- **5 messages per 60 seconds** per user
- Users exceeding the limit receive a "Rate limit exceeded" message
- Rate limits reset after the window expires

## Troubleshooting

### Service Not Found

```bash
systemctl --user daemon-reload
```

### Check Configuration

```bash
python3 apps/modules/telegram_bridge.py status
```

### View Full Logs

```bash
tail -f ~/system_logs/telegram_bridge.log
```

### Restart Service

```bash
drone @api telegram stop && drone @api telegram start
```

## tmux Session Management

Sessions are named `telegram-{branch_name}` (e.g., `telegram-dev_central`).

```bash
tmux list-sessions                          # List all tmux sessions
tmux attach -t telegram-dev_central         # Attach to see live conversation
tmux kill-session -t telegram-dev_central   # Manually kill a session
```

Sessions survive bridge restarts. Bridge auto-creates sessions on first message to a branch.

## Related

- [API README](../README.md)
- FPLAN-0288: Telegram Bridge v1-v3 Implementation
- FPLAN-0317: Telegram Bridge v4 - tmux Persistent Sessions

---

*Part of API branch documentation*
