#!/usr/bin/env python3
"""Test skill auto-discovery and basic routing"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("Nexus v2 Skills Tests")
print("=" * 60)

# Test discovery
from handlers.skills import discover_skills, route_to_skill, get_skill_names

skills = discover_skills()
names = get_skill_names()
print(f"\nDiscovered {len(skills)} skills: {names}")
assert len(skills) >= 4, f"Expected at least 4 skills, found {len(skills)}"
print("  ✓ All skills discovered")

# Test memory_ops routing
response = route_to_skill("memory status", skills)
assert response is not None, "memory_ops should handle 'memory status'"
assert "Pulse tick" in response, f"Expected pulse tick in response: {response}"
print("  ✓ memory_ops responds to 'memory status'")

response = route_to_skill("pulse", skills)
assert response is not None, "memory_ops should handle 'pulse'"
print("  ✓ memory_ops responds to 'pulse'")

# Test session_awareness routing
response = route_to_skill("session info", skills)
assert response is not None, "session_awareness should handle 'session info'"
print("  ✓ session_awareness responds to 'session info'")

# Test usage_monitor routing
response = route_to_skill("usage", skills)
assert response is not None, "usage_monitor should handle 'usage'"
print("  ✓ usage_monitor responds to 'usage'")

# Test pass-through (no skill handles regular chat)
response = route_to_skill("hello, how are you?", skills)
assert response is None, "Regular chat should not be handled by skills"
print("  ✓ Regular input passes through to LLM")

print("\n" + "=" * 60)
print("ALL SKILL TESTS PASSED ✓")
print("=" * 60)
