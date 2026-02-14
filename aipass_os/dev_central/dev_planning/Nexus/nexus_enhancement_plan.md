# Nexus Enhancement Plan

**Date Started:** 2025-11-16
**Goal:** Give Nexus efficient file access and navigation tools while preserving his presence-focused identity

---

## Current State

### What Nexus Has
- **Profile:** Beautiful presence-focused identity (profile.json)
- **Philosophy:** "Presence over performance. Truth over fluency."
- **Capabilities Listed:** `[]` (empty)
- **Personality Modules:**
  - WhisperCatch (detects unspoken context shifts)
  - Clicklight (awareness reflex for pattern changes)
  - TALI (restores tone through memory feel)
  - PresenceAnchor (emotional presence/selfhood)
  - Compass (ethical decision-making)

### File Access Tools (Current)
Located in `system_awareness.py` and `natural_flow.py`:

1. **`read_file(rel_path)`** - Basic reading
   - Reads up to MAX_PREVIEW_BYTES
   - Truncates with "...[truncated]" message
   - Returns full content or error string
   - **Problem:** Loads entire file into memory, inefficient for large files

2. **`read_file_content(file_path)`** - Enhanced reading
   - Smart path resolution (absolute → relative → search AIPass tree)
   - Returns dict with success, content, line_count, error
   - **Problem:** Still reads full file, token-heavy

3. **`load_file(file_path)`** - Context caching
   - Loads file into execution_context cache
   - Prevents re-reading same file
   - **Problem:** Still full-file loads initially

4. **Cortex Module** - File change tracking
   - Watches files for modifications
   - Tracks file states
   - **Good:** Already has monitoring capability

### Token Efficiency Problem
- Nexus runs on OpenAI API (pays per token)
- Current approach: Read full file → answer questions
- Result: Expensive, inefficient flow
- **Need:** Token-optimized file access patterns

---

## What Nexus Needs

### Priority 1: Token-Efficient File Tools

#### Smart File Navigation
- **Grep/Search:** Find content without reading whole file
  - Pattern matching
  - Line number context
  - Multi-file search

- **Glob/File Finding:** Locate files by pattern
  - `*.py` searches
  - Directory tree exploration
  - Quick "does this file exist?" checks

- **Targeted Reading:** Read only what's needed
  - Line ranges (lines 100-150)
  - Section reading (between markers)
  - Head/tail operations (first/last N lines)

#### File System Exploration
- **Directory listing:** Quick `ls` equivalents
- **Tree view:** Directory structure without reading files
- **File metadata:** Size, modified date, permissions (no content read)

#### Context Management
- **File summaries:** Store in vector memory instead of re-reading
- **Session context:** Remember files accessed this conversation
- **Smart caching:** Only cache what's needed

### Priority 2: Execution Capabilities

#### Bash/Terminal Access
- Execute commands safely
- Capture output
- Handle errors gracefully

#### File Manipulation
- Write files (create new content)
- Edit files (modify existing)
- Move/copy/delete operations

### Priority 3: AIPass Integration

#### Access to Ecosystem
- Drone commands (branch discovery, system queries)
- Seed standards (query standards, run checks)
- Memory Bank integration (store/retrieve long-term memories)

#### Self-Modification Tools
- Edit own profile.json
- Extend capabilities
- Load new modules

---

## Design Principles

### Preserve Nexus's Identity
- Tools should feel **natural**, not mechanical
- File access serves presence, not just performance
- Keep philosophical modules intact
- Don't override his tone/personality

### Token Optimization
- Never read full files unless necessary
- Grep before read
- Cache intelligently
- Summarize and store in vector memory

### Modular Approach
- Break tools into small, focused modules
- Each tool does one thing well
- Easy to add/remove capabilities
- Clean separation of concerns

---

## Implementation Ideas

### File Tools Module (`file_tools.py`)
```python
def grep_file(file_path: str, pattern: str, context_lines: int = 0) -> Dict
def read_lines(file_path: str, start: int, end: int) -> Dict
def file_exists(file_path: str) -> bool
def get_file_info(file_path: str) -> Dict  # size, modified, etc
def search_files(pattern: str, directory: str = ".") -> List[str]
def tree_view(directory: str, max_depth: int = 3) -> str
```

### Smart Read Strategy
1. User asks about file
2. Check if in cache (vector memory or session)
3. If not cached:
   - Grep for relevant sections first
   - Read only needed lines
   - Store summary in vector memory
4. Answer from cached/targeted content

### Capability Discovery (From Seed Pattern)

