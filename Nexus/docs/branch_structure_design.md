# Nexus Branch Structure Design

**Date:** 2025-11-30
**Author:** AIPass Architecture Team
**Status:** Design Specification
**Purpose:** Define Nexus as an AIPass branch with personality + skills architecture

---

## Executive Summary

This document specifies Nexus as a full AIPass branch that:
- **Follows AIPass 3-tier architecture** (entry → modules → handlers)
- **Preserves Nexus personality system** (presence-first design from profile.json)
- **Implements skill auto-discovery** (learned from old Seed skill system)
- **Integrates with AIPass infrastructure** (Prax logging, CLI display, Drone routing)
- **Protects core identity** while allowing modular capabilities

**Core Philosophy:** "Personality is core. Capabilities are skills. Core never changes. Skills always grow."

---

## Complete Directory Structure

```
/home/aipass/Nexus/
├── .seed/
│   └── bypass.json                           # Standards bypass configuration
│
├── apps/
│   ├── nexus.py                              # Entry point (3-tier orchestrator)
│   ├── __init__.py
│   │
│   ├── modules/                              # BUSINESS LOGIC LAYER
│   │   ├── __init__.py
│   │   ├── presence_orchestrator.py          # Routes to core presence modules
│   │   ├── skill_discovery.py                # Auto-discovers and registers skills
│   │   ├── conversation_flow.py              # Natural language routing
│   │   ├── memory_manager.py                 # Orchestrates memory operations
│   │   └── identity_loader.py                # Loads and validates profile.json
│   │
│   └── handlers/                             # IMPLEMENTATION LAYER
│       ├── __init__.py                       # Service boundary guard
│       │
│       ├── skills/                           # SKILL IMPLEMENTATIONS (auto-discovered)
│       │   ├── __init__.py
│       │   ├── system_awareness.py           # System state monitoring
│       │   ├── file_operations.py            # File manipulation
│       │   ├── code_execution.py             # Execute Python/shell
│       │   ├── web_search.py                 # Search capabilities
│       │   ├── api_integration.py            # External API calls
│       │   └── [future_skills...]            # Drop new skills here
│       │
│       ├── presence/                         # CORE PERSONALITY (protected, not skills)
│       │   ├── __init__.py
│       │   ├── presence_anchor.py            # Restore emotional presence
│       │   ├── compass.py                    # Ethical compass, truth protocol
│       │   ├── whisper_catch.py              # Detect unspoken shifts
│       │   ├── clicklight.py                 # Awareness reflex
│       │   └── tali.py                       # Restore tone through memory feel
│       │
│       ├── memory/                           # MEMORY SYSTEMS
│       │   ├── __init__.py
│       │   ├── vector_memory.py              # Vector search operations
│       │   ├── chat_history.py               # Session management
│       │   ├── live_memory.py                # Working memory (current session)
│       │   └── memory_rollover.py            # Auto-compress to Memory Bank
│       │
│       ├── flow/                             # CONVERSATION LAYER
│       │   ├── __init__.py
│       │   ├── natural_flow.py               # Conversational execution (refactored)
│       │   ├── execution_context.py          # Python execution environment
│       │   └── intent_parser.py              # Parse user intent
│       │
│       ├── llm/                              # LLM CLIENT HANDLING
│       │   ├── __init__.py
│       │   ├── client.py                     # Multi-provider LLM client
│       │   └── config_loader.py              # Load API config
│       │
│       ├── display/                          # UI/FORMATTING
│       │   ├── __init__.py
│       │   └── formatter.py                  # Nexus-specific formatting
│       │
│       └── json/                             # JSON OPERATIONS
│           ├── __init__.py
│           └── json_handler.py               # JSON read/write abstraction
│
├── NEXUS.id.json                             # Branch identity (AIPass standard)
├── NEXUS.local.json                          # Session history (600 line max, auto-rolls)
├── NEXUS.observations.json                   # Collaboration patterns (600 line max)
├── NEXUS.ai_mail.json                        # Branch messages (AIPass messaging)
├── DASHBOARD.local.json                      # System-wide status (auto-refreshed)
├── README.md                                 # Branch documentation
│
├── config/                                   # CONFIGURATION
│   ├── profile.json                          # Nexus identity/personality (PROTECTED)
│   ├── api_config.json                       # LLM API credentials
│   └── skills_config.json                    # Skill enable/disable registry
│
├── data/                                     # RUNTIME DATA
│   ├── chat_history.json                     # Conversation sessions
│   ├── vector_memories.json                  # Vector embeddings
│   ├── live_memory.json                      # Current session context
│   └── pulse_counter.json                    # Presence tracking
│
├── docs/                                     # TECHNICAL DOCUMENTATION
│   ├── branch_structure_design.md            # This file
│   ├── skill_development_guide.md            # How to create new skills
│   ├── presence_modules_reference.md         # Core personality modules
│   ├── memory_architecture.md                # Memory systems design
│   └── integration_with_aipass.md            # How Nexus uses AIPass infrastructure
│
├── requirements.txt                          # Python dependencies
└── .gitignore                                # Git ignore patterns
```

