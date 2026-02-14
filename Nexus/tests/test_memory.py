#!/home/aipass/.venv/bin/python3
# -*- coding: utf-8 -*-
"""Memory system tests for Nexus v2"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from handlers.memory import pulse_manager, knowledge_base, summary

def test_pulse_manager():
    """Test pulse manager functions"""
    print("Testing pulse_manager...")

    # Test get_tick
    tick = pulse_manager.get_tick()
    assert tick >= 933, f"Tick should start at 933, got {tick}"
    print(f"  ✓ get_tick() = {tick}")

    # Test increment_tick
    new_tick = pulse_manager.increment_tick()
    assert new_tick == tick + 1, f"Expected {tick + 1}, got {new_tick}"
    print(f"  ✓ increment_tick() = {new_tick}")

    # Test start_session
    pulse_data = pulse_manager.start_session()
    assert pulse_data["session_start_tick"] == new_tick, "Session start tick mismatch"
    assert pulse_data["total_sessions"] >= 1, "Total sessions should increment"
    print(f"  ✓ start_session() - Session #{pulse_data['total_sessions']}")

    # Test end_session
    pulse_data = pulse_manager.end_session()
    assert "last_updated" in pulse_data, "Missing last_updated"
    print(f"  ✓ end_session() - Updated at {pulse_data['last_updated']}")

    print("✓ pulse_manager tests passed\n")

def test_knowledge_base():
    """Test knowledge base functions"""
    print("Testing knowledge_base...")

    # Test add_entry
    initial_count = len(knowledge_base.load_knowledge())
    knowledge_base.add_entry("Test entry for memory system", source="test")
    new_count = len(knowledge_base.load_knowledge())
    assert new_count == initial_count + 1, "Entry not added"
    print(f"  ✓ add_entry() - {new_count} total entries")

    # Test search_knowledge
    results = knowledge_base.search_knowledge("Test entry")
    assert len(results) > 0, "Search should find test entry"
    print(f"  ✓ search_knowledge() - Found {len(results)} matches")

    # Test get_recent
    recent = knowledge_base.get_recent(5)
    assert len(recent) <= 5, "get_recent should limit results"
    assert recent[0]["text"] == "Test entry for memory system", "Most recent not first"
    print(f"  ✓ get_recent(5) - Got {len(recent)} entries")

    # Test max entries (would need 200+ entries to test properly, skip for now)
    print(f"  ⊙ MAX_ENTRIES = {knowledge_base.MAX_ENTRIES} (not tested)")

    print("✓ knowledge_base tests passed\n")

def test_summary_memory():
    """Test summary memory functions"""
    print("Testing summary_memory...")

    # Test save_summary
    initial_count = len(summary.load_summaries())
    summary.save_summary("Test session summary", session_tick=934, key_topics=["memory", "testing"])
    new_count = len(summary.load_summaries())
    assert new_count == initial_count + 1, "Summary not saved"
    print(f"  ✓ save_summary() - {new_count} total summaries")

    # Test load_summaries
    summaries = summary.load_summaries()
    assert len(summaries) > 0, "No summaries loaded"
    assert summaries[0]["tick"] == 934, "Most recent summary not first"
    print(f"  ✓ load_summaries() - Loaded {len(summaries)} summaries")

    # Test get_context_summary
    context = summary.get_context_summary(n=3)
    assert "Session 934" in context, "Context should include test summary"
    assert "memory" in context or "testing" in context, "Topics missing from context"
    print(f"  ✓ get_context_summary(3) - {len(context)} chars")

    print("✓ summary_memory tests passed\n")

if __name__ == "__main__":
    print("=" * 60)
    print("Nexus v2 Memory System Tests")
    print("=" * 60 + "\n")

    try:
        test_pulse_manager()
        test_knowledge_base()
        test_summary_memory()

        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