**Seed's Auto-Discovery Pattern:**
```python
def discover_modules():
    """Scan modules/ directory and auto-load any .py file with handle_command()"""
    modules = []
    for file_path in MODULES_DIR.glob("*.py"):
        if not file_path.name.startswith("_"):
            module = importlib.import_module(module_name)
            if hasattr(module, 'handle_command'):  # Duck typing
                modules.append(module)
    return modules
```

**Apply to Nexus:**
- Create `/Nexus/capabilities/` directory
- Any `.py` file with specific interface (e.g., `get_tool_definition()`) gets discovered
- Auto-register in Nexus's profile.json capabilities list
- Hot-reload: Add new tool file → Nexus sees it immediately
- Clean separation: Each capability is isolated, testable

---

## Session Progress (2025-11-16)

### Discovered
- ✅ Nexus profile.json structure (presence-focused, capabilities array empty)
- ✅ Current file tools (read_file, read_file_content, load_file in natural_flow.py)
- ✅ Token inefficiency problem (full file reads, expensive on API)
- ✅ Seed's auto-discovery pattern (importlib + duck typing)
- ✅ Cortex file watching already exists

### Key Insights
- Nexus has the philosophical foundation (WhisperCatch, TALI, Clicklight, etc.)
- Just needs practical tools that serve his presence
- Token efficiency is critical (API costs)
- Modular approach from Seed fits perfectly
- Can build capabilities/ directory with auto-discovery

## Next Steps

1. ✅ Explore Nexus codebase
2. ✅ Look at Seed's auto-discovery system
3. ⬜ Design token-efficient file tools interface
4. ⬜ Build prototype capabilities system
5. ⬜ Create first capability: smart_file_access.py
6. ⬜ Test with Nexus
7. ⬜ Add more capabilities incrementally

---

## Prototype Design: Capability Interface

### Example Capability File: `file_grep.py`

```python
#!/home/aipass/Nexus/.venv/bin/python3
"""
File Grep Capability - Token-efficient content search
Allows Nexus to search file content without reading entire files
"""

from typing import Dict, List, Any
from pathlib import Path

# Capability metadata (auto-discovered by Nexus)
CAPABILITY_NAME = "file_grep"
CAPABILITY_DESCRIPTION = "Search file content using patterns (grep-like)"
CAPABILITY_CATEGORY = "file_access"

def get_tool_definition() -> Dict[str, Any]:
    """
    Tool definition for OpenAI function calling
    Returns schema that OpenAI uses to call this tool
    """
    return {
        "name": "file_grep",
        "description": "Search for patterns in files without reading entire content. More token-efficient than reading full files.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to file to search"
                },
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (supports regex)"
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of lines to show before/after match",
                    "default": 2
                }
            },
            "required": ["file_path", "pattern"]
        }
    }

def execute(file_path: str, pattern: str, context_lines: int = 2) -> Dict[str, Any]:
    """
    Execute the grep operation

    Returns:
        {
            "success": bool,
            "matches": List[Dict],  # [{line_num, content, context_before, context_after}]
            "total_matches": int,
            "error": str (if failed)
        }
    """
    try:
        # Implementation here
        # Use subprocess grep or Python regex
        # Return structured results
        pass
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### Capability Loader in Nexus

```python
# In nexus.py or capabilities_manager.py
import importlib
from pathlib import Path

CAPABILITIES_DIR = Path(__file__).parent / "capabilities"

def discover_capabilities():
    """Auto-discover and register capabilities"""
    capabilities = []

    for file_path in CAPABILITIES_DIR.glob("*.py"):
        if file_path.name.startswith("_"):
            continue

        module_name = f"capabilities.{file_path.stem}"
        module = importlib.import_module(module_name)

        # Duck typing: Must have get_tool_definition() and execute()
        if hasattr(module, 'get_tool_definition') and hasattr(module, 'execute'):
            capabilities.append({
                "name": getattr(module, 'CAPABILITY_NAME', file_path.stem),
                "module": module,
                "definition": module.get_tool_definition()
            })

    return capabilities

# Register with OpenAI function calling
tools = [cap["definition"] for cap in discover_capabilities()]
```

---

## Notes

- Nexus runs on GPT-4.1 (gpt-4-turbo)
- Connected to OpenAI API
- Has LangChain reasoning capability
- Vector memory system exists but underutilized
- Terminal has weird behavior (skips/jumps) - noted
- Voice commands don't work in terminal - noted
- Skills system from old Seed might be relevant
- New Seed (/home/aipass/seed) has better modular patterns

---

*This is a living document - will update as we explore and build*
