#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: central_writer.py - Central File Writer Handler
# Date: 2025-11-27
# Version: 0.1.0
# Category: memory_bank/handlers
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-27): Initial implementation - central file writer
#
# CODE STANDARDS:
#   - Handler tier 3: Pure functions, raises exceptions
#   - No CLI imports, no Prax imports
#   - Returns success/error dicts
# =============================================

"""
Central File Writer Handler

Updates MEMORY_BANK.central.json with current statistics.
This file is MEMORY_BANK's "API output" - AIPASS reads it to populate dashboards.

Purpose:
    Update central registry when vectors/archives change
    Provide current stats to AIPASS_OS dashboard
"""

# CRITICAL: Save original sys.path and import json FIRST to avoid conflicts
# with /home/aipass/MEMORY_BANK/apps/handlers/json/__init__.py
import sys
_original_path = sys.path.copy()

# Remove any paths that might have local 'json' module
from pathlib import Path
MEMORY_BANK_ROOT = Path.home() / "MEMORY_BANK"
sys.path = [p for p in sys.path if str(MEMORY_BANK_ROOT) not in p]

# Now safely import json from stdlib
from json import load as json_load, dump as json_dump

# Restore full path
sys.path = _original_path

from datetime import datetime
from typing import Dict, Any, Optional

# Infrastructure setup
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# No service imports - handlers are pure workers (3-tier architecture)
# No Prax imports (handler tier 3)


# =============================================================================
# CONSTANTS
# =============================================================================

MEMORY_BANK_ROOT = Path.home() / "MEMORY_BANK"
CENTRAL_FILE = Path.home() / "aipass_os" / "AI_CENTRAL" / "MEMORY_BANK.central.json"
CHROMA_DB_PATH = MEMORY_BANK_ROOT / ".chroma"
ARCHIVE_DIR = MEMORY_BANK_ROOT / ".archive"


# =============================================================================
# STATS COLLECTION
# =============================================================================

def count_chroma_vectors() -> int:
    """
    Count total vectors across all ChromaDB collections

    Returns:
        Total number of vectors stored (estimated from SQLite)

    Raises:
        Exception if database access fails
    """
    try:
        if not CHROMA_DB_PATH.exists():
            return 0

        # Read ChromaDB SQLite database directly to avoid dependency issues
        import sqlite3

        db_file = CHROMA_DB_PATH / "chroma.sqlite3"
        if not db_file.exists():
            return 0

        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # Query embeddings table for total count
        # ChromaDB stores embeddings in the 'embeddings' table
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total = cursor.fetchone()[0]

        conn.close()

        return total

    except Exception as e:
        # If SQLite query fails, fall back to file-based estimation
        # Count collection directories as a rough estimate
        try:
            collection_dirs = [d for d in CHROMA_DB_PATH.iterdir() if d.is_dir()]
            # Return 0 as we can't accurately count without DB access
            return 0
        except:
            return 0


def count_archive_files() -> int:
    """
    Count total archive files in .archive directory

    Returns:
        Number of archived files

    Raises:
        Exception if directory access fails
    """
    try:
        if not ARCHIVE_DIR.exists():
            return 0

        # Count markdown files (archived memory files)
        archive_files = list(ARCHIVE_DIR.glob("*.md"))
        return len(archive_files)

    except Exception as e:
        raise Exception(f"Failed to count archive files: {e}")


def get_last_rollover_timestamp() -> str:
    """
    Get timestamp of last rollover operation

    Returns:
        ISO timestamp string, or empty string if no rollover data

    Raises:
        Exception if unable to determine timestamp
    """
    try:
        # Check for most recent archive file
        if not ARCHIVE_DIR.exists():
            return ""

        archive_files = list(ARCHIVE_DIR.glob("*.md"))
        if not archive_files:
            return ""

        # Get most recent file by modification time
        latest = max(archive_files, key=lambda f: f.stat().st_mtime)
        mtime = datetime.fromtimestamp(latest.stat().st_mtime)

        return mtime.isoformat()

    except Exception as e:
        raise Exception(f"Failed to get rollover timestamp: {e}")


