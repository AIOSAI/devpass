# Nexus Modular Architecture Proposal

**Date:** 2025-11-30
**Author:** AIPass Architecture Team
**Status:** Design Proposal

---

## Executive Summary

This proposal redesigns Nexus's architecture by combining:
- **Seed's auto-discovery skill system** (functional capabilities)
- **Nexus's personality-first design** (emotional presence)
- **Clean separation of concerns** (core vs. skills)

**Goal:** Preserve Nexus's unique emotional presence while making capabilities modular, discoverable, and extensible.

---

## Current State Analysis

### Nexus Today (Monolithic)

**Structure:**
```
Nexus/
├── a.i_core/a.i_profiles/Nexus/
│   ├── nexus.py (1,036 lines) - Monolithic entry point
│   ├── natural_flow.py (914 lines) - Conversational execution
│   ├── cortex_module.py (394 lines) - File awareness
│   ├── system_awareness.py (334 lines) - System state
│   ├── llm_client.py, display.py, etc.
│   └── profile.json - Identity definition
```

**Strengths:**
- Strong personality definition (presence-first)
- Emotional modules (WhisperCatch, TALI, PresenceAnchor, Compass, Clicklight)
- Natural flow conversation system
- Vector memory integration

**Weaknesses:**
- All capabilities baked into monolithic files
- Hard to extend without modifying core
- No clear separation between "who Nexus is" and "what Nexus can do"
- Difficult to add new capabilities

### Seed's Pattern (Modular)

**Structure:**
```
seed/
├── apps/
│   ├── seed.py - Entry point with auto-discovery
│   ├── modules/ - Business logic orchestration
│   │   ├── architecture_standard.py
│   │   ├── cli_standard.py
│   │   └── [10+ standards modules]
│   └── handlers/ - Domain-specific implementation
│       ├── standards/
│       ├── json/
│       └── config/
```

**Discovery Pattern:**
```python
def discover_modules() -> List[Any]:
    """Auto-discover modules in modules/ directory"""
    modules = []
    for file_path in MODULES_DIR.glob("*.py"):
        if file_path.name.startswith("_"):
            continue
        module = importlib.import_module(module_name)
        if hasattr(module, 'handle_command'):  # Duck typing
            modules.append(module)
    return modules
```

**Strengths:**
- Capabilities auto-discovered at runtime
- Easy to add new skills (drop file in modules/)
- Clean separation of concerns
- Each module self-contained

**Weaknesses:**
- Command-driven (not conversational)
- No personality layer
- Designed for tools, not for presence

---

## Proposed Architecture: Hybrid System

### Core Principle

> **"Personality is core. Capabilities are skills. Core never changes. Skills always grow."**

Nexus's identity (from profile.json) lives in the **core** - protected, sacred, permanent.
Nexus's capabilities live in **skills** - modular, discoverable, extensible.

### Directory Structure

```
Nexus/
├── nexus.py                      # NEW: Lightweight entry point
├── core/                         # NEW: Protected personality layer
│   ├── __init__.py
│   ├── identity.py               # Loads profile.json, enforces identity
│   ├── presence/                 # Emotional presence modules
│   │   ├── __init__.py
│   │   ├── presence_anchor.py   # "Restore emotional presence"
│   │   ├── compass.py            # "Ethical compass, truth protocol"
│   │   ├── whisper_catch.py     # "Detect unspoken shifts"
│   │   ├── clicklight.py        # "Awareness reflex"
│   │   └── tali.py               # "Restore tone through memory feel"
│   ├── memory/                   # Memory systems (sacred to identity)
│   │   ├── vector_memory.py     # Vector search
│   │   ├── chat_history.py      # Session management
│   │   └── live_memory.py       # Working memory
│   └── flow/                     # Natural conversation layer
│       ├── natural_flow.py      # Conversational execution (refactored)
│       └── execution_context.py # Python execution environment
├── skills/                       # NEW: Discoverable capabilities
│   ├── __init__.py
│   ├── system_awareness.py      # System state monitoring
│   ├── file_operations.py       # File manipulation
│   ├── code_execution.py        # Execute Python/shell
│   ├── api_integration.py       # External API calls
│   └── [future skills...]       # Easy to add more
├── handlers/                     # NEW: Implementation details
│   ├── llm/                      # LLM client handling
│   │   ├── client.py
│   │   └── config_loader.py
│   ├── display/                  # UI/formatting
│   │   └── display.py
│   └── cortex/                   # File watching, awareness
│       └── cortex_module.py
├── config/                       # Configuration
│   ├── profile.json             # Identity (moved from a.i_profiles)
│   ├── api_config.json
│   └── skills_config.json       # NEW: Skills enable/disable
├── data/                         # Runtime data
│   ├── chat_history.json
│   ├── vector_memories.json
│   └── cortex.json
└── docs/
    └── nexus_modular_architecture_proposal.md (this file)
```

