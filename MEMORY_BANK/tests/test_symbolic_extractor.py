#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_symbolic_extractor.py - Symbolic Extractor Unit Tests
# Date: 2026-02-04
# Version: 0.1.0
# Category: memory_bank/tests
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2026-02-04): Initial version - tests for symbolic extraction
#
# CODE STANDARDS:
#   - pytest conventions
#   - Comprehensive coverage of all extraction functions
# =============================================

"""
Unit tests for Symbolic Memory Extractor Handler

Tests all extraction functions with various conversation scenarios.
"""

import sys
from pathlib import Path

# Infrastructure setup
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

import pytest
from MEMORY_BANK.apps.modules.symbolic import (
    extract_technical_flow,
    extract_emotional_journey,
    extract_collaboration_patterns,
    extract_key_learnings,
    extract_context_triggers,
    extract_symbolic_dimensions,
    analyze_conversation
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def empty_chat():
    """Empty conversation"""
    return []


@pytest.fixture
def debugging_chat():
    """Debugging-focused conversation"""
    return [
        {"role": "user", "content": "I have an error in my code, it keeps failing"},
        {"role": "assistant", "content": "Let me help debug this. Can you trace the issue?"},
        {"role": "user", "content": "I tried checking the logs but I'm stuck"},
        {"role": "assistant", "content": "Let's try a different approach. The fix is simple."},
        {"role": "user", "content": "Got it! That works! Breakthrough!"}
    ]


@pytest.fixture
def learning_chat():
    """Learning-focused conversation"""
    return [
        {"role": "user", "content": "I want to understand how memory systems work"},
        {"role": "assistant", "content": "Memory systems store and retrieve information. Let me explain."},
        {"role": "user", "content": "That makes sense. I learned something new today!"},
        {"role": "assistant", "content": "Great! You've discovered the key insight."}
    ]


@pytest.fixture
def emotional_chat():
    """Emotionally varied conversation"""
    return [
        {"role": "user", "content": "This is so frustrating, I'm stuck and confused"},
        {"role": "assistant", "content": "I understand. Let's work through this together."},
        {"role": "user", "content": "Maybe this approach would work?"},
        {"role": "assistant", "content": "Yes! That's awesome, you got it!"},
        {"role": "user", "content": "Finally! Success! This is amazing!"}
    ]


@pytest.fixture
def collaborative_chat():
    """Collaborative building conversation"""
    return [
        {"role": "user", "content": "Let's build something together. What if we try this?"},
        {"role": "assistant", "content": "Great idea! We can collaborate on this approach."},
        {"role": "user", "content": "How about we consider using modules?"},
        {"role": "assistant", "content": "I'll explain how that works. Let me show you."}
    ]


@pytest.fixture
def technical_chat():
    """Technical terms heavy conversation"""
    return [
        {"role": "user", "content": "The module system needs a handler for vector storage"},
        {"role": "assistant", "content": "We should create a branch with rollover support"},
        {"role": "user", "content": "The extraction pattern should compress the memory"},
        {"role": "assistant", "content": "Yes, the handler will process the JSON file"}
    ]


# =============================================================================
# EXTRACT TECHNICAL FLOW TESTS
# =============================================================================

class TestExtractTechnicalFlow:
    """Tests for extract_technical_flow()"""

    def test_empty_chat(self, empty_chat):
        """Empty chat returns no_conversation"""
        result = extract_technical_flow(empty_chat)
        assert result['success'] is True
        assert 'no_conversation' in result['patterns']

    def test_debugging_chat(self, debugging_chat):
        """Debugging chat detects problem patterns"""
        result = extract_technical_flow(debugging_chat)
        assert result['success'] is True
        assert 'problem_struggle_breakthrough' in result['patterns']

    def test_learning_chat(self, learning_chat):
        """Learning chat detects learning patterns"""
        result = extract_technical_flow(learning_chat)
        assert result['success'] is True
        assert 'learning_conversation' in result['patterns']

    def test_returns_details(self, debugging_chat):
        """Returns category counts in details"""
        result = extract_technical_flow(debugging_chat)
        assert 'details' in result
        assert 'category_counts' in result['details']


# =============================================================================
# EXTRACT EMOTIONAL JOURNEY TESTS
# =============================================================================

class TestExtractEmotionalJourney:
    """Tests for extract_emotional_journey()"""

    def test_empty_chat(self, empty_chat):
        """Empty chat returns neutral"""
        result = extract_emotional_journey(empty_chat)
        assert result['success'] is True
        assert 'neutral' in result['arc']

    def test_emotional_chat(self, emotional_chat):
        """Emotional chat detects frustration to breakthrough"""
        result = extract_emotional_journey(emotional_chat)
        assert result['success'] is True
        assert 'frustration_to_breakthrough' in result['arc']

    def test_returns_timeline(self, emotional_chat):
        """Returns emotion timeline in details"""
        result = extract_emotional_journey(emotional_chat)
        assert 'details' in result
        assert 'timeline' in result['details']


# =============================================================================
# EXTRACT COLLABORATION PATTERNS TESTS
# =============================================================================

class TestExtractCollaborationPatterns:
    """Tests for extract_collaboration_patterns()"""

    def test_empty_chat(self, empty_chat):
        """Empty chat returns no_interaction"""
        result = extract_collaboration_patterns(empty_chat)
        assert result['success'] is True
        assert 'no_interaction' in result['patterns']

    def test_collaborative_chat(self, collaborative_chat):
        """Collaborative chat detects building patterns"""
        result = extract_collaboration_patterns(collaborative_chat)
        assert result['success'] is True
        assert 'collaborative_building' in result['patterns']

    def test_user_only_chat(self):
        """User-only chat returns one_sided"""
        chat = [{"role": "user", "content": "Hello"}]
        result = extract_collaboration_patterns(chat)
        assert result['success'] is True
        assert 'one_sided_conversation' in result['patterns']

    def test_returns_metrics(self, collaborative_chat):
        """Returns interaction metrics in details"""
        result = extract_collaboration_patterns(collaborative_chat)
        assert 'details' in result
        assert 'avg_user_length' in result['details']


# =============================================================================
# EXTRACT KEY LEARNINGS TESTS
# =============================================================================

class TestExtractKeyLearnings:
    """Tests for extract_key_learnings()"""

    def test_empty_chat(self, empty_chat):
        """Empty chat returns no_insights"""
        result = extract_key_learnings(empty_chat)
        assert result['success'] is True
        assert 'no_insights' in result['insights']

    def test_learning_chat(self, learning_chat):
        """Learning chat detects insights"""
        result = extract_key_learnings(learning_chat)
        assert result['success'] is True
        assert 'discovery' in result['insights'] or 'understanding' in result['insights']

    def test_debugging_skills(self, debugging_chat):
        """Debugging chat detects debugging skills"""
        result = extract_key_learnings(debugging_chat)
        assert result['success'] is True
        assert 'debugging_skills' in result['insights']


# =============================================================================
# EXTRACT CONTEXT TRIGGERS TESTS
# =============================================================================

class TestExtractContextTriggers:
    """Tests for extract_context_triggers()"""

    def test_empty_chat(self, empty_chat):
        """Empty chat returns empty triggers"""
        result = extract_context_triggers(empty_chat)
        assert result['success'] is True
        assert result['triggers'] == []

    def test_technical_chat(self, technical_chat):
        """Technical chat extracts relevant triggers"""
        result = extract_context_triggers(technical_chat)
        assert result['success'] is True
        assert len(result['triggers']) > 0
        # Should find terms like 'module', 'handler', 'memory', etc.
        assert any(t in result['triggers'] for t in ['module', 'handler', 'memory', 'branch'])

    def test_returns_term_counts(self, technical_chat):
        """Returns term counts in details"""
        result = extract_context_triggers(technical_chat)
        assert 'details' in result
        assert 'term_counts' in result['details']


# =============================================================================
# EXTRACT SYMBOLIC DIMENSIONS TESTS
# =============================================================================

class TestExtractSymbolicDimensions:
    """Tests for extract_symbolic_dimensions()"""

    def test_empty_chat(self, empty_chat):
        """Empty chat returns all dimensions"""
        result = extract_symbolic_dimensions(empty_chat)
        assert result['success'] is True
        assert 'dimensions' in result
        assert 'technical' in result['dimensions']
        assert 'emotional' in result['dimensions']
        assert 'collaboration' in result['dimensions']
        assert 'learnings' in result['dimensions']
        assert 'triggers' in result['dimensions']

    def test_full_extraction(self, debugging_chat):
        """Full extraction includes all dimensions"""
        result = extract_symbolic_dimensions(debugging_chat)
        assert result['success'] is True
        assert len(result['dimensions']['technical']) > 0
        assert len(result['dimensions']['emotional']) > 0

    def test_returns_details(self, debugging_chat):
        """Returns details for each dimension"""
        result = extract_symbolic_dimensions(debugging_chat)
        assert 'details' in result
        assert 'technical' in result['details']


# =============================================================================
# ANALYZE CONVERSATION TESTS
# =============================================================================

class TestAnalyzeConversation:
    """Tests for analyze_conversation()"""

    def test_empty_chat(self, empty_chat):
        """Empty chat returns zero counts"""
        result = analyze_conversation(empty_chat)
        assert result['success'] is True
        assert result['message_count'] == 0

    def test_full_analysis(self, debugging_chat):
        """Full analysis includes all fields"""
        result = analyze_conversation(debugging_chat)
        assert result['success'] is True
        assert result['message_count'] == 5
        assert 'dimensions' in result
        assert 'metadata' in result
        assert 'timestamp' in result['metadata']
        assert 'depth' in result['metadata']

    def test_depth_calculation(self):
        """Depth is calculated based on words and messages"""
        # Light conversation
        light_chat = [{"role": "user", "content": "hi"}]
        result = analyze_conversation(light_chat)
        assert result['metadata']['depth'] == 'light'

    def test_metadata_fields(self, debugging_chat):
        """Metadata includes expected fields"""
        result = analyze_conversation(debugging_chat)
        metadata = result['metadata']
        assert 'total_chars' in metadata
        assert 'total_words' in metadata
        assert 'depth' in metadata
        assert 'timestamp' in metadata


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case tests"""

    def test_none_content(self):
        """Handles messages with None content"""
        chat = [{"role": "user", "content": None}]
        result = analyze_conversation(chat)
        assert result['success'] is True

    def test_missing_role(self):
        """Handles messages with missing role"""
        chat = [{"content": "Hello there"}]
        result = analyze_conversation(chat)
        assert result['success'] is True

    def test_empty_content(self):
        """Handles messages with empty content"""
        chat = [{"role": "user", "content": ""}]
        result = analyze_conversation(chat)
        assert result['success'] is True

    def test_large_conversation(self):
        """Handles large conversations"""
        chat = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i} " * 50}
            for i in range(50)
        ]
        result = analyze_conversation(chat)
        assert result['success'] is True
        assert result['metadata']['depth'] in ['substantial', 'deep_extended']
