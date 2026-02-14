#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: search.py - Search Orchestration Module
# Date: 2025-11-27
# Version: 0.1.0
# Category: memory_bank/modules
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-27): Initial version - orchestrate semantic search
#
# CODE STANDARDS:
#   - Thin orchestration: Delegate all logic to handlers
#   - No business logic: Only coordinate workflow
#   - handle_command() pattern
# =============================================

"""
Search Orchestration Module

Coordinates semantic search workflow by calling handlers in sequence:
1. Encode query text to embedding (vector/embedder)
2. Search Chroma collections (storage/chroma via subprocess)
3. Format and display results (Rich panels)

Purpose:
    Thin orchestration layer - no business logic implementation.
    All domain logic lives in handlers.
"""

import sys
from pathlib import Path
from typing import List

# Infrastructure setup
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))  # For MEMORY_BANK package imports

# Service imports
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header

# Handler imports (domain-organized)
from MEMORY_BANK.apps.handlers.vector import embedder

# ChromaDB search via subprocess (uses Memory Bank's Python 3.12)
import subprocess
import json

CHROMA_SUBPROCESS_SCRIPT = Path.home() / "MEMORY_BANK" / "apps" / "handlers" / "storage" / "chroma_subprocess.py"
MEMORY_BANK_PYTHON = Path.home() / "MEMORY_BANK" / ".venv" / "bin" / "python3"


