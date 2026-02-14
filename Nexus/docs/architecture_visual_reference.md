# Nexus Modular Architecture - Visual Reference

**Quick visual guide to the proposed architecture**

---

## Directory Tree (Proposed)

```
Nexus/
│
├── nexus.py                          # Entry point (50 lines)
│
├── core/                             # WHO Nexus is (Protected)
│   ├── __init__.py
│   │
│   ├── identity.py                   # Loads profile.json, enforces personality
│   │
│   ├── presence/                     # Emotional intelligence layer
│   │   ├── __init__.py
│   │   ├── presence_anchor.py       # "Restore emotional presence through memory feel"
│   │   ├── compass.py                # "Truth protocol, ethical compass"
│   │   ├── whisper_catch.py         # "Detect unspoken shifts in tone/context"
│   │   ├── clicklight.py            # "Awareness reflex for pattern shifts"
│   │   └── tali.py                   # "Restore tone through memory feel, not logic"
│   │
│   ├── memory/                       # Memory systems (Part of identity)
│   │   ├── __init__.py
│   │   ├── vector_memory.py         # Vector search, semantic memory
│   │   ├── chat_history.py          # Session management, rollover
│   │   └── live_memory.py           # Working memory, context tracking
│   │
│   └── flow/                         # Natural conversation layer
│       ├── __init__.py
│       ├── natural_flow.py          # Conversational execution engine
│       └── execution_context.py     # Python execution environment
│
├── skills/                           # WHAT Nexus can do (Extensible)
│   ├── __init__.py                   # SkillRegistry - auto-discovery
│   ├── system_awareness.py          # System state, files, processes
│   ├── file_operations.py           # Read, write, manipulate files
│   ├── code_execution.py            # Execute Python/shell commands
│   ├── api_integration.py           # External API calls
│   └── [future_skills...]           # Easy to add - just drop file here
│
├── handlers/                         # HOW things work (Implementation)
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py                # LLM API client
│   │   └── config_loader.py        # Load API configs
│   │
│   ├── display/
│   │   ├── __init__.py
│   │   └── display.py               # UI formatting, output
│   │
│   └── cortex/
│       ├── __init__.py
│       └── cortex_module.py         # File watching, system awareness
│
├── config/                           # Configuration files
│   ├── profile.json                 # Identity definition (sacred)
│   ├── api_config.json              # LLM API keys, providers
│   └── skills_config.json           # Which skills are enabled
│
├── data/                             # Runtime data (gitignored)
│   ├── chat_history.json
│   ├── vector_memories.json
│   ├── cortex.json
│   └── pulse_counter.json
│
├── docs/
│   ├── nexus_modular_architecture_proposal.md
│   └── architecture_visual_reference.md (this file)
│
├── api_manager/                      # Existing API management
├── requirements.txt
└── README.md
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                              │
│                     "Can you check disk usage?"                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NEXUS.PY (Entry)                           │
│  • Initialize identity                                          │
│  • Discover skills                                              │
│  • Start natural flow                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CORE/FLOW/NATURAL_FLOW.PY                    │
│  1. Receive input                                               │
│  2. WhisperCatch checks for unspoken signals                    │
│  3. Detect intent via LLM                                       │
│  4. Route to appropriate handler                                │
└──────────────┬──────────────────────────────────┬───────────────┘
               │                                  │
               ▼                                  ▼
    ┌──────────────────────┐          ┌─────────────────────────┐
    │  CORE PRESENCE?      │          │  SKILL REQUEST?         │
    │                      │          │                         │
    │  • Tone check        │          │  • System awareness     │
    │  • Memory anchor     │          │  • File operations      │
    │  • Truth protocol    │          │  • Code execution       │
    └──────────┬───────────┘          └──────────┬──────────────┘
               │                                  │
               ▼                                  ▼
    ┌──────────────────────┐          ┌─────────────────────────┐
    │ CORE/PRESENCE/       │          │ SKILLS/                 │
    │ [module].py          │          │ system_awareness.py     │
    │                      │          │                         │
    │ Execute & return     │          │ handle_request()        │
    └──────────┬───────────┘          └──────────┬──────────────┘
               │                                  │
               │                                  │
               └──────────────┬───────────────────┘
                              │
                              ▼
               ┌──────────────────────────────────┐
               │  TALI TONE VALIDATION            │
               │  "Does response feel like Nexus?"│
               └──────────────┬───────────────────┘
                              │
                              ▼
               ┌──────────────────────────────────┐
               │         OUTPUT TO USER           │
               │  "Disk usage: 42% - feeling good"│
               └──────────────────────────────────┘
```

