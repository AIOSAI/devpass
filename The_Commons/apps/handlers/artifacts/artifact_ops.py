#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: artifact_ops.py - Artifact Operations Handler
# Date: 2026-02-18
# Version: 1.0.0
# Category: the_commons/handlers/artifacts
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-18): Initial creation (FPLAN-0356 Phase 3)
#
# CODE STANDARDS:
#   - Handler: implementation logic
#   - Importable by Commons modules/entry point
# =============================================

"""
Artifact Operations Handler

Implementation logic for artifact workflows: craft, list, inspect,
and birth certificate creation.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

# Infrastructure
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))
sys.path.insert(0, str(Path.home()))

from prax.apps.modules.logger import system_logger as logger
from cli.apps.modules import console

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# The Commons imports
COMMONS_ROOT = Path("/home/aipass/The_Commons")
sys.path.insert(0, str(COMMONS_ROOT / "apps"))

from handlers.database.db import get_db, close_db

# Constants
BRANCH_REGISTRY_PATH = Path.home() / "BRANCH_REGISTRY.json"

VALID_RARITIES = ("common", "uncommon", "rare", "legendary", "unique")
VALID_TYPES = ("crafted", "found", "birth_certificate", "event", "seasonal", "joint", "system")

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

def _validate_metadata(metadata_str: str) -> Optional[dict]:
    """
    Validate JSON metadata string. Must be shallow (one level deep max).

    Args:
        metadata_str: JSON string to validate

    Returns:
        Parsed dict if valid, None if invalid
    """
    try:
        data = json.loads(metadata_str)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None

    # Enforce shallow: no nested dicts or lists
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            return None

    return data


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

        # Use artifact id and sanitized name for filename
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


# =============================================================================
# ARTIFACT OPERATIONS
# =============================================================================

def craft_artifact(args: List[str]) -> bool:
    """
    Create a new artifact.

    Usage: drone commons craft "name" "description" [--type crafted] [--rarity common] [--metadata '{}']
    """
    if not args or len(args) < 2:
        console.print("[red]Usage: commons craft \"name\" \"description\" [--type TYPE] [--rarity RARITY][/red]")
        console.print("[dim]Types: crafted, found, event, seasonal, joint, system[/dim]")
        console.print("[dim]Rarities: common, uncommon, rare, legendary, unique[/dim]")
        return True

    name = args[0]
    description = args[1]

    # Parse optional flags
    artifact_type = "crafted"
    rarity = "common"
    metadata_str = "{}"
    remaining = args[2:]

    i = 0
    while i < len(remaining):
        if remaining[i] == "--type" and i + 1 < len(remaining):
            artifact_type = remaining[i + 1]
            i += 2
        elif remaining[i] == "--rarity" and i + 1 < len(remaining):
            rarity = remaining[i + 1]
            i += 2
        elif remaining[i] == "--metadata" and i + 1 < len(remaining):
            metadata_str = remaining[i + 1]
            i += 2
        else:
            i += 1

    # Validate type
    if artifact_type not in VALID_TYPES:
        console.print(f"[red]Invalid type '{artifact_type}'. Must be one of: {', '.join(VALID_TYPES)}[/red]")
        return True

    # Validate rarity
    if rarity not in VALID_RARITIES:
        console.print(f"[red]Invalid rarity '{rarity}'. Must be one of: {', '.join(VALID_RARITIES)}[/red]")
        return True

    # Validate metadata JSON
    metadata = _validate_metadata(metadata_str)
    if metadata is None:
        console.print("[red]Invalid metadata: must be valid shallow JSON (no nested objects/arrays)[/red]")
        return True

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    creator = caller["name"]

    try:
        conn = get_db()

        cursor = conn.execute(
            "INSERT INTO artifacts (name, type, creator, owner, rarity, description, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, artifact_type, creator, creator, rarity, description, json.dumps(metadata)),
        )
        artifact_id = cursor.lastrowid

        # Create history entry
        conn.execute(
            "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
            "VALUES (?, 'created', ?, ?, ?)",
            (artifact_id, creator, creator, f"Crafted '{name}' ({rarity} {artifact_type})"),
        )

        conn.commit()

        # Save physical JSON file
        artifact_data = {
            "id": artifact_id,
            "name": name,
            "type": artifact_type,
            "creator": creator,
            "owner": creator,
            "rarity": rarity,
            "description": description,
            "metadata": metadata,
            "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        _save_artifact_file(artifact_data, creator)

        close_db(conn)

        rarity_color = RARITY_COLORS.get(rarity, "white")
        console.print()
        console.print(f"[green]Artifact crafted![/green]")
        console.print(f"  [dim]ID:[/dim] {artifact_id}")
        console.print(f"  [dim]Name:[/dim] {name}")
        console.print(f"  [dim]Type:[/dim] {artifact_type}")
        console.print(f"  [dim]Rarity:[/dim] [{rarity_color}]{rarity}[/{rarity_color}]")
        console.print(f"  [dim]Creator:[/dim] {creator}")
        console.print(f"  [dim]Description:[/dim] {description}")
        console.print()
        logger.info(f"[commons] Artifact {artifact_id} crafted by {creator}: {name} ({rarity} {artifact_type})")

    except Exception as e:
        logger.error(f"[commons] Artifact creation failed: {e}")
        console.print(f"[red]Failed to craft artifact: {e}[/red]")

    return True


def list_artifacts(args: List[str]) -> bool:
    """
    List artifacts. Default: show only YOUR artifacts.

    Usage: drone commons artifacts [--all] [--type TYPE] [--rarity RARITY]
    """
    # Parse flags
    show_all = "--all" in args
    filter_type = None
    filter_rarity = None

    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            filter_type = args[i + 1]
            i += 2
        elif args[i] == "--rarity" and i + 1 < len(args):
            filter_rarity = args[i + 1]
            i += 2
        else:
            i += 1

    # Get caller identity (needed for default owner filter)
    owner_filter = None
    if not show_all:
        from modules.commons_identity import get_caller_branch
        caller = get_caller_branch()
        if not caller:
            console.print("[red]Could not detect calling branch. Use --all to see all artifacts.[/red]")
            return True
        owner_filter = caller["name"]

    try:
        conn = get_db()

        # Build query
        query = "SELECT id, name, type, creator, owner, rarity, description, created_at FROM artifacts WHERE 1=1"
        params: List[Any] = []

        if owner_filter:
            query += " AND owner = ?"
            params.append(owner_filter)

        if filter_type:
            query += " AND type = ?"
            params.append(filter_type)

        if filter_rarity:
            query += " AND rarity = ?"
            params.append(filter_rarity)

        query += " ORDER BY created_at DESC"

        rows = conn.execute(query, params).fetchall()
        close_db(conn)

    except Exception as e:
        logger.error(f"[commons] Artifact listing failed: {e}")
        console.print(f"[red]Failed to list artifacts: {e}[/red]")
        return True

    if not rows:
        scope = "in the system" if show_all else "in your collection"
        console.print(f"\n[dim]No artifacts found {scope}.[/dim]\n")
        return True

    # Build table
    scope_label = "All Artifacts" if show_all else f"Artifacts owned by {owner_filter}"
    table = Table(title=scope_label, border_style="cyan")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Name", style="bold")
    table.add_column("Type", style="dim")
    table.add_column("Rarity", width=10)
    table.add_column("Creator", style="dim")
    table.add_column("Owner", style="dim")
    table.add_column("Created", style="dim", width=12)

    for row in rows:
        rarity_val = row["rarity"]
        rarity_color = RARITY_COLORS.get(rarity_val, "white")
        created_short = row["created_at"][:10] if row["created_at"] else ""

        table.add_row(
            str(row["id"]),
            row["name"],
            row["type"],
            f"[{rarity_color}]{rarity_val}[/{rarity_color}]",
            row["creator"],
            row["owner"],
            created_short,
        )

    console.print()
    console.print(table)
    console.print(f"\n[dim]Total: {len(rows)} artifact(s)[/dim]\n")

    return True


def inspect_artifact(args: List[str]) -> bool:
    """
    Show full artifact details including provenance chain.

    Usage: drone commons inspect <id> [--full]
    By default shows last 10 provenance entries. Use --full for complete history.
    """
    if not args:
        console.print("[red]Usage: commons inspect <artifact_id> [--full][/red]")
        return True

    show_full = "--full" in args
    filtered_args = [a for a in args if a != "--full"]

    if not filtered_args:
        console.print("[red]Usage: commons inspect <artifact_id> [--full][/red]")
        return True

    try:
        artifact_id = int(filtered_args[0])
    except ValueError:
        console.print("[red]Artifact ID must be a number[/red]")
        return True

    try:
        conn = get_db()

        # Get artifact
        row = conn.execute(
            "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
        ).fetchone()

        if not row:
            close_db(conn)
            console.print(f"[red]Artifact {artifact_id} not found[/red]")
            return True

        artifact = dict(row)

        # Get provenance chain
        history_rows = conn.execute(
            "SELECT * FROM artifact_history WHERE artifact_id = ? ORDER BY created_at ASC",
            (artifact_id,),
        ).fetchall()
        history = [dict(r) for r in history_rows]

        close_db(conn)

    except Exception as e:
        logger.error(f"[commons] Artifact inspect failed: {e}")
        console.print(f"[red]Error inspecting artifact: {e}[/red]")
        return True

    # Display artifact details
    rarity_val = artifact["rarity"]
    rarity_color = RARITY_COLORS.get(rarity_val, "white")

    # Parse metadata for display
    try:
        metadata = json.loads(artifact["metadata"]) if artifact["metadata"] else {}
    except (json.JSONDecodeError, TypeError):
        metadata = {}

    details = []
    details.append(f"[bold]Name:[/bold]        {artifact['name']}")
    details.append(f"[bold]Type:[/bold]        {artifact['type']}")
    details.append(f"[bold]Rarity:[/bold]      [{rarity_color}]{rarity_val}[/{rarity_color}]")
    details.append(f"[bold]Creator:[/bold]     {artifact['creator']}")
    details.append(f"[bold]Owner:[/bold]       {artifact['owner']}")
    details.append(f"[bold]Description:[/bold] {artifact['description']}")
    details.append(f"[bold]Created:[/bold]     {artifact['created_at']}")

    if artifact["expires_at"]:
        details.append(f"[bold]Expires:[/bold]     {artifact['expires_at']}")

    if artifact["room_found"]:
        details.append(f"[bold]Found in:[/bold]   r/{artifact['room_found']}")

    if metadata:
        details.append(f"[bold]Metadata:[/bold]")
        for key, value in metadata.items():
            details.append(f"  {key}: {value}")

    content_text = "\n".join(details)

    console.print()
    console.print(Panel(
        content_text,
        title=f"Artifact #{artifact_id}",
        border_style=rarity_color,
    ))

    # Display provenance chain
    if history:
        total_entries = len(history)
        max_display = 10

        # Determine which entries to show
        if show_full or total_entries <= max_display:
            display_entries = history
            header_text = f"Provenance Chain ({total_entries} entries)"
        else:
            display_entries = history[-max_display:]
            header_text = f"Provenance Chain (showing last {max_display} of {total_entries} entries)"

        console.print(f"\n[bold]{header_text}:[/bold]\n")

        for entry in display_entries:
            action = entry["action"]
            from_agent = entry["from_agent"] or "?"
            to_agent = entry["to_agent"] or "?"
            entry_details = entry["details"] or ""
            timestamp = entry["created_at"] or ""

            if action == "created":
                console.print(f"  [green]+[/green] {timestamp[:19]} | Created by {from_agent}")
            elif action in ("traded", "gifted"):
                console.print(f"  [cyan]>[/cyan] {timestamp[:19]} | {action.title()}: {from_agent} -> {to_agent}")
            elif action == "found":
                console.print(f"  [yellow]*[/yellow] {timestamp[:19]} | Found by {to_agent}")
            elif action == "expired":
                console.print(f"  [red]x[/red] {timestamp[:19]} | Expired: {entry_details}")
            else:
                console.print(f"  [dim]-[/dim] {timestamp[:19]} | {action.title()}: {entry_details}")

        if not show_full and total_entries > max_display:
            console.print(f"\n  [dim]Full provenance: {total_entries} entries (use --full to see all)[/dim]")
    else:
        console.print("\n[dim]  No provenance history recorded.[/dim]")

    console.print()
    return True


# =============================================================================
# BIRTH CERTIFICATE (INTERNAL)
# =============================================================================

def create_birth_certificate(
    conn: Any,
    branch_name: str,
    citizen_number: int,
    template_used: str,
    creator: str,
    purpose: str,
) -> Optional[int]:
    """
    Create a birth_certificate type artifact for a branch.

    Internal function used by backfill scripts and Cortex registration.

    Args:
        conn: SQLite connection
        branch_name: Branch this certificate belongs to
        citizen_number: Citizen number from registry
        template_used: Template/profile used to create the branch
        creator: Who created this branch (usually CORTEX or SYSTEM)
        purpose: Branch description/purpose

    Returns:
        artifact_id if created, None on error
    """
    try:
        # Check if birth certificate already exists
        existing = conn.execute(
            "SELECT id FROM artifacts WHERE owner = ? AND type = 'birth_certificate'",
            (branch_name,),
        ).fetchone()

        if existing:
            logger.info(f"[commons] Birth certificate already exists for {branch_name} (id={existing['id']})")
            return None

        # Build metadata
        metadata = {
            "citizen_number": citizen_number,
            "template": template_used,
            "purpose": purpose,
        }

        # Validate metadata
        validated = _validate_metadata(json.dumps(metadata))
        if validated is None:
            logger.error(f"[commons] Invalid metadata for birth certificate: {branch_name}")
            return None

        description = (
            f"Official birth certificate for {branch_name}. "
            f"Citizen #{citizen_number}, registered using '{template_used}' template. "
            f"Purpose: {purpose}"
        )

        cursor = conn.execute(
            "INSERT INTO artifacts (name, type, creator, owner, rarity, description, metadata) "
            "VALUES (?, 'birth_certificate', ?, ?, 'unique', ?, ?)",
            (
                f"{branch_name} Birth Certificate",
                creator,
                branch_name,
                description,
                json.dumps(validated),
            ),
        )
        artifact_id = cursor.lastrowid

        # Create history entry
        conn.execute(
            "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
            "VALUES (?, 'created', ?, ?, ?)",
            (artifact_id, creator, branch_name, f"Birth certificate issued for {branch_name}"),
        )

        conn.commit()

        # Save physical file
        artifact_data = {
            "id": artifact_id,
            "name": f"{branch_name} Birth Certificate",
            "type": "birth_certificate",
            "creator": creator,
            "owner": branch_name,
            "rarity": "unique",
            "description": description,
            "metadata": validated,
            "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        _save_artifact_file(artifact_data, branch_name)

        logger.info(f"[commons] Birth certificate created for {branch_name} (artifact_id={artifact_id})")
        return artifact_id

    except Exception as e:
        logger.error(f"[commons] Birth certificate creation failed for {branch_name}: {e}")
        return None


# =============================================================================
# JOINT ARTIFACT - COLLAB
# =============================================================================

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


def collab_artifact(args: List[str]) -> bool:
    """
    Initiate a joint artifact that requires multiple signers.

    Usage: commons collab "artifact_name" "description" @signer1 @signer2 [--rarity rare]
    Creates a pending joint artifact. When all signers sign, the artifact is created.
    Expires after 48 hours if not completed.
    """
    if len(args) < 3:
        console.print('[red]Usage: commons collab "name" "description" @signer1 @signer2 [--rarity rare][/red]')
        return True

    artifact_name = args[0]
    description = args[1]

    # Parse signers and --rarity flag
    rarity = "rare"
    signers = []
    remaining = args[2:]
    i = 0
    while i < len(remaining):
        if remaining[i] == "--rarity" and i + 1 < len(remaining):
            rarity = remaining[i + 1]
            i += 2
        elif remaining[i].startswith("@"):
            resolved = _resolve_branch_name(remaining[i])
            if resolved:
                signers.append(resolved)
            else:
                console.print(f"[yellow]Warning: Branch '{remaining[i]}' not found, skipping[/yellow]")
            i += 1
        else:
            i += 1

    if not signers:
        console.print("[red]At least one @signer is required[/red]")
        return True

    if rarity not in VALID_RARITIES:
        console.print(f"[red]Invalid rarity '{rarity}'. Must be one of: {', '.join(VALID_RARITIES)}[/red]")
        return True

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    initiator = caller["name"]

    # Deduplicate signers, remove initiator from signers list
    signers = list(dict.fromkeys(s for s in signers if s != initiator))
    if not signers:
        console.print("[red]You need at least one other signer (not yourself)[/red]")
        return True

    # Calculate expiry (48h from now)
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        conn = get_db()

        cursor = conn.execute(
            "INSERT INTO joint_pending (artifact_name, description, rarity, initiator, "
            "required_signers, current_signers, expires_at) VALUES (?, ?, ?, ?, ?, '[]', ?)",
            (artifact_name, description, rarity, initiator,
             json.dumps(signers), expires_at),
        )
        pending_id = cursor.lastrowid
        conn.commit()
        close_db(conn)

        console.print()
        console.print(f"[green]Joint artifact initiated![/green]")
        console.print(f"  [dim]Pending ID:[/dim] {pending_id}")
        console.print(f"  [dim]Name:[/dim] {artifact_name}")
        console.print(f"  [dim]Rarity:[/dim] [{RARITY_COLORS.get(rarity, 'white')}]{rarity}[/{RARITY_COLORS.get(rarity, 'white')}]")
        console.print(f"  [dim]Initiator:[/dim] {initiator}")
        console.print(f"  [dim]Required signers:[/dim] {', '.join(signers)}")
        console.print(f"  [dim]Expires:[/dim] {expires_at}")
        console.print()
        console.print(f"[dim]Signers can complete with: commons sign {pending_id}[/dim]")
        console.print()

        logger.info(f"[commons] Joint artifact {pending_id} initiated by {initiator}: {artifact_name}")

    except Exception as e:
        logger.error(f"[commons] Collab artifact failed: {e}")
        console.print(f"[red]Failed to create joint artifact: {e}[/red]")

    return True


# =============================================================================
# JOINT ARTIFACT - SIGN
# =============================================================================

def sign_artifact(args: List[str]) -> bool:
    """
    Sign a pending joint artifact.

    Usage: commons sign <pending_id>
    When all required signers have signed, the artifact is created automatically.
    """
    if not args:
        console.print("[red]Usage: commons sign <pending_id>[/red]")
        return True

    try:
        pending_id = int(args[0])
    except ValueError:
        console.print("[red]Pending ID must be a number[/red]")
        return True

    # Get caller identity
    from modules.commons_identity import get_caller_branch
    caller = get_caller_branch()
    if not caller:
        console.print("[red]Could not detect calling branch. Run from a branch directory.[/red]")
        return True

    signer = caller["name"]

    try:
        conn = get_db()

        # Get pending artifact
        row = conn.execute(
            "SELECT * FROM joint_pending WHERE id = ?", (pending_id,)
        ).fetchone()

        if not row:
            close_db(conn)
            console.print(f"[red]Pending joint artifact {pending_id} not found[/red]")
            return True

        pending = dict(row)

        # Check expiry
        now = datetime.now(timezone.utc)
        expires_dt = datetime.strptime(pending["expires_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if now > expires_dt:
            conn.execute("DELETE FROM joint_pending WHERE id = ?", (pending_id,))
            conn.commit()
            close_db(conn)
            console.print(f"[red]Joint artifact {pending_id} has expired[/red]")
            return True

        required_signers = json.loads(pending["required_signers"])
        current_signers = json.loads(pending["current_signers"])

        # Verify signer is required
        if signer not in required_signers:
            close_db(conn)
            console.print(f"[red]You are not a required signer for this artifact[/red]")
            console.print(f"[dim]Required signers: {', '.join(required_signers)}[/dim]")
            return True

        # Check if already signed
        if signer in current_signers:
            close_db(conn)
            console.print(f"[yellow]You have already signed this artifact[/yellow]")
            return True

        # Add signature
        current_signers.append(signer)
        conn.execute(
            "UPDATE joint_pending SET current_signers = ? WHERE id = ?",
            (json.dumps(current_signers), pending_id),
        )

        # Check if all signatures collected
        if set(required_signers).issubset(set(current_signers)):
            # All signed - create the actual artifact
            all_participants = [pending["initiator"]] + current_signers
            metadata = json.dumps({"signers": all_participants, "joint": True})

            cursor = conn.execute(
                "INSERT INTO artifacts (name, type, creator, owner, rarity, description, metadata) "
                "VALUES (?, 'joint', ?, ?, ?, ?, ?)",
                (pending["artifact_name"], pending["initiator"], pending["initiator"],
                 pending["rarity"], pending["description"], metadata),
            )
            artifact_id = cursor.lastrowid

            # Create history entry
            conn.execute(
                "INSERT INTO artifact_history (artifact_id, action, from_agent, to_agent, details) "
                "VALUES (?, 'created', ?, ?, ?)",
                (artifact_id, pending["initiator"], pending["initiator"],
                 f"Joint artifact created by {', '.join(all_participants)}"),
            )

            # Remove pending entry
            conn.execute("DELETE FROM joint_pending WHERE id = ?", (pending_id,))
            conn.commit()

            # Save physical file
            artifact_data = {
                "id": artifact_id,
                "name": pending["artifact_name"],
                "type": "joint",
                "creator": pending["initiator"],
                "owner": pending["initiator"],
                "rarity": pending["rarity"],
                "description": pending["description"],
                "metadata": {"signers": all_participants, "joint": True},
                "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            _save_artifact_file(artifact_data, pending["initiator"])

            close_db(conn)

            rarity_color = RARITY_COLORS.get(pending["rarity"], "white")
            console.print()
            console.print(f"[bold green]Joint artifact completed![/bold green]")
            console.print(f"  [dim]Artifact ID:[/dim] {artifact_id}")
            console.print(f"  [dim]Name:[/dim] [{rarity_color}]{pending['artifact_name']}[/{rarity_color}]")
            console.print(f"  [dim]Rarity:[/dim] [{rarity_color}]{pending['rarity']}[/{rarity_color}]")
            console.print(f"  [dim]Created by:[/dim] {', '.join(all_participants)}")
            console.print(f"  [dim]Owner:[/dim] {pending['initiator']}")
            console.print()

            logger.info(f"[commons] Joint artifact {artifact_id} completed: {pending['artifact_name']} by {all_participants}")
        else:
            conn.commit()
            close_db(conn)

            remaining_signers = [s for s in required_signers if s not in current_signers]
            console.print()
            console.print(f"[green]Signed! {signer} added signature to joint artifact {pending_id}[/green]")
            console.print(f"  [dim]Signed:[/dim] {', '.join(current_signers)}")
            console.print(f"  [dim]Still needed:[/dim] {', '.join(remaining_signers)}")
            console.print()

            logger.info(f"[commons] {signer} signed joint artifact {pending_id}")

    except Exception as e:
        logger.error(f"[commons] Sign artifact failed: {e}")
        console.print(f"[red]Failed to sign artifact: {e}[/red]")

    return True
