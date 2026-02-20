#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-

# ===================AIPASS====================
# META DATA HEADER
# Name: nexus.py - Nexus conversational AI main chat loop
# Date: 2026-02-18
# Version: 3.0.0
# Category: Nexus/apps
#
# CHANGELOG (Max 5 entries):
#   - v3.0.0 (2026-02-18): Full v1 feature transfer - config-based provider,
#     LangChain, rich prompt, cortex, execution engine, auto-knowledge,
#     shorthand parsing, error recovery
#   - v2.0.0 (2026-02-14): Basic chat loop with skills and memory
#   - v1.0.0 (2026-02-08): Initial entry point
#
# CODE STANDARDS:
#   - Graceful degradation: every component optional
#   - Error recovery: continue loop on failure, never crash
#   - Config-driven: provider/model from api_config.json
# =============================================

"""
Nexus Conversational AI - Main Entry Point

Launches an interactive chat session powered by a configurable LLM provider.
Integrates: rich prompt builder, cortex file awareness, execution engine,
auto-knowledge extraction, shorthand/tone parsing, skills, and full
4-layer memory (pulse, knowledge, summaries, vectors).

Usage: python3 nexus.py
"""

import sys
import logging
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

NEXUS_DIR = Path(__file__).resolve().parent

# Add Nexus to path for handler imports
if str(NEXUS_DIR) not in sys.path:
    sys.path.insert(0, str(NEXUS_DIR))

logger = logging.getLogger("nexus")

# ---------------------------------------------------------------------------
# Component imports - all optional with graceful fallback
# ---------------------------------------------------------------------------

# System handlers (required)
from handlers.system import ui
from handlers.system.llm_client import make_client, chat

# Config loader (optional - falls back to default OpenAI)
get_ready_config = None
use_langchain = None
try:
    from handlers.system.config_loader import get_ready_config, use_langchain  # type: ignore[assignment]
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logger.info("Config loader unavailable, using default OpenAI")

# LangChain (optional)
make_langchain_client = None
langchain_enhanced_chat = None
lc_is_available = None
try:
    from handlers.system.langchain_interface import (  # type: ignore[assignment]
        make_langchain_client, langchain_enhanced_chat, is_available as lc_is_available
    )
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.info("LangChain interface unavailable")

# Rich prompt builder
build_rich_prompt = None
gather_memory_context = None
gather_cortex_block = None
build_system_prompt = None
try:
    from handlers.system.prompt_builder import (  # type: ignore[assignment]
        build_rich_prompt, gather_memory_context, gather_cortex_block
    )
    RICH_PROMPT_AVAILABLE = True
except ImportError:
    RICH_PROMPT_AVAILABLE = False
    from handlers.system.prompt_builder import build_system_prompt  # type: ignore[assignment]
    logger.info("Rich prompt builder unavailable, using lean prompt")

# Memory handlers
from handlers.memory import (
    save_session, get_session_count,
    start_session as start_pulse_session,
    load_knowledge, get_memory_count as get_vector_count,
    search_memories
)

# Auto-knowledge extraction (optional)
detect_and_store = None
detect_memory_search = None
try:
    from handlers.memory.auto_knowledge import detect_and_store, detect_memory_search  # type: ignore[assignment]
    AUTO_KNOWLEDGE_AVAILABLE = True
except ImportError:
    AUTO_KNOWLEDGE_AVAILABLE = False
    logger.info("Auto-knowledge extraction unavailable")

# Shorthand parser (optional)
parse_shorthand = None
get_tone_context = None
try:
    from handlers.memory.shorthand_parser import (  # type: ignore[assignment]
        parse as parse_shorthand, get_tone_context
    )
    SHORTHAND_AVAILABLE = True
except ImportError:
    SHORTHAND_AVAILABLE = False
    logger.info("Shorthand parser unavailable")

# Skills
from handlers.skills import discover_skills, route_to_skill

# Execution engine (optional)
ExecutionContext = None
detect_intent = None
handle_execution_request = None
try:
    from handlers.execution import (  # type: ignore[assignment]
        ExecutionContext, detect_intent, handle_execution_request
    )
    EXECUTION_AVAILABLE = True
except ImportError:
    EXECUTION_AVAILABLE = False
    logger.info("Execution engine unavailable")

# Cortex file watcher (optional)
CortexFileWatcher = None
reset_session_counters = None
try:
    from handlers.cortex import CortexFileWatcher, reset_session_counters  # type: ignore[assignment]
    CORTEX_AVAILABLE = True
except ImportError:
    CORTEX_AVAILABLE = False
    logger.info("Cortex file watcher unavailable")


# ---------------------------------------------------------------------------
# Initialization helpers
# ---------------------------------------------------------------------------