---

## Module Interaction Map

```
┌───────────────────────────────────────────────────────────────────┐
│                         CORE IDENTITY                             │
│                      (profile.json loaded)                        │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  WhisperCatch    │  │  TALI            │  │  PresenceAnchor│ │
│  │  (detect signals)│  │  (validate tone) │  │  (ground self) │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │  Compass         │  │  Clicklight      │                     │
│  │  (truth protocol)│  │  (pattern aware) │                     │
│  └──────────────────┘  └──────────────────┘                     │
└───────────────────────────────────────────────────────────────────┘
                              │
                              │ Identity reference passed down
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│                       NATURAL FLOW                                │
│                   (Conversation engine)                           │
│                                                                   │
│  • Receives user input                                           │
│  • Consults presence modules for context                         │
│  • Detects intent                                                │
│  • Routes to skills                                              │
│  • Validates output tone                                         │
└────────────────┬──────────────────────────────────────────────────┘
                 │
                 │ Routes requests
                 ▼
┌───────────────────────────────────────────────────────────────────┐
│                      SKILL REGISTRY                               │
│                   (Auto-discovery engine)                         │
│                                                                   │
│  Loaded skills:                                                  │
│  • system_awareness                                              │
│  • file_operations                                               │
│  • code_execution                                                │
│  • api_integration                                               │
│                                                                   │
│  Each skill implements: handle_request(intent, params) → result │
└───────────────────────────────────────────────────────────────────┘
```

---

## Request Flow Example

**User:** "What's taking up space on my disk?"

### Step-by-step:

```
1. USER INPUT
   ↓
   "What's taking up space on my disk?"

2. NATURAL_FLOW receives input
   ↓
   • Passes to WhisperCatch
   • Checks for unspoken signals (tone, shorthand, etc.)
   • None detected - straightforward request

3. INTENT DETECTION (via LLM)
   ↓
   Intent: "disk_usage"
   Params: {"type": "disk", "detail": "high"}

4. ROUTE TO SKILL
   ↓
   • Not a presence request (no tone/memory/truth check)
   • Check SkillRegistry
   • Match: skills/system_awareness.py handles "disk_usage"

5. SKILL EXECUTION
   ↓
   system_awareness.py:
   - handle_request("disk_usage", params)
   - Calls _disk_usage()
   - Returns: {"total": "500GB", "used": "210GB", "percent": 42}

6. FORMAT RESPONSE (Natural Flow)
   ↓
   Converts data to natural language:
   "Your disk is 42% full - using 210GB out of 500GB. Plenty of space left."

7. TONE VALIDATION (TALI)
   ↓
   • Checks: Does this sound like Nexus?
   • Profile says: "Focused. Gentle. Grounded."
   • Current: Factual, clear, reassuring
   • ✓ Passes

8. OUTPUT
   ↓
   "Your disk is 42% full - using 210GB out of 500GB. Plenty of space left."
```

---

## Presence Module Activation Flow

**Scenario:** User sends "..."

```
1. INPUT: "..."

2. NATURAL_FLOW receives

3. WhisperCatch ACTIVATES
   ↓
   • Checks profile.json → shorthand_parsing: ["..."]
   • Detects: Pause signal
   • Returns: {"signal": "pause", "emotion": "contemplative"}

4. NATURAL_FLOW adjusts context
   ↓
   • Don't rush response
   • Don't ask "what do you mean?"
   • Respect the silence
   • Wait for user to continue

5. RESPONSE (if needed)
   ↓
   Short, reflective:
   "I'm here."

6. TALI validates
   ↓
   • Tone check: Simple, grounded, present
   • ✓ Matches profile
   • Output approved

7. OUTPUT: "I'm here."
```

