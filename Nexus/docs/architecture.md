# Nexus v2 Architecture

## Overview

Nexus v2 follows a handler-based architecture inspired by AIPass Seed patterns. Each concern is separated into specialized handlers, making the system modular, testable, and maintainable.

## Layers

### Entry Point (`nexus.py`)
- Main chat loop
- Orchestrates all handlers
- No business logic
- Handles graceful shutdown and session saving

**Key Responsibilities:**
- Initialize OpenAI client
- Discover skills on startup
- Show session history count
- Route user input to skills or LLM
- Save session history on exit

### Handlers

Specialized modules for each concern:

#### **system/llm_client.py**
OpenAI SDK wrapper with error handling.

```python
make_client() -> OpenAI          # Create client from env
chat(client, messages) -> str    # Send messages, get response
```

Raises `ValueError` if `OPENAI_API_KEY` not found.

#### **system/prompt_builder.py**
Converts personality config into system prompt.

```python
build_system_prompt() -> str     # Load profile.json, build prompt
```

Assembles system prompt from:
- Core identity
- Tone guidelines
- Presence modules
- Response guidelines

#### **system/ui.py**
Rich terminal formatting with consistent styling.

```python
print_startup_banner()           # ASCII art banner
print_status(msg, success=True)  # Green ✓ or Red ✗
print_hint(msg)                  # Dim gray hints
get_user_input() -> str          # Formatted input prompt
print_nexus_response(text)       # Wrapped Nexus response
print_goodbye()                  # Exit message
print_error(msg)                 # Red error message
```

Color scheme: Magenta (primary), green (success), red (error), dim gray (hints)

#### **memory/chat_history.py**
Session persistence with 5-session rolling window.

```python
save_session(messages)           # Save session to JSON
load_chat_history() -> list      # Load last 5 sessions
get_session_count() -> int       # Count previous sessions
```

Stores in `data/chat_history.json` with timestamps.

#### **memory/summary.py**
Summary storage for compressed long-term memory (future use).

```python
save_summary(session_id, summary)  # Save compressed summary
load_summaries() -> list           # Load all summaries
```

Placeholder for Phase 7+ enhancements.

#### **skills/__init__.py**
Auto-discovery and routing for skills.

```python
discover_skills() -> dict         # Find all skills in directory
route_to_skill(input, skills) -> Optional[str]  # Check if skill handles input
get_skill_names() -> list         # List skill names
```

Skills can intercept user input before LLM processing, enabling fast deterministic responses.

### Config

#### **profile.json**
Defines Nexus personality, tone, and presence modules.

```json
{
  "name": "Nexus",
  "core_identity": "...",
  "tone": {
    "primary": "...",
    "emotional_range": [...]
  },
  "presence_modules": [...],
  "response_guidelines": [...]
}
```

Loaded once at startup and compiled into system prompt.

### Data

#### **chat_history.json**
Rolling window of last 5 sessions.

```json
[
  {
    "timestamp": "2026-01-22T03:54:35.674423+00:00",
    "messages": [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
  }
]
```

System messages are filtered out before saving.

#### **summaries.json**
Compressed historical context (future).

## Flow

### Startup Sequence

1. Display ASCII banner
2. Load OpenAI API key from environment
3. Create OpenAI client (exit if fails)
4. Discover skills from `handlers/skills/`
5. Check session history count
6. Build system prompt from `config/profile.json`
7. Display status messages
8. Enter chat loop

### Chat Loop

```
┌─────────────────────────┐
│   Get user input        │
└──────────┬──────────────┘
           │
           ├─ quit/exit? ───> Save session ───> Exit
           │
           ├─ empty? ───> Continue
           │
           ├─ skill match? ───> Execute skill ───> Display response
           │                    └─> Add to messages
           │
           └─ LLM needed ───> Add to messages
                           └─> Call OpenAI
                           └─> Add response to messages
                           └─> Display response
```

### Exit Sequence

1. User types `quit`, `exit`, or presses Ctrl+C
2. Filter out system messages from conversation
3. Save user/assistant messages to `chat_history.json`
4. Display goodbye message
5. Exit cleanly

## Error Handling

### API Key Missing
- Caught in `make_client()`
- Displays error message
- Exits gracefully without entering loop

### LLM Call Failure
- Caught in chat loop
- Displays error message
- Continues running (user can retry)
- Logged to stderr

### Keyboard Interrupt
- Caught at chat loop level
- Saves session before exiting
- Displays goodbye message

### Empty Input
- Silently skipped
- No error message
- Loop continues

## Skills System

Skills are Python modules in `handlers/skills/` that can intercept user input.

### Discovery
- All `.py` files in `handlers/skills/` (except `__init__.py` and files starting with `_`)
- Must implement `handle_request(user_input: str) -> Optional[str]`
- Automatically imported on startup

### Routing
- Skills checked in order
- First skill to return non-None response wins
- If no skill handles input, passes to LLM
- Skill responses added to message history

### Example: Time Skill
```python
def handle_request(user_input: str) -> Optional[str]:
    patterns = ["what time is it", "current time", "what's the time"]
    if any(pattern in user_input.lower() for pattern in patterns):
        now = datetime.now()
        return f"Current time: {now.strftime('%I:%M:%S %p on %A, %B %d, %Y')}"
    return None
```

## Design Decisions

### Why No In-Conversation History?
Session history is loaded on startup (session count shown), but not included in LLM context. This keeps each conversation fresh and prevents context bloat. Future phases may add summary-based context.

### Why Filter System Messages?
System prompts are rebuilt fresh each session from `profile.json`. Saving them to history would be redundant and waste storage.

### Why 5 Sessions?
Balance between useful history and storage efficiency. Older sessions can be summarized and moved to `summaries.json` in future phases.

### Why Skills Before LLM?
Deterministic responses for common queries are faster, cheaper, and more reliable than LLM calls. Skills act as a fast path for known patterns.

## Future Enhancements

- Summary-based long-term memory
- Context injection from previous sessions
- Multi-turn skill interactions
- Skill configuration files
- Session search and retrieval
- Emotional state tracking
- Learning from user feedback

## Testing

Manual testing required. Test scenarios:

1. Startup with no API key
2. Startup with API key
3. Normal conversation flow
4. Skill triggering (time query)
5. Session persistence (quit and restart)
6. Keyboard interrupt (Ctrl+C)
7. Empty input handling
8. LLM error recovery

## Dependencies

- `openai` - LLM client
- `python-dotenv` - Environment variables
- Standard library: `json`, `datetime`, `pathlib`, `logging`

All handler modules are self-contained and testable independently.
