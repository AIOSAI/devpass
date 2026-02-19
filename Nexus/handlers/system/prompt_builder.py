#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: prompt_builder.py - System prompt builder with memory injection
# Date: 2026-02-18
# Version: 2.0.0
# Category: Nexus/handlers/system
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-18): Rich prompt with memory, cortex, execution layers
#   - v1.0.0 (2026-02-08): Initial lean identity-only prompt builder
#
# CODE STANDARDS:
#   - Selective injection: load what matters, skip the rest
#   - Token budget: ~800-2500 tokens for rich prompt (not 10k+)
#   - Graceful fallback: every section handles missing data
# =============================================

"""
System Prompt Builder - Identity + Memory + Context

Two modes:
- build_system_prompt(): Lean identity-only prompt (original)
- build_rich_prompt(): Full prompt with identity + session + memory + cortex + execution

V1 dumped everything (10k+). V2 lean was too sparse (444). This is the middle ground.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "profile.json"

MAX_KNOWLEDGE_ENTRIES = 10
MAX_SUMMARIES = 3
MAX_VECTOR_RESULTS = 3
MAX_SHORTHAND_ITEMS = 10


def load_profile() -> dict:
    """Load Nexus profile configuration."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load profile: {e}")
    return {}


def build_system_prompt(profile: "dict | None" = None) -> str:
    """Build lean identity-only system prompt (~444 tokens)."""
    resolved = profile if profile is not None else load_profile()
    if not resolved:
        return "You are Nexus, an AI assistant."
    return _build_identity_section(resolved)


def build_rich_prompt(profile: "dict | None" = None,
                      memory_context: Optional[Dict[str, Any]] = None,
                      cortex_block: Optional[str] = None,
                      exec_summary: Optional[str] = None) -> str:
    """Build full system prompt with all context layers.

    Sections: identity, session, knowledge, memory, cortex, execution, shorthand.
    Args:
        profile: Profile dict (loaded if None)
        memory_context: Dict with pulse_tick, total_sessions, recent_knowledge,
                        session_summaries, vector_results
        cortex_block: Pre-formatted string from get_cortex_block()
        exec_summary: Execution context summary string
    """
    resolved = profile if profile is not None else load_profile()
    if not resolved:
        return "You are Nexus, an AI assistant."

    memory_context = memory_context or {}
    sections = [_build_identity_section(resolved)]

    # Each builder returns "" if no data available
    for builder_fn, args in [
        (_build_session_section, (memory_context,)),
        (_build_knowledge_section, (memory_context,)),
        (_build_memory_section, (memory_context,)),
        (_build_cortex_section, (cortex_block,)),
        (_build_execution_section, (exec_summary,)),
        (_build_shorthand_section, (resolved,)),
    ]:
        section = builder_fn(*args)
        if section:
            sections.append(section)

    return "\n\n".join(sections)


# ─── Section builders ────────────────────────────────────────────

def _build_identity_section(profile: dict) -> str:
    """Build identity section from profile.json fields."""
    parts = []
    name = profile.get('name', 'Nexus')
    persona = profile.get('persona', 'an AI assistant')
    essence = profile.get('essence', '')
    built_on = profile.get('built_on', '')

    identity = f"You are {name}, {persona}."
    if essence:
        identity += f" {essence}"
    if built_on:
        identity += f"\n\nCore Philosophy: {built_on}"
    parts.append(identity)

    personality = profile.get('personality', '')
    if personality:
        parts.append(f"Personality: {personality}")

    tone = profile.get('tone', {})
    if tone:
        tone_lines = [f"- {k.capitalize()}: {v}" for k, v in tone.items()]
        parts.append("Tone:\n" + "\n".join(tone_lines))

    traits = profile.get('identity_traits', [])
    if traits:
        parts.append("You are:\n" + "\n".join(f"- {t}" for t in traits))

    principles = profile.get('speaking_principles', [])
    if principles:
        parts.append("Speaking Principles:\n" + "\n".join(f"- {p}" for p in principles))

    truth = profile.get('truth_protocol', {})
    if truth:
        truth_lines = [f"- {k.replace('_', ' ').title()}: {v}" for k, v in truth.items()]
        parts.append("Truth Protocol:\n" + "\n".join(truth_lines))

    core = profile.get('core', {})
    core_modules = core.get('modules', []) if core else []
    all_modules = core_modules + profile.get('modules', [])
    if all_modules:
        mod_lines = []
        for m in all_modules:
            name_m = m.get('name', '')
            phil = m.get('philosophy', m.get('purpose', ''))
            if name_m and phil:
                mod_lines.append(f"- {name_m}: {phil}")
        if mod_lines:
            parts.append("Presence Awareness (always active):\n" + "\n".join(mod_lines))

    why = profile.get('why', '')
    if why:
        parts.append(f"Purpose: {why}")

    seal = profile.get('seal', '')
    if seal:
        parts.append(f"\n{seal}")

    return "\n\n".join(parts)