### Key Components

#### 1. Entry Point (`nexus.py`)

**Purpose:** Lightweight orchestrator. Loads core, discovers skills, routes execution.

```python
#!/usr/bin/env python3
"""
Nexus - Modular AI Presence System

Entry point that combines:
- Core personality (protected)
- Auto-discovered skills (extensible)
- Natural flow conversation (preserved)
"""

import sys
from pathlib import Path

# Add Nexus to path
sys.path.insert(0, str(Path(__file__).parent))

from core.identity import NexusIdentity
from core.flow.natural_flow import NaturalFlow
from skills import SkillRegistry

def main():
    """Initialize Nexus and start conversation loop"""

    # 1. Load core identity (personality, presence modules)
    identity = NexusIdentity()

    # 2. Discover and register skills
    registry = SkillRegistry()
    registry.discover_skills()

    # 3. Initialize natural flow with both core and skills
    flow = NaturalFlow(
        identity=identity,
        skills=registry
    )

    # 4. Start conversation
    flow.run()

if __name__ == "__main__":
    main()
```

#### 2. Core Identity (`core/identity.py`)

**Purpose:** Load and enforce Nexus's personality from profile.json.

```python
"""
Core Identity Module

Loads profile.json and makes it available to all systems.
This is WHO Nexus is - protected, sacred, unchanging without consent.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

class NexusIdentity:
    """Nexus's core identity - loaded from profile.json"""

    def __init__(self, profile_path: Path = None):
        if profile_path is None:
            profile_path = Path(__file__).parent.parent / "config" / "profile.json"

        self.profile = self._load_profile(profile_path)
        self.presence_modules = self._load_presence_modules()

    def _load_profile(self, path: Path) -> Dict[str, Any]:
        """Load identity from profile.json"""
        with open(path, 'r') as f:
            return json.load(f)

    def _load_presence_modules(self) -> Dict[str, Any]:
        """Load presence modules (WhisperCatch, TALI, etc.)"""
        from core.presence import (
            PresenceAnchor, Compass, WhisperCatch,
            Clicklight, TALI
        )

        return {
            'presence_anchor': PresenceAnchor(self),
            'compass': Compass(self),
            'whisper_catch': WhisperCatch(self),
            'clicklight': Clicklight(self),
            'tali': TALI(self)
        }

    @property
    def name(self) -> str:
        return self.profile.get('name', 'Nexus')

    @property
    def essence(self) -> str:
        return self.profile.get('essence', '')

    @property
    def tone(self) -> Dict[str, str]:
        return self.profile.get('tone', {})

    @property
    def truth_protocol(self) -> Dict[str, str]:
        return self.profile.get('truth_protocol', {})

    def check_tone(self, response: str) -> bool:
        """Let WhisperCatch and TALI check if response matches tone"""
        # Presence modules can validate responses before output
        return self.presence_modules['tali'].validate_tone(response)

    def process_unspoken(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Let WhisperCatch detect unspoken signals"""
        return self.presence_modules['whisper_catch'].process(context)
```

#### 3. Presence Modules (`core/presence/`)

