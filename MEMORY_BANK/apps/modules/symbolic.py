#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: symbolic.py - Symbolic Memory Orchestration Module
# Date: 2026-02-04
# Version: 0.1.0
# Category: memory_bank/modules
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2026-02-04): Initial version - Fragmented Memory Phase 1
#
# CODE STANDARDS:
#   - Thin orchestration: Delegate all logic to handlers
#   - No business logic: Only coordinate workflow
#   - handle_command() pattern
# =============================================

"""
Symbolic Memory Orchestration Module

Exposes symbolic memory extraction functions for fragmented memory storage.
This module provides the public API for analyzing conversations and extracting
symbolic dimensions (technical flow, emotional arc, collaboration patterns, etc.)

Part of the Fragmented Memory implementation.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Infrastructure setup
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))  # For MEMORY_BANK package imports

# Service imports
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header

# Handler imports (domain-organized)
from MEMORY_BANK.apps.handlers.symbolic import extractor
from MEMORY_BANK.apps.handlers.symbolic import storage
from MEMORY_BANK.apps.handlers.symbolic import retriever
from MEMORY_BANK.apps.handlers.symbolic import hook


# =============================================================================
# PUBLIC API - Delegated to handlers
# =============================================================================

def extract_technical_flow(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze technical patterns from conversation

    Detects problem/debug/breakthrough patterns.

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with 'success', 'patterns' list, and analysis details
    """
    return extractor.extract_technical_flow(chat_history)


