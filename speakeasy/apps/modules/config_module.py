#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: config_module.py - Configuration orchestration module
# Date: 2026-02-11
# Version: 1.1.0
# Category: speakeasy/modules
#
# CHANGELOG (Max 5 entries):
#   - v1.1.0 (2026-02-11): Refactored to thin orchestrator pattern
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
# =============================================

"""
Configuration Module - Orchestrates configuration management

Commands:
- config show [section.key] - Show current config or specific value
- config set <section.key> <value> - Set config value
- config reset - Reset to defaults
"""

import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console
from typing import List, Any, Dict, Optional

# Import handler functions
sys.path.insert(0, str(Path(__file__).parent.parent))
from handlers import config_handler


# =============================================================================
# ORCHESTRATION STATE (cache management)
# =============================================================================

_config_cache: Optional[Dict[str, Any]] = None
_config_path = Path.home() / "speakeasy" / "config.yaml"


# =============================================================================
# COMMAND HANDLER
# =============================================================================

def handle_command(command: str, args: List[str]) -> bool:
    """
    Handle configuration commands

    Args:
        command: Command name
        args: Command arguments

    Returns:
        True if command was handled
    """
    global _config_cache

    if command != "config":
        return False

    # Ensure config is loaded
    if _config_cache is None:
        try:
            _config_cache = config_handler.load_config(_config_path)
            logger.info(f"[CONFIG] Loaded configuration from {_config_path}")
        except Exception as e:
            logger.error(f"[CONFIG] Failed to load config: {e}")
            _config_cache = config_handler.get_default_config()
            logger.info("[CONFIG] Using default configuration")

    # No args = show full config
    if len(args) == 0:
        _show_config(_config_cache)
        return True

    subcommand = args[0]

    # config show [section.key]
    if subcommand == "show":
        if len(args) == 1:
            _show_config(_config_cache)
        else:
            _show_value(_config_cache, args[1])
        return True

    # config set <section.key> <value>
    elif subcommand == "set":
        if len(args) < 3:
            console.print("Usage: config set <section.key> <value>")
            return True

        if '.' not in args[1]:
            console.print(f"[red]Invalid path format:[/red] {args[1]}")
            console.print("[dim]Use format: section.key[/dim]")
            return True

        section, key = args[1].split('.', 1)
        value = config_handler.parse_value(args[2])

        # Handler sets value and validates
        success, errors = config_handler.set_value(_config_cache, section, key, value)

        if success:
            # Save to disk
            try:
                config_handler.save_config(_config_cache, _config_path)
                logger.info(f"[CONFIG] Set {section}.{key} = {value}")
                console.print(f"[green]✓[/green] Set {args[1]} = {value}")
            except Exception as e:
                logger.error(f"[CONFIG] Failed to save config: {e}")
                console.print(f"[red]✗[/red] Failed to save configuration")
        else:
            logger.error(f"[CONFIG] Validation failed: {errors}")
            console.print(f"[red]✗[/red] Failed to set {args[1]}: {', '.join(errors)}")

        return True

    # config reset
    elif subcommand == "reset":
        try:
            _config_cache = config_handler.get_default_config()
            config_handler.save_config(_config_cache, _config_path)
            logger.info("[CONFIG] Reset to default configuration")
            console.print("[green]✓[/green] Configuration reset to defaults")
        except Exception as e:
            logger.error(f"[CONFIG] Failed to reset config: {e}")
            console.print("[red]✗[/red] Failed to reset configuration")
        return True

    # config reload
    elif subcommand == "reload":
        try:
            _config_cache = config_handler.load_config(_config_path)
            logger.info("[CONFIG] Reloaded configuration from disk")
            console.print("[green]✓[/green] Configuration reloaded")
        except Exception as e:
            logger.error(f"[CONFIG] Failed to reload config: {e}")
            console.print("[red]✗[/red] Failed to reload configuration")
        return True

    else:
        console.print(f"Unknown config subcommand: {subcommand}")
        console.print("Available: show, set, reset, reload")
        return True


# =============================================================================
# CLI OUTPUT FUNCTIONS
# =============================================================================

def _show_config(config: Dict[str, Any]):
    """Show full configuration"""
    console.print("\n[bold cyan]=== Speakeasy Configuration ===[/bold cyan]\n")
    for section, values in config.items():
        console.print(f"[yellow][{section}][/yellow]")
        if isinstance(values, dict):
            for key, value in values.items():
                console.print(f"  [dim]{key}:[/dim] {value}")
        else:
            console.print(f"  {values}")
        console.print()


def _show_value(config: Dict[str, Any], path: str):
    """Show specific configuration value"""
    if '.' not in path:
        console.print(f"[red]Invalid path format:[/red] {path}")
        console.print("[dim]Use format: section.key[/dim]")
        return

    section, key = path.split('.', 1)
    value = config_handler.get_value(config, section, key)

    if value is None:
        console.print(f"[red]Not found:[/red] {path}")
    else:
        console.print(f"[cyan]{path}[/cyan] = {value}")
