#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_symbolic_storage.py - Symbolic Storage Unit Tests
# Date: 2026-02-04
# Version: 0.1.0
# Category: memory_bank/tests
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2026-02-04): Initial version - tests for symbolic storage
#
# CODE STANDARDS:
#   - pytest conventions
#   - Comprehensive coverage of storage functions
# =============================================

"""
Unit tests for Symbolic Fragment Storage Handler

Tests fragment creation, metadata flattening, and ChromaDB storage.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Infrastructure setup
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

import pytest
from MEMORY_BANK.apps.modules.symbolic import (
    analyze_conversation,
    create_fragment,
    store_fragment,
    store_fragments_batch,
    flatten_dimensions
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_analysis():
    """Sample analysis output from analyze_conversation()"""
    return {
        'success': True,
        'message_count': 5,
        'dimensions': {
            'technical': ['problem_struggle_breakthrough'],
            'emotional': ['frustration_to_breakthrough'],
            'collaboration': ['balanced_exchange', 'assistant_teaching'],
            'learnings': ['debugging_skills', 'discovery'],
            'triggers': ['error', 'debug', 'fix', 'module', 'handler']
        },
        'metadata': {
            'timestamp': '2026-02-04T12:00:00',
            'total_chars': 500,
            'total_words': 100,
            'depth': 'moderate'
        }
    }


@pytest.fixture
def sample_fragment(sample_analysis):
    """Sample fragment from create_fragment()"""
    result = create_fragment(sample_analysis, source_branch='SEED')
    return result['fragment']


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
def temp_chroma_dir():
    """Temporary directory for ChromaDB testing"""
    temp_dir = tempfile.mkdtemp(prefix="test_chroma_")
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# CREATE FRAGMENT TESTS
# =============================================================================

class TestCreateFragment:
    """Tests for create_fragment()"""

    def test_creates_fragment_from_analysis(self, sample_analysis):
        """Creates fragment with correct structure"""
        result = create_fragment(sample_analysis)

        assert result['success'] is True
        assert 'fragment' in result

        fragment = result['fragment']
        assert 'id' in fragment
        assert fragment['id'].startswith('frag_')
        assert 'content' in fragment
        assert 'dimensions' in fragment
        assert 'metadata' in fragment

    def test_fragment_has_all_dimensions(self, sample_analysis):
        """Fragment includes all dimension types"""
        result = create_fragment(sample_analysis)
        fragment = result['fragment']
        dims = fragment['dimensions']

        assert 'technical' in dims
        assert 'emotional' in dims
        assert 'collaboration' in dims
        assert 'learnings' in dims
        assert 'triggers' in dims

    def test_fragment_metadata(self, sample_analysis):
        """Fragment metadata includes expected fields"""
        result = create_fragment(sample_analysis)
        fragment = result['fragment']
        meta = fragment['metadata']

        assert 'timestamp' in meta
        assert 'message_count' in meta
        assert 'depth' in meta
        assert meta['message_count'] == 5

    def test_source_branch_added(self, sample_analysis):
        """Source branch is added to metadata when provided"""
        result = create_fragment(sample_analysis, source_branch='SEED')
        fragment = result['fragment']

        assert fragment['metadata']['source_branch'] == 'SEED'

    def test_custom_content(self, sample_analysis):
        """Custom content overrides generated essence"""
        custom = "Custom fragment content for testing"
        result = create_fragment(sample_analysis, content=custom)

        assert result['fragment']['content'] == custom

    def test_empty_analysis_fails(self):
        """Empty analysis returns error"""
        result = create_fragment({})
        assert result['success'] is False
        assert 'error' in result

    def test_none_analysis_fails(self):
        """None analysis returns error"""
        result = create_fragment(None)
        assert result['success'] is False


# =============================================================================
# FLATTEN DIMENSIONS TESTS
# =============================================================================

class TestFlattenDimensions:
    """Tests for flatten_dimensions()"""

    def test_flattens_dimensions(self, sample_fragment):
        """Flattens nested dimensions to indexed keys"""
        result = flatten_dimensions(sample_fragment)

        assert result['success'] is True
        assert 'metadata' in result

        flat = result['metadata']
        assert 'technical_0' in flat
        assert flat['technical_0'] == 'problem_struggle_breakthrough'

    def test_triggers_as_comma_separated(self, sample_fragment):
        """Triggers stored as comma-separated string"""
        result = flatten_dimensions(sample_fragment)
        flat = result['metadata']

        assert 'triggers' in flat
        assert isinstance(flat['triggers'], str)
        assert 'error' in flat['triggers']
        assert 'debug' in flat['triggers']

    def test_metadata_fields_preserved(self, sample_fragment):
        """Metadata fields are preserved in flattened output"""
        result = flatten_dimensions(sample_fragment)
        flat = result['metadata']

        assert 'timestamp' in flat
        assert 'message_count' in flat
        assert 'depth' in flat

    def test_source_branch_preserved(self, sample_fragment):
        """Source branch is preserved when present"""
        result = flatten_dimensions(sample_fragment)
        flat = result['metadata']

        assert flat.get('source_branch') == 'SEED'

    def test_empty_fragment_fails(self):
        """Empty fragment returns error"""
        result = flatten_dimensions({})
        assert result['success'] is False

    def test_limits_dimension_values(self, sample_analysis):
        """Limits dimension values to 5 per type"""
        # Add more than 5 values
        sample_analysis['dimensions']['technical'] = [f'pattern_{i}' for i in range(10)]
        frag_result = create_fragment(sample_analysis)
        result = flatten_dimensions(frag_result['fragment'])
        flat = result['metadata']

        # Should only have 5 indexed keys for technical
        tech_keys = [k for k in flat.keys() if k.startswith('technical_')]
        assert len(tech_keys) <= 5


# =============================================================================
# STORE FRAGMENT TESTS
# =============================================================================

class TestStoreFragment:
    """Tests for store_fragment()"""

    def test_stores_fragment_successfully(self, sample_fragment, temp_chroma_dir):
        """Stores fragment in ChromaDB"""
        result = store_fragment(sample_fragment, db_path=temp_chroma_dir)

        assert result['success'] is True
        assert 'fragment_id' in result
        assert result['fragment_id'] == sample_fragment['id']
        assert result['collection'] == 'symbolic_fragments'

    def test_increments_total_count(self, sample_fragment, temp_chroma_dir):
        """Total fragments count increases after storage"""
        result = store_fragment(sample_fragment, db_path=temp_chroma_dir)

        assert result['total_fragments'] >= 1

    def test_empty_fragment_fails(self, temp_chroma_dir):
        """Empty fragment returns error"""
        result = store_fragment({}, db_path=temp_chroma_dir)
        assert result['success'] is False

    def test_fragment_missing_content_fails(self, temp_chroma_dir):
        """Fragment without content returns error"""
        fragment = {'id': 'test_123'}
        result = store_fragment(fragment, db_path=temp_chroma_dir)
        assert result['success'] is False

    def test_fragment_missing_id_fails(self, temp_chroma_dir):
        """Fragment without id returns error"""
        fragment = {'content': 'test content'}
        result = store_fragment(fragment, db_path=temp_chroma_dir)
        assert result['success'] is False


# =============================================================================
# STORE FRAGMENTS BATCH TESTS
# =============================================================================

class TestStoreFragmentsBatch:
    """Tests for store_fragments_batch()"""

    def test_stores_multiple_fragments(self, sample_analysis, temp_chroma_dir):
        """Stores multiple fragments in batch"""
        # Create multiple fragments
        fragments = []
        for i in range(3):
            analysis = sample_analysis.copy()
            analysis['message_count'] = i + 1
            frag_result = create_fragment(analysis, source_branch=f'BRANCH_{i}')
            fragments.append(frag_result['fragment'])

        result = store_fragments_batch(fragments, db_path=temp_chroma_dir)

        assert result['success'] is True
        assert result['stored'] == 3
        assert result['total_fragments'] >= 3

    def test_empty_list_succeeds(self, temp_chroma_dir):
        """Empty fragment list returns success with zero stored"""
        result = store_fragments_batch([], db_path=temp_chroma_dir)

        assert result['success'] is True
        assert result['stored'] == 0

    def test_filters_invalid_fragments(self, sample_analysis, temp_chroma_dir):
        """Skips fragments without content or id"""
        frag_result = create_fragment(sample_analysis)
        valid_fragment = frag_result['fragment']

        fragments = [
            valid_fragment,
            {'id': 'no_content'},
            {'content': 'no_id'}
        ]

        result = store_fragments_batch(fragments, db_path=temp_chroma_dir)

        assert result['success'] is True
        assert result['stored'] == 1


# =============================================================================
# END-TO-END TESTS
# =============================================================================

class TestEndToEnd:
    """End-to-end integration tests"""

    def test_full_workflow(self, debugging_chat, temp_chroma_dir):
        """Full workflow: analyze -> create fragment -> store"""
        # Step 1: Analyze conversation
        analysis = analyze_conversation(debugging_chat)
        assert analysis['success'] is True

        # Step 2: Create fragment
        frag_result = create_fragment(analysis, source_branch='TEST')
        assert frag_result['success'] is True

        fragment = frag_result['fragment']
        assert fragment['metadata']['source_branch'] == 'TEST'

        # Step 3: Store fragment
        store_result = store_fragment(fragment, db_path=temp_chroma_dir)
        assert store_result['success'] is True
        assert store_result['total_fragments'] >= 1

    def test_generated_essence_quality(self, debugging_chat):
        """Generated essence captures key dimensions"""
        analysis = analyze_conversation(debugging_chat)
        frag_result = create_fragment(analysis)
        content = frag_result['fragment']['content']

        # Should mention key detected patterns
        assert 'Technical' in content or 'Emotional' in content or 'Collaboration' in content

    def test_multiple_conversations_batch(self, temp_chroma_dir):
        """Store fragments from multiple conversations"""
        conversations = [
            [
                {"role": "user", "content": "Help me debug this error"},
                {"role": "assistant", "content": "Let me trace the issue"}
            ],
            [
                {"role": "user", "content": "I want to understand modules"},
                {"role": "assistant", "content": "Modules help organize code"}
            ],
            [
                {"role": "user", "content": "This is frustrating!"},
                {"role": "assistant", "content": "Got it working!"}
            ]
        ]

        fragments = []
        for i, chat in enumerate(conversations):
            analysis = analyze_conversation(chat)
            frag_result = create_fragment(analysis, source_branch=f'TEST_{i}')
            fragments.append(frag_result['fragment'])

        result = store_fragments_batch(fragments, db_path=temp_chroma_dir)

        assert result['success'] is True
        assert result['stored'] == 3