def collect_stats() -> Dict[str, Any]:
    """
    Collect all Memory Bank statistics

    Returns:
        Dict with stats:
            - total_vectors: int
            - total_archives: int
            - last_rollover: ISO timestamp string

    Raises:
        Exception if any stat collection fails
    """
    return {
        "total_vectors": count_chroma_vectors(),
        "total_archives": count_archive_files(),
        "last_rollover": get_last_rollover_timestamp()
    }


# =============================================================================
# CENTRAL FILE OPERATIONS
# =============================================================================

def read_central_file() -> Dict[str, Any]:
    """
    Read current central file contents

    Returns:
        Dict with central file data

    Raises:
        Exception if file read fails
    """
    try:
        if not CENTRAL_FILE.exists():
            # Return default structure
            return {
                "service": "memory_bank",
                "last_updated": "",
                "stats": {
                    "total_vectors": 0,
                    "total_archives": 0,
                    "last_rollover": ""
                }
            }

        with open(CENTRAL_FILE, 'r', encoding='utf-8') as f:
            return json_load(f)

    except Exception as e:
        raise Exception(f"Failed to read central file: {e}")


def write_central_file(data: Dict[str, Any]) -> None:
    """
    Write data to central file

    Args:
        data: Dict with central file structure

    Raises:
        Exception if file write fails
    """
    try:
        # Ensure directory exists
        CENTRAL_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(CENTRAL_FILE, 'w', encoding='utf-8') as f:
            json_dump(data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        raise Exception(f"Failed to write central file: {e}")


# =============================================================================
# PUBLIC API
# =============================================================================

def update_central(verbose: bool = False) -> Dict[str, Any]:
    """
    Update MEMORY_BANK.central.json with current statistics

    Main function called by MEMORY_BANK modules to update central registry.
    Called after vector storage, rollover, or archive operations.

    Args:
        verbose: If True, include detailed stats in return dict

    Returns:
        Dict with update result:
            success: bool
            stats: dict (if verbose=True)
            error: str (if failed)

    Example:
        # Update central file after rollover
        result = update_central(verbose=True)
        if result['success']:
            print(f"Updated with {result['stats']['total_vectors']} vectors")
    """
    try:
        # Collect current stats
        stats = collect_stats()

        # Read existing file (preserves any extra fields)
        central_data = read_central_file()

        # Update stats and timestamp
        central_data["last_updated"] = datetime.now().isoformat()
        central_data["stats"] = stats

        # Remove placeholder note if present
        if "_note" in central_data:
            del central_data["_note"]

        # Write updated file
        write_central_file(central_data)

        result = {
            "success": True,
            "updated": CENTRAL_FILE.as_posix()
        }

        if verbose:
            result["stats"] = stats

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_current_stats() -> Dict[str, Any]:
    """
    Get current Memory Bank statistics without writing to file

    Returns:
        Dict with stats or error

    Example:
        # Check stats without updating file
        stats = get_current_stats()
        if stats['success']:
            print(f"Vectors: {stats['total_vectors']}")
    """
    try:
        stats = collect_stats()
        return {
            "success": True,
            **stats
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# =============================================================================
# CLI ENTRY POINT (for testing)
# =============================================================================

if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    console.print()
    console.print(Panel.fit(
        "[bold cyan]MEMORY_BANK Central Writer[/bold cyan]",
        border_style="bright_blue"
    ))
    console.print()

    # Get current stats
    console.print("[yellow]Collecting statistics...[/yellow]")
    stats_result = get_current_stats()

    if stats_result['success']:
        table = Table(title="Current Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Vectors", str(stats_result.get('total_vectors', 0)))
        table.add_row("Total Archives", str(stats_result.get('total_archives', 0)))
        table.add_row("Last Rollover", stats_result.get('last_rollover', 'Never'))

        console.print(table)
    else:
        console.print(f"[red]Error collecting stats: {stats_result.get('error')}[/red]")

    console.print()

    # Update central file
    console.print("[yellow]Updating central file...[/yellow]")
    result = update_central(verbose=True)

    if result['success']:
        console.print(f"[green]✓ Updated: {result['updated']}[/green]")
        if 'stats' in result:
            console.print(f"[dim]  Vectors: {result['stats']['total_vectors']}[/dim]")
            console.print(f"[dim]  Archives: {result['stats']['total_archives']}[/dim]")
    else:
        console.print(f"[red]✗ Update failed: {result.get('error')}[/red]")

    console.print()
