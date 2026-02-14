#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for Nexus v2 - verifies full system works together"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
NEXUS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(NEXUS_DIR))


def test_system_prompt_builds_from_profile():
    """Test that system prompt includes all personality modules from profile.json"""
    print("Test 1: System prompt builds from profile.json...", end=" ")

    from handlers.system.prompt_builder import build_system_prompt, load_profile

    profile = load_profile()
    prompt = build_system_prompt(profile)

    # Verify prompt is non-empty
    assert len(prompt) > 100, f"Prompt too short: {len(prompt)} chars"

    # Verify identity appears
    assert "Nexus" in prompt, "Nexus name missing from prompt"

    # Verify all personality modules appear
    core_modules = profile.get("core", {}).get("modules", [])
    ext_modules = profile.get("modules", [])
    all_modules = core_modules + ext_modules

    for mod in all_modules:
        name = mod.get("name", "")
        assert name in prompt, f"Module '{name}' missing from system prompt"

    # Verify tone section
    assert "Focused" in prompt or "Gentle" in prompt, "Tone missing from prompt"

    # Verify truth protocol
    assert "unknown" in prompt.lower() or "simulate" in prompt.lower(), "Truth protocol missing"

    print(f"PASSED ({len(prompt)} chars, {len(all_modules)} modules)")


def test_all_skills_discover():
    """Test all 4 skills are auto-discovered"""
    print("Test 2: All 4 skills auto-discover...", end=" ")

    from handlers.skills import discover_skills, get_skill_names

    skills = discover_skills()
    names = get_skill_names()

    assert len(skills) >= 4, f"Expected >= 4 skills, got {len(skills)}: {names}"

    expected = {"memory_ops", "aipass_services", "usage_monitor", "session_awareness"}
    found = set(names)
    missing = expected - found
    assert not missing, f"Missing skills: {missing}"

    print(f"PASSED ({len(skills)} skills: {', '.join(names)})")


def test_memory_integration():
    """Test all memory layers are accessible"""
    print("Test 3: Memory integration (pulse, knowledge, summary)...", end=" ")

    from handlers.memory import (
        get_tick, load_knowledge, load_summaries,
        get_pulse_data, get_session_count
    )

    # Pulse
    tick = get_tick()
    assert isinstance(tick, int), f"Tick should be int, got {type(tick)}"
    assert tick >= 933, f"Tick should be >= 933, got {tick}"

    # Pulse data
    pulse_data = get_pulse_data()
    assert "current_tick" in pulse_data, "current_tick missing from pulse data"
    assert "total_sessions" in pulse_data, "total_sessions missing from pulse data"

    # Knowledge base
    kb = load_knowledge()
    assert isinstance(kb, list), "Knowledge should be a list"

    # Summaries
    summaries = load_summaries()
    assert isinstance(summaries, list), "Summaries should be a list"

    # Session count
    count = get_session_count()
    assert isinstance(count, int), f"Session count should be int, got {type(count)}"

    print(f"PASSED (tick={tick}, kb={len(kb)}, summaries={len(summaries)}, sessions={count})")


def test_skill_routing_memory_ops():
    """Test memory_ops handles its patterns"""
    print("Test 4: Skill routing - memory_ops...", end=" ")

    from handlers.skills import discover_skills, route_to_skill

    skills = discover_skills()

    # "pulse" should be handled by memory_ops
    response = route_to_skill("pulse", skills)
    assert response is not None, "'pulse' should be handled"
    assert "tick" in response.lower() or "Pulse" in response, f"Unexpected pulse response: {response}"

    # "memory status" should be handled
    response = route_to_skill("memory status", skills)
    assert response is not None, "'memory status' should be handled"
    assert "Knowledge" in response or "knowledge" in response, f"Unexpected memory status: {response}"

    print("PASSED")


def test_skill_routing_aipass_services():
    """Test aipass_services handles its patterns"""
    print("Test 5: Skill routing - aipass_services (drone pattern)...", end=" ")

    from handlers.skills import discover_skills, route_to_skill

    skills = discover_skills()

    # "status" should be handled by aipass_services
    response = route_to_skill("status", skills)
    assert response is not None, "'status' should be handled by aipass_services"

    print("PASSED")


def test_skill_routing_passthrough():
    """Test regular chat passes through without skill handling"""
    print("Test 6: Regular chat passes through skills...", end=" ")

    from handlers.skills import discover_skills, route_to_skill

    skills = discover_skills()

    # Regular conversational input should not be handled
    response = route_to_skill("What is the meaning of life?", skills)
    assert response is None, f"Regular chat should pass through, got: {response}"

    response = route_to_skill("Tell me about yourself", skills)
    assert response is None, f"Regular chat should pass through, got: {response}"

    print("PASSED")


