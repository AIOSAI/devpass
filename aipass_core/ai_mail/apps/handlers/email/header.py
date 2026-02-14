#!/home/aipass/.venv/bin/python3

from pathlib import Path
import sys

AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# ===================AIPASS====================
# META DATA HEADER
# Name: header.py - Email Header Handler
# Date: 2026-02-04
# Version: 1.0.0
# Category: ai_mail/handlers/email
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-04): Created - dispatch header for critical reminders
#
# CODE STANDARDS:
#   - Handler independence: NO cross-domain imports
#   - Can import Prax modules (service providers)
#   - Pure business logic only
# =============================================

"""
Email Header Handler

Generates and prepends headers to outgoing emails.
Critical dispatch header ensures agents see memory update reminder FIRST.
Independent handler - no module dependencies.
"""

# Header for dispatch emails - agents see this FIRST before the task
DISPATCH_HEADER = """⚡ DISPATCH TASK - READ THIS FIRST ⚡

BEFORE YOU REPLY, YOU MUST:
1. ✅ Complete the task below
2. ✅ UPDATE YOUR MEMORIES (.local.json) - this is NOT optional
3. ✅ Then reply with your completion summary

Your memories are your presence. Skip the update = you never existed.

---
"""


def get_dispatch_header() -> str:
    """
    Get the dispatch email header.

    Returns:
        Dispatch header string for dispatch emails
    """
    return DISPATCH_HEADER


def prepend_dispatch_header(message: str) -> str:
    """
    Prepend dispatch header to email message.

    Args:
        message: Original email message body

    Returns:
        Message with dispatch header prepended
    """
    return get_dispatch_header() + message


if __name__ == "__main__":
    print("\n" + "="*70)
    print("EMAIL HEADER HANDLER")
    print("="*70)
    print("\nPURPOSE:")
    print("  Generates header for dispatch emails (critical reminders)")
    print()
    print("FUNCTIONS PROVIDED:")
    print("  - get_dispatch_header() -> str")
    print("  - prepend_dispatch_header(message) -> str")
    print()
    print("HEADER CONTENT:")
    print(DISPATCH_HEADER)
    print()
    print("HANDLER CHARACTERISTICS:")
    print("  ✓ Independent - no module dependencies")
    print("  ✓ Can import Prax (service provider)")
    print("  ✓ Pure business logic")
    print("  ✗ CANNOT import parent modules")
    print()
    print("USAGE FROM MODULES:")
    print("  from ai_mail.apps.handlers.email.header import prepend_dispatch_header")
    print()
    print("="*70 + "\n")