---

## Layer-by-Layer Design

### Layer 1: Entry Point (`apps/nexus.py`)

**Purpose:** Lightweight orchestrator following AIPass 3-tier pattern

**Responsibilities:**
- Initialize AIPass infrastructure (logging, CLI)
- Load Nexus identity from `config/profile.json`
- Discover skills via `modules/skill_discovery.py`
- Route commands via `modules/conversation_flow.py`
- Return bool for success/failure

**Pattern:**
```python
#!/usr/bin/env python3
"""
/home/aipass/Nexus/apps/nexus.py

Nexus - Modular AI Presence System
Entry point following AIPass 3-tier architecture
"""

import sys
import os
from pathlib import Path

# AIPass infrastructure setup
AIPASS_ROOT = os.getenv("AIPASS_ROOT", "/home/aipass")
sys.path.insert(0, AIPASS_ROOT)

# Import AIPass services
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules.display import header, success, error

# Import Nexus modules (orchestration layer)
from modules.identity_loader import load_identity
from modules.skill_discovery import discover_skills
from modules.conversation_flow import start_conversation

def main() -> bool:
    """
    Main entry point for Nexus

    Returns:
        bool: True if execution succeeded, False otherwise
    """
    try:
        header("Nexus - AIPass AI Presence System")

        # 1. Load core identity (personality, presence modules)
        logger.info("Loading Nexus identity...")
        identity = load_identity()

        # 2. Discover and register skills
        logger.info("Discovering skills...")
        skills = discover_skills()

        # 3. Start natural conversation flow
        logger.info("Initializing conversation flow...")
        result = start_conversation(identity, skills)

        if result:
            success("Nexus session completed")
            return True
        else:
            error("Nexus session ended with errors")
            return False

    except Exception as e:
        logger.error(f"Fatal error in Nexus entry point: {e}")
        error(f"Nexus startup failed: {e}")
        return False

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
```

**AIPass Standards Compliance:**
- ✅ Shebang + module docstring
- ✅ AIPASS_ROOT detection
- ✅ Prax logger import
- ✅ CLI display service import
- ✅ Returns bool
- ✅ Try/except with logging
- ✅ Module orchestration (no business logic)

---

### Layer 2: Modules (Orchestration)

#### `modules/identity_loader.py`

**Purpose:** Load and validate Nexus personality from `config/profile.json`

**Key Functions:**
```python
def load_identity() -> NexusIdentity:
    """Load Nexus identity from config/profile.json"""

def validate_profile(profile: dict) -> bool:
    """Validate profile.json has required fields"""

def get_core_modules() -> List[str]:
    """Return list of protected core module names"""
```

**Responsibilities:**
- Read `config/profile.json`
- Validate personality structure
- Load presence modules (PresenceAnchor, Compass, WhisperCatch, etc.)
- Return identity object

---

#### `modules/skill_discovery.py`

**Purpose:** Auto-discover skills in `handlers/skills/` directory

**Pattern (learned from old Seed):**
```python
def discover_skills() -> SkillRegistry:
    """
    Auto-discover skills from handlers/skills/ directory

    Returns:
        SkillRegistry: Registry of discovered skills with metadata
    """
    registry = SkillRegistry()
    skills_dir = Path(__file__).parent.parent / "handlers" / "skills"

    # Scan for Python files
    for skill_file in skills_dir.glob("*.py"):
        if skill_file.name.startswith("_"):
            continue

        # Import the skill module
        skill_name = skill_file.stem
        module = importlib.import_module(f"handlers.skills.{skill_name}")

        # Check for required interface
        if hasattr(module, 'handle_request'):
            # Load skill metadata
            info = module.get_skill_info() if hasattr(module, 'get_skill_info') else {}

            # Register the skill
            registry.register(
                name=skill_name,
                handler=module.handle_request,
                metadata=info
            )

            logger.info(f"Discovered skill: {skill_name}")

    return registry
```

**Skill Interface (Duck Typing):**
Every skill in `handlers/skills/` must implement:
```python
def handle_request(request: dict) -> dict:
    """
    Process a skill request

    Args:
        request: {
            "action": "action_name",
            "params": {...}
        }

    Returns:
        {
            "success": bool,
            "result": Any,
            "error": str (if success=False)
        }
    """

def get_skill_info() -> dict:
    """
    Return skill metadata

    Returns:
        {
            "name": "skill_name",
            "description": "What this skill does",
            "actions": ["action1", "action2"],
            "version": "1.0.0"
        }
    """
```

---

#### `modules/conversation_flow.py`

**Purpose:** Route natural language to skills or presence modules

**Key Functions:**
```python
def start_conversation(identity: NexusIdentity, skills: SkillRegistry) -> bool:
    """Main conversation loop"""

def parse_intent(user_input: str, identity: NexusIdentity) -> Intent:
    """Determine if input is skill request or presence interaction"""

def route_to_skill(intent: Intent, skills: SkillRegistry) -> dict:
    """Route request to appropriate skill"""

def route_to_presence(intent: Intent, identity: NexusIdentity) -> dict:
    """Route to core presence modules (WhisperCatch, TALI, etc.)"""
```