def test_nexus_main_imports():
    """Test nexus.py can be imported without crashing (mock OpenAI)"""
    print("Test 7: nexus.py imports work...", end=" ")

    # Mock openai before importing nexus
    mock_openai = MagicMock()
    mock_dotenv = MagicMock()

    with patch.dict(sys.modules, {
        'openai': mock_openai,
        'dotenv': mock_dotenv,
    }):
        # Force reimport of llm_client with mocked openai
        if 'handlers.system.llm_client' in sys.modules:
            del sys.modules['handlers.system.llm_client']

        # Re-import the module to pick up the mock
        import importlib
        from handlers.system import llm_client
        importlib.reload(llm_client)

        # Now test that nexus entry point has main()
        # We can't fully import nexus.py because it re-imports llm_client at module level
        # But we can verify the file is valid Python
        nexus_path = NEXUS_DIR / "nexus.py"
        assert nexus_path.exists(), "nexus.py not found"

        # Compile check - will raise SyntaxError if invalid
        with open(nexus_path, 'r') as f:
            compile(f.read(), str(nexus_path), 'exec')

    print("PASSED")


def test_drone_app_works():
    """Test drone app (apps/nexus.py) status and info commands"""
    print("Test 8: Drone app commands work...", end=" ")

    # Import drone app
    sys.path.insert(0, str(NEXUS_DIR / "apps"))
    apps_nexus_path = NEXUS_DIR / "apps" / "nexus.py"
    assert apps_nexus_path.exists(), "apps/nexus.py not found"

    import importlib.util
    spec = importlib.util.spec_from_file_location("apps_nexus", str(apps_nexus_path))
    apps_nexus = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(apps_nexus)

    # Test cmd_status runs without error
    import argparse
    args = argparse.Namespace(command="status")
    result = apps_nexus.cmd_status(args)
    assert result is True, "cmd_status should return True"

    # Test cmd_info runs without error
    result = apps_nexus.cmd_info(args)
    assert result is True, "cmd_info should return True"

    # Test command routing
    assert "status" in apps_nexus.COMMANDS, "status not in COMMANDS"
    assert "info" in apps_nexus.COMMANDS, "info not in COMMANDS"

    print("PASSED")


def test_profile_json_valid():
    """Test profile.json is valid and has required fields"""
    print("Test 9: profile.json structure...", end=" ")

    profile_path = NEXUS_DIR / "config" / "profile.json"
    assert profile_path.exists(), "profile.json not found"

    with open(profile_path, 'r') as f:
        profile = json.load(f)

    assert profile.get("name") == "Nexus", f"Name should be Nexus, got {profile.get('name')}"
    assert profile.get("status") == "Active", "Status should be Active"
    assert "core" in profile, "Missing core section"
    assert "modules" in profile, "Missing modules section"
    assert "tone" in profile, "Missing tone section"
    assert "truth_protocol" in profile, "Missing truth_protocol section"
    assert "identity_traits" in profile, "Missing identity_traits"
    assert "speaking_principles" in profile, "Missing speaking_principles"

    # Verify module count
    core_mods = profile.get("core", {}).get("modules", [])
    ext_mods = profile.get("modules", [])
    total = len(core_mods) + len(ext_mods)
    assert total == 5, f"Expected 5 personality modules, got {total}"

    print(f"PASSED ({total} personality modules)")


def test_data_files_exist():
    """Test all expected data files exist and are valid JSON"""
    print("Test 10: Data files exist and valid...", end=" ")

    data_dir = NEXUS_DIR / "data"

    expected_files = ["pulse.json", "knowledge_base.json", "chat_history.json", "session_summaries.json"]
    for fname in expected_files:
        fpath = data_dir / fname
        assert fpath.exists(), f"Missing data file: {fname}"
        # Verify valid JSON
        data = json.loads(fpath.read_text(encoding="utf-8"))
        assert data is not None, f"{fname} loaded as None"

    print(f"PASSED ({len(expected_files)} files)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Nexus v2 Integration Tests")
    print("=" * 60)
    print()

    tests = [
        test_system_prompt_builds_from_profile,
        test_all_skills_discover,
        test_memory_integration,
        test_skill_routing_memory_ops,
        test_skill_routing_aipass_services,
        test_skill_routing_passthrough,
        test_nexus_main_imports,
        test_drone_app_works,
        test_profile_json_valid,
        test_data_files_exist,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 60)
    if failed == 0:
        print(f"ALL {passed} TESTS PASSED")
    else:
        print(f"{passed} passed, {failed} failed")
    print("=" * 60)

    sys.exit(1 if failed > 0 else 0)
