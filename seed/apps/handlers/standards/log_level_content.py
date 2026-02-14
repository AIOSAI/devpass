#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: log_level_content.py - Log Level Hygiene Standards Content
# Date: 2026-02-13
# Version: 1.0.0
# Category: seed/standards/content
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-13): Initial content - log level hygiene standard
#
# CODE STANDARDS:
#   - Content handler provides Rich-formatted text for display
# =============================================

"""
Log Level Hygiene Standards Content

Provides Rich-formatted reference text for the log level hygiene standard.
"""


def get_log_level_standards() -> str:
    """Return Rich-formatted log level hygiene standards text"""
    return """[bold white]LOG LEVEL HYGIENE STANDARD[/bold white]

[yellow]PURPOSE:[/yellow]
  Ensure ERROR level is reserved for real system failures.
  User input errors must use WARNING level.
  This is critical for Medic v2 push-based error detection accuracy.

[yellow]THE RULES:[/yellow]

  [bold red]ERROR[/bold red] = System failures ONLY
    - Crashes, unhandled exceptions
    - Timeouts, connection failures
    - Import failures, missing dependencies
    - File I/O errors (disk full, permission denied)
    - Internal state corruption

  [bold yellow]WARNING[/bold yellow] = User input errors
    - Unknown command, unrecognized action
    - Invalid arguments, bad syntax
    - Missing required arguments
    - Typos in user input
    - Command routing failures (no module handled)

  [bold cyan]INFO[/bold cyan] = Normal operations
    - Successful completions
    - Module discoveries
    - Configuration loaded
    - Service started/stopped

[yellow]EXAMPLES:[/yellow]

  [red]BAD:[/red]
    logger.error(f"Unknown command: {command}")
    logger.error(f"No module handled command: {args.command}")
    logger.error(f"Invalid argument: {arg}")

  [green]GOOD:[/green]
    logger.warning(f"Unknown command: {command}")
    logger.warning(f"No module handled command: {args.command}")
    logger.warning(f"Invalid argument: {arg}")
    logger.error(f"Failed to connect to database: {e}")
    logger.error(f"Import failed: {e}")

[yellow]WHY THIS MATTERS:[/yellow]
  Medic v2 monitors ERROR-level log entries to detect real system issues.
  If user typos trigger ERROR, Medic sees noise instead of signal.
  Clean log levels = accurate error detection = healthier system."""
