#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: __init__.py - Central Handlers Package
# Date: 2025-11-24
# Version: 0.1.0
# Category: aipass/handlers/central
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2025-11-24): Initial package structure
#
# CODE STANDARDS:
#   - Package initialization for central aggregation handlers
# =============================================

"""
Central Handlers Package

Business logic for central aggregation operations.
Domain: Central coordination, branch aggregation, cross-branch syncing

Key module: reader.py - reads all .central.json files from AI_CENTRAL/
"""

from .reader import (
    read_all_centrals,
    read_central_file,
    get_central_path,
    list_central_files,
    AI_CENTRAL_DIR
)

__all__ = [
    'read_all_centrals',
    'read_central_file',
    'get_central_path',
    'list_central_files',
    'AI_CENTRAL_DIR'
]
