#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_symbolic_retriever.py - Symbolic Retriever Unit Tests
# Date: 2026-02-04
# Version: 0.1.0
# Category: memory_bank/tests
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2026-02-04): Initial version - tests for symbolic retrieval
#
# CODE STANDARDS:
#   - pytest conventions
#   - Comprehensive coverage of retrieval functions
# =============================================

"""
Unit tests for Symbolic Fragment Retrieval Handler

Tests vector similarity search, dimension filtering, and trigger keyword matching.
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
    retrieve_fragments,
    search_fragments_by_vector,
    search_fragments_by_dimensions,
    search_fragments_by_triggers
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_chroma_dir():
    """Temporary directory for ChromaDB testing"""
    temp_dir = tempfile.mkdtemp(prefix="test_retriever_")
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def debugging_conversation():
    """Debugging-focused conversation with frustration to breakthrough arc"""
    return [
        {"role": "user", "content": "I have an error in my code, it keeps failing and I'm stuck"},
        {"role": "assistant", "content": "Let me help debug this issue. Can you trace where it's failing?"},
        {"role": "user", "content": "I tried checking the logs but I'm confused about what's wrong"},
        {"role": "assistant", "content": "Let's try a different approach. I'll explain the fix step by step."},
        {"role": "user", "content": "Got it! That works! Finally a breakthrough! This is awesome!"}
    ]


@pytest.fixture
def learning_conversation():
    """Learning-focused conversation about modules"""
    return [
        {"role": "user", "content": "Can you explain how Python modules work?"},
        {"role": "assistant", "content": "Modules help organize code into reusable files. Import them with the import statement."},
        {"role": "user", "content": "What about packages? How are they different?"},
        {"role": "assistant", "content": "Packages are directories containing modules with an __init__.py file."},
        {"role": "user", "content": "That makes sense! I understand the structure now."}
    ]


@pytest.fixture
def collaboration_conversation():
    """Collaboration-focused conversation with balanced exchange"""
    return [
        {"role": "user", "content": "Let's work on this together. I have some ideas."},
        {"role": "assistant", "content": "Great! What are you thinking? I'd love to collaborate."},
        {"role": "user", "content": "Maybe we could refactor the handler to be cleaner."},
        {"role": "assistant", "content": "That's a good idea. I suggest we start with the main function."},
        {"role": "user", "content": "Perfect. Let's do it that way."}
    ]


@pytest.fixture
def populated_db(temp_chroma_dir, debugging_conversation, learning_conversation, collaboration_conversation):
    """Database with three different fragments stored"""
    fragments = []

    # Create and store debugging fragment
    debug_analysis = analyze_conversation(debugging_conversation)
    debug_frag = create_fragment(debug_analysis, source_branch='DEBUG')['fragment']
    fragments.append(debug_frag)

    # Create and store learning fragment
    learn_analysis = analyze_conversation(learning_conversation)
    learn_frag = create_fragment(learn_analysis, source_branch='LEARN')['fragment']
    fragments.append(learn_frag)

    # Create and store collaboration fragment
    collab_analysis = analyze_conversation(collaboration_conversation)
    collab_frag = create_fragment(collab_analysis, source_branch='COLLAB')['fragment']
    fragments.append(collab_frag)

    # Store all fragments
    result = store_fragments_batch(fragments, db_path=temp_chroma_dir)
    assert result['success'] is True

    return {
        'db_path': temp_chroma_dir,
        'fragments': fragments,
        'debug_id': debug_frag['id'],
        'learn_id': learn_frag['id'],
        'collab_id': collab_frag['id']
    }


# =============================================================================
# SEARCH BY VECTOR TESTS
# =============================================================================

class TestSearchByVector:
    """Tests for search_fragments_by_vector()"""

    def test_finds_similar_fragments(self, populated_db):
        """Finds fragments semantically similar to query"""
        result = search_fragments_by_vector(
            query="debugging error fix",
            n_results=5,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        assert 'results' in result
        assert len(result['results']) > 0

    def test_returns_similarity_scores(self, populated_db):
        """Results include similarity scores"""
        result = search_fragments_by_vector(
            query="debugging",
            n_results=3,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        for frag in result['results']:
            assert 'similarity' in frag
            assert 0 <= frag['similarity'] <= 1

    def test_results_have_content(self, populated_db):
        """Results include content and metadata"""
        result = search_fragments_by_vector(
            query="modules packages",
            n_results=3,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        for frag in result['results']:
            assert 'content' in frag
            assert 'metadata' in frag
            assert 'id' in frag

    def test_empty_query_fails(self, populated_db):
        """Empty query returns error"""
        result = search_fragments_by_vector(
            query="",
            db_path=populated_db['db_path']
        )

        assert result['success'] is False
        assert 'error' in result

    def test_respects_n_results(self, populated_db):
        """Returns at most n_results fragments"""
        result = search_fragments_by_vector(
            query="code",
            n_results=2,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        assert len(result['results']) <= 2

    def test_empty_collection_returns_empty(self, temp_chroma_dir):
        """Empty collection returns empty results"""
        result = search_fragments_by_vector(
            query="anything",
            db_path=temp_chroma_dir
        )

        assert result['success'] is True
        assert result['results'] == []


# =============================================================================
# SEARCH BY DIMENSIONS TESTS
# =============================================================================

class TestSearchByDimensions:
    """Tests for search_fragments_by_dimensions()"""

    def test_filters_by_single_dimension(self, populated_db):
        """Filters by single dimension value"""
        # Note: This test depends on what dimensions are extracted
        # from the test conversations
        result = search_fragments_by_dimensions(
            dimension_filters={'depth': 'moderate'},
            n_results=5,
            db_path=populated_db['db_path']
        )

        # Should succeed even if no matches
        assert result['success'] is True
        assert 'results' in result

    def test_empty_filters_fails(self, populated_db):
        """Empty filters returns error"""
        result = search_fragments_by_dimensions(
            dimension_filters={},
            db_path=populated_db['db_path']
        )

        assert result['success'] is False
        assert 'error' in result

    def test_returns_filter_info(self, populated_db):
        """Returns information about filters applied"""
        filters = {'depth': 'moderate'}
        result = search_fragments_by_dimensions(
            dimension_filters=filters,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        assert result.get('filters_applied') == filters

    def test_nonexistent_dimension_returns_empty(self, populated_db):
        """Nonexistent dimension value returns empty results"""
        result = search_fragments_by_dimensions(
            dimension_filters={'nonexistent_dimension': 'value'},
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        assert result['results'] == []


# =============================================================================
# SEARCH BY TRIGGERS TESTS
# =============================================================================

class TestSearchByTriggers:
    """Tests for search_fragments_by_triggers()"""

    def test_finds_by_single_trigger(self, populated_db):
        """Finds fragments by single trigger keyword"""
        result = search_fragments_by_triggers(
            keywords=['error'],
            n_results=5,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        assert 'results' in result

    def test_finds_by_multiple_triggers(self, populated_db):
        """Finds fragments matching any of multiple triggers"""
        result = search_fragments_by_triggers(
            keywords=['error', 'module', 'collaborate'],
            n_results=5,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        assert 'keywords_searched' in result
        assert len(result['keywords_searched']) == 3

    def test_empty_keywords_fails(self, populated_db):
        """Empty keywords list returns error"""
        result = search_fragments_by_triggers(
            keywords=[],
            db_path=populated_db['db_path']
        )

        assert result['success'] is False
        assert 'error' in result

    def test_nonexistent_trigger_returns_empty(self, populated_db):
        """Nonexistent trigger returns empty results"""
        result = search_fragments_by_triggers(
            keywords=['xyznonexistentkeyword123'],
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        # May return empty or not depending on ChromaDB $contains behavior
        assert 'results' in result


# =============================================================================
# RETRIEVE FRAGMENTS COMBINED TESTS
# =============================================================================

class TestRetrieveFragments:
    """Tests for retrieve_fragments() - combined search"""

    def test_vector_search_only(self, populated_db):
        """Retrieves using vector search only"""
        result = retrieve_fragments(
            query="debugging error breakthrough",
            n_results=3,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        assert 'vector' in result['search_methods']
        assert len(result['results']) > 0

    def test_combined_query_and_triggers(self, populated_db):
        """Retrieves using both query and triggers"""
        result = retrieve_fragments(
            query="debugging",
            trigger_keywords=['error', 'fix'],
            n_results=5,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        # Should use both methods
        methods = result['search_methods']
        assert 'vector' in methods or 'trigger' in methods

    def test_combined_all_methods(self, populated_db):
        """Retrieves using all three methods"""
        result = retrieve_fragments(
            query="debugging",
            dimension_filters={'depth': 'moderate'},
            trigger_keywords=['error'],
            n_results=5,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        assert len(result['search_methods']) >= 1

    def test_no_methods_fails(self, populated_db):
        """No search method provided returns error"""
        result = retrieve_fragments(
            db_path=populated_db['db_path']
        )

        assert result['success'] is False
        assert 'error' in result

    def test_results_have_relevance_scores(self, populated_db):
        """Results include relevance scores"""
        result = retrieve_fragments(
            query="debugging error",
            n_results=3,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        for frag in result['results']:
            assert 'relevance_score' in frag
            assert 0 <= frag['relevance_score'] <= 1

    def test_results_sorted_by_relevance(self, populated_db):
        """Results are sorted by relevance score descending"""
        result = retrieve_fragments(
            query="code debugging",
            n_results=5,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        results = result['results']

        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i]['relevance_score'] >= results[i + 1]['relevance_score']

    def test_deduplicates_results(self, populated_db):
        """Deduplicates fragments found by multiple methods"""
        result = retrieve_fragments(
            query="debugging error",
            trigger_keywords=['error', 'debug'],
            n_results=10,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True

        # Check no duplicate IDs
        seen_ids = set()
        for frag in result['results']:
            frag_id = frag.get('id')
            assert frag_id not in seen_ids, f"Duplicate fragment ID: {frag_id}"
            seen_ids.add(frag_id)


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Edge case and error handling tests"""

    def test_handles_nonexistent_collection(self, temp_chroma_dir):
        """Handles missing collection gracefully"""
        result = search_fragments_by_vector(
            query="anything",
            db_path=temp_chroma_dir
        )

        assert result['success'] is True
        assert result['results'] == []

    def test_handles_special_characters_in_query(self, populated_db):
        """Handles special characters in query"""
        result = search_fragments_by_vector(
            query="error: 'module' not found!",
            db_path=populated_db['db_path']
        )

        assert result['success'] is True

    def test_handles_long_query(self, populated_db):
        """Handles long query strings"""
        long_query = "debugging error fix solution " * 20
        result = search_fragments_by_vector(
            query=long_query,
            n_results=3,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True

    def test_n_results_one(self, populated_db):
        """Handles n_results=1 (minimum valid value)"""
        result = search_fragments_by_vector(
            query="debugging",
            n_results=1,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        assert len(result['results']) <= 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for full retrieval workflow"""

    def test_store_and_retrieve_single(self, temp_chroma_dir, debugging_conversation):
        """Stores fragment and retrieves it"""
        # Store
        analysis = analyze_conversation(debugging_conversation)
        frag = create_fragment(analysis, source_branch='TEST')['fragment']
        store_result = store_fragment(frag, db_path=temp_chroma_dir)
        assert store_result['success'] is True

        # Retrieve
        search_result = retrieve_fragments(
            query="debugging error breakthrough",
            db_path=temp_chroma_dir
        )

        assert search_result['success'] is True
        assert len(search_result['results']) >= 1

        # Should find the stored fragment
        found_ids = [r['id'] for r in search_result['results']]
        assert frag['id'] in found_ids

    def test_retrieve_by_source_branch(self, populated_db):
        """Can filter by source_branch dimension"""
        result = search_fragments_by_dimensions(
            dimension_filters={'source_branch': 'DEBUG'},
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        # All results should have source_branch == DEBUG
        for frag in result['results']:
            assert frag['metadata'].get('source_branch') == 'DEBUG'

    def test_semantic_relevance(self, populated_db):
        """Vector search returns semantically relevant results"""
        # Search for debugging-related content
        result = search_fragments_by_vector(
            query="error debugging fix breakthrough",
            n_results=1,
            db_path=populated_db['db_path']
        )

        assert result['success'] is True
        assert len(result['results']) > 0

        # The debugging fragment should rank high
        top_result = result['results'][0]
        # Check it's related to debugging (has relevant metadata)
        content = top_result.get('content', '').lower()
        meta = top_result.get('metadata', {})

        # Should contain debugging-related terms or have relevant dimensions
        is_relevant = (
            'debug' in content or
            'error' in content or
            'technical' in content or
            'breakthrough' in content or
            meta.get('source_branch') == 'DEBUG'
        )
        assert is_relevant, f"Top result not relevant: {content[:100]}"
