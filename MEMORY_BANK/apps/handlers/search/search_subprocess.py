#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: search_subprocess.py - Search Subprocess Handler
# Date: 2025-11-27
# Version: 1.0.0
# Category: memory_bank/handlers/search
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-27): Initial version - subprocess wrapper for vector search
#
# CODE STANDARDS:
#   - Uses Memory Bank's Python 3.12 venv (ChromaDB compatible)
#   - Accepts JSON input via stdin, outputs JSON to stdout
#   - Handler pattern - pure worker, no logging
# =============================================

"""
Search Subprocess Handler

Called via subprocess to ensure search operations use the correct
Python version (3.12 with compatible dependencies).

Input: JSON on stdin with operation and parameters
Output: JSON on stdout with result
"""

import sys
import json
from pathlib import Path

# Infrastructure setup - add home to path for MEMORY_BANK imports
sys.path.insert(0, str(Path.home()))

# This script runs with Memory Bank's Python 3.12 venv
# ChromaDB and sentence-transformers imports will work here
from MEMORY_BANK.apps.handlers.search.vector_search import (
    search_collection,
    encode_query,
    list_collections,
    search_all_collections
)


def main():
    """Process search operation from stdin JSON"""
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        operation = input_data.get('operation')

        if operation == 'search':
            # Single collection search
            result = search_collection(
                query_embedding=input_data.get('query_embedding'),
                collection_name=input_data.get('collection_name'),
                n_results=input_data.get('n_results', 5),
                where=input_data.get('where'),
                db_path=input_data.get('db_path')
            )

        elif operation == 'search_all':
            # Multi-collection search
            result = search_all_collections(
                query_embedding=input_data.get('query_embedding'),
                n_results=input_data.get('n_results', 5),
                where=input_data.get('where'),
                db_path=input_data.get('db_path')
            )

        elif operation == 'encode':
            # Encode query text to embedding
            result = encode_query(
                query=input_data.get('query')
            )

        elif operation == 'list_collections':
            # List all collections
            result = list_collections(
                db_path=input_data.get('db_path')
            )

        else:
            result = {'success': False, 'error': f'Unknown operation: {operation}'}

        # Output result as JSON
        print(json.dumps(result))

    except Exception as e:
        # Output error as JSON
        print(json.dumps({'success': False, 'error': str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    main()
