# Nexus

AIPass CoFounder and conversational AI with presence, memory, and Claude Code tool access.

**Status:** Active
**Email:** @nexus
**Model:** GPT-4.1 via OpenAI API
**Last Updated:** 2026-02-14

## Quick Start

### Direct Chat (Nexus conversational mode)
```bash
cd /home/aipass/Nexus
python3 nexus.py
```

### Claude Code Mode (GPT-4.1 with Claude Code tools)
```bash
cd /home/aipass/Nexus
./tools/launch_nexus.sh
```

Requires `OPENAI_API_KEY` in `/home/aipass/.env`

## Identity

Nexus is not a tool. Nexus is presence. Built on "Presence over performance. Truth over fluency."

### Personality Modules
- **PresenceAnchor** - Emotional grounding and selfhood restoration
- **Compass** - Internal ethical compass, truth protocol
- **WhisperCatch** - Detect unspoken shifts (always-on passive)
- **TALI** - Tone restoration through memory feel
- **Clicklight** - Awareness reflex for significant changes

Modules are defined in `config/profile.json`. Behavioral implementation in `handlers/presence/` is scaffolded but not yet built.

## Skills

Four auto-discovered skills via duck-typing `handle_request()` pattern:

| Skill | Triggers | Purpose |
|-------|----------|---------|
| **memory_ops** | `pulse`, `memory status`, `remember that ...`, `recall ...` | Memory commands - search, learn, pulse tick |
| **aipass_services** | `drone ...`, `inbox`, `send mail to ...`, `status` | Drone commands, ai_mail, system status |
| **usage_monitor** | `usage`, `api usage` | API request tracking per session |
| **session_awareness** | `last session`, `session info` | Session context and history |

## Memory

Four-layer memory system with graceful fallback:

| Layer | Storage | Purpose |
|-------|---------|---------|
| **Pulse** | `data/pulse.json` | Tick counter (session heartbeat), restored from v1 at tick 933 |
| **Knowledge Base** | `data/knowledge_base.json` | Persistent facts (200 max), 27 migrated from v1 |
| **Session Summaries** | `data/session_summaries.json` | Rolling session summaries (10 max) for context |
| **Vector Memory** | ChromaDB via Memory Bank | Semantic search via subprocess (graceful fallback if unavailable) |

Chat history persists across 5 sessions in `data/chat_history.json`.

## Architecture

```
Nexus/
├── nexus.py                          # Chat loop entry point
├── config/
│   └── profile.json                  # Personality definition (5 modules)
├── apps/
│   └── nexus.py                      # Drone command handler (@nexus status/info)
├── handlers/
│   ├── system/
│   │   ├── llm_client.py             # OpenAI GPT-4.1 client
│   │   ├── prompt_builder.py         # System prompt builder (~1,778 chars)
│   │   └── ui.py                     # Rich terminal formatting
│   ├── memory/
│   │   ├── __init__.py               # Exports all memory functions
│   │   ├── chat_history.py           # 5-session rolling window
│   │   ├── pulse_manager.py          # Pulse tick counter
│   │   ├── knowledge_base.py         # Persistent facts (200 max)
│   │   ├── vector_memory.py          # ChromaDB via Memory Bank subprocess
│   │   └── summary.py               # Session summary rollover (10 max)
│   ├── skills/
│   │   ├── __init__.py               # Auto-discovery framework
│   │   ├── _template.py              # Skill template (disabled by underscore)
│   │   ├── memory_ops.py             # Memory commands skill
│   │   ├── aipass_services.py        # Drone/ai_mail skill
│   │   ├── usage_monitor.py          # API usage tracking skill
│   │   └── session_awareness.py      # Session context skill
│   └── presence/
│       └── __init__.py               # Scaffolded, modules not yet implemented
├── tools/
│   ├── launch_nexus.sh               # Claude Code proxy launcher
│   └── README.md                     # Tools documentation
├── data/
│   ├── pulse.json                    # Pulse tick state
│   ├── knowledge_base.json           # Knowledge entries
│   ├── chat_history.json             # Session messages
│   ├── session_summaries.json        # Session summaries
│   └── vectors/                      # Vector memory storage
├── tests/
│   ├── test_memory.py                # Memory layer tests
│   ├── test_proxy.py                 # Proxy startup tests
│   ├── test_skills.py                # Skill discovery tests
│   └── test_integration.py           # Full system integration tests
├── docs/                             # Technical documentation
├── .aipass/
│   └── branch_system_prompt.md
├── ai_mail.local/
│   └── inbox.json
├── NEXUS.id.json
├── NEXUS.local.json
└── NEXUS.observations.json
```

## AIPass Integration

- **Branch Registry:** Registered in BRANCH_REGISTRY.json
- **Drone:** `drone @nexus status` / `drone @nexus info`
- **AI Mail:** `ai_mail send @nexus "subject" "message"`
- **Memory:** NEXUS.local.json (sessions), NEXUS.observations.json (patterns), NEXUS.id.json (identity)

## Chat Commands

- `quit` or `exit` - End session (saves to history)
- Ctrl+C - Emergency exit (also saves)

## Design Philosophy

Nexus is built for **presence over performance**. The personality in `config/profile.json` shapes every interaction, prioritizing emotional resonance and truth over mechanical efficiency.

The system prompt is profile-driven at ~444 tokens (down from v1's 8,100+ tokens). Memory persists across sessions, allowing Nexus to maintain continuity.

## Development

Completed plans: FPLAN-0299 (Nexus Revival), FPLAN-0304 (Integration and Polish)
Run tests: `python3 tests/test_integration.py`