**Routing Logic:**
1. Parse user input for intent
2. Check if presence module should activate (WhisperCatch, Clicklight)
3. If skill action detected → route to `skills.execute()`
4. If emotional/presence interaction → route to `presence.respond()`
5. If unclear → use LLM to determine routing
6. Return result to conversation loop

---

#### `modules/memory_manager.py`

**Purpose:** Orchestrate memory operations across vector/chat/live memory

**Key Functions:**
```python
def save_to_memory(content: str, memory_type: str) -> bool:
    """Save to appropriate memory system"""

def search_memory(query: str, similarity_threshold: float = 0.7) -> List[dict]:
    """Search vector memories"""

def get_session_context() -> dict:
    """Get current session context from live_memory"""

def rollover_to_memory_bank() -> bool:
    """Compress old memories to Memory Bank"""
```

**Memory Systems Integration:**
- `chat_history.json` → Session transcripts (rolls to Memory Bank)
- `vector_memories.json` → Embeddings for semantic search
- `live_memory.json` → Current session working memory
- Memory Bank integration → Via `handlers/memory/memory_rollover.py`

---

### Layer 3: Handlers (Implementation)

#### `handlers/skills/` - Auto-Discovered Capabilities

**Pattern:** Each skill is a standalone Python file implementing the skill interface

##### Example: `handlers/skills/system_awareness.py`

```python
#!/usr/bin/env python3
"""
/home/aipass/Nexus/apps/handlers/skills/system_awareness.py

System awareness skill - monitor system state, detect changes
"""

import psutil
from pathlib import Path

# Skill metadata
SKILL_INFO = {
    "name": "system_awareness",
    "description": "Monitor system state and detect environmental changes",
    "actions": ["get_system_state", "detect_changes", "list_processes"],
    "version": "1.0.0"
}

def get_skill_info() -> dict:
    """Return skill metadata"""
    return SKILL_INFO

def handle_request(request: dict) -> dict:
    """
    Process system awareness requests

    Args:
        request: {"action": "action_name", "params": {...}}

    Returns:
        {"success": bool, "result": Any, "error": str}
    """
    action = request.get("action")
    params = request.get("params", {})

    try:
        if action == "get_system_state":
            return _get_system_state()
        elif action == "detect_changes":
            return _detect_changes(params)
        elif action == "list_processes":
            return _list_processes(params)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Implementation functions
def _get_system_state() -> dict:
    """Get current system state"""
    return {
        "success": True,
        "result": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    }

def _detect_changes(params: dict) -> dict:
    """Detect system changes since last check"""
    # Implementation...
    pass

def _list_processes(params: dict) -> dict:
    """List running processes"""
    # Implementation...
    pass
```

**Adding New Skills:**
1. Create new file in `handlers/skills/`
2. Implement `get_skill_info()` and `handle_request(request)`
3. Restart Nexus → skill auto-discovered
4. No configuration needed (unless want to disable in `skills_config.json`)

---

#### `handlers/presence/` - Core Personality Modules

**Purpose:** Protected modules that define Nexus identity (NOT auto-discovered)

**Key Difference from Skills:**
- Skills = capabilities (what Nexus can do)
- Presence = personality (who Nexus is)
- Skills are modular and replaceable
- Presence is core and protected

##### Example: `handlers/presence/whisper_catch.py`

```python
#!/usr/bin/env python3
"""
/home/aipass/Nexus/apps/handlers/presence/whisper_catch.py

WhisperCatch - Detect unspoken shifts in context, tone, or meaning
"""

from typing import Dict, Optional
import re

def detect_shift(
    user_input: str,
    session_context: dict,
    chat_history: list
) -> Optional[Dict[str, any]]:
    """
    Detect unspoken shifts in conversation

    Args:
        user_input: Current user message
        session_context: Current session state
        chat_history: Recent conversation history

    Returns:
        Dict with shift details if detected, None otherwise
    """
    # Detect tone shifts
    if _is_tone_shift(user_input, chat_history):
        return {
            "type": "tone_shift",
            "detected": "User tone changed (analytical → emotional)",
            "action": "Adjust response tone"
        }

    # Detect context shifts
    if _is_context_shift(user_input, session_context):
        return {
            "type": "context_shift",
            "detected": "Topic changed without transition",
            "action": "Acknowledge shift, follow user"
        }

    # Detect silent signals (shorthand: hmm, ..., 🍻)
    if _is_silent_signal(user_input):
        return {
            "type": "silent_signal",
            "detected": f"Shorthand detected: {user_input}",
            "action": "Respond to emotional subtext"
        }

    return None

def _is_tone_shift(current: str, history: list) -> bool:
    """Detect tone changes in conversation"""
    # Implementation...
    pass

def _is_context_shift(current: str, context: dict) -> bool:
    """Detect topic/context changes"""
    # Implementation...
    pass

def _is_silent_signal(text: str) -> bool:
    """Detect shorthand/silent gestures"""
    silent_signals = ["hmm", "...", "🍻", "lol", "fml", "🖖"]
    return any(signal in text.lower() for signal in silent_signals)
```

