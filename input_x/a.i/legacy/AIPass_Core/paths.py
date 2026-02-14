"""Path utilities for the AIPass ecosystem.

This module exposes common repository directories so other modules
can reliably locate resources without repeating path logic.
"""
from pathlib import Path

# Resolve the AIPass_Core directory
ROOT = Path(__file__).resolve()
while ROOT.name != "AIPass_Core" and ROOT != ROOT.parent:
    ROOT = ROOT.parent

# Navigate up to the AIPass-Ecosystem root
ECOSYSTEM_ROOT = ROOT.parent.parent.parent  # legacy -> a.i -> AIPass-Ecosystem
KEYS_DIR = ECOSYSTEM_ROOT  # Now points to root where .env file is located
