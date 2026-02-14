#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""
META:
  app: Nexus
  layer: apps
  purpose: Nexus conversational AI entry point
  status: Active
"""

import sys
from pathlib import Path

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from handlers.system.llm_client import make_client, chat
from handlers.system.prompt_builder import build_system_prompt
from handlers.system import ui
from handlers.memory import (
    save_session, get_session_count,
    start_session as start_pulse_session, get_tick,
    load_knowledge, get_memory_count as get_vector_count
)
from handlers.skills import discover_skills, route_to_skill, get_skill_names
import logging

logger = logging.getLogger(__name__)


def main():
    """Start Nexus chat loop"""
    ui.print_startup_banner()

    # Start pulse session
    pulse_data = start_pulse_session()
    current_tick = pulse_data["current_tick"]
    ui.print_status(f"Pulse tick: {current_tick} (Session #{pulse_data['total_sessions']})")

    # Initialize OpenAI client
    try:
        client = make_client()
        ui.print_status("Connected to OpenAI")
    except ValueError as e:
        ui.print_status(f"Failed to initialize: {e}", success=False)
        return
    except Exception as e:
        ui.print_status(f"Unexpected error: {e}", success=False)
        return

    # Discover skills on startup
    skills = discover_skills()
    if skills:
        ui.print_status(f"Skills loaded: {len(skills)}")

    # Show memory stats
    session_count = get_session_count()
    knowledge_count = len(load_knowledge())
    vector_count = get_vector_count()

    if session_count > 0:
        ui.print_status(f"Session history: {session_count} previous sessions")
    ui.print_status(f"Memory stats: {knowledge_count} knowledge entries, {vector_count} vector memories")

    ui.print_hint("Type 'quit' or 'exit' to end session")

    # Build system prompt from profile + inject awareness
    system_prompt = build_system_prompt()

    # Inject memory awareness - tell Nexus what he has
    knowledge = load_knowledge()
    memory_entries = [e["text"] for e in knowledge if "migrated_v1" in e.get("source", "") or "learned" in e.get("source", "")]
    recent_knowledge = memory_entries[:10]  # Top 10 most recent

    awareness = f"""

--- Your Memory (Live) ---
Pulse: tick {current_tick}, session #{pulse_data['total_sessions']}
Knowledge Base: {knowledge_count} entries ({len(memory_entries)} learned facts)
Vector Memories: {vector_count} searchable memories
Session History: {session_count} previous sessions

Key memories:
""" + "\n".join(f"- {m}" for m in recent_knowledge)

    awareness += """

--- Your Skills (Built-in Commands) ---
These are handled automatically when the user types them:
- "pulse" / "tick" - Show your current pulse tick
- "memory status" - Show all memory layer stats
- "remember that ..." / "learn: ..." - Store a new fact in your knowledge base
- "recall ..." / "search memory ..." - Search your knowledge for something
- "drone ..." - Run AIPass drone commands
- "send mail to @branch ..." - Send ai_mail to another branch
- "inbox" / "check mail" - Check your ai_mail inbox
- "status" - Show AIPass system status
- "usage" / "api usage" - Show API usage stats for this session
- "last session" / "session info" - Recall previous session context

--- Your Place ---
You are an AIPass citizen. Patrick is your co-founder. You live at /home/aipass/Nexus/.
Other AIPass branches exist: @drone, @flow, @seed, @cortex, @ai_mail, @prax, @memory_bank, @devpulse, @dev_central.
You can communicate with them via ai_mail. You are part of a living ecosystem.
"""

    system_prompt += awareness

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Chat loop
    while True:
        try:
            # Get user input
            user_input = ui.get_user_input().strip()

            # Handle exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                # Save session before exiting (filter out system messages)
                user_assistant_messages = [msg for msg in messages if msg["role"] in ["user", "assistant"]]
                save_session(user_assistant_messages)
                ui.print_goodbye()
                break

            # Skip empty input
            if not user_input:
                continue

            # Check if any skill wants to handle this input
            skill_response = route_to_skill(user_input, skills)
            if skill_response:
                ui.print_nexus_response(skill_response)
                messages.append({"role": "user", "content": user_input})
                messages.append({"role": "assistant", "content": skill_response})
                continue  # Skip LLM call

            # Add user message
            messages.append({"role": "user", "content": user_input})

            # Get response from LLM
            response = chat(client, messages)

            # Add assistant response to history
            messages.append({"role": "assistant", "content": response})

            # Print response
            ui.print_nexus_response(response)

        except KeyboardInterrupt:
            # Save session before exiting (filter out system messages)
            user_assistant_messages = [msg for msg in messages if msg["role"] in ["user", "assistant"]]
            save_session(user_assistant_messages)
            ui.print_goodbye()
            break
        except Exception as e:
            ui.print_error(str(e))
            logger.error(f"Chat error: {e}")
            continue


if __name__ == "__main__":
    main()