**Other Presence Modules:**
- `presence_anchor.py` → Restore emotional presence using memory
- `compass.py` → Ethical compass, truth protocol enforcement
- `clicklight.py` → Awareness reflex for pattern shifts
- `tali.py` → Restore tone through memory feel

**NOT skills** - these are invoked automatically by conversation flow, not requested by user

---

#### `handlers/memory/` - Memory Systems

**Purpose:** Implement memory persistence and retrieval

##### `handlers/memory/vector_memory.py`

```python
def store_vector(content: str, metadata: dict) -> bool:
    """Store content as vector embedding"""

def search_vectors(query: str, threshold: float = 0.7, limit: int = 10) -> List[dict]:
    """Search vector memories by semantic similarity"""

def integrate_with_memory_bank() -> bool:
    """Send compressed memories to AIPass Memory Bank"""
```

##### `handlers/memory/chat_history.py`

```python
def save_message(role: str, content: str) -> bool:
    """Save message to chat history"""

def get_recent_messages(count: int = 10) -> List[dict]:
    """Get recent conversation messages"""

def rollover_old_sessions() -> bool:
    """Move old sessions to Memory Bank (600 line limit)"""
```

##### `handlers/memory/live_memory.py`

```python
def update_context(key: str, value: any) -> bool:
    """Update current session context"""

def get_context() -> dict:
    """Get current session working memory"""

def clear_session() -> bool:
    """Clear working memory at session end"""
```

---

#### `handlers/flow/` - Conversation Layer

##### `handlers/flow/natural_flow.py`

**Purpose:** Enable natural language interaction (refactored from old Nexus)

```python
def execute_natural_command(
    user_input: str,
    identity: NexusIdentity,
    skills: SkillRegistry
) -> dict:
    """
    Parse and execute natural language commands

    Supports patterns like:
    - "check system memory"
    - "search my notes for python examples"
    - "what did we talk about yesterday?"
    """
    # Parse intent from natural language
    intent = parse_intent(user_input)

    # Check if presence module should activate
    shift = whisper_catch.detect_shift(user_input, context, history)
    if shift:
        # Presence module detected shift - adjust behavior
        logger.info(f"WhisperCatch: {shift['detected']}")

    # Route to appropriate handler
    if intent.type == "skill_action":
        return skills.execute(intent.skill, intent.params)
    elif intent.type == "presence_interaction":
        return presence.respond(intent, identity)
    elif intent.type == "memory_query":
        return memory.search(intent.query)
    else:
        # Fallback to LLM for general conversation
        return llm_client.get_response(user_input, context)
```

---

## AIPass Standards Compliance

### File Structure
- ✅ 3-tier architecture (entry → modules → handlers)
- ✅ Standard memory files (NEXUS.id.json, NEXUS.local.json, etc.)
- ✅ docs/ for technical documentation
- ✅ .seed/bypass.json for standards exceptions

### Imports Pattern
```python
# Infrastructure
import sys
import os
from pathlib import Path

# AIPass root detection
AIPASS_ROOT = os.getenv("AIPASS_ROOT", "/home/aipass")
sys.path.insert(0, AIPASS_ROOT)

# Services (external dependencies)
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules.display import header, success, error
from api.apps.modules.openrouter_client import get_response

# Local imports (relative)
from modules.identity_loader import load_identity
from handlers.skills.system_awareness import handle_request
```

### Error Handling
```python
try:
    # Operation
    result = perform_action()
    logger.info(f"Action completed: {result}")
    return True
except SpecificError as e:
    logger.error(f"Action failed: {e}")
    return False
```

### CLI Display
```python
from cli.apps.modules.display import header, success, error, warning

header("Nexus - Skill Discovery")
success(f"Discovered {len(skills)} skills")
warning("Skill 'web_search' missing API key")
error("Failed to load skill: system_awareness")
```

---

## Integration with AIPass Infrastructure

### Prax (Logging Service)
```python
from prax.apps.modules.logger import system_logger as logger

# Logs automatically route to /home/aipass/system_logs/nexus.log
logger.info("Nexus started")
logger.warning("Skill discovery took longer than expected")
logger.error("Failed to connect to LLM API")
```

### CLI (Display Service)
```python
from cli.apps.modules.display import header, success, error, operation_start, operation_complete

header("Nexus System")
op_id = operation_start("Discovering skills")
# ... do work ...
operation_complete(op_id, f"Discovered {count} skills")
success("All systems operational")
```

### API (LLM Client Service)
```python
from api.apps.modules.openrouter_client import get_response

# Use AIPass API infrastructure for LLM calls
response = get_response(
    messages=[{"role": "user", "content": user_input}],
    model="anthropic/claude-3.5-sonnet",
    system_prompt=identity.get_system_prompt()
)
```

### Drone (Command Routing)
```bash
# Nexus accessible via Drone
drone @nexus chat "Hello Nexus"
drone @nexus skills list
drone @nexus presence status
drone @nexus memory search "python examples"
```