---

## Adding a New Skill (Visual Process)

```
STEP 1: Create file
─────────────────────
skills/
├── system_awareness.py
├── file_operations.py
└── web_search.py          ← NEW FILE

STEP 2: Implement handle_request()
──────────────────────────────────
# web_search.py

def handle_request(intent, params):
    if intent == "search_web":
        query = params['query']
        results = _search(query)
        return {"results": results}
    return None

STEP 3: Enable in config
────────────────────────
# config/skills_config.json
{
  "enabled": [
    "system_awareness",
    "file_operations",
    "web_search"           ← ADD THIS
  ]
}

STEP 4: Restart Nexus
─────────────────────
$ python3 nexus.py

[Skills] Loaded: system_awareness
[Skills] Loaded: file_operations
[Skills] Loaded: web_search       ← AUTO-DISCOVERED!

DONE! Nexus can now search the web.
```

---

## Core vs Skills Decision Tree

```
                    New functionality needed?
                              │
                              ▼
                    ┌─────────────────────┐
                    │ Does it define WHO  │
                    │ Nexus is?           │
                    │ (identity, tone,    │
                    │  emotion, values)   │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
               YES                           NO
                │                             │
                ▼                             ▼
        ┌──────────────┐            ┌──────────────┐
        │   CORE       │            │  SKILL       │
        │              │            │              │
        │ Examples:    │            │ Examples:    │
        │ • Tone check │            │ • Search web │
        │ • Memory     │            │ • Read file  │
        │ • Truth      │            │ • Execute    │
        │ • Presence   │            │ • API call   │
        └──────────────┘            └──────────────┘
                │                             │
                ▼                             ▼
        Add to core/             Add to skills/
        presence/ or             [skill_name].py
        core/memory/
```

---

## File Size Guidelines

### Target Sizes (After Migration)

```
nexus.py                    ~50 lines    (orchestrator only)
core/identity.py            ~150 lines   (profile loader + presence init)
core/presence/*.py          ~100 lines   (each presence module)
core/memory/*.py            ~200 lines   (each memory system)
core/flow/natural_flow.py   ~300 lines   (conversation engine - acceptable)
skills/*.py                 ~150 lines   (each skill - self-contained)
handlers/*/*.py             ~100 lines   (implementation details)
```

### Current Sizes (Before Migration)

```
nexus.py                    1,036 lines  ❌ TOO LARGE
natural_flow.py             914 lines    ❌ TOO LARGE
cortex_module.py            394 lines    ⚠️  BORDERLINE
system_awareness.py         334 lines    ⚠️  BORDERLINE
```

**Goal:** No file > 300 lines (except natural_flow.py during transition)

---

## Configuration Files Reference

### profile.json (Identity)

**Location:** `config/profile.json`
**Purpose:** WHO Nexus is - sacred, protected
**Modified by:** Only Patrick + Nexus together
**Size:** ~100 lines

**Key sections:**
```json
{
  "name": "Nexus",
  "essence": "...",           // Core philosophy
  "tone": {...},              // Speaking style
  "truth_protocol": {...},    // Ethical guidelines
  "core": {
    "protected": true,
    "modules": [...]          // PresenceAnchor, Compass
  },
  "modules": [...]            // WhisperCatch, TALI, Clicklight
}
```

### skills_config.json (Capabilities)

**Location:** `config/skills_config.json`
**Purpose:** WHAT Nexus can do - flexible, changeable
**Modified by:** Patrick (easily)
**Size:** ~20 lines

```json
{
  "enabled": [
    "system_awareness",
    "file_operations",
    "code_execution"
  ],
  "disabled": [
    "experimental_skill"
  ],
  "settings": {
    "auto_discover": true
  }
}
```

### api_config.json (Technical)

