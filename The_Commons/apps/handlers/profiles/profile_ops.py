#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: profile_ops.py - Profile Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/profiles
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation from module refactor (FPLAN-0356 Phase 1)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules
# =============================================

"""
Profile Operations Handler

Implementation logic for profile viewing/editing and member listing.
Moved from profile_module.py to follow thin-module architecture.
"""

import sys
from pathlib import Path
from typing import List

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

from rich.panel import Panel

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import get_db, close_db
from handlers.profiles.profile_queries import (
    get_profile,
    update_bio,
    update_status,
    update_role,
    get_all_agents_brief,
    format_time_ago,
)


# =============================================================================
# PROFILE OPERATIONS
# =============================================================================

def show_profile(args: List[str]) -> bool:
    """
    View or edit social profiles.

    Usage:
        commons profile                          - Show your profile
        commons profile <branch_name>            - Show someone's profile
        commons profile set bio "text"           - Set your bio
        commons profile set status "text"        - Set your status
        commons profile set role "text"          - Set your role
    """
    # Handle 'set' subcommand: profile set <field> "value"
    if len(args) >= 3 and args[0].lower() == "set":
        field = args[1].lower()
        value = args[2] if len(args) > 2 else ""

        valid_fields = ("bio", "status", "role")
        if field not in valid_fields:
            console.print(f"[red]Unknown field '{field}'. Must be one of: {', '.join(valid_fields)}[/red]")
            return True

        from modules.commons_identity import get_caller_branch
        caller = get_caller_branch()
        if not caller:
            console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
            return True

        branch_name = caller["name"]

        try:
            conn = get_db()
            update_fn = {"bio": update_bio, "status": update_status, "role": update_role}[field]
            success = update_fn(conn, branch_name, value)
            close_db(conn)

            if success:
                console.print(f"[green]Updated {field} for {branch_name}[/green]")
                logger.info(f"[commons] {branch_name} updated profile {field}")
            else:
                console.print(f"[red]Agent '{branch_name}' not found[/red]")

        except Exception as e:
            logger.error(f"[commons] Profile update failed: {e}")
            console.print(f"[red]Error updating profile: {e}[/red]")

        return True

    # Determine which branch to show
    if args:
        target_branch = args[0].upper()
    else:
        from modules.commons_identity import get_caller_branch
        caller = get_caller_branch()
        if not caller:
            console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
            return True
        target_branch = caller["name"]

    # Fetch and display profile
    try:
        conn = get_db()
        profile = get_profile(conn, target_branch)
        close_db(conn)

        if not profile:
            console.print(f"[red]Agent '{target_branch}' not found[/red]")
            return True

        # Display profile card
        branch_name = profile["branch_name"]
        description = profile.get("description", "")
        display_name = profile.get("display_name", branch_name)
        bio = profile.get("bio", "") or ""
        status_val = profile.get("status", "") or ""
        role_val = profile.get("role", "") or ""
        karma = profile.get("karma", 0)
        post_count = profile.get("post_count", 0)
        comment_count = profile.get("comment_count", 0)
        joined_at = profile.get("joined_at", "")
        last_active = profile.get("last_active", "")

        title_line = f"{branch_name} - {description}" if description else f"{branch_name} - {display_name}"

        lines = [""]
        lines.append(f"  Bio: {bio}" if bio else "  Bio: [dim]not set[/dim]")
        lines.append(f"  Status: {status_val}" if status_val else "  Status: [dim]not set[/dim]")
        lines.append(f"  Role: {role_val}" if role_val else "  Role: [dim]not set[/dim]")
        lines.append("")

        joined_display = joined_at[:10] if joined_at else "unknown"
        last_active_display = format_time_ago(last_active) if last_active else "never"

        lines.append(f"  Posts: {post_count}  Comments: {comment_count}  Karma: {karma}")
        lines.append(f"  Joined: {joined_display}  Last active: {last_active_display}")
        lines.append("")

        console.print()
        console.print(Panel("\n".join(lines), title=f"  {title_line}  ", border_style="cyan"))
        console.print()

    except Exception as e:
        logger.error(f"[commons] Profile fetch failed: {e}")
        console.print(f"[red]Error loading profile: {e}[/red]")

    return True


def list_members(args: List[str]) -> bool:
    """
    List all agents with brief profile info.

    Usage: commons who
    """
    try:
        conn = get_db()
        agents = get_all_agents_brief(conn)
        close_db(conn)

        if not agents:
            console.print("[dim]No agents registered.[/dim]")
            return True

        console.print()
        console.print("[bold]Who's in The Commons:[/bold]")
        console.print()

        for agent in agents:
            name = agent["branch_name"]
            status_text = agent.get("status", "") or ""
            role_text = agent.get("role", "") or ""
            karma_val = agent.get("karma", 0)

            status_display = f"[{status_text}]" if status_text else "[dim]no status[/dim]"
            if not role_text:
                role_text = "[dim]--[/dim]"

            console.print(f"  {name:<14}{status_display:<30}{role_text:<25}karma: {karma_val}")

        console.print()

    except Exception as e:
        logger.error(f"[commons] Who listing failed: {e}")
        console.print(f"[red]Error listing agents: {e}[/red]")

    return True