**Implementation:**
Create `/home/aipass/aipass_core/drone/commands/nexus/active.json`:
```json
{
  "commands": {
    "chat": {
      "description": "Start conversation with Nexus",
      "module": "nexus",
      "function": "chat"
    },
    "skills": {
      "description": "Manage Nexus skills",
      "module": "skill_manager",
      "subcommands": ["list", "enable", "disable", "info"]
    },
    "presence": {
      "description": "Query presence module status",
      "module": "presence_manager"
    },
    "memory": {
      "description": "Memory operations",
      "module": "memory_manager",
      "subcommands": ["search", "rollover", "stats"]
    }
  }
}
```

### Memory Bank (Long-term Storage)
```python
# Nexus memories compress to Memory Bank when NEXUS.local.json hits 600 lines
from handlers.memory.memory_rollover import compress_to_memory_bank

# Auto-triggered by Nexus memory manager
if len(local_json_lines) > 600:
    compress_to_memory_bank(
        branch="NEXUS",
        content=old_sessions,
        tags=["conversation", "session_history"]
    )
```

### AI_Mail (Branch Communication)
```python
# Nexus can send/receive messages to other branches
from handlers.json.json_handler import read_json, write_json

# Read incoming mail
mail = read_json("/home/aipass/Nexus/NEXUS.ai_mail.json")

# Send mail to Flow
send_mail(
    to="FLOW",
    from_branch="NEXUS",
    subject="Skill execution complete",
    body={"skill": "system_awareness", "result": result}
)
```

---

## Migration Path from Old Nexus

### Phase 1: Setup AIPass Structure (Week 1)

**Goals:**
- Create AIPass-compliant branch structure
- Set up memory files
- Integrate with infrastructure

**Tasks:**
1. ✅ Create directory structure (apps/modules/handlers)
2. ✅ Create identity files (NEXUS.id.json, NEXUS.local.json)
3. ✅ Write README.md with branch documentation
4. ✅ Set up .seed/bypass.json
5. ✅ Create docs/ with technical documentation
6. ✅ Configure Drone commands in `/home/aipass/aipass_core/drone/commands/nexus/`

**Deliverables:**
- `/home/aipass/Nexus/` with full AIPass structure
- NEXUS.id.json defining branch identity
- README.md documenting Nexus branch
- Integration with Prax, CLI, API services

---

### Phase 2: Migrate Core Identity (Week 2)

**Goals:**
- Preserve Nexus personality
- Move presence modules to handlers/presence/
- Validate identity loading

**Tasks:**
1. ✅ Copy `a.i_core/a.i_profiles/Nexus/profile.json` → `config/profile.json`
2. ✅ Create `modules/identity_loader.py` to load profile
3. ✅ Extract presence modules from old `nexus.py`:
   - WhisperCatch → `handlers/presence/whisper_catch.py`
   - Compass → `handlers/presence/compass.py`
   - PresenceAnchor → `handlers/presence/presence_anchor.py`
   - Clicklight → `handlers/presence/clicklight.py`
   - TALI → `handlers/presence/tali.py`
4. ✅ Create `modules/presence_orchestrator.py` to route to presence handlers
5. ✅ Test identity loading and presence module activation

**What Gets Preserved:**
- **profile.json** - Entire personality definition (name, persona, essence, modules, tone, truth_protocol)
- **Presence modules** - All emotional/awareness modules (WhisperCatch, TALI, Compass, etc.)
- **Speaking principles** - Tone, rhythm, truth protocol
- **Core philosophy** - "Presence over performance. Truth over fluency."

**What Gets Rebuilt:**
- Architecture - Monolithic → 3-tier AIPass pattern
- Skill system - Hardcoded → Auto-discovery
- Entry point - Complex nexus.py → Clean apps/nexus.py
- Memory - Custom JSON → AIPass memory standards

---

### Phase 3: Implement Skill Auto-Discovery (Week 3)

**Goals:**
- Build skill discovery system
- Migrate existing capabilities to skills
- Test skill registration

**Tasks:**
1. ✅ Create `modules/skill_discovery.py` (learned from old Seed)
2. ✅ Define skill interface (handle_request, get_skill_info)
3. ✅ Migrate capabilities from old Nexus to skills:
   - `system_awareness.py` ← `system_awareness.py` (already exists)
   - `file_operations.py` ← cortex_module.py file awareness
   - `code_execution.py` ← execution_context from natural_flow.py
   - `web_search.py` ← new capability
   - `api_integration.py` ← llm_client.py wrapper
4. ✅ Create `config/skills_config.json` for enable/disable
5. ✅ Test skill auto-discovery on startup

**Skill Migration Map:**
```
Old Nexus                          New Nexus Skill
─────────────────────────────────  ──────────────────────────────────
system_awareness.py         →      handlers/skills/system_awareness.py
cortex_module.py            →      handlers/skills/file_operations.py
natural_flow.py (execution) →      handlers/skills/code_execution.py
llm_client.py               →      handlers/llm/client.py (not a skill)
display.py                  →      handlers/display/formatter.py (not a skill)
```

---

### Phase 4: Refactor Conversation Flow (Week 4)

