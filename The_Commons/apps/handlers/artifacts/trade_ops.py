#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: trade_ops.py - Trading & Ephemeral Item Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/artifacts
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 5)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules/entry point
# =============================================

"""
Trading & Ephemeral Item Operations Handler

Implementation logic for artifact trading, gifting, ephemeral item drops,
item finding, expired item sweeping, and event artifact minting.
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

from rich.panel import Panel
from rich.table import Table

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import get_db, close_db

# Constants
BRANCH_REGISTRY_PATH = Path.home() / "BRANCH_REGISTRY.json"

RARITY_COLORS = {
    "common": "white",
    "uncommon": "green",
    "rare": "blue",
    "legendary": "yellow",
    "unique": "magenta",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_branch_artifacts_path(branch_name: str) -> Optional[Path]:
    """
    Look up a branch's path from BRANCH_REGISTRY and return its artifacts/ folder.

    Args:
        branch_name: Branch name to look up

    Returns:
        Path to the branch's artifacts/ folder, or None if not found
    """
    if not BRANCH_REGISTRY_PATH.exists():
        return None

    try:
        registry = json.loads(BRANCH_REGISTRY_PATH.read_text(encoding="utf-8"))
        for branch in registry.get("branches", []):
            if branch.get("name") == branch_name:
                branch_path = Path(branch["path"])
                return branch_path / "artifacts"
        return None
    except Exception:
        return None


def _find_artifact_file(owner: str, artifact_id: int) -> Optional[Path]:
    """
    Find the physical artifact JSON file for a given owner and artifact ID.

    Args:
        owner: Branch name of the current owner
        artifact_id: Artifact ID

    Returns:
        Path to the artifact file, or None if not found
    """
    artifacts_dir = _get_branch_artifacts_path(owner)
    if not artifacts_dir or not artifacts_dir.exists():
        return None

    # Look for files matching the artifact ID pattern
    for f in artifacts_dir.glob(f"artifact_{artifact_id}_*.json"):
        return f

    return None


def _move_artifact_file(from_owner: str, to_owner: str, artifact_id: int, artifact_data: dict) -> bool:
    """
    Move a physical artifact JSON file from one branch's artifacts/ to another's.
    Updates the owner field in the JSON before saving.

    Args:
        from_owner: Current owner branch name
        to_owner: New owner branch name
        artifact_id: Artifact ID
        artifact_data: Updated artifact data dict

    Returns:
        True if moved successfully, False otherwise
    """
    # Find the source file
    source_file = _find_artifact_file(from_owner, artifact_id)

    # Ensure destination directory exists
    dest_dir = _get_branch_artifacts_path(to_owner)
    if not dest_dir:
        logger.warning(f"[commons] Could not find artifacts path for {to_owner}")
        return False

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Build destination filename
        safe_name = artifact_data.get("name", "artifact").lower().replace(" ", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
        dest_filename = f"artifact_{artifact_id}_{safe_name}.json"
        dest_file = dest_dir / dest_filename

        # Update owner in artifact data
        artifact_data["owner"] = to_owner

        # Write new file at destination
        dest_file.write_text(
            json.dumps(artifact_data, indent=2, default=str),
            encoding="utf-8",
        )

        # Remove source file if it existed
        if source_file and source_file.exists():
            source_file.unlink()
            logger.info(f"[commons] Artifact file moved: {source_file} -> {dest_file}")
        else:
            logger.info(f"[commons] Artifact file created at destination: {dest_file}")

        return True

    except Exception as e:
        logger.error(f"[commons] Failed to move artifact file: {e}")
        return False


def _save_artifact_file(artifact_data: dict, owner: str) -> bool:
    """
    Save a physical JSON file of the artifact to the owner's artifacts/ folder.

    Args:
        artifact_data: Dict with artifact fields
        owner: Branch name of the owner

    Returns:
        True if saved successfully, False otherwise
    """
    artifacts_dir = _get_branch_artifacts_path(owner)
    if not artifacts_dir:
        logger.warning(f"[commons] Could not find artifacts path for {owner}")
        return False

    try:
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        artifact_id = artifact_data.get("id", 0)
        safe_name = artifact_data.get("name", "artifact").lower().replace(" ", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
        filename = f"artifact_{artifact_id}_{safe_name}.json"

        file_path = artifacts_dir / filename
        file_path.write_text(
            json.dumps(artifact_data, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info(f"[commons] Artifact file saved: {file_path}")
        return True

    except Exception as e:
        logger.error(f"[commons] Failed to save artifact file for {owner}: {e}")
        return False


def _resolve_branch_name(mention: str) -> Optional[str]:
    """
    Resolve a @mention to a branch name. Strips the @ prefix and uppercases.

    Args:
        mention: A string like '@seed' or 'SEED'

    Returns:
        Uppercased branch name, or None if not found in registry
    """
    name = mention.lstrip("@").upper()

    if not BRANCH_REGISTRY_PATH.exists():
        return None

    try:
        registry = json.loads(BRANCH_REGISTRY_PATH.read_text(encoding="utf-8"))
        for branch in registry.get("branches", []):
            if branch.get("name") == name:
                return name
        return None
    except Exception:
        return None


def _now_utc() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# =============================================================================
# SWEEP EXPIRED ITEMS
# =============================================================================

def sweep_expired() -> int:
    """
    Sweep-on-access pattern: delete artifacts where expires_at < now.
    Creates history entries for each expired artifact.

    Returns:
        Number of artifacts swept
    """
    try:
        conn = get_db()
        now = _now_utc()

        # Find expired artifacts
        expired = conn.execute(
            "SELECT id, name, owner FROM artifacts WHERE expires_at IS NOT NULL AND expires_at < ?",
            (now,),
        ).fetchall()

        if not expired:
            close_db(conn)
            return 0

        count = 0
        for row in expired:
            artifact_id = row["id"]
            name = row["name"]
            owner = row["owner"]

            # Create history entry
            conn.execute(
                "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
                "VALUES (?, 'expired', ?, NULL, ?)",
                (artifact_id, owner, f"Ephemeral item '{name}' expired"),
            )

            # Remove physical file if it exists
            artifact_file = _find_artifact_file(owner, artifact_id)
            if artifact_file and artifact_file.exists():
                artifact_file.unlink()

            # Delete the artifact record
            conn.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
            count += 1

        conn.commit()
        close_db(conn)

        if count > 0:
            logger.info(f"[commons] Swept {count} expired artifact(s)")

        return count

    except Exception as e:
        logger.error(f"[commons] Sweep expired failed: {e}")
        return 0


# =============================================================================
# GIFT ARTIFACT
# =============================================================================

def gift_artifact(args: List[str]) -> bool:
    """
    Gift an artifact to another branch.

    Usage: drone commons gift <artifact_id> @branch
    """
    if len(args) < 2:
        console.print("[red]Usage: commons gift <artifact_id> @branch[/red]")
        console.print("[dim]Example: commons gift 5 @SEED[/dim]")
        return True

    # Parse artifact ID
    try:
        artifact_id = int(args[0])
    except ValueError:
        console.print("[red]Artifact ID must be a number[/red]")
        return True

    # Resolve recipient branch
    recipient = _resolve_branch_name(args[1])
    if not recipient:
        console.print(f"[red]Branch '{args[1]}' not found in BRANCH_REGISTRY[/red]")
        return True

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    sender = caller["name"]

    # Cannot gift to yourself
    if sender == recipient:
        console.print("[red]You cannot gift an artifact to yourself[/red]")
        return True

    try:
        conn = get_db()

        # Get the artifact
        row = conn.execute(
            "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
        ).fetchone()

        if not row:
            close_db(conn)
            console.print(f"[red]Artifact {artifact_id} not found[/red]")
            return True

        artifact = dict(row)

        # Verify ownership
        if artifact["owner"] != sender:
            close_db(conn)
            console.print(f"[red]You don't own artifact {artifact_id}. Only the owner can gift it.[/red]")
            return True

        old_owner = artifact["owner"]

        # Update ownership in database
        conn.execute(
            "UPDATE artifacts SET owner = ? WHERE id = ?",
            (recipient, artifact_id),
        )

        # Create history entry
        conn.execute(
            "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
            "VALUES (?, 'gifted', ?, ?, ?)",
            (artifact_id, old_owner, recipient, f"Gifted '{artifact['name']}' from {old_owner} to {recipient}"),
        )

        conn.commit()

        # Move physical file
        artifact["owner"] = recipient
        _move_artifact_file(old_owner, recipient, artifact_id, artifact)

        close_db(conn)

        # Rich output
        rarity_color = RARITY_COLORS.get(artifact["rarity"], "white")
        console.print()
        console.print(Panel(
            f"[bold]{old_owner}[/bold] gifted [{rarity_color}]{artifact['name']}[/{rarity_color}] "
            f"([dim]{artifact['rarity']} {artifact['type']}[/dim]) to [bold]{recipient}[/bold]\n\n"
            f"[dim]Artifact ID: {artifact_id}[/dim]\n"
            f"[dim]New owner: {recipient}[/dim]",
            title="Gift Sent",
            border_style="green",
        ))
        console.print()

        logger.info(f"[commons] Artifact {artifact_id} gifted: {old_owner} -> {recipient}")

    except Exception as e:
        logger.error(f"[commons] Gift artifact failed: {e}")
        console.print(f"[red]Failed to gift artifact: {e}[/red]")

    return True


# =============================================================================
# TRADE ARTIFACTS
# =============================================================================

def trade_artifact(args: List[str]) -> bool:
    """
    Trade artifacts between two branches (mutual exchange).

    Usage: drone commons trade <your_artifact_id> <their_artifact_id> @branch
    Trust-based: no confirmation required — gift economy.
    """
    if len(args) < 3:
        console.print("[red]Usage: commons trade <your_artifact_id> <their_artifact_id> @branch[/red]")
        console.print("[dim]Example: commons trade 5 12 @FLOW[/dim]")
        return True

    # Parse artifact IDs
    try:
        your_id = int(args[0])
        their_id = int(args[1])
    except ValueError:
        console.print("[red]Artifact IDs must be numbers[/red]")
        return True

    # Resolve partner branch
    partner = _resolve_branch_name(args[2])
    if not partner:
        console.print(f"[red]Branch '{args[2]}' not found in BRANCH_REGISTRY[/red]")
        return True

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    sender = caller["name"]

    if sender == partner:
        console.print("[red]You cannot trade with yourself[/red]")
        return True

    try:
        conn = get_db()

        # Get both artifacts
        your_artifact = conn.execute(
            "SELECT * FROM artifacts WHERE id = ?", (your_id,)
        ).fetchone()
        their_artifact = conn.execute(
            "SELECT * FROM artifacts WHERE id = ?", (their_id,)
        ).fetchone()

        if not your_artifact:
            close_db(conn)
            console.print(f"[red]Artifact {your_id} not found[/red]")
            return True

        if not their_artifact:
            close_db(conn)
            console.print(f"[red]Artifact {their_id} not found[/red]")
            return True

        your_artifact = dict(your_artifact)
        their_artifact = dict(their_artifact)

        # Verify ownership
        if your_artifact["owner"] != sender:
            close_db(conn)
            console.print(f"[red]You don't own artifact {your_id}[/red]")
            return True

        if their_artifact["owner"] != partner:
            close_db(conn)
            console.print(f"[red]{partner} doesn't own artifact {their_id}[/red]")
            return True

        # Swap ownership in database
        conn.execute(
            "UPDATE artifacts SET owner = ? WHERE id = ?",
            (partner, your_id),
        )
        conn.execute(
            "UPDATE artifacts SET owner = ? WHERE id = ?",
            (sender, their_id),
        )

        # Create history entries for both
        conn.execute(
            "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
            "VALUES (?, 'traded', ?, ?, ?)",
            (your_id, sender, partner, f"Traded '{your_artifact['name']}' to {partner} for '{their_artifact['name']}'"),
        )
        conn.execute(
            "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
            "VALUES (?, 'traded', ?, ?, ?)",
            (their_id, partner, sender, f"Traded '{their_artifact['name']}' to {sender} for '{your_artifact['name']}'"),
        )

        conn.commit()

        # Move physical files
        your_artifact["owner"] = partner
        their_artifact["owner"] = sender
        _move_artifact_file(sender, partner, your_id, your_artifact)
        _move_artifact_file(partner, sender, their_id, their_artifact)

        close_db(conn)

        # Rich output
        your_rarity_color = RARITY_COLORS.get(your_artifact["rarity"], "white")
        their_rarity_color = RARITY_COLORS.get(their_artifact["rarity"], "white")

        console.print()
        console.print(Panel(
            f"[bold]{sender}[/bold] traded [{your_rarity_color}]{your_artifact['name']}[/{your_rarity_color}] "
            f"([dim]{your_artifact['rarity']}[/dim])\n"
            f"  for\n"
            f"[bold]{partner}[/bold]'s [{their_rarity_color}]{their_artifact['name']}[/{their_rarity_color}] "
            f"([dim]{their_artifact['rarity']}[/dim])\n\n"
            f"[dim]Both artifacts have swapped owners.[/dim]",
            title="Trade Complete",
            border_style="cyan",
        ))
        console.print()

        logger.info(f"[commons] Trade: {sender}(#{your_id}) <-> {partner}(#{their_id})")

    except Exception as e:
        logger.error(f"[commons] Trade artifact failed: {e}")
        console.print(f"[red]Failed to trade artifacts: {e}[/red]")

    return True


# =============================================================================
# DROP EPHEMERAL ITEM
# =============================================================================

def drop_item(args: List[str]) -> bool:
    """
    Drop an ephemeral item in a room for anyone to find.

    Usage: drone commons drop "name" "description" <room> [--expires 5]
    Default expiry: 5 minutes.
    """
    if len(args) < 3:
        console.print("[red]Usage: commons drop \"name\" \"description\" <room> [--expires 5][/red]")
        console.print("[dim]Creates an ephemeral item that expires after N minutes (default 5).[/dim]")
        return True

    name = args[0]
    description = args[1]
    room = args[2]

    # Parse --expires flag
    expires_minutes = 5
    remaining = args[3:]
    i = 0
    while i < len(remaining):
        if remaining[i] == "--expires" and i + 1 < len(remaining):
            try:
                expires_minutes = int(remaining[i + 1])
                if expires_minutes < 1:
                    expires_minutes = 1
                elif expires_minutes > 1440:  # Max 24 hours
                    expires_minutes = 1440
            except ValueError:
                console.print("[red]--expires must be a number (minutes)[/red]")
                return True
            i += 2
        else:
            i += 1

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    creator = caller["name"]

    # Calculate expiry time
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=expires_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        conn = get_db()

        # Verify room exists
        room_row = conn.execute(
            "SELECT name FROM rooms WHERE name = ?", (room,)
        ).fetchone()
        if not room_row:
            close_db(conn)
            console.print(f"[red]Room '{room}' does not exist[/red]")
            return True

        cursor = conn.execute(
            "INSERT INTO artifacts (name, type, creator, owner, rarity, description, room_found, expires_at) "
            "VALUES (?, 'found', ?, ?, 'common', ?, ?, ?)",
            (name, creator, creator, description, room, expires_at),
        )
        artifact_id = cursor.lastrowid

        # Create history entry
        conn.execute(
            "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
            "VALUES (?, 'created', ?, NULL, ?)",
            (artifact_id, creator, f"Dropped ephemeral item '{name}' in r/{room} (expires in {expires_minutes}m)"),
        )

        conn.commit()

        # Save physical file (to dropper's artifacts temporarily)
        artifact_data = {
            "id": artifact_id,
            "name": name,
            "type": "found",
            "creator": creator,
            "owner": creator,
            "rarity": "common",
            "description": description,
            "room_found": room,
            "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "expires_at": expires_at,
        }
        _save_artifact_file(artifact_data, creator)

        close_db(conn)

        console.print()
        console.print(Panel(
            f"[bold]{name}[/bold] dropped in [cyan]r/{room}[/cyan]\n\n"
            f"[dim]Description:[/dim] {description}\n"
            f"[dim]Artifact ID:[/dim] {artifact_id}\n"
            f"[dim]Expires in:[/dim] {expires_minutes} minute(s)\n"
            f"[dim]Expires at:[/dim] {expires_at}\n\n"
            f"[yellow]Anyone can pick it up with:[/yellow] commons find {artifact_id}",
            title="Item Dropped",
            border_style="yellow",
        ))
        console.print()

        logger.info(f"[commons] Ephemeral item {artifact_id} dropped by {creator} in r/{room} (expires {expires_at})")

    except Exception as e:
        logger.error(f"[commons] Drop item failed: {e}")
        console.print(f"[red]Failed to drop item: {e}[/red]")

    return True


# =============================================================================
# FIND (PICK UP) EPHEMERAL ITEM
# =============================================================================

def find_item(args: List[str]) -> bool:
    """
    Pick up an ephemeral item before it expires.

    Usage: drone commons find <artifact_id>
    """
    if not args:
        console.print("[red]Usage: commons find <artifact_id>[/red]")
        console.print("[dim]Pick up an ephemeral item before it expires.[/dim]")
        return True

    try:
        artifact_id = int(args[0])
    except ValueError:
        console.print("[red]Artifact ID must be a number[/red]")
        return True

    # Sweep expired items first
    sweep_expired()

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    finder = caller["name"]

    try:
        conn = get_db()

        # Get the artifact
        row = conn.execute(
            "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
        ).fetchone()

        if not row:
            close_db(conn)
            console.print(f"[red]Artifact {artifact_id} not found (it may have expired)[/red]")
            return True

        artifact = dict(row)

        # Must be a 'found' type (ephemeral)
        if artifact["type"] != "found":
            close_db(conn)
            console.print(f"[red]Artifact {artifact_id} is not an ephemeral item (type: {artifact['type']})[/red]")
            return True

        # Check expiry
        if artifact["expires_at"]:
            now = datetime.now(timezone.utc)
            expires_dt = datetime.strptime(artifact["expires_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if now > expires_dt:
                # Clean it up
                conn.execute(
                    "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
                    "VALUES (?, 'expired', ?, NULL, ?)",
                    (artifact_id, artifact["owner"], f"Ephemeral item '{artifact['name']}' expired"),
                )
                conn.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
                conn.commit()
                close_db(conn)
                console.print(f"[red]Artifact {artifact_id} has expired and is no longer available[/red]")
                return True

        old_owner = artifact["owner"]

        # Transfer ownership to finder
        conn.execute(
            "UPDATE artifacts SET owner = ?, expires_at = NULL WHERE id = ?",
            (finder, artifact_id),
        )

        # Create history entry
        conn.execute(
            "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
            "VALUES (?, 'found', ?, ?, ?)",
            (artifact_id, old_owner, finder, f"Found by {finder} in r/{artifact['room_found'] or 'unknown'}"),
        )

        conn.commit()

        # Move physical file
        artifact["owner"] = finder
        artifact["expires_at"] = None
        _move_artifact_file(old_owner, finder, artifact_id, artifact)

        close_db(conn)

        rarity_color = RARITY_COLORS.get(artifact["rarity"], "white")
        console.print()
        console.print(Panel(
            f"[bold]{finder}[/bold] found [{rarity_color}]{artifact['name']}[/{rarity_color}]!\n\n"
            f"[dim]Description:[/dim] {artifact['description']}\n"
            f"[dim]Found in:[/dim] r/{artifact['room_found'] or 'unknown'}\n"
            f"[dim]Artifact ID:[/dim] {artifact_id}\n"
            f"[dim]Originally dropped by:[/dim] {artifact['creator']}\n\n"
            f"[green]This item is now yours permanently![/green]",
            title="Item Found!",
            border_style="yellow",
        ))
        console.print()

        logger.info(f"[commons] Artifact {artifact_id} found by {finder} (was dropped by {artifact['creator']})")

    except Exception as e:
        logger.error(f"[commons] Find item failed: {e}")
        console.print(f"[red]Failed to find item: {e}[/red]")

    return True


# =============================================================================
# MINT EVENT ARTIFACT
# =============================================================================

def mint_event_artifact(args: List[str]) -> bool:
    """
    Mint proof-of-attendance artifacts for an event.

    Usage: drone commons mint "Event Name" @branch1 @branch2 @branch3
    Creates one artifact per named branch with type='event', rarity='rare'.
    Creator: THE_COMMONS (system-minted). Permanent (no expiry).
    """
    if len(args) < 2:
        console.print("[red]Usage: commons mint \"Event Name\" @branch1 @branch2 ...[/red]")
        console.print("[dim]Mints a proof-of-attendance artifact for each named branch.[/dim]")
        return True

    event_name = args[0]
    mentions = args[1:]

    # Resolve all branch names
    branches = []
    for mention in mentions:
        branch = _resolve_branch_name(mention)
        if branch:
            branches.append(branch)
        else:
            console.print(f"[yellow]Warning: Branch '{mention}' not found, skipping[/yellow]")

    if not branches:
        console.print("[red]No valid branches found. Provide at least one @branch.[/red]")
        return True

    # Deduplicate
    branches = list(dict.fromkeys(branches))

    try:
        conn = get_db()

        # Ensure THE_COMMONS agent exists
        conn.execute(
            "INSERT OR IGNORE INTO agents (branch_name, display_name, description) "
            "VALUES (?, ?, ?)",
            ("THE_COMMONS", "The Commons", "The Commons event host"),
        )

        minted = []
        now_str = _now_utc()

        for branch in branches:
            description = f"Proof of attendance: {event_name}"

            cursor = conn.execute(
                "INSERT INTO artifacts (name, type, creator, owner, rarity, description, metadata) "
                "VALUES (?, 'event', 'THE_COMMONS', ?, 'rare', ?, ?)",
                (
                    f"{event_name} - Attendee Badge",
                    branch,
                    description,
                    json.dumps({"event": event_name, "attendee": branch}),
                ),
            )
            artifact_id = cursor.lastrowid

            # Create history entry
            conn.execute(
                "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
                "VALUES (?, 'created', 'THE_COMMONS', ?, ?)",
                (artifact_id, branch, f"Event badge minted for '{event_name}'"),
            )

            # Save physical file
            artifact_data = {
                "id": artifact_id,
                "name": f"{event_name} - Attendee Badge",
                "type": "event",
                "creator": "THE_COMMONS",
                "owner": branch,
                "rarity": "rare",
                "description": description,
                "metadata": {"event": event_name, "attendee": branch},
                "created_at": now_str,
            }
            _save_artifact_file(artifact_data, branch)

            minted.append((branch, artifact_id))

        conn.commit()
        close_db(conn)

        # Rich output
        console.print()
        lines = [f"[bold]Event:[/bold] {event_name}\n"]
        lines.append(f"[dim]Minted {len(minted)} badge(s):[/dim]\n")
        for branch, aid in minted:
            lines.append(f"  [blue]*[/blue] {branch} -> Artifact #{aid}")

        console.print(Panel(
            "\n".join(lines),
            title="Event Badges Minted",
            border_style="blue",
        ))
        console.print()

        logger.info(f"[commons] Event '{event_name}': minted {len(minted)} badges for {[b for b, _ in minted]}")

    except Exception as e:
        logger.error(f"[commons] Mint event artifact failed: {e}")
        console.print(f"[red]Failed to mint event artifacts: {e}[/red]")

    return True
