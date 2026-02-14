"""
Bulletin Board Handlers

Business logic for bulletin board operations.
Organized by domain: storage, CRUD, propagation.
"""

from .storage import load_bulletins, save_bulletins
from .crud import create_bulletin, list_bulletins, acknowledge_bulletin
from .propagation import propagate_to_branches

__all__ = [
    "load_bulletins",
    "save_bulletins",
    "create_bulletin",
    "list_bulletins",
    "acknowledge_bulletin",
    "propagate_to_branches",
]