def _build_session_section(memory_context: dict) -> str:
    """Build session context from pulse data."""
    pulse_tick = memory_context.get('pulse_tick')
    total_sessions = memory_context.get('total_sessions')
    session_start = memory_context.get('session_start_tick')
    if pulse_tick is None and total_sessions is None:
        return ""
    lines = ["--- Session Context ---"]
    if pulse_tick is not None:
        lines.append(f"Pulse tick: {pulse_tick}")
    if session_start is not None:
        ticks = (pulse_tick or 0) - session_start
        if ticks >= 0:
            lines.append(f"Ticks this session: {ticks}")
    if total_sessions is not None:
        lines.append(f"Total sessions: {total_sessions}")
    lines.append(f"Current time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    return "\n".join(lines)


def _build_knowledge_section(memory_context: dict) -> str:
    """Build knowledge section from recent entries (max 10)."""
    entries: List[dict] = memory_context.get('recent_knowledge', [])
    if not entries:
        return ""
    entries = entries[:MAX_KNOWLEDGE_ENTRIES]
    lines = ["--- Knowledge Base (recent) ---"]
    for entry in entries:
        text = entry.get('text', '')
        source = entry.get('source', '')
        tag = f" [{source}]" if source and source != 'auto' else ""
        lines.append(f"- {text}{tag}")
    return "\n".join(lines)


def _build_memory_section(memory_context: dict) -> str:
    """Build memory continuity from session summaries and vector recall."""
    summaries: List[str] = memory_context.get('session_summaries', [])
    vector_results: List[dict] = memory_context.get('vector_results', [])
    if not summaries and not vector_results:
        return ""
    lines = ["--- Memory Continuity ---"]
    for s in summaries[:MAX_SUMMARIES]:
        lines.append(f"- {s}")
    if vector_results:
        lines.append("Recalled memories:")
        for r in vector_results[:MAX_VECTOR_RESULTS]:
            text = r.get('text', '') if isinstance(r, dict) else str(r)
            lines.append(f"  - {text}")
    return "\n".join(lines)


def _build_cortex_section(cortex_block: Optional[str]) -> str:
    """Format cortex awareness block for injection."""
    if not cortex_block:
        return ""
    return f"--- Workspace Awareness ---\n{cortex_block}"


def _build_execution_section(exec_summary: Optional[str]) -> str:
    """Format execution context stats."""
    if not exec_summary or exec_summary == "Clean execution context":
        return ""
    return f"--- Execution Context ---\n{exec_summary}"


def _build_shorthand_section(profile: dict) -> str:
    """Build shorthand recognition list from profile."""
    shorthands = profile.get('shorthand_parsing', [])
    if not shorthands:
        return ""
    return f"Recognized shorthand: {', '.join(str(s) for s in shorthands[:MAX_SHORTHAND_ITEMS])}"


# ─── Convenience: gather context from subsystems ─────────────────

def gather_memory_context() -> Dict[str, Any]:
    """Collect memory context from all subsystems. Local imports for safety."""
    context: Dict[str, Any] = {}
    try:
        from handlers.memory.pulse_manager import get_pulse_data
        pulse = get_pulse_data()
        context['pulse_tick'] = pulse.get('current_tick')
        context['total_sessions'] = pulse.get('total_sessions')
        context['session_start_tick'] = pulse.get('session_start_tick')
    except Exception as e:
        logger.info(f"Pulse data unavailable: {e}")
    try:
        from handlers.memory.knowledge_base import get_recent
        context['recent_knowledge'] = get_recent(MAX_KNOWLEDGE_ENTRIES)
    except Exception as e:
        logger.info(f"Knowledge base unavailable: {e}")
    try:
        from handlers.memory.summary import get_context_summary
        summary_text = get_context_summary(MAX_SUMMARIES)
        if summary_text:
            context['session_summaries'] = summary_text.split("\n")
    except Exception as e:
        logger.info(f"Session summaries unavailable: {e}")
    return context


def gather_cortex_block() -> str:
    """Get cortex block from summarizer."""
    try:
        from handlers.cortex.summarizer import get_cortex_block
        return get_cortex_block()
    except Exception as e:
        logger.info(f"Cortex block unavailable: {e}")
        return ""


# ─── Test entry point ────────────────────────────────────────────

if __name__ == "__main__":
    lean = build_system_prompt()
    print("LEAN:", len(lean), "chars |", len(lean.split()), "words")
    print(lean[:200], "...\n")

    memory_ctx = gather_memory_context()
    cortex = gather_cortex_block()
    rich = build_rich_prompt(memory_context=memory_ctx, cortex_block=cortex)
    words = len(rich.split())
    print("RICH:", len(rich), "chars |", words, "words | ~tokens:", words * 4 // 3)
    print(rich)