def _init_provider():
    """Initialize LLM provider from config or default.

    Returns:
        Tuple of (client, provider_name, model, temperature, lc_client)
    """
    lc_client = None

    if CONFIG_AVAILABLE:
        try:
            cfg = get_ready_config()  # type: ignore[misc]
            provider = cfg["provider"]
            model = cfg["model"]
            temperature = cfg["temperature"]
            api_key = cfg["api_key"]

            client = make_client(provider=provider, api_key=api_key, model=model)
            ui.print_status(f"Connected to {provider}: {model}")

            # Try LangChain if enabled
            if LANGCHAIN_AVAILABLE and cfg.get("use_langchain") and lc_is_available():  # type: ignore[misc]
                lc_client = make_langchain_client(  # type: ignore[misc]
                    provider=provider, api_key=api_key,
                    model=model, temperature=temperature
                )
                if lc_client:
                    ui.print_status("LangChain enhanced reasoning ready")

            return client, provider, model, temperature, lc_client
        except Exception as exc:
            ui.print_status(f"Config-based init failed: {exc}", success=False)
            ui.print_status("Falling back to default OpenAI...", success=False)

    # Fallback: default OpenAI
    client = make_client()
    ui.print_status("Connected to OpenAI (default)")
    return client, "openai", "gpt-4.1", 0.7, None


def _build_system_prompt(exec_context=None):
    """Build the system prompt with all available context layers.

    Args:
        exec_context: ExecutionContext instance (optional)

    Returns:
        Complete system prompt string.
    """
    if RICH_PROMPT_AVAILABLE:
        memory_ctx = gather_memory_context()  # type: ignore[misc]
        cortex_block = gather_cortex_block()  # type: ignore[misc]
        exec_summary = exec_context.get_context_summary() if exec_context else None
        return build_rich_prompt(  # type: ignore[misc]
            memory_context=memory_ctx,
            cortex_block=cortex_block,
            exec_summary=exec_summary,
        )

    # Fallback to lean prompt
    return build_system_prompt()  # type: ignore[misc]


def _init_cortex():
    """Start cortex file watcher if available.

    Returns:
        CortexFileWatcher instance or None.
    """
    if not CORTEX_AVAILABLE:
        return None

    try:
        reset_session_counters()  # type: ignore[misc]
        watcher = CortexFileWatcher(watch_dir=NEXUS_DIR)  # type: ignore[misc]
        if watcher.start():
            ui.print_status("Cortex file watcher active")
            return watcher
        ui.print_status("Cortex watcher failed to start", success=False)
    except Exception as exc:
        logger.warning("Cortex init failed: %s", exc)

    return None


# ---------------------------------------------------------------------------
# Chat loop helpers
# ---------------------------------------------------------------------------

def _handle_memory_search(user_input, messages):
    """Check for memory search intent and inject results.

    Args:
        user_input: The user's message.
        messages:   Current message list (modified in place).

    Returns:
        Memory search response string, or None if not a search.
    """
    if not AUTO_KNOWLEDGE_AVAILABLE:
        return None

    is_search, query = detect_memory_search(user_input)  # type: ignore[misc]
    if not is_search or not query:
        return None

    # Search vector memories
    results = search_memories(query, n=5)
    if not results:
        return None

    # Format results for context injection
    result_texts = []
    for r in results:
        text = r.get("text", str(r)) if isinstance(r, dict) else str(r)
        result_texts.append(f"- {text}")

    memory_block = "Recalled memories matching your query:\n" + "\n".join(result_texts)
    messages.append({"role": "system", "content": memory_block})
    logger.info("Injected %d memory search results for: %s", len(results), query[:50])
    return None  # Don't short-circuit — let LLM respond with context


def _process_execution(user_input, exec_context, messages):
    """Check for execution intent and run code if detected.

    Args:
        user_input:   The user's message.
        exec_context: ExecutionContext instance.
        messages:     Current message list (modified in place).

    Returns:
        Execution result string to display, or None if not an execution request.
    """
    if not EXECUTION_AVAILABLE or exec_context is None:
        return None

    intent = detect_intent(user_input)  # type: ignore[misc]
    if intent.get("intent") not in ("execution", "file_op", "data"):
        return None

    if intent.get("confidence", 0) < 0.5:
        return None

    result = handle_execution_request(user_input, exec_context)  # type: ignore[misc]
    if result and result.get("output"):
        output = result["output"]
        # Inject execution result into context for LLM awareness
        messages.append({
            "role": "system",
            "content": f"Code execution result:\n```\n{output}\n```"
        })
        ui.print_status(f"[Execution] {intent['intent']}: {intent.get('detail', '')}")
        return output

    return None


def _process_auto_knowledge(user_input, response):
    """Run auto-knowledge extraction on the conversation turn.

    Args:
        user_input: The user's message.
        response:   Nexus's response text.
    """
    if not AUTO_KNOWLEDGE_AVAILABLE:
        return

    try:
        stored = detect_and_store(user_input, response)  # type: ignore[misc]
        if stored:
            ui.print_hint(f"[Auto-Knowledge] Stored {len(stored)} fact(s)")
    except Exception as exc:
        logger.warning("Auto-knowledge extraction failed: %s", exc)


