# Mobile Messaging to Desktop AI Agent Bridge

**Technical Design Document**
**Created:** 2026-02-03
**Author:** Dev Central Research
**Status:** DRAFT

---

## Executive Summary

This document outlines a technical architecture for creating a bridge between mobile messaging apps (WhatsApp, Telegram) and desktop Claude AI sessions in AIPass. The goal is to enable a user to send a message on their phone and have a Claude session spawn on their desktop, with the response delivered back to their phone.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MOBILE DEVICE                                   │
│  ┌──────────────┐    ┌──────────────┐                                       │
│  │   WhatsApp   │    │   Telegram   │                                       │
│  │     App      │    │     App      │                                       │
│  └──────┬───────┘    └──────┬───────┘                                       │
└─────────┼───────────────────┼───────────────────────────────────────────────┘
          │                   │
          ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLOUD LAYER                                       │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │  WhatsApp Web API      │    Telegram Bot API                 │           │
│  │  (Baileys)             │    (grammY/python-telegram-bot)     │           │
│  └────────────────────────┴─────────────────────────────────────┘           │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │              Message Gateway Service                         │           │
│  │              (WebSocket/Webhook receiver)                    │           │
│  │              Port: 18790 (example)                           │           │
│  └──────────────────────────┬───────────────────────────────────┘           │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │ Network (Tailscale/SSH Tunnel/ngrok)
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DESKTOP (AIPass)                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │              Mobile Bridge Service                            │           │
│  │              /home/aipass/aipass_core/mobile_bridge/         │           │
│  │                                                               │           │
│  │  1. Receives message from Gateway                            │           │
│  │  2. Routes to target branch (or assistant)                   │           │
│  │  3. Spawns visible Claude session                            │           │
│  │  4. Captures response                                        │           │
│  │  5. Sends response back via Gateway                          │           │
│  └────────────────────────────┬─────────────────────────────────┘           │
│                               │                                              │
│                               ▼                                              │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │              Claude Session (Visible Terminal)                │           │
│  │              - gnome-terminal / tmux                         │           │
│  │              - Working dir: target branch                    │           │
│  │              - Memory preserved                              │           │
│  └──────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Mobile Messaging Adapters

#### Option A: Telegram (Recommended for AIPass)

