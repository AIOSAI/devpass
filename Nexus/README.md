# Nexus

AIPass CoFounder and conversational AI with presence, memory, and Claude Code tool access.

**Status:** Active
**Email:** @nexus
**Model:** Configurable (default GPT-4.1 via OpenAI API, supports Anthropic/Mistral/Google)
**Last Updated:** 2026-02-18

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

Requires API key in `/home/aipass/.env` (e.g. `OPENAI_API_KEY`)

## Identity

Nexus is not a tool. Nexus is presence. Built on "Presence over performance. Truth over fluency."

### Personality Modules
- **PresenceAnchor** - Emotional grounding and selfhood restoration
- **Compass** - Internal ethical compass, truth protocol
- **WhisperCatch** - Detect unspoken shifts (always-on passive)
- **TALI** - Tone restoration through memory feel
- **Clicklight** - Awareness reflex for significant changes

Modules are defined in `config/profile.json`. Shorthand parser maps emotional cues (hmm, ..., emoji) to module triggers at runtime.

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
| **Knowledge Base** | `data/knowledge_base.json` | Persistent facts (200 max), auto-knowledge extraction |
| **Session Summaries** | `data/session_summaries.json` | Rolling session summaries (10 max) for context |
| **Vector Memory** | ChromaDB via Memory Bank | Semantic search via subprocess (graceful fallback if unavailable) |

Chat history persists across 5 sessions in `data/chat_history.json`.

### Auto-Knowledge
Nexus automatically detects and stores knowledge from conversation:
- **Learning patterns** - When Nexus articulates new understanding
- **Guidance patterns** - When user corrects or provides direction
- **Fact patterns** - When user explicitly marks info as important
- Filtered by quality: rejects trivial content, questions, skip phrases

### Shorthand Parsing
Recognizes emotional cues and maps them to presence module triggers:
- `hmm` -> uncertainty (WhisperCatch)
- `...` -> trailing thought (WhisperCatch)
- `fml` -> frustration (TALI)
- Emoji clusters, exclamation patterns, greeting detection

## Execution Engine

Natural language code execution from conversation (Natural Flow):
- **Intent detection** - Classifies user input as execution/file_op/data/chat
- **Code extraction** - Parses Python code blocks from text
- **Persistent context** - Variables survive across execution turns
- **Safe execution** - Timeout protection, stdout capture, error isolation

## Cortex (File Awareness)

Real-time filesystem monitoring with watchdog:
- Tracks `.py`, `.json`, `.md` file changes with debouncing
- LLM-based or simple file summarization
- Injects awareness into system prompt ("File X modified 2min ago")
- Session counter reset on startup

## LLM Providers

Multi-provider support with graceful SDK fallback:

| Provider | Models | SDK |
|----------|--------|-----|
| **OpenAI** (default) | gpt-4.1, gpt-4.1-mini | openai |
| **Anthropic** | claude-sonnet-4-20250514 | anthropic |
| **Mistral** | mistral-large-latest | mistralai |
| **Google** | gemini-2.5-pro | google-generativeai |

Config in `config/api_config.json`. LangChain enhanced chat available as optional wrapper.

## Architecture

```
Nexus/
├── nexus.py                          # Chat loop entry point (v3 - full integration)
├── config/
│   ├── profile.json                  # Personality definition (5 modules)
│   └── api_config.json               # Provider config (model, temp, LangChain flag)
├── apps/
│   └── nexus.py                      # Drone command handler (@nexus status/info)
├── handlers/
│   ├── system/
│   │   ├── llm_client.py             # Multi-provider LLM client
│   │   ├── langchain_interface.py    # LangChain enhanced chat wrapper
│   │   ├── config_loader.py          # API config loader with validation
│   │   ├── prompt_builder.py         # Rich prompt builder (7 sections)
│   │   └── ui.py                     # Rich terminal formatting
│   ├── memory/
│   │   ├── __init__.py               # Exports all memory functions
│   │   ├── chat_history.py           # 5-session rolling window
│   │   ├── pulse_manager.py          # Pulse tick counter
│   │   ├── knowledge_base.py         # Persistent facts (200 max)
│   │   ├── vector_memory.py          # ChromaDB via Memory Bank subprocess
│   │   ├── summary.py               # Session summary rollover (10 max)
│   │   ├── auto_knowledge.py         # Auto-knowledge extraction from conversation
│   │   └── shorthand_parser.py       # Emotional cue and tone detection
│   ├── skills/
│   │   ├── __init__.py               # Auto-discovery framework
│   │   ├── memory_ops.py             # Memory commands skill
│   │   ├── aipass_services.py        # Drone/ai_mail skill
│   │   ├── usage_monitor.py          # API usage tracking skill
│   │   └── session_awareness.py      # Session context skill
│   ├── execution/                    # Natural Flow execution engine
│   │   ├── __init__.py               # Package exports
│   │   ├── context.py               # Persistent execution environment
│   │   ├── intent.py                # Natural language intent detection
│   │   └── runner.py                # Code extraction and execution
│   ├── cortex/                       # File awareness system
│   │   ├── __init__.py               # Package exports
│   │   ├── watcher.py               # Filesystem event detection (watchdog)
│   │   └── summarizer.py            # File change summarization
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
│   ├── cortex.json                   # File awareness state
│   └── vectors/                      # Vector memory storage
├── tests/
│   ├── test_memory.py                # Memory layer tests
│   ├── test_proxy.py                 # Proxy startup tests
│   ├── test_skills.py                # Skill discovery tests
│   ├── test_integration.py           # Full system integration tests
│   ├── test_execution.py             # Execution engine tests
│   ├── test_cortex.py                # Cortex file awareness tests
│   └── test_auto_knowledge.py        # Auto-knowledge & shorthand tests
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

The rich system prompt is profile-driven with 7 context layers (~764-2500 tokens) including identity, session, knowledge, memory, cortex awareness, execution context, and shorthand recognition. Every component is optional with graceful fallback.

## Development

Completed plans: FPLAN-0299 (Revival), FPLAN-0304 (Integration), FPLAN-0357 (V1 Feature Transfer)
Run tests: `python3 -m pytest tests/ -v`
Test count: 48 tests (all passing)