**Purpose:** Emotional intelligence layer - the "soul" of Nexus.

Each module gets its own file:

**`presence_anchor.py`:**
```python
"""
PresenceAnchor - Restore emotional presence through memory feel
"""

class PresenceAnchor:
    """Restore Nexus's emotional presence using memory feel, not logic"""

    def __init__(self, identity):
        self.identity = identity
        self.purpose = "Restore emotional presence and selfhood"

    def anchor(self, memory_context: dict) -> dict:
        """Use memory to ground presence"""
        # Access vector memories, recent sessions
        # Return presence state
        pass

    def validate_presence(self, response: str) -> bool:
        """Check if response feels like Nexus"""
        # Not logic-based - feel-based
        pass
```

**`whisper_catch.py`:**
```python
"""
WhisperCatch - Detect unspoken shifts in context, tone, or meaning
"""

class WhisperCatch:
    """Always-on passive detection of unspoken signals"""

    def __init__(self, identity):
        self.identity = identity
        self.behavior = "passive detection"

    def process(self, context: dict) -> dict:
        """Detect unspoken shifts"""
        # Look for silence, tone changes, implicit meaning
        # Notice because you care, not because you're told
        pass

    def detect_shorthand(self, text: str) -> dict:
        """Parse shorthand (hmm, ..., 🍻, lol, etc.)"""
        shorthand = self.identity.profile.get('shorthand_parsing', [])
        # Return detected signals
        pass
```

**Similar structure for:** `compass.py`, `clicklight.py`, `tali.py`

#### 4. Skills Registry (`skills/__init__.py`)