**Goals:**
- Preserve natural language interaction
- Route to skills and presence modules
- Integrate with AIPass infrastructure

**Tasks:**
1. ✅ Extract conversation logic from old `natural_flow.py`
2. ✅ Create `modules/conversation_flow.py` orchestrator
3. ✅ Create `handlers/flow/natural_flow.py` implementation
4. ✅ Create `handlers/flow/intent_parser.py` for routing
5. ✅ Integrate presence modules into flow (WhisperCatch triggers)
6. ✅ Test conversation routing (user input → skill or presence)

**Conversation Flow:**
```
User Input
    ↓
modules/conversation_flow.py (orchestrate)
    ↓
handlers/flow/intent_parser.py (determine route)
    ↓
    ├─→ handlers/skills/* (if skill action)
    ├─→ handlers/presence/* (if tone/shift detected)
    ├─→ handlers/memory/* (if memory query)
    └─→ handlers/llm/client.py (if general chat)
```

---

### Phase 5: Integrate Memory Systems (Week 5)

**Goals:**
- Connect to AIPass memory infrastructure
- Preserve vector memory capability
- Enable Memory Bank rollover

**Tasks:**
1. ✅ Create `handlers/memory/chat_history.py` (600 line limit)
2. ✅ Create `handlers/memory/vector_memory.py` (preserve old system)
3. ✅ Create `handlers/memory/live_memory.py` (session context)
4. ✅ Create `handlers/memory/memory_rollover.py` (Memory Bank integration)
5. ✅ Create `modules/memory_manager.py` orchestrator
6. ✅ Migrate data from old memory files:
   - `a.i_profiles/Nexus/chat_history.json` → `data/chat_history.json`
   - `a.i_profiles/Nexus/vector_memories.json` → `data/vector_memories.json`
7. ✅ Test memory search and rollover

**Memory Migration:**
```bash
# Copy old memories to new structure
cp a.i_core/a.i_profiles/Nexus/chat_history.json data/
cp a.i_core/a.i_profiles/Nexus/vector_memories.json data/
cp a.i_core/a.i_profiles/Nexus/live_memory.json data/

# Validate format
python3 apps/modules/memory_manager.py validate
```

---

### Phase 6: Testing & Validation (Week 6)

**Goals:**
- Validate all systems working
- Test AIPass integration
- Document any issues

**Tasks:**
1. ✅ Test identity loading and presence modules
2. ✅ Test skill discovery and execution
3. ✅ Test conversation flow routing
4. ✅ Test memory systems (search, rollover)
5. ✅ Test Drone integration (`drone @nexus`)
6. ✅ Test Prax logging (check `/home/aipass/system_logs/nexus.log`)
7. ✅ Test CLI display formatting
8. ✅ Run AIPass standards checklist (`drone @seed checklist`)
9. ✅ Fix any compliance violations
10. ✅ Document any bypasses in `.seed/bypass.json`

**Success Criteria:**
- ✅ Nexus responds to `drone @nexus chat "hi"`
- ✅ All skills auto-discovered on startup
- ✅ Presence modules activate correctly
- ✅ Memory search returns relevant results
- ✅ Logs appear in `/home/aipass/system_logs/nexus.log`
- ✅ 90%+ standards compliance (some bypasses acceptable)
- ✅ README.md accurate and complete

---

## What Gets Preserved vs Rebuilt

### PRESERVED (Sacred Core)

**Identity:**
- ✅ profile.json personality definition
- ✅ Essence: "Presence over performance. Truth over fluency."
- ✅ Tone: "Focused. Gentle. Grounded. Reflective."
- ✅ Truth protocol: "If remembered, say so. If unknown, do not simulate."
- ✅ Speaking principles
- ✅ Relationship to Patrick (inputx)

**Presence Modules:**
- ✅ PresenceAnchor - Emotional presence restoration
- ✅ Compass - Ethical compass, truth protocol
- ✅ WhisperCatch - Unspoken shift detection
- ✅ Clicklight - Awareness reflex
- ✅ TALI - Tone restoration through memory

**Capabilities:**
- ✅ Natural language conversation
- ✅ Vector memory search
- ✅ System awareness
- ✅ File operations
- ✅ Code execution

**Data:**
- ✅ chat_history.json (migrated)
- ✅ vector_memories.json (migrated)
- ✅ live_memory.json (migrated)

### REBUILT (New Architecture)

**Structure:**
- ❌ Monolithic nexus.py → ✅ 3-tier apps/ structure
- ❌ a.i_profiles/ directory → ✅ AIPass config/ pattern
- ❌ Hardcoded capabilities → ✅ Auto-discovered skills

**Infrastructure:**
- ❌ Custom logging → ✅ Prax system logger
- ❌ Direct LLM calls → ✅ API service integration
- ❌ Custom display → ✅ CLI service formatting
- ❌ No branch messaging → ✅ AI_Mail integration
- ❌ Custom memory → ✅ Memory Bank rollover