def _get_tone_injection(user_input):
    """Parse shorthand/emotional cues and return tone context for injection.

    Args:
        user_input: The user's message.

    Returns:
        Tone context string or None.
    """
    if not SHORTHAND_AVAILABLE:
        return None

    try:
        signals = parse_shorthand(user_input)  # type: ignore[misc]
        return get_tone_context(signals)  # type: ignore[misc]
    except Exception as exc:
        logger.warning("Shorthand parsing failed: %s", exc)
        return None


def _send_to_llm(client, messages, model, temperature, provider, lc_client):
    """Send messages to LLM with LangChain fallback.

    Tries LangChain first if available, falls back to direct client.

    Args:
        client:      Direct SDK client.
        messages:    Message list.
        model:       Model identifier.
        temperature: Sampling temperature.
        provider:    Provider name string.
        lc_client:   LangChain client or None.

    Returns:
        Response text string.
    """
    # Try LangChain enhanced chat first
    if LANGCHAIN_AVAILABLE and lc_client is not None:
        try:
            lc_response = langchain_enhanced_chat(  # type: ignore[misc]
                provider, lc_client, model, messages, temperature
            )
            if lc_response:
                return lc_response
        except Exception as exc:
            logger.warning("LangChain chat failed, falling back: %s", exc)

    # Direct client
    return chat(client, messages, model=model, temperature=temperature, provider=provider)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Start Nexus conversational AI chat loop."""
    ui.print_startup_banner()

    # --- Pulse session ---
    pulse_data = start_pulse_session()
    current_tick = pulse_data["current_tick"]
    ui.print_status(f"Pulse tick: {current_tick} (Session #{pulse_data['total_sessions']})")

    # --- Initialize LLM provider ---
    try:
        client, provider, model, temperature, lc_client = _init_provider()
    except Exception as exc:
        ui.print_status(f"Failed to initialize LLM: {exc}", success=False)
        return

    # --- Skills ---
    skills = discover_skills()
    if skills:
        ui.print_status(f"Skills loaded: {len(skills)}")

    # --- Memory stats ---
    session_count = get_session_count()
    knowledge_count = len(load_knowledge())
    vector_count = get_vector_count()
    if session_count > 0:
        ui.print_status(f"Session history: {session_count} previous sessions")
    ui.print_status(f"Memory: {knowledge_count} knowledge, {vector_count} vectors")

    # --- Cortex ---
    watcher = _init_cortex()

    # --- Execution context ---
    exec_context = None
    if EXECUTION_AVAILABLE:
        exec_context = ExecutionContext()  # type: ignore[misc]
        ui.print_status("Execution engine ready")

    # --- Build rich system prompt ---
    system_prompt = _build_system_prompt(exec_context)

    ui.print_hint("Type 'quit' or 'exit' to end session")

    messages = [{"role": "system", "content": system_prompt}]

    # --- Chat loop ---
    while True:
        try:
            user_input = ui.get_user_input().strip()

            # Exit commands
            if user_input.lower() in ("quit", "exit", "q"):
                break

            # Skip empty input
            if not user_input:
                continue

            # Skill routing (handles built-in commands)
            skill_response = route_to_skill(user_input, skills)
            if skill_response:
                ui.print_nexus_response(skill_response)
                messages.append({"role": "user", "content": user_input})
                messages.append({"role": "assistant", "content": skill_response})
                continue

            # Add user message
            messages.append({"role": "user", "content": user_input})

            # Shorthand/tone detection — inject context if detected
            tone_ctx = _get_tone_injection(user_input)
            if tone_ctx:
                messages.append({"role": "system", "content": tone_ctx})

            # Memory search — inject recalled memories if triggered
            _handle_memory_search(user_input, messages)

            # Execution engine — run code if intent detected
            exec_output = _process_execution(user_input, exec_context, messages)
            if exec_output:
                # Show execution output, but still get LLM commentary
                ui.print_hint(f"[Output]\n{exec_output}")

            # Send to LLM
            response = _send_to_llm(
                client, messages, model, temperature, provider, lc_client
            )

            # Add response to history
            messages.append({"role": "assistant", "content": response})

            # Print response
            ui.print_nexus_response(response)

            # Auto-knowledge extraction (post-response)
            _process_auto_knowledge(user_input, response)

            # Refresh system prompt periodically (every 10 turns)
            turn_count = sum(1 for m in messages if m["role"] == "user")
            if turn_count % 10 == 0:
                refreshed = _build_system_prompt(exec_context)
                messages[0] = {"role": "system", "content": refreshed}
                logger.info("System prompt refreshed at turn %d", turn_count)

        except KeyboardInterrupt:
            break
        except Exception as exc:
            ui.print_error(str(exc))
            logger.error("Chat loop error: %s", exc)
            continue  # Recover gracefully, never crash

    # --- Cleanup ---
    # Save session
    user_assistant_messages = [
        msg for msg in messages if msg["role"] in ("user", "assistant")
    ]
    if user_assistant_messages:
        save_session(user_assistant_messages)

    # Stop cortex watcher
    if watcher:
        watcher.stop()

    ui.print_goodbye()


if __name__ == "__main__":
    main()