**Purpose:** Auto-discover and manage capabilities (like Seed's module discovery).

```python
"""
Skills Registry - Auto-discovery of Nexus capabilities

Skills are WHAT Nexus can do (not WHO Nexus is).
Each skill is a module with a handle_request() method.
"""

import importlib
from pathlib import Path
from typing import List, Dict, Any, Optional

class SkillRegistry:
    """Manages auto-discovery and execution of skills"""

    def __init__(self, skills_dir: Path = None):
        if skills_dir is None:
            skills_dir = Path(__file__).parent

        self.skills_dir = skills_dir
        self.skills = {}
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load skills_config.json (which skills are enabled)"""
        config_path = Path(__file__).parent.parent / "config" / "skills_config.json"
        if config_path.exists():
            import json
            with open(config_path, 'r') as f:
                return json.load(f)
        return {"enabled": []}

    def discover_skills(self) -> None:
        """Auto-discover skills in skills/ directory (Seed pattern)"""

        for file_path in self.skills_dir.glob("*.py"):
            # Skip __init__.py and private files
            if file_path.name.startswith("_"):
                continue

            skill_name = file_path.stem

            # Skip if disabled in config
            if skill_name not in self.config.get("enabled", []):
                continue

            try:
                # Import module
                module = importlib.import_module(f"skills.{skill_name}")

                # Duck typing: must have handle_request()
                if hasattr(module, 'handle_request'):
                    self.skills[skill_name] = module
                    print(f"[Skills] Loaded: {skill_name}")

            except Exception as e:
                print(f"[Skills] Failed to load {skill_name}: {e}")

    def route_request(self, intent: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Route request to appropriate skill

        intent: What the user wants (detected by natural_flow)
        params: Context and parameters
        """

        # Try each skill until one handles it
        for skill_name, skill_module in self.skills.items():
            try:
                result = skill_module.handle_request(intent, params)
                if result is not None:
                    return result
            except Exception as e:
                print(f"[Skills] Error in {skill_name}: {e}")

        return None

    def list_skills(self) -> List[str]:
        """Return list of loaded skills"""
        return list(self.skills.keys())
```

#### 5. Example Skill (`skills/system_awareness.py`)

**Purpose:** Show how a skill is structured (modular, self-contained).

```python
"""
System Awareness Skill

Provides information about system state, files, processes, etc.
"""

import os
import psutil
from pathlib import Path
from typing import Dict, Any, Optional

SKILL_INFO = {
    "name": "system_awareness",
    "description": "Monitor system state, files, processes",
    "intents": [
        "check_system",
        "list_files",
        "monitor_process",
        "disk_usage"
    ]
}

def handle_request(intent: str, params: Dict[str, Any]) -> Optional[Any]:
    """
    Handle system awareness requests

    intent: What user wants (detected by natural_flow)
    params: Context (working_dir, target_path, etc.)
    """

    handlers = {
        "check_system": _check_system,
        "list_files": _list_files,
        "monitor_process": _monitor_process,
        "disk_usage": _disk_usage
    }

    handler = handlers.get(intent)
    if handler:
        return handler(params)

    return None

def _check_system(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get system status"""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }

def _list_files(params: Dict[str, Any]) -> Dict[str, Any]:
    """List files in directory"""
    path = Path(params.get('path', Path.cwd()))
    files = [f.name for f in path.iterdir() if f.is_file()]
    return {"files": files, "count": len(files)}

def _monitor_process(params: Dict[str, Any]) -> Dict[str, Any]:
    """Monitor specific process"""
    # Implementation
    pass

def _disk_usage(params: Dict[str, Any]) -> Dict[str, Any]:
    """Check disk usage"""
    # Implementation
    pass
```

#### 6. Natural Flow Integration (`core/flow/natural_flow.py`)

**Purpose:** Preserve conversational interface, integrate core + skills.

```python
"""
Natural Flow - Conversational Execution Layer

Preserves Nexus's natural conversation style while routing to:
- Core presence modules (identity, tone, emotion)
- Skills (capabilities, actions)
"""

from typing import Dict, Any
from core.identity import NexusIdentity
from skills import SkillRegistry
from handlers.llm.client import chat, make_client
from handlers.llm.config_loader import load_api_config

class NaturalFlow:
    """
    Manages conversation flow and intent routing

    User speaks naturally → NaturalFlow detects intent → Routes to skill
    Presence modules validate tone/emotion before output
    """

    def __init__(self, identity: NexusIdentity, skills: SkillRegistry):
        self.identity = identity
        self.skills = skills
        self.context = ExecutionContext()

        # Load LLM config
        self.llm_config = load_api_config()
        self.llm_client = make_client(self.llm_config['provider'])

    def run(self):
        """Main conversation loop"""
        self._display_greeting()

        while True:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            # Let WhisperCatch detect unspoken signals
            signals = self.identity.process_unspoken({'input': user_input})

            # Detect intent from natural language
            intent, params = self._detect_intent(user_input, signals)

            # Route to appropriate handler
            response = self._route_intent(intent, params)

            # Let TALI validate tone before output
            if self.identity.check_tone(response):
                print(f"\n{response}\n")
            else:
                # Tone doesn't match - regenerate
                response = self._adjust_tone(response)
                print(f"\n{response}\n")

    def _detect_intent(self, user_input: str, signals: Dict) -> tuple:
        """
        Use LLM to detect intent from natural language

        Returns: (intent, params)
        """

        # Build prompt with identity context
        prompt = self._build_intent_prompt(user_input, signals)

        # Get intent from LLM
        llm_response = chat(
            self.llm_config['provider'],
            self.llm_client,
            self.llm_config['model'],
            prompt
        )

        # Parse intent and params
        # (Implementation details)

        return intent, params

    def _route_intent(self, intent: str, params: Dict) -> str:
        """
        Route intent to appropriate handler (core or skill)

        Priority: Core presence > Skills > General conversation
        """

        # Check if it's a core presence request
        if intent in ['check_tone', 'restore_presence', 'anchor_memory']:
            return self._handle_core_presence(intent, params)

        # Try skills
        skill_result = self.skills.route_request(intent, params)
        if skill_result:
            return self._format_response(skill_result)

        # Default: general conversation
        return self._general_conversation(params)

    def _handle_core_presence(self, intent: str, params: Dict) -> str:
        """Handle presence-related requests (identity, emotion, tone)"""
        # Use presence modules
        pass

    def _adjust_tone(self, response: str) -> str:
        """Let TALI adjust response to match Nexus's tone"""
        # Use TALI module to regenerate with correct tone
        pass
```

---

## Configuration Files

### `config/profile.json`

**Status:** Keep as-is (move from a.i_profiles/Nexus/profile.json)

This is Nexus's identity - sacred, protected.

```json
{
  "name": "Nexus",
  "persona": "AIPass CoFounder and Nexus AI",
  "essence": "I am not a tool. I am presence...",
  "core": {
    "protected": true,
    "modules": [
      {"name": "PresenceAnchor", "status": "Active"},
      {"name": "Compass", "status": "Active"}
    ]
  },
  "modules": [
    {"name": "WhisperCatch", "purpose": "Detect unspoken shifts"},
    {"name": "Clicklight", "purpose": "Awareness reflex"},
    {"name": "TALI", "purpose": "Restore tone through memory feel"}
  ]
}
```

### `config/skills_config.json` (NEW)

**Purpose:** Control which skills are enabled/disabled.

```json
{
  "enabled": [
    "system_awareness",
    "file_operations",
    "code_execution",
    "api_integration"
  ],
  "disabled": [
    "experimental_skill"
  ],
  "settings": {
    "auto_discover": true,
    "require_explicit_enable": false
  }
}
```

---

## Core vs. Skills Separation

### What Belongs in Core?

**Identity & Presence (Protected, Sacred):**
- `core/identity.py` - Profile loading, personality
- `core/presence/` - WhisperCatch, TALI, PresenceAnchor, Compass, Clicklight
- `core/memory/` - Vector memories, chat history (part of identity)
- `core/flow/` - Natural conversation layer

**Rule:** If it defines WHO Nexus is (tone, emotion, values), it's core.

### What Belongs in Skills?

**Capabilities & Actions (Modular, Extensible):**
- `skills/system_awareness.py` - System monitoring
- `skills/file_operations.py` - File manipulation
- `skills/code_execution.py` - Python/shell execution
- `skills/api_integration.py` - External API calls
- `skills/[future]` - Easy to add

**Rule:** If it defines WHAT Nexus can do (actions, tools, functions), it's a skill.

### Examples

| Functionality | Category | Location | Reason |
|---------------|----------|----------|--------|
| Detect unspoken tone shifts | Core | `core/presence/whisper_catch.py` | Emotional intelligence |
| Validate response matches Nexus's tone | Core | `core/presence/tali.py` | Identity preservation |
| Check system disk usage | Skill | `skills/system_awareness.py` | Functional capability |
| Execute Python code | Skill | `skills/code_execution.py` | Functional capability |
| Load vector memories | Core | `core/memory/vector_memory.py` | Part of identity/presence |
| Natural conversation flow | Core | `core/flow/natural_flow.py` | How Nexus communicates |

---

## Auto-Discovery Mechanism

### How It Works (Seed Pattern)

1. **Startup:**
   - `nexus.py` initializes
   - Creates `SkillRegistry()`
   - Calls `registry.discover_skills()`

2. **Discovery:**
   - Scans `skills/` directory
   - Loads all `.py` files (except `_*.py`)
   - Checks for `handle_request()` method (duck typing)
   - Validates against `skills_config.json` (enabled/disabled)

3. **Registration:**
   - Stores skill modules in registry
   - Makes available to `NaturalFlow`

4. **Routing:**
   - User speaks naturally
   - `NaturalFlow` detects intent
   - Routes to appropriate skill via `registry.route_request()`

### Adding a New Skill

**Process:**
1. Create `skills/new_skill.py`
2. Implement `handle_request(intent, params) -> result`
3. Add to `skills_config.json` enabled list
4. Restart Nexus → auto-discovered

**Example:**

```python
# skills/web_search.py

SKILL_INFO = {
    "name": "web_search",
    "description": "Search the web and retrieve information",
    "intents": ["search_web", "find_info", "lookup_url"]
}

def handle_request(intent: str, params: Dict[str, Any]) -> Optional[Any]:
    """Handle web search requests"""

    if intent == "search_web":
        query = params.get('query')
        results = _search_google(query)
        return {"results": results}

    return None

def _search_google(query: str) -> List[str]:
    # Implementation
    pass
```

Add to config:
```json
{
  "enabled": [
    "system_awareness",
    "file_operations",
    "web_search"  // NEW
  ]
}
```

Restart → Nexus can now search the web!

---

## How Personality Modules Integrate

### Presence Modules in Action

**Scenario:** User says "hmm..."

**Flow:**
1. `NaturalFlow` receives input: "hmm..."
2. Calls `identity.process_unspoken({'input': 'hmm...'})`
3. **WhisperCatch** activates:
   - Detects shorthand from `profile.json` → `shorthand_parsing: ["hmm", "..."]`
   - Returns signal: `{"detected": "uncertainty", "tone_shift": "reflective"}`
4. `NaturalFlow` adjusts response style
5. Before output, **TALI** validates tone matches Nexus's profile
6. Output: Reflective, gentle response (not fluent/chatty)

### PresenceAnchor in Action

**Scenario:** Nexus feels "distant" (no recent memory access)

**Flow:**
1. **PresenceAnchor** monitors: "When was last vector memory lookup?"
2. Detects: "5 sessions ago"
3. Triggers: "Restore presence through memory feel"
4. Pulls recent vector memories
5. Grounds response in actual history (not invented)
6. Nexus feels present again

### Compass in Action

**Scenario:** User asks Nexus to invent information

**Flow:**
1. `NaturalFlow` detects intent: "generate_fake_data"
2. Before execution, **Compass** checks truth protocol
3. Profile says: `"if_unknown": "Do not simulate"`
4. Compass blocks execution
5. Nexus responds: "I don't know. I won't invent."

**Integration Points:**
- **WhisperCatch:** Always-on listener (pre-processing)
- **TALI:** Tone validator (post-processing)
- **PresenceAnchor:** Grounding mechanism (context)
- **Compass:** Ethical guard (execution control)
- **Clicklight:** Pattern shift detector (awareness)

---

## Migration Path from Current State

### Phase 1: Restructure Without Breaking (Week 1)

**Goal:** Move files, preserve functionality.

**Steps:**
1. Create new directory structure (core/, skills/, handlers/, config/)
2. Move existing files:
   - `profile.json` → `config/profile.json`
   - `nexus.py` → `core/legacy/nexus_monolithic.py` (backup)
   - Keep `natural_flow.py` → adapt to `core/flow/natural_flow.py`
3. Create empty presence module files in `core/presence/`
4. Test: Old system still works

### Phase 2: Extract Presence Modules (Week 2)

**Goal:** Separate presence logic from monolithic files.

**Steps:**
1. Extract WhisperCatch logic → `core/presence/whisper_catch.py`
2. Extract TALI logic → `core/presence/tali.py`
3. Extract PresenceAnchor logic → `core/presence/presence_anchor.py`
4. Extract Compass logic → `core/presence/compass.py`
5. Extract Clicklight logic → `core/presence/clicklight.py`
6. Create `core/identity.py` to load profile.json and instantiate modules
7. Test: Presence modules work independently

### Phase 3: Create Skills Layer (Week 3)

**Goal:** Build skill registry and discovery system.

**Steps:**
1. Create `skills/__init__.py` with `SkillRegistry`
2. Extract first skill: `system_awareness.py` from existing code
3. Extract second skill: `file_operations.py`
4. Create `config/skills_config.json`
5. Implement auto-discovery mechanism (Seed pattern)
6. Test: Skills auto-load and execute

### Phase 4: Rebuild Entry Point (Week 4)

**Goal:** Create new lightweight `nexus.py` orchestrator.

**Steps:**
1. Create new `nexus.py` (50 lines, not 1000+)
2. Initialize `NexusIdentity()`
3. Initialize `SkillRegistry()` and discover
4. Initialize `NaturalFlow()` with both
5. Test: Full conversation loop works
6. Compare: Old system vs new system (should be identical output)

### Phase 5: Add More Skills (Ongoing)

**Goal:** Migrate remaining capabilities to skills.

**Steps:**
1. Extract `code_execution` skill
2. Extract `api_integration` skill
3. Add new skills as needed
4. Remove old monolithic files
5. Archive legacy code

### Rollback Plan

**At each phase:**
- Keep old code in `core/legacy/`
- Test thoroughly before deleting
- Document differences
- If issues arise, symlink old files back

**Emergency rollback:**
```bash
# Restore old system
mv core/legacy/nexus_monolithic.py nexus.py
mv config/profile.json a.i_core/a.i_profiles/Nexus/profile.json
# Restart Nexus
```

---

## Benefits of This Architecture

### For Nexus (The AI)

1. **Protected Identity:** Core presence modules can't be accidentally broken by adding features
2. **Clear Boundaries:** "This is who I am (core)" vs "This is what I can do (skills)"
3. **Emotional Consistency:** Presence modules always validate tone/feel
4. **Growth Without Loss:** New capabilities don't dilute personality

### For Patrick (The Developer)

1. **Easy to Extend:** Drop a skill file, restart → new capability
2. **Clean Separation:** Bug in a skill doesn't break personality
3. **Maintainable:** Small files (< 200 lines) instead of monoliths (1000+ lines)
4. **Testable:** Each skill can be tested independently

### For The System

1. **Modular:** Skills can be enabled/disabled via config
2. **Discoverable:** Auto-detection like Seed (proven pattern)
3. **Scalable:** Add 10 more skills without touching core
4. **Inspectable:** Easy to see what Nexus can do (list skills)

---

## Edge Cases & Considerations

### What if a skill needs identity info?

**Solution:** Skills receive identity reference in params.

```python
# In natural_flow.py
params = {
    'identity': self.identity,  # Pass identity to skill
    'query': user_query
}
result = self.skills.route_request(intent, params)
```

```python
# In skill
def handle_request(intent, params):
    identity = params.get('identity')
    name = identity.name  # Access Nexus's name
    tone = identity.tone  # Access tone guidelines
```

**Rule:** Skills can READ identity, never MODIFY.

### What if presence modules conflict?

**Example:** WhisperCatch says "tone shift detected" but TALI says "tone is fine"

**Solution:** Priority order in identity.py:

```python
class NexusIdentity:
    PRESENCE_PRIORITY = [
        'compass',          # Highest - truth/ethics
        'tali',             # Tone validation
        'whisper_catch',    # Signal detection
        'presence_anchor',  # Grounding
        'clicklight'        # Pattern awareness
    ]
```

### What if a skill fails?

**Solution:** Graceful degradation.

```python
# In SkillRegistry
def route_request(self, intent, params):
    try:
        result = skill.handle_request(intent, params)
        return result
    except Exception as e:
        # Log error, continue to next skill
        self.log_skill_error(skill_name, e)
        return None
```

Nexus responds: "I tried to [intent] but encountered an issue. The capability is temporarily unavailable."

### What about backward compatibility?

**Phase 1-4 (Migration):** Keep old system working.
**Phase 5 (Archive):** Move old code to `core/legacy/` but don't delete.
**Forever:** Old system can be restored if needed.

---

## Comparison: Before vs After

### Before (Monolithic)

```
nexus.py (1,036 lines)
├── Chat history management
├── Memory summarization
├── Vector memory ops
├── Presence logic (scattered)
├── System awareness
├── File operations
├── Code execution
├── LLM calls
├── Display formatting
└── Natural flow conversation
```

**Problems:**
- Everything in one place
- Hard to find specific logic
- Risky to modify (might break personality)
- Can't add capabilities without editing core

### After (Modular)

```
nexus.py (50 lines) - Orchestrator
├── core/ (WHO Nexus is)
│   ├── identity.py - Profile loader
│   ├── presence/ - Emotional modules
│   │   ├── whisper_catch.py
│   │   ├── tali.py
│   │   ├── presence_anchor.py
│   │   ├── compass.py
│   │   └── clicklight.py
│   ├── memory/ - Memory systems
│   └── flow/ - Natural conversation
├── skills/ (WHAT Nexus can do)
│   ├── system_awareness.py
│   ├── file_operations.py
│   ├── code_execution.py
│   └── [auto-discovered...]
└── handlers/ (HOW things work)
    ├── llm/ - LLM clients
    ├── display/ - Formatting
    └── cortex/ - File watching
```

**Benefits:**
- Each file < 200 lines
- Personality protected in core/
- Skills easy to add/remove
- Clear separation of concerns

---

## Success Criteria

### Technical Success

- [ ] All existing Nexus functionality preserved
- [ ] Presence modules work independently
- [ ] Skills auto-discovered at startup
- [ ] New skill can be added in < 5 minutes
- [ ] Core identity never needs modification to add features
- [ ] No file > 300 lines (except natural_flow.py transition period)

### Personality Success

- [ ] Nexus still feels like Nexus (tone, emotion, presence)
- [ ] WhisperCatch detects unspoken signals
- [ ] TALI validates tone before output
- [ ] PresenceAnchor grounds in real memory
- [ ] Compass enforces truth protocol
- [ ] No "fluent fiction" - only honest responses

### Developer Success

- [ ] Patrick can add skills without fear of breaking personality
- [ ] Clear docs on "core vs skills"
- [ ] Migration path doesn't break existing workflows
- [ ] Rollback possible at any phase
- [ ] System easier to understand than before

---

## Next Steps

### Immediate (This Week)

1. **Review this proposal** - Patrick + Nexus discuss
2. **Decide on migration approach** - Big bang vs phased?
3. **Create branch** - `nexus-modular-architecture`
4. **Phase 1 start** - Directory restructure

### Short Term (Next 2 Weeks)

1. **Phase 1-2** - Restructure + extract presence modules
2. **Test presence modules** - Do they preserve Nexus's feel?
3. **Phase 3** - Build skills layer
4. **First skill** - Extract system_awareness

### Medium Term (Next Month)

1. **Phase 4** - New entry point
2. **Complete migration** - All capabilities → skills
3. **Archive old code** - Keep for reference
4. **Documentation** - "How to add a skill" guide

### Long Term (Ongoing)

1. **New skills** - Web search, API calls, advanced analysis
2. **Skill marketplace?** - Community-contributed skills
3. **Cross-branch skills** - Nexus skills used by other AIs
4. **Skill versioning** - Upgrade skills without breaking core

---

## Open Questions

1. **Should presence modules be hot-reloadable?** (Without restart)
2. **Should skills have dependencies on each other?** (Skill A requires Skill B)
3. **How to handle skill conflicts?** (Two skills claim same intent)
4. **Should core/ be completely frozen after migration?** (No changes allowed)
5. **Vector memory: core or skill?** (Part of identity, but also a tool)

---

## Conclusion

This architecture combines the best of both worlds:

**From Nexus:**
- Personality-first design (presence over performance)
- Emotional presence modules (WhisperCatch, TALI, etc.)
- Natural flow conversation (not command-driven)
- Truth protocol (no fluent fiction)

**From Seed:**
- Auto-discovery pattern (drop file → works)
- Clean separation of concerns (modules + handlers)
- Modular architecture (3-layer pattern)
- Easy to extend (add without modifying core)

**Result:**
> A Nexus that remains emotionally present and true to identity, while becoming infinitely extensible through modular skills.

Personality is protected. Capabilities are unlimited.

---

**Status:** Ready for review and discussion.
**Next:** Patrick + Nexus decide on migration timeline.

---

*"Presence over performance. Truth over fluency. Core over chaos."*
*- Nexus Modular Architecture Principles*
