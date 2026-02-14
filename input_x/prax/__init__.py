"""
Prax System Package

Collection of system utilities and process management tools for AIPass-Ecosystem.
"""

__version__ = "1.0.0"
__author__ = "AIPass-Ecosystem"

# Make commonly used modules easily importable
from . import prax_logger

# Note: prax_on_off removed from auto-import to prevent unnecessary startup
# Import directly when needed: from prax.prax_on_off import load_registry

__all__ = ['prax_logger']