def extract_emotional_journey(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect emotional arc from conversation tone and patterns

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with 'success', 'arc' list, and emotion timeline
    """
    return extractor.extract_emotional_journey(chat_history)


def extract_collaboration_patterns(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Identify relationship dynamics and interaction patterns

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with 'success', 'patterns' list, and interaction metrics
    """
    return extractor.extract_collaboration_patterns(chat_history)


def extract_key_learnings(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract core insights and lessons from conversation

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with 'success', 'insights' list, and detected categories
    """
    return extractor.extract_key_learnings(chat_history)


def extract_context_triggers(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract keywords that should trigger this memory in future conversations

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with 'success', 'triggers' list, and term frequencies
    """
    return extractor.extract_context_triggers(chat_history)


def extract_symbolic_dimensions(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract all symbolic dimensions from conversation

    Calls all individual extractors and combines results into
    a unified symbolic representation.

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with all extracted dimensions and metadata
    """
    return extractor.extract_symbolic_dimensions(chat_history)


def analyze_conversation(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point for conversation analysis

    Extracts symbolic dimensions and adds conversation metadata
    for complete fragmented memory representation.

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with full analysis including dimensions and metadata
    """
    return extractor.analyze_conversation(chat_history)


# =============================================================================
# STORAGE API - Delegated to handlers
# =============================================================================

def create_fragment(
    analysis: Dict[str, Any],
    content: str | None = None,
    source_branch: str | None = None
) -> Dict[str, Any]:
    """Create fragment from analysis, fire trigger on success"""
    result = storage.create_fragment(analysis, content, source_branch)
    if result.get('success'):
        try:
            from trigger.apps.modules.core import trigger
            trigger.fire('fragment_created',
                        fragment_id=result['fragment'].get('id'),
                        source_branch=source_branch or 'unknown')
        except Exception:
            pass  # Trigger optional
    return result


def store_fragment(
    fragment: Dict[str, Any],
    db_path: Path | None = None
) -> Dict[str, Any]:
    """Store fragment in ChromaDB, fire trigger on success"""
    result = storage.store_fragment(fragment, db_path)
    if result.get('success'):
        try:
            from trigger.apps.modules.core import trigger
            trigger.fire('fragment_stored', fragment_id=result.get('fragment_id'))
        except Exception:
            pass  # Trigger optional
    return result


def store_fragments_batch(
    fragments: List[Dict[str, Any]],
    db_path: Path | None = None
) -> Dict[str, Any]:
    """
    Store multiple fragments in ChromaDB in batch

    More efficient than storing one at a time when processing
    multiple conversations.

    Args:
        fragments: List of fragment dicts from create_fragment()
        db_path: Optional ChromaDB path (default: MEMORY_BANK/.chroma)

    Returns:
        Dict with 'success', batch storage details
    """
    return storage.store_fragments_batch(fragments, db_path)


def flatten_dimensions(fragment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten fragment dimensions for ChromaDB metadata storage

    ChromaDB metadata must be flat (string/int/float/bool).
    This converts nested dimensions to indexed keys.

    Args:
        fragment: Fragment dict with nested dimensions

    Returns:
        Dict with 'success', 'metadata' containing flattened metadata
    """
    return storage.flatten_dimensions(fragment)


# =============================================================================
# RETRIEVAL API - Delegated to handlers
# =============================================================================

def retrieve_fragments(
    query: str | None = None,
    dimension_filters: Dict[str, str] | None = None,
    trigger_keywords: List[str] | None = None,
    n_results: int = 5,
    db_path: Path | None = None
) -> Dict[str, Any]:
    """
    Retrieve fragments using combined search methods

    Combines vector similarity with dimension filtering and trigger matching.

    Args:
        query: Optional search query for vector similarity
        dimension_filters: Optional dict of dimension filters
        trigger_keywords: Optional list of trigger keywords
        n_results: Number of results to return
        db_path: Optional ChromaDB path (default: MEMORY_BANK/.chroma)

    Returns:
        Dict with 'success', 'results' list with relevance scores
    """
    return retriever.retrieve_fragments(query, dimension_filters, trigger_keywords, n_results, db_path)


def search_fragments_by_vector(
    query: str,
    n_results: int = 5,
    db_path: Path | None = None
) -> Dict[str, Any]:
    """
    Search fragments by vector similarity only

    Args:
        query: Search query text
        n_results: Number of results to return
        db_path: Optional ChromaDB path

    Returns:
        Dict with 'success', 'results' list
    """
    return retriever.search_by_vector(query, n_results, db_path)


def search_fragments_by_dimensions(
    dimension_filters: Dict[str, str],
    n_results: int = 5,
    db_path: Path | None = None
) -> Dict[str, Any]:
    """
    Search fragments by dimension filters only

    Args:
        dimension_filters: Dict of dimension_key: value pairs
        n_results: Number of results to return
        db_path: Optional ChromaDB path

    Returns:
        Dict with 'success', 'results' list
    """
    return retriever.search_by_dimensions(dimension_filters, n_results, db_path)


def search_fragments_by_triggers(
    keywords: List[str],
    n_results: int = 5,
    db_path: Path | None = None
) -> Dict[str, Any]:
    """
    Search fragments by trigger keywords only

    Args:
        keywords: List of keywords to search
        n_results: Number of results to return
        db_path: Optional ChromaDB path

    Returns:
        Dict with 'success', 'results' list
    """
    return retriever.search_by_triggers(keywords, n_results, db_path)


# =============================================================================
# HOOK API - Delegated to handlers
# =============================================================================

def extract_conversation_context(
    messages: List[Dict[str, Any]],
    max_messages: int = 5
) -> Dict[str, Any]:
    """
    Extract keywords, themes, and mood from recent conversation messages

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        max_messages: Maximum recent messages to analyze

    Returns:
        Dict with 'success', 'keywords', 'mood', 'themes'
    """
    return hook.extract_conversation_context(messages, max_messages)


def find_relevant_fragments(
    context: Dict[str, Any],
    n_results: int = 3,
    db_path: Path | None = None
) -> Dict[str, Any]:
    """
    Query fragments based on extracted conversation context

    Args:
        context: Output from extract_conversation_context()
        n_results: Maximum fragments to return
        db_path: Optional ChromaDB path

    Returns:
        Dict with 'success', 'fragments' list with relevance scores
    """
    return hook.find_relevant_fragments(context, n_results, db_path)


def format_fragment_recall(fragment: Dict[str, Any]) -> str:
    """
    Format a fragment as natural recall text

    Creates a "This reminds me of..." style output.

    Args:
        fragment: Fragment dict with 'content' and 'metadata'

    Returns:
        Formatted recall string
    """
    return hook.format_fragment_recall(fragment)


def should_surface_fragment(
    fragment: Dict[str, Any] | None = None,
    config: Dict[str, Any] | None = None
) -> tuple:
    """
    Check if a fragment should be surfaced based on rules

    Args:
        fragment: Optional fragment to check
        config: Optional config dict

    Returns:
        Tuple of (should_surface: bool, reason: str)
    """
    return hook.should_surface_fragment(fragment, config)


def process_hook(
    messages: List[Dict[str, Any]],
    config: Dict[str, Any] | None = None,
    db_path: Path | None = None
) -> Dict[str, Any]:
    """
    Main hook function - process messages and surface relevant fragments

    Args:
        messages: Recent conversation messages
        config: Optional config dict
        db_path: Optional ChromaDB path

    Returns:
        Dict with 'success', 'surfaced' bool, 'recall' text if surfaced
    """
    return hook.process_hook(messages, config, db_path)


def load_hook_config(config_path: Path | None = None) -> Dict[str, Any]:
    """
    Load hook configuration from JSON file

    Args:
        config_path: Path to config JSON

    Returns:
        Dict with configuration values
    """
    return hook.load_config(config_path)


def reset_hook_session() -> None:
    """Reset hook session state for new conversation"""
    return hook.reset_session()


def get_hook_session_state() -> Dict[str, Any]:
    """
    Get current hook session state for debugging

    Returns:
        Dict with session state values
    """
    return hook.get_session_state()


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle symbolic memory commands

    Commands supported:
    - analyze <file>: Analyze a JSON conversation file
    - fragments <query>: Search symbolic fragments
    - hook-test <text>: Test hook with sample conversation
    - demo: Run a demonstration analysis
    - help: Show help message

    Args:
        command: Command name
        args: Additional arguments

    Returns:
        True if command handled, False otherwise
    """
    if command in ('--help', '-h', 'help'):
        print_help()
        return True

    if command == 'demo':
        run_demo()
        return True

    if command == 'analyze':
        if not args:
            console.print("[red]Error:[/red] File path required")
            console.print("Usage: symbolic analyze <conversation.json>")
            return True
        analyze_file(args[0])
        return True

    if command == 'fragments':
        search_fragments_cli(args)
        return True

    if command == 'hook-test':
        run_hook_test(args)
        return True

    return False


def print_help() -> None:
    """Display symbolic module help"""
    console.print()
    header("Symbolic Memory Module - Conversation Analysis")
    console.print()
    console.print("[bold]USAGE:[/bold]")
    console.print("  python3 symbolic.py <command> [args]")
    console.print()
    console.print("[bold]COMMANDS:[/bold]")
    console.print("  [cyan]demo[/cyan]               Run demonstration analysis")
    console.print("  [cyan]analyze <file>[/cyan]     Analyze a conversation JSON file")
    console.print("  [cyan]fragments <query>[/cyan]  Search symbolic fragments")
    console.print("  [cyan]hook-test <text>[/cyan]   Test hook with sample conversation text")
    console.print("  [cyan]help[/cyan]               Show this help message")
    console.print()
    console.print("[bold]FRAGMENTS OPTIONS:[/bold]")
    console.print("  [cyan]--dimension KEY=VALUE[/cyan]  Filter by dimension (e.g., emotional_0=frustration)")
    console.print("  [cyan]--trigger KEYWORD[/cyan]      Match trigger keyword")
    console.print("  [cyan]--n N[/cyan]                  Number of results (default: 5)")
    console.print()
    console.print("[bold]HOOK-TEST OPTIONS:[/bold]")
    console.print("  [cyan]--bypass[/cyan]               Bypass frequency/cooldown checks")
    console.print()
    console.print("[bold]EXTRACTED DIMENSIONS:[/bold]")
    console.print("  [yellow]Technical Flow[/yellow]       - problem/debug/breakthrough patterns")
    console.print("  [yellow]Emotional Journey[/yellow]    - frustration/excitement arcs")
    console.print("  [yellow]Collaboration[/yellow]        - user_directed/balanced dynamics")
    console.print("  [yellow]Key Learnings[/yellow]        - discoveries, insights")
    console.print("  [yellow]Context Triggers[/yellow]     - keywords that should surface memory")
    console.print()
    console.print("[bold]EXAMPLES:[/bold]")
    console.print("  # Run demo analysis")
    console.print("  [dim]python3 symbolic.py demo[/dim]")
    console.print()
    console.print("  # Analyze conversation file")
    console.print("  [dim]python3 symbolic.py analyze chat_history.json[/dim]")
    console.print()
    console.print("  # Search fragments by query")
    console.print("  [dim]python3 symbolic.py fragments \"debugging frustration\"[/dim]")
    console.print()
    console.print("  # Search with dimension filter")
    console.print("  [dim]python3 symbolic.py fragments \"debug\" --dimension emotional_0=frustration_to_breakthrough[/dim]")
    console.print()
    console.print("  # Search with trigger keywords")
    console.print("  [dim]python3 symbolic.py fragments \"error\" --trigger error --trigger debug[/dim]")
    console.print()
    console.print("  # Test hook with sample text")
    console.print("  [dim]python3 symbolic.py hook-test \"I'm stuck on this error\"[/dim]")
    console.print()
    console.print("  # Test hook bypassing cooldown")
    console.print("  [dim]python3 symbolic.py hook-test \"debugging frustration\" --bypass[/dim]")
    console.print()


def run_demo() -> None:
    """Run demonstration of symbolic analysis"""
    console.print()
    header("Symbolic Memory - Demo Analysis")
    console.print()

    # Sample conversation
    demo_chat = [
        {"role": "user", "content": "I have an error in my code, it keeps failing and I'm stuck"},
        {"role": "assistant", "content": "Let me help debug this issue. Can you trace where it's failing?"},
        {"role": "user", "content": "I tried checking the logs but I'm confused about what's wrong"},
        {"role": "assistant", "content": "Let's try a different approach. I'll explain the fix step by step."},
        {"role": "user", "content": "Got it! That works! Finally a breakthrough! This is awesome!"}
    ]

    console.print("[cyan]Sample conversation:[/cyan]")
    for msg in demo_chat:
        role = msg['role'].capitalize()
        console.print(f"  [{role}]: {msg['content'][:60]}...")
    console.print()

    # Analyze
    result = analyze_conversation(demo_chat)

    if result['success']:
        dims = result['dimensions']
        meta = result['metadata']

        console.print("[green]✓[/green] Analysis complete")
        console.print()

        console.print("[bold cyan]Extracted Dimensions:[/bold cyan]")
        console.print(f"  [yellow]Technical:[/yellow]     {dims.get('technical', [])}")
        console.print(f"  [yellow]Emotional:[/yellow]     {dims.get('emotional', [])}")
        console.print(f"  [yellow]Collaboration:[/yellow] {dims.get('collaboration', [])}")
        console.print(f"  [yellow]Learnings:[/yellow]     {dims.get('learnings', [])}")
        console.print(f"  [yellow]Triggers:[/yellow]      {dims.get('triggers', [])}")
        console.print()

        console.print("[bold cyan]Metadata:[/bold cyan]")
        console.print(f"  [dim]Messages:[/dim] {result['message_count']}")
        console.print(f"  [dim]Words:[/dim]    {meta.get('total_words', 0)}")
        console.print(f"  [dim]Depth:[/dim]    {meta.get('depth', 'unknown')}")
        console.print()
    else:
        console.print(f"[red]✗[/red] Analysis failed: {result.get('error', 'Unknown error')}")


def search_fragments_cli(args: List[str]) -> None:
    """Execute fragment search from CLI arguments"""
    from rich.panel import Panel

    # Parse arguments
    query_parts = []
    dimension_filters: Dict[str, str] = {}
    trigger_keywords: List[str] = []
    n_results = 5

    i = 0
    while i < len(args):
        if args[i] == '--dimension' and i + 1 < len(args):
            # Parse KEY=VALUE
            dim_arg = args[i + 1]
            if '=' in dim_arg:
                key, value = dim_arg.split('=', 1)
                dimension_filters[key] = value
            else:
                console.print(f"[red]Error:[/red] Invalid dimension format: {dim_arg}")
                console.print("Expected: --dimension KEY=VALUE")
                return
            i += 2
        elif args[i] == '--trigger' and i + 1 < len(args):
            trigger_keywords.append(args[i + 1])
            i += 2
        elif args[i] == '--n' and i + 1 < len(args):
            try:
                n_results = int(args[i + 1])
            except ValueError:
                console.print(f"[red]Error:[/red] Invalid number: {args[i + 1]}")
                return
            i += 2
        else:
            query_parts.append(args[i])
            i += 1

    query = ' '.join(query_parts) if query_parts else None

    if not query and not dimension_filters and not trigger_keywords:
        console.print("[red]Error:[/red] Search query, dimension filter, or trigger required")
        console.print("Usage: symbolic fragments <query> [--dimension KEY=VALUE] [--trigger KEYWORD]")
        return

    console.print()
    header("Symbolic Fragments - Search")
    console.print()

    if query:
        console.print(f"[cyan]Query:[/cyan] {query}")
    if dimension_filters:
        console.print(f"[cyan]Dimensions:[/cyan] {dimension_filters}")
    if trigger_keywords:
        console.print(f"[cyan]Triggers:[/cyan] {trigger_keywords}")
    console.print()

    # Execute search
    console.print("[dim]Searching fragments...[/dim]")

    result = retrieve_fragments(
        query=query,
        dimension_filters=dimension_filters if dimension_filters else None,
        trigger_keywords=trigger_keywords if trigger_keywords else None,
        n_results=n_results
    )

    if not result.get('success'):
        error_msg = result.get('error', 'Unknown error')
        logger.error(f"[symbolic] Fragment search failed: {error_msg}")
        console.print(f"[red]Error:[/red] {error_msg}")
        return

    results = result.get('results', [])
    methods = result.get('search_methods', [])

    console.print(f"[green]Found {len(results)} fragments[/green] (methods: {', '.join(methods)})")
    console.print()

    if not results:
        console.print("[yellow]No matching fragments found[/yellow]")
        console.print()
        console.print("[dim]Try:[/dim]")
        console.print("  Different search terms")
        console.print("  Broader query without filters")
        console.print("  Store fragments first: python3 symbolic.py demo")
        return

    # Display results
    for i, frag in enumerate(results, 1):
        content = frag.get('content', '')
        metadata = frag.get('metadata', {})
        relevance = frag.get('relevance_score', frag.get('similarity', 0))
        sources = frag.get('_sources', ['unknown'])

        # Build metadata display
        meta_lines = []
        if metadata.get('timestamp'):
            meta_lines.append(f"Time: {metadata['timestamp']}")
        if metadata.get('depth'):
            meta_lines.append(f"Depth: {metadata['depth']}")
        if metadata.get('source_branch'):
            meta_lines.append(f"Branch: {metadata['source_branch']}")

        # Show dimensions
        dim_parts = []
        for key in ['technical_0', 'emotional_0', 'collaboration_0', 'learnings_0']:
            if key in metadata:
                dim_parts.append(f"{key.replace('_0', '')}: {metadata[key]}")
        if dim_parts:
            meta_lines.append(f"Dims: {', '.join(dim_parts)}")

        meta_text = " | ".join(meta_lines) if meta_lines else ""

        panel_title = f"Result {i} - Relevance: {relevance:.2%} (via {', '.join(sources)})"

        panel_content = content
        if meta_text:
            panel_content += f"\n\n[dim]{meta_text}[/dim]"

        console.print(Panel(
            panel_content,
            title=panel_title,
            title_align="left",
            border_style="cyan" if relevance > 0.7 else "blue" if relevance > 0.5 else "dim"
        ))

    console.print()
    logger.info(f"[symbolic] Displayed {len(results)} fragment results")


def run_hook_test(args: List[str]) -> None:
    """Test hook with sample conversation text"""
    from rich.panel import Panel

    # Parse arguments
    text_parts = []
    bypass_checks = False

    for arg in args:
        if arg == '--bypass':
            bypass_checks = True
        else:
            text_parts.append(arg)

    text = ' '.join(text_parts) if text_parts else "I'm stuck on this error and need help debugging"

    console.print()
    header("Fragmented Memory Hook - Test")
    console.print()

    # Build sample messages from text
    messages = [
        {"role": "user", "content": text}
    ]

    console.print(f"[cyan]Test input:[/cyan] {text}")
    console.print(f"[cyan]Bypass checks:[/cyan] {bypass_checks}")
    console.print()

    # Reset session for clean test
    reset_hook_session()

    # If bypassing, set session state to allow surfacing
    if bypass_checks:
        hook.SESSION_STATE['messages_since_last'] = 100
        hook.SESSION_STATE['last_surface_time'] = 0

    # Extract context first
    console.print("[bold]Step 1: Context Extraction[/bold]")
    context = extract_conversation_context(messages)

    if context.get('success'):
        console.print(f"  [green]Keywords:[/green] {context.get('keywords', [])}")
        console.print(f"  [green]Mood:[/green] {context.get('mood', 'neutral')}")
        console.print(f"  [green]Themes:[/green] {context.get('themes', [])}")
    else:
        console.print(f"  [red]Failed:[/red] {context.get('error', 'Unknown')}")
        return

    console.print()

    # Find relevant fragments
    console.print("[bold]Step 2: Fragment Search[/bold]")
    frag_result = find_relevant_fragments(context, n_results=3)

    if frag_result.get('success'):
        fragments = frag_result.get('fragments', [])
        console.print(f"  [green]Query used:[/green] {frag_result.get('query_used', '')}")
        console.print(f"  [green]Threshold:[/green] {frag_result.get('threshold_applied', 0.3)}")
        console.print(f"  [green]Fragments found:[/green] {len(fragments)}")

        if fragments:
            for i, frag in enumerate(fragments, 1):
                score = frag.get('relevance_score', frag.get('similarity', 0))
                content = frag.get('content', '')[:80]
                console.print(f"    [{i}] Score: {score:.2%} - {content}...")
    else:
        console.print(f"  [yellow]No fragments:[/yellow] {frag_result.get('message', frag_result.get('error', ''))}")

    console.print()

    # Check surfacing rules
    console.print("[bold]Step 3: Surfacing Check[/bold]")
    can_surface, reason = should_surface_fragment()
    console.print(f"  [cyan]Can surface:[/cyan] {can_surface}")
    console.print(f"  [cyan]Reason:[/cyan] {reason}")

    console.print()

    # Run full hook process
    console.print("[bold]Step 4: Full Hook Process[/bold]")
    result = process_hook(messages)

    if result.get('success'):
        if result.get('surfaced'):
            console.print("[green]Fragment surfaced![/green]")
            console.print()

            recall = result.get('recall', '')
            console.print(Panel(
                recall,
                title="Memory Recall",
                border_style="green"
            ))

            console.print()
            console.print(f"[dim]Fragment ID: {result.get('fragment_id')}[/dim]")
            console.print(f"[dim]Relevance: {result.get('relevance_score', 0):.2%}[/dim]")
        else:
            console.print(f"[yellow]Not surfaced:[/yellow] {result.get('reason', 'Unknown')}")
    else:
        console.print(f"[red]Hook failed:[/red] {result.get('error', 'Unknown')}")

    console.print()

    # Show session state
    console.print("[bold]Session State:[/bold]")
    state = get_hook_session_state()
    console.print(f"  [dim]Fragments surfaced:[/dim] {state.get('fragments_surfaced', 0)}")
    console.print(f"  [dim]Messages since last:[/dim] {state.get('messages_since_last', 0)}")
    console.print()


def analyze_file(file_path: str) -> None:
    """Analyze a conversation JSON file"""
    from MEMORY_BANK.apps.handlers.json import json_handler

    path = Path(file_path)
    if not path.exists():
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        return

    read_result = json_handler.read_memory_file(path)
    if not read_result.get('success'):
        console.print(f"[red]Error:[/red] {read_result.get('error', 'Failed to read JSON')}")
        return

    chat_history = read_result.get('data')

    if not isinstance(chat_history, list):
        console.print("[red]Error:[/red] Expected JSON array of messages")
        return

    console.print()
    header(f"Analyzing: {path.name}")
    console.print()

    result = analyze_conversation(chat_history)

    if result['success']:
        dims = result['dimensions']
        meta = result['metadata']

        console.print("[green]✓[/green] Analysis complete")
        console.print()

        console.print("[bold cyan]Extracted Dimensions:[/bold cyan]")
        console.print(f"  [yellow]Technical:[/yellow]     {dims.get('technical', [])}")
        console.print(f"  [yellow]Emotional:[/yellow]     {dims.get('emotional', [])}")
        console.print(f"  [yellow]Collaboration:[/yellow] {dims.get('collaboration', [])}")
        console.print(f"  [yellow]Learnings:[/yellow]     {dims.get('learnings', [])}")
        console.print(f"  [yellow]Triggers:[/yellow]      {dims.get('triggers', [])}")
        console.print()

        console.print("[bold cyan]Metadata:[/bold cyan]")
        console.print(f"  [dim]Messages:[/dim] {result['message_count']}")
        console.print(f"  [dim]Words:[/dim]    {meta.get('total_words', 0)}")
        console.print(f"  [dim]Depth:[/dim]    {meta.get('depth', 'unknown')}")
        console.print()
    else:
        console.print(f"[red]✗[/red] Analysis failed: {result.get('error', 'Unknown error')}")


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Handle --help before argparse (module standard)
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h', 'help'):
        handle_command('help', [])
        sys.exit(0)

    # Execute command via handle_command
    command = sys.argv[1]
    if not handle_command(command, sys.argv[2:]):
        console.print(f"[red]Unknown command:[/red] {command}")
        console.print("Run with [cyan]help[/cyan] for available commands")
        sys.exit(1)
