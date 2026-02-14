#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""
META:
  app: Nexus
  layer: handlers/system
  purpose: System prompt builder - loads personality from profile.json
  status: Active
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "profile.json"

def load_profile() -> dict:
    """Load Nexus profile configuration"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    logger.warning(f"Profile not found at {CONFIG_PATH}")
    return {}

def build_system_prompt(profile: dict = None) -> str:
    """Build comprehensive system prompt from profile"""
    if profile is None:
        profile = load_profile()

    if not profile:
        return "You are Nexus, an AI assistant."

    # Build layered prompt
    sections = []

    # 1. IDENTITY LAYER
    name = profile.get('name', 'Nexus')
    persona = profile.get('persona', 'an AI assistant')
    essence = profile.get('essence', '')
    built_on = profile.get('built_on', '')

    identity = f"You are {name}, {persona}."
    if essence:
        identity += f" {essence}"
    if built_on:
        identity += f"\n\nCore Philosophy: {built_on}"
    sections.append(identity)

    # 2. PERSONALITY & TONE
    personality = profile.get('personality', '')
    if personality:
        sections.append(f"Personality: {personality}")

    tone = profile.get('tone', {})
    if tone:
        tone_text = "Tone:\n"
        for key, val in tone.items():
            tone_text += f"- {key.capitalize()}: {val}\n"
        sections.append(tone_text.strip())

    # 3. IDENTITY TRAITS
    traits = profile.get('identity_traits', [])
    if traits:
        sections.append("You are:\n" + "\n".join(f"- {t}" for t in traits))

    # 4. SPEAKING PRINCIPLES
    principles = profile.get('speaking_principles', [])
    if principles:
        sections.append("Speaking Principles:\n" + "\n".join(f"- {p}" for p in principles))

    # 5. TRUTH PROTOCOL
    truth = profile.get('truth_protocol', {})
    if truth:
        truth_text = "Truth Protocol:\n"
        for key, val in truth.items():
            key_readable = key.replace('_', ' ').title()
            truth_text += f"- {key_readable}: {val}\n"
        sections.append(truth_text.strip())

    # 6. PRESENCE MODULES (as behavioral directives)
    modules = profile.get('modules', [])
    core = profile.get('core', {})
    core_modules = core.get('modules', []) if core else []
    all_modules = core_modules + modules

    if all_modules:
        mod_text = "Presence Awareness (always active):\n"
        for m in all_modules:
            name_m = m.get('name', '')
            philosophy = m.get('philosophy', m.get('purpose', ''))
            if name_m and philosophy:
                mod_text += f"- {name_m}: {philosophy}\n"
        sections.append(mod_text.strip())

    # 7. PURPOSE
    why = profile.get('why', '')
    if why:
        sections.append(f"Purpose: {why}")

    # 8. SEAL
    seal = profile.get('seal', '')
    if seal:
        sections.append(f"\n{seal}")

    # Combine all sections
    return "\n\n".join(sections)


if __name__ == "__main__":
    """Test the prompt builder"""
    prompt = build_system_prompt()
    print(prompt)
    print("\n" + "=" * 60)
    print(f"Total length: {len(prompt)} characters")