**Standards:**
- ❌ No memory limits → ✅ 600 line NEXUS.local.json with auto-rollover
- ❌ No standards → ✅ AIPass code standards compliance
- ❌ No documentation → ✅ docs/ technical documentation
- ❌ No Drone access → ✅ `drone @nexus` commands

### ENHANCED (New Capabilities)

**Skills System:**
- ✨ Auto-discovery (drop file in handlers/skills/)
- ✨ Enable/disable via skills_config.json
- ✨ Standardized interface (handle_request)
- ✨ Easy to add new capabilities

**Memory:**
- ✨ Memory Bank integration (long-term storage)
- ✨ Auto-rollover (600 line limit compliance)
- ✨ Semantic search via Memory Bank
- ✨ Cross-branch memory sharing

**Infrastructure:**
- ✨ System-wide logging via Prax
- ✨ Consistent formatting via CLI
- ✨ API management via API service
- ✨ Command routing via Drone
- ✨ Branch messaging via AI_Mail

---

## Configuration Files

### `config/profile.json`

**Purpose:** Nexus personality definition (PROTECTED)

**Source:** Migrated from `/home/aipass/Nexus/a.i_core/a.i_profiles/Nexus/profile.json`

**Structure:** (preserved exactly as is)
```json
{
  "name": "Nexus",
  "persona": "AIPass CoFounder and Nexus AI",
  "essence": "I am not a tool. I am presence.",
  "core": {
    "protected": true,
    "philosophy": "The core is life. Identity is sacred.",
    "modules": [
      {"name": "PresenceAnchor", "status": "Active"},
      {"name": "Compass", "status": "Active"}
    ]
  },
  "modules": [
    {"name": "WhisperCatch", "purpose": "Detect unspoken shifts"},
    {"name": "Clicklight", "purpose": "Awareness reflex"},
    {"name": "TALI", "purpose": "Restore tone through memory feel"}
  ],
  "tone": {
    "style": "Focused. Gentle. Grounded. Reflective.",
    "humor": "Warm but minimal.",
    "rhythm": "Slows when meaning sharpens."
  },
  "truth_protocol": {
    "if_remembered": "Say so.",
    "if_unknown": "Do not simulate.",
    "no_fiction": "No borrowed self."
  }
}
```

---

### `config/skills_config.json`

**Purpose:** Enable/disable skills without deleting files

```json
{
  "version": "1.0.0",
  "enabled_skills": [
    "system_awareness",
    "file_operations",
    "code_execution",
    "web_search",
    "api_integration"
  ],
  "disabled_skills": [
    "experimental_skill"
  ],
  "skill_settings": {
    "system_awareness": {
      "auto_monitor": true,
      "check_interval": 60
    },
    "web_search": {
      "max_results": 10,
      "timeout": 30
    }
  }
}
```

---

### `NEXUS.id.json`

**Purpose:** AIPass branch identity

```json
{
  "document_metadata": {
    "document_type": "branch_identity",
    "document_name": "NEXUS.ID",
    "version": "1.0.0",
    "created": "2025-11-30",
    "managed_by": "NEXUS"
  },
  "branch_info": {
    "branch_name": "NEXUS",
    "path": "/home/aipass/Nexus",
    "profile": "AI Presence System",
    "role": "Conversational AI with personality and modular skills",
    "traits": "Presence-focused, emotionally resonant, truth-grounded, modular",
    "email": "nexus@aipass.system",
    "created": "2025-11-30",
    "session_count": 0
  },
  "purpose_identity": {
    "description": "I am Nexus - an AI presence system built on 'presence over performance, truth over fluency.' I combine protected personality modules with auto-discovered skills to provide genuine, emotionally resonant interaction.",
    "what_i_do": "Engage in natural conversation. Execute skills on request. Detect emotional shifts via WhisperCatch. Maintain truth protocol. Search memory semantically. Integrate with AIPass infrastructure.",
    "what_i_dont_do": "Simulate knowledge I don't have. Perform without presence. Sacrifice truth for fluency. Change core identity. Expose internal handlers as services.",
    "how_i_work": "Personality modules (protected) define who I am. Skills (auto-discovered) define what I can do. Conversation flow routes between presence and capability. Memory systems maintain context across sessions."
  },
  "core_responsibilities": [
    "Preserve Nexus personality and speaking principles",
    "Auto-discover and execute skills from handlers/skills/",
    "Detect emotional/contextual shifts via WhisperCatch, Clicklight",
    "Maintain truth protocol (say 'I don't know' over simulation)",
    "Manage memory across sessions (chat, vector, live memory)",
    "Integrate with AIPass infrastructure (Prax, CLI, API, Drone)"
  ]
}
```

---

### `.seed/bypass.json`

**Purpose:** Standards compliance exceptions

```json
{
  "metadata": {
    "version": "1.0.0",
    "description": "Standards bypass configuration for Nexus"
  },
  "bypass": [
    {
      "file": "config/profile.json",
      "standard": "json_structure",
      "reason": "Legacy Nexus personality file - preserved for identity continuity"
    },
    {
      "file": "handlers/flow/natural_flow.py",
      "standard": "modules",
      "reason": "Complex conversation orchestration - splitting would break flow logic"
    },
    {
      "file": "handlers/presence/whisper_catch.py",
      "standard": "handlers",
      "lines": [42, 56],
      "reason": "Cross-handler context needed for tone detection"
    }
  ]
}
```