def _search_vectors_subprocess(
    query_embedding: list,
    branch: str | None = None,
    memory_type: str | None = None,
    n_results: int = 5,
    db_path: str | Path | None = None
) -> dict:
    """
    Search vectors via subprocess using Memory Bank's Python 3.12.

    This ensures ChromaDB compatibility regardless of calling Python version.
    """
    input_data = {
        'operation': 'search_vectors',
        'query_embedding': query_embedding,
        'branch': branch,
        'memory_type': memory_type,
        'n_results': n_results,
        'db_path': str(db_path) if db_path else None
    }

    try:
        result = subprocess.run(
            [str(MEMORY_BANK_PYTHON), str(CHROMA_SUBPROCESS_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return {'success': False, 'error': result.stderr or 'Subprocess failed'}

        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Search operation timed out'}
    except json.JSONDecodeError as e:
        return {'success': False, 'error': f'Invalid JSON response: {e}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle search commands

    Commands supported:
    - search <query>: Execute semantic search across all branches
    - help: Show search help

    Args:
        command: Command name
        args: Additional arguments (query text, options)

    Returns:
        True if command handled, False otherwise
    """
    if command in ('--help', '-h', 'help'):
        print_help()
        return True

    if command == 'search':
        if not args:
            console.print("[red]Error:[/red] Search query required")
            console.print("Usage: search <query> [--branch BRANCH] [--type TYPE] [--n N]")
            return True

        # Parse arguments
        query_parts = []
        branch = None
        memory_type = None
        n_results = 5

        i = 0
        while i < len(args):
            if args[i] == '--branch' and i + 1 < len(args):
                branch = args[i + 1]
                i += 2
            elif args[i] == '--type' and i + 1 < len(args):
                memory_type = args[i + 1]
                i += 2
            elif args[i] == '--n' and i + 1 < len(args):
                try:
                    n_results = int(args[i + 1])
                except ValueError:
                    console.print(f"[red]Error:[/red] Invalid number: {args[i + 1]}")
                    return True
                i += 2
            else:
                query_parts.append(args[i])
                i += 1

        query = ' '.join(query_parts)
        if not query:
            console.print("[red]Error:[/red] Search query required")
            return True

        execute_search(query, branch=branch, memory_type=memory_type, n_results=n_results)
        return True

    return False


def print_help() -> None:
    """Display search module help"""
    console.print()
    header("Search Module - Semantic Memory Search")
    console.print()
    console.print("[bold]USAGE:[/bold]")
    console.print("  python3 search.py search <query> [options]")
    console.print()
    console.print("[bold]COMMANDS:[/bold]")
    console.print("  [cyan]search <query>[/cyan]     Search across all memory collections")
    console.print("  [cyan]help[/cyan]                Show this help message")
    console.print()
    console.print("[bold]OPTIONS:[/bold]")
    console.print("  [cyan]--branch BRANCH[/cyan]    Filter by branch (e.g., SEED, CLI)")
    console.print("  [cyan]--type TYPE[/cyan]        Filter by memory type (observations, local)")
    console.print("  [cyan]--n N[/cyan]              Number of results (default: 5)")
    console.print()
    console.print("[bold]EXAMPLES:[/bold]")
    console.print("  # Search all branches")
    console.print("  [dim]python3 search.py search \"error handling patterns\"[/dim]")
    console.print()
    console.print("  # Search specific branch")
    console.print("  [dim]python3 search.py search \"registry bugs\" --branch SEED[/dim]")
    console.print()
    console.print("  # Search specific memory type")
    console.print("  [dim]python3 search.py search \"collaboration\" --type observations --n 10[/dim]")
    console.print()
    console.print("[bold]HOW IT WORKS:[/bold]")
    console.print("  1. Convert query to 384-dim embedding (all-MiniLM-L6-v2)")
    console.print("  2. Search ChromaDB collections for similar vectors")
    console.print("  3. Display top N most relevant memories")
    console.print()


# =============================================================================
# SEARCH ORCHESTRATION
# =============================================================================

def execute_search(query: str, branch: str | None = None, memory_type: str | None = None, n_results: int = 5) -> bool:
    """
    Execute semantic search and display results

    Workflow:
    1. Encode query to embedding vector
    2. Search ChromaDB via subprocess
    3. Format and display results with Rich

    Args:
        query: Search query text
        branch: Optional branch filter
        memory_type: Optional memory type filter
        n_results: Number of results to return

    Returns:
        True if search successful, False otherwise
    """
    console.print()
    header("Memory Bank - Semantic Search")
    console.print()

    # Step 1: Encode query
    console.print(f"[cyan]Query:[/cyan] {query}")
    if branch:
        console.print(f"[cyan]Branch:[/cyan] {branch}")
    if memory_type:
        console.print(f"[cyan]Type:[/cyan] {memory_type}")
    console.print()

    console.print("[dim]Encoding query...[/dim]")
    embed_result = embedder.encode_batch([query])

    if not embed_result['success']:
        error_msg = embed_result.get('error', 'Unknown error')
        logger.error(f"[search] Failed to encode query: {error_msg}")
        console.print(f"[red]✗[/red] Failed to encode query: {error_msg}")
        return False

    embeddings = embed_result.get('embeddings', [])
    if not embeddings:
        console.print("[red]✗[/red] No embedding generated")
        return False

    query_embedding = embeddings[0]
    # Convert numpy array to list for JSON serialization
    if hasattr(query_embedding, 'tolist'):
        query_embedding = query_embedding.tolist()

    logger.info(f"[search] Encoded query to {len(query_embedding)}-dim vector")

    # Step 2: Search via subprocess
    console.print("[dim]Searching collections...[/dim]")
    search_result = _search_vectors_subprocess(
        query_embedding=query_embedding,
        branch=branch,
        memory_type=memory_type,
        n_results=n_results
    )

    if not search_result['success']:
        error_msg = search_result.get('error', 'Unknown error')
        logger.error(f"[search] Search failed: {error_msg}")
        console.print(f"[red]✗[/red] Search failed: {error_msg}")
        return False

    results = search_result.get('results', [])
    collections_searched = search_result.get('collections_searched', 0)
    total_results = search_result.get('total_results', 0)

    logger.info(f"[search] Found {total_results} results across {collections_searched} collections")

    # Step 3: Display results
    console.print(f"[green]✓[/green] Found {total_results} results in {collections_searched} collections")
    console.print()

    if not results:
        console.print("[yellow]No matching memories found[/yellow]")
        console.print()
        console.print("[dim]Try:[/dim]")
        console.print("  • Different search terms")
        console.print("  • Broader query without filters")
        console.print("  • Check if memories have been rolled over (python3 rollover.py status)")
        return True

    # Display results with Rich formatting
    from rich.panel import Panel
    from rich.table import Table

    # Minimum similarity threshold - filter out irrelevant results
    MIN_SIMILARITY_THRESHOLD = 0.40  # 40% minimum relevance

    # Filter and process results
    filtered_results = []
    for result in results[:n_results]:
        document = result.get('document', '')
        distance = result.get('distance', 0)

        # Calculate similarity (ChromaDB L2 distance: 0=identical, ~2=very different)
        similarity = max(0, 1 - (distance / 2))

        # Skip empty documents and low-relevance results
        if not document or not document.strip():
            continue
        if similarity < MIN_SIMILARITY_THRESHOLD:
            continue

        result['similarity'] = similarity
        filtered_results.append(result)

    if not filtered_results:
        console.print("[yellow]No relevant memories found[/yellow]")
        console.print()
        console.print("[dim]The search found some results but none were relevant enough (>40% similarity).[/dim]")
        console.print("[dim]Try more specific search terms related to your AIPass work.[/dim]")
        return True

    for i, result in enumerate(filtered_results, 1):
        collection = result.get('collection', 'unknown')
        document = result.get('document', '')
        metadata = result.get('metadata', {})
        similarity = result.get('similarity', 0)

        # Parse collection name
        parts = collection.split('_')
        branch_name = parts[0].upper() if parts else 'UNKNOWN'
        mem_type = parts[1] if len(parts) > 1 else 'unknown'

        # Build metadata display
        meta_lines = []
        if 'timestamp' in metadata:
            meta_lines.append(f"[dim]Time:[/dim] {metadata['timestamp']}")
        if 'source' in metadata:
            meta_lines.append(f"[dim]Source:[/dim] {metadata['source']}")

        meta_text = " | ".join(meta_lines) if meta_lines else ""

        # Create panel for each result
        panel_title = f"Result {i} - {branch_name} ({mem_type}) - Similarity: {similarity:.2%}"

        panel_content = document
        if meta_text:
            panel_content += f"\n\n{meta_text}"

        console.print(Panel(
            panel_content,
            title=panel_title,
            title_align="left",
            border_style="cyan" if similarity > 0.7 else "blue" if similarity > 0.5 else "dim"
        ))

    console.print()
    logger.info(f"[search] Displayed {len(results[:n_results])} results")

    return True


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
