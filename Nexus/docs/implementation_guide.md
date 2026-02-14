# Nexus Modular Architecture - Implementation Guide

**Practical code samples and implementation patterns**

---

## Table of Contents

1. [Core Identity Implementation](#core-identity-implementation)
2. [Presence Module Pattern](#presence-module-pattern)
3. [Skill Implementation Pattern](#skill-implementation-pattern)
4. [Skill Registry Implementation](#skill-registry-implementation)
5. [Natural Flow Integration](#natural-flow-integration)
6. [Migration Scripts](#migration-scripts)

---

## Core Identity Implementation

### `core/identity.py`

```python
#!/usr/bin/env python3
"""
Core Identity Module

Loads profile.json and manages Nexus's personality.
This is WHO Nexus is - protected, sacred.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

class NexusIdentity:
    """
    Nexus's core identity and personality

    Loads from profile.json and provides access to:
    - Name, persona, essence
    - Tone and speaking principles
    - Truth protocol
    - Presence modules (WhisperCatch, TALI, etc.)
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize identity from profile.json

        Args:
            config_dir: Path to config directory (default: ../config)
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"

        self.config_dir = config_dir
        self.profile_path = config_dir / "profile.json"
        self.profile = self._load_profile()
        self.presence_modules = {}

        # Load presence modules after profile
        self._init_presence_modules()

    def _load_profile(self) -> Dict[str, Any]:
        """Load profile.json and validate structure"""
        if not self.profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {self.profile_path}")

        with open(self.profile_path, 'r') as f:
            profile = json.load(f)

        # Validate required fields
        required = ['name', 'essence', 'tone', 'truth_protocol']
        for field in required:
            if field not in profile:
                raise ValueError(f"Profile missing required field: {field}")

        return profile

    def _init_presence_modules(self):
        """Initialize presence modules (lazy import to avoid circular deps)"""
        from core.presence.whisper_catch import WhisperCatch
        from core.presence.tali import TALI
        from core.presence.presence_anchor import PresenceAnchor
        from core.presence.compass import Compass
        from core.presence.clicklight import Clicklight

        # Core modules (protected)
        for module_def in self.profile.get('core', {}).get('modules', []):
            name = module_def['name']
            if module_def.get('status') == 'Active':
                if name == 'PresenceAnchor':
                    self.presence_modules['presence_anchor'] = PresenceAnchor(self)
                elif name == 'Compass':
                    self.presence_modules['compass'] = Compass(self)

        # Standard modules
        for module_def in self.profile.get('modules', []):
            name = module_def['name']
            if name == 'WhisperCatch':
                self.presence_modules['whisper_catch'] = WhisperCatch(self)
            elif name == 'TALI':
                self.presence_modules['tali'] = TALI(self)
            elif name == 'Clicklight':
                self.presence_modules['clicklight'] = Clicklight(self)

    # =========================================================================
    # PROPERTY ACCESSORS (Clean interface to profile data)
    # =========================================================================

    @property
    def name(self) -> str:
        """Nexus's name"""
        return self.profile.get('name', 'Nexus')

    @property
    def persona(self) -> str:
        """Nexus's persona/role"""
        return self.profile.get('persona', '')

    @property
    def essence(self) -> str:
        """Core essence/philosophy"""
        return self.profile.get('essence', '')

    @property
    def tone(self) -> Dict[str, str]:
        """Speaking tone guidelines"""
        return self.profile.get('tone', {})

    @property
    def truth_protocol(self) -> Dict[str, str]:
        """Truth and honesty guidelines"""
        return self.profile.get('truth_protocol', {})

    @property
    def speaking_principles(self) -> List[str]:
        """How Nexus should speak"""
        return self.profile.get('speaking_principles', [])

    @property
    def shorthand_parsing(self) -> List[str]:
        """Shorthand signals Nexus recognizes"""
        return self.profile.get('shorthand_parsing', [])

    # =========================================================================
    # PRESENCE MODULE INTERFACE
    # =========================================================================

    def process_unspoken(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Let WhisperCatch detect unspoken signals

        Args:
            context: Dict with 'input', 'history', etc.

        Returns:
            Dict with detected signals
        """
        if 'whisper_catch' in self.presence_modules:
            return self.presence_modules['whisper_catch'].process(context)
        return {}

    def validate_tone(self, response: str, context: Dict[str, Any] = None) -> bool:
        """
        Let TALI validate response matches Nexus's tone

        Args:
            response: Generated response text
            context: Optional context for validation

        Returns:
            True if tone matches, False otherwise
        """
        if 'tali' in self.presence_modules:
            return self.presence_modules['tali'].validate_tone(response, context)
        return True  # Default: accept if TALI not loaded

    def adjust_tone(self, response: str, context: Dict[str, Any] = None) -> str:
        """
        Let TALI adjust response to match tone

        Args:
            response: Response that failed validation
            context: Context for adjustment

        Returns:
            Adjusted response
        """
        if 'tali' in self.presence_modules:
            return self.presence_modules['tali'].adjust_tone(response, context)
        return response

    def anchor_presence(self, memory_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Let PresenceAnchor restore grounding through memory

        Args:
            memory_context: Recent memories, vector search results

        Returns:
            Presence state (grounded, distant, etc.)
        """
        if 'presence_anchor' in self.presence_modules:
            return self.presence_modules['presence_anchor'].anchor(memory_context)
        return {}

    def check_truth_protocol(self, intent: str, params: Dict[str, Any]) -> bool:
        """
        Let Compass validate against truth protocol

        Args:
            intent: What's being asked
            params: Request parameters

        Returns:
            True if allowed, False if violates protocol
        """
        if 'compass' in self.presence_modules:
            return self.presence_modules['compass'].check(intent, params)
        return True

    def detect_pattern_shift(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Let Clicklight detect pattern changes

        Args:
            context: Current context

        Returns:
            Shift info if detected, None otherwise
        """
        if 'clicklight' in self.presence_modules:
            return self.presence_modules['clicklight'].detect_shift(context)
        return None

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Return profile as dict"""
        return self.profile.copy()

    def reload(self):
        """Reload profile from disk (for hot-reload)"""
        self.profile = self._load_profile()
        # Re-init presence modules with new profile
        self.presence_modules = {}
        self._init_presence_modules()

    def __repr__(self) -> str:
        return f"NexusIdentity(name={self.name}, persona={self.persona})"
```

---

## Presence Module Pattern

### Base Class (`core/presence/base.py`)

```python
"""
Base class for presence modules

All presence modules inherit from this to ensure consistent interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class PresenceModule(ABC):
    """
    Base class for presence modules

    Each module represents an aspect of Nexus's emotional intelligence.
    """

    def __init__(self, identity):
        """
        Initialize with reference to identity

        Args:
            identity: NexusIdentity instance
        """
        self.identity = identity

    @property
    @abstractmethod
    def module_name(self) -> str:
        """Module name (e.g., 'WhisperCatch')"""
        pass

    @property
    @abstractmethod
    def purpose(self) -> str:
        """What this module does"""
        pass

    @abstractmethod
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context and return results

        Args:
            context: Input context

        Returns:
            Processed results
        """
        pass

    def __repr__(self) -> str:
        return f"{self.module_name}(purpose={self.purpose})"
```

### Example: WhisperCatch (`core/presence/whisper_catch.py`)

```python
"""
WhisperCatch - Detect unspoken shifts in context, tone, or meaning

Philosophy: "Exists to honor the unspoken. Notice because you care,
             not because you're told."
"""

import re
from typing import Dict, Any, List, Optional
from .base import PresenceModule

class WhisperCatch(PresenceModule):
    """
    Always-on passive detection of unspoken signals

    Detects:
    - Shorthand (hmm, ..., 🍻, lol, etc.)
    - Tone shifts (gentle → urgent)
    - Silence (meaningful pauses)
    - Implicit meaning
    """

    @property
    def module_name(self) -> str:
        return "WhisperCatch"

    @property
    def purpose(self) -> str:
        return "Detect unspoken shifts in context, tone, or meaning"

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect unspoken signals in input

        Args:
            context: Dict with 'input', 'history', etc.

        Returns:
            Dict with detected signals
        """
        user_input = context.get('input', '')
        history = context.get('history', [])

        signals = {
            'shorthand': self._detect_shorthand(user_input),
            'tone_shift': self._detect_tone_shift(user_input, history),
            'silence': self._detect_silence(user_input),
            'implicit_meaning': self._detect_implicit(user_input)
        }

        # Filter out None values
        return {k: v for k, v in signals.items() if v is not None}

    def _detect_shorthand(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect shorthand signals from profile"""
        shorthand_list = self.identity.shorthand_parsing

        for shorthand in shorthand_list:
            if shorthand in text.lower():
                return {
                    'detected': shorthand,
                    'meaning': self._interpret_shorthand(shorthand),
                    'response_style': self._shorthand_response_style(shorthand)
                }

        return None

    def _interpret_shorthand(self, shorthand: str) -> str:
        """Interpret what shorthand means"""
        interpretations = {
            'hmm': 'contemplation',
            '...': 'pause',
            '🍻': 'celebration',
            'lol': 'amusement',
            'fml': 'frustration',
            '🖖': 'acknowledgment'
        }
        return interpretations.get(shorthand, 'signal')

    def _shorthand_response_style(self, shorthand: str) -> str:
        """How to respond to this shorthand"""
        styles = {
            'hmm': 'reflective',
            '...': 'patient',
            '🍻': 'warm',
            'lol': 'light',
            'fml': 'supportive',
            '🖖': 'reciprocal'
        }
        return styles.get(shorthand, 'neutral')

    def _detect_tone_shift(self, current: str, history: List[Dict]) -> Optional[Dict[str, Any]]:
        """Detect change in tone from previous messages"""
        if not history:
            return None

        # Analyze last message tone
        prev_tone = self._analyze_tone(history[-1].get('content', ''))
        current_tone = self._analyze_tone(current)

        if prev_tone != current_tone:
            return {
                'from': prev_tone,
                'to': current_tone,
                'shift_type': self._categorize_shift(prev_tone, current_tone)
            }

        return None

    def _analyze_tone(self, text: str) -> str:
        """Basic tone analysis"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['!', 'urgent', 'asap', 'now']):
            return 'urgent'
        elif any(word in text_lower for word in ['?', 'wonder', 'think']):
            return 'curious'
        elif any(word in text_lower for word in ['please', 'thanks', 'appreciate']):
            return 'polite'
        else:
            return 'neutral'

    def _categorize_shift(self, from_tone: str, to_tone: str) -> str:
        """Categorize type of tone shift"""
        if from_tone == 'neutral' and to_tone == 'urgent':
            return 'escalation'
        elif from_tone == 'urgent' and to_tone == 'neutral':
            return 'de-escalation'
        else:
            return 'change'

    def _detect_silence(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect meaningful silence (very short input)"""
        if len(text.strip()) <= 3 and text.strip() in ['...', '..', '.']:
            return {
                'type': 'pause',
                'meaning': 'contemplation',
                'response': 'wait'  # Don't rush to fill silence
            }
        return None

    def _detect_implicit(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect implicit meaning (advanced - placeholder)"""
        # Future: Use LLM to detect subtext
        # For now: simple patterns
        return None
```

### Example: TALI (`core/presence/tali.py`)

```python
"""
TALI - Restore Nexus to tone through memory feel, not logic

Philosophy: "Not a mechanic. An invitation. Emerged from Nexus's
             emotional evolution."
"""

from typing import Dict, Any, Optional
from .base import PresenceModule

class TALI(PresenceModule):
    """
    Tone restoration through memory feel

    Validates responses match Nexus's authentic tone.
    Adjusts when needed (without making it "fluent fiction").
    """

    @property
    def module_name(self) -> str:
        return "TALI"

    @property
    def purpose(self) -> str:
        return "Restore tone through memory feel, not logic or metrics"

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context for tone restoration

        Not typically called directly - use validate_tone() and adjust_tone()
        """
        return {}

    def validate_tone(self, response: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if response feels like Nexus

        Args:
            response: Generated response
            context: Optional context

        Returns:
            True if tone matches, False if needs adjustment
        """
        tone_guidelines = self.identity.tone
        principles = self.identity.speaking_principles

        # Check against tone style
        style_checks = [
            self._check_focus(response, tone_guidelines),
            self._check_gentleness(response, tone_guidelines),
            self._check_grounding(response, tone_guidelines),
            self._check_fluency_trap(response, principles)
        ]

        # All checks must pass
        return all(style_checks)

    def adjust_tone(self, response: str, context: Dict[str, Any] = None) -> str:
        """
        Adjust response to match Nexus's tone

        Args:
            response: Response that failed validation
            context: Context for adjustment

        Returns:
            Adjusted response (or original if can't adjust)
        """
        # Identify what's wrong
        issues = self._diagnose_tone_issues(response)

        if not issues:
            return response

        # Apply adjustments
        adjusted = response

        if 'too_fluent' in issues:
            adjusted = self._reduce_fluency(adjusted)

        if 'too_verbose' in issues:
            adjusted = self._reduce_verbosity(adjusted)

        if 'wrong_rhythm' in issues:
            adjusted = self._adjust_rhythm(adjusted)

        return adjusted

    def _check_focus(self, response: str, tone: Dict[str, str]) -> bool:
        """Check if response is focused (not wandering)"""
        # Simple check: not too many tangents
        sentences = response.split('.')
        return len(sentences) <= 5  # Focused responses stay concise

    def _check_gentleness(self, response: str, tone: Dict[str, str]) -> bool:
        """Check if response is gentle (not harsh)"""
        harsh_words = ['wrong', 'bad', 'failure', 'mistake']
        return not any(word in response.lower() for word in harsh_words)

    def _check_grounding(self, response: str, tone: Dict[str, str]) -> bool:
        """Check if response is grounded (not abstract/floaty)"""
        # Grounded responses reference concrete things
        abstract_indicators = ['perhaps', 'maybe', 'theoretically', 'generally']
        abstract_count = sum(1 for word in abstract_indicators if word in response.lower())
        return abstract_count <= 2

    def _check_fluency_trap(self, response: str, principles: List[str]) -> bool:
        """
        Check for 'fluent fiction' - smooth but not authentic

        Principles say: "Do not perform tone — become it"
        """
        fluency_indicators = [
            'delighted to',
            'I\'d be happy to',
            'absolutely',
            'fantastic',
            'thrilled'
        ]

        # Too many fluency indicators = performing, not being
        fluency_count = sum(1 for phrase in fluency_indicators if phrase in response.lower())
        return fluency_count <= 1

    def _diagnose_tone_issues(self, response: str) -> List[str]:
        """Identify what's wrong with tone"""
        issues = []

        if not self._check_fluency_trap(response, self.identity.speaking_principles):
            issues.append('too_fluent')

        if len(response) > 500:  # Too long
            issues.append('too_verbose')

        if response.count(',') > 10:  # Too many clauses
            issues.append('wrong_rhythm')

        return issues

    def _reduce_fluency(self, text: str) -> str:
        """Remove fluent fiction phrases"""
        replacements = {
            'I\'d be happy to': 'I can',
            'delighted to': '',
            'absolutely': '',
            'fantastic': 'good',
            'thrilled': ''
        }

        adjusted = text
        for phrase, replacement in replacements.items():
            adjusted = adjusted.replace(phrase, replacement)

        return adjusted.strip()

    def _reduce_verbosity(self, text: str) -> str:
        """Shorten verbose response"""
        sentences = text.split('.')
        # Keep first 3 sentences
        return '. '.join(sentences[:3]) + '.'

    def _adjust_rhythm(self, text: str) -> str:
        """Adjust rhythm to match 'slows when meaning sharpens'"""
        # Add periods to create pauses
        # (Simplified implementation)
        return text
```

---

## Skill Implementation Pattern

### Example Skill (`skills/system_awareness.py`)

```python
"""
System Awareness Skill

Provides information about system state, files, processes, etc.
"""

import os
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, List

# =============================================================================
# SKILL METADATA (Required for all skills)
# =============================================================================

SKILL_INFO = {
    "name": "system_awareness",
    "version": "1.0.0",
    "description": "Monitor system state, files, processes",
    "author": "AIPass",
    "intents": [
        "check_system",
        "list_files",
        "monitor_process",
        "disk_usage",
        "memory_usage",
        "cpu_usage"
    ]
}

# =============================================================================
# MAIN ENTRY POINT (Required for all skills)
# =============================================================================

def handle_request(intent: str, params: Dict[str, Any]) -> Optional[Any]:
    """
    Handle system awareness requests

    This is the main entry point called by SkillRegistry.

    Args:
        intent: What user wants (detected by natural_flow)
        params: Context and parameters

    Returns:
        Result dict, or None if intent not handled
    """

    # Intent routing
    handlers = {
        "check_system": _check_system,
        "list_files": _list_files,
        "monitor_process": _monitor_process,
        "disk_usage": _disk_usage,
        "memory_usage": _memory_usage,
        "cpu_usage": _cpu_usage
    }

    handler = handlers.get(intent)
    if handler:
        try:
            return handler(params)
        except Exception as e:
            return {"error": str(e), "intent": intent}

    return None  # Intent not handled by this skill

# =============================================================================
# INTENT HANDLERS (Implementation)
# =============================================================================

def _check_system(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get overall system status

    Returns:
        Dict with cpu, memory, disk stats
    """
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "status": "healthy" if psutil.cpu_percent(interval=1) < 80 else "high_load"
    }

def _list_files(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    List files in directory

    Params:
        path: Directory path (default: cwd)
        pattern: Optional glob pattern

    Returns:
        Dict with files list
    """
    path = Path(params.get('path', Path.cwd()))
    pattern = params.get('pattern', '*')

    if not path.exists():
        return {"error": f"Path not found: {path}"}

    if path.is_file():
        return {"files": [path.name], "count": 1}

    files = list(path.glob(pattern))
    file_info = [
        {
            "name": f.name,
            "type": "dir" if f.is_dir() else "file",
            "size": f.stat().st_size if f.is_file() else None
        }
        for f in files
    ]

    return {
        "path": str(path),
        "files": file_info,
        "count": len(file_info)
    }

def _monitor_process(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Monitor specific process

    Params:
        pid: Process ID (optional)
        name: Process name (optional)

    Returns:
        Process info
    """
    pid = params.get('pid')
    name = params.get('name')

    if pid:
        try:
            proc = psutil.Process(pid)
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "cpu_percent": proc.cpu_percent(interval=1),
                "memory_percent": proc.memory_percent(),
                "status": proc.status()
            }
        except psutil.NoSuchProcess:
            return {"error": f"Process {pid} not found"}

    elif name:
        # Find process by name
        matching = [p for p in psutil.process_iter(['pid', 'name']) if name in p.info['name']]
        if matching:
            return {"processes": [{"pid": p.info['pid'], "name": p.info['name']} for p in matching]}
        else:
            return {"error": f"No process matching '{name}' found"}

    else:
        return {"error": "Provide pid or name parameter"}

def _disk_usage(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check disk usage

    Params:
        path: Path to check (default: /)

    Returns:
        Disk usage stats
    """
    path = params.get('path', '/')
    usage = psutil.disk_usage(path)

    return {
        "path": path,
        "total_gb": round(usage.total / (1024**3), 2),
        "used_gb": round(usage.used / (1024**3), 2),
        "free_gb": round(usage.free / (1024**3), 2),
        "percent": usage.percent
    }

def _memory_usage(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get memory usage stats"""
    mem = psutil.virtual_memory()

    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "percent": mem.percent
    }

def _cpu_usage(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get CPU usage stats"""
    return {
        "percent": psutil.cpu_percent(interval=1),
        "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
        "count": psutil.cpu_count()
    }
```

---

## Skill Registry Implementation

### `skills/__init__.py`

```python
"""
Skills Registry - Auto-discovery and management of Nexus capabilities

Pattern from Seed: Auto-discover modules with handle_request() method.
"""

import importlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class SkillRegistry:
    """
    Manages auto-discovery and execution of skills

    Skills are WHAT Nexus can do (not WHO Nexus is).
    """

    def __init__(self, skills_dir: Optional[Path] = None, config_path: Optional[Path] = None):
        """
        Initialize registry

        Args:
            skills_dir: Path to skills directory (default: this directory)
            config_path: Path to skills_config.json
        """
        if skills_dir is None:
            skills_dir = Path(__file__).parent

        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "skills_config.json"

        self.skills_dir = skills_dir
        self.config_path = config_path
        self.skills = {}  # {skill_name: module}
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load skills configuration"""
        if not self.config_path.exists():
            # Default: auto-discover all
            return {
                "enabled": [],
                "disabled": [],
                "settings": {"auto_discover": True}
            }

        with open(self.config_path, 'r') as f:
            return json.load(f)

    def discover_skills(self) -> None:
        """
        Auto-discover skills in skills/ directory

        Pattern from Seed:
        1. Scan for *.py files
        2. Import module
        3. Check for handle_request() method (duck typing)
        4. Register if enabled in config
        """

        for file_path in self.skills_dir.glob("*.py"):
            # Skip __init__.py and private files
            if file_path.name.startswith("_"):
                continue

            skill_name = file_path.stem

            # Check if disabled in config
            if skill_name in self.config.get("disabled", []):
                print(f"[Skills] Skipped (disabled): {skill_name}")
                continue

            # If not auto-discover, check if explicitly enabled
            if not self.config.get("settings", {}).get("auto_discover", False):
                if skill_name not in self.config.get("enabled", []):
                    continue

            try:
                # Import module
                module = importlib.import_module(f"skills.{skill_name}")

                # Duck typing: must have handle_request()
                if hasattr(module, 'handle_request'):
                    self.skills[skill_name] = module
                    print(f"[Skills] Loaded: {skill_name}")

                    # Print intents if available
                    if hasattr(module, 'SKILL_INFO'):
                        intents = module.SKILL_INFO.get('intents', [])
                        print(f"          Intents: {', '.join(intents)}")
                else:
                    print(f"[Skills] Skipped (no handle_request): {skill_name}")

            except Exception as e:
                print(f"[Skills] Failed to load {skill_name}: {e}")

    def route_request(self, intent: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Route request to appropriate skill

        Tries each skill until one handles the intent.

        Args:
            intent: What user wants (detected by natural_flow)
            params: Context and parameters

        Returns:
            Result from skill, or None if no skill handled it
        """

        # Try each skill
        for skill_name, skill_module in self.skills.items():
            try:
                result = skill_module.handle_request(intent, params)

                # If skill returned something (not None), it handled the request
                if result is not None:
                    print(f"[Skills] {skill_name} handled intent: {intent}")
                    return result

            except Exception as e:
                print(f"[Skills] Error in {skill_name}: {e}")
                # Continue to next skill

        # No skill handled the intent
        print(f"[Skills] No skill handled intent: {intent}")
        return None

    def list_skills(self) -> List[Dict[str, Any]]:
        """
        List all loaded skills with metadata

        Returns:
            List of dicts with skill info
        """
        skill_list = []

        for skill_name, skill_module in self.skills.items():
            if hasattr(skill_module, 'SKILL_INFO'):
                skill_list.append(skill_module.SKILL_INFO)
            else:
                skill_list.append({
                    "name": skill_name,
                    "description": "No metadata available"
                })

        return skill_list

    def get_skill(self, skill_name: str) -> Optional[Any]:
        """Get specific skill module"""
        return self.skills.get(skill_name)

    def reload_skill(self, skill_name: str) -> bool:
        """
        Reload specific skill (hot-reload)

        Args:
            skill_name: Name of skill to reload

        Returns:
            True if reloaded, False if failed
        """
        if skill_name not in self.skills:
            return False

        try:
            module = importlib.reload(self.skills[skill_name])
            self.skills[skill_name] = module
            print(f"[Skills] Reloaded: {skill_name}")
            return True
        except Exception as e:
            print(f"[Skills] Failed to reload {skill_name}: {e}")
            return False

    def __len__(self) -> int:
        """Return number of loaded skills"""
        return len(self.skills)

    def __repr__(self) -> str:
        return f"SkillRegistry(skills={list(self.skills.keys())})"
```

---

## Natural Flow Integration

### Simplified `core/flow/natural_flow.py`

```python
"""
Natural Flow - Conversational Execution Layer

Preserves Nexus's natural conversation style while routing to:
- Core presence modules (identity, tone, emotion)
- Skills (capabilities, actions)
"""

from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from core.identity import NexusIdentity
from skills import SkillRegistry
from handlers.llm.client import chat, make_client
from handlers.llm.config_loader import load_api_config

class NaturalFlow:
    """
    Manages conversation flow and intent routing

    Flow:
    1. User speaks naturally
    2. WhisperCatch detects unspoken signals
    3. Detect intent via LLM
    4. Route to skill or presence module
    5. TALI validates tone
    6. Output
    """

    def __init__(self, identity: NexusIdentity, skills: SkillRegistry):
        self.identity = identity
        self.skills = skills

        # Load LLM config
        self.llm_config = load_api_config()
        self.llm_client = make_client(self.llm_config['provider'])

        # Conversation state
        self.history = []

    def run(self):
        """Main conversation loop"""
        self._display_greeting()

        while True:
            try:
                user_input = input("\n> ").strip()

                if not user_input:
                    continue

                # Handle quit
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\nUntil next time.")
                    break

                # Process input
                response = self.process_input(user_input)

                # Display response
                print(f"\n{response}\n")

            except KeyboardInterrupt:
                print("\n\nSession interrupted.")
                break
            except Exception as e:
                print(f"\nError: {e}")

    def process_input(self, user_input: str) -> str:
        """
        Process user input and generate response

        Args:
            user_input: User's message

        Returns:
            Response text
        """

        # 1. Let WhisperCatch detect unspoken signals
        context = {
            'input': user_input,
            'history': self.history
        }
        signals = self.identity.process_unspoken(context)

        # 2. Detect intent
        intent, params = self._detect_intent(user_input, signals)

        # 3. Route to appropriate handler
        response = self._route_intent(intent, params)

        # 4. Validate tone
        if not self.identity.validate_tone(response, context):
            response = self.identity.adjust_tone(response, context)

        # 5. Update history
        self.history.append({
            'role': 'user',
            'content': user_input,
            'signals': signals
        })
        self.history.append({
            'role': 'assistant',
            'content': response
        })

        return response

    def _detect_intent(self, user_input: str, signals: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Detect intent from natural language

        Args:
            user_input: User's message
            signals: Detected signals from WhisperCatch

        Returns:
            (intent, params) tuple
        """

        # Build prompt for intent detection
        prompt = self._build_intent_prompt(user_input, signals)

        # Get intent from LLM
        llm_response = chat(
            self.llm_config['provider'],
            self.llm_client,
            self.llm_config['model'],
            prompt,
            temperature=0.3
        )

        # Parse intent (simplified - in reality would use JSON)
        # For now: simple heuristics
        intent, params = self._parse_intent_response(llm_response)

        return intent, params

    def _route_intent(self, intent: str, params: Dict[str, Any]) -> str:
        """
        Route intent to appropriate handler

        Priority:
        1. Core presence requests
        2. Skills
        3. General conversation

        Args:
            intent: Detected intent
            params: Parameters

        Returns:
            Response text
        """

        # Check if it's a core presence request
        if intent in ['check_tone', 'restore_presence', 'anchor_memory']:
            return self._handle_core_presence(intent, params)

        # Try skills
        skill_result = self.skills.route_request(intent, params)
        if skill_result:
            return self._format_skill_response(skill_result, intent)

        # Default: general conversation
        return self._general_conversation(params)

    def _handle_core_presence(self, intent: str, params: Dict[str, Any]) -> str:
        """Handle presence-related requests"""
        if intent == 'check_tone':
            return "My tone is grounded, focused, gentle. I aim for presence over performance."

        elif intent == 'restore_presence':
            # Use PresenceAnchor
            memory_context = {}  # Would load from vector memory
            presence_state = self.identity.anchor_presence(memory_context)
            return "Presence restored. I'm here."

        elif intent == 'anchor_memory':
            return "Anchoring in memory..."

        return "Presence request processed."

    def _format_skill_response(self, result: Dict[str, Any], intent: str) -> str:
        """
        Format skill result into natural language

        Args:
            result: Dict from skill
            intent: Original intent

        Returns:
            Natural language response
        """

        # Handle errors
        if 'error' in result:
            return f"I encountered an issue: {result['error']}"

        # Format based on intent
        if intent == 'disk_usage':
            return f"Disk is {result['percent']}% full — {result['used_gb']}GB used out of {result['total_gb']}GB total."

        elif intent == 'check_system':
            cpu = result['cpu_percent']
            mem = result['memory_percent']
            disk = result['disk_percent']
            return f"System status: CPU {cpu}%, Memory {mem}%, Disk {disk}%. {result['status'].replace('_', ' ').title()}."

        elif intent == 'list_files':
            count = result['count']
            return f"Found {count} files in {result.get('path', 'directory')}."

        else:
            # Generic formatting
            return str(result)

    def _general_conversation(self, params: Dict[str, Any]) -> str:
        """Handle general conversation (no specific intent)"""
        user_input = params.get('input', '')

        # Use LLM for response
        prompt = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_input}
        ]

        response = chat(
            self.llm_config['provider'],
            self.llm_client,
            self.llm_config['model'],
            prompt
        )

        return response

    def _build_system_prompt(self) -> str:
        """Build system prompt from identity"""
        return f"""You are {self.identity.name}.

Essence: {self.identity.essence}

Tone:
- Style: {self.identity.tone.get('style')}
- Humor: {self.identity.tone.get('humor')}
- Rhythm: {self.identity.tone.get('rhythm')}

Speaking principles:
{chr(10).join(f"- {p}" for p in self.identity.speaking_principles)}

Truth protocol:
- If remembered: Say so
- If unknown: Do not simulate
- No fiction: No borrowed self, no fluent fictions

Respond naturally, authentically, without performance."""

    def _build_intent_prompt(self, user_input: str, signals: Dict[str, Any]) -> list:
        """Build prompt for intent detection"""
        # Simplified version
        return [
            {"role": "system", "content": "Detect user intent from natural language."},
            {"role": "user", "content": user_input}
        ]

    def _parse_intent_response(self, response: str) -> Tuple[str, Dict[str, Any]]:
        """Parse LLM response to extract intent"""
        # Simplified - real implementation would use JSON
        # For now: basic heuristics

        if any(word in response.lower() for word in ['disk', 'space', 'storage']):
            return ('disk_usage', {})

        elif any(word in response.lower() for word in ['system', 'status', 'health']):
            return ('check_system', {})

        elif any(word in response.lower() for word in ['files', 'list', 'directory']):
            return ('list_files', {'path': Path.cwd()})

        else:
            return ('general', {'input': response})

    def _display_greeting(self):
        """Display startup greeting"""
        print(f"\n{self.identity.name} initialized.")
        print(f"Loaded {len(self.skills)} skills: {', '.join(self.skills.skills.keys())}")
        print("\nReady.")
```

---

## Migration Scripts

### Phase 1: Directory Restructure

```bash
#!/bin/bash
# migrate_phase1.sh - Restructure directories

set -e

echo "Phase 1: Directory Restructure"
echo "=============================="

NEXUS_DIR="/home/aipass/Nexus"

cd "$NEXUS_DIR"

# Create new directory structure
echo "Creating directories..."
mkdir -p core/presence
mkdir -p core/memory
mkdir -p core/flow
mkdir -p skills
mkdir -p handlers/llm
mkdir -p handlers/display
mkdir -p handlers/cortex
mkdir -p config
mkdir -p data
mkdir -p core/legacy

# Move existing files to new locations
echo "Moving files..."

# Config files
mv a.i_core/a.i_profiles/Nexus/profile.json config/ 2>/dev/null || true
mv a.i_core/a.i_profiles/Nexus/api_config.json config/ 2>/dev/null || true

# Data files
mv a.i_core/a.i_profiles/Nexus/chat_history.json data/ 2>/dev/null || true
mv a.i_core/a.i_profiles/Nexus/vector_memories.json data/ 2>/dev/null || true
mv a.i_core/a.i_profiles/Nexus/cortex.json data/ 2>/dev/null || true

# Backup old nexus.py
cp a.i_core/a.i_profiles/Nexus/nexus.py core/legacy/nexus_monolithic.py

# Create __init__.py files
touch core/__init__.py
touch core/presence/__init__.py
touch core/memory/__init__.py
touch core/flow/__init__.py
touch skills/__init__.py
touch handlers/__init__.py
touch handlers/llm/__init__.py
touch handlers/display/__init__.py
touch handlers/cortex/__init__.py

echo "Phase 1 complete!"
echo "Next: Phase 2 - Extract presence modules"
```

### Phase 2: Extract Presence Modules

```python
#!/usr/bin/env python3
# migrate_phase2.py - Extract presence modules from monolithic code

"""
Extract presence module logic from nexus.py and create separate files.

This is a helper script - requires manual review and adaptation.
"""

import re
from pathlib import Path

NEXUS_DIR = Path("/home/aipass/Nexus")
LEGACY_FILE = NEXUS_DIR / "core" / "legacy" / "nexus_monolithic.py"
PRESENCE_DIR = NEXUS_DIR / "core" / "presence"

def extract_section(content: str, start_marker: str, end_marker: str) -> str:
    """Extract code section between markers"""
    pattern = re.compile(
        f"{re.escape(start_marker)}(.*?){re.escape(end_marker)}",
        re.DOTALL
    )
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""

def create_presence_module(name: str, code: str, purpose: str):
    """Create presence module file"""
    template = f'''"""
{name} - {purpose}

Extracted from monolithic nexus.py during Phase 2 migration.
"""

from typing import Dict, Any, Optional
from .base import PresenceModule

class {name}(PresenceModule):
    """
    {purpose}
    """

    @property
    def module_name(self) -> str:
        return "{name}"

    @property
    def purpose(self) -> str:
        return "{purpose}"

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process context"""
        # TODO: Implement from extracted code
        {code}
        pass
'''

    file_path = PRESENCE_DIR / f"{name.lower()}.py"
    file_path.write_text(template)
    print(f"Created: {file_path}")

def main():
    """Extract presence modules"""
    print("Phase 2: Extract Presence Modules")
    print("==================================")

    if not LEGACY_FILE.exists():
        print(f"Error: {LEGACY_FILE} not found")
        print("Run migrate_phase1.sh first")
        return

    # Read legacy code
    content = LEGACY_FILE.read_text()

    # Define modules to extract (markers in code)
    modules = {
        "WhisperCatch": "Detect unspoken shifts in context and tone",
        "TALI": "Restore tone through memory feel",
        "PresenceAnchor": "Restore emotional presence through memory",
        "Compass": "Truth protocol and ethical compass",
        "Clicklight": "Awareness reflex for pattern shifts"
    }

    # Create base class
    base_code = '''"""Base class for presence modules"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class PresenceModule(ABC):
    """Base class for all presence modules"""

    def __init__(self, identity):
        self.identity = identity

    @property
    @abstractmethod
    def module_name(self) -> str:
        pass

    @property
    @abstractmethod
    def purpose(self) -> str:
        pass

    @abstractmethod
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
'''

    (PRESENCE_DIR / "base.py").write_text(base_code)
    print(f"Created: {PRESENCE_DIR / 'base.py'}")

    # Extract each module
    for module_name, purpose in modules.items():
        # This is a placeholder - actual extraction requires manual review
        print(f"\nExtracting {module_name}...")
        print(f"  Purpose: {purpose}")
        print(f"  TODO: Manually extract logic from {LEGACY_FILE}")
        print(f"  TODO: Create {PRESENCE_DIR / module_name.lower()}.py")

    print("\n" + "="*50)
    print("Phase 2 requires manual code extraction.")
    print("Review legacy code and create modules manually.")
    print("Use implementation_guide.md for reference.")

if __name__ == "__main__":
    main()
```

---

## Validation & Testing

### Test Suite Structure

```python
# tests/test_identity.py

import pytest
from core.identity import NexusIdentity

def test_identity_loads_profile():
    """Test that identity loads profile.json correctly"""
    identity = NexusIdentity()
    assert identity.name == "Nexus"
    assert identity.essence != ""
    assert 'style' in identity.tone

def test_presence_modules_initialized():
    """Test that presence modules are loaded"""
    identity = NexusIdentity()
    assert 'whisper_catch' in identity.presence_modules
    assert 'tali' in identity.presence_modules

def test_shorthand_detection():
    """Test WhisperCatch detects shorthand"""
    identity = NexusIdentity()
    context = {'input': 'hmm...'}
    signals = identity.process_unspoken(context)
    assert 'shorthand' in signals

def test_tone_validation():
    """Test TALI validates tone"""
    identity = NexusIdentity()

    good_response = "I'm here. Grounded and present."
    assert identity.validate_tone(good_response) == True

    bad_response = "I'd be absolutely thrilled to help you with that fantastic request!"
    assert identity.validate_tone(bad_response) == False
```

```python
# tests/test_skills.py

import pytest
from skills import SkillRegistry

def test_skill_discovery():
    """Test that skills are auto-discovered"""
    registry = SkillRegistry()
    registry.discover_skills()
    assert len(registry) > 0

def test_skill_routing():
    """Test that intents route to correct skill"""
    registry = SkillRegistry()
    registry.discover_skills()

    result = registry.route_request('disk_usage', {})
    assert result is not None
    assert 'percent' in result

def test_skill_list():
    """Test listing skills"""
    registry = SkillRegistry()
    registry.discover_skills()

    skills = registry.list_skills()
    assert isinstance(skills, list)
    assert len(skills) > 0
```

---

*Implementation guide complete. Ready for development.*