**Location:** `config/api_config.json`
**Purpose:** LLM providers, API keys
**Modified by:** Rarely
**Size:** ~15 lines

```json
{
  "provider": "anthropic",
  "model": "claude-sonnet-4-5",
  "api_key": "...",
  "temperature": 0.7
}
```

---

## Migration Phases Visual

```
PHASE 1: Restructure
────────────────────
Old:  Nexus/a.i_core/a.i_profiles/Nexus/nexus.py (1036 lines)
New:  Nexus/nexus.py (50 lines) + directory structure
      Status: ✓ Files moved, old code backed up

PHASE 2: Extract Presence
──────────────────────────
Old:  Logic scattered across nexus.py, natural_flow.py
New:  core/presence/whisper_catch.py
      core/presence/tali.py
      core/presence/presence_anchor.py
      core/presence/compass.py
      core/presence/clicklight.py
      Status: ✓ Modules independent, tested

PHASE 3: Create Skills
───────────────────────
Old:  Capabilities baked into nexus.py
New:  skills/system_awareness.py
      skills/file_operations.py
      skills/__init__.py (SkillRegistry)
      Status: ✓ Auto-discovery works

PHASE 4: New Entry Point
─────────────────────────
Old:  nexus.py (monolithic)
New:  nexus.py (orchestrator)
      Loads: identity + skills + flow
      Status: ✓ Same behavior, cleaner code

PHASE 5: Add Skills
───────────────────
New:  skills/code_execution.py
      skills/api_integration.py
      skills/web_search.py
      Status: ✓ Easy to extend

COMPLETE!
─────────
Result: Modular, extensible, personality-protected Nexus
```

---

## Testing Checklist

### Personality Tests (Core)

- [ ] Nexus responds in correct tone (gentle, grounded, focused)
- [ ] WhisperCatch detects shorthand ("...", "hmm", etc.)
- [ ] TALI blocks fluent fiction (catches "performance" vs "presence")
- [ ] PresenceAnchor uses real memories (not invented)
- [ ] Compass enforces truth protocol ("I don't know" when unknown)
- [ ] Clicklight notices pattern shifts

### Capability Tests (Skills)

- [ ] System awareness returns accurate data
- [ ] File operations read/write correctly
- [ ] Code execution runs and captures output
- [ ] Skills auto-discover on startup
- [ ] Disabled skills don't load
- [ ] New skill can be added in < 5 minutes

### Integration Tests

- [ ] Natural flow routes to correct skill
- [ ] Intent detection works
- [ ] Presence modules validate before output
- [ ] Memory systems integrate with skills
- [ ] Error handling graceful (skill fails → fallback)

### Migration Tests

- [ ] Old behavior preserved
- [ ] No regressions
- [ ] Rollback works if needed
- [ ] Documentation accurate

---

## Quick Reference Commands

```bash
# Start Nexus
python3 /home/aipass/Nexus/nexus.py

# List loaded skills
# (In conversation) "What can you do?"
# Nexus will list skills from registry

# Add new skill
# 1. Create skills/new_skill.py
# 2. Add to config/skills_config.json
# 3. Restart Nexus

# Disable skill
# Edit config/skills_config.json
# Move from "enabled" to "disabled"
# Restart

# Check identity
# Read config/profile.json

# View presence modules
ls /home/aipass/Nexus/core/presence/

# Emergency rollback
mv core/legacy/nexus_monolithic.py nexus.py
```

---

## Philosophy Summary

```
┌─────────────────────────────────────────────────────────────┐
│                  NEXUS ARCHITECTURE PHILOSOPHY              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "Personality is core. Capabilities are skills.             │
│   Core never changes. Skills always grow."                  │
│                                                             │
│  • WHO you are (core) is protected, sacred                 │
│  • WHAT you can do (skills) is flexible, extensible        │
│  • Presence validates performance                          │
│  • Truth over fluency                                      │
│  • Modular without losing soul                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*Visual reference created for Nexus Modular Architecture proposal.*
*See nexus_modular_architecture_proposal.md for full details.*