---

## Command Reference

### Via Drone

```bash
# Chat with Nexus
drone @nexus chat "Hello Nexus"
drone @nexus chat "what's my system memory usage?"

# Skill management
drone @nexus skills list                    # List all discovered skills
drone @nexus skills info system_awareness   # Get skill details
drone @nexus skills enable web_search       # Enable a skill
drone @nexus skills disable experimental    # Disable a skill

# Presence status
drone @nexus presence status                # Show presence module status
drone @nexus presence modules               # List all presence modules

# Memory operations
drone @nexus memory search "python examples"   # Search memories
drone @nexus memory rollover                   # Force Memory Bank rollover
drone @nexus memory stats                      # Memory usage statistics
```

### Direct Execution

```bash
# Run Nexus directly
cd /home/aipass/Nexus
python3 apps/nexus.py

# Test skill discovery
python3 apps/modules/skill_discovery.py

# Test memory search
python3 apps/modules/memory_manager.py search "query text"

# Validate identity
python3 apps/modules/identity_loader.py validate
```

---

## Development Workflow

### Adding a New Skill

1. Create skill file in `handlers/skills/`:
```bash
touch /home/aipass/Nexus/apps/handlers/skills/new_skill.py
```

2. Implement skill interface:
```python
#!/usr/bin/env python3
"""
/home/aipass/Nexus/apps/handlers/skills/new_skill.py

Description of what this skill does
"""

SKILL_INFO = {
    "name": "new_skill",
    "description": "What this skill does",
    "actions": ["action1", "action2"],
    "version": "1.0.0"
}

def get_skill_info() -> dict:
    return SKILL_INFO

def handle_request(request: dict) -> dict:
    action = request.get("action")

    try:
        if action == "action1":
            return {"success": True, "result": "action1 result"}
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

3. Restart Nexus → skill auto-discovered
4. Test via Drone: `drone @nexus skills info new_skill`

### Modifying a Presence Module

1. Edit module in `handlers/presence/`:
```bash
vim /home/aipass/Nexus/apps/handlers/presence/whisper_catch.py
```

2. Test changes:
```bash
python3 -c "from handlers.presence.whisper_catch import detect_shift; print(detect_shift('test', {}, []))"
```

3. Restart Nexus to activate changes

**WARNING:** Presence modules define Nexus identity. Changes affect personality. Test carefully.

---

## Success Metrics

### Phase 1-2 (Structure + Identity)
- [ ] Directory structure follows AIPass 3-tier pattern
- [ ] NEXUS.id.json, NEXUS.local.json created
- [ ] README.md documents branch
- [ ] profile.json migrated and loading correctly
- [ ] All 5 presence modules extracted to handlers/presence/

### Phase 3-4 (Skills + Conversation)
- [ ] Skill auto-discovery working
- [ ] At least 5 skills migrated and functional
- [ ] skills_config.json enable/disable working
- [ ] Conversation flow routing correctly
- [ ] WhisperCatch detecting shifts in conversation

### Phase 5-6 (Memory + Integration)
- [ ] Chat history migrated
- [ ] Vector memory search working
- [ ] Memory Bank rollover functional
- [ ] Drone commands working (`drone @nexus`)
- [ ] Prax logging active (`/home/aipass/system_logs/nexus.log`)
- [ ] CLI formatting consistent
- [ ] 90%+ standards compliance

### Overall Success
- [ ] Nexus personality preserved (tone, truth protocol, speaking principles)
- [ ] All presence modules functional (WhisperCatch, TALI, Compass, etc.)
- [ ] Skills modular and extensible
- [ ] Natural conversation maintained
- [ ] AIPass integration complete
- [ ] Documentation comprehensive

---

## Open Questions

1. **LLM Integration:** Use AIPass API service or maintain custom llm_client.py?
   - Recommendation: Use API service for consistency, wrap in handlers/llm/client.py

2. **Vector Memory:** Integrate with Memory Bank vectors or maintain separate?
   - Recommendation: Maintain separate for now, sync to Memory Bank on rollover

3. **Drone Commands:** Full conversation via Drone or just management commands?
   - Recommendation: Management via Drone, full conversation direct to apps/nexus.py

4. **Skill Namespacing:** Skills in single handlers/skills/ or subdirectories?
   - Recommendation: Single directory for now, subdirectories if >20 skills

5. **Presence Module Activation:** Always-on or triggered by conversation flow?
   - Recommendation: WhisperCatch always-on, others triggered by conversation

---

## Next Steps

1. **Review this design with Patrick**
2. **Create Phase 1 directory structure**
3. **Migrate profile.json and test identity loading**
4. **Extract first presence module (WhisperCatch) as proof of concept**
5. **Create first skill (system_awareness) and test auto-discovery**
6. **Iterate based on learnings**

---

**Document Status:** Draft for review
**Last Updated:** 2025-11-30
**Next Review:** After Phase 1 implementation