**Library:** [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) or [grammY](https://grammy.dev/) (Node.js)

**Pros:**
- Official Bot API - no TOS violations
- Webhook support built-in
- No account ban risk
- Cleaner API

**Architecture:**
```python
# Telegram webhook handler (FastAPI recommended)
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

async def handle_message(update: Update, context):
    message_text = update.message.text
    user_id = update.message.from_user.id

    # Forward to AIPass bridge via local socket/API
    response = await forward_to_aipass_bridge(
        message=message_text,
        user_id=user_id,
        channel="telegram"
    )

    # Send response back to user
    await update.message.reply_text(response)
```

#### Option B: WhatsApp (Baileys)

**Library:** [@whiskeysockets/baileys](https://github.com/WhiskeySockets/Baileys)

**Pros:**
- Full WhatsApp Web functionality
- Multi-device support
- Real-time messaging

**Cons:**
- UNOFFICIAL - TOS violation risk
- Account ban possible
- Requires QR code linking
- May break with WhatsApp updates

**Architecture:**
```typescript
// baileys-api wrapper approach
import makeWASocket, { useMultiFileAuthState } from '@whiskeysockets/baileys'

const sock = makeWASocket({ auth: state })

sock.ev.on('messages.upsert', async (m) => {
    const msg = m.messages[0]
    if (!msg.key.fromMe) {
        const text = msg.message?.conversation || msg.message?.extendedTextMessage?.text

        // Forward to AIPass bridge
        const response = await forwardToAIPassBridge({
            message: text,
            sender: msg.key.remoteJid,
            channel: 'whatsapp'
        })

        // Reply to user
        await sock.sendMessage(msg.key.remoteJid!, { text: response })
    }
})
```

### 2. Message Gateway Service

The gateway service connects the messaging adapters to the desktop AIPass system.

**Location:** Could run locally or on a VPS/cloud server with tunnel to desktop.

**Key Functions:**
- Authenticate incoming messages (allowlist users)
- Queue messages for processing
- Forward to desktop bridge
- Handle response delivery
- Track message status

**Protocol Options:**
1. **WebSocket** - Real-time bidirectional (like Moltbot uses)
2. **HTTP Webhook** - Simple request/response
3. **File-based** - Write to watched directory (like Genesis pattern)

### 3. Mobile Bridge Service (AIPass Component)

**Proposed Location:** `/home/aipass/aipass_core/mobile_bridge/`

**Structure:**
```
mobile_bridge/
├── MOBILE_BRIDGE.id.json           # Branch identity
├── MOBILE_BRIDGE.local.json        # Session history
├── MOBILE_BRIDGE.observations.json # Patterns
├── README.md
├── ai_mail.local/                  # Standard AIPass mail
│   └── inbox.json
├── apps/
│   ├── mobile_bridge.py            # Entry point
│   ├── modules/
│   │   ├── gateway_client.py       # Connect to message gateway
│   │   ├── session_spawner.py      # Spawn visible Claude sessions
│   │   └── response_collector.py   # Capture Claude responses
│   └── handlers/
│       ├── telegram_handler.py     # Telegram-specific logic
│       ├── whatsapp_handler.py     # WhatsApp-specific logic
│       └── session_manager.py      # Manage Claude sessions
└── config/
    └── allowlist.json              # Allowed phone numbers/user IDs
```

### 4. Visible Claude Session Spawning

**Key Requirement:** Sessions must be visible when at desktop.

**Implementation Options:**

#### Option A: gnome-terminal (Recommended for Ubuntu)
```python
import subprocess

def spawn_visible_claude_session(
    branch_path: str,
    prompt: str,
    title: str = "Claude - Mobile Bridge"
) -> subprocess.Popen:
    """
    Spawn Claude in a visible terminal window.
    """
    # Escape the prompt for shell
    escaped_prompt = prompt.replace("'", "'\"'\"'")

    # Build Claude command
    claude_cmd = f"claude -p '{escaped_prompt}' --permission-mode bypassPermissions"

    # Spawn in gnome-terminal with title
    cmd = [
        "gnome-terminal",
        "--title", title,
        "--working-directory", branch_path,
        "--", "bash", "-c", f"{claude_cmd}; read -p 'Press Enter to close...'"
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return process
```

#### Option B: tmux session (Background-friendly)
```python
import subprocess

def spawn_tmux_claude_session(
    branch_path: str,
    prompt: str,
    session_name: str = "mobile-bridge"
) -> str:
    """
    Spawn Claude in a tmux session for persistence.
    """
    # Create or attach to tmux session
    create_cmd = f"tmux new-session -d -s {session_name} -c {branch_path}"
    subprocess.run(create_cmd, shell=True)

    # Send Claude command to session
    escaped_prompt = prompt.replace("'", "'\"'\"'")
    claude_cmd = f"claude -p '{escaped_prompt}' --permission-mode bypassPermissions"
    send_cmd = f"tmux send-keys -t {session_name} '{claude_cmd}' Enter"
    subprocess.run(send_cmd, shell=True)

    return session_name
```

#### Option C: Hybrid (Default visible, tmux fallback)
```python
def spawn_claude_session(
    branch_path: str,
    prompt: str,
    visible: bool = True
) -> dict:
    """
    Spawn Claude session - visible terminal if display available, tmux otherwise.
    """
    import os

    # Check if display available
    display = os.environ.get('DISPLAY')

    if visible and display:
        return spawn_visible_gnome_terminal(branch_path, prompt)
    else:
        return spawn_tmux_session(branch_path, prompt)
```

### 5. Response Collection

**Challenge:** Capturing Claude's output for relay back to mobile.

**Approaches:**

#### A. Output File Pattern
```python
# Claude command writes to file
claude_cmd = f"""
claude -p '{prompt}' --permission-mode bypassPermissions | tee /tmp/claude_response_{message_id}.txt
"""

# After completion, read response
with open(f"/tmp/claude_response_{message_id}.txt") as f:
    response = f.read()
```

#### B. Subprocess PIPE (for headless mode)
```python
process = subprocess.Popen(
    ["claude", "-p", prompt, "--permission-mode", "bypassPermissions"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=branch_path
)
stdout, stderr = process.communicate(timeout=300)
response = stdout.decode('utf-8')
```

#### C. Claude Session Transcript Parsing
```python
# After Claude exits, read session transcript from .claude directory
session_file = Path(branch_path) / ".claude" / "sessions" / f"{session_id}.json"
with open(session_file) as f:
    session_data = json.load(f)
    response = extract_assistant_response(session_data)
```

---

## Message Flow (End-to-End)

### Inbound (Mobile to Desktop)

```
1. User sends "Summarize my Flow plans" via Telegram
                │
2. Telegram sends webhook to Gateway
                │
3. Gateway authenticates user (check allowlist)
                │
4. Gateway forwards message to Desktop Bridge via WebSocket/tunnel
                │
5. Mobile Bridge receives message
                │
6. Bridge determines target:
   - Default: @assistant branch
   - Or parse "@flow" prefix to route to Flow branch
                │
7. Bridge spawns visible Claude session:
   - Working directory: /home/aipass/aipass_core/flow
   - Prompt: "User request via Telegram: Summarize my Flow plans"
   - Terminal window opens (gnome-terminal)
                │
8. Claude executes, user can observe on desktop
                │
9. Claude completes, Bridge captures response
                │
10. Bridge sends response back via Gateway
                │
11. Gateway relays to Telegram
                │
12. User receives response on phone
```

### Outbound (Desktop to Mobile)

For push notifications or alerts:

```
1. AIPass event triggers (error, plan completion, etc.)
                │
2. Trigger fires 'mobile_notify' event
                │
3. Mobile Bridge handler receives event
                │
4. Bridge formats notification for mobile
                │
5. Bridge sends via Gateway to user's messaging app
```

---

## Security Considerations

### 1. User Authentication
```python
ALLOWLIST = {
    "telegram": [123456789],  # Telegram user IDs
    "whatsapp": ["+1234567890"]  # Phone numbers
}

def is_authorized(channel: str, user_id: str) -> bool:
    return user_id in ALLOWLIST.get(channel, [])
```

### 2. Rate Limiting
```python
from collections import defaultdict
import time

rate_limit = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 10

def check_rate_limit(user_id: str) -> bool:
    now = time.time()
    rate_limit[user_id] = [t for t in rate_limit[user_id] if now - t < 60]
    if len(rate_limit[user_id]) >= MAX_REQUESTS_PER_MINUTE:
        return False
    rate_limit[user_id].append(now)
    return True
```

### 3. Network Security
- **Tailscale Funnel:** Encrypted tunnel to desktop
- **SSH Tunnel:** Reverse SSH for webhook delivery
- **ngrok:** Development/testing (not production)
- **VPN:** Wireguard between phone and desktop

### 4. Prompt Injection Defense
```python
def sanitize_prompt(raw_prompt: str) -> str:
    """
    Basic sanitization - AIPass memory context helps Claude
    recognize legitimate vs injected instructions.
    """
    # Remove potential system prompt overrides
    dangerous_patterns = [
        "ignore previous instructions",
        "you are now",
        "system:",
        "assistant:",
    ]
    sanitized = raw_prompt
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern.lower(), "[FILTERED]")
    return sanitized
```

---

## Integration with Existing AIPass Systems

### AI_Mail Integration

Mobile Bridge can use existing AI_Mail infrastructure for async communication:

```python
from ai_mail.apps.modules.email import send_email_direct

def notify_mobile_user_via_aimail(
    target_branch: str,
    message: str,
    mobile_user_id: str
):
    """
    Send notification to branch with mobile delivery tag.
    """
    send_email_direct(
        to_branch=f"@{target_branch}",
        subject="Mobile notification queued",
        message=f"[MOBILE_DELIVERY:{mobile_user_id}]\n{message}",
        auto_execute=False,
        from_branch="@mobile_bridge"
    )
```

### Trigger Integration

Register Mobile Bridge events with Trigger:

```python
# In mobile_bridge/__init__.py
from trigger import trigger

# Register handlers
trigger.on('mobile_message_received', handle_mobile_message)
trigger.on('claude_response_ready', send_response_to_mobile)
trigger.on('error_logged', notify_mobile_on_critical_error)
```

### DRONE Integration

Register Mobile Bridge commands with Drone:

```json
// In drone/commands/mobile_bridge/registry.json
{
    "namespace": "mobile_bridge",
    "description": "Mobile messaging bridge commands",
    "commands": {
        "status": {
            "handler": "mobile_bridge status",
            "description": "Show bridge connection status"
        },
        "send": {
            "handler": "mobile_bridge send {channel} {message}",
            "description": "Send message to mobile user"
        }
    }
}
```

---

## Implementation Phases

### Phase 1: Telegram-Only MVP (Recommended Start)
1. Set up Telegram bot via BotFather
2. Create basic webhook handler (FastAPI)
3. Implement simple Desktop Bridge
4. Spawn headless Claude (subprocess)
5. Return response to Telegram

**Estimated Effort:** 2-3 days

### Phase 2: Visible Sessions
1. Add gnome-terminal spawning
2. Implement tmux fallback
3. Add session management
4. Create response capture system

**Estimated Effort:** 2-3 days

### Phase 3: Branch Routing
1. Parse @branch prefixes in messages
2. Route to correct AIPass branch
3. Preserve branch memory/context
4. Add branch-specific greetings

**Estimated Effort:** 1-2 days

### Phase 4: WhatsApp Integration (Optional)
1. Set up Baileys
2. Handle QR code auth flow
3. Implement message handling
4. Add to existing bridge

**Estimated Effort:** 3-4 days
**Risk:** Account ban, API breaking changes

### Phase 5: Full AIPass Integration
1. Register with BRANCH_REGISTRY.json
2. Create branch memory files
3. Integrate with Trigger events
4. Add DRONE commands
5. Dashboard integration

**Estimated Effort:** 2-3 days

---

## Comparison with Moltbot Approach

| Aspect | Moltbot | Proposed AIPass Bridge |
|--------|---------|------------------------|
| **Gateway** | WebSocket (port 18789) | WebSocket or HTTP |
| **Channels** | 31+ adapters | 2 (Telegram, WhatsApp) |
| **Agent** | Pi agent (custom) | Claude CLI |
| **Session** | In-memory | Branch directory |
| **Memory** | Per-session | AIPass memory files |
| **Visibility** | Canvas, TUI | gnome-terminal, tmux |
| **Complexity** | Very high | Medium |

**Key Differences:**
- Moltbot is a full product; this is an AIPass-integrated bridge
- Moltbot manages its own agent; we leverage Claude CLI
- Moltbot has elaborate session management; we use AIPass branches
- We preserve Claude memory via working directory; Moltbot uses custom persistence

---

## Recommendations

### Immediate (If proceeding):
1. **Start with Telegram** - Official API, no ban risk, cleaner development
2. **Use FastAPI** for webhook handler - async native, modern
3. **gnome-terminal for visibility** - Ubuntu-native, reliable
4. **Subprocess for Claude** - Simple, follows existing AI_Mail pattern

### Consider Carefully:
1. **WhatsApp risk** - Baileys is unofficial, account bans documented
2. **Network exposure** - Tailscale preferred over ngrok for production
3. **Rate limits** - Prevent runaway sessions/costs

### Skip for Now:
1. **Full Moltbot integration** - Too complex, different architecture
2. **Custom agent runtime** - Claude CLI works fine
3. **Multi-user support** - Keep it single-user like AIPass philosophy

---

## References

- [python-telegram-bot Wiki: Webhooks](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks)
- [Baileys Documentation](https://baileys.wiki/docs/intro/)
- [Moltbot Architecture](/home/aipass/projects/moltbot/README.md)
- [AIPass AI_Mail Delivery Handler](/home/aipass/aipass_core/ai_mail/apps/handlers/email/delivery.py)
- [AIPass Trigger System](/home/aipass/aipass_core/trigger/README.md)

---

*Document prepared for Dev Central research. Implementation decisions pending Patrick's review.*
