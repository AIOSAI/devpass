#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: chroma_subprocess.py - ChromaDB Subprocess Handler
# Date: 2025-11-27
# Version: 1.0.0
# Category: memory_bank/handlers/storage
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2025-11-27): Initial version - subprocess wrapper for ChromaDB
#
# CODE STANDARDS:
#   - Uses Memory Bank's Python 3.12 venv (ChromaDB compatible)
#   - Accepts JSON input via stdin, outputs JSON to stdout
#   - Handler pattern - pure worker, no logging
# =============================================

"""
ChromaDB Subprocess Handler

Called via subprocess from rollover module to ensure ChromaDB uses
the correct Python version (3.12 with compatible dependencies).

Input: JSON on stdin with operation and parameters
Output: JSON on stdout with result
"""

import sys
import json
from pathlib import Path

# Infrastructure setup - add home to path for MEMORY_BANK imports
sys.path.insert(0, str(Path.home()))

# This script runs with Memory Bank's Python 3.12 venv
# ChromaDB imports will work here
from MEMORY_BANK.apps.handlers.storage.chroma import store_vectors, list_all_collections, search_vectors


def main():
    """Process ChromaDB operation from stdin JSON"""
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        operation = input_data.get('operation')

        if operation == 'store_vectors':
            result = store_vectors(
                branch=input_data.get('branch'),
                memory_type=input_data.get('memory_type'),
                embeddings=input_data.get('embeddings'),
                documents=input_data.get('documents'),
                metadatas=input_data.get('metadatas'),
                db_path=input_data.get('db_path')
            )
        elif operation == 'list_collections':
            result = list_all_collections()
        elif operation == 'search_vectors':
            result = search_vectors(
                query_embedding=input_data.get('query_embedding'),
                branch=input_data.get('branch'),
                memory_type=input_data.get('memory_type'),
                n_results=input_data.get('n_results', 5),
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
