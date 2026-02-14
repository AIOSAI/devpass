#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: telegram_bridge.py - Telegram Bridge Module
# Date: 2026-02-03
# Version: 1.4.0
# Category: api/modules
# CODE STANDARDS: Seed v1.0.0
#
# CHANGELOG (Max 5 entries):
#   - v1.4.0 (2026-02-13): Remove 'start' from drone routing - blocking call causes 30s timeout
#   - v1.3.0 (2026-02-13): Add startup health check - verify Telegram API connection before polling
#   - v1.2.0 (2026-02-10): Handle start/status only, pass stop/logs to telegram_service.py
#   - v1.1.0 (2026-02-10): Disable drone routing - only telegram_service.py handles telegram commands
#   - v1.0.0 (2026-02-03): Initial module - Telegram bridge entry point
# =============================================

"""
Telegram Bridge Module

Orchestrates Telegram bot operations:
- Start the bridge service
- Check status
- Validate configuration
"""

import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from typing import List
from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console, header, success, error
from api.apps.handlers.telegram import config
from api.apps.handlers.telegram import bridge


def print_introspection() -> None:
    """Show module introspection - connected handlers and capabilities"""
    console.print()
    header("Telegram Bridge Module Introspection")
    console.print()

    console.print("[cyan]Purpose:[/cyan] Telegram bot bridge to AIPass desktop")
    console.print()

    console.print("[cyan]Connected Handlers:[/cyan]")
    console.print("  • api.apps.handlers.telegram.config")
    console.print("  • api.apps.handlers.telegram.bridge")
    console.print()

    console.print("[cyan]Available Workflows:[/cyan]")
    console.print("  • start() - Start the bridge in polling mode")
    console.print("  • status() - Check bridge configuration status")
    console.print()

    console.print("[cyan]Bot Info:[/cyan]")
    bot_username = config.get_bot_username()
    console.print(f"  • Username: @{bot_username}")
    console.print()


def print_help() -> None:
    """Print module help with argparse"""
    import argparse

    parser = argparse.ArgumentParser(
        prog="python3 telegram.py",
        description="Telegram Bridge - Connect Telegram to AIPass",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  start            - Start the Telegram bridge (long-polling)
  status           - Check configuration status

USAGE:
  python3 telegram.py start
  python3 telegram.py status

EXAMPLES:
  # Start the bridge (blocks until Ctrl+C)
  python3 telegram.py start

  # Check configuration
  python3 telegram.py status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # start command
    subparsers.add_parser("start", help="Start the Telegram bridge")

    # status command
    subparsers.add_parser("status", help="Check configuration status")

    console.print(parser.format_help())


def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle Telegram bridge commands.

    Only handles 'status' directly. Start/stop/logs return False
    so telegram_service.py handles them via systemd (non-blocking).

    Args:
        command: Command name
        args: Command arguments

    Returns:
        True if command was handled, False to pass through
    """
    if not args:
        return False

    subcommand = args[0] if args else ""

    if command == "telegram" and subcommand == "status":
        status()
        return True

    return False


def start() -> None:
    """Start the Telegram bridge in polling mode"""
    header("Telegram Bridge")
    console.print()

    # Validate config via handler
    if not config.validate_config():
        error("Invalid configuration. Check ~/.aipass/telegram_config.json")
        return

    bot_username = config.get_bot_username()
    success(f"Starting @{bot_username}...")
    console.print()

    # Delegate to handler (blocks until Ctrl+C)
    bridge.run_polling()


def status() -> None:
    """Check Telegram bridge configuration status"""
    header("Telegram Bridge Status")
    console.print()

    # Delegate validation to handler
    if not config.validate_config():
        error("Configuration: Invalid or missing")
        console.print()
        console.print("[dim]Expected config at: ~/.aipass/telegram_config.json[/dim]")
        console.print("[dim]Format: {\"telegram_bot_token\": \"...\", \"telegram_bot_username\": \"...\"}[/dim]")
        return

    success("Configuration: Valid")

    # Get info from handler
    bot_username = config.get_bot_username()
    console.print()
    console.print(f"[cyan]Bot Username:[/cyan] @{bot_username}")
    console.print()

    success("Ready to start")


# =============================================
# PUBLIC API - Re-export for cross-branch access
# =============================================

def run_bridge() -> None:
    """
    Public API: Start the Telegram bridge

    This can be called from other branches to start the bridge service.
    """
    bridge.run_polling()


if __name__ == "__main__":
    """Standalone execution mode"""
    args = sys.argv[1:]

    # Show introspection when run without arguments
    if len(args) == 0:
        print_introspection()
        sys.exit(0)

    # Show help for explicit help flags
    if args[0] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)

    # Execute command directly (standalone mode, not drone-routed)
    command = args[0]

    if command == "start":
        start()
        sys.exit(0)
    elif command == "status":
        status()
        sys.exit(0)
    else:
        console.print()
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print()
        console.print("Run [dim]python3 telegram.py --help[/dim] for available commands")
        console.print()
        sys.exit(1)
